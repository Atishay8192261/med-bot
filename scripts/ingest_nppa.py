import os, csv, json, psycopg, re
from dotenv import load_dotenv

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def clean(x):
    if x is None: return None
    s = str(x).strip()
    s = re.sub(r"\s+", " ", s)
    return s if s else None

def main():
    path = "data/nppa_ceiling_sample.csv"  # swap to real later
    rows = []
    with open(path) as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append({
                "generic_name": clean(r.get("generic_name")),
                "strength": clean(r.get("strength")),
                "pack": clean(r.get("pack")),
                "ceiling_price": float(r.get("ceiling_price")) if r.get("ceiling_price") else None,
                "source_row": r
            })
    with db() as conn, conn.cursor() as cur:
        for r in rows:
            cur.execute(
                """
              INSERT INTO nppa_ceiling_prices (generic_name, strength, pack, ceiling_price, source_row, updated_at)
              VALUES (%s,%s,%s,%s,%s,NOW())
                """,
                (r["generic_name"], r["strength"], r["pack"], r["ceiling_price"], json.dumps(r["source_row"]))
            )
    print(f"NPPA INGESTED: {len(rows)} rows")

if __name__ == "__main__":
    main()
