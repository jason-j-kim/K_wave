"""GACMI command-line entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set

from . import __version__
from .config_loader import load_config, get_env
from .dates import MonthRange, parse_month
from .logger import get_logger
from .utils import CANONICAL_COLUMNS, ensure_dir, save_csv, processed_dir, output_dir

LOGGER = get_logger("gacmi.main")


COLLECTOR_NAMES = [
    "gdelt",
    "wikipedia",
    "google_books",
    "openlibrary",
    "wikidata",
    "met",
    "artic",
    "europeana",
    "ticketmaster",
    "youtube",
]


def _resolve_collectors(only: Optional[str], skip: Optional[str]) -> Set[str]:
    selected = set(COLLECTOR_NAMES)
    if only:
        wanted = {s.strip() for s in only.split(",") if s.strip()}
        selected = wanted & set(COLLECTOR_NAMES)
    if skip:
        for s in skip.split(","):
            selected.discard(s.strip())
    return selected


def _run_collectors(month: MonthRange, only: Optional[str], skip: Optional[str]) -> Path:
    """Run all enabled collectors and merge their output into a long-format CSV."""
    from .collectors import (
        gdelt_collector,
        wikipedia_collector,
        google_books_collector,
        openlibrary_collector,
        wikidata_collector,
        met_collector,
        artic_collector,
        europeana_collector,
        ticketmaster_collector,
        youtube_collector,
    )

    cfg = load_config()
    selected = _resolve_collectors(only, skip)
    LOGGER.info("Running collectors %s for month=%s", sorted(selected), month.label)

    all_records: List[dict] = []
    collectors = {
        "gdelt": gdelt_collector,
        "wikipedia": wikipedia_collector,
        "google_books": google_books_collector,
        "openlibrary": openlibrary_collector,
        "wikidata": wikidata_collector,
        "met": met_collector,
        "artic": artic_collector,
        "europeana": europeana_collector,
        "ticketmaster": ticketmaster_collector,
        "youtube": youtube_collector,
    }

    for name in COLLECTOR_NAMES:
        if name not in selected:
            LOGGER.info("Skipping collector: %s", name)
            continue
        try:
            module = collectors[name]
            records = module.collect(cfg=cfg, month=month, logger=LOGGER)
            LOGGER.info("Collector %s returned %d records", name, len(records))
            all_records.extend(records)
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Collector %s crashed: %s", name, exc)

    out_path = processed_dir() / f"monthly_metrics_{month.file_label}.csv"
    save_csv(all_records, out_path, columns=CANONICAL_COLUMNS)
    LOGGER.info("Wrote %d collected records to %s", len(all_records), out_path)
    return out_path


def cmd_collect(args: argparse.Namespace) -> int:
    month = parse_month(args.month)
    _run_collectors(month, args.only, args.skip)
    return 0


def cmd_process(args: argparse.Namespace) -> int:
    from .processing.aggregate_metrics import aggregate_for_month
    month = parse_month(args.month)
    aggregate_for_month(month=month, logger=LOGGER)
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    from .scoring.signal_scores import compute_signal_scores
    from .scoring.domain_subindex_scores import compute_domain_subindex_scores
    from .scoring.subindex_scores import compute_subindex_scores
    from .scoring.composite_score import compute_composite
    from .scoring.confidence_scores import compute_confidences

    month = parse_month(args.month)
    cfg = load_config()
    LOGGER.info("Scoring %s", month.label)

    signal_df = compute_signal_scores(cfg=cfg, month=month, logger=LOGGER)
    domain_df = compute_domain_subindex_scores(cfg=cfg, month=month, signal_df=signal_df, logger=LOGGER)
    subindex_df = compute_subindex_scores(cfg=cfg, month=month, domain_df=domain_df, logger=LOGGER)
    confidences = compute_confidences(cfg=cfg, month=month, domain_df=domain_df, logger=LOGGER)
    compute_composite(
        cfg=cfg,
        month=month,
        subindex_df=subindex_df,
        confidences=confidences,
        logger=LOGGER,
    )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from .reporting.generate_charts import generate_all_charts
    from .reporting.generate_markdown_report import generate_report

    month = parse_month(args.month)
    cfg = load_config()
    LOGGER.info("Generating report for %s", month.label)
    generate_all_charts(cfg=cfg, month=month, logger=LOGGER)
    generate_report(cfg=cfg, month=month, logger=LOGGER)
    return 0


def cmd_run_all(args: argparse.Namespace) -> int:
    rc = cmd_collect(args)
    if rc != 0:
        return rc
    rc = cmd_process(args)
    if rc != 0:
        return rc
    rc = cmd_score(args)
    if rc != 0:
        return rc
    return cmd_report(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gacmi",
        description=f"Global Arts and Culture Momentum Index v{__version__}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def _add_month(p: argparse.ArgumentParser) -> None:
        p.add_argument("--month", required=True, help="YYYY-MM or 'previous'")

    p = sub.add_parser("collect", help="Run data collectors")
    _add_month(p)
    p.add_argument("--only", help="Comma-separated collector subset")
    p.add_argument("--skip", help="Comma-separated collectors to skip")
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("process", help="Aggregate raw metrics")
    _add_month(p)
    p.set_defaults(func=cmd_process)

    p = sub.add_parser("score", help="Compute signal/domain/sub-index/composite scores")
    _add_month(p)
    p.set_defaults(func=cmd_score)

    p = sub.add_parser("report", help="Render charts and markdown report")
    _add_month(p)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("run-all", help="collect → process → score → report")
    _add_month(p)
    p.add_argument("--only", help="Comma-separated collector subset")
    p.add_argument("--skip", help="Comma-separated collectors to skip")
    p.set_defaults(func=cmd_run_all)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
