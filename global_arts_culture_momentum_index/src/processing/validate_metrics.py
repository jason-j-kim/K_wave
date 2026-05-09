"""Sanity checks for the collected metrics CSV."""
from __future__ import annotations

from typing import List

import pandas as pd


def validate(df: pd.DataFrame) -> List[str]:
    """Return a list of warning messages found in the metrics dataframe."""
    warnings: List[str] = []
    if df.empty:
        warnings.append("metrics dataframe is empty")
        return warnings
    if df["raw_value"].isna().mean() > 0.8:
        warnings.append("more than 80% of raw_value entries are missing")
    for col in ["month", "country_code", "domain_code", "signal_type"]:
        if df[col].isna().any():
            warnings.append(f"null values in {col}")
    return warnings
