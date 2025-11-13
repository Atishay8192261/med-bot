import os, pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_price_summary_with_os_backend(monkeypatch):
    monkeypatch.setenv("SEARCH_BACKEND", "os")
    monkeypatch.setenv("NO_EXTERNAL", "1")
    from app.main import app, get_signature_by_name  # type: ignore
    sig = get_signature_by_name("Augmentin")
    if not sig:
        pytest.skip("Signature for Augmentin not found")
    client = TestClient(app)
    r = client.get("/alternatives", params={"signature": sig}).json()
    assert r["signature"] == sig
    if r.get("price_summary"):
        ps = r["price_summary"]
        assert ps["min_price"] <= ps["median"] <= ps["max_price"]
