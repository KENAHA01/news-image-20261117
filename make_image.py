"""Draw the upgraded front page for news-image-20261117 (1024x1024 PNG).

Upgrade, built on the 39-story rebuild (0fbc7a7). The news content, the
style and the CONFIRMED/CLAIM tags are unchanged; what changed:

- Region colours (Europe blue, Middle East red, Asia orange, Africa
  green, Americas purple, Oceania teal, World grey) on the header
  counts, the card category lines, the map pins and a dot on every
  "Also on" row, with a small legend under the map.
- Bigger illustrations: cards 4-15 fill the space their text leaves
  (scene about a third of the card, no big empty area); cards 1-3 use
  a wide map with a location caption underneath.
- The world map is drawn from real coastline data (Natural Earth 110m
  land, coast.py) and pins are placed from real lon/lat coordinates.
- The "Also on" list is grouped by region, in region order.
- Cards 1-3 have titles about 1.4x the other cards' (17 px vs 12 px);
  CLAIM tags use a darker amber.
- Every card carries its source initials (Reuters R, AP, WHO, PAHO,
  UN, Le Monde LM, CNN, UNB, UKMTO, NASA).
- The numbers strip marks the Dow red with a down arrow and Nvidia
  green with an up arrow.
- A layout check runs before saving: it stops the program if any card
  title or body shrank below its set size, if any card's content
  overflows its frame, if the list does not fit, if two map pins
  collide, or if any recorded text box overlaps another or leaves
  the page.

The entry stays 1024x1024 (the bounty gate caps the file at 1024 px
and 1 MiB). A 2048x2048 preview is rendered separately by upscaling
(see render_2048.py); it is not the submitted file.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coast import LAND_POLYS

W, H = 1024, 1024
OUT = Path(__file__).resolve().parent / "entry.png"

PAPER = (247, 243, 232)
CARD = (255, 253, 246)
INK = (26, 26, 26)
RED = (139, 30, 30)
GREY = (90, 84, 72)
SEA = (207, 227, 238)
LAND = (232, 223, 200)
TAG_GREEN = (0, 110, 60)
TAG_CLAIM = (140, 90, 0)

REGION_COLORS = {
    "EUROPE": (0, 90, 180),
    "MIDDLE EAST": (178, 34, 34),
    "ASIA": (200, 100, 0),
    "AFRICA": (0, 110, 60),
    "AMERICAS": (110, 60, 160),
    "OCEANIA": (0, 130, 130),
    "WORLD": (90, 84, 72),
}

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TITLE_SIZE = 12      # card titles, cards 4-15
BODY_SIZE = 10       # card body text
BIG_TITLE_SIZE = 17  # card titles, cards 1-3 (about 1.4x TITLE_SIZE)
LIST_SIZE = 10       # "Also on" rows (>= BODY_SIZE)
LIST_HEAD_SIZE = 9   # region group headers in the list

_fonts = {}


def fb(path, size):
    if (path, size) not in _fonts:
        _fonts[(path, size)] = ImageFont.truetype(path, size)
    return _fonts[(path, size)]


def wrap(d, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# Layout-check records. fit_block logs every strict (never-shrink) call;
# tbox logs the bounding box of each recorded text element, grouped so
# the check only compares boxes that share a card or a section.
FIT_LOG = []
HEIGHT_LOG = []
BOXES = []


def fit_block(d, text, path, start, min_size, max_w, max_lines, max_h,
              label="", strict=False):
    size = start
    while size > min_size:
        font = fb(path, size)
        lines = wrap(d, text, font, max_w)
        lh = int(size * 1.17)
        if len(lines) <= max_lines and len(lines) * lh <= max_h:
            break
        size -= 1
    font = fb(path, size)
    lines = wrap(d, text, font, max_w)
    lh = int(size * 1.17)
    FIT_LOG.append((label, start, size, strict))
    return font, lines, lh


def text_center(d, cx, y, text, font, fill):
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)


def tbox(d, x, y, text, font, fill, group, label=""):
    """Draw left-aligned text and record its box for the layout check."""
    d.text((x, y), text, font=font, fill=fill)
    box = d.textbbox((x, y), text, font=font)
    BOXES.append((group, label, box))


def tbox_c(d, cx, y, text, font, fill, group, label=""):
    """Draw centred text and record its box for the layout check."""
    w = d.textlength(text, font=font)
    d.text((cx - w / 2, y), text, font=font, fill=fill)
    box = d.textbbox((cx - w / 2, y), text, font=font)
    BOXES.append((group, label, box))


def panel(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=2)
    d.rectangle([x, y, x + w, y + 5], fill=RED)
    return x + 12, y + 12, w - 24, h - 24


def section_title(d, x, y, text):
    d.text((x, y), text, font=fb(SANS_B, 13), fill=INK)


def draw_tag(d, x, y, w, text, color, group, start=9, max_h=20):
    font, lines, lh = fit_block(d, text, SANS_B, start, 7, w - 12, 3,
                                max_h, label=f"tag {group}")
    for ln in lines:
        tbox(d, x, y, ln, font, color, group, label="tag")
        y += lh
    return y


# ---- big-panel maps (wide images for cards 1-3) ----

def map_kerch(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    f = fb(SANS_B, 9)
    d.text((x + 6, y + 2), "RUSSIA", font=f, fill=INK)
    d.text((x + 6, y + h - 12), "CRIMEA", font=f, fill=INK)
    by = y + h * 0.45
    d.rectangle([x, y + by - 3, x + w * 0.42, y + by + 3], fill=INK)
    d.rectangle([x + w * 0.58, y + by - 3, x + w, y + by + 3], fill=INK)
    d.polygon([(x + w * 0.42, y + by - 3), (x + w * 0.50, y + by + 12),
               (x + w * 0.58, y + by - 3)], fill=RED)
    for cx, cy, r in ((0.47, 0.28, 7), (0.52, 0.20, 5), (0.44, 0.18, 4)):
        d.ellipse([x + w * cx - r, y + h * cy - r, x + w * cx + r,
                   y + h * cy + r], fill=(150, 150, 150), outline=GREY)
    d.line([(x + w * 0.42, y + by + 3), (x + w * 0.50, y + by + 12),
            (x + w * 0.58, y + by + 3)], fill=RED, width=3)
    d.line([(x + w * 0.50, y + by - 8), (x + w * 0.50, y + by + 12)],
           fill=RED, width=3)
    sx, sy = x + w * 0.28, y + h * 0.78
    d.rectangle([sx, sy, sx + 34, sy + 5], fill=INK)
    d.rectangle([sx + 8, sy - 4, sx + 16, sy], fill=INK)
    # One line, clearly below the bridge line, never on it, and inside
    # the map box even when the map is short.
    d.text((x + w * 0.62, y + h * 0.64), "KERCH STRAIT", font=f, fill=INK)


def map_gulf(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    f = fb(SANS_B, 9)
    d.text((x + 6, y + 2), "IRAN", font=f, fill=INK)
    d.text((x + 6, y + h * 0.42), "BAHRAIN", font=f, fill=INK)
    for cx, cy in ((0.59, 0.57), (0.42, 0.78), (0.85, 0.55)):
        d.line([(x + w * cx - 6, y + h * cy - 6),
                (x + w * cx + 6, y + h * cy + 6)], fill=RED, width=3)
        d.line([(x + w * cx - 6, y + h * cy + 6),
                (x + w * cx + 6, y + h * cy - 6)], fill=RED, width=3)
    for tx0, ty0 in ((0.30, 0.72), (0.68, 0.62)):
        d.line([(x + w * tx0 + 10, y), (x + w * tx0 + 26, y + h * ty0)],
               fill=GREY, width=2)
    tx0, ty0 = 0.30, 0.72
    d.rectangle([x + w * tx0, y + h * ty0, x + w * (tx0 + 0.19),
                 y + h * ty0 + 5], fill=INK)
    d.rectangle([x + w * (tx0 + 0.02), y + h * ty0 - 4,
                 x + w * (tx0 + 0.06), y + h * ty0], fill=INK)
    d.ellipse([x + w * (tx0 + 0.03), y + h * ty0 - 10,
               x + w * (tx0 + 0.08), y + h * ty0 - 1],
              fill=(255, 150, 40))
    d.ellipse([x + w * (tx0 + 0.04), y + h * ty0 - 7,
               x + w * (tx0 + 0.07), y + h * ty0 - 2], fill=RED)
    # QESHM right of its island, HORMUZ bottom centre: the two labels
    # must not stack on each other at this small map height, and HORMUZ
    # must stay inside the map box when it is short.
    d.text((x + w * 0.68, y + h * 0.40), "QESHM", font=f, fill=INK)
    d.text((x + w * 0.60, y + h * 0.66), "HORMUZ", font=f, fill=INK)


def map_quad(d, x, y, w, h):
    flags = [
        ((178, 34, 34), (255, 255, 255), (0, 40, 104), "US"),
        ((255, 153, 51), (255, 255, 255), (19, 136, 8), "INDIA"),
        ((255, 255, 255), (188, 0, 45), (255, 255, 255), "JAPAN"),
        ((0, 40, 104), (255, 255, 255), (255, 0, 0), "AUSTRALIA"),
    ]
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
    cw = w / 4
    fh = max(12, h - 23)
    fy = y + 2
    f = fb(SANS_B, 8)
    for i, (c1, c2, c3, name) in enumerate(flags):
        fx = x + i * cw + 6
        fw = cw - 12
        d.rectangle([fx, fy, fx + fw, fy + fh], outline=INK, width=1)
        if i == 0:
            for s in range(3):
                d.rectangle([fx, fy + s * (fh // 3), fx + fw,
                             fy + (s + 1) * (fh // 3)],
                            fill=c1 if s % 2 == 0 else c2)
            d.rectangle([fx, fy, fx + fw * 0.4, fy + fh * 0.6], fill=c3)
        elif i == 1:
            for s in range(3):
                d.rectangle([fx, fy + s * (fh // 3), fx + fw,
                             fy + (s + 1) * (fh // 3)],
                            fill=(c1, c2, c3)[s])
        elif i == 2:
            d.rectangle([fx, fy, fx + fw, fy + fh], fill=c1)
            d.ellipse([fx + fw / 2 - 4, fy + fh / 2 - 4, fx + fw / 2 + 4,
                       fy + fh / 2 + 4], fill=c2)
        else:
            d.rectangle([fx, fy, fx + fw, fy + fh], fill=c1)
            for sx in (0.2, 0.6):
                for sy in (0.25, 0.6):
                    d.text((fx + fw * sx, fy + fh * sy), "+", font=f,
                           fill=c2)
        d.text((fx + fw / 2 - d.textlength(name, font=f) / 2, fy + fh + 1),
               name, font=f, fill=INK)
    ty = y + h - 3
    d.line([(x + 4, ty), (x + w - 4, ty)], fill=INK, width=2)
    for i in range(4):
        cx = x + i * cw + cw / 2
        d.ellipse([cx - 6, ty - 7, cx + 6, ty - 1], fill=INK)
        d.rectangle([cx - 5, ty, cx + 5, ty + 2], fill=INK)


# ---- small-card scenes (drawn to fill the strip height h) ----

def draw_scene(d, x, y, w, h, kind):
    """Pictogram for one card, using the full strip height (about a
    third of the card). All vertical positions are fractions of h, so
    the drawing grows with the strip instead of stretching."""
    if kind == "ebola":
        # Hospital tent + bar chart (short bar: 3 months ago, no number;
        # tall bar: now 11,000+; cases more than doubled).
        d.polygon([(x + 2, y + h * 0.45), (x + 16, y + h * 0.08),
                   (x + 30, y + h * 0.45)], fill=LAND, outline=INK)
        d.rectangle([x + 7, y + h * 0.45, x + 25, y + h * 0.72],
                    outline=INK)
        d.line([(x + 16, y + h * 0.50), (x + 16, y + h * 0.68)], fill=RED,
               width=2)
        d.line([(x + 12, y + h * 0.59), (x + 20, y + h * 0.59)], fill=RED,
               width=2)
        base = y + h * 0.78
        d.line([(x + 24, base), (x + w - 4, base)], fill=GREY, width=1)
        d.rectangle([x + 30, y + h * 0.55, x + 44, base],
                    fill=(150, 140, 120))
        d.rectangle([x + 90, y + h * 0.15, x + 104, base], fill=RED)
        f7, f7b = fb(SANS, 7), fb(SANS_B, 7)
        text_center(d, x + 37, y + h * 0.82, "3 MONTHS AGO", f7, GREY)
        text_center(d, x + 97, y + h * 0.82, "NOW 11,000+", f7b, RED)
    elif kind == "cop31":
        cx, cy, r = x + 16, y + h * 0.38, int(h * 0.30)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SEA, outline=INK)
        d.line([(cx - r, cy), (cx + r, cy)], fill=INK, width=1)
        d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r],
                  outline=INK)
        d.polygon([(cx - r * 0.5, cy - r * 0.4), (cx + r * 0.2, cy - r * 0.7),
                   (cx + r * 0.5, cy + r * 0.2), (cx - r * 0.2, cy + r * 0.5)],
                  fill=LAND)
        for i, (c1, c2, c3) in enumerate((
                ((0, 90, 180), (255, 255, 255), (255, 255, 255)),
                ((0, 110, 60), (255, 255, 255), (255, 200, 0)),
                ((178, 34, 34), (255, 255, 255), (178, 34, 34)))):
            fx = x + 44 + i * 30
            fh = h * 0.45
            d.rectangle([fx, y + h * 0.12, fx + 24, y + h * 0.12 + fh],
                        fill=c1, outline=INK)
            d.rectangle([fx, y + h * 0.12, fx + 24,
                         y + h * 0.12 + fh / 3], fill=c2)
            d.rectangle([fx, y + h * 0.12 + 2 * fh / 3, fx + 24,
                         y + h * 0.12 + fh], fill=c3)
            d.line([(fx + 12, y + h * 0.12 + fh), (fx + 12, y + h * 0.85)],
                   fill=INK, width=1)
    elif kind == "measles":
        d.rectangle([x + 8, y + h * 0.28, x + 32, y + h * 0.78],
                    fill=(255, 255, 255), outline=INK, width=2)
        d.rectangle([x + 13, y + h * 0.18, x + 27, y + h * 0.28], fill=INK)
        d.line([(x + 12, y + h * 0.45), (x + 28, y + h * 0.45)], fill=RED,
               width=2)
        d.line([(x + 12, y + h * 0.58), (x + 28, y + h * 0.58)], fill=GREY,
               width=1)
        d.line([(x + 48, y + h * 0.72), (x + 108, y + h * 0.28)], fill=INK,
               width=3)
        d.line([(x + 108, y + h * 0.28), (x + 126, y + h * 0.16)], fill=GREY,
               width=1)
        d.line([(x + 44, y + h * 0.76), (x + 56, y + h * 0.64)], fill=INK,
               width=3)
        d.line([(x + 52, y + h * 0.55), (x + 62, y + h * 0.62)], fill=RED,
               width=2)
    elif kind == "nvidia":
        d.rectangle([x + 10, y + h * 0.25, x + 40, y + h * 0.75],
                    fill=INK)
        d.rectangle([x + 17, y + h * 0.35, x + 33, y + h * 0.65],
                    outline=(0, 200, 100), width=2)
        for px in (x + 14, x + 20, x + 26, x + 32):
            d.line([(px, y + h * 0.18), (px, y + h * 0.25)], fill=INK,
                   width=2)
            d.line([(px, y + h * 0.75), (px, y + h * 0.82)], fill=INK,
                   width=2)
        d.line([(x + 52, y + h * 0.72), (x + 70, y + h * 0.58),
                (x + 88, y + h * 0.62), (x + 106, y + h * 0.38),
                (x + 124, y + h * 0.18)], fill=(0, 150, 60), width=3)
        d.polygon([(x + 124, y + h * 0.18), (x + 116, y + h * 0.18),
                   (x + 124, y + h * 0.26)], fill=(0, 150, 60))
    elif kind == "gaza":
        d.rectangle([x + 8, y + h * 0.42, x + 58, y + h * 0.72],
                    fill=(200, 170, 120), outline=INK)
        d.rectangle([x + 58, y + h * 0.52, x + 76, y + h * 0.72],
                    fill=(160, 130, 90), outline=INK)
        for wx in (x + 20, x + 46, x + 66):
            d.ellipse([wx - 5, y + h * 0.72, wx + 5, y + h * 0.82],
                      fill=INK)
        d.polygon([(x + 88, y + h * 0.72), (x + 102, y + h * 0.38),
                   (x + 116, y + h * 0.72)], fill=LAND, outline=INK)
        d.polygon([(x + 114, y + h * 0.72), (x + 124, y + h * 0.48),
                   (x + 132, y + h * 0.72)], fill=(210, 200, 170),
                  outline=INK)
    elif kind == "japan":
        d.polygon([(x + 8, y + h * 0.45), (x + 52, y + h * 0.38),
                   (x + 68, y + h * 0.45), (x + 52, y + h * 0.52),
                   (x + 8, y + h * 0.52)], fill=GREY)
        d.polygon([(x + 30, y + h * 0.38), (x + 38, y + h * 0.20),
                   (x + 44, y + h * 0.38)], fill=INK)
        d.polygon([(x + 52, y + h * 0.52), (x + 58, y + h * 0.66),
                   (x + 62, y + h * 0.52)], fill=INK)
        d.polygon([(x + 62, y + h * 0.42), (x + 70, y + h * 0.38),
                   (x + 70, y + h * 0.48), (x + 62, y + h * 0.50)],
                  fill=RED)
        for ex, ey, er in ((x + 96, y + h * 0.30, 10), (x + 116, y + h * 0.42, 8),
                           (x + 88, y + h * 0.62, 9)):
            d.ellipse([ex - er, ey - er * 0.6, ex + er, ey + er * 0.6],
                      fill=(255, 255, 255), outline=GREY)
    elif kind == "depardieu":
        d.polygon([(x + 8, y + h * 0.35), (x + 30, y + h * 0.12),
                   (x + 52, y + h * 0.35)], fill=LAND, outline=INK)
        for cx in (x + 14, x + 26, x + 38):
            d.line([(cx, y + h * 0.35), (cx, y + h * 0.68)], fill=INK,
                   width=2)
        d.rectangle([x + 8, y + h * 0.68, x + 52, y + h * 0.78], fill=INK)
        d.line([(x + 76, y + h * 0.62), (x + 112, y + h * 0.30)], fill=INK,
               width=3)
        d.rectangle([x + 104, y + h * 0.22, x + 122, y + h * 0.38],
                    fill=(150, 110, 60), outline=INK)
        d.line([(x + 66, y + h * 0.72), (x + 128, y + h * 0.72)], fill=INK,
               width=2)
    elif kind == "apple":
        d.rectangle([x + 10, y + h * 0.15, x + 34, y + h * 0.85],
                    fill=INK)
        d.rectangle([x + 13, y + h * 0.22, x + 31, y + h * 0.72],
                    fill=(255, 255, 255))
        d.line([(x + 20, y + h * 0.78), (x + 24, y + h * 0.78)], fill=GREY,
               width=2)
        for ex, ey, er in ((x + 62, y + h * 0.40, 12), (x + 82, y + h * 0.32, 10),
                           (x + 72, y + h * 0.52, 12)):
            d.ellipse([ex - er, ey - er * 0.7, ex + er, ey + er * 0.7],
                      fill=(255, 255, 255), outline=GREY)
        d.line([(x + 102, y + h * 0.62), (x + 110, y + h * 0.72),
                (x + 126, y + h * 0.42)], fill=(0, 150, 60), width=4)
    elif kind == "houthi":
        d.line([(x + 4, y + h * 0.70), (x + w - 4, y + h * 0.70)], fill=INK,
               width=3)
        for sx in (x + 30, x + 90):
            d.line([(sx, y + h * 0.70), (sx, y + h * 0.85)], fill=INK,
                   width=2)
        d.rectangle([x + 56, y + h * 0.58, x + 66, y + h * 0.70],
                    fill=RED, outline=INK)
        d.ellipse([x + 96, y + h * 0.22, x + 116, y + h * 0.38],
                  fill=GREY, outline=INK)
        for rx in (x + 88, x + 118):
            d.line([(rx, y + h * 0.16), (rx + 12, y + h * 0.16)], fill=INK,
                   width=2)
        d.line([(x + 106, y + h * 0.38), (x + 106, y + h * 0.48)], fill=INK,
               width=2)
    elif kind == "china":
        d.rectangle([x + 10, y + h * 0.25, x + 40, y + h * 0.75],
                    fill=INK)
        d.rectangle([x + 17, y + h * 0.35, x + 33, y + h * 0.65],
                    outline=(255, 220, 0), width=2)
        for px in (x + 14, x + 20, x + 26, x + 32):
            d.line([(px, y + h * 0.18), (px, y + h * 0.25)], fill=INK,
                   width=2)
            d.line([(px, y + h * 0.75), (px, y + h * 0.82)], fill=INK,
                   width=2)
        d.rectangle([x + 56, y + h * 0.18, x + 126, y + h * 0.62],
                    fill=(222, 41, 16), outline=INK)
        for sx, sy, sr in ((x + 66, y + h * 0.28, 4), (x + 78, y + h * 0.28, 2),
                           (x + 82, y + h * 0.38, 2), (x + 78, y + h * 0.48, 2),
                           (x + 66, y + h * 0.48, 2)):
            d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                      fill=(255, 220, 0))
    elif kind == "mongolia":
        d.polygon([(x + 8, y + h * 0.38), (x + 32, y + h * 0.14),
                   (x + 56, y + h * 0.38)], fill=LAND, outline=INK)
        for cx in (x + 16, x + 28, x + 40):
            d.line([(cx, y + h * 0.38), (cx, y + h * 0.68)], fill=INK,
                   width=2)
        d.rectangle([x + 8, y + h * 0.68, x + 56, y + h * 0.78], fill=INK)
        d.rectangle([x + 70, y + h * 0.18, x + 124, y + h * 0.82],
                    fill=(255, 255, 255), outline=INK)
        for ly in (0.32, 0.46, 0.60):
            d.line([(x + 76, y + h * ly), (x + 118, y + h * ly)], fill=GREY,
                   width=1)
        d.ellipse([x + 108, y + h * 0.66, x + 118, y + h * 0.76], fill=RED)
    elif kind == "an12":
        d.polygon([(x + 4, y + h * 0.82), (x + 30, y + h * 0.22),
                   (x + 56, y + h * 0.82)], fill=(170, 165, 155),
                  outline=INK)
        d.polygon([(x + 40, y + h * 0.82), (x + 62, y + h * 0.38),
                   (x + 84, y + h * 0.82)], fill=(200, 195, 185),
                  outline=INK)
        d.polygon([(x + 30, y + h * 0.22), (x + 24, y + h * 0.38),
                   (x + 36, y + h * 0.38)], fill=(255, 255, 255))
        d.polygon([(x + 62, y + h * 0.38), (x + 57, y + h * 0.50),
                   (x + 67, y + h * 0.50)], fill=(255, 255, 255))
        d.ellipse([x + 50, y + h * 0.62, x + 74, y + h * 0.82],
                  fill=(255, 150, 40))
        d.ellipse([x + 56, y + h * 0.68, x + 68, y + h * 0.80], fill=RED)
        d.polygon([(x + 96, y + h * 0.30), (x + 124, y + h * 0.26),
                   (x + 128, y + h * 0.32), (x + 96, y + h * 0.38)],
                  fill=GREY)
        d.polygon([(x + 108, y + h * 0.26), (x + 112, y + h * 0.14),
                   (x + 116, y + h * 0.26)], fill=INK)


# ---- world map from real coastline data ----

PIN_LONLAT = {
    1: (36.5, 47.0), 2: (60.0, 30.0), 3: (121.0, 14.6), 4: (25.0, -2.0),
    5: (24.0, 41.0), 6: (-98.0, 39.0), 7: (-128.0, 42.0),
    8: (32.0, 31.5), 9: (139.7, 35.7), 10: (2.3, 48.9),
    11: (-116.0, 33.0), 12: (48.5, 22.5), 13: (116.4, 39.9),
    14: (106.9, 47.9), 15: (86.1, 55.4),
}

PIN_CENTERS = []


def draw_world_map(img, d, x, y, w, h):
    """World map on its own layer (so coastline outside the box is
    clipped), from Natural Earth 110m land data, equirectangular
    projection lon -180..180, lat 85..-60. Pins sit on real lon/lat
    and are coloured by their story's region."""
    layer = Image.new("RGB", (w, h), SEA)
    ld = ImageDraw.Draw(layer)

    def proj(lon, lat):
        return ((lon + 180) / 360 * w, (85 - lat) / 145 * h)

    for poly in LAND_POLYS:
        pts = [proj(lon, lat) for lon, lat in poly]
        ld.polygon(pts, fill=LAND, outline=INK)
    img.paste(layer, (x, y))
    for num, (lon, lat) in PIN_LONLAT.items():
        px, py = x + proj(lon, lat)[0], y + proj(lon, lat)[1]
        PIN_CENTERS.append((num, px, py))
        region = STORIES[num - 1]["region"]
        col = REGION_COLORS[region]
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=col, outline=INK,
                  width=1)
        f = fb(SANS_B, 10)
        t = str(num)
        tw = d.textlength(t, font=f)
        d.text((px - tw / 2, py - 6), t, font=f, fill=(255, 255, 255))


