"""GDELT DOC 2.0 collector.

Produces ``Global_Media_Attention`` for all 10 domains. URL-level
deduplication (mode=ArtList) is preferred; ``mode=TimelineVolRaw`` is used
as a sanity check or fallback.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

API_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
SOURCE = "gdelt"
SIGNAL = "Global_Media_Attention"
API_NAME = "GDELT DOC 2.0"

# Reasonable safety cap to keep responses bounded; if results would exceed
# this, we annotate the record so the analyst knows the count is censored.
ARTLIST_MAX = 250


def _query_artlist(query: str, start: str, end: str, logger=None) -> Optional[List[Dict[str, Any]]]:
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": ARTLIST_MAX,
        "startdatetime": start,
        "enddatetime": end,
        "sort": "DateDesc",
    }
    data = http_get_json(API_ENDPOINT, params=params, timeout=45, retries=3, logger=logger)
    if data is None:
        return None
    return data.get("articles", []) or []


def _query_timeline_volume(query: str, start: str, end: str, logger=None) -> Optional[float]:
    params = {
        "query": query,
        "mode": "TimelineVolRaw",
        "format": "json",
        "startdatetime": start,
        "enddatetime": end,
    }
    data = http_get_json(API_ENDPOINT, params=params, timeout=45, retries=3, logger=logger)
    if data is None:
        return None
    timeline = data.get("timeline") or []
    total = 0.0
    for series in timeline:
        for entry in series.get("data", []) or []:
            try:
                total += float(entry.get("value", 0.0))
            except (TypeError, ValueError):
                continue
    return total


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        if logger:
            logger.info("GDELT disabled by config")
        return []

    start, end = month.gdelt_range()
    raw_path = raw_dir(SOURCE) / f"gdelt_{month.file_label}.json"
    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("gdelt_queries", []))
            if not queries:
                if logger:
                    logger.warning("GDELT: no queries for %s/%s", country_code, domain_code)
                continue
            seen_urls = set()
            article_count = 0
            source_set = set()
            volume_estimate = 0.0
            had_artlist = False
            had_volume = False
            errors = 0

            for q in queries:
                articles = _query_artlist(q, start, end, logger=logger)
                if articles is None:
                    errors += 1
                    vol = _query_timeline_volume(q, start, end, logger=logger)
                    if vol is not None:
                        volume_estimate += vol
                        had_volume = True
                    continue
                had_artlist = True
                for art in articles:
                    url = art.get("url") or art.get("documentidentifier")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    article_count += 1
                    domain_name = art.get("domain") or art.get("sourcecountry") or ""
                    if domain_name:
                        source_set.add(domain_name)

                raw_blob.setdefault(country_code, {}).setdefault(domain_code, {}).setdefault("artlist", {})[q] = articles

            sub_index = subindex_for_signal(cfg, SIGNAL, domain_code) or "GAC_Attention"
            query_label = " | ".join(queries)
            if had_artlist:
                out.append(
                    make_record(
                        cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                        signal_type=SIGNAL, sub_index=sub_index,
                        metric_name="gdelt_article_count_dedup",
                        raw_value=float(article_count),
                        source=SOURCE, api_name=API_NAME, api_endpoint=API_ENDPOINT,
                        query=query_label, query_type="gdelt_queries",
                        status="ok" if errors == 0 else "partial",
                        notes=f"errors={errors}; cap={ARTLIST_MAX}/query",
                    )
                )
                out.append(
                    make_record(
                        cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                        signal_type=SIGNAL, sub_index=sub_index,
                        metric_name="gdelt_source_count_dedup",
                        raw_value=float(len(source_set)),
                        source=SOURCE, api_name=API_NAME, api_endpoint=API_ENDPOINT,
                        query=query_label, query_type="gdelt_queries",
                        status="ok" if errors == 0 else "partial",
                        notes="distinct news sources after URL-level dedup",
                    )
                )
            elif had_volume:
                out.append(
                    make_record(
                        cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                        signal_type=SIGNAL, sub_index=sub_index,
                        metric_name="gdelt_volume_estimate",
                        raw_value=float(volume_estimate),
                        source=SOURCE, api_name=API_NAME, api_endpoint=API_ENDPOINT,
                        query=query_label, query_type="gdelt_queries",
                        status="fallback",
                        notes="ArtList unavailable; using TimelineVolRaw fallback",
                    )
                )
            else:
                out.append(
                    make_record(
                        cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                        signal_type=SIGNAL, sub_index=sub_index,
                        metric_name="gdelt_article_count_dedup",
                        raw_value=None,
                        source=SOURCE, api_name=API_NAME, api_endpoint=API_ENDPOINT,
                        query=query_label, query_type="gdelt_queries",
                        status="missing",
                        notes="all GDELT queries failed",
                    )
                )

    save_json(raw_blob, raw_path)
    return out
