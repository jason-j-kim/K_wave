"""Test that signal scores correctly aggregate normalized metrics."""
from pathlib import Path

import pandas as pd

from src.config_loader import load_config
from src.dates import parse_month
from src.scoring.signal_scores import compute_signal_scores
from src.utils import CANONICAL_COLUMNS, processed_dir, output_dir


def _seed_metrics(month_label: str, file_label: str) -> Path:
    rows = []
    countries = ["KR", "JP", "US"]
    for i, c in enumerate(countries):
        # GDELT-like metric for Music
        rows.append({
            "month": month_label, "country_code": c, "country_name": c,
            "domain_code": "Music", "domain_name": "Music",
            "signal_type": "Global_Media_Attention", "sub_index": "GAC_Attention",
            "metric_name": "gdelt_article_count_dedup",
            "raw_value": 10.0 * (i + 1), "source": "gdelt", "api_name": "g",
            "api_endpoint": "x", "query": "q", "query_type": "gdelt_queries",
            "collected_at": "now", "status": "ok", "notes": "",
            "is_domain_specific_source": False, "requires_api_key": False,
            "source_confidence_level": "medium", "flow_type": "monthly_flow",
        })
        # Wikipedia metric for Music
        rows.append({
            "month": month_label, "country_code": c, "country_name": c,
            "domain_code": "Music", "domain_name": "Music",
            "signal_type": "Wikipedia_Attention", "sub_index": "GAC_Attention",
            "metric_name": "wikipedia_pageviews",
            "raw_value": 100.0 * (3 - i), "source": "wikipedia", "api_name": "w",
            "api_endpoint": "x", "query": "q", "query_type": "wikipedia_pages",
            "collected_at": "now", "status": "ok", "notes": "",
            "is_domain_specific_source": False, "requires_api_key": False,
            "source_confidence_level": "medium", "flow_type": "monthly_flow",
        })
    df = pd.DataFrame(rows)
    df = df.reindex(columns=CANONICAL_COLUMNS)
    path = processed_dir() / f"monthly_metrics_{file_label}.csv"
    df.to_csv(path, index=False)
    return path


def test_signal_scores_per_country_domain(tmp_path, monkeypatch):
    cfg = load_config()
    month = parse_month("2099-01")
    _seed_metrics(month.label, month.file_label)
    df = compute_signal_scores(cfg=cfg, month=month, logger=None)
    music = df[df["domain_code"] == "Music"]
    # Two signal types
    assert set(music["signal_type"]) >= {"Global_Media_Attention", "Wikipedia_Attention"}
    # Country with highest GDELT raw should have highest GMA score
    gma = music[music["signal_type"] == "Global_Media_Attention"].set_index("country_code")
    assert gma.loc["US", "signal_score"] > gma.loc["KR", "signal_score"]
