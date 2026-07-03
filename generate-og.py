#!/usr/bin/env python3
"""
generate-og.py — IHS Open Graph Image Generator
================================================
Run from the IHS-Website directory:

    pip install Pillow requests
    python generate-og.py

What it does:
  1. Downloads EB Garamond Bold, EB Garamond Italic, and Source Sans 3 into fonts/
  2. Generates 1200×630 branded PNG files into assets/
  3. Injects/updates og: and twitter: meta tags in each HTML file

Run with --force to regenerate PNGs that already exist.
"""

import io
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Optional

# ── dependency check ──────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Missing Pillow. Run: pip install Pillow requests")
try:
    import requests
except ImportError:
    sys.exit("Missing requests. Run: pip install Pillow requests")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent.resolve()
ASSETS = BASE / "assets"
FONTS  = BASE / "fonts"
FONTS.mkdir(exist_ok=True)

BASE_URL  = "https://irokosociety.org"
LOGO_PATH = ASSETS / "IHS-Logo.jpg"

FORCE = "--force" in sys.argv

# ── colors ────────────────────────────────────────────────────────────────────
GREEN      = (30,  74,  39)
CREAM_BOX  = (246, 241, 221)   # logo panel background

def _blend(c, alpha):
    """Alpha-composite cream color onto green background."""
    return tuple(int(c[i] * alpha + GREEN[i] * (1 - alpha)) for i in range(3))

CREAM      = (237, 234, 208)
COL_LABEL  = _blend(CREAM, 0.60)
COL_TITLE  = CREAM
COL_SUB    = _blend(CREAM, 0.75)
COL_DOMAIN = _blend(CREAM, 0.40)

# ── layout constants ──────────────────────────────────────────────────────────
W, H = 1200, 630

# Logo-box layout (used by all non-photo pages)
LOGO_BOX = dict(x=75, y=180, w=269, h=269)   # exact pixel measurements
TEXT_X_LOGO = LOGO_BOX["x"] + LOGO_BOX["w"] + 75   # ≈419

# Photo layout (visual-ethnography)
PHOTO_W, PHOTO_H = 380, 480
PHOTO_X = 72
PHOTO_Y = (H - PHOTO_H) // 2   # vertically centered = 75
TEXT_X_PHOTO = PHOTO_X + PHOTO_W + 64   # ≈516

# Text column right margin
RIGHT_PAD = 72

# Vertical positions (right-panel text)
LABEL_Y  = 170
TITLE_OFFSET_FROM_LABEL = 38   # px gap between label baseline and title top

# Font sizes
SZ_LABEL  = 18
SZ_TITLE  = 62
SZ_SUB    = 26
SZ_DOMAIN = 16

# ── font management ───────────────────────────────────────────────────────────
_FONT_SPECS = {
    "garamond_bold": ("EB Garamond",   "700", "0"),
    "garamond_ital": ("EB Garamond",   "400", "1"),
    "sourcesans":    ("Source Sans 3", "400", "0"),
}

_font_cache: dict = {}


def _download_font(key: str) -> Optional[Path]:
    dest = FONTS / f"{key}.ttf"
    if dest.exists():
        return dest
    family, weight, ital = _FONT_SPECS[key]
    family_param = family.replace(" ", "+")
    css_url = (
        f"https://fonts.googleapis.com/css2"
        f"?family={family_param}:ital,wght@{ital},{weight}"
    )
    # Request with an old User-Agent so Google returns TTF (not WOFF2)
    headers = {"User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"}
    print(f"  Downloading font: {family} {weight}{'i' if ital=='1' else ''} …")
    try:
        css = requests.get(css_url, headers=headers, timeout=15).text
        urls = re.findall(r"url\(([^)]+\.ttf)\)", css)
        if not urls:
            print(f"  WARNING: no TTF URL found for {family}. Skipping.")
            return None
        r = requests.get(urls[0], headers=headers, timeout=30)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  Saved → fonts/{key}.ttf")
        return dest
    except Exception as e:
        print(f"  WARNING: could not download {family}: {e}")
        return None


