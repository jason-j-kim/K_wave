"""Ticketmaster Discovery collector (optional)."""
from __future__ import annotations

from typing import Any, Dict, List

from ..config_loader import Config, get_env
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

SOURCE = "ticketmaster"
SIGNAL = "Performing_Event_Visibility"
API_NAME = "Ticketmaster Discovery"
ENDPOINT = "https://app.ticketmaster.com/discovery/v2/events.json"


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        return []
    api_key = get_env(src_cfg.get("env_key", "TICKETMASTER_API_KEY"))
    if not api_key:
        if logger:
            logger.info("Ticketmaster API key missing; skipping")
        return []

    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []
    start = month.first_day.strftime("%Y-%m-%dT00:00:00Z")
    end = month.last_day.strftime("%Y-%m-%dT23:59:59Z")

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("event_queries", []))
            if not queries:
                continue
            event_count = 0
            venues: set = set()
            markets: set = set()
            errors = 0
            per_q: Dict[str, Any] = {}
            for q in queries:
                params = {
                    "apikey": api_key, "keyword": q, "size": 100,
                    "startDateTime": start, "endDateTime": end,
                    "classificationName": "Arts & Theatre",
                }
                data = http_get_json(ENDPOINT, params=params, timeout=30, retries=2, logger=logger)
                if data is None:
                    errors += 1
                    per_q[q] = None
                    continue
                page = data.get("page", {}) or {}
                total = int(page.get("totalElements", 0) or 0)
                event_count += total
                events = (data.get("_embedded") or {}).get("events", []) or []
                for ev in events:
                    for venue in (ev.get("_embedded") or {}).get("venues", []) or []:
                        if venue.get("id"):
                            venues.add(venue["id"])
                        market = venue.get("market") or {}
                        if market.get("id"):
                            markets.add(market["id"])
                per_q[q] = total
            raw_blob.setdefault(country_code, {})[domain_code] = per_q
            sub_index = subindex_for_signal(cfg, SIGNAL, domain_code) or "GAC_Institutional"
            query_label = " | ".join(queries)
            status = "ok" if errors == 0 else ("partial" if errors < len(queries) else "missing")
            for metric_name, val in [
                ("ticketmaster_event_count", event_count),
                ("ticketmaster_venue_count", len(venues)),
                ("ticketmaster_market_count", len(markets)),
            ]:
                out.append(make_record(
                    cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                    signal_type=SIGNAL, sub_index=sub_index,
                    metric_name=metric_name,
                    raw_value=float(val) if errors < len(queries) else None,
                    source=SOURCE, api_name=API_NAME, api_endpoint=ENDPOINT,
                    query=query_label, query_type="event_queries",
                    status=status, notes=f"errors={errors}/{len(queries)}",
                ))

    save_json(raw_blob, raw_dir(SOURCE) / f"ticketmaster_{month.file_label}.json")
    return out
