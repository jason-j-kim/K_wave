"""Test domain × sub-index scoring including missing-signal redistribution."""
import pandas as pd

from src.config_loader import load_config
from src.dates import parse_month
from src.scoring.domain_subindex_scores import compute_domain_subindex_scores


def test_domain_subindex_uses_weights_and_redistributes():
    cfg = load_config()
    month = parse_month("2099-02")
    # Manually built signal_df: only KR has both signals; JP only has Wikipedia.
    signal_df = pd.DataFrame([
        {"country_code": "KR", "country_name": "Korea", "domain_code": "Music",
         "signal_type": "Global_Media_Attention", "sub_index": "GAC_Attention", "signal_score": 80.0},
        {"country_code": "KR", "country_name": "Korea", "domain_code": "Music",
         "signal_type": "Wikipedia_Attention", "sub_index": "GAC_Attention", "signal_score": 60.0},
        {"country_code": "JP", "country_name": "Japan", "domain_code": "Music",
         "signal_type": "Wikipedia_Attention", "sub_index": "GAC_Attention", "signal_score": 90.0},
    ])
    df = compute_domain_subindex_scores(cfg=cfg, month=month, signal_df=signal_df)
    kr_music = df[(df["country_code"] == "KR") & (df["domain_code"] == "Music")
                  & (df["sub_index"] == "GAC_Attention")].iloc[0]
    expected = 0.55 * 80 + 0.45 * 60
    assert abs(kr_music["domain_subindex_score"] - expected) < 1e-6
    jp_music = df[(df["country_code"] == "JP") & (df["domain_code"] == "Music")
                  & (df["sub_index"] == "GAC_Attention")].iloc[0]
    # Only Wikipedia available -> redistributed weight of 1.0
    assert abs(jp_music["domain_subindex_score"] - 90.0) < 1e-6
    assert "Global_Media_Attention" in jp_music["missing_signals"]


def test_domain_subindex_marks_missing_when_all_signals_missing():
    cfg = load_config()
    month = parse_month("2099-02")
    signal_df = pd.DataFrame(columns=["country_code", "country_name", "domain_code", "signal_type", "sub_index", "signal_score"])
    df = compute_domain_subindex_scores(cfg=cfg, month=month, signal_df=signal_df)
    assert df["domain_subindex_score"].isna().all()
