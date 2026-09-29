"""post.md를 네이버 에디터에 붙여넣기 좋은 미리보기 HTML로 바꿉니다.

사용법: python make_preview.py posts/2026-09-30_isa
-> posts/2026-09-30_isa/preview.html (브라우저로 열어 전체 선택 후 복사)
"""
import html
import re
import sys
from pathlib import Path

post_dir = Path(sys.argv[1])
text = (post_dir / "post.md").read_text(encoding="utf-8")
title = re.search(r"\[제목\]\n(.+)", text).group(1)
body = re.search(r"\[본문\]\n(.*?)\n\[해시태그\]", text, re.S).group(1)
tags = re.search(r"\[해시태그\]\n(.+)", text).group(1)

parts = []
for block in re.split(r"\n\s*\n", body.strip()):
    block = block.strip()
    if m := re.fullmatch(r"\[이미지: (.+?)\]", block):
        parts.append(f'<p><img src="{m.group(1)}" style="max-width:100%"></p>')
    elif block.startswith("## "):
        parts.append(f"<h2>{html.escape(block[3:])}</h2>")
    else:
        parts.append(f"<p>{html.escape(block)}</p><p><br></p>")

page = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>body{{max-width:700px;margin:40px auto;padding:0 16px;font-family:sans-serif;line-height:1.8;font-size:17px}}
h1{{font-size:24px}}h2{{font-size:20px;margin-top:32px}}.tags{{color:#2a78d6}}</style></head><body>
<h1>{html.escape(title)}</h1>
{''.join(parts)}
<p class="tags">{html.escape(tags)}</p>
</body></html>"""
(post_dir / "preview.html").write_text(page, encoding="utf-8")
print(f"저장: {post_dir / 'preview.html'}")
