#!/usr/bin/env python3
"""
generate-og.py — IHS Open Graph Image Generator
================================================
Run from the IHS-Website directory:

    pip install Pillow
    python generate-og.py

What it does:
  1. Downloads EB Garamond Bold, EB Garamond Italic, and Source Sans 3 into fonts/
  2. Generates 1200×630 branded PNG files into assets/
  3. Injects/updates og: and twitter: meta tags in each HTML file

Run with --force to regenerate PNGs that already exist.
Run with --only archive/records/<slug>.html to refresh one page.
Archive share wrappers are discovered from archive/records/*.html.
"""

import io
import html
import os
import re
import sys
import textwrap
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from pathlib import Path
from typing import Optional

# ── dependency check ──────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Missing Pillow. Run: pip install Pillow")

# ── paths ─────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).parent.resolve()
ASSETS = BASE / "assets"
FONTS  = BASE / "fonts"
FONTS.mkdir(exist_ok=True)

BASE_URL  = "https://irokosociety.org"
LOGO_PATH = ASSETS / "IHS-Logo.jpg"

FORCE = "--force" in sys.argv


def _cli_values(flag):
    values = []
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == flag:
            if i + 1 >= len(args):
                sys.exit(f"Missing value for {flag}")
            values.append(args[i + 1])
            i += 2
            continue
        if arg.startswith(f"{flag}="):
            values.append(arg.split("=", 1)[1])
        i += 1
    return values


def _normalize_ref(value):
    value = str(value).strip().replace("\\", "/")
    if value.startswith("./"):
        value = value[2:]
    if value.startswith("assets/") and value.endswith(".png"):
        value = value[len("assets/"):-4]
    elif value.endswith(".png"):
        value = value[:-4]
    return value


ONLY_TARGETS = {_normalize_ref(value) for value in _cli_values("--only")}

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
ARCHIVE_BLUE = (26, 52, 104)

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
SZ_SERIES = 16

# ── font management ───────────────────────────────────────────────────────────
_FONT_SPECS = {
    "garamond_bold": ("EB Garamond",   "700", "0"),
    "garamond_ital": ("EB Garamond",   "400", "1"),
    "sourcesans":    ("Source Sans 3", "400", "0"),
}

_font_cache: dict = {}


def fetch_bytes(url: str, headers: Optional[dict] = None, timeout: int = 30) -> bytes:
    """Fetch URL bytes using the standard library."""
    request = Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


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
    print(f"  Downloading font: {family} {weight}{'i' if ital=='1' else ''} ...")
    try:
        css = fetch_bytes(css_url, headers=headers, timeout=15).decode("utf-8", errors="replace")
        urls = re.findall(r"url\(([^)]+\.ttf)\)", css)
        if not urls:
            print(f"  WARNING: no TTF URL found for {family}. Skipping.")
            return None
        dest.write_bytes(fetch_bytes(urls[0], headers=headers, timeout=30))
        print(f"  Saved -> fonts/{key}.ttf")
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
    print("    Downloading photo ...")
    photo = Image.open(io.BytesIO(fetch_bytes(photo_url, timeout=30))).convert("RGB")

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


