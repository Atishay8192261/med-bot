import re

ALIAS_FALLBACKS = {
    "paracetamol": "acetaminophen",
    "clavulanic acid": "clavulanate potassium",
    "amoxycillin": "amoxicillin",
}

def norm_term(s: str) -> str:
    x = s or ""
    x = re.sub(r"[™®]", "", x)
    x = x.strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x

def alias_if_needed(term_norm: str) -> str | None:
    return ALIAS_FALLBACKS.get(term_norm)
