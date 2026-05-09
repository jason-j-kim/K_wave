"""BTS Wire — Frame · Member 자동 분류기 (v0.1.2)
- 영어 키워드 매칭에 단어 경계(word boundary) 적용
- 'RM'이 'ARMY' 안에서 잘못 매칭되던 핵심 버그 수정
- 'Jin' in 'Beijing', 'V' in 'MV' 같은 충돌도 함께 해결
- 한국어/일본어/한자 키워드는 단어 경계 개념이 없어 그대로 substring 매칭
"""
import json
import re
from pathlib import Path

FRAME_KEYWORDS = {
    'Industry': ['HYBE', '빅히트', 'contract', 'deal', '계약', '음반', 'sales', '매출', 'revenue', 'earnings', 'stock', '주가'],
    'Music':    ['comeback', 'MV', 'music video', '뮤비', 'single', 'album', '앨범', 'chart', 'Billboard', 'Spotify', 'streaming', 'song', 'track', '복귀', 'カムバック'],
    'Style':    ['fashion', 'Dior', 'Louis Vuitton', 'Cartier', 'Gucci', 'Tiffany', 'brand', 'ambassador', '앰배서더', 'パリ', 'ファッション', 'moda'],
    'Society':  ['military', 'service', 'discharge', '제대', '입대', 'diplomacy', 'soft power', '외교', 'cultural', '除隊', '退伍'],
    'Fandom':   ['ARMY', 'fan', 'fans', '팬', 'tour', 'concert', '콘서트', 'meeting', 'reunion', 'meetup', 'fandom'],
    'Gossip':   ['dating', 'scandal', '열애', '루머', 'controversy', '논란', 'rumor', 'gossip'],
}

MEMBERS = {
    'RM':    ['RM', 'Kim Namjoon', '김남준', 'ナムジュン', 'NAMJUN'],
    'Jin':   ['Jin', '진', 'Kim Seokjin', '김석진', 'Seokjin'],
    'SUGA':  ['SUGA', 'Suga', '슈가', 'Min Yoongi', '민윤기', 'Agust D'],
    'jhope': ['j-hope', 'J-Hope', 'JHope', '제이홉', 'Jung Hoseok', 'Hobi'],
    'Jimin': ['Jimin', '지민', 'Park Jimin', '박지민', 'ジミン'],
    'V':     ['V', 'Taehyung', '뷔', '태형', 'Kim Taehyung', 'テヒョン'],
    'JK':    ['Jung Kook', 'Jungkook', 'JK', '정국', 'Jeon Jungkook', 'ジョングク'],
}


def is_ascii_word(s):
    """영어 알파벳/공백/하이픈만으로 이루어진 키워드인지"""
    return all(c.isascii() for c in s)


def matches(keyword, text):
    """키워드 매칭. 영어는 단어 경계, 한국어/일본어는 substring."""
    if is_ascii_word(keyword):
        return bool(re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE))
    return keyword in text


def classify_frame(title):
    scores = {}
    for f, kws in FRAME_KEYWORDS.items():
        scores[f] = sum(1 for k in kws if matches(k, title))
    if max(scores.values()) == 0:
        return 'Music'  # default
    return max(scores, key=scores.get)


def classify_members(title):
    found = []
    for m, names in MEMBERS.items():
        for name in names:
            if matches(name, title):
                found.append(m)
                break
    return found


def main():
    raw = json.loads(Path('data/raw_today.json').read_text(encoding='utf-8'))
    for item in raw['items']:
        item['frame'] = classify_frame(item['title'])
        item['members'] = classify_members(item['title'])
    out = Path('data/classified_today.json')
    out.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'classified {len(raw["items"])} items')


if __name__ == '__main__':
    main()
