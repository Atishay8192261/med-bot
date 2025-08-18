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
    rxcuis: Optional[List[str]] = None
    salt_signature: Optional[str] = None

@app.get("/health")
def health():
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
          SELECT id, brand_name, strength, dosage_form, pack, mrp_inr, manufacturer, discontinued,
                 rxcuis, salt_signature
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
            pid, bn, st, df, pk, mrp, mf, disc, rxs, sig = r
            out.append(Brand(
                id=pid, brand_name=bn, strength=st, dosage_form=df, pack=pk,
                mrp_inr=float(mrp) if mrp is not None else None,
                manufacturer=mf, discontinued=bool(disc),
                salts=salts_map.get(pid, []),
                rxcuis=rxs if rxs is not None else None,
                salt_signature=sig
            ).model_dump())
    return {"matches": out}

DISCLAIMER = (
  "Educational information only; not medical advice. "
  "Always consult a licensed healthcare professional. Sources: MedlinePlus."
)

from typing import Dict, Any


def get_signature_by_name(name: str) -> Optional[str]:
    like = f"%{name}%"
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT salt_signature
          FROM products_in
          WHERE brand_name ILIKE %s
          ORDER BY brand_name
          LIMIT 1
        """,
            (like,),
        )
        row = cur.fetchone()
        return row[0] if row and row[0] else None


def get_monograph_by_signature(sig: str) -> Optional[Dict[str, Any]]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT title, sources, sections
          FROM medline_monograph_by_signature
          WHERE salt_signature=%s
        """,
            (sig,),
        )
        row = cur.fetchone()
        if not row:
            return None
        title, sources, sections = row
        return {"title": title, "sources": sources, "sections": sections}

@app.get("/monograph")
def monograph(signature: Optional[str] = None, name: Optional[str] = None):
    if not signature and not name:
        raise HTTPException(status_code=400, detail="Provide either signature or name")

    sig = signature
    if not sig and name:
        sig = get_signature_by_name(name)
        if not sig:
            raise HTTPException(status_code=404, detail="No signature found for name")

    doc = get_monograph_by_signature(sig)
    if not doc:
        raise HTTPException(status_code=404, detail="Monograph not found for signature")

    return {
        "title": doc["title"],
        "signature": sig,
        "sources": doc["sources"],
        "sections": doc["sections"],
        "disclaimer": DISCLAIMER,
    }

# --- Chunk 4: alternatives ---
from typing import Any

def salts_by_signature(sig: str) -> List[Dict[str, Any]]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT DISTINCT ps.salt_name, ps.salt_pos
          FROM products_in p
          JOIN product_salts ps ON ps.product_id=p.id
          WHERE p.salt_signature=%s
          ORDER BY ps.salt_pos
        """,
            (sig,),
        )
        return [{"salt_pos": r[1], "salt_name": r[0]} for r in cur.fetchall()]

def brands_by_signature(sig: str) -> List[Dict[str, Any]]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT id, brand_name, manufacturer, mrp_inr
          FROM products_in
          WHERE salt_signature=%s
          ORDER BY brand_name
        """,
            (sig,),
        )
        return [
            {
                "id": r[0],
                "brand_name": r[1],
                "manufacturer": r[2],
                "mrp_inr": float(r[3]) if r[3] is not None else None,
            }
            for r in cur.fetchall()
        ]

def jana_by_signature(sig: str) -> List[Dict[str, Any]]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT generic_name, strength, dosage_form, pack, mrp_inr
          FROM janaushadhi_products
          WHERE salt_signature=%s
          ORDER BY generic_name
        """,
            (sig,),
        )
        return [
            {
                "generic_name": r[0],
                "strength": r[1],
                "dosage_form": r[2],
                "pack": r[3],
                "mrp_inr": float(r[4]) if r[4] is not None else None,
            }
            for r in cur.fetchall()
        ]

def nppa_by_signature(sig: str) -> Optional[float]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT MIN(ceiling_price)
          FROM nppa_ceiling_prices
          WHERE salt_signature=%s
        """,
            (sig,),
        )
        row = cur.fetchone()
        return float(row[0]) if row and row[0] is not None else None

@app.get("/alternatives")
def alternatives(signature: Optional[str] = None, name: Optional[str] = None):
    if not signature and not name:
        raise HTTPException(status_code=400, detail="Provide either signature or name")

    sig = signature or get_signature_by_name(name)
    if not sig:
        raise HTTPException(status_code=404, detail="No signature found")

    salts = salts_by_signature(sig)
    brands = brands_by_signature(sig)
    jana = jana_by_signature(sig)
    ceiling = nppa_by_signature(sig)

    prices = [b["mrp_inr"] for b in brands if b["mrp_inr"] is not None]
    jana_prices = [j["mrp_inr"] for j in jana if j["mrp_inr"] is not None]
    all_prices = prices + jana_prices
    summary = None
    if all_prices:
        summary = {
            "min_price": min(all_prices),
            "max_price": max(all_prices),
            "count": len(all_prices),
            "n_brands": len(prices),
            "n_jana": len(jana_prices),
            "nppa_ceiling": ceiling,
        }

    return {
        "signature": sig,
        "salts": salts,
        "brands": brands,
        "janaushadhi": jana,
        "nppa_ceiling_price": ceiling,
        "price_summary": summary,
        "disclaimer": "Price info is indicative and may vary by location and time. Educational use only.",
    }
