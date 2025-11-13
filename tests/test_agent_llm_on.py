import os, pytest
from app.langgraph_agent import run_turn


@pytest.mark.integration
def test_agent_llm_on(monkeypatch):
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("No OPENAI_API_KEY set")
    monkeypatch.setenv("LLM_ENABLED", "1")
    monkeypatch.setenv("AGENT_LOCAL", "1")  # in-process for speed
    r = run_turn("sess-llm", "What is Augmentin used for?")
    assert r["answer"]