def render_contained_photo_panel(img: Image.Image, photo_url: str) -> int:
    """Fit the entire photo inside the left panel without cropping."""
    draw = ImageDraw.Draw(img)
    draw.rectangle(
        [PHOTO_X, PHOTO_Y, PHOTO_X + PHOTO_W, PHOTO_Y + PHOTO_H],
        fill=CREAM_BOX,
    )

    print("    Downloading photo ...")
    photo = Image.open(io.BytesIO(fetch_bytes(photo_url, timeout=30))).convert("RGB")
    photo.thumbnail((PHOTO_W - 28, PHOTO_H - 28), Image.LANCZOS)
    paste_x = PHOTO_X + (PHOTO_W - photo.width) // 2
    paste_y = PHOTO_Y + (PHOTO_H - photo.height) // 2
    img.paste(photo, (paste_x, paste_y))
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
    elif page.get("layout") == "photo_contain":
        text_x = render_contained_photo_panel(img, page["photo_url"])
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
    sub_bottom = draw_wrapped(draw, page["subtitle"], f_sub, text_x, sub_y, max_w, COL_SUB, 1.45)

    # Optional series marker below the subtitle.
    if page.get("series"):
        f_series = get_font("sourcesans", SZ_SERIES)
        series_text = page["series"]
        pad_x, pad_y = 16, 10
        series_w = _text_w(draw, series_text, f_series)
        series_h = _text_h(draw, series_text, f_series)
        series_y = sub_bottom + 14
        draw.rectangle(
            [
                text_x,
                series_y,
                text_x + series_w + (pad_x * 2),
                series_y + series_h + (pad_y * 2),
            ],
            fill=ARCHIVE_BLUE,
        )
        draw.text(
            (text_x + pad_x, series_y + pad_y),
            series_text,
            font=f_series,
            fill=COL_TITLE,
        )

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
{og_locale_lines}\
  <meta property="og:title"       content="{og_title}">
  <meta property="og:description" content="{og_description}">
  <meta property="og:url"         content="{og_url}">
  <meta property="og:image"       content="{og_image}">
  <meta property="og:image:width"  content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:type"   content="image/png">
  <meta property="og:image:alt"    content="{image_alt}">
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="{og_title}">
  <meta name="twitter:description" content="{og_description}">
  <meta name="twitter:image"       content="{og_image}">
  <meta name="twitter:image:alt"   content="{image_alt}">
