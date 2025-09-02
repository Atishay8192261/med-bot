import os, psycopg, time, statistics, re
from typing import List, Optional, Tuple, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from app.search_service import build_search_service, PGSearchService, OpenSearchService
from app.langgraph_agent import run_turn

load_dotenv()
app = FastAPI(title="India Medicine Bot - MVP (Chunks 1-7)")
_search_service = build_search_service()

# Optional OpenTelemetry instrumentation (no-op if not configured)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    if not trace.get_tracer_provider() or isinstance(trace.get_tracer_provider(), trace.NoOpTracerProvider):
        resource = Resource.create({"service.name": "india-med-bot"})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)
except Exception:  # instrumentation is optional
    tracer = None

# --- simple in-process caches (non-distributed) ---
_SIG_NAME_CACHE: dict[str, Tuple[float, str]] = {}  # name_norm -> (ts, signature)
_CACHE_TTL = 300  # seconds

def _cache_get_sig(name_norm: str) -> Optional[str]:
    item = _SIG_NAME_CACHE.get(name_norm)
    if not item:
        return None
    ts, sig = item
    if time.time() - ts > _CACHE_TTL:
        _SIG_NAME_CACHE.pop(name_norm, None)
        return None
    return sig

def _cache_put_sig(name_norm: str, sig: str):
    _SIG_NAME_CACHE[name_norm] = (time.time(), sig)

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
    db_ok = False
    db_err = None
    try:
        with db() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1;")
        db_ok = True
    except Exception as e:
        db_err = f"{e.__class__.__name__}: {str(e)[:120]}"
    search_backend = type(_search_service).__name__
    search_ok = True
    if isinstance(_search_service, OpenSearchService):
        try:
            search_ok = _search_service.is_alive()
        except Exception:
            search_ok = False
    return {
        "ok": db_ok and search_ok,
        "db": db_ok,
        "db_error": db_err,
        "search_backend": search_backend,
        "search_ok": search_ok,
    }

@app.get("/resolve")
def resolve(
    name: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    like = f"%{name}%"
    offset = (page - 1) * limit
    out = []
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT id, brand_name, strength, dosage_form, pack, mrp_inr, manufacturer, discontinued,
                 rxcuis, salt_signature
          FROM products_in
          WHERE brand_name ILIKE %s
          ORDER BY brand_name
          LIMIT %s OFFSET %s
        """,
            (like, limit + 1, offset),  # fetch one extra to detect more
        )
        rows = cur.fetchall()
        more = len(rows) > limit
        rows = rows[:limit]
        if not rows:
            raise HTTPException(status_code=404, detail="No brand found")
        ids = [r[0] for r in rows]
        cur.execute(
            """
          SELECT product_id, salt_pos, salt_name
          FROM product_salts
          WHERE product_id = ANY(%s)
          ORDER BY product_id, salt_pos
        """,
            (ids,),
        )
        salts_map = {}
        for pid, pos, sname in cur.fetchall():
            salts_map.setdefault(pid, []).append(Salt(salt_pos=pos, salt_name=sname))
        for r in rows:
            pid, bn, st, df, pk, mrp, mf, disc, rxs, sig = r
            out.append(
                Brand(
                    id=pid,
                    brand_name=bn,
                    strength=st,
                    dosage_form=df,
                    pack=pk,
                    mrp_inr=float(mrp) if mrp is not None else None,
                    manufacturer=mf,
                    discontinued=bool(disc),
                    salts=salts_map.get(pid, []),
                    rxcuis=rxs if rxs is not None else None,
                    salt_signature=sig,
                ).model_dump()
            )
    return {"matches": out, "pagination": {"page": page, "limit": limit, "returned": len(out), "more": more}}

# --- Chunk 7: /search endpoint ---
class SearchHit(BaseModel):
    id: Optional[int] = None
    brand_name: str
    mrp_inr: Optional[float] = None
    manufacturer: Optional[str] = None
    salt_signature: Optional[str] = None
    salts: List[str] = []

class SearchResponse(BaseModel):
    query: str
    hits: List[SearchHit]

@app.get("/search", response_model=SearchResponse)
def search(query: str = Query(..., min_length=1), limit: int = 10):
    hits = _search_service.search_brands(query, limit=limit)
    return {"query": query, "hits": hits}

DISCLAIMER = (
  "Educational information only; not medical advice. "
  "Always consult a licensed healthcare professional. Sources: MedlinePlus."
)

from typing import Dict, Any


def get_signature_by_name(name: str) -> Optional[str]:
    key = name.strip().lower()
    cached = _cache_get_sig(key)
    if cached:
        return cached
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
        sig = row[0] if row and row[0] else None
    if sig:
        _cache_put_sig(key, sig)
    return sig


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
    import re
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
          SELECT ps.salt_name, ps.salt_pos
          FROM products_in p
          JOIN product_salts ps ON ps.product_id=p.id
          WHERE p.salt_signature=%s
          ORDER BY ps.salt_pos, ps.salt_name
        """,
            (sig,),
        )
        rows = cur.fetchall()
    # Normalize whitespace + case for dedup, keep first encountered per (normalized,pos)
    seen = set()
    out: List[Dict[str, Any]] = []
    for name, pos in rows:
        norm_key = (re.sub(r"\s+", " ", name.strip().lower()), pos)
        if norm_key in seen:
            continue
        seen.add(norm_key)
        # Return salt name cleaned (single spaces) but preserve original casing heuristically via title if excessive spacing
        clean = re.sub(r"\s+", " ", name.strip())
        out.append({"salt_pos": pos, "salt_name": clean})
    return out

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
        cur.execute("SELECT MIN(ceiling_price) FROM nppa_ceiling_prices WHERE salt_signature=%s", (sig,))
        row = cur.fetchone();
        return float(row[0]) if row and row[0] is not None else None

