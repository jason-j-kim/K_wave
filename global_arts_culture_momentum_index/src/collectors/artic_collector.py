"""Art Institute of Chicago collector."""
from __future__ import annotations

from typing import Any, Dict, List

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

SOURCE = "artic"
API_NAME = "Art Institute of Chicago API"
ENDPOINT = "https://api.artic.edu/api/v1/artworks/search"


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        return []
    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []
    psd = src_cfg.get("produces_signal_per_domain", {}) or {}

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("museum_queries", []))
            if not queries:
                continue
            total = 0
            errors = 0
            per_q: Dict[str, Any] = {}
            for q in queries:
                data = http_get_json(ENDPOINT, params={"q": q, "limit": 1}, timeout=30, retries=3, logger=logger)
                if data is None:
                    errors += 1
                    per_q[q] = None
                    continue
                pagination = data.get("pagination", {}) or {}
                tot = int(pagination.get("total", 0) or 0)
                per_q[q] = tot
                total += tot
            raw_blob.setdefault(country_code, {})[domain_code] = per_q
            signal = psd.get(domain_code)
            if not signal:
                continue
            sub_index = subindex_for_signal(cfg, signal, domain_code) or "GAC_Institutional"
            query_label = " | ".join(queries)
            status = "ok" if errors == 0 else ("partial" if errors < len(queries) else "missing")
            out.append(make_record(
                cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                signal_type=signal, sub_index=sub_index,
                metric_name="artic_result_count",
                raw_value=float(total) if errors < len(queries) else None,
                source=SOURCE, api_name=API_NAME, api_endpoint=ENDPOINT,
                query=query_label, query_type="museum_queries",
                status=status, notes=f"errors={errors}/{len(queries)}",
                is_domain_specific_source=True,
            ))

    save_json(raw_blob, raw_dir(SOURCE) / f"artic_{month.file_label}.json")
    return out
