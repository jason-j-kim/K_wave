"""Google Books Volumes collector."""
from __future__ import annotations

from typing import Any, Dict, List

from ..config_loader import Config, get_env
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

SOURCE = "google_books"
SIGNAL = "Book_Discoverability"
API_NAME = "Google Books Volumes API"
ENDPOINT = "https://www.googleapis.com/books/v1/volumes"


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        return []

    api_key = get_env("GOOGLE_BOOKS_API_KEY")
    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("book_queries", []))
            if not queries:
                continue
            total_items = 0
            returned_items = 0
            errors = 0
            per_q: Dict[str, Any] = {}
            for q in queries:
                params: Dict[str, Any] = {"q": q, "maxResults": 40, "printType": "books"}
                if api_key:
                    params["key"] = api_key
                data = http_get_json(ENDPOINT, params=params, timeout=30, retries=3, logger=logger)
                if data is None:
                    errors += 1
                    per_q[q] = None
                    continue
                ti = int(data.get("totalItems", 0) or 0)
                items = data.get("items", []) or []
                total_items += ti
                returned_items += len(items)
                per_q[q] = {"totalItems": ti, "returned": len(items)}
            raw_blob.setdefault(country_code, {})[domain_code] = per_q
            sub_index = subindex_for_signal(cfg, SIGNAL, domain_code) or "GAC_Discoverability"
            query_label = " | ".join(queries)
            status = "ok" if errors == 0 else ("partial" if errors < len(queries) else "missing")

            out.append(make_record(
                cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                signal_type=SIGNAL, sub_index=sub_index,
                metric_name="google_books_total_items",
                raw_value=float(total_items) if errors < len(queries) else None,
                source=SOURCE, api_name=API_NAME, api_endpoint=ENDPOINT,
                query=query_label, query_type="book_queries",
                status=status, notes=f"errors={errors}/{len(queries)}",
            ))
            out.append(make_record(
                cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                signal_type=SIGNAL, sub_index=sub_index,
                metric_name="google_books_returned_items",
                raw_value=float(returned_items) if errors < len(queries) else None,
                source=SOURCE, api_name=API_NAME, api_endpoint=ENDPOINT,
                query=query_label, query_type="book_queries",
                status=status, notes="capped at 40 per query",
            ))

    save_json(raw_blob, raw_dir(SOURCE) / f"google_books_{month.file_label}.json")
    return out
