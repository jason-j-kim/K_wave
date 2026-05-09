# Global Arts and Culture Momentum Index — GACMI Beta 0.1

**Korean name:** 글로벌 문화예술 모멘텀 지수
**Short name:** GACMI
**Version:** Beta 0.1

GACMI Beta 0.1 is structured as three sub-indices (GAC-Attention,
GAC-Discoverability, GAC-Institutional) plus a composite. **Read the three
sub-indices first; the composite is a summary, not a substitute. Confidence
scores must be read together with the index scores.**

---

## 1. What GACMI is

GACMI is an automated monthly country-level comparative index that measures
the global digital, media, bibliographic, platform, collection-database,
event-database, and knowledge-graph momentum of each country's arts and
culture. Beta 0.1 is the first stage; everything is automated and
reproducible.

It produces three sub-indices:

| Sub-index | Korean | Built from | Domains covered |
|---|---|---|---|
| GAC-Attention (주목지수) | 주목지수 | GDELT + English Wikipedia (+ optional YouTube as exploratory only) | All 10 |
| GAC-Discoverability (발견가능성지수) | 발견가능성지수 | Google Books + Open Library | Publishing/Literature, Webtoon/Digital Fiction |
| GAC-Institutional (제도적가시성지수) | 제도적가시성지수 | Met + Art Institute of Chicago + Wikidata (+ optional Europeana, Ticketmaster) | Visual Arts, Performing Arts, Design/Craft, Heritage/Language |

The **Composite GACMI** is the configurable weighted combination of the
three (default ⅓ each).

## 2. What Beta 0.1 measures

Global visibility, discoverability, attention, and platform/database
presence around country-associated arts and culture categories, **as
mediated by English-language infrastructures** (GDELT, English Wikipedia,
US/EU museums, English bibliographic catalogs).

## 3. What Beta 0.1 does NOT measure

- artistic quality
- cultural depth or value
- institutional strength
- expert evaluation
- ecosystem structure (industry size, public budgets, labour, etc.)

## 4. Why all 10 domains from the start

Cultural strength is uneven across domains. Restricting the index to a few
domains would produce misleading rankings. All 10 domains are present in
GAC-Attention; GAC-Discoverability and GAC-Institutional cover only the
domains where their data sources actually have meaningful coverage.

## 5. Why equal domain weights within each sub-index

Beta 0.1 has no construct-validity studies to justify unequal domain
weighting. Equal weights are the most defensible default and make the
methodology transparent.

## 6. Why three sub-indices

Each sub-index measures a different construct:

- **GAC-Attention** — flows of public/news/encyclopedic attention
- **GAC-Discoverability** — bibliographic catalog presence (stock-like)
- **GAC-Institutional** — visibility in Western institutional collections,
  knowledge graphs, event databases (mostly stock data with little
  month-to-month variation)

Combining them into a single number hides what is being measured. Read the
sub-indices separately.

## 7. Why composite weights default to ⅓ each

There is no empirical basis to prefer one sub-index over another. Equal
1/3 weighting is the neutral default. Composite weights are configurable
in `config/sub_indices.yml`.

## 8. Why keyword baskets

Beta 0.1 contains no human verification of artist nationality, production
country, exhibition lists, awards, etc. Manually verifying this for every
country and domain monthly is not feasible. Reproducible per-(country,
domain) keyword baskets give a transparent, automated alternative. This
introduces real biases (overlap, ambiguity, English-language framing) — see
**Limitations**.

## 9. Why no human verification

Same reason — Beta 0.1 is the automated baseline. Beta 0.4 will add an
optional human review layer.

## 10. Why China is excluded in Beta 0.1

China's primary digital cultural infrastructure (Baidu, Bilibili, Weibo,
iQiyi, Douyin, etc.) is largely invisible to GDELT, English Wikipedia, and
YouTube. Including China would systematically misrepresent its cultural
activity. China may be added in a future version with appropriate
Chinese-language sources.

## 11. Why YouTube is exploratory only

Search-based YouTube counts represent cumulative query engagement, not
exact monthly consumption, and cannot be normalized into a clean monthly
flow. YouTube data, when collected, is reported in a separate exploratory
annex; it is **never** part of any sub-index or the composite GACMI.

## 12. Anglosphere mediation disclosure

