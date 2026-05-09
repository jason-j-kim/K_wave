"""Confidence scores per sub-index and composite.

For a sub-index, the confidence is

  100 * Σ_available (domain_w * signal_w * src_conf_mult)
        / Σ_expected  (domain_w * signal_w * src_conf_mult)

Domain weights within a sub-index are equal. Signal weights come from
``config/weights.yml``. The source-confidence multiplier comes from the
canonical source for each (signal, domain) pair.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import output_dir


def _canonical_source_for_signal_domain(cfg: Config, signal: str, domain: str) -> Optional[str]:
    candidates = cfg.source_for_signal(signal, domain=domain)
    candidates = [c for c in candidates if cfg.sources.get(c, {}).get("enabled", False)]
    if not candidates:
        # Fall back to any candidate so we still have a multiplier baseline.
        all_candidates = cfg.source_for_signal(signal, domain=domain)
        if not all_candidates:
            return None
        return all_candidates[0]
    return candidates[0]


def compute_confidences(
    cfg: Config, month: MonthRange,
    domain_df: pd.DataFrame,
    logger=None,
) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    coverage_rows: List[Dict[str, object]] = []
    composite_weights = cfg.composite_weights

    composite_per_country: Dict[str, Dict[str, float]] = {}

    for sub_index in cfg.sub_index_names():
        sub_domains = cfg.sub_index_domains(sub_index)
        n_domains = len(sub_domains)
        if n_domains == 0:
            continue
        domain_w = 1.0 / n_domains
        for country in cfg.country_codes():
            expected = 0.0
            available = 0.0
            avail_signals: List[str] = []
            missing_signals: List[str] = []
            for domain in sub_domains:
                weights = cfg.domain_subindex_signal_map(sub_index, domain)
                # Find the row(s) of available signals for this country/domain/sub_index
                row = domain_df[
                    (domain_df["country_code"] == country)
                    & (domain_df["sub_index"] == sub_index)
                    & (domain_df["domain_code"] == domain)
                ]
                avail_set: set = set()
                if not row.empty:
                    avail_str = row.iloc[0].get("available_signals", "") or ""
                    avail_set = {s for s in avail_str.split(",") if s}
                for signal, sw in weights.items():
                    src = _canonical_source_for_signal_domain(cfg, signal, domain)
                    mult = cfg.source_confidence_multiplier(src) if src else 1.0
                    weight_term = domain_w * sw * mult
                    expected += weight_term
                    if signal in avail_set:
                        available += weight_term
                        avail_signals.append(f"{domain}:{signal}")
                    else:
                        missing_signals.append(f"{domain}:{signal}")
            confidence = (100.0 * available / expected) if expected > 0 else 0.0
            rows.append({
                "month": month.label,
                "country_code": country,
                "country_name": cfg.countries[country]["name"],
                "sub_index": sub_index,
                "confidence": confidence,
                "available_signals": ";".join(avail_signals),
                "missing_signals": ";".join(missing_signals),
            })
            composite_per_country.setdefault(country, {})[sub_index] = confidence
            # coverage row: how many domains had at least one available signal
            coverage_rows.append({
                "month": month.label,
                "country_code": country,
                "country_name": cfg.countries[country]["name"],
                "sub_index": sub_index,
                "n_expected_domains": n_domains,
                "n_domains_with_data": int(((domain_df["country_code"] == country)
                                            & (domain_df["sub_index"] == sub_index)
                                            & (domain_df["domain_subindex_score"].notna())).sum()),
            })

    # Composite confidence: weighted mean of sub-index confidences with
    # the same composite weights as the score (redistributed if missing).
    for country, sub_conf in composite_per_country.items():
        wsum = 0.0
        weighted = 0.0
        for sub, w in composite_weights.items():
            c = sub_conf.get(sub)
            if c is None:
                continue
            wsum += w
            weighted += c * w
        composite_conf = (weighted / wsum) if wsum > 0 else 0.0
        rows.append({
            "month": month.label,
            "country_code": country,
            "country_name": cfg.countries[country]["name"],
            "sub_index": "GACMI_Composite",
            "confidence": composite_conf,
            "available_signals": "",
            "missing_signals": "",
        })

    df = pd.DataFrame(rows)
    coverage_df = pd.DataFrame(coverage_rows)
    coverage_df.to_csv(output_dir() / f"data_coverage_{month.file_label}.csv", index=False)
    if logger:
        logger.info("Wrote confidence rows=%d, coverage rows=%d", len(df), len(coverage_df))
    return df
