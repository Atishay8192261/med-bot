import os
import pytest
from app.llm_service import build_llm_service


@pytest.mark.skipif(os.getenv("LLM_ENABLED","0") != "1", reason="LLM disabled")
def test_rewrite_keeps_disclaimer_and_sources():
    svc = build_llm_service()
    assert svc is not None
    base = (
        "Amoxicillin and clavulanate are used for bacterial infections.\n\n"
        "Side effects: nausea, diarrhea.\n\n"
        "Sources: MedlinePlus (https://medlineplus.gov)\n\n"
        "Disclaimer: This is educational information, not a substitute for professional medical advice."
    )
    out = svc.rewrite(base)
    assert out and len(out) >= len("Side effects")
    assert "Disclaimer" in out
    assert "Sources" in out
    # Heuristic: no new dosing added when not present
    assert not (" mg" in out.lower() and "take" in out.lower())
