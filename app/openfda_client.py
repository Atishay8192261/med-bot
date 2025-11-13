from __future__ import annotations
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import psycopg, json
from .ext_http import get as http_get
from .normalization import normalize_term
from collections import deque
import time

OPENFDA_BASE = os.getenv("OPENFDA_BASE", "https://api.fda.gov/drug/label.json")
TTL_DAYS = int(os.getenv("OPENFDA_TTL_DAYS", "7"))
API_KEY = os.getenv("OPENFDA_API_KEY")
NO_EXTERNAL = os.getenv("NO_EXTERNAL", "0") == "1"
RATE_LIMIT_PER_MIN = int(os.getenv("OPENFDA_RATE_LIMIT_PER_MIN", "60"))

_mem_cache: dict[str, tuple[float, dict]] = {}
_mem_ttl_sec = TTL_DAYS * 86400
_rate_window = deque()


class OpenFDAClient:
    def __init__(self, conn_str: str):
        self.conn_str = conn_str

    def _from_cache(self, term_norm: str) -> Optional[Dict[str, Any]]:
        with psycopg.connect(self.conn_str) as cx:
            row = cx.execute(
                "SELECT payload, fetched_at FROM openfda_cache_by_ingredient WHERE term_norm=%s",
                (term_norm,),
            ).fetchone()
        if not row:
            return None
        payload, fetched_at = row
        if fetched_at and fetched_at < datetime.utcnow() - timedelta(days=TTL_DAYS):
            return None
        return payload

    def _to_cache(self, term_norm: str, payload: Dict[str, Any]) -> None:
        with psycopg.connect(self.conn_str) as cx:
            cx.execute(
                """
            INSERT INTO openfda_cache_by_ingredient(term_norm, payload, fetched_at)
            VALUES (%s, %s, now())
            ON CONFLICT (term_norm) DO UPDATE SET payload=EXCLUDED.payload, fetched_at=now()
            """,
                (term_norm, json.dumps(payload)),
            )
            cx.commit()

    def _memory_get(self, term_norm: str):
        item = _mem_cache.get(term_norm)
        if not item:
            return None
        ts, payload = item
        if time.time() - ts > _mem_ttl_sec:
            _mem_cache.pop(term_norm, None)
            return None
        return payload

    def _memory_put(self, term_norm: str, payload: Dict[str, Any]):
        _mem_cache[term_norm] = (time.time(), payload)

    def _rate_limit(self):
        now = time.time()
        while _rate_window and now - _rate_window[0] > 60:
            _rate_window.popleft()
        if len(_rate_window) >= RATE_LIMIT_PER_MIN:
            sleep_for = 60 - (now - _rate_window[0]) + 0.01
            if sleep_for > 0:
                time.sleep(min(sleep_for, 5))
        _rate_window.append(time.time())

    def fetch_sections_by_ingredient(self, term: str) -> Optional[Dict[str, List[str]]]:
        term_norm = normalize_term(term)
        cached = self._memory_get(term_norm)
        if cached is not None:
            return cached
        cached = self._from_cache(term_norm)
        if cached is not None:
            self._memory_put(term_norm, cached)
            return cached
        if NO_EXTERNAL:
            return None
        self._rate_limit()
        params = {
            "search": f'openfda.substance_name:"{term}" OR active_ingredient:"{term}"',
            "limit": 5,
        }
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY
        r = http_get(OPENFDA_BASE, params=params, headers=headers)
        if r.status_code != 200:
            return None
        data = r.json() or {}
        results = data.get("results") or []
        if not results:
            return None
        buckets = {"uses": [], "precautions": [], "side_effects": []}
        fields = {
            "uses": ["indications_and_usage", "purpose"],
            "precautions": [
                "warnings",
                "warnings_and_cautions",
                "information_for_patients",
                "patient_information",
                "ask_doctor",
                "do_not_use",
                "stop_use",
            ],
            "side_effects": ["adverse_reactions", "adverse_reactions_table"],
        }

        def take(v):
            if not v:
                return []
            if isinstance(v, list):
                return [s for s in v if isinstance(s, str)]
            if isinstance(v, str):
                return [v]
            return []

        for doc in results:
            for k, flds in fields.items():
                for fld in flds:
                    buckets[k].extend(take(doc.get(fld)))

        for k in list(buckets.keys()):
            uniq = []
            seen = set()
            for s in buckets[k]:
                t = s.strip()
                if not t:
                    continue
                h = hash(t)
                if h in seen:
                    continue
                uniq.append(t)
                seen.add(h)
            buckets[k] = uniq
        if not any(buckets.values()):
            return None
        self._to_cache(term_norm, buckets)
        self._memory_put(term_norm, buckets)
        return buckets

_LEGACY_DB_URL = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"
_LEGACY_CLIENT = OpenFDAClient(_LEGACY_DB_URL)

def fetch_by_ingredient(ingredient: str):  # pragma: no cover legacy adapter
    data = _LEGACY_CLIENT.fetch_sections_by_ingredient(ingredient) or {}
    flat = {}
    for k, v in data.items():
        if v:
            flat[k] = v[0] if isinstance(v, list) else v
    return flat
