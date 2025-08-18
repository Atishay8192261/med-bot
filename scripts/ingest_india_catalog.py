import os, csv, re, sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg

load_dotenv()
CSV_PATH = Path("data/india_catalog_sample.csv")
if not CSV_PATH.exists():
    print(f"ERROR: {CSV_PATH} not found.")
    sys.exit(1)

def split_salts(s: str):
    if not s:
        return []
    # Split on + , | and handle extra spaces/parentheses artifacts
    parts = re.split(r"[+,\|]", s)
    cleaned = []
    for p in parts:
        x = re.sub(r"[™®]", "", p, flags=re.IGNORECASE).strip()
        x = re.sub(r"\s+", " ", x)
        if x:
            cleaned.append(x)
    return cleaned

conn = psycopg.connect(
    host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
)

inserted = 0
skipped = 0

with conn:
    with conn.cursor() as cur:
        with CSV_PATH.open() as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                bn = (r.get("brand_name") or "").strip()
                if not bn:
                    skipped += 1
                    continue
                strength = (r.get("strength") or "").strip() or None
                dosage_form = (r.get("dosage_form") or "").strip() or None
                pack = (r.get("pack") or "").strip() or None
                mrp = r.get("mrp_inr")
                mrp_inr = float(mrp) if (mrp is not None and mrp != "") else None
                manufacturer = (r.get("manufacturer") or "").strip() or None
                discontinued = str(r.get("discontinued","false")).lower() in ("true","1","yes")

                # Insert brand row
                cur.execute("""
                  INSERT INTO products_in (brand_name, strength, dosage_form, pack, mrp_inr, manufacturer, discontinued)
                  VALUES (%s,%s,%s,%s,%s,%s,%s)
                  RETURNING id
                """, (bn, strength, dosage_form, pack, mrp_inr, manufacturer, discontinued))
                pid = cur.fetchone()[0]

                salts = split_salts(r.get("salts",""))
                for i, sname in enumerate(salts, start=1):
                    cur.execute("""
                      INSERT INTO product_salts (product_id, salt_name, salt_pos)
                      VALUES (%s,%s,%s)
                    """, (pid, sname, i))
                inserted += 1

print(f"INGEST COMPLETE: inserted={inserted}, skipped={skipped}")
