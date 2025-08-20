import re

ALIAS_FALLBACKS = {
    "paracetamol": "acetaminophen",
    "clavulanic acid": "clavulanate potassium",
    "amoxycillin": "amoxicillin",
    "azithromycine": "azithromycin",
    "ranitidine hcl": "ranitidine",
    "ranitidine hydrochloride": "ranitidine",
    # Additional Indian market and spelling variants
    "metformin hcl": "metformin",
    "metformin hydrochloride": "metformin",
    "diclofenac sodium": "diclofenac",
    "diclofenac potassium": "diclofenac",
    "ibuprofen lysine": "ibuprofen",
    "amox-clav": "amoxicillin clavulanate",
    "amoxicillin clavulanic acid": "amoxicillin clavulanate",
    "clavulanate potassium": "clavulanate",  # normalize form
    "acetylsalicylic acid": "aspirin",
}

def norm_term(s: str) -> str:
    x = s or ""
    x = re.sub(r"[™®]", "", x)
    x = x.strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x

def alias_if_needed(term_norm: str) -> str | None:
    return ALIAS_FALLBACKS.get(term_norm)
