"""Compute domain × sub-index scores from signal scores.

Within each (country, domain, sub_index, month) cell, signals are weighted
according to ``config/weights.yml``. If a signal is missing, its weight is
redistributed proportionally across available signals in the same cell.
If all signals for the cell are missing, the cell value is null.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import output_dir


def _weighted_score(weights: Dict[str, float], scores: Dict[str, float]) -> float | None:
    """Compute weighted average over the *available* (non-null) signals.

    Missing signals are dropped and the remaining weights renormalized.
    """
    avail = {k: v for k, v in weights.items() if k in scores and scores[k] is not None and not (isinstance(scores[k], float) and np.isnan(scores[k]))}
    if not avail:
        return None
    total_w = sum(avail.values())
    if total_w == 0:
        return None
    return sum((w / total_w) * scores[k] for k, w in avail.items())


def compute_domain_subindex_scores(
    cfg: Config, month: MonthRange, signal_df: pd.DataFrame, logger=None
) -> pd.DataFrame:
    rows: List[Dict[str, float | str | None]] = []

    # Build a fast lookup: (country, domain, signal) -> signal_score
    score_map: Dict[tuple, float] = {}
    for _, r in signal_df.iterrows():
        key = (r["country_code"], r["domain_code"], r["signal_type"])
        score_map[key] = r["signal_score"]

    for sub_index in cfg.sub_index_names():
        domains = cfg.sub_index_domains(sub_index)
        for country in cfg.country_codes():
            for domain in domains:
                weights = cfg.domain_subindex_signal_map(sub_index, domain)
                if not weights:
                    continue
                scores = {}
                missing_signals: List[str] = []
                avail_signals: List[str] = []
                for signal in weights.keys():
                    val = score_map.get((country, domain, signal))
                    if val is None or (isinstance(val, float) and np.isnan(val)):
                        missing_signals.append(signal)
                    else:
                        scores[signal] = float(val)
                        avail_signals.append(signal)
                value = _weighted_score(weights, scores)
                rows.append({
                    "month": month.label,
                    "country_code": country,
                    "country_name": cfg.countries[country]["name"],
                    "domain_code": domain,
                    "sub_index": sub_index,
                    "domain_subindex_score": value,
                    "available_signals": ",".join(avail_signals),
                    "missing_signals": ",".join(missing_signals),
                    "n_available": len(avail_signals),
                    "n_expected": len(weights),
                })

    df = pd.DataFrame(rows)
    out_path = output_dir() / f"domain_subindex_scores_{month.file_label}.csv"
    df.to_csv(out_path, index=False)
    if logger:
        logger.info("Wrote domain x sub-index scores: %s (%d rows)", out_path, len(df))
    return df
