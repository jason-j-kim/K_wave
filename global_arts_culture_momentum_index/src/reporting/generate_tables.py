"""Build markdown tables from scoring CSVs."""
from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from ..dates import MonthRange
from ..utils import output_dir


def _format_score(value) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):.1f}"


def subindex_ranking_table(subindex_df: pd.DataFrame, sub_index: str) -> str:
    sub = subindex_df[subindex_df["sub_index"] == sub_index].copy()
    if sub.empty:
        return "_no data_\n"
    sub = sub.sort_values("subindex_score", ascending=False, na_position="last")
    sub["rank"] = sub["subindex_score"].rank(ascending=False, method="min").astype("Int64")
    lines = ["| Rank | Country | Score | Available domains | Missing domains |",
             "|---:|:---|---:|:---|:---|"]
    for _, r in sub.iterrows():
        lines.append(
            f"| {r['rank'] if pd.notna(r['rank']) else '—'} "
            f"| {r['country_name']} "
            f"| {_format_score(r['subindex_score'])} "
            f"| {r.get('available_domains','') or '—'} "
            f"| {r.get('missing_domains','') or '—'} |"
        )
    return "\n".join(lines) + "\n"


def composite_table(composite_df: pd.DataFrame) -> str:
    if composite_df.empty:
        return "_no data_\n"
    df = composite_df.copy()
    lines = [
        "| Rank | Country | GACMI | GAC-Att | GAC-Disc | GAC-Inst | Conf. |",
        "|---:|:---|---:|---:|---:|---:|---:|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['rank'] if pd.notna(r['rank']) else '—'} "
            f"| {r['country_name']} "
            f"| {_format_score(r['gacmi_composite'])} "
            f"| {_format_score(r['gac_attention'])} "
            f"| {_format_score(r['gac_discoverability'])} "
            f"| {_format_score(r['gac_institutional'])} "
            f"| {_format_score(r['confidence_composite'])} |"
        )
    return "\n".join(lines) + "\n"


def domain_heatmap_table(domain_df: pd.DataFrame, sub_index: str, country_codes: List[str]) -> str:
    sub = domain_df[domain_df["sub_index"] == sub_index]
    if sub.empty:
        return "_no data_\n"
    pivot = sub.pivot_table(
        index="country_code",
        columns="domain_code",
        values="domain_subindex_score",
        aggfunc="mean",
    ).reindex(country_codes)
    lines = ["| Country | " + " | ".join(pivot.columns) + " |",
             "|:---" + "|---:" * len(pivot.columns) + "|"]
    for cc, row in pivot.iterrows():
        cells = [_format_score(v) for v in row.values]
        lines.append(f"| {cc} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def confidence_table(confidences_df: pd.DataFrame) -> str:
    if confidences_df.empty:
        return "_no data_\n"
    pivot = confidences_df.pivot_table(
        index=["country_code", "country_name"],
        columns="sub_index",
        values="confidence",
    ).reset_index()
    cols = [c for c in ["GAC_Attention", "GAC_Discoverability", "GAC_Institutional", "GACMI_Composite"] if c in pivot.columns]
    lines = ["| Country | " + " | ".join(cols) + " |",
             "|:---" + "|---:" * len(cols) + "|"]
    for _, r in pivot.iterrows():
        cells = [_format_score(r.get(c)) for c in cols]
        lines.append(f"| {r['country_name']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def coverage_table(coverage_df: pd.DataFrame) -> str:
    if coverage_df.empty:
        return "_no data_\n"
    pivot = coverage_df.pivot_table(
        index=["country_code", "country_name"],
        columns="sub_index",
        values="n_domains_with_data",
    ).reset_index()
    cols = [c for c in pivot.columns if c not in ("country_code", "country_name")]
    lines = ["| Country | " + " | ".join(str(c) for c in cols) + " |",
             "|:---" + "|---:" * len(cols) + "|"]
    for _, r in pivot.iterrows():
        cells = [str(int(r.get(c))) if pd.notna(r.get(c)) else "—" for c in cols]
        lines.append(f"| {r['country_name']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
