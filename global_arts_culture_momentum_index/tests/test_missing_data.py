"""Tests for missing-data behavior end-to-end."""
import os

from src.collectors import europeana_collector, ticketmaster_collector, youtube_collector
from src.config_loader import load_config
from src.dates import parse_month


def test_europeana_skips_when_disabled():
    cfg = load_config()
    month = parse_month("2099-06")
    out = europeana_collector.collect(cfg=cfg, month=month, logger=None)
    assert out == []


def test_ticketmaster_skips_when_disabled():
    cfg = load_config()
    month = parse_month("2099-06")
    out = ticketmaster_collector.collect(cfg=cfg, month=month, logger=None)
    assert out == []


def test_youtube_returns_empty_for_official_pipeline(monkeypatch):
    cfg = load_config()
    month = parse_month("2099-06")
    out = youtube_collector.collect(cfg=cfg, month=month, logger=None)
    # YouTube is exploratory: it must return [] for the official pipeline merge.
    assert out == []


def test_dates_previous_month():
    m = parse_month("2026-01")
    prev = m.previous()
    assert prev.year == 2025 and prev.month == 12


def test_dates_parse_invalid():
    import pytest
    with pytest.raises(ValueError):
        parse_month("2026/05")