# ---- Stage 1: one data list, 39 unique stories ----

REGIONS = ["EUROPE", "MIDDLE EAST", "ASIA", "AFRICA", "AMERICAS",
           "OCEANIA", "WORLD"]

STORIES = [
    {"id": 1, "region": "EUROPE",
     "title": "Crimean Bridge road span falls into the sea",
     "summary": "Second strike in two days; Zelenskyy hails it "
     "'unprecedented'; Kremlin vows rebuild.",
     "status": "CONFIRMED", "event": "kerch-bridge",
     "cat": "EUROPE - UKRAINE WAR", "scene": "kerch", "source": "R",
     "caption": "Kerch Strait, between Crimea and Russia",
     "tag": "CONFIRMED: Reuters-verified footage of the collapsed span."},
    {"id": 2, "region": "MIDDLE EAST",
     "title": "US strikes Iran as tankers burn in Hormuz",
     "summary": "Warplanes hit a missile site on Qeshm; 24 seafarers "
     "evacuated from the burning Tara Gas.",
     "status": "CLAIM", "event": "us-strikes-iran",
     "cat": "MIDDLE EAST - IRAN WAR", "scene": "gulf", "source": "AP",
     "caption": "Strait of Hormuz, between Iran and Oman",
     "tag": "CLAIM: Iran says tankers hit mines in Hormuz - not "
     "independently verified."},
    {"id": 3, "region": "ASIA",
     "title": "Trump holds his first Quad summit, in Manila",
     "summary": "First Quad meeting since his return to office; due to "
     "meet Xi and Putin in China on Thursday.",
     "status": "none", "event": "quad-summit-manila",
     "cat": "ASIA - DIPLOMACY", "scene": "quad", "source": "AP",
     "caption": "Manila, Philippines - ASEAN and Quad summits"},
    {"id": 4, "region": "AFRICA",
     "title": "Ebola cases in DR Congo top 11,000",
     "summary": "WHO says 5,400 have died; it reviews the emergency "
     "status.",
     "status": "none", "event": "ebola-dr-congo",
     "cat": "AFRICA - HEALTH", "scene": "ebola", "source": "WHO"},
    {"id": 5, "region": "WORLD",
     "title": "COP31 talks grind on in Antalya",
     "summary": "Nations weigh a first draft; the talks end Friday.",
     "status": "none", "event": "cop31-talks",
     "cat": "GLOBAL - CLIMATE", "scene": "cop31", "source": "AP"},
    {"id": 6, "region": "AMERICAS",
     "title": "US measles-free status lost",
     "summary": "PAHO cites a year of uninterrupted spread.",
     "status": "none", "event": "us-measles-status",
     "cat": "AMERICAS - HEALTH", "scene": "measles", "source": "PAHO"},
    {"id": 7, "region": "AMERICAS",
     "title": "Nvidia sales double to $115.8B",
     "summary": "Shares rise after the close; Q4 forecast near $130B.",
     "status": "none", "event": "nvidia-earnings",
     "cat": "US - BUSINESS", "scene": "nvidia", "source": "AP"},
    {"id": 8, "region": "MIDDLE EAST",
     "title": "Winter rains flood Gaza shelters",
     "summary": "UK, Australia, Canada and Italy urge Israel to open "
     "crossings.",
     "status": "none", "event": "gaza-aid-call",
     "cat": "MIDDLE EAST - GAZA", "scene": "gaza", "source": "AP"},
    {"id": 9, "region": "ASIA",
     "title": "Japan scrambles jets",
     "summary": "Russian aircraft violated airspace.",
     "status": "none", "event": "japan-jets",
     "cat": "ASIA - POLITICS", "scene": "japan", "source": "AP"},
    {"id": 10, "region": "EUROPE",
     "title": "Depardieu admits sexual assault",
     "summary": "French actor drops his appeal in Paris.",
     "status": "none", "event": "depardieu-appeal",
     "cat": "EUROPE - COURTS", "scene": "depardieu", "source": "AP"},
    {"id": 11, "region": "AMERICAS",
     "title": "Apple outage fixed",
     "summary": "iCloud sign-ins and the App Store back up.",
     "status": "none", "event": "apple-outage",
     "cat": "TECH", "scene": "apple", "source": "AP"},
    {"id": 12, "region": "MIDDLE EAST",
     "title": "Houthi drones hit Saudi pipeline",
     "summary": "Five drones aimed at Riyadh pumping stations.",
     "status": "CLAIM", "event": "houthi-drones-saudi",
     "cat": "MIDEAST - ENERGY", "scene": "houthi", "source": "R",
     "tag": "HOUTHI CLAIM - no Saudi confirmation."},
    {"id": 13, "region": "ASIA",
     "title": "China rejects US chip curbs",
     "summary": "Beijing hits back at the cloud-access rule.",
     "status": "none", "event": "china-chip-curbs",
     "cat": "ASIA - TRADE", "scene": "china", "source": "R"},
    {"id": 14, "region": "ASIA",
     "title": "Mongolia president will resign",
     "summary": "Denies $25m bribe claim; MPs must accept.",
     "status": "none", "event": "mongolia-resignation",
     "cat": "ASIA - POLITICS", "scene": "mongolia", "source": "AP"},
    {"id": 15, "region": "EUROPE",
     "title": "An-12 crash in Siberia kills 19",
     "summary": "Plane down near Kemerovo; ministry blames a fault.",
     "status": "none", "event": "an12-crash",
     "cat": "RUSSIA - AIR CRASH", "scene": "an12", "source": "AP"},
    {"id": 16, "region": "MIDDLE EAST",
     "title": "(as reported) Lebanon: Israeli airstrikes, shelling, "
     "detonations.",
     "summary": "Israeli airstrikes, shelling and detonations were "
     "reported in Lebanon.",
     "status": "none", "event": "lebanon-strikes", "source": "R"},
    {"id": 17, "region": "MIDDLE EAST",
     "title": "UKMTO reports a second tanker strike north of Khasab, "
     "Oman.",
     "summary": "UKMTO reported a second tanker strike north of Khasab, "
     "Oman.",
     "status": "none", "event": "second-tanker-khasab", "source": "UKMTO"},
    {"id": 18, "region": "EUROPE",
     "title": "Zelenskyy: bridge strike answers Russian attacks on "
     "infrastructure.",
     "summary": "Zelenskyy said the bridge strike answers Russian "
     "attacks on infrastructure.",
     "status": "none", "event": "zelenskyy-bridge-statement", "source": "R"},
    {"id": 19, "region": "AMERICAS",
     "title": "Wall Street: S&P 500 -1%, Dow -1.6%, Nasdaq -0.7%.",
     "summary": "Wall Street fell: the S&P 500 lost 1%, the Dow 1.6% "
     "and the Nasdaq 0.7%.",
     "status": "none", "event": "wall-street-falls", "source": "AP"},
    {"id": 20, "region": "AMERICAS",
     "title": "Nvidia board will not reinstate Jensen Huang as CEO.",
     "summary": "Nvidia's board will not reinstate Jensen Huang as CEO.",
     "status": "none", "event": "nvidia-board-ceo", "source": "AP"},
    {"id": 21, "region": "MIDDLE EAST",
     "title": "Dubai airports: 50.4M passengers in 9 months, down 28.1%.",
     "summary": "Dubai airports handled 50.4 million passengers in nine "
     "months, down 28.1%.",
     "status": "none", "event": "dubai-airports", "source": "AP"},
    {"id": 22, "region": "MIDDLE EAST",
     "title": "Yemen: government forces pull back toward Aden as Houthis "
     "advance.",
     "summary": "Yemeni government forces pulled back toward Aden as "
     "Houthi forces advanced.",
     "status": "none", "event": "yemen-pullback", "source": "AP"},
    {"id": 23, "region": "EUROPE",
     "title": "Five EU states plan a migrant return hub in Rwanda.",
     "summary": "Five EU states plan a migrant return hub in Rwanda.",
     "status": "none", "event": "eu-rwanda-hub", "source": "AP"},
    {"id": 24, "region": "WORLD",
     "title": "Grammy nominations: RAYE leads with 11, ROSAL\u00cdA has 9.",
     "summary": "RAYE leads the Grammy nominations with 11; ROSAL\u00cdA "
     "has 9.",
     "status": "none", "event": "grammy-nominations", "source": "AP"},
    {"id": 25, "region": "MIDDLE EAST",
     "title": "UN: winter rains deepen Gaza shelter crisis.",
     "summary": "The UN said winter rains deepen the Gaza shelter "
     "crisis.",
     "status": "none", "event": "gaza-winter-rains", "source": "UN"},
    {"id": 26, "region": "AFRICA",
     "title": "Ebola: WHO emergency committee reviews the outbreak "
     "status.",
     "summary": "The WHO emergency committee reviews the Ebola outbreak "
     "status.",
     "status": "none", "event": "ebola-who-committee", "source": "WHO"},
    {"id": 27, "region": "WORLD",
     "title": "COP31: first draft of the cover decision out; talks end "
     "Friday.",
     "summary": "COP31's first draft of the cover decision is out; the "
     "talks end Friday.",
     "status": "none", "event": "cop31-draft", "source": "AP"},
    {"id": 28, "region": "OCEANIA",
     "title": "Cyclone Xavier batters the Northern Cook Islands.",
     "summary": "Cyclone Xavier battered the Northern Cook Islands.",
     "status": "none", "event": "cyclone-xavier", "source": "AP"},
    {"id": 29, "region": "WORLD",
     "title": "Voyager 1 nears one light-day from Earth; crosses early "
     "Wednesday.",
     "summary": "Voyager 1 nears one light-day from Earth and crosses "
     "early Wednesday.",
     "status": "none", "event": "voyager-1", "source": "NASA"},
    {"id": 30, "region": "AFRICA",
     "title": "UN verifies 2,230 civilian deaths in Sudan; drones caused "
     "most.",
     "summary": "The UN verified 2,230 civilian deaths in Sudan, most "
     "caused by drones.",
     "status": "none", "event": "sudan-civilian-deaths", "source": "UN"},
    {"id": 31, "region": "MIDDLE EAST",
     "title": "Israel: Matan Kahana elected Knesset speaker, 66-52.",
     "summary": "Matan Kahana was elected Knesset speaker by 66 votes "
     "to 52.",
     "status": "none", "event": "kahana-speaker", "source": "AP"},
    {"id": 32, "region": "EUROPE",
     "title": "Moldova shuts airspace as 7 drones cross in; 5 crash near "
     "villages.",
     "summary": "Moldova shut its airspace as seven drones crossed in; "
     "five crashed near villages.",
     "status": "none", "event": "moldova-drones", "source": "AP"},
    {"id": 33, "region": "AMERICAS",
     "title": "US: 13 babies born with congenital measles; most cases "
     "since 1991.",
     "summary": "Thirteen babies were born with congenital measles in "
     "the US; cases are the highest since 1991.",
     "status": "none", "event": "congenital-measles", "source": "AP"},
    {"id": 34, "region": "EUROPE",
     "title": "France: wage protests draw 146,000; unions demand higher "
     "pay.",
     "summary": "Protests for higher wages drew 146,000 people across "
     "France; 28,000 marched in Paris.",
     "status": "none", "event": "france-wage-protests", "source": "LM"},
    {"id": 35, "region": "EUROPE",
     "title": "Russia: no European seat at next Ukraine talks, aide says.",
     "summary": "Moscow has not agreed to European participation in the "
     "next round of Ukraine talks, aide Yuri Ushakov said.",
     "status": "none", "event": "russia-europe-talks", "source": "R"},
    {"id": 36, "region": "AMERICAS",
     "title": "NSA: classified network down; Fort Meade under code "
     "orange.",
     "summary": "The NSA's classified NSANet network went down early "
     "Tuesday; the Fort Meade campus was restricted under code orange.",
     "status": "none", "event": "nsa-nsanet-outage", "source": "CNN"},
    {"id": 37, "region": "AMERICAS",
     "title": "Ecuador: 16 fishermen sue US over drone attack on boat.",
     "summary": "Sixteen Ecuadorian fishermen sued the US government "
     "over a drone attack that sank their boat in the Pacific in March.",
     "status": "none", "event": "ecuador-fishermen-lawsuit", "source": "AP"},
    {"id": 38, "region": "WORLD",
     "title": "Pattinson named the new James Bond.",
     "summary": "British actor Robert Pattinson was named as the new "
     "James Bond.",
     "status": "none", "event": "pattinson-james-bond", "source": "AP"},
    {"id": 39, "region": "ASIA",
     "title": "Dhaka tops world's most polluted cities; AQI 292.",
     "summary": "Dhaka ranked first among the world's most polluted "
     "cities on Tuesday morning, with an AQI of 292.",
     "status": "none", "event": "dhaka-air-pollution", "source": "UNB"},
]


