"""이미지 HTML을 PNG로 렌더링합니다. 여백만큼 아래를 잘라냅니다."""
import subprocess
from pathlib import Path
from PIL import Image, ImageChops

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
HERE = Path(__file__).parent
OUT = HERE.parent / "images"
PAD = 60

for html in sorted(HERE.glob("*.html")):
    png = OUT / f"{html.stem}.png"
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--virtual-time-budget=5000", "--window-size=900,1800" if html.stem != "thumb" else "--window-size=900,900",
                    f"--screenshot={png}", html.as_uri()], check=True, capture_output=True)
    img = Image.open(png).convert("RGB")
    bg = Image.new("RGB", img.size, img.getpixel((img.width - 1, img.height - 1)))
    bbox = ImageChops.difference(img, bg).getbbox()
    if bbox and html.stem != "thumb":  # 썸네일은 900x900 정사각형 유지
        img = img.crop((0, 0, img.width, min(img.height, bbox[3] + PAD)))
    img.save(png, optimize=True)
    print(png.name, img.size)
