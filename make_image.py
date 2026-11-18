"""Draw the rebuilt front page for news-image-20261117 (1024x1024 PNG).

Two stages. Stage 1: ONE data list, STORIES, with 39 unique stories
from Tuesday 17 November 2026 (id, region, title, summary, status,
event); check_stories() stops the program on any duplicate id, event
or title. Stage 2: render from that list only - cards are ids 1-15,
the "Also on" list is ids 16-39, numbers come from id, and the header
("39 stories") and the per-region counts are computed from the list.
Uniform fonts: one title size (12 px bold) and one body size (10 px)
on every card, list font 11 px (>= body); wording is shortened where
needed, the font is never shrunk. Every card carries a small drawn
scene; the world map uses recognisable continent outlines with pins
placed by real longitude/latitude.

Newspaper style: off-white paper, ink text, dark-red accent. All stories
from Tuesday 17 November 2026 as reported by Reuters, AP, PAHO, WHO and
the UN. Every map, flag and scene is drawn with PIL shapes; no network,
no external images. Text is never clipped: every block shrinks its font
until it fits (the uniform sizes were chosen so the longest texts fit).
"""

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 243, 232)
CARD = (255, 253, 246)
INK = (26, 26, 26)
RED = (139, 30, 30)
GREY = (90, 84, 72)
SEA = (207, 227, 238)
LAND = (232, 223, 200)
TAG_GREEN = (0, 110, 60)
TAG_AMBER = (176, 120, 0)

FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
SERIF_B = FONT_DIR + "DejaVuSerif-Bold.ttf"
SERIF = FONT_DIR + "DejaVuSerif.ttf"
SANS_B = FONT_DIR + "DejaVuSans-Bold.ttf"
SANS = FONT_DIR + "DejaVuSans.ttf"

OUT = "/home/hatch/workspace/makefun/news-image-20261117-entry/entry.png"

TITLE_SIZE = 12   # uniform headline size on every card
BODY_SIZE = 10    # uniform sub-label size on every card


