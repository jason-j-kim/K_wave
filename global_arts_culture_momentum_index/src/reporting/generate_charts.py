"""Matplotlib charts for the GACMI monthly report (no seaborn)."""
from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import output_dir, reports_dir


def _load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _save(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def country_ranking_chart(cfg: Config, month: MonthRange) -> Path:
    df = _load(output_dir() / f"gacmi_composite_{month.file_label}.csv")
    fig, ax = plt.subplots(figsize=(8, 5))
    if df.empty:
        ax.text(0.5, 0.5, "no data", ha="center", va="center")
    else:
        df = df.sort_values("gacmi_composite", ascending=True, na_position="first")
        ax.barh(df["country_name"], df["gacmi_composite"].fillna(0), color="#3a86ff")
        ax.set_xlabel("GACMI composite (0–100)")
        ax.set_title(f"GACMI composite ranking — {month.label}")
    out = reports_dir() / f"gacmi_country_rankings_{month.file_label}.png"
    _save(fig, out)
    return out


def subindex_comparison_chart(cfg: Config, month: MonthRange) -> Path:
    df = _load(output_dir() / f"gacmi_composite_{month.file_label}.csv")
    fig, ax = plt.subplots(figsize=(11, 5))
    if df.empty:
        ax.text(0.5, 0.5, "no data", ha="center", va="center")
    else:
        df = df.sort_values("gacmi_composite", ascending=False, na_position="last")
        x = np.arange(len(df))
        width = 0.27
        ax.bar(x - width, df["gac_attention"].fillna(0), width, label="GAC-Attention", color="#3a86ff")
        ax.bar(x, df["gac_discoverability"].fillna(0), width, label="GAC-Discoverability", color="#ffb703")
        ax.bar(x + width, df["gac_institutional"].fillna(0), width, label="GAC-Institutional", color="#8338ec")
        ax.set_xticks(x)
        ax.set_xticklabels(df["country_name"], rotation=30, ha="right")
        ax.set_ylabel("Score (0–100)")
        ax.set_title(f"Sub-index comparison by country — {month.label}")
        ax.legend()
    out = reports_dir() / f"gacmi_subindex_comparison_{month.file_label}.png"
    _save(fig, out)
    return out


def domain_heatmap_chart(cfg: Config, month: MonthRange) -> Path:
    df = _load(output_dir() / f"domain_subindex_scores_{month.file_label}.csv")
    sub_indices = cfg.sub_index_names()
    fig, axes = plt.subplots(1, len(sub_indices), figsize=(4 * len(sub_indices) + 2, 5))
    if len(sub_indices) == 1:
        axes = [axes]
    countries = cfg.country_codes()
    for ax, sub in zip(axes, sub_indices):
        sub_df = df[df["sub_index"] == sub] if not df.empty else df
        if sub_df.empty:
            ax.text(0.5, 0.5, "no data", ha="center", va="center")
            ax.set_title(sub)
            continue
        pivot = sub_df.pivot_table(index="country_code", columns="domain_code",
                                   values="domain_subindex_score", aggfunc="mean").reindex(countries)
        pivot = pivot.reindex(columns=cfg.sub_index_domains(sub))
        data = pivot.values
        im = ax.imshow(np.where(np.isnan(data), 0, data), aspect="auto", cmap="viridis", vmin=0, vmax=100)
        ax.set_xticks(range(pivot.shape[1]))
        ax.set_xticklabels(pivot.columns, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(pivot.shape[0]))
        ax.set_yticklabels(pivot.index, fontsize=8)
        ax.set_title(sub)
        fig.colorbar(im, ax=ax, fraction=0.04, pad=0.04)
    fig.suptitle(f"Domain × country heatmap — {month.label}")
    out = reports_dir() / f"gacmi_domain_heatmap_{month.file_label}.png"
    _save(fig, out)
    return out


def confidence_chart(cfg: Config, month: MonthRange) -> Path:
    df = _load(output_dir() / f"gacmi_composite_{month.file_label}.csv")
    fig, ax = plt.subplots(figsize=(11, 5))
    if df.empty:
        ax.text(0.5, 0.5, "no data", ha="center", va="center")
    else:
        df = df.sort_values("country_name")
        x = np.arange(len(df))
        width = 0.2
        for i, col, label, color in [
            (-1.5, "confidence_attention", "Attention", "#3a86ff"),
            (-0.5, "confidence_discoverability", "Discoverability", "#ffb703"),
            (0.5, "confidence_institutional", "Institutional", "#8338ec"),
            (1.5, "confidence_composite", "Composite", "#06d6a0"),
        ]:
            ax.bar(x + width * i, df[col].fillna(0), width, label=label, color=color)
        ax.set_xticks(x)
        ax.set_xticklabels(df["country_name"], rotation=30, ha="right")
        ax.set_ylabel("Confidence (0–100)")
        ax.set_title(f"Confidence by country — {month.label}")
        ax.legend()
    out = reports_dir() / f"gacmi_confidence_{month.file_label}.png"
    _save(fig, out)
    return out


def domain_coverage_chart(cfg: Config, month: MonthRange) -> Path:
    df = _load(output_dir() / f"data_coverage_{month.file_label}.csv")
    fig, ax = plt.subplots(figsize=(11, 5))
    if df.empty:
        ax.text(0.5, 0.5, "no data", ha="center", va="center")
    else:
        pivot = df.pivot_table(index="country_name", columns="sub_index",
                               values="n_domains_with_data", aggfunc="sum").fillna(0)
        countries = pivot.index.tolist()
        x = np.arange(len(countries))
        width = 0.27
        for i, col in enumerate(pivot.columns):
            ax.bar(x + width * (i - 1), pivot[col].values, width, label=col)
        ax.set_xticks(x)
        ax.set_xticklabels(countries, rotation=30, ha="right")
        ax.set_ylabel("Domains with data")
        ax.set_title(f"Domain coverage by sub-index — {month.label}")
        ax.legend()
    out = reports_dir() / f"gacmi_domain_coverage_{month.file_label}.png"
    _save(fig, out)
    return out


def generate_all_charts(cfg: Config, month: MonthRange, logger=None) -> List[Path]:
    paths = [
        country_ranking_chart(cfg, month),
        subindex_comparison_chart(cfg, month),
        domain_heatmap_chart(cfg, month),
        confidence_chart(cfg, month),
        domain_coverage_chart(cfg, month),
    ]
    if logger:
        logger.info("Wrote %d charts", len(paths))
    return paths
