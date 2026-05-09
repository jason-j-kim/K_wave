"""Signal-level score computation.

For each (country, domain, month, signal_type), the signal score is the
mean of normalized metric values that contribute to that signal type.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..config_loader import Config
from ..dates import MonthRange
from ..processing.aggregate_metrics import load_monthly_metrics
from ..processing.normalize_metrics import normalize_dataframe
from ..utils import output_dir


def compute_signal_scores(cfg: Config, month: MonthRange, logger=None) -> pd.DataFrame:
    """Return long dataframe (country, domain, signal_type, signal_score)."""
    df = load_monthly_metrics(month)
    if df.empty:
        if logger:
            logger.warning("No metrics for %s -- signal scores will be empty", month.label)
        empty = pd.DataFrame(columns=["month", "country_code", "country_name", "domain_code",
                                       "signal_type", "sub_index", "signal_score", "n_metrics"])
        empty.to_csv(output_dir() / f"signal_scores_{month.file_label}.csv", index=False)
        return empty

    # Drop exploratory rows
    df = df[df["sub_index"] != "EXPLORATORY"].copy()
    df = df[df["raw_value"].notna()]

    method = cfg.normalization_method
    if logger:
        logger.info("Normalization method: %s", method)

    df = normalize_dataframe(
        df,
        value_col="raw_value",
        group_cols=["domain_code", "signal_type", "metric_name"],
        method=method,
        output_col="normalized_score",
    )

    grouped = (
        df.groupby(["month", "country_code", "country_name",
                    "domain_code", "domain_name", "signal_type", "sub_index"], dropna=False)
        .agg(signal_score=("normalized_score", "mean"),
             n_metrics=("normalized_score", "count"))
        .reset_index()
    )

    out_path = output_dir() / f"signal_scores_{month.file_label}.csv"
    grouped.to_csv(out_path, index=False)
    if logger:
        logger.info("Wrote signal scores: %s (%d rows)", out_path, len(grouped))
    return grouped
