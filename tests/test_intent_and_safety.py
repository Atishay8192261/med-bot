from app.intent import classify_intent, has_red_flags

def test_intent_basic():
    assert classify_intent("cheaper alternative?") == "cheaper"
    assert classify_intent("what are the side effects") == "side_effects"
    assert classify_intent("how to take this") == "how_to_take"
    assert classify_intent("what is this used for") == "uses"

def test_red_flags():
    assert has_red_flags("dose for child") is True
    assert has_red_flags("pregnancy warning?") is True
    assert has_red_flags("price please") is False
