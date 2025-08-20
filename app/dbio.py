import os, psycopg
from typing import Any, Dict, List, Optional


def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )


def get_signature_by_name(name: str) -> Optional[str]:
    like = f"%{name}%"
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT salt_signature
          FROM products_in
          WHERE brand_name ILIKE %s AND salt_signature IS NOT NULL
          ORDER BY brand_name LIMIT 1
        """,
            (like,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_salts(sig: str) -> List[Dict[str, Any]]:
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT ps.salt_name, ps.salt_pos
          FROM products_in p JOIN product_salts ps ON ps.product_id = p.id
          WHERE p.salt_signature=%s ORDER BY ps.salt_pos
        """,
            (sig,),
        )
        rows = cur.fetchall()
    seen = set(); out: List[Dict[str, Any]] = []
    for name, pos in rows:
        if name not in seen:
            out.append({"salt_name": name, "salt_pos": pos}); seen.add(name)
    return out


def get_alternatives(sig: str) -> Dict[str, Any]:
    from .main import brands_by_signature, jana_by_signature, nppa_by_signature
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
        "brands": brands,
        "janaushadhi": jana,
        "nppa_ceiling_price": ceiling,
        "price_summary": summary,
    }
