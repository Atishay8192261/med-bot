import os
from app.langgraph_agent import run_turn


def test_agent_no_llm_path_unchanged(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "0")
    r = run_turn("t-llm0", "What is Augmentin used for?")
    assert r["answer"]


def test_agent_llm_on(monkeypatch):
    if not os.getenv("OPENAI_API_KEY"):
        return
    monkeypatch.setenv("LLM_ENABLED", "1")
    r = run_turn("t-llm1", "What is Augmentin used for?")
    assert r["answer"]