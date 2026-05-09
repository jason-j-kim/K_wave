"""Render the monthly Markdown report for GACMI."""
from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from ..config_loader import Config
from ..dates import MonthRange
from ..utils import output_dir, reports_dir
from .generate_tables import (
    composite_table,
    confidence_table,
    coverage_table,
    domain_heatmap_table,
    subindex_ranking_table,
)


VERBATIM_DEFINITION = (
    "GACMI Beta 0.1 is not a full evaluation of national culture, artistic quality, "
    "or cultural value. It is an automated monthly signal index based on global media "
    "attention (GDELT), Wikipedia attention, bibliographic discoverability (Google Books, "
    "Open Library), museum and cultural collection database visibility (Met, Art Institute "
    "of Chicago, Europeana), event database visibility (Ticketmaster), and knowledge graph "
    "visibility (Wikidata)."
)
VERBATIM_KEYWORD_BASKETS = (
    "Because no human verification is used in Beta 0.1, the index uses reproducible "
    "country-domain keyword baskets rather than manually validated artist-level or "
    "work-level attribution."
)
VERBATIM_THREE_SUBINDICES = (
    "GACMI Beta 0.1 is structured as three sub-indices: GAC-Attention (covering all 10 domains), "
    "GAC-Discoverability (covering Publishing/Literature and Webtoon/Digital Fiction), and "
    "GAC-Institutional (covering Visual Arts, Performing Arts, Design/Craft, and Heritage/Language). "
    "The composite GACMI is the equally weighted combination of these three sub-indices."
)
VERBATIM_INSTITUTIONAL_STOCK = (
    "GAC-Institutional is built primarily on stock (catalog) data with little month-to-month "
    "variation. Month-over-month changes in this sub-index mainly reflect re-ranking among "
    "countries, not real cultural momentum."
)
VERBATIM_ANGLOSPHERE = (
    "Although GACMI is named 'Global,' the data infrastructure is overwhelmingly English-language "
    "and Western: GDELT (English-language news), English Wikipedia, US museums (Met, Art Institute "
    "of Chicago), European cultural databases (Europeana), and English-language book catalogs. "
    "The score should be read as 'global visibility through Anglosphere infrastructures of "
    "national arts and culture,' not as 'global cultural activity.'"
)
VERBATIM_CHINA = (
    "China is excluded from Beta 0.1 because its primary digital cultural infrastructure is "
    "largely invisible to these data sources. Including China would systematically misrepresent "
    "its cultural activity."
)
VERBATIM_RELATIVE = (
    "Scores should be interpreted as relative monthly visibility signals, not as final rankings "
    "of cultural greatness."
)

LIMITATIONS = [
    "English-language keyword bias",
    "English Wikipedia bias",
    "Global English-language news media bias (GDELT)",
    "Bibliographic database bias toward English catalogs",
    "Western institution bias in museum APIs (Met, ArtIC)",
    "European institution bias in Europeana",
    "Ticketmaster market coverage bias (heavily US/UK)",
    "Platform availability bias",
    "Country-size bias",
    "China excluded (Beta 0.1 limitation)",
    "Keyword ambiguity and overlap",
    "No human validation",
    "No entity-level attribution",
    "No direct measurement of artistic quality",
    "No direct measurement of cultural value",
    "No structural ecosystem measurement in Beta 0.1",
    "GAC-Institutional sub-index is dominated by stock data with low monthly variation",
    "Within-month percentile normalization removes absolute level information; mom_change "
    "measures change in relative rank, not absolute attention",
]

ROADMAP = """\
- **Beta 0.2** — multilingual keyword baskets, country-specific language queries, more
  countries (including China via Chinese-language sources), 12-month rolling baselines,
  domain-keyword refinement, optional GDELT tone signal.
- **Beta 0.3** — Wikidata entity matching for higher-precision attribution, TMDb /
  MusicBrainz / IGDB metadata, automated country attribution, robust z-score default.
- **Beta 0.4** — optional human review layer; awards, festivals, exhibitions, prizes,
  art fairs, design awards, museum acquisitions, art auction data.
- **Version 1.0** — Global Arts and Culture Structural Index combined with GACMI Momentum
  into a Composite Index; sub-index weights re-evaluated using construct-validity studies.
"""


