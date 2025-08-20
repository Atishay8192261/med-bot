import statistics

def test_quartile_logic():
    data = [1,2,3,4,5,6,7,8]
    assert statistics.median(data) == 4.5