def nppa_by_signature_or_generic(sig: str) -> Optional[float]:
    # First exact signature
    exact = nppa_by_signature(sig)
    if exact is not None:
        return exact
    target_salts = [s["salt_name"].lower() for s in salts_by_signature(sig)]
    if not target_salts:
        return None
    want = set(target_salts)
    best: Optional[float] = None
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT generic_name, ceiling_price FROM nppa_ceiling_prices WHERE salt_signature IS NULL")
        for gname, price in cur.fetchall():
            if not gname or price is None:
                continue
            parts = [p.strip().lower() for p in re.split(r"[+,|]", gname) if p.strip()]
            if set(parts) == want:
                fp = float(price)
                if best is None or fp < best:
                    best = fp
    return best

@app.get("/alternatives")
def alternatives(signature: Optional[str] = None, name: Optional[str] = None):
    if not signature and not name:
        raise HTTPException(status_code=400, detail="Provide either signature or name")

    resolved_from_name = None
    if name:
        resolved_from_name = get_signature_by_name(name)
    if signature and resolved_from_name and signature != resolved_from_name:
        raise HTTPException(status_code=400, detail="Provided signature does not match resolved name signature")

    sig = signature or resolved_from_name
    if not sig:
        raise HTTPException(status_code=404, detail="No signature found")

    salts = salts_by_signature(sig)
    brands = brands_by_signature(sig)
    jana = jana_by_signature(sig)
    ceiling = nppa_by_signature_or_generic(sig)

    prices = [b["mrp_inr"] for b in brands if b["mrp_inr"] is not None]
    jana_prices = [j["mrp_inr"] for j in jana if j["mrp_inr"] is not None]
    all_prices = prices + jana_prices
    summary = None
    if all_prices:
        sorted_all = sorted(all_prices)
        q2 = statistics.median(sorted_all)
        q1 = sorted_all[len(sorted_all)//4]
        q3 = sorted_all[(3*len(sorted_all))//4]
        summary = {
            "min_price": sorted_all[0],
            "q1": q1,
            "median": q2,
            "q3": q3,
            "max_price": sorted_all[-1],
            "count": len(sorted_all),
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

# --- Chunk 5: /advise endpoint ---
from app.intent import classify_intent, has_red_flags
from app.dbio import get_signature_by_name as dbio_get_signature_by_name
from app.advise_service import advise_for

@app.get("/advise")
def advise_endpoint(
    name: Optional[str] = None,
    signature: Optional[str] = None,
    query: Optional[str] = None,
    intent: Optional[str] = None,
):
    if not name and not signature:
        raise HTTPException(status_code=400, detail="Provide either name or signature")
    sig = signature
    if not sig and name:
        sig = dbio_get_signature_by_name(name)
        if not sig:
            raise HTTPException(status_code=404, detail="No signature found for name")
    red = has_red_flags(query or "")
    intent_final = intent if intent in ("uses","side_effects","how_to_take","precautions","cheaper","summary") else classify_intent(query)
    if tracer:
        with tracer.start_as_current_span("advise") as span:
            span.set_attribute("intent", intent_final)
            span.set_attribute("signature", sig)
            payload = advise_for(sig, name, intent_final, red_flag=red)
    else:
        payload = advise_for(sig, name, intent_final, red_flag=red)
    # best-effort telemetry log
    try:
        import psycopg
        with db() as conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO advise_logs (user_query, name, signature, intent, success, notes) VALUES (%s,%s,%s,%s,%s,%s)""",
                (query, name, sig, intent_final, True, None),
            )
    except Exception:
        pass
    payload["intent"] = intent_final
    payload["red_flag"] = red
    return payload

# --- Chunk 7 optional: agent HTTP endpoint ---
class AgentRequest(BaseModel):
    session_id: str = "demo"
    message: str

class AgentReply(BaseModel):
    brand: Optional[str] = None
    signature: Optional[str] = None
    intent: Optional[str] = None
    answer: Optional[str] = None
    have_monograph: bool = False
    have_alternatives: bool = False

@app.post("/agent/message", response_model=AgentReply)
def agent_message(payload: AgentRequest = Body(...)):
    out = run_turn(payload.session_id, payload.message)
    return out
