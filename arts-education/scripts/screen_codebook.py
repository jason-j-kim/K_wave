#!/usr/bin/env python3
"""마이크로데이터 문항 선별기.

국민문화예술교육조사(MDIS)를 비롯한 조사자료를 받자마자 돌려서
"이 자료에 처치 변수와 결과 변수가 실제로 있는가"를 판정한다.

    python3 screen_codebook.py <파일 또는 폴더> [-o 보고서.md]

지원 형식: .sav(SPSS) .dta(Stata) .csv .xlsx
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# 변수를 분류하는 키워드. 라벨과 변수명 양쪽에 적용한다.
BUCKETS: dict[str, tuple[str, ...]] = {
    "처치·예술교육": (
        "문화예술교육", "예술교육", "예능", "예체능", "미술", "음악", "무용",
        "연극", "공예", "사진", "영화", "문학", "국악", "악기", "강좌", "수강",
        "배운", "배우", "교육경험", "교육참여", "동아리", "방과후", "특기적성",
        "art", "music", "educ",
    ),
    "결과·웰빙": (
        "행복", "만족", "삶의", "생활만족", "우울", "스트레스", "자아존중",
        "자존감", "외로", "고립", "불안", "정서", "의미", "가치있", "보람",
        "웰빙", "심리", "happi", "satisf", "depress", "wellbe", "ces",
    ),
    "매개·태도": (
        "인식", "관심", "중요", "필요", "수요", "의향", "효과", "도움",
        "신뢰", "공정", "관계", "소속",
    ),
    "통제·인구": (
        "성별", "연령", "나이", "소득", "학력", "교육수준", "지역", "시도",
        "가구", "직업", "혼인", "건강", "가중치", "weight", "sex", "age",
        "income", "regio",
    ),
}

# 결과변수 판정에 쓰는 강한 신호. 하나라도 잡히면 "결과변수 있음".
STRONG_OUTCOME = ("행복", "삶의 만족", "삶에 대한 만족", "생활만족",
                  "우울", "자아존중", "외로", "웰빙")


def read_any(path: Path) -> tuple[pd.DataFrame, dict[str, str], dict[str, dict]]:
    """(데이터, 변수명→라벨, 변수명→값라벨)을 돌려준다."""
    suffix = path.suffix.lower()
    labels: dict[str, str] = {}
    value_labels: dict[str, dict] = {}

    if suffix in (".sav", ".zsav", ".dta", ".por"):
        import pyreadstat

        reader = {
            ".sav": pyreadstat.read_sav,
            ".zsav": pyreadstat.read_sav,
            ".por": pyreadstat.read_por,
            ".dta": pyreadstat.read_dta,
        }[suffix]
        df, meta = reader(str(path))
        labels = dict(meta.column_names_to_labels or {})
        value_labels = dict(meta.variable_value_labels or {})
    elif suffix == ".csv":
        for enc in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
            try:
                df = pd.read_csv(path, encoding=enc, low_memory=False)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise RuntimeError(f"인코딩을 찾지 못했다: {path}")
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        raise RuntimeError(f"지원하지 않는 형식: {suffix}")

    return df, labels, value_labels


def classify(name: str, label: str) -> list[str]:
    haystack = f"{name} {label}".lower()
    return [b for b, kws in BUCKETS.items()
            if any(k.lower() in haystack for k in kws)]


def describe(series: pd.Series) -> str:
    n = len(series)
    missing = series.isna().sum()
    uniq = series.nunique(dropna=True)
    bits = [f"결측 {missing}/{n} ({missing / n:.1%})" if n else "빈 자료",
            f"고유값 {uniq}"]
    if pd.api.types.is_numeric_dtype(series) and uniq > 1:
        bits.append(f"범위 {series.min():g}~{series.max():g}")
    return ", ".join(bits)


def screen(path: Path) -> list[str]:
    out: list[str] = [f"\n## {path.name}\n"]
    try:
        df, labels, value_labels = read_any(path)
    except Exception as exc:  # 형식이 낯설어도 나머지 파일은 계속 본다
        out.append(f"읽지 못했다: {exc}\n")
        return out

    out.append(f"관측치 {len(df):,}행, 변수 {len(df.columns):,}개\n")

    found: dict[str, list[str]] = {b: [] for b in BUCKETS}
    for col in df.columns:
        label = labels.get(col, "")
        for bucket in classify(str(col), str(label)):
            found[bucket].append(col)

    outcome_hits: list[str] = []
    for bucket, cols in found.items():
        out.append(f"\n### {bucket} — {len(cols)}개\n")
        if not cols:
            out.append("해당 없음.\n")
            continue
        out.append("| 변수 | 라벨 | 분포 | 값 라벨 |")
        out.append("|---|---|---|---|")
        for col in cols[:60]:
            label = str(labels.get(col, "")).replace("|", "/")
            vl = value_labels.get(col, {})
            vl_txt = ", ".join(f"{k}={v}" for k, v in list(vl.items())[:6])
            if len(vl) > 6:
                vl_txt += f" … (총 {len(vl)})"
            out.append(f"| `{col}` | {label} | {describe(df[col])} | {vl_txt} |")
            if bucket == "결과·웰빙" and any(
                s in f"{col} {label}" for s in STRONG_OUTCOME
            ):
                outcome_hits.append(f"{col} ({label})")
        if len(cols) > 60:
            out.append(f"\n… 외 {len(cols) - 60}개 생략.\n")

    out.append("\n### 판정\n")
    treat = found["처치·예술교육"]
    out.append(f"- 처치 후보 {len(treat)}개"
               + (f": {', '.join(treat[:8])}" if treat else " — **없다**"))
    if outcome_hits:
        out.append(f"- **결과변수 있음** ({len(outcome_hits)}개): "
                   + "; ".join(outcome_hits[:8]))
        out.append("- → 처치와 결과가 같은 자료에 있다. 횡단이라도 기술분석이 가능하다.")
    else:
        out.append("- **강한 결과변수 없음.** 만족도 문항이 있다면 "
                   "프로그램 만족이지 삶의 만족이 아닐 가능성이 높다.")
        out.append("- → 이 자료는 처치 측정 전용으로 쓰고, 결과는 패널 자료에서 가져온다.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", type=Path, help="데이터 파일 또는 폴더")
    ap.add_argument("-o", "--out", type=Path, help="마크다운 보고서 저장 경로")
    args = ap.parse_args()

    if args.target.is_dir():
        files = sorted(p for p in args.target.rglob("*")
                       if p.suffix.lower() in
                       (".sav", ".zsav", ".por", ".dta", ".csv", ".xlsx", ".xls"))
    else:
        files = [args.target]

    if not files:
        print(f"데이터 파일을 찾지 못했다: {args.target}", file=sys.stderr)
        return 1

    lines = [f"# 문항 선별 보고 — {args.target}", f"\n대상 파일 {len(files)}개."]
    for f in files:
        lines += screen(f)

    report = "\n".join(lines)
    print(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"\n저장: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