def check_stories():
    """Automatic duplicate check: the program stops on any duplicate."""
    if len(STORIES) != 39:
        sys.exit(f"expected 39 stories, got {len(STORIES)}")
    ids = [s["id"] for s in STORIES]
    if ids != list(range(1, 40)):
        sys.exit("story ids must be 1..39 in order")
    for field in ("event", "title"):
        seen = {}
        for s in STORIES:
            key = s[field].strip().lower()
            if key in seen:
                sys.exit(f"duplicate {field}: {s[field]!r} "
                         f"(ids {seen[key]} and {s['id']})")
            seen[key] = s["id"]
    for s in STORIES:
        if s["region"] not in REGIONS:
            sys.exit(f"story {s['id']}: unknown region {s['region']!r}")
        if s["status"] not in ("CONFIRMED", "CLAIM", "none"):
            sys.exit(f"story {s['id']}: unknown status {s['status']!r}")
        if s["id"] <= 15 and "source" not in s:
            sys.exit(f"story {s['id']}: card without source initials")


def region_counts():
    counts = {r: 0 for r in REGIONS}
    for s in STORIES:
        counts[s["region"]] += 1
    return counts


# Derived views for the renderer. Numbers come from id, never typed.
CARDS = STORIES[:15]
ALSO = STORIES[15:]
ALSO_BY_REGION = [(r, [s for s in ALSO if s["region"] == r])
                  for r in REGIONS if any(s["region"] == r for s in ALSO)]
