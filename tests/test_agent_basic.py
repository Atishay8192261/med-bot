import pytest
from app.langgraph_agent import run_turn

@pytest.mark.integration
def test_simple_flow():
    sid = "t1"
    r1 = run_turn(sid, "What is Augmentin used for?")
    assert r1["intent"] == "uses"
    assert r1["signature"] is not None
    assert isinstance(r1["answer"], str) and len(r1["answer"]) > 0
    r2 = run_turn(sid, "Any cheaper option?")
    assert r2["intent"] == "cheaper"
    assert r2["signature"] == r1["signature"]
    assert r2["have_alternatives"] is True or isinstance(r2["answer"], str)
