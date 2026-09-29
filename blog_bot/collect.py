"""참고 블로그의 공개 RSS에서 글 '제목'과 메타데이터만 수집합니다.

본문은 저장하지 않습니다. 제목 패턴 분석(patterns.py)에 필요한 정보만 모읍니다.

사용법:
    python collect.py sdedy rmsgud2007
    -> data/titles.json 생성
"""

import argparse
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

RSS_URL = "https://rss.blog.naver.com/{blog_id}.xml"
DATA_DIR = Path(__file__).parent / "data"
USER_AGENT = "Mozilla/5.0 (title-pattern-research)"


def fetch_titles(blog_id: str) -> list[dict]:
    req = urllib.request.Request(RSS_URL.format(blog_id=blog_id), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        root = ET.fromstring(resp.read())

    posts = []
    for item in root.iter("item"):
        posts.append({
            "blog_id": blog_id,
            "title": (item.findtext("title") or "").strip(),
            "category": (item.findtext("category") or "").strip(),
            "pub_date": (item.findtext("pubDate") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            # 본문 대신 길이만 기록 (글 분량 참고용)
            "summary_length": len(item.findtext("description") or ""),
        })
    return posts


def main() -> None:
    parser = argparse.ArgumentParser(description="네이버 블로그 RSS 제목 수집")
    parser.add_argument("blog_ids", nargs="+", help="블로그 아이디 (예: sdedy)")
    parser.add_argument("--out", default=str(DATA_DIR / "titles.json"))
    args = parser.parse_args()

    all_posts = []
    for blog_id in args.blog_ids:
        try:
            posts = fetch_titles(blog_id)
        except Exception as exc:  # 한 블로그가 실패해도 나머지는 계속 수집
            print(f"[실패] {blog_id}: {exc}", file=sys.stderr)
            continue
        print(f"[수집] {blog_id}: {len(posts)}개")
        all_posts.extend(posts)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(all_posts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: {out} (총 {len(all_posts)}개)")


if __name__ == "__main__":
    main()
