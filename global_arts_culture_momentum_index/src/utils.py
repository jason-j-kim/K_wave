"""Utility helpers for GACMI."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CollectorRecord:
    """Canonical long-format row produced by every collector."""

    month: str
    country_code: str
    country_name: str
    domain_code: str
    domain_name: str
    signal_type: str
    sub_index: str
    metric_name: str
    raw_value: Optional[float]
    source: str
    api_name: str
    api_endpoint: str
    query: str
    query_type: str
    collected_at: str
    status: str
    notes: str
    is_domain_specific_source: bool
    requires_api_key: bool
    source_confidence_level: str
    flow_type: str

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


CANONICAL_COLUMNS: List[str] = [
    "month",
    "country_code",
    "country_name",
    "domain_code",
    "domain_name",
    "signal_type",
    "sub_index",
    "metric_name",
    "raw_value",
    "source",
    "api_name",
    "api_endpoint",
    "query",
    "query_type",
    "collected_at",
    "status",
    "notes",
    "is_domain_specific_source",
    "requires_api_key",
    "source_confidence_level",
    "flow_type",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Any, path: Path) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_csv(rows: Iterable[Dict[str, Any]], path: Path, columns: Optional[List[str]] = None) -> Path:
    ensure_dir(path.parent)
    df = pd.DataFrame(list(rows))
    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = None
        df = df[columns]
    df.to_csv(path, index=False)
    return path


def http_get_json(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    retries: int = 3,
    backoff: float = 1.5,
    logger=None,
) -> Optional[Dict[str, Any]]:
    """HTTP GET with retries and JSON decode. Returns ``None`` on failure."""
    headers = {"User-Agent": "GACMI-Beta/0.1 (research)", **(headers or {})}
    last_err: Optional[str] = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                last_err = "rate_limited"
                time.sleep(backoff ** attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_err = str(exc)
            if attempt < retries:
                time.sleep(backoff ** attempt)
            else:
                if logger:
                    logger.warning("HTTP GET failed after %s attempts: %s -- %s", retries, url, last_err)
    return None


def http_get_text(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    retries: int = 3,
    backoff: float = 1.5,
    logger=None,
) -> Optional[str]:
    headers = {"User-Agent": "GACMI-Beta/0.1 (research)", **(headers or {})}
    last_err: Optional[str] = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                last_err = "rate_limited"
                time.sleep(backoff ** attempt)
                continue
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as exc:
            last_err = str(exc)
            if attempt < retries:
                time.sleep(backoff ** attempt)
            else:
                if logger:
                    logger.warning("HTTP GET failed after %s attempts: %s -- %s", retries, url, last_err)
    return None


def safe_call(fn: Callable[..., Any], *args: Any, logger=None, default: Any = None, **kwargs: Any) -> Any:
    """Call ``fn``; log and return ``default`` on any exception."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        if logger:
            logger.exception("safe_call: %s failed: %s", getattr(fn, "__name__", str(fn)), exc)
        return default


def output_dir() -> Path:
    return ensure_dir(PROJECT_ROOT / "data" / "output")


def processed_dir() -> Path:
    return ensure_dir(PROJECT_ROOT / "data" / "processed")


def raw_dir(source: str) -> Path:
    return ensure_dir(PROJECT_ROOT / "data" / "raw" / source)


def reports_dir() -> Path:
    return ensure_dir(PROJECT_ROOT / "reports" / "monthly")
