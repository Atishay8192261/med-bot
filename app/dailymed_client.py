from __future__ import annotations
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import deque

import psycopg

from .ext_http import get as http_get
from .normalization import normalize_term
from . import metrics

DAILYMED_BASE = os.getenv("DAILYMED_BASE", "https://dailymed.nlm.nih.gov/dailymed/services/v2")
TTL_DAYS = int(os.getenv("DAILYMED_TTL_DAYS", "7"))
NO_EXTERNAL = os.getenv("NO_EXTERNAL", "0") in ("1", "true", "yes")
RATE_LIMIT_PER_MIN = int(os.getenv("DAILYMED_RATE_LIMIT_PER_MIN", "15"))

_mem_cache: dict[str, tuple[float, dict]] = {}
_mem_ttl_sec = TTL_DAYS * 86400
_rate_window = deque()  # timestamps of recent calls


class DailyMedClient:
    """Fetch limited DailyMed sections with dual (memory + DB) caching.

    Sections captured for fallback buckets: uses, precautions, side_effects.
    """

    def __init__(self, conn_str: str):
        self.conn_str = conn_str

    # ------------------ Cache helpers ------------------
    def _from_cache(self, term_norm: str) -> Optional[Dict[str, Any]]:
        try:
            with psycopg.connect(self.conn_str) as cx:
                row = cx.execute(
                    "SELECT payload, fetched_at FROM dailymed_cache_by_ingredient WHERE term_norm=%s",
                    (term_norm,),
                ).fetchone()
        except Exception:
            return None  # table might not exist in some test paths
        if not row:
            return None
        payload, fetched_at = row
        if fetched_at and fetched_at < datetime.utcnow() - timedelta(days=TTL_DAYS):
            return None
        return payload

    def _to_cache(self, term_norm: str, payload: Dict[str, Any]) -> None:
        try:
            with psycopg.connect(self.conn_str) as cx:
                cx.execute(
                    """
                INSERT INTO dailymed_cache_by_ingredient(term_norm, payload, fetched_at)
                VALUES (%s, %s, now())
                ON CONFLICT (term_norm) DO UPDATE SET payload=EXCLUDED.payload, fetched_at=now()
                """,
                    (term_norm, json.dumps(payload)),
                )
                cx.commit()
        except Exception:
            pass  # swallow in tests without schema

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

    # ------------------ Public API ------------------
    def fetch_sections_by_ingredient(self, term: str) -> Optional[Dict[str, List[str]]]:
        term_norm = normalize_term(term)
        cached = self._memory_get(term_norm)
        if cached is not None:
            metrics.cache_hit("dailymed", layer="memory")
            return cached
        cached = self._from_cache(term_norm)
        if cached is not None:
            metrics.cache_hit("dailymed", layer="db")
            self._memory_put(term_norm, cached)
            return cached
        metrics.cache_miss("dailymed")
        if NO_EXTERNAL:
            return None
        self._rate_limit()
        metrics.external_call("dailymed")
        r = http_get(f"{DAILYMED_BASE}/spls.json", params={"drug_name": term, "pagesize": 1})
        if r.status_code != 200:
            metrics.external_error("dailymed")
            return None
        data = r.json() or {}
        spls = data.get("data") or []
        if not spls:
            metrics.external_success("dailymed")  # call succeeded but empty
            return None
        setid = spls[0].get("setid")
        if not setid:
            metrics.external_success("dailymed")
            return None
        r2 = http_get(f"{DAILYMED_BASE}/spls/{setid}.json")
        if r2.status_code != 200:
            metrics.external_error("dailymed")
            return None
        det = r2.json() or {}
        sections: Dict[str, List[str]] = {"uses": [], "precautions": [], "side_effects": []}
        try:
            entry = (det.get("data") or [])[0]
            for sec in (entry.get("sections") or []):
                title = (sec.get("title") or "").lower()
                text = sec.get("text") or ""
                if not text:
                    continue
                if "indication" in title or "uses" in title:
                    sections["uses"].append(text)
                elif "warning" in title or "precaution" in title:
                    sections["precautions"].append(text)
                elif "adverse" in title or "side effect" in title:
                    sections["side_effects"].append(text)
        except Exception:
            pass
        if not any(sections.values()):
            metrics.external_success("dailymed")
            return None
        self._to_cache(term_norm, sections)
        self._memory_put(term_norm, sections)
        metrics.external_success("dailymed")
        return sections


_LEGACY_DB_URL = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"
_LEGACY_CLIENT = DailyMedClient(_LEGACY_DB_URL)


# ------------------ Legacy compatibility for existing medline_client imports ------------------
def search_label(ingredient: str):  # pragma: no cover - thin wrapper
    try:
        r = http_get(f"{DAILYMED_BASE}/spls.json", params={"drug_name": ingredient, "pagesize": 1})
        if r.status_code != 200:
            return None
        js = r.json() or {}
        data = js.get("data") or []
        return data[0] if data else None
    except Exception:
        return None


def get_sections_by_setid(setid: str):  # pragma: no cover legacy expanded
    try:
        r = http_get(f"{DAILYMED_BASE}/spls/{setid}.json")
        if r.status_code != 200:
            return {}
        js = r.json() or {}
        out = {}
        for sec in js.get("data") or []:
            title = (sec.get("title") or "").lower()
            text = sec.get("text") or ""
            if not text:
                continue
            if "indications" in title or "uses" in title:
                out.setdefault("uses", text)
            if "dosage and administration" in title:
                out.setdefault("how_to_take", text)
            if "warnings" in title or "precautions" in title:
                out.setdefault("precautions", text)
            if "adverse reactions" in title or "side effects" in title:
                out.setdefault("side_effects", text)
        return out
    except Exception:
        return {}

__all__ = [
    "DailyMedClient",
    "search_label",
    "get_sections_by_setid",
]
