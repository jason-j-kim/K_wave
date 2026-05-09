"""Wikipedia Pageviews collector (English, all-access, all-agents)."""
from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import quote

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

SOURCE = "wikipedia"
SIGNAL = "Wikipedia_Attention"
API_NAME = "Wikimedia REST API"
BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents"


def _fetch_page_views(article: str, start: str, end: str, logger=None) -> Dict[str, Any] | None:
    article_enc = quote(article, safe="")
    url = f"{BASE}/{article_enc}/monthly/{start}/{end}"
    return http_get_json(url, timeout=30, retries=3, logger=logger)


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        return []

    start, end = month.wikipedia_range()
    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            pages: List[str] = list(basket.get("wikipedia_pages", []))
            if not pages:
                if logger:
                    logger.warning("Wikipedia: no pages for %s/%s", country_code, domain_code)
                continue
            total_views = 0.0
            page_count_with_data = 0
            page_views: Dict[str, Any] = {}
            errors = 0
            for page in pages:
                data = _fetch_page_views(page, start, end, logger=logger)
                if data is None or "items" not in data:
                    errors += 1
                    page_views[page] = None
                    continue
                pv = sum(int(it.get("views", 0)) for it in data.get("items", []))
                page_views[page] = pv
                total_views += pv
                page_count_with_data += 1
            raw_blob.setdefault(country_code, {})[domain_code] = page_views

            sub_index = subindex_for_signal(cfg, SIGNAL, domain_code) or "GAC_Attention"
            query_label = " | ".join(pages)
            status = "ok" if errors == 0 else ("partial" if page_count_with_data > 0 else "missing")
            out.append(
                make_record(
                    cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                    signal_type=SIGNAL, sub_index=sub_index,
                    metric_name="wikipedia_pageviews",
                    raw_value=float(total_views) if page_count_with_data > 0 else None,
                    source=SOURCE, api_name=API_NAME, api_endpoint=BASE,
                    query=query_label, query_type="wikipedia_pages",
                    status=status,
                    notes=f"{page_count_with_data}/{len(pages)} pages had data; errors={errors}",
                )
            )

    save_json(raw_blob, raw_dir(SOURCE) / f"wikipedia_{month.file_label}.json")
    return out