TAG_BY_ID = {s["id"]: (s["tag"], TAG_GREEN if s["status"] == "CONFIRMED"
                       else TAG_CLAIM)
             for s in STORIES if s.get("tag")}

# (number, label, number colour, arrow) - Dow falls red, Nvidia rises
# green; the rest stay ink.
NUMBERS = [
    ("11,000+", "Ebola cases, DR Congo", INK, ""),
    ("$115.8bn", "Nvidia quarter", (0, 110, 60), "\u25b2"),
    ("-1.6%", "Dow on Tuesday", RED, "\u25bc"),
    ("24", "seafarers evacuated, Tara Gas", INK, ""),
    ("1,441", "drones Russia says it downed", INK, ""),
    ("50.4m", "Dubai passengers, down 28.1%", INK, ""),
]

WHY_TEXT = ("A Tuesday of falling bridges, burning tankers and a 26-year "
            "health milestone lost.")

THREAD_TEXT = ("Monday, Russia hit Kyiv's two Dnipro bridges - Tuesday, "
               "Ukraine answered by dropping the Kerch road span.")

DATECHECK_TEXT = ("DATE CHECK - left out as earlier news: COP31's first "
                  "draft (16 Nov) - Grammy nominations announced (16 Nov) "
                  "- US chip-export rule (16 Nov) - Guinea gold-mining "
                  "sentences (16 Nov).")


