import os, time, json, random, requests, psycopg
from typing import List, Tuple
from dotenv import load_dotenv
from .normalization import norm_term, alias_if_needed

load_dotenv()
RX_BASE = "https://rxnav.nlm.nih.gov/REST"

def db():
    return psycopg.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
    )

def http_get(url: str, params: dict, tries: int = 3, pause: float = 0.6):
    last = None
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 200:
                return r
            last = r
        except requests.RequestException as e:
            last = e
    # exponential backoff with jitter
    time.sleep(pause + random.uniform(0, pause/2))
    if hasattr(last, "raise_for_status"):
        last.raise_for_status()
    raise RuntimeError(f"HTTP failed for {url} params={params} last={last}")

def cache_get(term_norm: str) -> List[str] | None:
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT rxcuis FROM rxnorm_cache WHERE term_norm=%s", (term_norm,))
        row = cur.fetchone()
        return row[0] if row else None

def cache_put(term_norm: str, rxcuis: List[str], raw: dict | None):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO rxnorm_cache (term_norm, rxcuis, raw, updated_at)
            VALUES (%s,%s,%s,NOW())
            ON CONFLICT (term_norm) DO UPDATE SET rxcuis=excluded.rxcuis, raw=excluded.raw, updated_at=NOW()
            """,
            (term_norm, rxcuis, json.dumps(raw) if raw else None),
        )

def cache_err(term_norm: str, reason: str):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO rxnorm_errors (term_norm, reason, updated_at)
            VALUES (%s,%s,NOW())
            ON CONFLICT (term_norm) DO UPDATE SET reason=excluded.reason, updated_at=NOW()
            """,
            (term_norm, reason),
        )

def rxnorm_lookup(term: str) -> Tuple[List[str], dict | None]:
    """Return list of RxCUIs for a term, plus raw payload for trace/debug."""
    key = norm_term(term)
    cached = cache_get(key)
    if cached is not None:
        return cached, None

    # primary try: approximateTerm
    try:
        r = http_get(f"{RX_BASE}/approximateTerm.json", {"term": term, "maxEntries": 5})
        data = r.json()
    except Exception as e:
        cache_err(key, f"http_error:{e.__class__.__name__}")
        return [], None
    cands = data.get("approximateGroup", {}).get("candidate", []) or []
    rxcuis: List[str] = []
    for c in cands:
        rxcui = c.get("rxcui")
        if rxcui and str(rxcui) not in rxcuis:
            rxcuis.append(str(rxcui))

    # fallback via alias if nothing found
    if not rxcuis:
        alias = alias_if_needed(key)
        if alias:
            try:
                r = http_get(f"{RX_BASE}/approximateTerm.json", {"term": alias, "maxEntries": 5})
                data = r.json()
            except Exception:
                pass
            cands = data.get("approximateGroup", {}).get("candidate", []) or []
            for c in cands:
                rxcui = c.get("rxcui")
                if rxcui and str(rxcui) not in rxcuis:
                    rxcuis.append(str(rxcui))

    # Save in cache or error table
    if rxcuis:
        cache_put(key, rxcuis, data)
    else:
        cache_err(key, "no_rxcui")

    return rxcuis, data