def _missing_source_warnings(cfg: Config) -> List[str]:
    warnings: List[str] = []
    for name, conf in cfg.sources.items():
        if not isinstance(conf, dict) or name == "source_confidence_multipliers":
            continue
        if conf.get("requires_api_key") and not conf.get("enabled"):
            warnings.append(f"{name}: disabled or API key not provided ({conf.get('env_key', '')})")
        if name == "youtube" and conf.get("enabled"):
            warnings.append("youtube: enabled but EXPLORATORY ONLY — never enters official score")
    return warnings


def _render_sources_table(cfg: Config) -> str:
    lines = ["| Source | Enabled | Signal | Confidence multiplier |",
             "|:---|:---:|:---|---:|"]
    for name, conf in cfg.sources.items():
        if not isinstance(conf, dict) or name == "source_confidence_multipliers":
            continue
        sig = conf.get("produces_signal") or "(per-domain)"
        mult = cfg.source_confidence_multiplier(name)
        lines.append(f"| {name} | {'yes' if conf.get('enabled') else 'no'} | {sig} | {mult:.2f} |")
    return "\n".join(lines) + "\n"


def generate_report(cfg: Config, month: MonthRange, logger=None) -> Path:
    od = output_dir()
    composite_df = pd.read_csv(od / f"gacmi_composite_{month.file_label}.csv") if (od / f"gacmi_composite_{month.file_label}.csv").exists() else pd.DataFrame()
    subindex_df = pd.read_csv(od / f"subindex_scores_{month.file_label}.csv") if (od / f"subindex_scores_{month.file_label}.csv").exists() else pd.DataFrame()
    domain_df = pd.read_csv(od / f"domain_subindex_scores_{month.file_label}.csv") if (od / f"domain_subindex_scores_{month.file_label}.csv").exists() else pd.DataFrame()
    coverage_df = pd.read_csv(od / f"data_coverage_{month.file_label}.csv") if (od / f"data_coverage_{month.file_label}.csv").exists() else pd.DataFrame()
    confidences_df = subindex_df.copy()  # placeholder; we re-load real confidences from composite

    # Pull confidences out of composite_df for the confidence table.
    if not composite_df.empty:
        confidences_long = []
        for _, r in composite_df.iterrows():
            for sub_col, sub_name in [
                ("confidence_attention", "GAC_Attention"),
                ("confidence_discoverability", "GAC_Discoverability"),
                ("confidence_institutional", "GAC_Institutional"),
                ("confidence_composite", "GACMI_Composite"),
            ]:
                confidences_long.append({
                    "country_code": r["country_code"],
                    "country_name": r["country_name"],
                    "sub_index": sub_name,
                    "confidence": r.get(sub_col),
                })
        confidences_df = pd.DataFrame(confidences_long)

    youtube_path = od / f"exploratory_youtube_{month.file_label}.csv"
    youtube_section = ""
    if youtube_path.exists():
        ydf = pd.read_csv(youtube_path)
        if not ydf.empty:
            view_pivot = ydf[ydf["metric_name"] == "youtube_view_count"].pivot_table(
                index="country_name", columns="domain_code", values="raw_value", aggfunc="sum"
            )
            youtube_section = "### Exploratory annex: YouTube engagement\n\n"
            youtube_section += "Excluded from official sub-indices and composite GACMI.\n\n"
            youtube_section += view_pivot.to_markdown() + "\n"
        else:
            youtube_section = "### Exploratory annex: YouTube engagement\n\nNo data collected.\n"

    top_strengths = ""
    if not domain_df.empty:
        top = (domain_df.dropna(subset=["domain_subindex_score"])
                       .sort_values("domain_subindex_score", ascending=False)
                       .groupby("country_code").head(2))
        if not top.empty:
            top_strengths = "| Country | Top domain × sub-index | Score |\n|:---|:---|---:|\n"
            for _, r in top.iterrows():
                top_strengths += f"| {r['country_name']} | {r['domain_code']} ({r['sub_index']}) | {r['domain_subindex_score']:.1f} |\n"

    out_path = reports_dir() / f"gacmi_report_{month.file_label}.md"
    parts: List[str] = []
    parts.append(f"# Global Arts and Culture Momentum Index — {month.label}\n")
    parts.append(f"**Korean name:** 글로벌 문화예술 모멘텀 지수\n")
    parts.append(f"**Version:** Beta 0.1\n")
    parts.append(f"**Month:** {month.label}\n")

    parts.append("\n## 1. Definition\n")
    parts.append(VERBATIM_DEFINITION + "\n")
    parts.append("\n" + VERBATIM_THREE_SUBINDICES + "\n")

    parts.append("\n## 2. Anglosphere mediation note\n")
    parts.append(VERBATIM_ANGLOSPHERE + "\n")

    parts.append("\n## 3. Methodology summary\n")
    parts.append(
        "Each (country, domain) basket is queried against multiple sources. Raw counts are "
        "log-transformed (`ln(1+x)`) and percentile-ranked within (month × domain × signal × metric) "
        "to a 0–100 scale. Metrics are averaged into signal scores; signal scores are weighted into "
        "domain × sub-index scores; domain × sub-index scores are equally averaged into per-country "
        "sub-index scores; the composite GACMI is the configurable weighted average of the three "
        "sub-indices (default ⅓ each). Missing signals/domains/sub-indices trigger weight "
        "redistribution and a confidence-score reduction.\n"
    )
    parts.append(VERBATIM_KEYWORD_BASKETS + "\n")
    parts.append(VERBATIM_INSTITUTIONAL_STOCK + "\n")
    parts.append(VERBATIM_RELATIVE + "\n")

    parts.append("\n## 4. Countries included\n")
    parts.append(", ".join(cfg.countries[c]["name"] for c in cfg.country_codes()) + "\n\n")
    parts.append(VERBATIM_CHINA + "\n")

    parts.append("\n## 5. Domains included\n")
    parts.append(", ".join(cfg.domains[d]["name"] for d in cfg.domain_codes()) + "\n")

    parts.append("\n## 6. Data sources used\n")
    parts.append(_render_sources_table(cfg))

    parts.append("\n## 7. GAC-Attention ranking\n")
    parts.append(subindex_ranking_table(subindex_df, "GAC_Attention"))
    parts.append("\n## 8. GAC-Discoverability ranking\n")
    parts.append(subindex_ranking_table(subindex_df, "GAC_Discoverability"))
    parts.append("\n## 9. GAC-Institutional ranking\n")
    parts.append(subindex_ranking_table(subindex_df, "GAC_Institutional"))

    parts.append("\n## 10. Composite GACMI ranking\n")
    parts.append(composite_table(composite_df))

    parts.append("\n## 11. Domain × country heatmap (per sub-index)\n")
    for sub in cfg.sub_index_names():
        parts.append(f"\n### {sub}\n")
        parts.append(domain_heatmap_table(domain_df, sub, cfg.country_codes()))

    parts.append("\n## 12. Top country × domain strengths\n")
    parts.append(top_strengths or "_no data_\n")

    parts.append("\n## 13. Data coverage\n")
    parts.append(coverage_table(coverage_df))

    parts.append("\n## 14. Confidence scores\n")
    parts.append(confidence_table(confidences_df))

    parts.append("\n## 15. Missing source warnings\n")
    warns = _missing_source_warnings(cfg)
    if warns:
        for w in warns:
            parts.append(f"- {w}\n")
    else:
        parts.append("None.\n")

    if youtube_section:
        parts.append("\n## 16. " + youtube_section + "\n")
    else:
        parts.append("\n## 16. Exploratory annex\nYouTube data not collected.\n")

    parts.append("\n## 17. Limitations\n")
    for lim in LIMITATIONS:
        parts.append(f"- {lim}\n")

    parts.append("\n## 18. Roadmap\n")
    parts.append(ROADMAP)

    out_path.write_text("".join(parts), encoding="utf-8")
    if logger:
        logger.info("Wrote markdown report: %s", out_path)
    return out_path