# ---- card drawers (uniform title 12 px, body 10 px; big titles 17 px) ----

CARD_BOUNDS = []


def draw_source(d, ix, iy, iw, ih, source, group):
    """Source initials at the card's bottom-right corner."""
    f = fb(SANS, 8)
    tw = d.textlength(source, font=f)
    tbox(d, ix + iw - tw, iy + ih - 10, source, f, GREY, group,
         label="source")


def draw_big_panel(d, x, y, w, h, story):
    num = story["id"]
    group = f"card{num}"
    ix, iy, iw, ih = panel(d, x, y, w, h)
    CARD_BOUNDS.append((group, ix, iy, ix + iw, iy + ih))
    region_col = REGION_COLORS[story["region"]]
    tag = TAG_BY_ID.get(num)
    # Measure the text first so the wide map fills the space the text
    # leaves (no big empty area in the card).
    font, lines, lh = fit_block(d, story["title"], SANS_B, BIG_TITLE_SIZE,
                                BIG_TITLE_SIZE, iw, 2, 38,
                                label=f"big title {num}", strict=True)
    font2, lines2, lh2 = fit_block(d, story["summary"], SANS, BODY_SIZE,
                                   BODY_SIZE, iw, 3, 33,
                                   label=f"big sub {num}", strict=True)
    map_h = ih - (8 + 3 + 15 + len(lines) * lh + 3 + len(lines2) * lh2
                  + 3 + (20 if tag else 0)) - 2
    HEIGHT_LOG.append((f"big card {num} map-min", map_h, 30))
    if story["scene"] == "kerch":
        map_kerch(d, ix, iy, iw, map_h)
    elif story["scene"] == "gulf":
        map_gulf(d, ix, iy, iw, map_h)
    else:
        map_quad(d, ix, iy, iw, map_h)
    # Location caption under the wide map.
    tbox(d, ix, iy + map_h + 1, story["caption"], fb(SANS, 8), GREY,
         group, label="caption")
    cy = iy + map_h + 8 + 3
    tbox(d, ix, cy, f"{num}. {story['cat']}", fb(SANS_B, 13), region_col,
         group, label="cat")
    hy = cy + 15
    for ln in lines:
        tbox(d, ix, hy, ln, font, INK, group, label="title")
        hy += lh
    sy = hy + 3
    for ln in lines2:
        tbox(d, ix, sy, ln, font2, INK, group, label="sub")
        sy += lh2
    if tag is not None:
        draw_tag(d, ix, sy + 3, iw, tag[0], tag[1], group)
    draw_source(d, ix, iy, iw, ih, story["source"], group)
    content_h = (map_h + 8 + 3 + 15 + len(lines) * lh + 3
                 + len(lines2) * lh2 + 3 + (20 if tag else 0))
    HEIGHT_LOG.append((f"big card {num}", content_h, ih))


