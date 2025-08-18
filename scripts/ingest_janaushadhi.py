import os, json, pandas as pd, psycopg, re
from dotenv import load_dotenv

load_dotenv()

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def clean_text(x):
    if x is None: return None
    s = str(x).strip()
    s = re.sub(r"\s+", " ", s)
    return s if s else None

def load_df(path: str):
    if path.lower().endswith(".xlsx"):
        return pd.read_excel(path)
    elif path.lower().endswith(".csv"):
        return pd.read_csv(path)
    else:
        raise ValueError("Unsupported file type")

def main():
    path = "data/jan_aushadhi_sample.xlsx"  # swap to real file later
    df = load_df(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    need_cols = ["generic_name","strength","dosage_form","pack","mrp_inr"]
    for c in need_cols:
        if c not in df.columns:
            raise SystemExit(f"Missing column: {c}")

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "generic_name": clean_text(r.get("generic_name")),
            "strength": clean_text(r.get("strength")),
            "dosage_form": clean_text(r.get("dosage_form")),
            "pack": clean_text(r.get("pack")),
            "mrp_inr": float(r.get("mrp_inr")) if pd.notnull(r.get("mrp_inr")) else None,
            "source_row": {k: (None if pd.isna(v) else str(v)) for k,v in r.items()}
        })

    with db() as conn, conn.cursor() as cur:
        for row in rows:
            cur.execute("""
              INSERT INTO janaushadhi_products (generic_name, strength, dosage_form, pack, mrp_inr, source_row, updated_at)
              VALUES (%s,%s,%s,%s,%s,%s,NOW())
            """, (row["generic_name"], row["strength"], row["dosage_form"], row["pack"], row["mrp_inr"], json.dumps(row["source_row"])) )
    print(f"JAN AUSHADHI INGESTED: {len(rows)} rows")

if __name__ == "__main__":
    main()
