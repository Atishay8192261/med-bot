import os
from fastapi.testclient import TestClient
from app.main import app

def test_monograph_endpoint_fallback(monkeypatch):
    # Skip if no DB URL (can't create fake row easily); instead patch get_monograph_by_signature
    from app import main as m
    monkeypatch.setenv("NO_EXTERNAL","1")  # ensure no network
    base_doc = {"title":"Test","sources":["medline"],"sections":{"uses":[],"how_to_take":[],"precautions":[],"side_effects":[]}}
    monkeypatch.setattr(m, "get_monograph_by_signature", lambda sig: base_doc)
    monkeypatch.setattr(m, "get_signature_by_name", lambda name: "sig1")
    client = TestClient(app)
    r = client.get("/monograph?name=Foo")
    assert r.status_code == 200
    js = r.json()
    # With NO_EXTERNAL=1 sections remain empty as provided
    assert js["sections"]["uses"] == []