#!/usr/bin/env python3
"""
make-og-entre-espiritu-y-custodia.py

Builds assets/og-entre-espiritu-y-custodia.png, the Open Graph card for
entre-espiritu-y-custodia.html.

Layout: the IV Encuentro invitation centered in the upper area, scaled down,
with the IHS identification block beneath it. Palette matches generate-og.py.

Run from the repo root:
    python scripts/make-og-entre-espiritu-y-custodia.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent.parent
ASSETS = BASE / "assets"

W, H = 1200, 630
GREEN = (30, 74, 39)
CREAM = (237, 234, 208)


def blend(c, alpha):
    return tuple(int(c[i] * alpha + GREEN[i] * (1 - alpha)) for i in range(3))


COL_TITLE = CREAM
COL_SUB = blend(CREAM, 0.72)
COL_MARK = blend(CREAM, 0.46)

FONT_CANDIDATES = {
    "serif_bold": [
        BASE / "fonts" / "eb_garamond_700.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        Path("C:/Windows/Fonts/garabd.ttf"),
        Path("/System/Library/Fonts/Supplemental/Georgia Bold.ttf"),
    ],
    "sans": [
        BASE / "fonts" / "source_sans_3_400.ttf",
        Path("/usr/share/fonts/truetype/lato/Lato-Regular.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ],
    "sans_semibold": [
        BASE / "fonts" / "source_sans_3_600.ttf",
        Path("/usr/share/fonts/truetype/lato/Lato-Semibold.ttf"),
        Path("/usr/share/fonts/truetype/lato/Lato-Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ],
}


def font(kind, size):
    for p in FONT_CANDIDATES[kind]:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


def text_w(draw, s, f, tracking=0):
    if not tracking:
        return draw.textlength(s, font=f)
    return sum(draw.textlength(ch, font=f) for ch in s) + tracking * (len(s) - 1)


def draw_centered(draw, y, s, f, fill, tracking=0):
    x = (W - text_w(draw, s, f, tracking)) / 2
    if not tracking:
        draw.text((x, y), s, font=f, fill=fill)
        return
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking


def main():
    img = Image.new("RGB", (W, H), GREEN)
    draw = ImageDraw.Draw(img)

    # thin cream rule top and bottom, matches the site's banded chrome
    draw.rectangle([0, 0, W, 5], fill=blend(CREAM, 0.30))
    draw.rectangle([0, H - 5, W, H], fill=blend(CREAM, 0.30))

    # ---- flyer, centered in the upper area, scaled down ----
    flyer = Image.open(ASSETS / "flyer-iv-encuentro-2026.jpg").convert("RGB")
    target_h = 416
    target_w = int(flyer.width * (target_h / flyer.height))
    flyer = flyer.resize((target_w, target_h), Image.LANCZOS)

    fx = (W - target_w) // 2
    fy = 38

    # 3px cream keyline so the white flyer edge reads against the green
    draw.rectangle([fx - 3, fy - 3, fx + target_w + 2, fy + target_h + 2],
                   fill=blend(CREAM, 0.85))
    img.paste(flyer, (fx, fy))

    # ---- identification block beneath ----
    f_title = font("serif_bold", 36)
    f_sub = font("sans", 21)
    f_mark = font("sans_semibold", 15)

    y = fy + target_h + 24
    draw_centered(draw, y, "Entre Espíritu y Custodia", f_title, COL_TITLE)
    y += 46
    draw_centered(draw, y,
                  "Biblioteca Nacional de Cuba José Martí  ·  Ediciones Bachiller  ·  2026",
                  f_sub, COL_SUB)
    y += 33
    draw_centered(draw, y, "IROKO HISTORICAL SOCIETY   ·   IROKOSOCIETY.ORG",
                  f_mark, COL_MARK, tracking=2.4)

    out = ASSETS / "og-entre-espiritu-y-custodia.png"
    img.save(out, "PNG", optimize=True)
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
