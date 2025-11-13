from app.monograph_service import MonographService
import os

def test_merge_only_fills_missing(monkeypatch):
    svc = MonographService(os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot")
    monkeypatch.setenv("NO_EXTERNAL", "0")
    monkeypatch.setattr(svc.dm, "fetch_sections_by_ingredient", lambda term: {"uses":["DM uses"], "precautions":["DM prec"], "side_effects":["DM se"]})
    monkeypatch.setattr(svc.ofda, "fetch_sections_by_ingredient", lambda term: {"uses":["FDA uses"], "precautions":["FDA prec"], "side_effects":["FDA se"]})
    sections = {"uses":["ML uses"], "how_to_take":[], "precautions":[], "side_effects":[]}
    out = svc.merge_fallbacks(["amoxicillin"], sections)
    assert out["uses"] == ["ML uses"]
    assert out["precautions"][0] == "DM prec"
    assert out["side_effects"][0] == "DM se"
    sections2 = {"uses":[], "how_to_take":[], "precautions":[], "side_effects":[]}
    out2 = svc.merge_fallbacks(["amoxicillin"], sections2)
    assert out2["uses"][0] == "DM uses"