def get_font(key: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (key, size)
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    path = FONTS / f"{key}.ttf"
    if not path.exists():
        path = _download_font(key)

    if path and path.exists():
        f = ImageFont.truetype(str(path), size)
    else:
        # System-font fallbacks (Linux / macOS / Windows)
        fallbacks = {
            "garamond_bold": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
                "C:/Windows/Fonts/garabd.ttf",
                "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
            ],
            "garamond_ital": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
                "C:/Windows/Fonts/garait.ttf",
                "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf",
            ],
            "sourcesans":    [
                "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ],
        }
        f = None
        for fb in fallbacks.get(key, []):
            if os.path.exists(fb):
                try:
                    f = ImageFont.truetype(fb, size)
                    break
                except Exception:
                    continue
        if f is None:
            f = ImageFont.load_default()

    _font_cache[cache_key] = f
    return f


# ── text utilities ─────────────────────────────────────────────────────────────

def _text_w(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_h(draw: ImageDraw.ImageDraw, text: str, font) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list:
    """Word-wrap text to fit max_w pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if _text_w(draw, candidate, font) <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    x: int,
    y: int,
    max_w: int,
    color: tuple,
    leading_mult: float = 1.25,
) -> int:
    """Draw word-wrapped text. Returns y position after last line."""
    for line in wrap_text(draw, text, font, max_w):
        draw.text((x, y), line, font=font, fill=color)
        y += int(_text_h(draw, line, font) * leading_mult)
    return y


def auto_size_title(draw: ImageDraw.ImageDraw, title: str, max_w: int) -> tuple:
    """Return (font, size) that fits the title in ≤3 lines."""
    size = SZ_TITLE
    while size >= 32:
        f = get_font("garamond_bold", size)
        if len(wrap_text(draw, title, f, max_w)) <= 3:
            return f, size
        size -= 4
    return get_font("garamond_bold", 32), 32


# ── left-panel renderers ───────────────────────────────────────────────────────

def render_logo_panel(img: Image.Image) -> int:
    """Paste IHS logo into cream box. Returns text_x."""
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = LOGO_BOX["x"], LOGO_BOX["y"], LOGO_BOX["w"], LOGO_BOX["h"]
    draw.rectangle([bx, by, bx + bw, by + bh], fill=CREAM_BOX)
    logo = Image.open(LOGO_PATH).convert("RGB").resize((bw, bh), Image.LANCZOS)
    img.paste(logo, (bx, by))
    return TEXT_X_LOGO


def render_photo_panel(img: Image.Image, photo_url: str,
                       offset_x: int = 0, offset_y: int = 0) -> int:
    """Download and paste photo. Returns text_x.

    offset_x / offset_y: shift the crop window in pixels from the default
    centre position. Positive x moves the window right (reveals more of the
    left side of the source); positive y moves it down (reveals more of the
    top). Use negative values to go the other way.
    """
    print(f"    Downloading photo …")
    r = requests.get(photo_url, timeout=30)
    r.raise_for_status()
    photo = Image.open(io.BytesIO(r.content)).convert("RGB")

    # Fill-crop to PHOTO_W × PHOTO_H
    ph_ratio    = photo.width / photo.height
    panel_ratio = PHOTO_W / PHOTO_H
    if ph_ratio > panel_ratio:
        new_h = PHOTO_H
        new_w = int(photo.width * PHOTO_H / photo.height)
    else:
        new_w = PHOTO_W
        new_h = int(photo.height * PHOTO_W / photo.width)

    photo = photo.resize((new_w, new_h), Image.LANCZOS)

    # Default centre crop, shifted by offset
    left = max(0, min((new_w - PHOTO_W) // 2 + offset_x, new_w - PHOTO_W))
    top  = max(0, min((new_h - PHOTO_H) // 2 + offset_y, new_h - PHOTO_H))
    photo = photo.crop((left, top, left + PHOTO_W, top + PHOTO_H))
    img.paste(photo, (PHOTO_X, PHOTO_Y))
    return TEXT_X_PHOTO


# ── main image builder ─────────────────────────────────────────────────────────

def make_og_image(page: dict) -> Image.Image:
    img  = Image.new("RGB", (W, H), color=GREEN)
    draw = ImageDraw.Draw(img)

    # Left panel
    if page.get("layout") == "photo":
        text_x = render_photo_panel(
            img, page["photo_url"],
            offset_x=page.get("photo_offset_x", 0),
            offset_y=page.get("photo_offset_y", 0),
        )
    else:
        text_x = render_logo_panel(img)

    max_w = W - text_x - RIGHT_PAD

    # Label
    f_label = get_font("sourcesans", SZ_LABEL)
    draw.text((text_x, LABEL_Y), page["label"], font=f_label, fill=COL_LABEL)

    # Title (auto-size)
    f_title, _ = auto_size_title(draw, page["title"], max_w)
    title_y = LABEL_Y + TITLE_OFFSET_FROM_LABEL + _text_h(draw, "A", f_label)
    title_bottom = draw_wrapped(draw, page["title"], f_title, text_x, title_y, max_w, COL_TITLE, 1.15)

    # Subtitle
    f_sub = get_font("garamond_ital", SZ_SUB)
    sub_y = title_bottom + 20
    draw_wrapped(draw, page["subtitle"], f_sub, text_x, sub_y, max_w, COL_SUB, 1.45)

    # Domain (left-aligned with the label, title, and subtitle)
    f_domain  = get_font("sourcesans", SZ_DOMAIN)
    domain    = "irokosociety.org"
    dh        = _text_h(draw, domain, f_domain)
    draw.text((text_x, H - 42 - dh), domain, font=f_domain, fill=COL_DOMAIN)

    return img


# ── HTML meta-tag injection ────────────────────────────────────────────────────

OG_BLOCK = """\
  <meta property="og:type"        content="website">
  <meta property="og:site_name"   content="Iroko Historical Society">
  <meta property="og:title"       content="{og_title}">
  <meta property="og:description" content="{og_description}">
  <meta property="og:url"         content="{og_url}">
  <meta property="og:image"       content="{og_image}">
  <meta property="og:image:width"  content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:type"   content="image/png">
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="{og_title}">
  <meta name="twitter:description" content="{og_description}">
  <meta name="twitter:image"       content="{og_image}">"""


def inject_og_tags(html_path: Path, page: dict, png_filename: str) -> None:
    src = html_path.read_text(encoding="utf-8")

    og_image = f"{BASE_URL}/assets/{png_filename}"
    block    = OG_BLOCK.format(
        og_title       = page["og_title"],
        og_description = page["og_description"],
        og_url         = page["og_url"],
        og_image       = og_image,
    )

    # Remove any pre-existing og: / twitter: meta tags
    cleaned = re.sub(
        r'\s*<meta\s+(?:property="og:[^"]*"|property="twitter:[^"]*"|name="twitter:[^"]*")[^>]*>\n?',
        "",
        src,
        flags=re.IGNORECASE,
    )

    # Also update if og:image currently points at PhotoShelter CDN
    cleaned = re.sub(
        r'\s*<meta\s+property="og:image:(?:width|height|type)"[^>]*>\n?',
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Insert after </title> or after <meta charset…>
    if re.search(r"</title>", cleaned, re.IGNORECASE):
        new_src = re.sub(
            r"(</title>)",
            r"\1\n" + block,
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        new_src = re.sub(
            r"(<meta[^>]+charset[^>]*>)",
            r"\1\n" + block,
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )

    html_path.write_text(new_src, encoding="utf-8")


# ── page manifest ──────────────────────────────────────────────────────────────
#
#   slug        → output PNG filename (saved to assets/{slug}.png)
#   file        → path relative to IHS-Website root
#   layout      → 'logo' (default) or 'photo'
#   photo_url   → required when layout='photo'
#   label       → small-caps label in the top of the right panel (displayed on image)
#   title       → large Cinzel title (displayed on image)
#   subtitle    → italic subtitle (displayed on image)
#   og_title    → content for og:title meta tag
#   og_description → content for og:description meta tag
#   og_url      → content for og:url meta tag
#   skip        → True: don't regenerate PNG (existing hand-crafted image kept),
#                 but DO update HTML meta tags to point at it
#
PAGES = [
    # ── home ──────────────────────────────────────────────────────────────────
    dict(
        file       = "index.html",
        slug       = "og-home",
        label      = "IROKO · HISTORICAL SOCIETY",
        title      = "Iroko Historical Society",
        subtitle   = "A postcustodial cultural heritage complex for Afro-Atlantic sacred knowledge systems.",
        og_title   = "Iroko Historical Society",
        og_description = (
            "A postcustodial cultural heritage complex comprising a digital archive, "
            "research library, and living museum dedicated to Afro-Atlantic sacred knowledge systems."
        ),
        og_url     = f"{BASE_URL}/",
    ),
    # ── about ─────────────────────────────────────────────────────────────────
    dict(
        file       = "about.html",
        slug       = "og-about",
        label      = "IROKO · THE SOCIETY",
        title      = "About the Society",
        subtitle   = "Archive, research library, and living museum for the Afro-Atlantic world.",
        og_title   = "About the Society — Iroko Historical Society",
        og_description = (
            "The Iroko Historical Society is a postcustodial archive, research library, "
            "and living museum documenting sacred knowledge systems across the Afro-Atlantic world."
        ),
        og_url     = f"{BASE_URL}/about.html",
    ),
    # ── founder ───────────────────────────────────────────────────────────────
    dict(
        file       = "founder.html",
        slug       = "og-founder",
        label      = "IROKO · THE SOCIETY",
        title      = "The Founder",
        subtitle   = "Délé Fágbèmí Ọ̀ — practitioner-archivist, visual ethnographer, and historian of the Afro-Atlantic.",
        og_title   = "The Founder — Iroko Historical Society",
        og_description = (
            "Délé Fágbèmí Ọ̀ is the founder and Executive Director of the Iroko Historical Society — "
            "practitioner-archivist, visual ethnographer, and historian of the Afro-Atlantic world."
        ),
        og_url     = f"{BASE_URL}/founder.html",
    ),
    # ── mission ───────────────────────────────────────────────────────────────
    dict(
        file       = "mission.html",
        slug       = "og-mission",
        label      = "IROKO · THE SOCIETY",
        title      = "Mission & Stewardship",
        subtitle   = "On postcustodial ethics, community authority, and the long-term preservation of Afro-Atlantic sacred knowledge.",
        og_title   = "Mission & Stewardship — Iroko Historical Society",
        og_description = (
            "The Iroko Historical Society's principles of postcustodial stewardship — "
            "community-centered archival practice, ethical access frameworks, and long-term preservation."
        ),
        og_url     = f"{BASE_URL}/mission.html",
    ),
    # ── our stance ────────────────────────────────────────────────────────────
    dict(
        file       = "our-stance.html",
        slug       = "og-our-stance",
        label      = "IROKO · THE SOCIETY",
        title      = "Our Stance",
        subtitle   = "On repatriation, community authority, and the politics of sacred knowledge in the archival field.",
        og_title   = "Our Stance — Iroko Historical Society",
        og_description = (
            "The Iroko Historical Society's statement on community integrity, knowledge sovereignty, "
            "and the ethical stewardship of Afro-Atlantic sacred materials."
        ),
        og_url     = f"{BASE_URL}/our-stance.html",
    ),
    # ── collections ───────────────────────────────────────────────────────────
    dict(
        file       = "collections.html",
        slug       = "og-collections",
        label      = "IROKO · COLLECTIONS",
        title      = "Our Holdings",
        subtitle   = "Primary source documentation of sacred practice, material culture, and community life across the Afro-Atlantic world.",
        og_title   = "Collections — Iroko Historical Society",
        og_description = (
            "The Iroko Historical Society's holdings: primary source documentation "
            "of sacred practice, material culture, and community life across the Afro-Atlantic world."
        ),
        og_url     = f"{BASE_URL}/collections.html",
    ),
    # ── access policy ─────────────────────────────────────────────────────────
    dict(
        file       = "access-policy.html",
        slug       = "og-access-policy",
        label      = "IROKO · COLLECTIONS",
        title      = "Access & Use Policy",
        subtitle   = "A six-tiered framework governing access to initiatory, restricted, and publicly available materials.",
        og_title   = "Access & Use Policy — Iroko Historical Society",
        og_description = (
            "The Iroko Historical Society's six-tiered access framework governing "
            "initiatory, restricted, and publicly available archival materials."
        ),
        og_url     = f"{BASE_URL}/access-policy.html",
    ),
    # ── iroko commentaries ────────────────────────────────────────────────────
    dict(
        file       = "iroko-commentaries.html",
        slug       = "og-commentaries",
        label      = "IROKO · COMMENTARY",
        title      = "Iroko Commentaries",
        subtitle   = "Practitioner-scholar essays on sacred knowledge, archival practice, and the intellectual life of the Afro-Atlantic.",
        og_title   = "Iroko Commentaries — Iroko Historical Society",
        og_description = (
            "Iroko Commentaries gathers practitioner-scholar essays and reflections "
            "on sacred knowledge, archival ethics, and the intellectual life of the Afro-Atlantic world."
        ),
        og_url     = f"{BASE_URL}/iroko-commentaries.html",
    ),
    # ── iroko spirituality ────────────────────────────────────────────────────
    dict(
        file       = "iroko-spirituality.html",
        slug       = "og-iroko-spirituality",
        label      = "IROKO · SPIRITUALITY",
        title      = "Iroko Spirituality",
        subtitle   = "On the sacred traditions, cosmological frameworks, and living practices of the Afro-Atlantic world.",
        og_title   = "Iroko Spirituality — Iroko Historical Society",
        og_description = (
            "Sacred traditions, cosmological frameworks, and living practice — "
            "the Iroko Historical Society's resources on Afro-Atlantic religious life."
        ),
        og_url     = f"{BASE_URL}/iroko-spirituality.html",
    ),
    # ── visual ethnography ────────────────────────────────────────────────────
    dict(
        file       = "visual-ethnography.html",
        slug       = "og-visual-ethnography",
        layout     = "photo",
        photo_url  = (
            "https://m.psecn.photoshelter.com/img-get2"
            "/I00001I.Ui3.Uzdk/fit=700x700/fill="
            "/g=G0000n01IpmZArsk/I00001I.Ui3.Uzdk.jpg"
        ),
        # Crop offset — tweak these to reframe the photo:
        # positive offset_x → shift window right (shows more left edge of photo)
        # positive offset_y → shift window down  (shows more top of photo)
        photo_offset_x = 0,
        photo_offset_y = 50,
        label      = "IROKO · VISUAL ETHNOGRAPHY",
        title      = "Visual Ethnography",
        subtitle   = "Documentary photography of sacred spaces, ritual practice, and community life across the Afro-Atlantic world.",
        og_title   = "Visual Ethnography — Iroko Historical Society",
        og_description = (
            "Visual ethnography by Délé Fágbèmí Ọ̀ — documentary photography of sacred spaces, "
            "ritual practice, and community life across the Afro-Atlantic world."
        ),
        og_url     = f"{BASE_URL}/visual-ethnography.html",
    ),
    # ── research ──────────────────────────────────────────────────────────────
    dict(
        file       = "research.html",
        slug       = "og-research",
        label      = "IROKO · RESEARCH",
        title      = "Research & Scholarship",
        subtitle   = "Peer-reviewed publications, working papers, and presentations in Afro-Atlantic history and archival studies.",
        og_title   = "Research & Scholarship — Iroko Historical Society",
        og_description = (
            "Scholarly publications, working papers, and presentations by "
            "Délé Fágbèmí Ọ̀ and the Iroko Historical Society."
        ),
        og_url     = f"{BASE_URL}/research.html",
    ),
    # ── cv ────────────────────────────────────────────────────────────────────
    dict(
        file       = "cv.html",
        slug       = "og-cv",
        label      = "IROKO · CURRICULUM VITAE",
        title      = "Curriculum Vitae",
        subtitle   = "Selected CV of Délé Fágbèmí Ọ̀, founder and Executive Director of the Iroko Historical Society.",
        og_title   = "Curriculum Vitae — Délé Fágbèmí Ọ̀ — Iroko Historical Society",
        og_description = (
            "Selected curriculum vitae of Délé Fágbèmí Ọ̀, "
            "founder and Executive Director of the Iroko Historical Society."
        ),
        og_url     = f"{BASE_URL}/cv.html",
    ),
    # ── contact ───────────────────────────────────────────────────────────────
    dict(
        file       = "contact.html",
        slug       = "og-contact",
        label      = "IROKO · CONTACT",
        title      = "Contact",
        subtitle   = "Research inquiries, access requests, licensing, and general correspondence.",
        og_title   = "Contact — Iroko Historical Society",
        og_description = (
            "Reach the Iroko Historical Society for research inquiries, "
            "collection access requests, licensing, and general correspondence."
        ),
        og_url     = f"{BASE_URL}/contact.html",
    ),
    # ── contact form (same image as contact) ──────────────────────────────────
    dict(
        file       = "contact-form.html",
        slug       = "og-contact",   # reuse same PNG
        label      = "IROKO · CONTACT",
        title      = "Write to Us",
        subtitle   = "Research inquiries, access requests, licensing, and general correspondence.",
        og_title   = "Write to Us — Iroko Historical Society",
        og_description = (
            "Reach the Iroko Historical Society for research inquiries, "
            "collection access requests, licensing, and general correspondence."
        ),
        og_url     = f"{BASE_URL}/contact-form.html",
    ),
    # ── foundation day 2025 ───────────────────────────────────────────────────
    dict(
        file       = "foundation-day/2025.html",
        slug       = "og-foundation-day-2025",
        label      = "IROKO · FOUNDATION DAY",
        title      = "Foundation Day 2025",
        subtitle   = "The inaugural Foundation Day of the Iroko Historical Society.",
        og_title   = "Foundation Day 2025 — Iroko Historical Society",
        og_description = (
            "The inaugural Foundation Day of the Iroko Historical Society — "
            "marking the first year of postcustodial archival work."
        ),
        og_url     = f"{BASE_URL}/foundation-day/2025.html",
    ),
    # ── foundation day 2026 ───────────────────────────────────────────────────
    dict(
        file       = "foundation-day/2026.html",
        slug       = "og-foundation-day-2026",
        label      = "IROKO · FOUNDATION DAY",
        title      = "Foundation Day 2026",
        subtitle   = "State of the Society — closing Year Two, opening Year Three.",
        og_title   = "Foundation Day 2026 — State of the Society — Iroko Historical Society",
        og_description = (
            "The permanent record closing Year Two and opening Year Three of the "
            "Iroko Historical Society, including the founder's State of the Society address."
        ),
        og_url     = f"{BASE_URL}/foundation-day/2026.html",
    ),
    # ── foundation day 2027 (planned) ─────────────────────────────────────────
    dict(
        file       = "foundation-day/2027.html",
        slug       = "og-foundation-day-2027",
        label      = "IROKO · FOUNDATION DAY",
        title      = "Foundation Day 2027",
        subtitle   = "Planned — the public convening deferred from Year Two.",
        og_title   = "Foundation Day 2027 — Planned — Iroko Historical Society",
        og_description = (
            "Foundation Day 2027 is planned but not yet detailed. See the State of the "
            "Society, 2026 address for the reasoning behind the deferral."
        ),
        og_url     = f"{BASE_URL}/foundation-day/2027.html",
    ),
    # ── contribution intake ─────────────────────────────────────────────────
    dict(
        file       = "foundation-day/contribute.html",
        slug       = "og-contribute",
        label      = "IROKO · VISUAL ETHNOGRAPHY",
        title      = "Submit a Contribution",
        subtitle   = "Share a photograph, contextual note, or other proposed contribution for consideration by the Iroko Historical Society.",
        og_title   = "Submit a Contribution — Iroko Historical Society",
        og_description = (
            "Submit a photograph, contextual note, or other proposed contribution "
            "for consideration by the Iroko Historical Society."
        ),
        og_url     = f"{BASE_URL}/foundation-day/contribute.html",
    ),
    # ── contribution receipt ────────────────────────────────────────────────
    dict(
        file       = "foundation-day/contribution-received.html",
        slug       = "og-contribute",
        label      = "IROKO · VISUAL ETHNOGRAPHY",
        title      = "Contribution Received",
        subtitle   = "Thank you for sharing material with the Iroko Historical Society.",
        og_title   = "Contribution Received — Iroko Historical Society",
        og_description = (
            "Thank you for submitting a proposed contribution to the Iroko Historical Society."
        ),
        og_url     = f"{BASE_URL}/foundation-day/contribution-received.html",
    ),
    # ── find your tree (community observance, shareable on its own) ──────────
    dict(
        file       = "foundation-day/find-your-tree.html",
        slug       = "og-find-your-tree",
        layout     = "photo",
        photo_url  = "https://m.psecn.photoshelter.com/img-get/I0000BOUspDyBJo4/s/1200/I0000BOUspDyBJo4.jpg",
        label      = "IROKO · FOUNDATION DAY",
        title      = "Find Your Tree",
        subtitle   = "A community observance for July 14 — find a tree of significance, stand with it, and offer your attention.",
        og_title   = "Find Your Tree — Iroko Historical Society",
        og_description = (
            "On July 14, wherever you are, make a small pilgrimage: find a tree that "
            "holds significance in your landscape, stand with it, and offer your attention."
        ),
        og_url     = f"{BASE_URL}/foundation-day/find-your-tree.html",
    ),
    # ── commentaries ──────────────────────────────────────────────────────────
    dict(
        file       = "wont-they-do-it.html",
        slug       = "og-wont-they-do-it",
        label      = "IROKO · COMMENTARY",
        title      = "Won't They Do It",
        subtitle   = "Righteousness, Debt, and the Fallacy of Spiritual ROI",
        og_title   = "Won't They Do It — Iroko Commentary",
        og_description = (
            "Righteousness, Debt, and the Fallacy of Spiritual ROI. "
            "An Iroko Commentary by Délé Fágbèmí Ọ̀."
        ),
        og_url     = f"{BASE_URL}/wont-they-do-it.html",
    ),
    dict(
        file       = "the-bones-fall-prophecy-or-verdict.html",
        slug       = "og-bones-fall",
        label      = "IROKO · COMMENTARY",
        title      = "The Bones Fall",
        subtitle   = "Prophecy or Verdict? On Divinatory Inflation and the Ethics of Sacred Speech",
        og_title   = "The Bones Fall: Prophecy or Verdict? — Iroko Commentary",
        og_description = (
            "On Divinatory Inflation and the Ethics of Sacred Speech. "
            "An Iroko Commentary by Délé Fágbèmí Ọ̀."
        ),
        og_url     = f"{BASE_URL}/the-bones-fall-prophecy-or-verdict.html",
    ),
    dict(
        file       = "bread-before-the-end.html",
        slug       = "og-bread-before-end",
        label      = "IROKO · COMMENTARY",
        title      = "Bread Before the End",
        subtitle   = "Havana and the Memory of Constantinople",
        og_title   = "Bread Before the End: Havana and the Memory of Constantinople — Iroko Commentary",
        og_description = (
            "On the memory of Constantinople and the last meal before the fall. "
            "An Iroko Commentary by Délé Fágbèmí Ọ̀."
        ),
        og_url     = f"{BASE_URL}/bread-before-the-end.html",
    ),
    dict(
        file       = "the-scholar-is-not-the-custodian.html",
        slug       = "og-scholar-custodian",
        label      = "IROKO · COMMENTARY",
        title      = "The Scholar Is Not the Custodian",
        subtitle   = "On scholarly access, initiatory obligation, and sealed archives",
        og_title   = "The Scholar Is Not the Custodian — Iroko Commentary",
        og_description = (
            "On scholarly access, initiatory obligation, and sealed archives. "
            "An Iroko Commentary by Délé Fágbèmí Ọ̀."
        ),
        og_url     = f"{BASE_URL}/the-scholar-is-not-the-custodian.html",
    ),
]


# ── runner ─────────────────────────────────────────────────────────────────────

def main():
    print("IHS OG Image Generator")
    print("=" * 50)

    # Pre-download all fonts
    print("\nChecking fonts …")
    for key in _FONT_SPECS:
        _download_font(key)

    generated = []
    updated   = []
    skipped   = []
    errors    = []

    seen_slugs = set()

    for page in PAGES:
        html_path = BASE / page["file"]
        if not html_path.exists():
            print(f"\n  SKIP (file not found): {page['file']}")
            continue

        png_filename = f"{page['slug']}.png"
        png_path     = ASSETS / png_filename
        is_skip      = page.get("skip", False)

        print(f"\n[{page['file']}]")

        # Generate PNG (unless skipped or already exists without --force)
        if is_skip:
            print(f"  PNG: keeping existing {png_filename}")
        elif png_path.exists() and not FORCE and page["slug"] not in seen_slugs:
            # For non-skip pages: only regenerate if --force or first time
            # We regenerate if the file doesn't exist
            print(f"  PNG: {png_filename} already exists (use --force to regenerate)")
        else:
            if page["slug"] not in seen_slugs:
                try:
                    print(f"  Generating {png_filename} …")
                    img = make_og_image(page)
                    img.save(str(png_path), "PNG", optimize=True)
                    print(f"  Saved → assets/{png_filename}")
                    generated.append(png_filename)
                except Exception as e:
                    print(f"  ERROR: {e}")
                    errors.append((page["file"], str(e)))
            else:
                print(f"  PNG: reusing {png_filename} (shared slug)")

        seen_slugs.add(page["slug"])

        # Always update HTML meta tags
        try:
            inject_og_tags(html_path, page, png_filename)
            print(f"  Tags: updated {page['file']}")
            updated.append(page["file"])
        except Exception as e:
            print(f"  ERROR updating tags: {e}")
            errors.append((page["file"], str(e)))

    # Summary
    print("\n" + "=" * 50)
    print(f"Generated {len(generated)} PNG(s)")
    print(f"Updated   {len(updated)} HTML file(s)")
    if errors:
        print(f"Errors    {len(errors)}:")
        for f, e in errors:
            print(f"  {f}: {e}")
    print("\nDone. Commit assets/ and the updated HTML files.")


if __name__ == "__main__":
    main()
