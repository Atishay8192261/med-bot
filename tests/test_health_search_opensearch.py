import os
import pytest


@pytest.mark.integration
def test_health_and_search_opensearch(monkeypatch):
    # Require OpenSearch backend running (green). If not available, skip.
    monkeypatch.setenv("SEARCH_BACKEND", "os")
    monkeypatch.setenv("NO_EXTERNAL", "1")  # avoid external HTTP during test
    # Import after env set
    from app.main import app, _search_service  # type: ignore
    from fastapi.testclient import TestClient
    from app.search_service import OpenSearchService

    if not isinstance(_search_service, OpenSearchService):
        pytest.skip("OpenSearch backend not active")
    if not _search_service.is_alive():  # type: ignore
        pytest.skip("OpenSearch not reachable")

    client = TestClient(app)
    h = client.get("/health").json()
    assert h["search_backend"] == "OpenSearchService"
    assert h["search_ok"] is True
    r = client.get("/search", params={"query": "para", "limit": 5}).json()
    assert r["query"] == "para"
    assert "hits" in r