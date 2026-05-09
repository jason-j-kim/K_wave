"""Test composite GACMI score with redistribution."""
import pandas as pd

from src.config_loader import load_config
from src.dates import parse_month
from src.scoring.composite_score import compute_composite, _weighted_with_redistribution


def test_composite_default_weights_equal_third():
    cfg = load_config()
    weights = cfg.composite_weights
    assert all(abs(w - 1 / 3) < 0.01 for w in weights.values())


def test_weighted_with_redistribution_handles_missing():
    weights = {"GAC_Attention": 0.3334, "GAC_Discoverability": 0.3333, "GAC_Institutional": 0.3333}
    values = {"GAC_Attention": 60, "GAC_Discoverability": None, "GAC_Institutional": 80}
    result = _weighted_with_redistribution(weights, values)
    expected = (60 * 0.3334 + 80 * 0.3333) / (0.3334 + 0.3333)
    assert abs(result - expected) < 1e-6


def test_composite_writes_csv_and_ranks(tmp_path):
    cfg = load_config()
    month = parse_month("2099-04")
    subindex_df = pd.DataFrame([
        {"country_code": "KR", "country_name": "Korea", "sub_index": "GAC_Attention",
         "subindex_score": 80.0, "available_domains": "Music", "missing_domains": ""},
        {"country_code": "KR", "country_name": "Korea", "sub_index": "GAC_Discoverability",
         "subindex_score": 70.0, "available_domains": "", "missing_domains": ""},
        {"country_code": "KR", "country_name": "Korea", "sub_index": "GAC_Institutional",
         "subindex_score": 60.0, "available_domains": "", "missing_domains": ""},
        {"country_code": "JP", "country_name": "Japan", "sub_index": "GAC_Attention",
         "subindex_score": 50.0, "available_domains": "Music", "missing_domains": ""},
        {"country_code": "JP", "country_name": "Japan", "sub_index": "GAC_Discoverability",
         "subindex_score": 50.0, "available_domains": "", "missing_domains": ""},
        {"country_code": "JP", "country_name": "Japan", "sub_index": "GAC_Institutional",
         "subindex_score": 50.0, "available_domains": "", "missing_domains": ""},
    ])
    confidences = pd.DataFrame([
        {"country_code": c, "country_name": c, "sub_index": s, "confidence": 90.0}
        for c in ["KR", "JP"]
        for s in ["GAC_Attention", "GAC_Discoverability", "GAC_Institutional", "GACMI_Composite"]
    ])
    df = compute_composite(cfg=cfg, month=month, subindex_df=subindex_df, confidences=confidences)
    kr = df[df["country_code"] == "KR"].iloc[0]
    assert kr["rank"] == 1
    assert df.iloc[0]["country_code"] == "KR"
    assert kr["yoy_change_composite"] is None or pd.isna(kr["yoy_change_composite"])
