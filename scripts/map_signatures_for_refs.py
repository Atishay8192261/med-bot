import os, re, psycopg
from dotenv import load_dotenv
from app.rxnorm_client import rxnorm_lookup
from app.normalization import norm_term

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def split_salts(generic_name: str):
    if not generic_name:
        return []
    parts = re.split(r"[+,\|]", generic_name)
    out = [norm_term(x) for x in parts if x and norm_term(x)]
    return [re.sub(r"\s+", " ", x).title() for x in out]

def signature_for(generic_name: str):
    salts = split_salts(generic_name)
    rxcui_set = set()
    for s in salts:
        rxcuis, _ = rxnorm_lookup(s)
        if rxcuis:
            rxcui_set.add(rxcuis[0])
    if not rxcui_set:
        return None
    return "-".join(sorted(rxcui_set))

def update_janaushadhi():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, generic_name FROM janaushadhi_products WHERE salt_signature IS NULL")
        rows = cur.fetchall()
        ok = 0
        for _id, name in rows:
            sig = signature_for(name)
            cur.execute("UPDATE janaushadhi_products SET salt_signature=%s, updated_at=NOW() WHERE id=%s", (sig, _id))
            if sig:
                ok += 1
    print(f"JANA updated signatures. ok={ok}")

def update_nppa():
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, generic_name FROM nppa_ceiling_prices WHERE salt_signature IS NULL")
        rows = cur.fetchall()
        ok = 0
        for _id, name in rows:
            sig = signature_for(name)
            cur.execute("UPDATE nppa_ceiling_prices SET salt_signature=%s, updated_at=NOW() WHERE id=%s", (sig, _id))
            if sig:
                ok += 1
    print(f"NPPA updated signatures. ok={ok}")

def main():
    update_janaushadhi()
    update_nppa()

if __name__ == "__main__":
    main()
