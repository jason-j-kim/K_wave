from src.scoring.domain_subindex_scores import _weighted_score


def test_weighted_score_full_signals():
    weights = {"A": 0.6, "B": 0.4}
    scores = {"A": 80.0, "B": 50.0}
    assert _weighted_score(weights, scores) == 0.6 * 80 + 0.4 * 50


def test_weighted_score_redistributes_when_one_missing():
    weights = {"A": 0.6, "B": 0.4}
    # Only A available: weight redistributed to 1.0
    assert _weighted_score(weights, {"A": 80.0}) == 80.0


def test_weighted_score_three_signals_one_missing():
    weights = {"A": 0.5, "B": 0.3, "C": 0.2}
    scores = {"A": 50.0, "C": 100.0}  # B missing
    # Available weight 0.5+0.2=0.7, normalized: A=5/7, C=2/7
    expected = (0.5 * 50 + 0.2 * 100) / 0.7
    assert abs(_weighted_score(weights, scores) - expected) < 1e-9


def test_weighted_score_all_missing_returns_none():
    weights = {"A": 1.0}
    assert _weighted_score(weights, {}) is None
