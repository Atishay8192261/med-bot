from typing import Dict, Any, List, Optional
from .medline_client import get_or_fetch_ingredient_topic_with_fallback as get_or_fetch_ingredient_topic

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

    # De-duplicate sources preserving order
    seen = set()
    uniq = []
    for u in final["sources"]:
        if u and u not in seen:
            uniq.append(u); seen.add(u)
    final["sources"] = uniq
    return final
