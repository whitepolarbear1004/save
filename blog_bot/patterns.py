"""제목 후킹 패턴 분석기.

잘 되는 제목을 '관계 인물 + 돈 이슈 + 감정 반응 + 궁금증 장치'로 쪼개서
어떤 조합이 자주 쓰이는지 통계를 냅니다. 글 내용은 쓰지 않고 제목 구조만 봅니다.

사용법:
    python patterns.py                          # data/titles.json 분석
    python patterns.py --titles "제목1" "제목2"   # 직접 입력한 제목 분석
    -> data/patterns.json, data/patterns.md 생성
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# 제목을 구성하는 후킹 요소 사전. 분석 결과를 보며 계속 늘려가면 됩니다.
LEXICON = {
    "화제종목": [
        "삼성전자", "SK하이닉스", "하이닉스", "삼전닉스", "카카오", "네이버", "코스피", "나스닥", "S&P500",
        "ETF", "커버드콜", "월배당", "배당금", "배당", "비트코인", "ISA", "상한가", "상장",
    ],
    "정책지원금": [
        "근로장려금", "국민연금", "건강보험료", "건보료", "기초생활수급", "생계급여", "실업급여", "민생지원금",
        "온누리상품권", "청년미래적금", "도약장려금", "내일배움카드", "특례대출", "증여세", "소득세", "세금",
    ],
    "사람·세대": [
        "20대", "30대", "40대", "50대", "60대", "70대", "MZ", "직장인", "자영업", "부부", "서민", "개미", "서학개미",
    ],
    "관계인물": [
        "여친", "남친", "여자친구", "남자친구", "아내", "남편", "와이프", "신랑", "예비신부", "예비신랑",
        "시어머니", "시아버지", "시댁", "시누이", "장모", "장인어른", "처가", "며느리", "사위",
        "친구", "절친", "동창", "동료", "직장동료", "상사", "팀장", "부장", "사장", "후배", "선배",
        "부모", "엄마", "아빠", "형", "누나", "언니", "오빠", "동생", "조카", "이웃", "집주인", "세입자",
    ],
    "돈이슈": [
        "축의금", "부조금", "조의금", "데이트 통장", "데이트통장", "반반", "더치페이", "용돈", "월급",
        "연봉", "보너스", "성과급", "전세", "월세", "보증금", "대출", "빚", "적금", "주식", "코인",
        "생활비", "결혼비용", "혼수", "예단", "집값", "명절", "세뱃돈", "선물", "택배", "계산", "밥값",
        "커피값", "할부", "카드값", "상속", "유산", "청약",
    ],
    "손실후회": [
        "샀다가", "넣었다가", "물렸다", "날렸", "털린", "무너", "망한", "손절", "지옥", "폭탄", "날벼락", "후회", "싹둑",
    ],
    "감정반응": [
        "정떨어", "황당", "서운", "어이없", "화나", "빡", "분노", "충격", "소름", "눈물", "울컥",
        "실망", "당황", "기막", "민망", "섭섭", "괘씸", "파혼", "이혼", "싸움", "갈등",
        "입장 차이", "논란", "갑론을박", "시끌",
    ],
    "궁금증장치": [
        "보낸", "알고 보니", "알고보니", "결국", "이유", "그 후", "그후", "반전", "뜻밖", "의외",
        "한마디", "반응", "정체", "사연", "했더니", "하자는 말", "라는 말", "둘러싼", "때문에",
        "얼마길래", "뭐길래", "하길래", "나왔길래", "무슨 일", "근황", "따져보니", "계산해 보니", "계산해보니",
        "알아봤더니", "찾아봤더니", "모았더니", "생긴 일", "비결", "현실", "속마음", "어디까지",
    ],
}

QUOTE_RE = re.compile(r"^[\"'“‘]")  # 제목이 따옴표 인용으로 시작
MONEY_RE = re.compile(r"\d[\d,]*\s*(만\s*원|천\s*원|억|원|만원|만)")


def tag_title(title: str) -> dict:
    tags = {group: [w for w in words if w in title] for group, words in LEXICON.items()}
    return {
        "title": title,
        "length": len(title),
        "has_amount": bool(MONEY_RE.search(title)),
        "is_question": "?" in title,
        "starts_with_quote": bool(QUOTE_RE.match(title)),
        "tags": {k: v for k, v in tags.items() if v},
        # 인물/돈/감정/궁금증 중 몇 가지를 섞었는지 = 후킹 강도
        "hook_score": sum(1 for v in tags.values() if v)
        + (1 if MONEY_RE.search(title) else 0)
        + (1 if QUOTE_RE.match(title) else 0),
    }


def analyze(titles: list[str]) -> dict:
    tagged = [tag_title(t) for t in titles if t.strip()]
    n = len(tagged) or 1

    word_counts = {group: Counter() for group in LEXICON}
    combo_counts = Counter()
    for t in tagged:
        for group, words in t["tags"].items():
            word_counts[group].update(words)
        combo = " + ".join(sorted(t["tags"].keys()) + (["구체금액"] if t["has_amount"] else []))
        combo_counts[combo or "(패턴 없음)"] += 1

    lengths = sorted(t["length"] for t in tagged)
    return {
        "count": len(tagged),
        "avg_length": round(sum(lengths) / n, 1),
        "median_length": lengths[len(lengths) // 2] if lengths else 0,
        "amount_ratio": round(sum(t["has_amount"] for t in tagged) / n, 2),
        "question_ratio": round(sum(t["is_question"] for t in tagged) / n, 2),
        "quote_ratio": round(sum(t["starts_with_quote"] for t in tagged) / n, 2),
        "group_ratio": {g: round(sum(1 for t in tagged if g in t["tags"]) / n, 2) for g in LEXICON},
        "top_words": {g: c.most_common(10) for g, c in word_counts.items()},
        "top_combos": combo_counts.most_common(10),
        "best_examples": sorted(tagged, key=lambda t: -t["hook_score"])[:10],
    }


def to_markdown(report: dict) -> str:
    lines = [
        "# 제목 후킹 패턴 리포트",
        "",
        f"- 분석한 제목 수: {report['count']}",
        f"- 평균 길이: {report['avg_length']}자 (중앙값 {report['median_length']}자)",
        f"- 구체적 금액 포함 비율: {report['amount_ratio']:.0%}",
        f"- 질문형 비율: {report['question_ratio']:.0%}",
        f"- 따옴표 인용으로 시작하는 비율: {report['quote_ratio']:.0%}",
        "",
        "## 요소별 사용 비율",
        "",
    ]
    for group, ratio in report["group_ratio"].items():
        words = ", ".join(f"{w}({c})" for w, c in report["top_words"][group]) or "-"
        lines.append(f"- **{group}** {ratio:.0%} — {words}")
    lines += ["", "## 자주 쓰인 조합", ""]
    lines += [f"- {combo}: {cnt}회" for combo, cnt in report["top_combos"]]
    lines += ["", "## 후킹 강도 높은 제목 예시", ""]
    lines += [f"- ({t['hook_score']}점) {t['title']}" for t in report["best_examples"]]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="제목 후킹 패턴 분석")
    parser.add_argument("--input", default=str(DATA_DIR / "titles.json"))
    parser.add_argument("--titles", nargs="*", help="분석할 제목을 직접 입력")
    args = parser.parse_args()

    if args.titles:
        titles = args.titles
    else:
        titles = [p["title"] for p in json.loads(Path(args.input).read_text(encoding="utf-8"))]

    report = analyze(titles)
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "patterns.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = to_markdown(report)
    (DATA_DIR / "patterns.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
