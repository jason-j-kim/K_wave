"""BTS Wire — Daily News Collector
Google News RSS를 통해 6개 권역의 BTS 관련 보도를 수집한다.
"""
import feedparser
import json
from datetime import datetime, timezone
from pathlib import Path

REGIONS = {
    'KR':    [('https://news.google.com/rss/search?q=BTS+OR+%EB%B0%A9%ED%83%84%EC%86%8C%EB%85%84%EB%8B%A8&hl=ko&gl=KR&ceid=KR:ko', 'ko')],
    'US':    [('https://news.google.com/rss/search?q=BTS+kpop&hl=en-US&gl=US&ceid=US:en', 'en')],
    'LATAM': [
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=es-419&gl=MX&ceid=MX:es-419', 'es'),
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=pt-BR&gl=BR&ceid=BR:pt-419', 'pt'),
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=es&gl=AR&ceid=AR:es-419', 'es'),
    ],
    'EU':    [
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=en-GB&gl=GB&ceid=GB:en', 'en'),
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=fr&gl=FR&ceid=FR:fr', 'fr'),
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=de&gl=DE&ceid=DE:de', 'de'),
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=es&gl=ES&ceid=ES:es', 'es'),
    ],
    'AF':    [
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=en&gl=ZA&ceid=ZA:en', 'en'),
        ('https://news.google.com/rss/search?q=BTS+kpop&hl=en&gl=NG&ceid=NG:en', 'en'),
    ],
    'ASIA':  [
        ('https://news.google.com/rss/search?q=BTS&hl=ja&gl=JP&ceid=JP:ja', 'ja'),
    ],
}


def get_source(entry):
    """Google News RSS의 제목은 보통 'Headline - Source Name' 형식."""
    title = entry.get('title', '')
    if ' - ' in title:
        return title.rsplit(' - ', 1)[1]
    src = entry.get('source')
    if isinstance(src, dict):
        return src.get('title', '')
    if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
        return entry.source.title
    return ''


def get_clean_title(entry):
    title = entry.get('title', '')
    if ' - ' in title:
        return title.rsplit(' - ', 1)[0]
    return title


def collect_region(region, feeds):
    items = []
    for url, lang in feeds:
        try:
            d = feedparser.parse(url)
            for e in d.entries[:30]:
                items.append({
                    'title': get_clean_title(e),
                    'link': e.get('link', ''),
                    'published': e.get('published', ''),
                    'source': get_source(e),
                    'lang': lang,
                    'region': region,
                })
        except Exception as ex:
            print(f'[{region}] feed error: {ex}')
    return items


def main():
    all_items = []
    for region, feeds in REGIONS.items():
        items = collect_region(region, feeds)
        print(f'[{region}] {len(items)} items')
        all_items.extend(items)
    out = Path('data/raw_today.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        'collectedAt': datetime.now(timezone.utc).isoformat(),
        'count': len(all_items),
        'items': all_items,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {out} ({len(all_items)} items)')


if __name__ == '__main__':
    main()
