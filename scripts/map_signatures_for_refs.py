import os, re, psycopg, argparse, sys, time, math
from dotenv import load_dotenv
from app.rxnorm_client import rxnorm_lookup
from app.normalization import norm_term

load_dotenv()

# -------------------------------------------------
# DB helper
# -------------------------------------------------
def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

# -------------------------------------------------
# Normalization helpers
# -------------------------------------------------
def split_salts(generic_name: str):
    if not generic_name:
        return []
    parts = re.split(r"[+,\|]", generic_name)
    out = [norm_term(x) for x in parts if x and norm_term(x)]
    return [re.sub(r"\s+", " ", x).title() for x in out]

def signature_for(generic_name: str):
    salts = split_salts(generic_name)
    rxcui_set: set[str] = set()
    for s in salts:
        try:
            rxcuis, _ = rxnorm_lookup(s)
        except Exception:
            rxcuis = []
        if rxcuis:
            rxcui_set.add(rxcuis[0])
    if not rxcui_set:
        return None
    return "-".join(sorted(rxcui_set))

# -------------------------------------------------
# Core update routine with batching & progress
# -------------------------------------------------
def update_table(table: str, args):
    target_col = "janaushadhi_products" if table == "janaushadhi" else "nppa_ceiling_prices"
    sig_field = "salt_signature"
    select_cols = "id, generic_name"
    where_parts = []
    if not args.recompute_all:
        where_parts.append(f"{sig_field} IS NULL")
    where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
    limit_clause = f" LIMIT {args.limit}" if args.limit else ""
    sql = f"SELECT {select_cols} FROM {target_col}{where_clause} ORDER BY id{limit_clause};"
    start = time.time()
    processed = 0
    updated_non_null = 0
    unresolved = 0
    next_prog = args.progress_every
    batch = []

    with db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()
        total = len(rows)
        if total == 0:
            print(f"[{table.upper()}] Nothing to do.")
            return 0,0,0,0.0
        print(f"[{table.upper()}] Starting mapping total_rows={total} mode={'recompute_all' if args.recompute_all else 'missing_only'}")
        for rid, gname in rows:
            sig = signature_for(gname)
            batch.append((sig, rid))
            if sig:
                updated_non_null += 1
            else:
                unresolved += 1
            processed += 1
            if len(batch) >= args.db_batch:
                cur.executemany(f"UPDATE {target_col} SET {sig_field}=%s, updated_at=NOW() WHERE id=%s", batch)
                conn.commit()
                batch.clear()
            if processed >= next_prog:
                elapsed = time.time() - start
                rate = processed/elapsed if elapsed>0 else 0
                pct = processed/total*100 if total else 0
                eta = (total-processed)/rate if rate>0 else math.inf
                print(f"[{table.upper()}][PROGRESS] {processed}/{total} ({pct:.2f}%) non_null={updated_non_null} unresolved={unresolved} rate={rate:.1f}/s eta={eta/60:.1f}m")
                next_prog += args.progress_every
        if batch:
            cur.executemany(f"UPDATE {target_col} SET {sig_field}=%s, updated_at=NOW() WHERE id=%s", batch)
            conn.commit()
    elapsed = time.time()-start
    rate_final = processed/elapsed if elapsed>0 else 0
    print(f"[{table.upper()}] DONE processed={processed} non_null={updated_non_null} unresolved={unresolved} elapsed={elapsed/60:.2f}m avg_rate={rate_final:.1f}/s")
    return processed, updated_non_null, unresolved, elapsed

def parse_args(argv):
    ap = argparse.ArgumentParser(description="Map salt signatures for reference tables (Janaushadhi, NPPA)")
    ap.add_argument("--table", choices=["janaushadhi","nppa","all"], default="all", help="Which table to process")
    ap.add_argument("--recompute-all", action="store_true", help="Recompute even if salt_signature present")
    ap.add_argument("--limit", type=int, default=None, help="Limit rows (debug)")
    ap.add_argument("--db-batch", type=int, default=100, help="Rows per DB commit batch")
    ap.add_argument("--progress-every", type=int, default=500, help="Progress interval (rows)")
    return ap.parse_args(argv)

def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    totals = {}
    if args.table in ("janaushadhi","all"):
        totals['janaushadhi'] = update_table("janaushadhi", args)
    if args.table in ("nppa","all"):
        totals['nppa'] = update_table("nppa", args)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
