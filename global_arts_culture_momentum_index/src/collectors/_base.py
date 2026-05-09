"""Shared collector helpers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import CollectorRecord, now_iso


def make_record(
    *,
    cfg: Config,
    month: MonthRange,
    country_code: str,
    domain_code: str,
    signal_type: str,
    sub_index: str,
    metric_name: str,
    raw_value: Optional[float],
    source: str,
    api_name: str,
    api_endpoint: str,
    query: str,
    query_type: str,
    status: str,
    notes: str = "",
    is_domain_specific_source: bool = False,
) -> Dict[str, Any]:
    country = cfg.countries.get(country_code, {})
    domain = cfg.domains.get(domain_code, {})
    src_cfg = cfg.sources.get(source, {}) or {}
    signal_cfg = cfg.signals.get(signal_type, {}) or {}
    rec = CollectorRecord(
        month=month.label,
        country_code=country_code,
        country_name=country.get("name", country_code),
        domain_code=domain_code,
        domain_name=domain.get("name", domain_code),
        signal_type=signal_type,
        sub_index=sub_index,
        metric_name=metric_name,
        raw_value=raw_value,
        source=source,
        api_name=api_name,
        api_endpoint=api_endpoint,
        query=query,
        query_type=query_type,
        collected_at=now_iso(),
        status=status,
        notes=notes,
        is_domain_specific_source=is_domain_specific_source,
        requires_api_key=bool(src_cfg.get("requires_api_key", False)),
        source_confidence_level=src_cfg.get("source_confidence_level", "medium"),
        flow_type=signal_cfg.get("flow_type", "monthly_flow"),
    )
    return rec.to_dict()


def applicable_country_domain_pairs(cfg: Config, source_name: str) -> List[tuple]:
    src_cfg = cfg.sources.get(source_name, {}) or {}
    domains = src_cfg.get("applicable_domains", [])
    return [(c, d) for c in cfg.country_codes() for d in domains]


def subindex_for_signal(cfg: Config, signal: str, domain: str) -> Optional[str]:
    """Return the sub-index a (signal, domain) pair belongs to."""
    for sub_index in cfg.sub_index_names():
        sigs = cfg.sub_index_signals(sub_index)
        doms = cfg.sub_index_domains(sub_index)
        if signal in sigs and domain in doms:
            return sub_index
    return None
