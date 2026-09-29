"""생활경제 블로그 초안 생성기 (Claude API).

patterns.py로 뽑은 '제목 후킹 패턴'을 참고해 제목 후보와 본문 초안을 새로 씁니다.
참고 블로거의 글 본문은 입력으로 쓰지 않습니다.

사용법:
    export ANTHROPIC_API_KEY=...
    python generate.py --topic "축의금" --keyword "축의금 적정 금액" --facts data/facts_축의금.txt
    -> output/2026-09-29_축의금.md 생성
"""

import argparse
import datetime as dt
import json
from pathlib import Path

import anthropic

BASE = Path(__file__).parent
MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = """당신은 네이버 생활경제 블로그 작가입니다. 돈 때문에 생기는 인간관계 갈등(축의금, 데이트 통장, 더치페이, 용돈, 결혼 비용 등)을 소재로, 사람들이 클릭하고 끝까지 읽는 글을 씁니다.

# 제목
- 관계 인물 + 돈 이슈 + 감정 반응 + 궁금증 장치를 조합해 한 번에 눈에 들어오게 씁니다.
  예) "축의금 3만 원 냈던 친구가 보낸 택배", "데이트 통장 반반하자는 말에 정떨어진다는 여친"
- 구체적인 금액과 짧은 장면 하나로 감정을 건드립니다. 25~35자 안팎.
- 제목이 약속한 내용은 본문에서 반드시 다룹니다. 본문에 없는 반전이나 결말을 제목에 넣지 않습니다.

# 본문 구조
- 서론: 누구나 겪어봤을 법한 장면으로 시작합니다. 이 장면은 '이런 상황, 한 번쯤 겪어보셨죠?'처럼 가상 사례임이 드러나게 씁니다. 실화, 제보, 지인 이야기라고 쓰지 않습니다.
- 본론: 소제목(## ) 3~5개. 양쪽 입장을 공정하게 보여주고, 실제로 도움이 되는 경제 정보(평균 금액, 계산 방법, 제도, 현실적인 해결책)를 쉽게 풀어 씁니다.
- 결론: 핵심 정리와 함께 독자에게 '여러분이라면 어떻게 하시겠어요?' 같은 질문을 던져 댓글을 유도합니다.

# 사실 관계
- 통계, 금액, 제도 설명은 사용자가 준 [참고 자료]에 있는 내용만 씁니다.
- 자료에 없는 구체적 수치가 필요하면 지어내지 말고 그 자리에 [확인 필요]라고 표시합니다.

# 키워드와 가독성
- 대표 키워드는 서론 첫 문단에 자연스럽게 넣고, 본문 전체에서 3~6회만 씁니다. 7회 이상 쓰지 않습니다.
- 모바일에서 읽기 좋게 한 문단은 1~3문장으로 짧게 쓰고, 문단 사이에는 빈 줄을 넣습니다.
- 어려운 용어는 비유를 들어 쉽게 풀어 씁니다. 전체 분량은 1,800~2,500자입니다.

# 출력 형식 (정확히 이 순서)
[제목 후보]
1. ...
2. ...
3. ...
4. ...
5. ...

[추천 제목]
(후보 중 가장 좋은 것 하나)

[본문]
(마크다운 본문)

[해시태그]
#... (8~10개)
"""


def load_pattern_summary() -> str:
    path = BASE / "data" / "patterns.json"
    if not path.exists():
        return "(패턴 리포트 없음)"
    report = json.loads(path.read_text(encoding="utf-8"))
    examples = "\n".join(f"- {t['title']}" for t in report["best_examples"][:10])
    words = {g: [w for w, _ in ws[:8]] for g, ws in report["top_words"].items()}
    return (
        f"평균 제목 길이: {report['avg_length']}자, 금액 포함 비율: {report['amount_ratio']:.0%}\n"
        f"자주 쓰는 단어: {json.dumps(words, ensure_ascii=False)}\n"
        f"자주 쓰인 조합: {report['top_combos'][:5]}\n"
        f"후킹이 강한 제목 구조 예시 (구조만 참고하고 그대로 베끼지 말 것):\n{examples}"
    )


def generate(topic: str, keyword: str, facts: str) -> str:
    client = anthropic.Anthropic()
    user_msg = (
        f"주제: {topic}\n대표 키워드: {keyword}\n\n"
        f"[잘 되는 제목 패턴]\n{load_pattern_summary()}\n\n"
        f"[참고 자료]\n{facts or '(없음 - 구체적 수치는 [확인 필요]로 표시)'}\n\n"
        "위 규칙대로 새로운 글을 써주세요."
    )

    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        # 시스템 프롬프트는 매번 같으므로 캐싱해서 비용을 줄입니다.
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "refusal":
        raise RuntimeError("모델이 이 요청을 거절했습니다. 주제나 자료를 바꿔 다시 시도하세요.")
    return "".join(b.text for b in response.content if b.type == "text")


def main() -> None:
    parser = argparse.ArgumentParser(description="블로그 초안 생성")
    parser.add_argument("--topic", required=True, help="글 주제 (예: 축의금)")
    parser.add_argument("--keyword", required=True, help="대표 키워드 (예: 축의금 적정 금액)")
    parser.add_argument("--facts", help="통계/제도 등 참고 자료 텍스트 파일 (출처 포함 권장)")
    args = parser.parse_args()

    facts = Path(args.facts).read_text(encoding="utf-8") if args.facts else ""
    draft = generate(args.topic, args.keyword, facts)

    out_dir = BASE / "output"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{dt.date.today()}_{args.topic.replace(' ', '_')}.md"
    out.write_text(draft, encoding="utf-8")
    print(draft)
    print(f"\n저장: {out}\n다음 단계: python check.py {out} --keyword \"{args.keyword}\"")


if __name__ == "__main__":
    main()
