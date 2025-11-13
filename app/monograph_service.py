from typing import Dict, Any, List, Optional
import os
from .medline_client import get_or_fetch_ingredient_topic_with_fallback as get_or_fetch_ingredient_topic
from .dailymed_client import DailyMedClient
from .openfda_client import OpenFDAClient
from . import metrics

DB_URL = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"
NO_EXTERNAL = os.getenv("NO_EXTERNAL", "0") == "1"


class MonographService:
    def __init__(self, db_url: str):
        self.dm = DailyMedClient(db_url)
        self.ofda = OpenFDAClient(db_url)
        self._last_provenance: List[Dict[str, str]] = []

    @staticmethod
    def _merge_lists(dst: List[str], src: List[str], limit: int = 4):
        if not src:
            return dst
        seen = {hash((s or "").strip()): True for s in dst if isinstance(s, str)}
        for s in src:
            if not isinstance(s, str):
                continue
            key = hash(s.strip())
            if key in seen:
                continue
            dst.append(s)
            seen[key] = True
            if len(dst) >= limit:
                break
        return dst

    def merge_fallbacks(self, ingredient_terms: List[str], sections: Dict[str, List[str]]):
        buckets = ["uses", "precautions", "side_effects"]
        need = {k for k in buckets if not sections.get(k)}
        if not need or NO_EXTERNAL:
            return sections
        # reset provenance for this merge operation
        self._last_provenance = []
        dm_accum = {k: [] for k in buckets}
        ofda_accum = {k: [] for k in buckets}
        for term in ingredient_terms:
            dm = self.dm.fetch_sections_by_ingredient(term) or {}
            for k in buckets:
                dm_accum[k].extend(dm.get(k, []))
        for term in ingredient_terms:
            ofd = self.ofda.fetch_sections_by_ingredient(term) or {}
            for k in buckets:
                ofda_accum[k].extend(ofd.get(k, []))
        for k in buckets:
            sections.setdefault(k, [])
            if not sections[k]:
                before = len(sections[k])
                self._merge_lists(sections[k], dm_accum[k])
                if len(sections[k]) > before:
                    metrics.fallback_fill("dailymed", k)
                    self._last_provenance.append({"bucket": k, "source": "dailymed"})
            if not sections[k]:
                before = len(sections[k])
                self._merge_lists(sections[k], ofda_accum[k])
                if len(sections[k]) > before:
                    metrics.fallback_fill("openfda", k)
                    self._last_provenance.append({"bucket": k, "source": "openfda"})
        return sections

    def provenance(self) -> List[Dict[str, str]]:
        return list(self._last_provenance)

_MONO_SERVICE = MonographService(DB_URL)

def compose_for_signature(ingredients: List[str]) -> Optional[Dict[str, Any]]:
    got: List[Dict[str, Any]] = []
    for ing in ingredients:
        item = get_or_fetch_ingredient_topic(ing)
        if item:
            got.append(item)

    if not got:
        return None

    final: Dict[str, Any] = {
        "title": ", ".join([g.get("title") for g in got if g.get("title")]),
        "sources": [g.get("url") for g in got if g.get("url")],
        "sections": {}
    }

    for bucket in ("uses", "how_to_take", "precautions", "side_effects"):
        for g in got:
            sec = g.get("sections", {}).get(bucket)
            if sec:
                final["sections"][bucket] = sec
                break

    # Merge fallbacks for missing buckets
    final["sections"] = _MONO_SERVICE.merge_fallbacks(ingredients, final["sections"])


    # De-duplicate sources preserving order
    seen = set()
    uniq = []
    for u in final["sources"]:
        if u and u not in seen:
            uniq.append(u); seen.add(u)
    final["sources"] = uniq
    return final
