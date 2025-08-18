import os, psycopg
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

load_dotenv()
app = FastAPI(title="India Medicine Bot - MVP (Chunk 1)")

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

class Salt(BaseModel):
    salt_pos: int
    salt_name: str

class Brand(BaseModel):
    id: int
    brand_name: str
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    pack: Optional[str] = None
    mrp_inr: Optional[float] = None
    manufacturer: Optional[str] = None
    discontinued: bool
    salts: List[Salt] = []

@app.get("/health")
def health():
    # Lightweight DB ping
    try:
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1;")
    except Exception:
        return {"ok": False, "db": False}
    return {"ok": True, "db": True}

@app.get("/resolve")
def resolve(name: str = Query(..., min_length=2)):
    like = f"%{name}%"
    out = []
    with db() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT id, brand_name, strength, dosage_form, pack, mrp_inr, manufacturer, discontinued
          FROM products_in
          WHERE brand_name ILIKE %s
          ORDER BY brand_name
          LIMIT 20
        """, (like,))
        rows = cur.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="No brand found")

        ids = [r[0] for r in rows]
        cur.execute("""
          SELECT product_id, salt_pos, salt_name
          FROM product_salts
          WHERE product_id = ANY(%s)
          ORDER BY product_id, salt_pos
        """, (ids,))
        salts_map = {}
        for pid, pos, sname in cur.fetchall():
            salts_map.setdefault(pid, []).append(Salt(salt_pos=pos, salt_name=sname))

        for r in rows:
            pid, bn, st, df, pk, mrp, mf, disc = r
            out.append(Brand(
                id=pid, brand_name=bn, strength=st, dosage_form=df, pack=pk,
                mrp_inr=float(mrp) if mrp is not None else None,
                manufacturer=mf, discontinued=bool(disc),
                salts=salts_map.get(pid, [])
            ).model_dump())
    return {"matches": out}
