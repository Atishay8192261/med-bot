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
    # --- Newly added unresolved-to-known mappings (Chunk 4.9 hardening) ---
    # Herbal / extract standardizations
    "uniflexin": "boswellia serrata",   # marketed boswellia extract
    "aflapin": "boswellia serrata",     # proprietary boswellia derivative
    # Spelling / synonym variants
    "quiniodochlor": "clioquinol",      # synonym; clioquinol has RxNorm entry
    "embramine": "cyclizine",           # likely intended antiemetic
    "endoxifen": "tamoxifen",           # active metabolite -> parent drug
    # Biologic growth factors (choose best-known reference). nartograstim not present; map to filgrastim family
    "nartograstim": "filgrastim",
    # Multi-space combined salt artifact: leave unmapped (handled via future data cleaning)
}

def norm_term(s: str) -> str:
    x = s or ""
    x = re.sub(r"[™®]", "", x)
    x = x.strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x

def alias_if_needed(term_norm: str) -> str | None:
    return ALIAS_FALLBACKS.get(term_norm)

# Backwards compatibility: previous modules imported normalize_term
def normalize_term(s: str) -> str:  # pragma: no cover simple wrapper
    return norm_term(s)
