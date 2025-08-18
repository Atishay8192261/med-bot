import os, psycopg, sys
from dotenv import load_dotenv
from app.rxnorm_client import rxnorm_lookup

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def get_products_with_salts():
    sql = """
    SELECT p.id, p.brand_name, s.salt_pos, s.salt_name
    FROM products_in p
    JOIN product_salts s ON s.product_id = p.id
    ORDER BY p.id, s.salt_pos;
    """
    out = {}
    with db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        for pid, brand, pos, sname in cur.fetchall():
            out.setdefault(pid, {"brand": brand, "salts": []})
            out[pid]["salts"].append((pos, sname))
    return out

def update_product(pid: int, rxcuis_sorted: list[str]):
    sig = "-".join(rxcuis_sorted) if rxcuis_sorted else None
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          UPDATE products_in SET rxcuis=%s, salt_signature=%s, updated_at=NOW()
          WHERE id=%s
            """,
            (rxcuis_sorted if rxcuis_sorted else None, sig, pid),
        )

def main():
    prod = get_products_with_salts()
    total = len(prod)
    unresolved = 0

    for pid, rec in prod.items():
        rxcui_set = set()
        missing = []
        for _, salt in rec["salts"]:
            rxcuis, _ = rxnorm_lookup(salt)
            if rxcuis:
                # deterministically take the first candidate
                rxcui_set.add(rxcuis[0])
            else:
                missing.append(salt)

        rxcuis_sorted = sorted(rxcui_set)
        update_product(pid, rxcuis_sorted)

        if missing:
            unresolved += 1
            print(f"[WARN] pid={pid} brand={rec['brand']}: unresolved salts = {', '.join(missing)}")
        else:
            print(f"[OK]   pid={pid} brand={rec['brand']}: rxcuis={rxcuis_sorted}")

    print(f"\nDONE. products={total}, unresolved_products={unresolved}")

if __name__ == "__main__":
    sys.exit(main())
