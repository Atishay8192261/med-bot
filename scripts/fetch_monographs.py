import os, psycopg, json
from dotenv import load_dotenv
from app.monograph_service import compose_for_signature

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def products_by_signature():
    sql = """
    SELECT p.salt_signature, array_agg(ps.salt_name ORDER BY ps.salt_pos) as salts
    FROM products_in p
    JOIN product_salts ps ON ps.product_id=p.id
    WHERE p.salt_signature IS NOT NULL
    GROUP BY p.salt_signature;
    """
    out = {}
    with db() as conn, conn.cursor() as cur:
        cur.execute(sql)
        for sig, salts in cur.fetchall():
            out[sig] = [s for s in salts if s]
    return out

def put_monograph(sig: str, doc: dict):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          INSERT INTO medline_monograph_by_signature (salt_signature, title, sources, sections, updated_at)
          VALUES (%s,%s,%s,%s,NOW())
          ON CONFLICT (salt_signature) DO UPDATE SET
            title=excluded.title, sources=excluded.sources, sections=excluded.sections, updated_at=NOW()
        """,
            (sig, doc.get("title"), json.dumps(doc.get("sources")), json.dumps(doc.get("sections"))),
        )

def main():
    sig_map = products_by_signature()
    ok, miss = 0, 0
    for sig, salts in sig_map.items():
        doc = compose_for_signature(salts)
        if doc:
            put_monograph(sig, doc)
            ok += 1
            print(f"[OK] {sig} <- {salts}")
        else:
            miss += 1
            print(f"[MISS] {sig} <- {salts}")
    print(f"\nDONE. monographs={ok}, missing={miss}")

if __name__ == "__main__":
    main()
