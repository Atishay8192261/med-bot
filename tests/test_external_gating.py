import os
from app.dailymed_client import DailyMedClient
from app.openfda_client import OpenFDAClient
import app.openfda_client as ofmod
import app.dailymed_client as dmmod

def test_no_external_gate(monkeypatch):
    monkeypatch.setenv("NO_EXTERNAL", "1")
    db_url = os.getenv("DATABASE_URL") or "postgresql://appuser:apppass@localhost:5432/medbot"
    client_dm = DailyMedClient(db_url)
    client_of = OpenFDAClient(db_url)
    # Avoid touching DB cache tables (may not be migrated in unit context)
    monkeypatch.setattr(client_dm, "_from_cache", lambda *_: None)
    monkeypatch.setattr(client_dm, "_to_cache", lambda *a, **k: None)
    monkeypatch.setattr(client_of, "_from_cache", lambda *_: None)
    monkeypatch.setattr(client_of, "_to_cache", lambda *a, **k: None)
    # Force module-level gate variables
    monkeypatch.setattr(ofmod, "NO_EXTERNAL", True)
    monkeypatch.setattr(dmmod, "NO_EXTERNAL", True)
    assert client_dm.fetch_sections_by_ingredient("amoxicillin") is None
    assert client_of.fetch_sections_by_ingredient("amoxicillin") is None