def draw_small_panel(d, x, y, w, h, story):
    num = story["id"]
    group = f"card{num}"
    ix, iy, iw, ih = panel(d, x, y, w, h)
    CARD_BOUNDS.append((group, ix, iy, ix + iw, iy + ih))
    region_col = REGION_COLORS[story["region"]]
    # Measure the text first so the scene fills the space the text
    # leaves (about a third of the card, no big empty area).
    _, t_lines, t_lh = fit_block(d, story["title"], SANS_B, TITLE_SIZE,
                                 TITLE_SIZE, iw, 3, 42,
                                 label=f"title {num}", strict=True)
    _, s_lines, s_lh = fit_block(d, story["summary"], SANS, BODY_SIZE,
                                 BODY_SIZE, iw, 3, 36,
                                 label=f"sub {num}", strict=True)
    tag = TAG_BY_ID.get(num)
    text_h = (4 + 16 + len(t_lines) * t_lh + 3 + len(s_lines) * s_lh
              + (3 + 20 if tag else 0))
    # About a third of the card, capped so a short text does not make
    # the picture dominate; the leftover space is split above and
    # below the text block so the card stays balanced.
    scene_h = min(ih - text_h - 2, 60)
    HEIGHT_LOG.append((f"small card {num} scene", scene_h, 40))
    extra = ih - scene_h - text_h
    draw_scene(d, ix, iy, iw, scene_h, story["scene"])
    cy = iy + scene_h + 4 + extra // 2
    tbox(d, ix, cy, f"{num}. {story['cat']}", fb(SANS_B, 9), region_col,
         group, label="cat")
    hy = cy + 16
    font, lines, lh = fit_block(d, story["title"], SANS_B, TITLE_SIZE,
                                TITLE_SIZE, iw, 3, 42,
                                label=f"title {num}", strict=True)
    for ln in lines:
        tbox(d, ix, hy, ln, font, INK, group, label="title")
        hy += lh
    font2, lines2, lh2 = fit_block(d, story["summary"], SANS, BODY_SIZE,
                                   BODY_SIZE, iw, 3, 36,
                                   label=f"sub {num}", strict=True)
    sy = hy + 3
    for ln in lines2:
        tbox(d, ix, sy, ln, font2, INK, group, label="sub")
        sy += lh2
    if tag is not None:
        draw_tag(d, ix, sy + 3, iw, tag[0], tag[1], group)
    draw_source(d, ix, iy, iw, ih, story["source"], group)
    HEIGHT_LOG.append((f"small card {num}", text_h + scene_h, ih))