"""


def html_attr(value) -> str:
    return html.escape(str(value or ""), quote=True)


def inject_og_tags(html_path: Path, page: dict, png_filename: str) -> None:
    src = html_path.read_text(encoding="utf-8")

    og_image = f"{BASE_URL}/assets/{png_filename}"
    image_alt = page.get("image_alt") or f"{page['title']} - Iroko Historical Society social preview"
    og_locale_lines = ""
    if page.get("og_locale"):
        og_locale_lines += f'  <meta property="og:locale"      content="{html_attr(page["og_locale"])}">\n'
    for locale in page.get("og_locale_alternates", []):
        og_locale_lines += f'  <meta property="og:locale:alternate" content="{html_attr(locale)}">\n'

    block    = OG_BLOCK.format(
        og_title       = html_attr(page["og_title"]),
        og_description = html_attr(page["og_description"]),
        og_url         = html_attr(page["og_url"]),
        og_image       = html_attr(og_image),
        image_alt      = html_attr(image_alt),
        og_locale_lines = og_locale_lines,
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
    html_title = page.get("html_title")
    if html_title and re.search(r"<title>.*?</title>", cleaned, re.IGNORECASE | re.DOTALL):
        cleaned = re.sub(
            r"<title>.*?</title>",
            f"<title>{html.escape(str(html_title))}</title>",
            cleaned,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

    meta_description = page.get("meta_description", page["og_description"])
    if re.search(r'<meta\s+name="description"[^>]*>', cleaned, re.IGNORECASE):
        cleaned = re.sub(
            r'<meta\s+name="description"[^>]*>',
            f'<meta name="description" content="{html_attr(meta_description)}">',
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        cleaned = re.sub(
            r"(<meta[^>]+viewport[^>]*>)",
            r'\1' + f'\n  <meta name="description" content="{html_attr(meta_description)}">',
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )

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

    new_src = re.sub(
        r"(<meta[^>]+>)\s+(<title\b)",
        r"\1\n  \2",
        new_src,
        flags=re.IGNORECASE,
    )
    new_src = re.sub(
        r"(<link[^>]+>)\s+(<link\b)",
        r"\1\n  \2",
        new_src,
        flags=re.IGNORECASE,
    )
    new_src = new_src.replace(">  <title", ">\n  <title")
    new_src = new_src.replace(">  <link", ">\n  <link")

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
        label      = "IROKO · COMMENTARIES",
        title      = "Iroko Commentaries",
        subtitle   = "Practitioner-scholar essays on sacred knowledge, archival practice, and the intellectual life of the Afro-Atlantic.",
        og_title   = "Iroko Commentaries — Iroko Historical Society",
        og_description = (
            "Iroko Commentaries gathers practitioner-scholar essays and reflections "
            "on sacred knowledge, archival ethics, and the intellectual life of the Afro-Atlantic world."
        ),
        og_url     = f"{BASE_URL}/iroko-commentaries.html",
    ),
    # ── contribute to commentaries ────────────────────────────────────────────
    dict(
        file       = "contribute-commentary.html",
        slug       = "og-contribute-commentary",
        label      = "IROKO · COMMENTARIES",
        title      = "Contribute to Iroko Commentaries",
        subtitle   = "Write from where your knowledge lives.",
        og_title   = "Contribute to Iroko Commentaries — Iroko Historical Society",
        og_description = (
            "A commissioned essay series on Afro-Atlantic sacred practice, archives, "
            "and cultural stewardship. Scholars, practitioners, archivists, artists, and "
            "elders may propose a commentary in the language they know best."
        ),
        og_url     = f"{BASE_URL}/contribute-commentary.html",
    ),
    # ── contributor guidelines ────────────────────────────────────────────────
    dict(
        file       = "contributor-guidelines.html",
        slug       = "og-contributor-guidelines",
        label      = "IROKO · COMMENTARIES",
        title      = "Contributor Guidelines",
        subtitle   = "Standards, restricted knowledge, language and editions, copyright, and process.",
        og_title   = "Contributor Guidelines — Iroko Commentaries",
        og_description = (
            "Editorial policy for the Iroko Commentaries series: scope, situated authority, "
            "language and editions, sacred and contested knowledge, copyright, and the editorial process."
        ),
        og_url     = f"{BASE_URL}/contributor-guidelines.html",
    ),
    # ── propose a commentary ──────────────────────────────────────────────────
    dict(
        file       = "propose-commentary.html",
        slug       = "og-contribute-commentary",   # reuse same PNG
        label      = "IROKO · COMMENTARIES",
        title      = "Propose a Commentary",
        subtitle   = "Tell us what you want to write and how you know what you know.",
        og_title   = "Propose a Commentary — Iroko Historical Society",
        og_description = (
            "Send a short proposal to Iroko Commentaries. Proposals may be written "
            "in your preferred language."
        ),
        og_url     = f"{BASE_URL}/propose-commentary.html",
    ),
    # ── guest commentary template ─────────────────────────────────────────────
    dict(
        file       = "guest-commentary-template.html",
        slug       = "og-guest-commentary",
        label      = "IROKO · COMMENTARIES",
        title      = "Guest Commentary",
        subtitle   = "A signed essay by an invited contributor to the Iroko Historical Society.",
        og_title   = "Guest Commentary — Iroko Commentaries",
        og_description = (
            "A signed essay by an invited contributor, selected and edited for publication "
            "by the Iroko Historical Society."
        ),
        og_url     = f"{BASE_URL}/guest-commentary-template.html",
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
    # ── share your tree (community observance, shareable on its own) ─────────
    dict(
        file       = "foundation-day/share-your-tree.html",
        slug       = "og-share-your-tree",
        layout     = "photo",
        photo_url  = "https://m.psecn.photoshelter.com/img-get/I0000BOUspDyBJo4/s/1200/I0000BOUspDyBJo4.jpg",
        label      = "IROKO · FOUNDATION DAY",
        title      = "Share Your Tree",
        subtitle   = "A community observance for July 14 - find a tree of significance, stand with it, and share what you witnessed.",
        og_title   = "Share Your Tree — Iroko Historical Society",
        og_locale  = "en_US",
        og_locale_alternates = ["es_ES", "pt_BR", "ht_HT"],
        og_description = (
            "On July 14, wherever you are, make a small pilgrimage: find a tree that "
            "holds significance in your landscape, stand with it, and share your photograph or note."
        ),
        og_url     = f"{BASE_URL}/foundation-day/share-your-tree.html",
    ),
    dict(
        file       = "foundation-day/community-gallery-2025.html",
        slug       = "og-community-gallery-2025",
        layout     = "photo",
        photo_url  = "https://m.psecn.photoshelter.com/img-get/I0000BOUspDyBJo4/s/1200/I0000BOUspDyBJo4.jpg",
        label      = "IROKO · FOUNDATION DAY",
        title      = "Gallery of 2025 Submissions",
        subtitle   = "Foundation Day 2025 community submissions in the IHS PhotoShelter gallery.",
        og_title   = "Foundation Day 2025 Community Gallery — Iroko Historical Society",
        og_description = (
            "Open the IHS PhotoShelter gallery for Foundation Day 2025 "
            "community-submitted photographs and sacred-tree images."
        ),
        og_url     = f"{BASE_URL}/foundation-day/community-gallery-2025.html",
    ),
    dict(
        file       = "foundation-day/community-gallery-2026.html",
        slug       = "og-community-gallery-2026",
        layout     = "photo", 
        photo_url  = "https://m.psecn.photoshelter.com/direct-link/l/0/mswBpobsB70/uTAui7uxLuxFuituxruRui7uxuTUuim/IHS---Private-Observations---2026.jpeg",
        label      = "IROKO · FOUNDATION DAY",
        title      = "Gallery of 2026 Submissions",
        subtitle   = "Foundation Day 2026 community submissions in the IHS PhotoShelter gallery.",
        og_title   = "Foundation Day 2026 Community Gallery — Iroko Historical Society",
        og_description = (
            "Open the IHS PhotoShelter gallery for Foundation Day 2026 "
            "community-submitted photographs and sacred-tree images."
        ),
        og_url     = f"{BASE_URL}/foundation-day/community-gallery-2026.html",
    ),
    dict(
        file       = "foundation-day/share-your-tree-es.html",
        slug       = "og-share-your-tree-es",
        layout     = "photo",
        photo_url  = "https://m.psecn.photoshelter.com/img-get/I0000BOUspDyBJo4/s/1200/I0000BOUspDyBJo4.jpg",
        label      = "IROKO · DÍA DE FUNDACIÓN",
        title      = "Comparte tu árbol",
        subtitle   = "Una observancia comunitaria para el 14 de julio: encuentra un árbol de significado, acompáñalo y comparte lo que presenciaste.",
        og_title   = "Comparte tu árbol — Iroko Historical Society",
        og_locale  = "es_ES",
        og_locale_alternates = ["en_US", "pt_BR", "ht_HT"],
        og_description = (
            "El 14 de julio, dondequiera que estés, haz una pequeña peregrinación: "
            "encuentra un árbol que tenga significado en tu paisaje, quédate con él "
            "y comparte tu fotografía o nota."
        ),
        og_url     = f"{BASE_URL}/foundation-day/share-your-tree-es.html",
    ),
    dict(
        file       = "foundation-day/share-your-tree-pt.html",
        slug       = "og-share-your-tree-pt",
        layout     = "photo",
        photo_url  = "https://m.psecn.photoshelter.com/img-get/I0000BOUspDyBJo4/s/1200/I0000BOUspDyBJo4.jpg",
        label      = "IROKO · DIA DA FUNDAÇÃO",
        title      = "Compartilhe sua árvore",
        subtitle   = "Uma observância comunitária para 14 de julho: encontre uma árvore de significado, permaneça com ela e compartilhe o que testemunhou.",
        og_title   = "Compartilhe sua árvore — Iroko Historical Society",
        og_locale  = "pt_BR",
        og_locale_alternates = ["en_US", "es_ES", "ht_HT"],
        og_description = (
            "No dia 14 de julho, onde quer que você esteja, faça uma pequena peregrinação: "
            "encontre uma árvore que tenha significado em sua paisagem, permaneça com ela "
            "e compartilhe sua fotografia ou nota."
        ),
        og_url     = f"{BASE_URL}/foundation-day/share-your-tree-pt.html",
    ),
    dict(
        file       = "foundation-day/share-your-tree-ht.html",
        slug       = "og-share-your-tree-ht",
        layout     = "photo",
        photo_url  = "https://m.psecn.photoshelter.com/img-get/I0000BOUspDyBJo4/s/1200/I0000BOUspDyBJo4.jpg",
        label      = "IROKO · JOU FONDASYON",
        title      = "Pataje Pyebwa Ou",
        subtitle   = "Yon obsèvans kominotè pou 14 jiyè: chèche yon pyebwa ki gen siyifikasyon, kanpe bò kote li, epi pataje sa ou temwen.",
        og_title   = "Pataje Pyebwa Ou — Iroko Historical Society",
        og_locale  = "ht_HT",
        og_locale_alternates = ["en_US", "es_ES", "pt_BR"],
        og_description = (
            "14 jiyè, kèlkeswa kote ou ye, fè yon ti pelerinaj: chèche yon pyebwa "
            "ki gen siyifikasyon nan peyizaj ou, kanpe bò kote li, epi pataje foto "
            "oswa nòt ou."
        ),
        og_url     = f"{BASE_URL}/foundation-day/share-your-tree-ht.html",
    ),
    dict(
            file       = "visual-ethnography.html",
            slug       = "og-ethnography-gallery-jump.png",
            layout     = "photo",
            photo_url  = (
                "https://m.psecn.photoshelter.com/direct-link/l/0/mswBpobsB70/xTCxasxaCxT4xbMxbQxavxb2xaxbFxbpxT/Tata-F---%284-of-43%29.jpg"
                ),

            # Crop offset — tweak these to reframe the photo:
            # positive offset_x → shift window right (shows more left edge of photo)
            # positive offset_y → shift window down  (shows more top of photo)
            photo_offset_x = 0,
            photo_offset_y = -50,
            label      = "IROKO · ETHNOGRAPHY GALLERY",
            title      = "Visual Ethnography",
            subtitle   = "Visit the IHS PhotoShelter gallery for Visual Ethnography.",
            og_title   = "Visual Ethnography Gallery — Iroko Historical Society",
            og_description = (
                "Open the IHS PhotoShelter gallery for Visual Ethnography."
            ),
            og_url     = f"{BASE_URL}/visual-ethnography.html",
    ),
    
    # ── commentaries ──────────────────────────────────────────────────────────
    dict(
        file       = "before-the-boxes-disappear.html",
        slug       = "og-before-boxes",
        label      = "IROKO · COMMENTARIES",
        title      = "Before the Boxes Disappear",
        subtitle   = "How Ordinary Decisions Unmake a Community Archive",
        series     = "THE IROKO ARCHIVIST SERIES",
        og_title   = "Before the Boxes Disappear · Iroko Commentary",
        og_description = (
            "How ordinary decisions unmake a community archive. "
            "Essay 1 of the Iroko Archivist Series, by Délé Fágbèmí Ọ̀."
        ),
        og_url     = f"{BASE_URL}/before-the-boxes-disappear.html",
    ),
    dict(
        file       = "wont-they-do-it.html",
        slug       = "og-wont-they-do-it",
        label      = "IROKO · COMMENTARIES",
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
        label      = "IROKO · COMMENTARIES",
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
        label      = "IROKO · COMMENTARIES",
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
        label      = "IROKO · COMMENTARIES",
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


def _class_has(value, class_name):
    return class_name in str(value or "").split()


def _clean_html_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _strip_site_suffix(value):
    return re.sub(
        r"\s+(?:-|—)\s+Iroko Historical Society\s*$",
        "",
        _clean_html_text(value),
        flags=re.IGNORECASE,
    )


def _absolute_archive_image_url(value, html_path):
    value = str(value or "").strip()
    if not value:
        return ""
    if re.match(r"https?://", value, flags=re.IGNORECASE):
        return value
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("/"):
        return BASE_URL + value
    return (html_path.parent / value).resolve().as_uri()


class ArchiveRecordParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.canonical = ""
        self.image_url = ""
        self.buffers = {
            "page_title": [],
            "record_title": [],
            "subtitle": [],
        }
        self._capture_key = ""
        self._capture_tag = ""

    def _start_capture(self, key, tag):
        self._capture_key = key
        self._capture_tag = tag
        self.buffers[key] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr = {str(key).lower(): value or "" for key, value in attrs}

        if tag == "meta":
            key = attr.get("property") or attr.get("name")
            content = attr.get("content", "")
            if key and content:
                self.meta[key.lower()] = content
        elif tag == "link" and "canonical" in str(attr.get("rel", "")).lower().split():
            self.canonical = attr.get("href", "")
        elif tag == "img" and _class_has(attr.get("class"), "archive-record-image"):
            self.image_url = self.image_url or attr.get("src", "")

        if tag == "title":
            self._start_capture("page_title", tag)
        elif tag == "h1" and attr.get("id") == "record-title":
            self._start_capture("record_title", tag)
        elif tag == "p" and _class_has(attr.get("class"), "archive-record-dek"):
            self._start_capture("subtitle", tag)

    def handle_data(self, data):
        if self._capture_key:
            self.buffers[self._capture_key].append(data)

    def handle_endtag(self, tag):
        if self._capture_tag and tag.lower() == self._capture_tag:
            self._capture_key = ""
            self._capture_tag = ""

    def text(self, key):
        return _clean_html_text(" ".join(self.buffers.get(key, [])))


def archive_share_page_from_html(html_path):
    parser = ArchiveRecordParser()
    try:
        parser.feed(html_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"  WARNING: could not parse {html_path.relative_to(BASE)}: {exc}")
        return None

    file = html_path.relative_to(BASE).as_posix()
    title = (
        parser.text("record_title")
        or _strip_site_suffix(parser.meta.get("og:title", ""))
        or _strip_site_suffix(parser.text("page_title"))
    )
    subtitle = (
        parser.text("subtitle")
        or _clean_html_text(parser.meta.get("description", ""))
        or _clean_html_text(parser.meta.get("og:description", ""))
    )
    photo_url = _absolute_archive_image_url(parser.image_url, html_path)

    if not title or not photo_url:
        return None

    return dict(
        file=file,
        slug=f"og/archive/{html_path.stem}",
        layout="photo_contain",
        photo_url=photo_url,
        label="IROKO - ARCHIVAL RECORD",
        title=title,
        subtitle=subtitle,
        html_title=f"{title} | Iroko Historical Society",
        meta_description=subtitle,
        image_alt=f"Archival photograph titled {title}.",
        og_title=f"{title} - Iroko Historical Society",
        og_description=subtitle,
        og_url=parser.canonical or f"{BASE_URL}/{file}",
    )


def discover_archive_share_pages():
    """Discover share-wrapper OG entries from archive/records/*.html."""
    records_dir = BASE / "archive" / "records"
    if not records_dir.exists():
        return []

    pages = []
    for html_path in sorted(records_dir.glob("*.html")):
        page = archive_share_page_from_html(html_path)
        if page:
            pages.append(page)
    return pages


def page_entries():
    """Return built-in pages plus dynamic archive-share pages.

    Dynamic share records replace built-in entries with the same file or slug so
    older hard-coded archive records can still be refreshed from the HTML page.
    """
    pages = list(PAGES)
    for dynamic_page in discover_archive_share_pages():
        dynamic_file = dynamic_page.get("file")
        dynamic_slug = dynamic_page.get("slug")
        for index, existing_page in enumerate(pages):
            if existing_page.get("file") == dynamic_file or existing_page.get("slug") == dynamic_slug:
                pages[index] = dynamic_page
                break
        else:
            pages.append(dynamic_page)
    return pages


def selected_page(page):
    if not ONLY_TARGETS:
        return True
    refs = {
        _normalize_ref(page.get("file", "")),
        _normalize_ref(page.get("slug", "")),
        _normalize_ref(f"{page.get('slug', '')}.png"),
        _normalize_ref(f"assets/{page.get('slug', '')}.png"),
    }
    return bool(refs & ONLY_TARGETS)


# ── runner ─────────────────────────────────────────────────────────────────────

def main():
    print("IHS OG Image Generator")
    print("=" * 50)

    # Pre-download all fonts
    print("\nChecking fonts ...")
    for key in _FONT_SPECS:
        _download_font(key)

    generated = []
    updated   = []
    skipped   = []
    errors    = []

    seen_slugs = set()

    processed = 0

    for page in page_entries():
        if not selected_page(page):
            continue
        processed += 1
        html_path = BASE / page["file"]
        if not html_path.exists():
            print(f"\n  SKIP (file not found): {page['file']}")
            continue

        png_filename = f"{page['slug']}.png"
        png_path     = ASSETS / png_filename
        png_path.parent.mkdir(parents=True, exist_ok=True)
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
                    print(f"  Generating {png_filename} ...")
                    img = make_og_image(page)
                    img.save(str(png_path), "PNG", optimize=True)
                    print(f"  Saved -> assets/{png_filename}")
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
    if ONLY_TARGETS and processed == 0:
        print("WARNING: no pages matched --only target(s): " + ", ".join(sorted(ONLY_TARGETS)))
    print(f"Generated {len(generated)} PNG(s)")
    print(f"Updated   {len(updated)} HTML file(s)")
    if errors:
        print(f"Errors    {len(errors)}:")
        for f, e in errors:
            print(f"  {f}: {e}")
    print("\nDone. Commit assets/ and the updated HTML files.")


if __name__ == "__main__":
    main()
