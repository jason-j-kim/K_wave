"""Tests for the confidence-score formula."""
import pandas as pd

from src.config_loader import load_config
from src.dates import parse_month
from src.scoring.confidence_scores import compute_confidences


def test_confidence_full_data_is_100():
    cfg = load_config()
    month = parse_month("2099-05")
    rows = []
    for sub_index in cfg.sub_index_names():
        for domain in cfg.sub_index_domains(sub_index):
            sigs = list(cfg.domain_subindex_signal_map(sub_index, domain).keys())
            rows.append({
                "country_code": "KR", "country_name": "Korea",
                "domain_code": domain, "sub_index": sub_index,
                "domain_subindex_score": 50.0,
                "available_signals": ",".join(sigs),
                "missing_signals": "",
                "n_available": len(sigs),
                "n_expected": len(sigs),
            })
    df = pd.DataFrame(rows)
    conf = compute_confidences(cfg=cfg, month=month, domain_df=df)
    kr = conf[conf["country_code"] == "KR"]
    sub_conf = kr[kr["sub_index"] != "GACMI_Composite"]
    # All available -> confidence approaches 100 (medium multiplier = 1.0).
    for _, r in sub_conf.iterrows():
        assert abs(r["confidence"] - 100.0) < 0.01


def test_confidence_drops_when_signals_missing():
    cfg = load_config()
    month = parse_month("2099-05")
    rows = []
    for sub_index in cfg.sub_index_names():
        for domain in cfg.sub_index_domains(sub_index):
            sigs = list(cfg.domain_subindex_signal_map(sub_index, domain).keys())
            rows.append({
                "country_code": "KR", "country_name": "Korea",
                "domain_code": domain, "sub_index": sub_index,
                "domain_subindex_score": 50.0,
                "available_signals": "",
                "missing_signals": ",".join(sigs),
                "n_available": 0,
                "n_expected": len(sigs),
            })
    df = pd.DataFrame(rows)
    conf = compute_confidences(cfg=cfg, month=month, domain_df=df)
    kr = conf[(conf["country_code"] == "KR") & (conf["sub_index"] != "GACMI_Composite")]
    assert (kr["confidence"] == 0).all()