> Although GACMI is named "Global," the data infrastructure is
> overwhelmingly English-language and Western: GDELT (English-language
> news), English Wikipedia, US museums (Met, Art Institute of Chicago),
> European cultural databases (Europeana), and English-language book
> catalogs. The score should be read as "global visibility through
> Anglosphere infrastructures of national arts and culture," not as
> "global cultural activity."

## 13. Stock vs flow signals

| Signal | Type |
|---|---|
| Global_Media_Attention (GDELT) | monthly flow |
| Wikipedia_Attention | monthly flow |
| Performing_Event_Visibility (Ticketmaster) | monthly flow |
| Book_Discoverability | catalog stock |
| Museum_Collection_Visibility | catalog stock |
| Cultural_Heritage_Database_Visibility | catalog stock |
| Wikidata_Knowledge_Graph_Visibility | catalog stock |

GAC-Institutional is dominated by stock data, so its month-over-month
changes are small and mostly reflect re-ranking.

## 14. Countries included

Korea, Japan, United States, United Kingdom, France, Germany, Italy,
Spain, India, Brazil, Mexico (11). China is intentionally excluded — see
§10.

## 15. Domains included

Music, Drama and OTT Series, Film, Webtoon and Digital Fiction, Games and
Esports, Publishing and Literature, Visual Arts, Performing Arts, Design
and Craft, Heritage and Language (10).

## 16. Data sources

| Source | Signal | API key | Default |
|---|---|---|---|
| GDELT DOC 2.0 | Global_Media_Attention | no | enabled |
| Wikimedia REST (Pageviews) | Wikipedia_Attention | no | enabled |
| Google Books Volumes | Book_Discoverability | optional | enabled |
| Open Library Search | Book_Discoverability | no | enabled |
| Wikidata SPARQL + wbsearchentities | Wikidata_Knowledge_Graph_Visibility | no | enabled |
| Met Collection Search | Museum_Collection_Visibility / Cultural_Heritage_Database_Visibility | no | enabled |
| Art Institute of Chicago | Museum_Collection_Visibility / Cultural_Heritage_Database_Visibility | no | enabled |
| Europeana Search | Cultural_Heritage_Database_Visibility | yes (`EUROPEANA_API_KEY`) | disabled |
| Ticketmaster Discovery | Performing_Event_Visibility | yes (`TICKETMASTER_API_KEY`) | disabled |
| YouTube Data API v3 | (exploratory) | yes (`YOUTUBE_API_KEY`) | disabled |

Met and Art Institute of Chicago each map to **different signals depending
on the domain**. See `config/sources.yml`.

## 17. Installation

```bash
cd global_arts_culture_momentum_index
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # then fill in any optional keys you have
```

## 18. Environment variables

See `.env.example`. All keys are optional; collectors that require a key
skip themselves with a warning when the key is absent.

## 19. How to run

```bash
# Run everything for May 2026
python -m src.main run-all --month 2026-05

# Or step-by-step
python -m src.main collect --month 2026-05
python -m src.main process --month 2026-05
python -m src.main score   --month 2026-05
python -m src.main report  --month 2026-05

# Most recent completed calendar month
python -m src.main run-all --month previous

# Subset / skip collectors
python -m src.main collect --month 2026-05 --only gdelt
python -m src.main collect --month 2026-05 --skip ticketmaster,europeana
```

Outputs:
- `data/processed/monthly_metrics_YYYY_MM.csv`
- `data/output/signal_scores_YYYY_MM.csv`
- `data/output/domain_subindex_scores_YYYY_MM.csv`
- `data/output/subindex_scores_YYYY_MM.csv`
- `data/output/gacmi_composite_YYYY_MM.csv`
- `data/output/data_coverage_YYYY_MM.csv`
- `data/output/exploratory_youtube_YYYY_MM.csv` (if YouTube enabled)
- `reports/monthly/gacmi_report_YYYY_MM.md`
- `reports/monthly/*.png` (5 charts)

## 20. How to interpret the three sub-indices and the composite

- **GAC-Attention** is a monthly flow signal. Movement here genuinely
  reflects month-to-month attention shifts (new releases, news cycles).
- **GAC-Discoverability** is a slow-moving catalog stock. Read it as a
  baseline level of bibliographic presence.
- **GAC-Institutional** is also slow-moving (catalog stock plus a small
  monthly-flow component from Ticketmaster). MoM movement is mostly
  re-ranking, not real momentum.
- **Composite GACMI** is a summary. If a country shows a big composite
  jump, look at which sub-index drove it before drawing conclusions.

## 21. How to interpret confidence scores

