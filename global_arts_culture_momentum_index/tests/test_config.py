"""Tests for YAML config loading."""
from src.config_loader import load_config


def test_loads_all_configs():
    cfg = load_config()
    assert set(cfg.country_codes()) == {"KR", "JP", "US", "GB", "FR", "DE", "IT", "ES", "IN", "BR", "MX"}
    assert "Music" in cfg.domain_codes()
    assert len(cfg.domain_codes()) == 10
    assert set(cfg.sub_index_names()) == {"GAC_Attention", "GAC_Discoverability", "GAC_Institutional"}


def test_china_excluded():
    cfg = load_config()
    assert "CN" not in cfg.country_codes()


def test_signals_present():
    cfg = load_config()
    for s in [
        "Global_Media_Attention", "Wikipedia_Attention", "Book_Discoverability",
        "Museum_Collection_Visibility", "Cultural_Heritage_Database_Visibility",
        "Performing_Event_Visibility", "Wikidata_Knowledge_Graph_Visibility",
    ]:
        assert s in cfg.signals


def test_attention_covers_all_domains():
    cfg = load_config()
    assert set(cfg.sub_index_domains("GAC_Attention")) == set(cfg.domain_codes())


def test_discoverability_two_domains():
    cfg = load_config()
    assert set(cfg.sub_index_domains("GAC_Discoverability")) == {"Publishing_Literature", "Webtoon_Digital_Fiction"}


def test_institutional_four_domains():
    cfg = load_config()
    assert set(cfg.sub_index_domains("GAC_Institutional")) == {"Visual_Arts", "Performing_Arts", "Design_Craft", "Heritage_Language"}


def test_weights_sum_to_one_within_subindex_domain():
    cfg = load_config()
    for sub_index in cfg.sub_index_names():
        for domain in cfg.sub_index_domains(sub_index):
            sigs = cfg.domain_subindex_signal_map(sub_index, domain)
            if not sigs:
                continue
            total = sum(sigs.values())
            assert abs(total - 1.0) < 1e-6, f"{sub_index}/{domain} sums to {total}"


def test_composite_weights_present():
    cfg = load_config()
    cw = cfg.composite_weights
    assert set(cw) == {"GAC_Attention", "GAC_Discoverability", "GAC_Institutional"}
    assert abs(sum(cw.values()) - 1.0) < 1e-3


def test_keywords_complete_for_all_pairs():
    cfg = load_config()
    for c in cfg.country_codes():
        for d in cfg.domain_codes():
            basket = cfg.keyword_basket(c, d)
            assert basket, f"missing keyword basket for {c}/{d}"


def test_youtube_marked_exploratory():
    cfg = load_config()
    assert cfg.sources["youtube"].get("exploratory_only") is True
    assert cfg.exploratory_signals["YouTube_Platform_Engagement"]["enabled"] is False


def test_met_artic_per_domain_signal_mapping():
    cfg = load_config()
    assert cfg.source_signal_for_domain("met", "Visual_Arts") == "Museum_Collection_Visibility"
    assert cfg.source_signal_for_domain("met", "Heritage_Language") == "Cultural_Heritage_Database_Visibility"
    assert cfg.source_signal_for_domain("artic", "Design_Craft") == "Museum_Collection_Visibility"
    assert cfg.source_signal_for_domain("artic", "Heritage_Language") == "Cultural_Heritage_Database_Visibility"


def test_source_confidence_multipliers():
    cfg = load_config()
    m = cfg.source_confidence_multipliers
    assert m["high"] == 1.0
    assert m["medium"] == 1.0
    assert m["low_to_medium"] == 0.7
    assert m["low"] == 0.5
