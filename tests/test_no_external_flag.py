import os
from app.langgraph_agent import run_turn


def test_no_external_flag(monkeypatch):
    monkeypatch.setenv("NO_EXTERNAL", "1")
    monkeypatch.setenv("AGENT_LOCAL", "1")
    r = run_turn("sess-ext-off", "What is Augmentin used for?")
    assert r["answer"]