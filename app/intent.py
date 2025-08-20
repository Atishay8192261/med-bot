import re
from typing import Literal, Optional

Intent = Literal["uses", "side_effects", "how_to_take", "precautions", "cheaper", "summary"]

KEYMAP = [
    ("cheaper",      r"(cheap|price|cost|afford|alternative|substitute|generic|jana\s*aushadhi|nppa)"),
    ("side_effects", r"(side effect|adverse|reaction|rash|nausea|vomit|dizziness|sleepy)"),
    ("how_to_take",  r"(how (do i|to) take|dos(e|age)|when to take|before|after|food)"),
    ("precautions",  r"(precaution|warning|avoid|interact|alcohol|pregnan|breast|kidney|liver)"),
    ("uses",         r"(what (is|are)|use(d)? for|indication|treat)"),
]

RED_FLAGS = r"(pregnan|breastfeed|child|pediatric|pædiatric|elderly|kidney|liver|hepatic|renal|heart failure|dose|dosage)"

def classify_intent(query: Optional[str]) -> str:
    if not query:
        return "summary"
    q = query.lower().strip()
    for label, pat in KEYMAP:
        if re.search(pat, q):
            return label
    return "summary"

def has_red_flags(query: Optional[str]) -> bool:
    if not query: return False
    return re.search(RED_FLAGS, query.lower()) is not None
