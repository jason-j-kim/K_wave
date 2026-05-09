"""Aggregate the long-format collected metrics produced by the collectors.

Generates:
  data/processed/monthly_metrics_YYYY_MM.csv  -- already produced by the
    collect step; this module re-loads, validates, and may add per-source
    summaries.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from ..dates import MonthRange
from ..utils import CANONICAL_COLUMNS, processed_dir


def load_monthly_metrics(month: MonthRange) -> pd.DataFrame:
    path = processed_dir() / f"monthly_metrics_{month.file_label}.csv"
    if not path.exists():
        return pd.DataFrame(columns=CANONICAL_COLUMNS)
    return pd.read_csv(path)


def aggregate_for_month(month: MonthRange, logger=None) -> pd.DataFrame:
    """Reload and lightly validate the monthly metrics CSV."""
    df = load_monthly_metrics(month)
    if df.empty:
        if logger:
            logger.warning("No metrics found for %s", month.label)
        return df
    required = ["country_code", "domain_code", "signal_type", "metric_name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"monthly metrics CSV missing columns: {missing}")
    if logger:
        logger.info(
            "Loaded %d metric rows for %s (sources=%s)",
            len(df), month.label, sorted(df["source"].dropna().unique().tolist()),
        )
    return df
