"""Tests for log transform and percentile-rank normalization."""
import math

import numpy as np
import pandas as pd

from src.processing.normalize_metrics import (
    log_transform, normalize, normalize_dataframe, percentile_rank, robust_z_score,
)


def test_log_transform_basic():
    out = log_transform([0, 1, math.e - 1, None, float("nan")])
    assert out[0] == 0.0
    assert math.isclose(out[1], math.log(2))
    assert math.isclose(out[2], 1.0, rel_tol=1e-6)
    assert math.isnan(out[3])
    assert math.isnan(out[4])


def test_percentile_rank_formula():
    s = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
    pct = percentile_rank(s)
    # rank/(N-1)*100: 0, 25, 50, 75, 100
    assert list(pct) == [0.0, 25.0, 50.0, 75.0, 100.0]


def test_percentile_rank_handles_ties():
    s = pd.Series([10.0, 10.0, 30.0, 40.0, 50.0])
    pct = percentile_rank(s)
    # ranks (avg method): 1.5, 1.5, 3, 4, 5 -> (r-1)/4*100
    assert pct.iloc[0] == pct.iloc[1]
    assert pct.iloc[2] == 50.0
    assert pct.iloc[4] == 100.0


def test_percentile_rank_with_nan():
    s = pd.Series([10.0, None, 30.0, 40.0])
    pct = percentile_rank(s)
    assert math.isnan(pct.iloc[1])
    assert pct.iloc[0] == 0.0
    assert pct.iloc[3] == 100.0


def test_percentile_rank_single_value():
    s = pd.Series([42.0])
    pct = percentile_rank(s)
    assert pct.iloc[0] == 50.0


def test_robust_z_score_clips():
    s = pd.Series([1, 2, 3, 4, 5, 100])
    z = robust_z_score(s)
    assert z.max() <= 100.0
    assert z.min() >= 0.0


def test_normalize_dataframe_groups_correctly():
    df = pd.DataFrame({
        "country_code": ["A", "B", "A", "B"],
        "domain_code": ["Music", "Music", "Film", "Film"],
        "signal_type": ["GMA", "GMA", "GMA", "GMA"],
        "metric_name": ["x", "x", "x", "x"],
        "raw_value": [10.0, 100.0, 1.0, 2.0],
    })
    out = normalize_dataframe(
        df, value_col="raw_value", group_cols=["domain_code", "signal_type", "metric_name"]
    )
    assert "normalized" in out.columns
    music = out[out["domain_code"] == "Music"].sort_values("country_code")
    # Two values in group: 0 and 100 percentile
    assert sorted(music["normalized"].tolist()) == [0.0, 100.0]
