"""YouTube collector (EXPLORATORY ONLY).

Output is saved to data/raw/youtube/ and to a separate exploratory CSV.
It is NEVER mixed into any of the three sub-indices or the composite GACMI.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from ..config_loader import Config, get_env
from ..dates import MonthRange
from ..utils import http_get_json, raw_dir, save_csv, save_json, output_dir
from ._base import make_record

SOURCE = "youtube"
API_NAME = "YouTube Data API v3"
SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"


def collect(cfg: Config, month: MonthRange, logger=None) -> List[Dict[str, Any]]:
    """Returns an empty list; YouTube data is exploratory and is written to a
    separate CSV instead of being merged into the official metrics file."""
    src_cfg = cfg.sources.get(SOURCE, {})
    if not src_cfg.get("enabled", False):
        if logger:
            logger.info("YouTube disabled; skipping")
        return []
    api_key = get_env(src_cfg.get("env_key", "YOUTUBE_API_KEY"))
    if not api_key:
        if logger:
            logger.info("YouTube API key missing; skipping")
        return []

    raw_blob: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []

    for country_code in cfg.country_codes():
        for domain_code in src_cfg.get("applicable_domains", []):
            basket = cfg.keyword_basket(country_code, domain_code)
            queries: List[str] = list(basket.get("youtube_queries", []))
            if not queries:
                continue
            seen_video_ids: set = set()
            view_count = 0
            like_count = 0
            comment_count = 0
            for q in queries:
                search_params = {
                    "part": "snippet", "q": q, "type": "video",
                    "maxResults": 25, "key": api_key,
                    "publishedAfter": month.first_day.strftime("%Y-%m-%dT00:00:00Z"),
                    "publishedBefore": month.last_day.strftime("%Y-%m-%dT23:59:59Z"),
                }
                search = http_get_json(SEARCH_ENDPOINT, params=search_params, timeout=30, retries=2, logger=logger)
                if search is None:
                    continue
                ids = [it["id"]["videoId"] for it in search.get("items", []) if it.get("id", {}).get("videoId")]
                ids = [i for i in ids if i not in seen_video_ids]
                if not ids:
                    continue
                seen_video_ids.update(ids)
                stats = http_get_json(VIDEOS_ENDPOINT, params={
                    "part": "statistics", "id": ",".join(ids), "key": api_key,
                }, timeout=30, retries=2, logger=logger)
                if stats is None:
                    continue
                for vid in stats.get("items", []) or []:
                    s = vid.get("statistics", {}) or {}
                    view_count += int(s.get("viewCount", 0) or 0)
                    like_count += int(s.get("likeCount", 0) or 0)
                    comment_count += int(s.get("commentCount", 0) or 0)
            raw_blob.setdefault(country_code, {})[domain_code] = {
                "videos": len(seen_video_ids),
                "views": view_count,
                "likes": like_count,
                "comments": comment_count,
            }

            for metric_name, raw_value in [
                ("youtube_video_count", len(seen_video_ids)),
                ("youtube_view_count", view_count),
                ("youtube_like_count", like_count),
                ("youtube_comment_count", comment_count),
            ]:
                rows.append(make_record(
                    cfg=cfg, month=month, country_code=country_code, domain_code=domain_code,
                    signal_type="YouTube_Platform_Engagement",
                    sub_index="EXPLORATORY",
                    metric_name=metric_name,
                    raw_value=float(raw_value),
                    source=SOURCE, api_name=API_NAME, api_endpoint=SEARCH_ENDPOINT,
                    query=" | ".join(queries), query_type="youtube_queries",
                    status="exploratory",
                    notes="excluded from official sub-indices and composite",
                ))

    save_json(raw_blob, raw_dir(SOURCE) / f"youtube_{month.file_label}.json")
    if rows:
        save_csv(rows, output_dir() / f"exploratory_youtube_{month.file_label}.csv")
    return []
