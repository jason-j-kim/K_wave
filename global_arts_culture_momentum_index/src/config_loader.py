"""Configuration loader for GACMI.

Loads YAML config files into typed dataclasses / dicts. Provides a single
``Config`` object that the rest of the pipeline can pass around.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


CONFIG_DIR_DEFAULT = Path(__file__).resolve().parent.parent / "config"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    return data


@dataclass
class Config:
    """Aggregate of every YAML config file."""

    countries: Dict[str, Dict[str, Any]]
    domains: Dict[str, Dict[str, Any]]
    signals: Dict[str, Dict[str, Any]]
    sub_indices: Dict[str, Dict[str, Any]]
    weights: Dict[str, Any]
    exploratory_signals: Dict[str, Dict[str, Any]]
    sources: Dict[str, Any]
    keywords: Dict[str, Dict[str, Dict[str, List[str]]]]
    config_dir: Path

    @property
    def normalization_method(self) -> str:
        return self.weights.get("normalization_method", "percentile_rank")

    @property
    def composite_weights(self) -> Dict[str, float]:
        return dict(self.sub_indices["GACMI_Composite"]["default_weights"])

    @property
    def source_confidence_multipliers(self) -> Dict[str, float]:
        return dict(self.sources["source_confidence_multipliers"])

    def country_codes(self) -> List[str]:
        return list(self.countries.keys())

    def domain_codes(self) -> List[str]:
        return list(self.domains.keys())

    def sub_index_names(self) -> List[str]:
        return [k for k in self.sub_indices.keys() if k != "GACMI_Composite"]

    def sub_index_signals(self, sub_index: str) -> List[str]:
        return list(self.sub_indices[sub_index]["signals"])

    def sub_index_domains(self, sub_index: str) -> List[str]:
        return list(self.sub_indices[sub_index]["domains"])

    def signal_weight(self, sub_index: str, domain: str, signal: str) -> float:
        try:
            return float(self.weights[sub_index][domain][signal])
        except KeyError:
            return 0.0

    def domain_subindex_signal_map(self, sub_index: str, domain: str) -> Dict[str, float]:
        try:
            return dict(self.weights[sub_index][domain])
        except KeyError:
            return {}

    def keyword_basket(self, country: str, domain: str) -> Dict[str, List[str]]:
        return dict(self.keywords.get(country, {}).get(domain, {}))

    def source_for_signal(self, signal: str, domain: Optional[str] = None) -> List[str]:
        """Return list of source names that produce the given signal in domain."""
        out: List[str] = []
        for name, cfg in self.sources.items():
            if not isinstance(cfg, dict):
                continue
            if name == "source_confidence_multipliers":
                continue
            applicable = cfg.get("applicable_domains", [])
            if domain and domain not in applicable:
                continue
            sig = cfg.get("produces_signal")
            psd = cfg.get("produces_signal_per_domain", {})
            if sig == signal:
                out.append(name)
            elif domain and psd.get(domain) == signal:
                out.append(name)
        return out

    def source_signal_for_domain(self, source: str, domain: str) -> Optional[str]:
        cfg = self.sources.get(source, {})
        if not isinstance(cfg, dict):
            return None
        psd = cfg.get("produces_signal_per_domain")
        if isinstance(psd, dict):
            return psd.get(domain)
        return cfg.get("produces_signal")

    def source_confidence_multiplier(self, source: str) -> float:
        cfg = self.sources.get(source, {})
        level = cfg.get("source_confidence_level", "medium")
        return float(self.source_confidence_multipliers.get(level, 1.0))


def load_config(config_dir: Optional[Path | str] = None) -> Config:
    cdir = Path(config_dir) if config_dir else CONFIG_DIR_DEFAULT
    return Config(
        countries=_load_yaml(cdir / "countries.yml"),
        domains=_load_yaml(cdir / "domains.yml"),
        signals=_load_yaml(cdir / "signals.yml"),
        sub_indices=_load_yaml(cdir / "sub_indices.yml"),
        weights=_load_yaml(cdir / "weights.yml"),
        exploratory_signals=_load_yaml(cdir / "exploratory_signals.yml"),
        sources=_load_yaml(cdir / "sources.yml"),
        keywords=_load_yaml(cdir / "keywords.yml"),
        config_dir=cdir,
    )


def get_env(key: str) -> Optional[str]:
    """Lookup an environment variable, returning ``None`` if missing or blank."""
    val = os.environ.get(key)
    if val is None:
        return None
    val = val.strip()
    return val or None
