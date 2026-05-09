"""Test sub-index aggregation across domains with weight redistribution."""
import pandas as pd

from src.config_loader import load_config
from src.dates import parse_month
from src.scoring.subindex_scores import compute_subindex_scores


def test_subindex_equal_weights_redistribute_when_domain_missing():
    cfg = load_config()
    month = parse_month("2099-03")

    # GAC_Discoverability has 2 domains; KR has both; JP has only one.
    domain_df = pd.DataFrame([
        {"country_code": "KR", "country_name": "Korea",
         "domain_code": "Publishing_Literature", "sub_index": "GAC_Discoverability",
         "domain_subindex_score": 80.0, "available_signals": "x", "missing_signals": "",
         "n_available": 1, "n_expected": 1},
        {"country_code": "KR", "country_name": "Korea",
         "domain_code": "Webtoon_Digital_Fiction", "sub_index": "GAC_Discoverability",
         "domain_subindex_score": 60.0, "available_signals": "x", "missing_signals": "",
         "n_available": 1, "n_expected": 1},
        {"country_code": "JP", "country_name": "Japan",
         "domain_code": "Publishing_Literature", "sub_index": "GAC_Discoverability",
         "domain_subindex_score": 50.0, "available_signals": "x", "missing_signals": "",
         "n_available": 1, "n_expected": 1},
        {"country_code": "JP", "country_name": "Japan",
         "domain_code": "Webtoon_Digital_Fiction", "sub_index": "GAC_Discoverability",
         "domain_subindex_score": None, "available_signals": "", "missing_signals": "x",
         "n_available": 0, "n_expected": 1},
    ])
    df = compute_subindex_scores(cfg=cfg, month=month, domain_df=domain_df)
    kr = df[(df["country_code"] == "KR") & (df["sub_index"] == "GAC_Discoverability")].iloc[0]
    jp = df[(df["country_code"] == "JP") & (df["sub_index"] == "GAC_Discoverability")].iloc[0]
    assert abs(kr["subindex_score"] - 70.0) < 1e-6
    assert abs(jp["subindex_score"] - 50.0) < 1e-6
    assert "Webtoon_Digital_Fiction" in jp["missing_domains"]
