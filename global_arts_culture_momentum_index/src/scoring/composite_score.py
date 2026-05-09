"""Composite GACMI computation."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import output_dir


def _weighted_with_redistribution(
    weights: Dict[str, float], values: Dict[str, float]
) -> float | None:
    avail = {k: w for k, w in weights.items() if k in values and values[k] is not None and not (isinstance(values[k], float) and np.isnan(values[k]))}
    if not avail:
        return None
    total = sum(avail.values())
    if total == 0:
        return None
    return sum((w / total) * values[k] for k, w in avail.items())


def compute_composite(
    cfg: Config, month: MonthRange,
    subindex_df: pd.DataFrame,
    confidences: pd.DataFrame,
    logger=None,
) -> pd.DataFrame:
    weights = cfg.composite_weights
    rows: List[dict] = []

    sub_lookup = {(r["country_code"], r["sub_index"]): r for _, r in subindex_df.iterrows()}
    conf_lookup = {(r["country_code"], r["sub_index"]): r for _, r in confidences.iterrows() if r["sub_index"] != "GACMI_Composite"}
    composite_conf_lookup = {r["country_code"]: r for _, r in confidences.iterrows() if r["sub_index"] == "GACMI_Composite"}

    # Previous-month composite for MoM change.
    prev_path = output_dir() / f"gacmi_composite_{month.previous().file_label}.csv"
    prev_df = pd.read_csv(prev_path) if prev_path.exists() else pd.DataFrame()

    for country in cfg.country_codes():
        sub_values = {}
        sub_avail_domains: Dict[str, str] = {}
        sub_missing_domains: Dict[str, str] = {}
        for sub_index in weights.keys():
            row = sub_lookup.get((country, sub_index))
            if row is not None:
                sub_values[sub_index] = row["subindex_score"]
                sub_avail_domains[sub_index] = row.get("available_domains", "")
                sub_missing_domains[sub_index] = row.get("missing_domains", "")
            else:
                sub_values[sub_index] = None
        composite = _weighted_with_redistribution(weights, sub_values)

        record: Dict[str, object] = {
            "month": month.label,
            "country_code": country,
            "country_name": cfg.countries[country]["name"],
            "gacmi_composite": composite,
            "gac_attention": sub_values.get("GAC_Attention"),
            "gac_discoverability": sub_values.get("GAC_Discoverability"),
            "gac_institutional": sub_values.get("GAC_Institutional"),
        }
        for sub in weights.keys():
            crow = conf_lookup.get((country, sub))
            record[f"confidence_{sub.lower().replace('gac_', '')}"] = (
                float(crow["confidence"]) if crow is not None else None
            )
        crow = composite_conf_lookup.get(country)
        record["confidence_composite"] = float(crow["confidence"]) if crow is not None else None

        avail_domains_set: set = set()
        missing_domains_set: set = set()
        for sub in sub_avail_domains.values():
            if sub:
                avail_domains_set.update([d for d in sub.split(",") if d])
        for sub in sub_missing_domains.values():
            if sub:
                missing_domains_set.update([d for d in sub.split(",") if d])
        record["available_domains"] = ",".join(sorted(avail_domains_set))
        record["missing_domains"] = ",".join(sorted(missing_domains_set))

        if not prev_df.empty:
            prev = prev_df[prev_df["country_code"] == country]
            if not prev.empty:
                p = prev.iloc[0]
                def _diff(cur, col):
                    pv = p.get(col)
                    if pv is None or (isinstance(pv, float) and np.isnan(pv)):
                        return None
                    if cur is None or (isinstance(cur, float) and np.isnan(cur)):
                        return None
                    return float(cur) - float(pv)
                record["mom_change_composite"] = _diff(record["gacmi_composite"], "gacmi_composite")
                record["mom_change_attention"] = _diff(record["gac_attention"], "gac_attention")
                record["mom_change_discoverability"] = _diff(record["gac_discoverability"], "gac_discoverability")
                record["mom_change_institutional"] = _diff(record["gac_institutional"], "gac_institutional")
            else:
                record["mom_change_composite"] = None
                record["mom_change_attention"] = None
                record["mom_change_discoverability"] = None
                record["mom_change_institutional"] = None
        else:
            record["mom_change_composite"] = None
            record["mom_change_attention"] = None
            record["mom_change_discoverability"] = None
            record["mom_change_institutional"] = None
        # YoY reserved for v0.2+
        record["yoy_change_composite"] = None
        rows.append(record)

    df = pd.DataFrame(rows)
    df = df.sort_values("gacmi_composite", ascending=False, na_position="last").reset_index(drop=True)
    df.insert(1, "rank", df["gacmi_composite"].rank(ascending=False, method="min").astype("Int64"))

    cols = [
        "month", "rank", "country_code", "country_name",
        "gacmi_composite", "gac_attention", "gac_discoverability", "gac_institutional",
        "confidence_composite", "confidence_attention", "confidence_discoverability", "confidence_institutional",
        "available_domains", "missing_domains",
        "mom_change_composite", "mom_change_attention", "mom_change_discoverability", "mom_change_institutional",
        "yoy_change_composite",
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]

    out_path = output_dir() / f"gacmi_composite_{month.file_label}.csv"
    df.to_csv(out_path, index=False)
    if logger:
        logger.info("Wrote composite GACMI: %s (%d rows)", out_path, len(df))
    return df
