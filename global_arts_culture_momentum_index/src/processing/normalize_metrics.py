"""Normalization utilities for GACMI."""
from __future__ import annotations

import math
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd


def log_transform(values: Iterable[float]) -> List[float]:
    """Apply ln(1 + x) elementwise. ``None`` and NaN pass through."""
    out: List[float] = []
    for v in values:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            out.append(float("nan"))
        else:
            out.append(math.log1p(max(0.0, float(v))))
    return out


def percentile_rank(series: pd.Series) -> pd.Series:
    """Empirical percentile rank using (rank - 1) / (N - 1) * 100.

    ``N`` is the count of non-null values. Ties use the average rank.
    Returns 50.0 for the single-value case (no spread to rank against).
    Values that are NaN remain NaN.
    """
    valid_mask = series.notna()
    valid = series[valid_mask]
    n = len(valid)
    out = pd.Series(index=series.index, dtype="float64")
    out[:] = np.nan
    if n == 0:
        return out
    if n == 1:
        out.loc[valid.index] = 50.0
        return out
    ranks = valid.rank(method="average", ascending=True)
    pct = (ranks - 1) / (n - 1) * 100.0
    out.loc[valid.index] = pct.values
    return out


def robust_z_score(series: pd.Series) -> pd.Series:
    """Robust z-score using median and MAD; rescaled to mimic 0..100.

    Used as an alternative normalization. Values are mapped to roughly
    ``50 + 15 * z``, clamped to [0, 100]. NaNs preserved.
    """
    valid_mask = series.notna()
    valid = series[valid_mask]
    n = len(valid)
    out = pd.Series(index=series.index, dtype="float64")
    out[:] = np.nan
    if n == 0:
        return out
    median = float(valid.median())
    mad = float((valid - median).abs().median())
    if mad == 0:
        out.loc[valid.index] = 50.0
        return out
    z = (valid - median) / (1.4826 * mad)
    scaled = 50.0 + 15.0 * z
    scaled = scaled.clip(lower=0.0, upper=100.0)
    out.loc[valid.index] = scaled.values
    return out


def normalize(series: pd.Series, method: str = "percentile_rank") -> pd.Series:
    if method == "percentile_rank":
        return percentile_rank(series)
    if method == "robust_z_score":
        return robust_z_score(series)
    raise ValueError(f"Unknown normalization method: {method}")


def normalize_dataframe(
    df: pd.DataFrame,
    *,
    value_col: str,
    group_cols: List[str],
    method: str = "percentile_rank",
    output_col: Optional[str] = None,
) -> pd.DataFrame:
    """Apply log + group-wise normalization to ``value_col``."""
    if df.empty:
        df = df.copy()
        df[output_col or "normalized"] = pd.Series(dtype="float64")
        return df
    df = df.copy()
    df["_log_value"] = log_transform(df[value_col].tolist())
    out_col = output_col or "normalized"
    df[out_col] = (
        df.groupby(group_cols, dropna=False)["_log_value"]
        .transform(lambda s: normalize(s, method=method))
    )
    df = df.drop(columns=["_log_value"])
    return df
