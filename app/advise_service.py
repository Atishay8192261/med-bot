from typing import Dict, Any, Optional, List
from .monograph_service import compose_for_signature
from . import dbio
import time

_CACHE: dict[str, tuple[float, dict]] = {}
_TTL = 300.0

def _cache_get(key: str):
    item = _CACHE.get(key)
    if not item:
        return None
    ts, val = item
    if time.time() - ts > _TTL:
        _CACHE.pop(key, None)
        return None
    return val

def _cache_put(key: str, val: dict):
    _CACHE[key] = (time.time(), val)

DISCLAIMER = (
  "Educational information only, not medical advice. "
  "Consult a licensed healthcare professional. Sources: MedlinePlus; govt datasets for prices."
)

def build_summary_text(brand: str, salts: List[str], monosec: Dict[str, str]) -> str:
    uses = monosec.get("uses")
    if uses:
        return f"{brand}: {uses}"
    return f"{brand}: This medicine contains {', '.join(salts)}."

def build_side_effects_text(monosec: Dict[str, str]) -> Optional[str]:
    return monosec.get("side_effects")

def build_how_to_take_text(monosec: Dict[str, str]) -> Optional[str]:
    return monosec.get("how_to_take")

def build_precautions_text(monosec: Dict[str, str]) -> Optional[str]:
    return monosec.get("precautions")

def build_cheaper_text(sig: str, salts: List[str], alt: Dict[str, Any]) -> str:
    brands = alt.get("brands", [])
    jana = alt.get("janaushadhi", [])
    summary = alt.get("price_summary") or {}
    parts = []
    if summary:
        parts.append(
            f"Price range (observed): INR {summary.get('min_price')} – {summary.get('max_price')} (n={summary.get('count')})."
        )
        if summary.get("nppa_ceiling") is not None:
            parts.append(f"NPPA ceiling (if applicable): INR {summary['nppa_ceiling']} per unit.")
    if jana:
        cheapest = sorted(
            [j for j in jana if j.get('mrp_inr') is not None], key=lambda x: x['mrp_inr']
        )
        if cheapest:
            c = cheapest[0]
            parts.append(
                f"Jan Aushadhi option from govt scheme observed at ~INR {c['mrp_inr']} "
                f"({c.get('generic_name')} {c.get('strength') or ''} {c.get('dosage_form') or ''} {c.get('pack') or ''})."
            )
    if not parts:
        parts.append(
            "No government-price or generic alternatives found for this exact salt signature in the current dataset."
        )
    return " ".join(p for p in parts if p)

def advise_for(signature: str, brand_name: Optional[str], intent: str, red_flag: bool) -> Dict[str, Any]:
    salts = dbio.get_salts(signature)
    salt_names = [s["salt_name"] for s in salts] if salts else []

    mono = compose_for_signature(salt_names) or {"sections": {}, "sources": []}
    monosec = mono.get("sections", {})

    alt = _cache_get(f"alt:{signature}")
    if not alt:
        alt = dbio.get_alternatives(signature)
        _cache_put(f"alt:{signature}", alt)

    if red_flag and intent in ("how_to_take", "precautions", "summary", "uses", "side_effects"):
        text = (
            "I can’t provide personalized dosing, pregnancy/child safety, or condition‑specific guidance. "
            "Please consult a licensed clinician or pharmacist."
        )
    else:
        if intent == "uses":
            text = build_summary_text(brand_name or signature, salt_names, monosec)
        elif intent == "side_effects":
            text = build_side_effects_text(monosec) or "Side‑effects information was not available."
        elif intent == "how_to_take":
            text = build_how_to_take_text(monosec) or "Administration guidance was not available."
        elif intent == "precautions":
            text = build_precautions_text(monosec) or "Precautions information was not available."
        elif intent == "cheaper":
            text = build_cheaper_text(signature, salt_names, alt)
        else:  # summary
            text = build_summary_text(brand_name or signature, salt_names, monosec)

    return {
        "intent": intent,
        "signature": signature,
        "brand": brand_name,
        "salts": salt_names,
        "answer": text,
        "sources": mono.get("sources", []),
        "alternatives": alt,
        "disclaimer": DISCLAIMER,
    }