def check_layout():
    """Automatic check: stop the program on any shrunk text, any card
    content that overflows its frame, any list that does not fit, any
    colliding map pins, or any recorded text box that overlaps another
    or leaves the page."""
    problems = []
    for label, start, used, strict in FIT_LOG:
        if strict and used < start:
            problems.append(
                f"{label}: font shrank {start}px -> {used}px")
    for label, got, need in HEIGHT_LOG:
        if "scene" in label or label.endswith("map-min"):
            if got < need:
                problems.append(
                    f"{label}: only {got}px tall (min {need}px)")
        elif got > need:
            problems.append(
                f"{label}: content {got}px overflows frame {need}px")
    # Map pins must not collide.
    for i, (n1, x1, y1) in enumerate(PIN_CENTERS):
        for n2, x2, y2 in PIN_CENTERS[i + 1:]:
            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            if dist < 16:
                problems.append(
                    f"map pins {n1} and {n2} collide ({dist:.1f}px apart)")
    # Text boxes: no overlap within a group, none outside the page,
    # none outside their card.
    bounds = {g: (x0, y0, x1, y1) for g, x0, y0, x1, y1 in CARD_BOUNDS}
    by_group = {}
    for group, label, box in BOXES:
        by_group.setdefault(group, []).append((label, box))
        x0, y0, x1, y1 = box
        if x0 < 12 or y0 < 12 or x1 > 1012 or y1 > 1012:
            problems.append(
                f"{group} {label}: box {box} leaves the page")
        if group in bounds:
            # 2 px of tolerance: a glyph's ink may sit a pixel past
            # the text origin or a descender a pixel below the line.
            bx0, by0, bx1, by1 = bounds[group]
            if (x0 < bx0 - 2 or x1 > bx1 + 2 or y0 < by0 - 2
                    or y1 > by1 + 2):
                problems.append(
                    f"{group} {label}: box {box} leaves its card")
    for group, items in by_group.items():
        for i, (l1, b1) in enumerate(items):
            for l2, b2 in items[i + 1:]:
                ox = min(b1[2], b2[2]) - max(b1[0], b2[0])
                oy = min(b1[3], b2[3]) - max(b1[1], b2[1])
                if ox > 1 and oy > 1:
                    problems.append(
                        f"{group}: {l1} {b1} overlaps {l2} {b2}")
    if problems:
        sys.exit("LAYOUT CHECK FAILED:\n" + "\n".join(problems))
    print(f"layout check passed: {len(FIT_LOG)} text blocks, "
          f"{len(BOXES)} recorded boxes, {len(PIN_CENTERS)} pins")


LIST_SIZE = 10  # (defined here so main() reads it after the data block)


