"""Open Library Search collector."""
from __future__ import annotations

from typing import Any, Dict, List

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

SOURCE = "openlibrary"
SIGNAL = "Book_Discoverability"
API_NAME = "Open Library Search"
ENDPOINT = "https://openlibrary.org/search.json"


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        return []
    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("book_queries", []))
            if not queries:
                continue
            total_num_found = 0
            total_works = 0
            errors = 0
            per_q: Dict[str, Any] = {}
            for q in queries:
                data = http_get_json(ENDPOINT, params={"q": q, "limit": 50}, timeout=30, retries=3, logger=logger)
                if data is None:
                    errors += 1
                    per_q[q] = None
                    continue
                num_found = int(data.get("numFound", data.get("num_found", 0) or 0) or 0)
                docs = data.get("docs", []) or []
                total_num_found += num_found
                total_works += len(docs)
                per_q[q] = {"numFound": num_found, "returned": len(docs)}
            raw_blob.setdefault(country_code, {})[domain_code] = per_q
            sub_index = subindex_for_signal(cfg, SIGNAL, domain_code) or "GAC_Discoverability"
            query_label = " | ".join(queries)
            status = "ok" if errors == 0 else ("partial" if errors < len(queries) else "missing")

            out.append(make_record(
                cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                signal_type=SIGNAL, sub_index=sub_index,
                metric_name="openlibrary_num_found",
                raw_value=float(total_num_found) if errors < len(queries) else None,
                source=SOURCE, api_name=API_NAME, api_endpoint=ENDPOINT,
                query=query_label, query_type="book_queries",
                status=status, notes=f"errors={errors}/{len(queries)}",
            ))
            out.append(make_record(
                cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                signal_type=SIGNAL, sub_index=sub_index,
                metric_name="openlibrary_work_count",
                raw_value=float(total_works) if errors < len(queries) else None,
                source=SOURCE, api_name=API_NAME, api_endpoint=ENDPOINT,
                query=query_label, query_type="book_queries",
                status=status, notes="capped at 50 docs/query",
            ))

    save_json(raw_blob, raw_dir(SOURCE) / f"openlibrary_{month.file_label}.json")
    return out
