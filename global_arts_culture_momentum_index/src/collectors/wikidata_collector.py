"""Wikidata collector.

Two stages: ``wbsearchentities`` to confirm a keyword resolves to at
least one Wikidata entity, and a SPARQL ``COUNT`` query to estimate
distinct entities matching the keyword in English labels/altLabels.
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_json
from ._base import make_record, subindex_for_signal

SOURCE = "wikidata"
SIGNAL = "Wikidata_Knowledge_Graph_Visibility"
API_NAME = "Wikidata SPARQL / wbsearchentities"
SEARCH_ENDPOINT = "https://www.wikidata.org/w/api.php"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

SPARQL_TEMPLATE = """
SELECT (COUNT(DISTINCT ?item) AS ?n) WHERE {{
  ?item rdfs:label|skos:altLabel ?label .
  FILTER(CONTAINS(LCASE(STR(?label)), LCASE("{kw}")))
  FILTER(LANG(?label) = "en")
}}
"""


def _wbsearch(kw: str, logger=None) -> int:
    params = {
        "action": "wbsearchentities", "format": "json", "language": "en",
        "search": kw, "limit": 10,
    }
    data = http_get_json(SEARCH_ENDPOINT, params=params, timeout=20, retries=2, logger=logger)
    if data is None:
        return -1
    return len(data.get("search", []) or [])


def _sparql_count(kw: str, logger=None) -> int:
    safe_kw = kw.replace('"', '\\"')
    query = SPARQL_TEMPLATE.format(kw=safe_kw)
    headers = {"Accept": "application/sparql-results+json"}
    data = http_get_json(SPARQL_ENDPOINT, params={"query": query}, headers=headers,
                         timeout=30, retries=2, logger=logger)
    if data is None:
        return -1
    try:
        bindings = data["results"]["bindings"]
        if not bindings:
            return 0
        return int(bindings[0]["n"]["value"])
    except (KeyError, ValueError, TypeError):
        return -1


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        return []
    raw_blob: Dict[str, Any] = {}
    out: List[Dict[str, Any]] = []

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("wikidata_queries", []))
            if not queries:
                continue
            total = 0
            errors = 0
            per_q: Dict[str, Any] = {}
            for kw in queries:
                hits_search = _wbsearch(kw, logger=logger)
                count = _sparql_count(kw, logger=logger)
                per_q[kw] = {"wbsearch": hits_search, "sparql_count": count}
                if count < 0:
                    errors += 1
                else:
                    total += count
            raw_blob.setdefault(country_code, {})[domain_code] = per_q
            sub_index = subindex_for_signal(cfg, SIGNAL, domain_code) or "GAC_Institutional"
            query_label = " | ".join(queries)
            status = "ok" if errors == 0 else ("partial" if errors < len(queries) else "missing")
            out.append(make_record(
                cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                signal_type=SIGNAL, sub_index=sub_index,
                metric_name="wikidata_entity_count",
                raw_value=float(total) if errors < len(queries) else None,
                source=SOURCE, api_name=API_NAME, api_endpoint=SPARQL_ENDPOINT,
                query=query_label, query_type="wikidata_queries",
                status=status, notes=f"errors={errors}/{len(queries)}",
            ))

    save_json(raw_blob, raw_dir(SOURCE) / f"wikidata_{month.file_label}.json")
    return out
