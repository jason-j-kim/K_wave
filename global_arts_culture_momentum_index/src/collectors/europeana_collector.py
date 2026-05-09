"""Europeana Search collector (optional)."""
from __future__ import annotations

from typing import Any, Dict, List

from ..config_loader import Config, get_env
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

SOURCE = "europeana"
SIGNAL = "Cultural_Heritage_Database_Visibility"
API_NAME = "Europeana Search"
ENDPOINT = "https://api.europeana.eu/record/v2/search.json"


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        if logger:
            logger.info("Europeana disabled by config; skipping")
        return []
    api_key = get_env(src_cfg.get("env_key", "EUROPEANA_API_KEY"))
    if not api_key:
        if logger:
            logger.info("Europeana API key missing; skipping")
        return []

    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("museum_queries", [])) or list(basket.get("wikidata_queries", []))
            if not queries:
                continue
            total = 0
            errors = 0
            per_q: Dict[str, Any] = {}
            for q in queries:
                data = http_get_json(ENDPOINT, params={"wskey": api_key, "query": q, "rows": 1}, timeout=30, retries=2, logger=logger)
                if data is None:
                    errors += 1
                    per_q[q] = None
                    continue
                t = int(data.get("totalResults", 0) or 0)
                per_q[q] = t
                total += t
            raw_blob.setdefault(country_code, {})[domain_code] = per_q
            sub_index = subindex_for_signal(cfg, SIGNAL, domain_code) or "GAC_Institutional"
            query_label = " | ".join(queries)
            status = "ok" if errors == 0 else ("partial" if errors < len(queries) else "missing")
            out.append(make_record(
                cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                signal_type=SIGNAL, sub_index=sub_index,
                metric_name="europeana_result_count",
                raw_value=float(total) if errors < len(queries) else None,
                source=SOURCE, api_name=API_NAME, api_endpoint=ENDPOINT,
                query=query_label, query_type="museum_queries",
                status=status, notes=f"errors={errors}/{len(queries)}",
            ))

    save_json(raw_blob, raw_dir(SOURCE) / f"europeana_{month.file_label}.json")
    return out
