import os, sys, time, psycopg, argparse, math
from dotenv import load_dotenv
from app.rxnorm_client import rxnorm_lookup

load_dotenv()

# -------------------------------------
# DB helper
# -------------------------------------
def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

# -------------------------------------
# Data gathering
# -------------------------------------
def iter_products(with_signatures: bool | None, limit: int | None):
    """Yield (product_id, brand_name) and list of (pos, salt_name).

    with_signatures:
      True  -> only rows that ALREADY have salt_signature
      False -> only rows that do NOT have salt_signature
      None  -> all rows
    limit: optional maximum number of products
    """
    base = [
        "SELECT p.id, p.brand_name, s.salt_pos, s.salt_name, p.salt_signature",
        "FROM products_in p JOIN product_salts s ON s.product_id = p.id",
    ]
    where = []
    if with_signatures is True:
        where.append("p.salt_signature IS NOT NULL")
    elif with_signatures is False:
        where.append("p.salt_signature IS NULL")
    if where:
        base.append("WHERE " + " AND ".join(where))
    base.append("ORDER BY p.id, s.salt_pos")
    if limit:
        base.append(f"LIMIT {int(limit)}")
    sql = "\n".join(base) + ";"
    out: dict[int, dict] = {}
    with db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        for pid, brand, pos, sname, existing_sig in cur.fetchall():
            entry = out.setdefault(pid, {"brand": brand, "salts": [], "existing_sig": existing_sig})
            entry["salts"].append((pos, sname))
    return out

def update_product_batch(cur, batch_updates):
    for pid, rxcuis_sorted in batch_updates:
        sig = "-".join(rxcuis_sorted) if rxcuis_sorted else None
        cur.execute(
            """UPDATE products_in SET rxcuis=%s, salt_signature=%s, updated_at=NOW() WHERE id=%s""",
            (rxcuis_sorted if rxcuis_sorted else None, sig, pid),
        )

# -------------------------------------
# Main computation with progress monitoring
# -------------------------------------
def compute(args):
    start_time = time.time()
    target_set = iter_products(
        with_signatures=None if args.recompute_all else False,
        limit=args.limit,
    )
    total = len(target_set)
    if total == 0:
        print("Nothing to do (no products match criteria).")
        return 0, 0, 0.0

    print(
        f"Starting signature computation: total_products={total} mode={'recompute_all' if args.recompute_all else 'missing_only'}"
    )
    unresolved = 0
    processed = 0
    batch_updates: list[tuple[int, list[str]]] = []
    next_progress = args.progress_every

    # Rate limiting / courtesy pause optional (we rely on rxnorm_client internal backoff)
    with db() as conn, conn.cursor() as cur:
        for pid, rec in target_set.items():
            rxcui_set: set[str] = set()
            missing: list[str] = []
            for _, salt in rec["salts"]:
                try:
                    rxcuis, _ = rxnorm_lookup(salt)
                except Exception as e:  # network / transient
                    rxcuis = []
                if rxcuis:
                    rxcui_set.add(rxcuis[0])  # deterministic pick first
                else:
                    missing.append(salt)
            rxcuis_sorted = sorted(rxcui_set)
            batch_updates.append((pid, rxcuis_sorted))
            if missing:
                unresolved += 1
            processed += 1

            # Flush batch
            if len(batch_updates) >= args.db_batch:
                update_product_batch(cur, batch_updates)
                conn.commit()
                batch_updates.clear()

            # Progress output
            if processed >= next_progress:
                elapsed = time.time() - start_time
                rate = processed / elapsed if elapsed > 0 else 0.0
                eta = (total - processed) / rate if rate > 0 else float('inf')
                pct = processed / total * 100
                print(
                    f"[PROGRESS] {processed}/{total} ({pct:.2f}%) unresolved={unresolved} "
                    f"rate={rate:.1f} items/s eta={eta/60:.1f}m"
                )
                next_progress += args.progress_every

        # Final flush
        if batch_updates:
            update_product_batch(cur, batch_updates)
            conn.commit()

    elapsed = time.time() - start_time
    rate_final = processed / elapsed if elapsed > 0 else 0.0
    print(
        f"DONE products_processed={processed} unresolved_products={unresolved} "
        f"elapsed={elapsed/60:.2f}m avg_rate={rate_final:.1f}/s"
    )
    return processed, unresolved, elapsed

def parse_args(argv):
    ap = argparse.ArgumentParser(description="Compute RxNorm salt signatures for products_in")
    ap.add_argument("--recompute-all", action="store_true", help="Recompute even if salt_signature present")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of products (debug)")
    ap.add_argument("--db-batch", dest="db_batch", type=int, default=100, help="Rows per DB commit batch")
    ap.add_argument(
        "--progress-every", type=int, default=2000, help="Progress logging interval (products)"
    )
    return ap.parse_args(argv)

def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    compute(args)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