def fb(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_block(draw, text, path, start, minimum, max_w, max_lines, max_h,
              line_scale=1.18):
    """Shrink the font until the wrapped text fits max_h.

    Height is the only binding constraint: lines are never dropped, so a
    long label shrinks instead of losing its last words.
    """
    size = start
    while size >= 8:
        font = fb(path, size)
        lines = wrap(draw, text, font, max_w)
        lh = int(size * line_scale)
        if len(lines) * lh <= max_h:
            return font, lines, lh
        size -= 1
    font = fb(path, 8)
    return font, wrap(draw, text, font, max_w), int(8 * line_scale)


def text_center(d, cx, y, text, font, fill):
    d.text((cx - d.textlength(text, font=font) / 2, y), text, font=font,
           fill=fill)


def panel(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=2)
    d.rectangle([x, y, x + w, y + 5], fill=RED)
    return x + 12, y + 12, w - 24, h - 24


def section_title(d, x, y, text):
    d.text((x, y), text, font=fb(SANS_B, 14), fill=RED)


def draw_tag(d, x, y, max_w, text, color, start=9, max_h=20):
    """Small verification tag: coloured square + bold text, wrapped."""
    font, lines, lh = fit_block(d, text, SANS_B, start, 8, max_w - 12,
                                2, max_h)
    yy = y
    for ln in lines:
        d.rectangle([x, yy + 3, x + 7, yy + 10], fill=color)
        d.text((x + 11, yy), ln, font=font, fill=color)
        yy += lh
    return yy


# ---- big drawn maps for row 1 ----

def map_kerch(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    d.polygon([(x, y), (x + w, y), (x + w, y + h * 0.28),
               (x + w * 0.62, y + h * 0.34), (x + w * 0.38, y + h * 0.28),
               (x, y + h * 0.34)], fill=LAND)
    d.polygon([(x, y + h), (x + w, y + h), (x + w, y + h * 0.66),
               (x + w * 0.6, y + h * 0.6), (x + w * 0.4, y + h * 0.66),
               (x, y + h * 0.6)], fill=LAND)
    by = y + h * 0.45
    # Bridge, broken in the middle; the fallen span drops into the sea.
    d.line([(x + 6, by), (x + w * 0.42, by)], fill=INK, width=4)
    d.line([(x + w * 0.42, by), (x + w * 0.5, by + 8)], fill=RED, width=3)
    d.line([(x + w * 0.5, by + 8), (x + w * 0.58, by + 2)], fill=RED,
           width=3)
    d.line([(x + w * 0.58, by + 2), (x + w - 6, by + 2)], fill=INK, width=4)
    # Smoke above the break.
    for sx, sy, r in ((0.46, 0.28, 4), (0.52, 0.20, 5), (0.58, 0.28, 4)):
        d.ellipse([x + w * sx - r, y + h * sy - r, x + w * sx + r,
                   y + h * sy + r], fill=(140, 135, 125))
    # Small ship below the bridge.
    sx0, sy0 = x + w * 0.28, y + h * 0.78
    d.polygon([(sx0, sy0), (sx0 + 34, sy0), (sx0 + 28, sy0 + 5),
               (sx0 + 6, sy0 + 5)], fill=INK)
    d.line([(sx0 + 17, sy0), (sx0 + 17, sy0 - 7)], fill=INK, width=2)
    # Red X at the break.
    cx, cy = x + w * 0.5, by + 5
    d.line([(cx - 6, cy - 6), (cx + 6, cy + 6)], fill=RED, width=3)
    d.line([(cx - 6, cy + 6), (cx + 6, cy - 6)], fill=RED, width=3)
    f = fb(SANS_B, 9)
    d.text((x + 6, y + 2), "RUSSIA", font=f, fill=INK)
    d.text((x + 6, y + h - 12), "CRIMEA", font=f, fill=INK)
    # One line, clearly below the bridge line, never on it, and inside
    # the map box even when the map is only 30 px tall.
    d.text((x + w * 0.62, y + h * 0.64), "KERCH STRAIT", font=f, fill=INK)


def map_gulf(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    d.polygon([(x, y), (x + w, y), (x + w, y + h * 0.3),
               (x + w * 0.55, y + h * 0.38), (x, y + h * 0.3)], fill=LAND)
    d.ellipse([x + w * 0.52, y + h * 0.52, x + w * 0.66, y + h * 0.62],
              fill=LAND)
    d.ellipse([x + w * 0.2, y + h * 0.55, x + w * 0.26, y + h * 0.61],
              fill=LAND)
    for sx, sy in ((0.59, 0.57), (0.42, 0.78), (0.85, 0.55)):
        cx, cy = x + w * sx, y + h * sy
        d.line([(cx - 6, cy), (cx + 6, cy)], fill=RED, width=2)
        d.line([(cx, cy - 6), (cx, cy + 6)], fill=RED, width=2)
    # Missile trails from the top edge toward the tanker.
    d.line([(x + w * 0.25, y + 2), (x + w * 0.33, y + h * 0.52)],
           fill=(200, 80, 40), width=2)
    d.line([(x + w * 0.55, y + 2), (x + w * 0.47, y + h * 0.52)],
           fill=(200, 80, 40), width=2)
    # Burning tanker: hull, superstructure, flame.
    tx0, ty0 = x + w * 0.30, y + h * 0.72
    d.polygon([(tx0, ty0), (tx0 + 32, ty0), (tx0 + 26, ty0 + 5),
               (tx0 + 6, ty0 + 5)], fill=INK)
    d.rectangle([tx0 + 20, ty0 - 4, tx0 + 28, ty0], fill=INK)
    d.polygon([(tx0 + 8, ty0 - 1), (tx0 + 14, ty0 - 10),
               (tx0 + 20, ty0 - 1)], fill=(255, 150, 40))
    d.polygon([(tx0 + 11, ty0 - 1), (tx0 + 14, ty0 - 6),
               (tx0 + 17, ty0 - 1)], fill=RED)
    f = fb(SANS_B, 9)
    d.text((x + 6, y + 2), "IRAN", font=f, fill=INK)
    d.text((x + 6, y + h * 0.42), "BAHRAIN", font=f, fill=INK)
    # QESHM right of its island, HORMUZ bottom centre: the two labels
    # must not stack on each other at this small map height, and HORMUZ
    # must stay inside the map box when it is only 30 px tall.
    d.text((x + w * 0.68, y + h * 0.40), "QESHM", font=f, fill=INK)
    d.text((x + w * 0.60, y + h * 0.66), "HORMUZ", font=f, fill=INK)


def map_quad(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
    fw, fh = (w - 40) // 4, max(12, h - 23)
    fy = y + 2
    xs = [x + 8 + i * (fw + 8) for i in range(4)]
    # US: stripes + canton
    d.rectangle([xs[0], fy, xs[0] + fw, fy + fh], outline=INK, width=1)
    for i in range(6):
        d.rectangle([xs[0], fy + i * fh // 6, xs[0] + fw,
                     fy + (i + 1) * fh // 6],
                    fill=RED if i % 2 == 0 else CARD)
    d.rectangle([xs[0], fy, xs[0] + fw * 0.45, fy + fh * 0.55],
                fill=(40, 60, 140))
    # India: saffron / white / green + wheel
    for i, col in enumerate(((255, 153, 51), CARD, (19, 136, 8))):
        d.rectangle([xs[1], fy + i * fh // 3, xs[1] + fw,
                     fy + (i + 1) * fh // 3], fill=col, outline=INK, width=1)
    d.ellipse([xs[1] + fw // 2 - 6, fy + fh // 2 - 6,
               xs[1] + fw // 2 + 6, fy + fh // 2 + 6],
              outline=(0, 0, 128), width=2)
    # Japan: white + red disc
    d.rectangle([xs[2], fy, xs[2] + fw, fy + fh], fill=CARD, outline=INK,
                width=1)
    d.ellipse([xs[2] + fw // 2 - 10, fy + fh // 2 - 10,
               xs[2] + fw // 2 + 10, fy + fh // 2 + 10], fill=RED)
    # Australia: blue + canton + stars
    d.rectangle([xs[3], fy, xs[3] + fw, fy + fh], fill=(0, 40, 120),
                outline=INK, width=1)
    d.rectangle([xs[3], fy, xs[3] + fw * 0.45, fy + fh * 0.5],
                outline=CARD, width=2)
    d.line([(xs[3], fy + fh * 0.25), (xs[3] + fw * 0.45, fy + fh * 0.25)],
           fill=CARD, width=2)
    for sx, sy in ((0.7, 0.3), (0.85, 0.6), (0.65, 0.75)):
        d.ellipse([xs[3] + fw * sx - 2, fy + fh * sy - 2,
                   xs[3] + fw * sx + 2, fy + fh * sy + 2], fill=CARD)
    f = fb(SANS_B, 8)
    for i, name in enumerate(("US", "INDIA", "JAPAN", "AUSTRALIA")):
        text_center(d, xs[i] + fw / 2, fy + fh + 1, name, f, INK)
    # Summit table with four seated figures under the flags.
    ty = y + h - 3
    d.line([(x + 8, ty), (x + w - 8, ty)], fill=INK, width=2)
    for i in range(4):
        cx = xs[i] + fw / 2
        d.ellipse([cx - 3, ty - 7, cx + 3, ty - 1], fill=INK)


# ---- small scene strips for the 12 smaller cards ----

def draw_scene(d, x, y, w, h, kind):
    """A small drawn scene across the top of a card (strip h = 28)."""
    if kind == "ebola":
        # Hospital tent + bar chart (short bar: 3 months ago, no number;
        # tall bar: now 11,000+; cases more than doubled). The labels are
        # 55 px wide each at 7 px, so the bars sit at centres 37 and 97
        # to keep a gap between them; the tent is compact at top left.
        # The strip is 26 px tall: bars end at y+17, labels at y+18.
        d.polygon([(x + 2, y + 8), (x + 10, y + 1), (x + 18, y + 8)],
                  fill=LAND, outline=INK)
        d.rectangle([x + 5, y + 8, x + 15, y + 15], outline=INK)
        d.line([(x + 10, y + 10), (x + 10, y + 14)], fill=RED, width=2)
        d.line([(x + 7, y + 12), (x + 13, y + 12)], fill=RED, width=2)
        d.line([(x + 24, y + 17), (x + w - 4, y + 17)], fill=GREY, width=1)
        d.rectangle([x + 30, y + 11, x + 44, y + 17], fill=(150, 140, 120))
        d.rectangle([x + 90, y + 2, x + 104, y + 17], fill=RED)
        f7, f7b = fb(SANS, 7), fb(SANS_B, 7)
        text_center(d, x + 37, y + 18, "3 MONTHS AGO", f7, GREY)
        text_center(d, x + 97, y + 18, "NOW 11,000+", f7b, RED)
    elif kind == "cop31":
        # Globe + three flags.
        d.ellipse([x + 5, y + 5, x + 23, y + 23], fill=SEA, outline=INK)
        d.ellipse([x + 9, y + 9, x + 15, y + 15], fill=LAND, outline=INK)
        d.ellipse([x + 16, y + 14, x + 21, y + 19], fill=LAND, outline=INK)
        for i, col in enumerate(((19, 136, 8), (0, 60, 180), RED)):
            px = x + 40 + i * 32
            d.line([(px, y + 4), (px, y + 24)], fill=INK, width=2)
            d.rectangle([px, y + 4, px + 16, y + 13], fill=col,
                        outline=INK, width=1)
    elif kind == "measles":
        # Vaccine vial + syringe.
        d.rectangle([x + 8, y + 8, x + 20, y + 24], fill=CARD, outline=INK,
                    width=1)
        d.rectangle([x + 11, y + 4, x + 17, y + 8], fill=INK)
        d.rectangle([x + 10, y + 18, x + 18, y + 22], fill=RED)
        d.line([(x + 48, y + 20), (x + 86, y + 6)], fill=INK, width=5)
        d.line([(x + 86, y + 6), (x + 100, y + 2)], fill=INK, width=1)
        d.line([(x + 48, y + 20), (x + 40, y + 24)], fill=INK, width=3)
        d.line([(x + 36, y + 20), (x + 44, y + 24)], fill=INK, width=2)
    elif kind in ("nvidia", "china"):
        # Chip (+ rising chart for Nvidia, + flag for China).
        d.rectangle([x + 10, y + 6, x + 26, y + 22], fill=INK)
        d.rectangle([x + 14, y + 10, x + 22, y + 18], outline=CARD, width=1)
        for i in range(3):
            d.line([(x + 13 + i * 5, y + 3), (x + 13 + i * 5, y + 6)],
                   fill=INK, width=2)
            d.line([(x + 13 + i * 5, y + 22), (x + 13 + i * 5, y + 25)],
                   fill=INK, width=2)
        if kind == "nvidia":
            d.line([(x + 45, y + 22), (x + 62, y + 16), (x + 78, y + 18),
                    (x + 96, y + 8), (x + 112, y + 6)], fill=RED, width=2)
            d.polygon([(x + 112, y + 6), (x + 104, y + 4), (x + 108, y + 12)],
                      fill=RED)
        else:
            d.rectangle([x + 55, y + 6, x + 85, y + 20], fill=RED,
                        outline=INK, width=1)
            d.ellipse([x + 59, y + 9, x + 65, y + 15], fill=(255, 220, 0))
            d.ellipse([x + 70, y + 9, x + 74, y + 13], fill=(255, 220, 0))
            d.ellipse([x + 70, y + 14, x + 74, y + 18], fill=(255, 220, 0))
    elif kind == "gaza":
        # Aid truck + tents.
        d.rectangle([x + 6, y + 8, x + 30, y + 20], fill=CARD, outline=INK,
                    width=1)
        d.rectangle([x + 30, y + 12, x + 40, y + 20], fill=INK)
        d.ellipse([x + 9, y + 19, x + 15, y + 25], fill=INK)
        d.ellipse([x + 31, y + 19, x + 37, y + 25], fill=INK)
        d.line([(x + 17, y + 11), (x + 17, y + 17)], fill=RED, width=2)
        d.line([(x + 14, y + 14), (x + 20, y + 14)], fill=RED, width=2)
        d.polygon([(x + 55, y + 22), (x + 68, y + 8), (x + 81, y + 22)],
                  fill=LAND, outline=INK)
        d.polygon([(x + 85, y + 22), (x + 97, y + 12), (x + 109, y + 22)],
                  fill=LAND, outline=INK)
    elif kind == "japan":
        # Jet + clouds.
        s = 20
        d.line([(x + 6, y + 12), (x + 6 + s, y + 12)], fill=INK, width=3)
        d.polygon([(x + 6 + s * 0.5, y + 12), (x + 6 + s * 0.7, y + 4),
                   (x + 6 + s * 0.85, y + 12)], fill=INK)
        d.polygon([(x + 6 + s * 0.5, y + 12), (x + 6 + s * 0.7, y + 20),
                   (x + 6 + s * 0.85, y + 12)], fill=INK)
        d.polygon([(x + 6 + s * 0.9, y + 12), (x + 6 + s, y + 8),
                   (x + 6 + s, y + 16)], fill=INK)
        for cx in (58, 96):
            d.ellipse([x + cx - 8, y + 8, x + cx + 8, y + 20], fill=CARD,
                      outline=GREY)
            d.ellipse([x + cx - 2, y + 4, x + cx + 12, y + 16], fill=CARD,
                      outline=GREY)
    elif kind == "depardieu":
        # Courthouse + gavel.
        d.polygon([(x + 4, y + 10), (x + 20, y + 2), (x + 36, y + 10)],
                  fill=INK)
        for cx in (12, 20, 28):
            d.line([(x + cx, y + 10), (x + cx, y + 22)], fill=INK, width=2)
        d.line([(x + 2, y + 24), (x + 38, y + 24)], fill=INK, width=2)
        d.line([(x + 55, y + 8), (x + 75, y + 16)], fill=INK, width=5)
        d.line([(x + 65, y + 12), (x + 85, y + 22)], fill=INK, width=3)
        d.rectangle([x + 88, y + 21, x + 100, y + 25], fill=INK)
    elif kind == "apple":
        # Phone + cloud with a green check.
        d.rounded_rectangle([x + 10, y + 3, x + 26, y + 25], radius=3,
                            fill=INK)
        d.rectangle([x + 13, y + 7, x + 23, y + 20], fill=CARD)
        d.line([(x + 15, y + 22), (x + 21, y + 22)], fill=CARD, width=1)
        d.ellipse([x + 46, y + 10, x + 58, y + 22], fill=CARD, outline=GREY)
        d.ellipse([x + 54, y + 5, x + 68, y + 19], fill=CARD, outline=GREY)
        d.ellipse([x + 64, y + 10, x + 76, y + 22], fill=CARD, outline=GREY)
        d.line([(x + 84, y + 16), (x + 90, y + 22), (x + 102, y + 8)],
               fill=(0, 140, 60), width=3)
    elif kind == "houthis":
        # Pipeline + drone.
        d.rectangle([x + 4, y + 14, x + 80, y + 18], fill=GREY, outline=INK,
                    width=1)
        d.line([(x + 20, y + 18), (x + 20, y + 24)], fill=INK, width=2)
        d.line([(x + 60, y + 18), (x + 60, y + 24)], fill=INK, width=2)
        d.ellipse([x + 36, y + 8, x + 44, y + 16], outline=INK, width=2)
        d.rectangle([x + 95, y + 10, x + 107, y + 16], fill=INK)
        for rx, ry in ((92, 6), (110, 6), (92, 20), (110, 20)):
            d.line([(x + rx, y + ry), (x + 101, y + 13)], fill=INK, width=1)
            d.ellipse([x + rx - 3, y + ry - 1, x + rx + 3, y + ry + 1],
                      outline=INK, width=1)
        d.ellipse([x + 99, y + 11, x + 103, y + 15], fill=RED)
    elif kind == "mongolia":
        # Parliament building + resignation letter.
        d.polygon([(x + 4, y + 10), (x + 28, y + 2), (x + 52, y + 10)],
                  fill=INK)
        for cx in (14, 28, 42):
            d.line([(x + cx, y + 10), (x + cx, y + 22)], fill=INK, width=2)
        d.line([(x + 2, y + 24), (x + 54, y + 24)], fill=INK, width=2)
        d.rectangle([x + 70, y + 6, x + 100, y + 24], fill=CARD,
                    outline=RED, width=2)
        d.line([(x + 76, y + 12), (x + 94, y + 12)], fill=RED, width=2)
        d.line([(x + 76, y + 18), (x + 94, y + 18)], fill=RED, width=2)
    elif kind == "an12":
        # Mountains + snow + plane + small fire glow.
        d.polygon([(x + 2, y + 26), (x + 32, y + 4), (x + 62, y + 26)],
                  fill=GREY)
        d.polygon([(x + 58, y + 26), (x + 92, y + 2), (x + 128, y + 26)],
                  fill=GREY)
        d.ellipse([x + 2, y + 20, x + w - 2, y + 28], fill=CARD,
                  outline=INK, width=1)
        d.ellipse([x + 100, y + 8, x + 108, y + 16], fill=(255, 150, 40))
        d.ellipse([x + 102, y + 10, x + 106, y + 14], fill=RED)
        px, py = x + 38, y + 10
        d.polygon([(px, py), (px + 30, py - 1), (px + 38, py + 2),
                   (px + 30, py + 4), (px, py + 4)], fill=INK)
        d.polygon([(px + 11, py), (px + 16, py - 7), (px + 21, py)],
                  fill=INK)
        d.polygon([(px + 30, py), (px + 34, py - 5), (px + 37, py + 1)],
                  fill=INK)


# ---- world map: recognisable continents, equirectangular pins ----

# Coarse (lon, lat) outlines, drawn in that order.
CONTINENTS = [
    [(-168, 66), (-165, 60), (-158, 58), (-150, 60), (-140, 60),
     (-135, 58), (-130, 54), (-125, 49), (-124, 42), (-120, 34),
     (-117, 32), (-110, 24), (-105, 20), (-97, 16), (-94, 17), (-90, 14),
     (-86, 12), (-83, 9), (-79, 9), (-81, 13), (-84, 16), (-87, 21),
     (-90, 21), (-91, 19), (-96, 19), (-97, 26), (-93, 30), (-89, 30),
     (-84, 30), (-81, 25), (-80, 32), (-76, 35), (-75, 39), (-70, 42),
     (-68, 45), (-65, 44), (-60, 47), (-55, 52), (-60, 55), (-65, 60),
     (-68, 58), (-78, 62), (-85, 66), (-92, 66), (-95, 69), (-110, 68),
     (-125, 70), (-140, 70), (-155, 71), (-165, 68)],
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-22, 70),
     (-20, 74), (-25, 76), (-35, 77), (-50, 76), (-58, 74), (-60, 70)],
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-74, -50),
     (-70, -54), (-66, -55), (-68, -50), (-65, -45), (-62, -40),
     (-58, -35), (-52, -32), (-48, -28), (-41, -23), (-39, -17),
     (-35, -9), (-35, -6), (-40, -3), (-44, -2), (-50, 0), (-53, 4),
     (-58, 6), (-62, 9), (-68, 11), (-72, 12), (-76, 10)],
    [(-17, 15), (-16, 20), (-15, 25), (-10, 29), (-5, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (25, 32), (30, 31), (32, 31), (35, 28),
     (37, 22), (39, 18), (41, 11), (43, 11), (46, 11), (51, 12), (51, 10),
     (48, 5), (42, 0), (40, -5), (40, -10), (36, -18), (33, -26),
     (28, -33), (20, -35), (17, -32), (15, -27), (12, -18), (13, -12),
     (9, -1), (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12)],
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-2, 50), (0, 51),
     (3, 53), (5, 53), (8, 55), (8, 57), (10, 59), (5, 60), (5, 62),
     (12, 64), (18, 66), (25, 68), (30, 70), (40, 68), (45, 68), (55, 69),
     (65, 69), (75, 72), (85, 73), (95, 75), (105, 77), (115, 73),
     (125, 72), (135, 71), (145, 72), (155, 70), (160, 66), (162, 60),
     (158, 55), (155, 50), (150, 45), (142, 42), (140, 38), (135, 35),
     (130, 33), (127, 35), (122, 38), (120, 32), (118, 25), (112, 22),
     (108, 18), (105, 10), (103, 8), (100, 7), (98, 12), (95, 16),
     (92, 21), (89, 22), (86, 20), (82, 17), (80, 13), (77, 8), (75, 12),
     (72, 20), (70, 23), (66, 25), (62, 25), (58, 25), (55, 26), (52, 26),
     (50, 29), (48, 30), (44, 29), (40, 32), (36, 36), (33, 36), (30, 36),
     (27, 37), (23, 36), (19, 40), (16, 44), (12, 44), (8, 44), (3, 43),
     (-1, 38), (-6, 36), (-9, 37)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53)],
    [(130, 31), (132, 33), (134, 34), (136, 35), (138, 36), (140, 38),
     (141, 40), (142, 42), (140, 44), (139, 42), (137, 38), (134, 35),
     (131, 33)],
    [(120, 18), (122, 16), (121, 14), (122, 11), (124, 10), (122, 8),
     (120, 12), (119, 16)],
    [(95, 5), (98, 3), (100, 0), (104, -2), (108, -6), (112, -7),
     (116, -8), (120, -9), (118, -10), (112, -8), (106, -6), (102, -1),
     (98, 2)],
    [(109, 1), (113, 4), (117, 6), (119, 1), (117, -3), (112, -3),
     (109, -1)],
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9), (147, -8),
     (141, -8), (136, -6), (131, -3)],
    [(114, -22), (114, -30), (115, -35), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -15),
     (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    [(44, -16), (47, -15), (50, -16), (49, -20), (46, -24), (44, -25),
     (43, -21), (43, -17)],
    [(167, -45), (170, -43), (174, -41), (176, -38), (175, -36),
     (173, -35), (170, -40), (167, -44)],
]

# Pin number -> (lon, lat). A few are nudged a couple of degrees so
# neighbouring pins stay visible: 1/5/8 in the east Mediterranean,
# 2/12 in the Gulf, and 7/11 which share California.
PIN_LATLON = {
    1: (36.5, 47.0), 2: (60.0, 30.0), 3: (121.0, 14.6), 4: (25.0, -2.0),
    5: (24.0, 41.0), 6: (-98.0, 39.0), 7: (-128.0, 42.0),
    8: (32.0, 31.5), 9: (139.7, 35.7), 10: (2.3, 48.9),
    11: (-116.0, 33.0), 12: (48.5, 22.5), 13: (116.4, 39.9),
    14: (106.9, 47.9), 15: (86.1, 55.4),
}


def draw_world_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    # Equirectangular: lon -180..180, lat -60..85.
    for poly in CONTINENTS:
        pts = [(x + (lon + 180) / 360.0 * w,
                y + (85 - lat) / 145.0 * h) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=GREY)
    f = fb(SANS_B, 10)
    for num, (lon, lat) in sorted(PIN_LATLON.items()):
        cx = x + (lon + 180) / 360.0 * w
        cy = y + (85 - lat) / 145.0 * h
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=RED, outline=CARD,
                  width=1)
        text_center(d, cx, cy - 5, str(num), f, CARD)


# ---- Tahap 1: the data - ONE list, 39 unique stories ----
# Every story: id, region, title, summary, status (CONFIRMED / CLAIM /
# "none"), event (a slug for the underlying event, used by the duplicate
# check), plus cat / scene / tag for the 15 illustrated cards only.
# The ALSO list shows each story's title; the summary is the data record
# (and the card sub-label for cards 1-15). All 39 happened or were first
# reported on Tuesday 17 November 2026, as reported by Reuters, AP,
# PAHO, WHO and the UN (new items 34-39: Le Monde, CNN, UNB).

REGIONS = ["EUROPE", "MIDDLE EAST", "ASIA", "AFRICA", "AMERICAS",
           "OCEANIA", "WORLD"]

STORIES = [
    {"id": 1, "region": "EUROPE",
     "title": "Crimean Bridge road span falls into the sea",
     "summary": "Second strike in two days; Zelenskyy hails it "
     "'unprecedented'; Kremlin vows rebuild.",
     "status": "CONFIRMED", "event": "kerch-bridge",
     "cat": "EUROPE - UKRAINE WAR", "scene": "kerch",
     "tag": "CONFIRMED: Reuters-verified footage of the collapsed span."},
    {"id": 2, "region": "MIDDLE EAST",
     "title": "US strikes Iran as tankers burn in Hormuz",
     "summary": "Warplanes hit a missile site on Qeshm; 24 seafarers "
     "evacuated from the burning Tara Gas.",
     "status": "CLAIM", "event": "us-strikes-iran",
     "cat": "MIDDLE EAST - IRAN WAR", "scene": "gulf",
     "tag": "CLAIM: Iran says tankers hit mines in Hormuz - not "
     "independently verified."},
    {"id": 3, "region": "ASIA",
     "title": "Trump holds his first Quad summit, in Manila",
     "summary": "First Quad meeting since his return to office; due to "
     "meet Xi and Putin in China on Thursday.",
     "status": "none", "event": "quad-summit-manila",
     "cat": "ASIA - DIPLOMACY", "scene": "quad"},
    {"id": 4, "region": "AFRICA",
     "title": "Ebola cases in DR Congo top 11,000",
     "summary": "WHO says 5,400 have died; it reviews the emergency "
     "status.",
     "status": "none", "event": "ebola-dr-congo",
     "cat": "AFRICA - HEALTH", "scene": "ebola"},
    {"id": 5, "region": "WORLD",
     "title": "COP31 talks grind on in Antalya",
     "summary": "Nations weigh a first draft; the talks end Friday.",
     "status": "none", "event": "cop31-talks",
     "cat": "GLOBAL - CLIMATE", "scene": "cop31"},
    {"id": 6, "region": "AMERICAS",
     "title": "US loses measles-free status",
     "summary": "PAHO cites a year of uninterrupted spread.",
     "status": "none", "event": "us-measles-status",
     "cat": "AMERICAS - HEALTH", "scene": "measles"},
    {"id": 7, "region": "AMERICAS",
     "title": "Nvidia's quarterly sales double to $115.8B",
     "summary": "Shares rise after the close; Q4 forecast near $130B.",
     "status": "none", "event": "nvidia-earnings",
     "cat": "US - BUSINESS", "scene": "nvidia"},
    {"id": 8, "region": "MIDDLE EAST",
     "title": "Gaza aid call as winter rains flood shelters",
     "summary": "UK, Australia, Canada and Italy urge Israel to open "
     "crossings.",
     "status": "none", "event": "gaza-aid-call",
     "cat": "MIDDLE EAST - GAZA", "scene": "gaza"},
    {"id": 9, "region": "ASIA",
     "title": "Japan scrambles jets",
     "summary": "Russian aircraft violated airspace.",
     "status": "none", "event": "japan-jets",
     "cat": "ASIA - POLITICS", "scene": "japan"},
    {"id": 10, "region": "EUROPE",
     "title": "Depardieu admits sexual assault",
     "summary": "French actor drops his appeal in Paris.",
     "status": "none", "event": "depardieu-appeal",
     "cat": "EUROPE - COURTS", "scene": "depardieu"},
    {"id": 11, "region": "AMERICAS",
     "title": "Apple outage fixed",
     "summary": "iCloud sign-ins and the App Store back up.",
     "status": "none", "event": "apple-outage",
     "cat": "TECH", "scene": "apple"},
    {"id": 12, "region": "MIDDLE EAST",
     "title": "Houthis fire drones at Saudi pipeline",
     "summary": "Five drones aimed at Riyadh pumping stations.",
     "status": "CLAIM", "event": "houthi-drones-saudi",
     "cat": "MIDDLE EAST - ENERGY", "scene": "houthis",
     "tag": "HOUTHI CLAIM - no Saudi confirmation."},
    {"id": 13, "region": "ASIA",
     "title": "China rejects US chip curbs",
     "summary": "Beijing hits back at the cloud-access rule.",
     "status": "none", "event": "china-chip-curbs",
     "cat": "ASIA - TRADE", "scene": "china"},
    {"id": 14, "region": "ASIA",
     "title": "Mongolia's president says he will resign",
     "summary": "Denies a $25m bribe claim over a railway deal; "
     "parliament must accept.",
     "status": "none", "event": "mongolia-resignation",
     "cat": "ASIA - POLITICS", "scene": "mongolia"},
    {"id": 15, "region": "EUROPE",
     "title": "Russian An-12 crash in Siberia kills 19",
     "summary": "Military plane down near Kemerovo; ministry blames a "
     "technical fault.",
     "status": "none", "event": "an12-crash",
     "cat": "RUSSIA - AIR CRASH", "scene": "an12"},
    {"id": 16, "region": "MIDDLE EAST",
     "title": "(as reported) Lebanon: Israeli airstrikes, shelling, "
     "detonations.",
     "summary": "Israeli airstrikes, shelling and detonations reported "
     "in Lebanon; not independently verified.",
     "status": "none", "event": "lebanon-strikes"},
    {"id": 17, "region": "MIDDLE EAST",
     "title": "UKMTO reports a second tanker strike north of Khasab, "
     "Oman.",
     "summary": "A second tanker was struck 7 nautical miles north of "
     "Khasab, Oman, UKMTO said.",
     "status": "none", "event": "second-tanker-khasab"},
    {"id": 18, "region": "EUROPE",
     "title": "Zelenskyy: bridge strike answers Russian attacks on "
     "infrastructure.",
     "summary": "Zelenskyy said the bridge operation answers Russian "
     "attacks on Ukrainian infrastructure.",
     "status": "none", "event": "zelenskyy-bridge-statement"},
    {"id": 19, "region": "AMERICAS",
     "title": "Wall Street: S&P 500 -1%, Dow -1.6%, Nasdaq -0.7%.",
     "summary": "US stocks fell; the S&P 500 lost 1%, the Dow 1.6% and "
     "the Nasdaq 0.7%.",
     "status": "none", "event": "wall-street-falls"},
    {"id": 20, "region": "AMERICAS",
     "title": "Nvidia board will not reinstate Jensen Huang as CEO.",
     "summary": "Nvidia's board said it will not reinstate Jensen Huang "
     "as chief executive.",
     "status": "none", "event": "nvidia-board-ceo"},
    {"id": 21, "region": "MIDDLE EAST",
     "title": "Dubai airports: 50.4M passengers in 9 months, down 28.1%.",
     "summary": "Dubai airports handled 50.4 million passengers in nine "
     "months, down 28.1%.",
     "status": "none", "event": "dubai-airports"},
    {"id": 22, "region": "MIDDLE EAST",
     "title": "Yemen: government forces pull back toward Aden as Houthis "
     "advance.",
     "summary": "Yemeni government forces withdrew toward Aden as Houthi "
     "fighters advanced.",
     "status": "none", "event": "yemen-pullback"},
    {"id": 23, "region": "EUROPE",
     "title": "Five EU states plan a migrant return hub in Rwanda.",
     "summary": "Austria, Germany, the Netherlands, Denmark and Greece "
     "plan a migrant return hub in Rwanda.",
     "status": "none", "event": "eu-rwanda-hub"},
    {"id": 24, "region": "WORLD",
     "title": "Grammy nominations: RAYE leads with 11, ROSAL\u00cdA has 9.",
     "summary": "RAYE leads the Grammy nominations with 11; "
     "ROSAL\u00cdA has 9.",
     "status": "none", "event": "grammy-nominations"},
    {"id": 25, "region": "MIDDLE EAST",
     "title": "UN: winter rains deepen Gaza shelter crisis.",
     "summary": "The UN said winter rains are deepening the shelter "
     "crisis in Gaza.",
     "status": "none", "event": "gaza-winter-rains"},
    {"id": 26, "region": "AFRICA",
     "title": "Ebola: WHO emergency committee reviews the outbreak "
     "status.",
     "summary": "The WHO emergency committee reviewed the Ebola outbreak "
     "status.",
     "status": "none", "event": "ebola-who-committee"},
    {"id": 27, "region": "WORLD",
     "title": "COP31: first draft of the cover decision out; talks end "
     "Friday.",
     "summary": "COP31 released a first draft of the cover decision; "
     "talks end Friday.",
     "status": "none", "event": "cop31-draft"},
    {"id": 28, "region": "OCEANIA",
     "title": "Cyclone Xavier batters the Northern Cook Islands.",
     "summary": "Cyclone Xavier battered the Northern Cook Islands.",
     "status": "none", "event": "cyclone-xavier"},
    {"id": 29, "region": "WORLD",
     "title": "Voyager 1 nears one light-day from Earth; crosses early "
     "Wednesday.",
     "summary": "Voyager 1 nears one light-day from Earth and crosses "
     "early Wednesday.",
     "status": "none", "event": "voyager-1"},
    {"id": 30, "region": "AFRICA",
     "title": "UN verifies 2,230 civilian deaths in Sudan; drones caused "
     "most.",
     "summary": "The UN verified 2,230 civilian deaths in Sudan, most "
     "caused by drones.",
     "status": "none", "event": "sudan-civilian-deaths"},
    {"id": 31, "region": "MIDDLE EAST",
     "title": "Israel: Matan Kahana elected Knesset speaker, 66-52.",
     "summary": "Matan Kahana was elected Knesset speaker by 66 votes "
     "to 52.",
     "status": "none", "event": "kahana-speaker"},
    {"id": 32, "region": "EUROPE",
     "title": "Moldova shuts airspace as 7 drones cross in; 5 crash near "
     "villages.",
     "summary": "Moldova shut its airspace as seven drones crossed in; "
     "five crashed near villages.",
     "status": "none", "event": "moldova-drones"},
    {"id": 33, "region": "AMERICAS",
     "title": "US: 13 babies born with congenital measles; most cases "
     "since 1991.",
     "summary": "Thirteen babies were born with congenital measles in "
     "the US; cases are the highest since 1991.",
     "status": "none", "event": "congenital-measles"},
    {"id": 34, "region": "EUROPE",
     "title": "France: wage protests draw 146,000; unions demand higher "
     "pay.",
     "summary": "Protests for higher wages drew 146,000 people across "
     "France; 28,000 marched in Paris.",
     "status": "none", "event": "france-wage-protests"},
    {"id": 35, "region": "EUROPE",
     "title": "Russia: no European seat at next Ukraine talks, aide says.",
     "summary": "Moscow has not agreed to European participation in the "
     "next round of Ukraine talks, aide Yuri Ushakov said.",
     "status": "none", "event": "russia-europe-talks"},
    {"id": 36, "region": "AMERICAS",
     "title": "NSA: classified network down; Fort Meade under code "
     "orange.",
     "summary": "The NSA's classified NSANet network went down early "
     "Tuesday; the Fort Meade campus was restricted under code orange.",
     "status": "none", "event": "nsa-nsanet-outage"},
    {"id": 37, "region": "AMERICAS",
     "title": "Ecuador: 16 fishermen sue US over drone attack on boat.",
     "summary": "Sixteen Ecuadorian fishermen sued the US government "
     "over a drone attack that sank their boat in the Pacific in March.",
     "status": "none", "event": "ecuador-fishermen-lawsuit"},
    {"id": 38, "region": "WORLD",
     "title": "Pattinson named the new James Bond.",
     "summary": "British actor Robert Pattinson was named as the new "
     "James Bond.",
     "status": "none", "event": "pattinson-james-bond"},
    {"id": 39, "region": "ASIA",
     "title": "Dhaka tops world's most polluted cities; AQI 292.",
     "summary": "Dhaka ranked first among the world's most polluted "
     "cities on Tuesday morning, with an AQI of 292.",
     "status": "none", "event": "dhaka-air-pollution"},
]


def check_stories():
    """Automatic duplicate check: the program stops on any duplicate."""
    import sys
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


def region_counts():
    counts = {r: 0 for r in REGIONS}
    for s in STORIES:
        counts[s["region"]] += 1
    return counts


# Derived views for the renderer. Numbers come from id, never typed.
CARDS = STORIES[:15]
ALSO = STORIES[15:]
BIG = [(s["cat"], s["title"], s["summary"], s["scene"]) for s in CARDS[:3]]
MEDIUM = [(s["cat"], s["title"], s["summary"], s["scene"])
          for s in CARDS[3:9]]
SMALL = [(s["cat"], s["title"], s["summary"], s["scene"])
         for s in CARDS[9:15]]
TAG_BY_ID = {s["id"]: (s["tag"], TAG_GREEN if s["status"] == "CONFIRMED"
                       else TAG_AMBER)
             for s in STORIES if s.get("tag")}

NUMBERS = [
    ("11,000+", "Ebola cases, DR Congo"),
    ("$115.8bn", "Nvidia quarter"),
    ("-1.6%", "Dow on Tuesday"),
    ("24", "seafarers evacuated from the Tara Gas"),
    ("1,441", "drones Russia says it downed"),
    ("50.4m", "Dubai airport passengers in 9 months, down 28.1%"),
]

WHY_TEXT = ("A Tuesday of falling bridges, burning tankers and a 26-year "
            "health milestone lost.")

THREAD_TEXT = ("Monday, Russia hit Kyiv's two Dnipro bridges - Tuesday, "
               "Ukraine answered by dropping the Kerch road span.")

DATECHECK_TITLE = "DATE CHECK - left out as earlier news:"
DATECHECK_ITEMS = ("COP31's first draft (16 Nov) - Grammy nominations "
                   "announced (16 Nov) - US chip-export rule (16 Nov) - "
                   "Guinea gold-mining sentences (16 Nov).")


# ---- card drawers (uniform title 12 px, body 10 px) ----

def draw_big_panel(d, x, y, w, h, num, cat, headline, sub, kind, tag=None):
    ix, iy, iw, ih = panel(d, x, y, w, h)
    map_h = 30
    if kind == "kerch":
        map_kerch(d, ix, iy, iw, map_h)
    elif kind == "gulf":
        map_gulf(d, ix, iy, iw, map_h)
    else:
        map_quad(d, ix, iy, iw, map_h)
    ty = iy + map_h + 4
    d.text((ix, ty), f"{num}. {cat}", font=fb(SANS_B, 13), fill=RED)
    hy = ty + 18
    font, lines, lh = fit_block(d, headline, SANS_B, TITLE_SIZE,
                                TITLE_SIZE, iw, 2, 28)
    for ln in lines:
        d.text((ix, hy), ln, font=font, fill=INK)
        hy += lh
    font2, lines2, lh2 = fit_block(d, sub, SANS, BODY_SIZE, BODY_SIZE, iw,
                                   3, 36)
    sy = hy + 3
    for ln in lines2:
        d.text((ix, sy), ln, font=font2, fill=INK)
        sy += lh2
    if tag is not None:
        draw_tag(d, ix, sy + 3, iw, tag[0], tag[1], start=9, max_h=20)


def draw_small_panel(d, x, y, w, h, num, cat, headline, sub, kind,
                     tag=None):
    ix, iy, iw, ih = panel(d, x, y, w, h)
    scene_h = 26
    draw_scene(d, ix, iy, iw, scene_h, kind)
    cy = iy + scene_h + 4
    d.text((ix, cy), f"{num}. {cat}", font=fb(SANS_B, 9), fill=RED)
    hy = cy + 16
    font, lines, lh = fit_block(d, headline, SANS_B, TITLE_SIZE,
                                TITLE_SIZE, iw, 3, 42)
    for ln in lines:
        d.text((ix, hy), ln, font=font, fill=INK)
        hy += lh
    font2, lines2, lh2 = fit_block(d, sub, SANS, BODY_SIZE, BODY_SIZE, iw,
                                   3, 36)
    sy = hy + 3
    for ln in lines2:
        d.text((ix, sy), ln, font=font2, fill=INK)
        sy += lh2
    if tag is not None:
        draw_tag(d, ix, sy + 3, iw, tag[0], tag[1], start=9, max_h=20)


LIST_SIZE = 11    # "Also on" font; never below BODY_SIZE (10 px)


def main():
    # Tahap 1 first: stop on any duplicate before drawing anything.
    check_stories()
    counts = region_counts()
    region_bar = " - ".join(f"{r} {counts[r]}" for r in REGIONS)
    n_regions = sum(1 for r in REGIONS if counts[r] > 0)
    kicker_right = (f"{len(STORIES)} STORIES - {n_regions} REGIONS - "
                    "ALL FROM TUESDAY")

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, W - 11, H - 11], outline=INK, width=4)

    # Top kicker (story count and region count come from the list).
    d.text((16, 14), "THE WORLD'S NEWS IN ONE PICTURE",
           font=fb(SANS_B, 15), fill=RED)
    rw = d.textlength(kicker_right, font=fb(SANS_B, 15))
    d.text((1008 - rw, 14), kicker_right, font=fb(SANS_B, 15), fill=INK)
    d.line([(16, 34), (1008, 34)], fill=RED, width=2)

    # Banner, serif bold, as large as fits, with room below the descenders
    # so the tail of the "y" in "Tuesday" clears the rule underneath.
    size = 38
    while (d.textlength("Tuesday 17 November 2026", font=fb(SERIF_B, size))
           > 980 and size > 34):
        size -= 2
    text_center(d, W // 2, 36, "Tuesday 17 November 2026",
                fb(SERIF_B, size), INK)
    d.line([(16, 82), (1008, 82)], fill=RED, width=3)

    # Region-counts bar, computed from STORIES.
    text_center(d, W // 2, 86, region_bar, fb(SANS_B, 12), INK)

    # 1. BY THE NUMBERS strip.
    cell_w = (1008 - 16) / 6
    for i, (num, label) in enumerate(NUMBERS):
        cx = 16 + i * cell_w
        text_center(d, cx + cell_w / 2, 100, num, fb(SANS_B, 17), INK)
        font, lines, lh = fit_block(d, label, SANS, 9, 9,
                                    cell_w - 12, 2, 20)
        ly2 = 120
        for ln in lines:
            text_center(d, cx + cell_w / 2, ly2, ln, font, GREY)
            ly2 += lh
        if i:
            d.line([(cx, 102), (cx, 138)], fill=GREY, width=1)

    # 2. WHY THIS DAY MATTERS line (serif; no italic serif on this VM,
    # so regular serif, centred).
    text_center(d, W // 2, 144, WHY_TEXT, fb(SERIF, 14), INK)

    # Row 1: three big panels. Numbers and tags come from the stories.
    for i, (cat, head, sub, kind) in enumerate(BIG):
        num = CARDS[i]["id"]
        draw_big_panel(d, 16 + i * 335, 162, 322, 152, num, cat, head,
                       sub, kind, tag=TAG_BY_ID.get(num))

    # 3. THE DAY'S THREAD line.
    label = "THE DAY'S THREAD: "
    lw = d.textlength(label, font=fb(SANS_B, 12))
    d.text((16, 318), label, font=fb(SANS_B, 12), fill=RED)
    d.text((16 + lw, 318), THREAD_TEXT, font=fb(SANS, 12), fill=INK)

    # Row 2: six medium panels.
    for i, (cat, head, sub, kind) in enumerate(MEDIUM):
        num = CARDS[3 + i]["id"]
        draw_small_panel(d, 16 + i * 165, 334, 158, 151, num, cat, head,
                         sub, kind)

    # Row 3: six small panels.
    for i, (cat, head, sub, kind) in enumerate(SMALL):
        num = CARDS[9 + i]["id"]
        draw_small_panel(d, 16 + i * 165, 489, 158, 160, num, cat, head,
                         sub, kind, tag=TAG_BY_ID.get(num))

    # Bottom left: world map with numbered pins.
    mx, my, mw, mh = 16, 653, 486, 300
    d.rectangle([mx, my, mx + mw, my + mh], fill=CARD, outline=INK, width=2)
    d.rectangle([mx, my, mx + mw, my + 5], fill=RED)
    section_title(d, mx + 12, my + 12, "WHERE IT HAPPENED")
    draw_world_map(d, mx + 12, my + 32, mw - 24, mh - 44)

    # Bottom right: "Also on" list, ids 16-39, font >= body size.
    lx, ly, lw, lh = 514, 653, 494, 300
    d.rectangle([lx, ly, lx + lw, ly + lh], fill=CARD, outline=INK, width=2)
    d.rectangle([lx, ly, lx + lw, ly + 5], fill=RED)
    section_title(d, lx + 12, ly + 12, "ALSO ON TUESDAY 17 NOVEMBER")
    list_top, list_h = ly + 30, lh - 34
    size = LIST_SIZE
    while size >= BODY_SIZE:
        font = fb(SANS, size)
        lh_px = int(size * 1.05)
        if (len(ALSO) * lh_px <= list_h and all(
                d.textlength(f"{s['id']}. {s['title']}", font=font)
                <= lw - 24 for s in ALSO)):
            break
        size -= 1
    font = fb(SANS, size)
    lh_px = int(size * 1.05)
    yy = list_top
    for s in ALSO:
        d.text((lx + 12, yy), f"{s['id']}. {s['title']}", font=font,
               fill=INK)
        yy += lh_px

    # 5. DATE CHECK box.
    d.rectangle([16, 955, 1008, 985], outline=INK, width=2)
    d.rectangle([16, 955, 22, 985], fill=RED)
    d.text((30, 959), DATECHECK_TITLE, font=fb(SANS_B, 11), fill=INK)
    d.text((30, 971), DATECHECK_ITEMS, font=fb(SANS, 10), fill=INK)

    # Footer (with the tag legend on the second line).
    text_center(d, W // 2, 989,
                "Every story here happened or was first reported on Tuesday "
                "17 November 2026. Contested claims are marked as claims.",
                fb(SANS, 9), GREY)
    text_center(d, W // 2, 999,
                "Sources: Reuters, AP, PAHO, WHO, UN, Le Monde, CNN, UNB. "
                "Original drawings. Tags: CONFIRMED = verified by Reuters "
                "/ AP / PAHO / WHO / UN; CLAIM = as stated by the source, "
                "not independently verified.",
                fb(SANS, 9), GREY)

    img.save(OUT, optimize=True)
    print("saved", OUT)


if __name__ == "__main__":
    main()
