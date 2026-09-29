"""발행 전 점검기: 네이버 SEO 규칙과 기본 안전장치를 확인합니다.

사용법:
    python check.py output/2026-09-29_축의금.md --keyword "축의금 적정 금액"
"""

import argparse
import re
import sys
from pathlib import Path

MAX_KEYWORD = 6  # 키워드는 7번 이상 넣지 않는다
# 지어낸 이야기를 실제 사연처럼 보이게 하는 표현
FAKE_STORY_WORDS = ["실화", "제보받은", "제보 받은", "실제 사연", "제 친구 이야기", "지인 실화"]


def check(text: str, keyword: str) -> list[str]:
    problems = []

    count = text.count(keyword)
    if count == 0:
        problems.append(f"키워드 '{keyword}'가 본문에 없습니다.")
    elif count > MAX_KEYWORD:
        problems.append(f"키워드 '{keyword}'가 {count}번 들어갔습니다. {MAX_KEYWORD}번 이하로 줄이세요.")

    if len(re.findall(r"^##\s", text, re.M)) < 3:
        problems.append("소제목(##)이 3개 미만입니다.")

    # 모바일 가독성: 빈 줄 없이 붙어 있는 긴 문단 찾기
    for block in re.split(r"\n\s*\n", text):
        body_lines = [ln for ln in block.splitlines() if ln.strip() and not ln.startswith("#")]
        if len(body_lines) >= 4:
            problems.append(f"문단이 너무 깁니다(줄바꿈 두 번 필요): {body_lines[0][:30]}...")

    for word in FAKE_STORY_WORDS:
        if word in text:
            problems.append(f"'{word}' 표현이 있습니다. 가상 사례는 실제 사연처럼 쓰지 마세요.")

    if "[확인 필요]" in text:
        problems.append("[확인 필요] 표시가 남아 있습니다. 수치를 직접 확인하세요.")

    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="발행 전 점검")
    parser.add_argument("file")
    parser.add_argument("--keyword", required=True)
    args = parser.parse_args()

    text = Path(args.file).read_text(encoding="utf-8")
    # generate.py 출력이면 [본문] 부분만 점검 (제목 후보는 키워드 횟수에서 제외)
    body = re.search(r"\[본문\](.*?)(\[해시태그\]|$)", text, re.S)
    problems = check(body.group(1) if body else text, args.keyword)
    if problems:
        print("점검 결과: 수정 필요")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("점검 결과: 통과")


if __name__ == "__main__":
    main()
