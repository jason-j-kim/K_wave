"""Aggregate domain × sub-index scores into per-country sub-index scores.

Domains within a sub-index have equal weight. Missing domain cells trigger
weight redistribution; if every domain is missing, the country/sub-index
cell is null.
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import output_dir


def compute_subindex_scores(
    cfg: Config, month: MonthRange, domain_df: pd.DataFrame, logger=None
) -> pd.DataFrame:
    rows: List[dict] = []

    for sub_index in cfg.sub_index_names():
        sub_domains = cfg.sub_index_domains(sub_index)
        n_domains = len(sub_domains)
        if n_domains == 0:
            continue
        for country in cfg.country_codes():
            sub_rows = domain_df[
                (domain_df["country_code"] == country)
                & (domain_df["sub_index"] == sub_index)
                & (domain_df["domain_code"].isin(sub_domains))
            ]
            avail = sub_rows[sub_rows["domain_subindex_score"].notna()]
            missing_domains = [d for d in sub_domains if d not in set(avail["domain_code"])]
            if avail.empty:
                rows.append({
                    "month": month.label,
                    "country_code": country,
                    "country_name": cfg.countries[country]["name"],
                    "sub_index": sub_index,
                    "subindex_score": None,
                    "available_domains": "",
                    "missing_domains": ",".join(missing_domains),
                    "n_available_domains": 0,
                    "n_expected_domains": n_domains,
                })
                continue
            # equal weights, redistributed across available domains
            score = float(avail["domain_subindex_score"].mean())
            rows.append({
                "month": month.label,
                "country_code": country,
                "country_name": cfg.countries[country]["name"],
                "sub_index": sub_index,
                "subindex_score": score,
                "available_domains": ",".join(sorted(avail["domain_code"].tolist())),
                "missing_domains": ",".join(missing_domains),
                "n_available_domains": int(len(avail)),
                "n_expected_domains": n_domains,
            })

    df = pd.DataFrame(rows)
    out_path = output_dir() / f"subindex_scores_{month.file_label}.csv"
    df.to_csv(out_path, index=False)
    if logger:
        logger.info("Wrote sub-index scores: %s (%d rows)", out_path, len(df))
    return df