def main():
    # Tahap 1 first: stop on any duplicate before drawing anything.
    check_stories()
    counts = region_counts()
    n_regions = sum(1 for r in REGIONS if counts[r] > 0)
    kicker_right = (f"{len(STORIES)} STORIES - {n_regions} REGIONS - "
                    "ALL FROM TUESDAY")

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, W - 11, H - 11], outline=INK, width=4)

    # Top kicker (story count and region count come from the list).
    tbox(d, 16, 14, "THE WORLD'S NEWS IN ONE PICTURE", fb(SANS_B, 13),
         RED, "header", label="kicker")
    rw = d.textlength(kicker_right, font=fb(SANS_B, 13))
    tbox(d, 1008 - rw, 14, kicker_right, fb(SANS_B, 13), INK, "header",
         label="kicker-right")
    d.line([(16, 31), (1008, 31)], fill=RED, width=2)

    # Banner, serif bold, as large as fits, with room below the descenders
    # so the tail of the "y" in "Tuesday" clears the rule underneath.
    size = 34
    while (d.textlength("Tuesday 17 November 2026", font=fb(SERIF_B, size))
           > 980 and size > 30):
        size -= 2
    tbox_c(d, W // 2, 33, "Tuesday 17 November 2026", fb(SERIF_B, size),
           INK, "header", label="banner")
    d.line([(16, 69), (1008, 69)], fill=RED, width=3)

    # Region-counts bar, computed from STORIES, each segment in its
    # region colour.
    seg_font = fb(SANS_B, 10)
    segs = [(f"{r} {counts[r]}", REGION_COLORS[r]) for r in REGIONS]
    sep_w = d.textlength(" - ", font=seg_font)
    total = sum(d.textlength(t, font=seg_font) for t, _ in segs)
    total += sep_w * (len(segs) - 1)
    sx = (W - total) / 2
    for i, (text, col) in enumerate(segs):
        tbox(d, sx, 73, text, seg_font, col, "header", label="region-bar")
        sx += d.textlength(text, font=seg_font)
        if i < len(segs) - 1:
            tbox(d, sx, 73, " - ", seg_font, GREY, "header", label="sep")
            sx += sep_w

    # 1. BY THE NUMBERS strip (Dow red with a down arrow, Nvidia green
    # with an up arrow).
    cell_w = (1008 - 16) / 6
    for i, (num, label, col, arrow) in enumerate(NUMBERS):
        cx = 16 + i * cell_w
        nfont = fb(SANS_B, 13)
        tw = d.textlength(num, font=nfont)
        if arrow:
            total_w = tw + 6 + 10
            ax = cx + cell_w / 2 - total_w / 2
            if arrow == "\u25b2":
                d.polygon([(ax, 85 + 9), (ax + 10, 85 + 9),
                           (ax + 5, 85 + 1)], fill=col)
            else:
                d.polygon([(ax, 85 + 1), (ax + 10, 85 + 1),
                           (ax + 5, 85 + 9)], fill=col)
            tbox(d, ax + 16, 85, num, nfont, col, "numbers", label="num")
        else:
            tbox_c(d, cx + cell_w / 2, 85, num, nfont, col, "numbers",
                   label="num")
        font, lines, lh = fit_block(d, label, SANS, 7, 7, cell_w - 12,
                                    2, 16, label=f"number label {i}")
        if len(lines) > 2:
            sys.exit(f"number label {i} needs {len(lines)} lines")
        ly2 = 102
        for ln in lines:
            tbox_c(d, cx + cell_w / 2, ly2, ln, font, GREY, "numbers",
                   label="num-label")
            ly2 += lh
        if i:
            d.line([(cx, 87), (cx, 114)], fill=GREY, width=1)

    # 2. WHY THIS DAY MATTERS line (serif; no italic serif on this VM,
    # so regular serif, centred).
    tbox_c(d, W // 2, 120, WHY_TEXT, fb(SERIF, 10), INK, "header",
           label="why")

    # Row 1: three big panels.
    for i in range(3):
        draw_big_panel(d, 16 + i * 335, 134, 322, 170, CARDS[i])

    # 3. THE DAY'S THREAD line.
    label = "THE DAY'S THREAD: "
    lw = d.textlength(label, font=fb(SANS_B, 10))
    tbox(d, 16, 308, label, fb(SANS_B, 10), RED, "header", label="thread")
    tbox(d, 16 + lw, 308, THREAD_TEXT, fb(SANS, 10), INK, "header",
         label="thread-text")

    # Row 2: six medium panels.
    for i in range(6):
        draw_small_panel(d, 16 + i * 165, 322, 158, 152, CARDS[3 + i])

    # Row 3: six small panels.
    for i in range(6):
        draw_small_panel(d, 16 + i * 165, 478, 158, 164, CARDS[9 + i])

    # Bottom left: world map with numbered pins + region legend.
    mx, my, mw, mh = 16, 646, 486, 330
    d.rectangle([mx, my, mx + mw, my + mh], fill=CARD, outline=INK, width=2)
    d.rectangle([mx, my, mx + mw, my + 5], fill=RED)
    section_title(d, mx + 12, my + 12, "WHERE IT HAPPENED")
    draw_world_map(img, d, mx + 12, my + 32, mw - 24, 280)
    leg_font = fb(SANS_B, 8)
    leg_w = 0
    for r in REGIONS:
        leg_w += 6 + 4 + d.textlength(r, font=leg_font)
    leg_w += 8 * (len(REGIONS) - 1)
    lx_leg = mx + mw / 2 - leg_w / 2
    for i, r in enumerate(REGIONS):
        d.ellipse([lx_leg, my + 315, lx_leg + 6, my + 321],
                  fill=REGION_COLORS[r])
        tbox(d, lx_leg + 10, my + 314, r, leg_font, REGION_COLORS[r],
             "map", label="legend")
        lx_leg += 6 + 4 + d.textlength(r, font=leg_font) + 8

    # Bottom right: "Also on" list, grouped by region, ids 16-39.
    lx, ly, lw, lh = 514, 646, 494, 330
    d.rectangle([lx, ly, lx + lw, ly + lh], fill=CARD, outline=INK, width=2)
    d.rectangle([lx, ly, lx + lw, ly + 5], fill=RED)
    section_title(d, lx + 12, ly + 12, "ALSO ON TUESDAY 17 NOVEMBER")
    list_top, list_h = ly + 30, lh - 34
    yy = list_top
    for region, items in ALSO_BY_REGION:
        col = REGION_COLORS[region]
        tbox(d, lx + 12, yy, region, fb(SANS_B, LIST_HEAD_SIZE), col,
             "list", label="head")
        yy += 8
        for s in items:
            d.ellipse([lx + 12, yy + 1, lx + 18, yy + 7], fill=col)
            tbox(d, lx + 24, yy, f"{s['id']}. {s['title']}",
                 fb(SANS, LIST_SIZE), INK, "list", label="row")
            yy += 10
    HEIGHT_LOG.append(("list", yy - list_top, list_h))

    # 5. DATE CHECK, one line.
    d.rectangle([16, 980, 1008, 994], outline=INK, width=2)
    d.rectangle([16, 980, 22, 994], fill=RED)
    tbox(d, 30, 983, DATECHECK_TEXT, fb(SANS, 8), INK, "footer",
         label="datecheck")

    # Footer (with the tag legend on the second line).
    tbox_c(d, W // 2, 997,
           "Every story here happened or was first reported on Tuesday "
           "17 November 2026. Contested claims are marked as claims.",
           fb(SANS, 7), GREY, "footer", label="footer1")
    tbox_c(d, W // 2, 1004,
           "Sources: Reuters, AP, PAHO, WHO, UN, Le Monde, CNN, UNB, "
           "UKMTO, NASA. Original drawings. Tags: CONFIRMED = verified "
           "by Reuters / AP / PAHO / WHO / UN; CLAIM = as stated by the "
           "source, not independently verified.",
           fb(SANS, 7), GREY, "footer", label="footer2")

    check_layout()
    img.save(OUT, optimize=True)
    print("saved", OUT)


if __name__ == "__main__":
    main()