Confidence is a 0–100 measure of how much of the expected weight (domain ×
signal × source-confidence multiplier) actually produced data this month.
A country with low confidence has many missing signals/domains; treat its
score as provisional.

## 22. Limitations

- English-language keyword bias
- English Wikipedia bias
- Global English-language news media bias (GDELT)
- Bibliographic database bias toward English catalogs
- Western institution bias in museum APIs (Met, ArtIC)
- European institution bias in Europeana
- Ticketmaster market coverage bias (heavily US/UK)
- Platform availability bias
- Country-size bias
- China excluded (Beta 0.1 limitation)
- Keyword ambiguity and overlap
- No human validation
- No entity-level attribution
- No direct measurement of artistic quality
- No direct measurement of cultural value
- No structural ecosystem measurement in Beta 0.1
- GAC-Institutional sub-index is dominated by stock data with low monthly variation
- Within-month percentile normalization removes absolute level information; mom_change measures change in **relative** rank, not absolute attention
- With N=11 countries, percentile rank is essentially an 11-step ordinal scale; differences smaller than ~10 percentile points are not meaningful
- `yoy_change_*` is reserved for v0.2+ and is always null in Beta 0.1

## 23. Roadmap

- **Beta 0.2** — multilingual keyword baskets, country-specific language
  queries, additional countries (including China via Chinese-language
  sources), 12-month rolling baselines, optional GDELT tone signal.
- **Beta 0.3** — Wikidata entity matching for higher-precision
  attribution, TMDb / MusicBrainz / IGDB metadata, automated country
  attribution, robust z-score as default normalization.
- **Beta 0.4** — optional human review layer; awards, festivals,
  exhibitions, prizes, art fairs, design awards, museum acquisitions, art
  auction data.
- **Version 1.0** — Global Arts and Culture Structural Index (separate
  from momentum), composite Momentum × Structural Index, sub-index weights
  re-evaluated using construct-validity studies.

---

## Worked example: Korea, May 2026 (illustrative)

1. **Collect**: GDELT returns deduplicated article counts for K-pop /
   Korean cinema / Korean theatre / etc. Wikipedia Pageviews returns
   monthly views for `K-pop`, `Squid_Game`, `Hangul`, etc. Google Books
   and Open Library return totalItems / numFound for the Korean
   Publishing/Literature and Webtoon book queries. Met and Art Institute
   of Chicago return object counts for Korean ceramics, Korean art, etc.
   Wikidata SPARQL counts entities with English labels matching Korean
   art/theatre/heritage keywords. Europeana is **disabled by default**
   because no API key is supplied.

2. **Normalize** every metric: `ln(1 + raw_value)`, then percentile-rank
   within (month × domain × signal × metric) across the 11 countries.

3. **Signal score** for `(Korea, Music, Global_Media_Attention)` is the
   mean of the normalized GDELT metrics (article-count and source-count).
   For `(Korea, Music, Wikipedia_Attention)` it is the normalized
   wikipedia-pageviews metric.

4. **Domain × sub-index score**:
   `(Korea, Music, GAC_Attention) = 0.55 * GMA_norm + 0.45 * Wiki_norm`.

5. **Sub-index score**: `(Korea, GAC_Attention)` is the equal-weighted
   mean of the 10 domain × sub-index scores under GAC-Attention.

6. **Composite**: `gacmi_composite(Korea) = 0.3334 * GAC_Attention(Korea)
   + 0.3333 * GAC_Discoverability(Korea) + 0.3333 *
   GAC_Institutional(Korea)`.

**Missing-Europeana redistribution.** Suppose `EUROPEANA_API_KEY` is not
set. For `(Korea, Heritage_Language, GAC_Institutional)`, the configured
weights are `Cultural_Heritage_Database_Visibility = 0.55` and
`Wikidata_Knowledge_Graph_Visibility = 0.45`. Met and ArtIC also produce
`Cultural_Heritage_Database_Visibility` for Heritage_Language, so the
heritage-database signal still has data — the only change is that one
contributing source is missing. Confidence for this cell drops slightly
(the source-confidence-weighted denominator stays the same, but the
"missing optional source" is reflected in the missing_sources annotation).
If the heritage-database signal had **no** contributing sources at all,
its weight (0.55) would be redistributed to the Wikidata signal (effective
weight 1.0) and confidence would drop accordingly.

## License

This project is for research and educational use. See `LICENSE` if added.
