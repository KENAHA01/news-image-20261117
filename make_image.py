"""Draw the dense v3 front page for news-image-20261117 (1024x1024 PNG).

v3 = v2 (13 numbered stories, world map with pins, 18 one-liners) plus a
verification layer: a BY THE NUMBERS strip, a WHY THIS DAY MATTERS line,
a THE DAY'S THREAD line, CONFIRMED / CLAIM tags on contested items, and a
DATE CHECK box for items that belong to 16 November, not this day.

Newspaper style: off-white paper, ink text, dark-red accent. All stories
from Tuesday 17 November 2026 as reported by Reuters, AP, PAHO, WHO and
the UN. Every map, flag and icon is drawn with PIL shapes; no network, no
external images. Text is never clipped: every block shrinks its font
until it fits.
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


def fb(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
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


def text_center(draw, cx, y, text, font, fill):
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def panel(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=2)
    draw.rectangle([x, y, x + w, y + 5], fill=RED)
    return x + 12, y + 12, w - 24, h - 24


def section_title(draw, x, y, text, size=16):
    draw.text((x, y), text, font=fb(SANS_B, size), fill=INK)


# ---- small icons (drawn in a square box of side s at x, y) ----

def icon_virus(d, x, y, s):
    import math
    cx, cy, r = x + s / 2, y + s / 2, s * 0.24
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        d.line([(cx + r * math.cos(a), cy + r * math.sin(a)),
                (cx + r * 1.7 * math.cos(a), cy + r * 1.7 * math.sin(a))],
               fill=INK, width=2)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)


def icon_globe(d, x, y, s):
    d.ellipse([x + 2, y + 2, x + s - 2, y + s - 2], outline=INK, width=2)
    d.ellipse([x + s * 0.2, y + s * 0.2, x + s * 0.8, y + s * 0.8],
              outline=INK, width=1)
    d.line([(x + 2, y + s / 2), (x + s - 2, y + s / 2)], fill=INK, width=1)
    d.polygon([(x + s * 0.55, y + s * 0.15), (x + s * 0.85, y + s * 0.3),
               (x + s * 0.7, y + s * 0.55), (x + s * 0.5, y + s * 0.4)],
              fill=(46, 125, 50))


def icon_cross(d, x, y, s):
    d.ellipse([x + 2, y + 2, x + s - 2, y + s - 2], outline=INK, width=2)
    c = s * 0.16
    d.rectangle([x + s / 2 - c / 2, y + s * 0.22,
                 x + s / 2 + c / 2, y + s * 0.78], fill=RED)
    d.rectangle([x + s * 0.22, y + s / 2 - c / 2,
                 x + s * 0.78, y + s / 2 + c / 2], fill=RED)


def icon_chip(d, x, y, s):
    d.rectangle([x + s * 0.2, y + s * 0.2, x + s * 0.8, y + s * 0.8],
                fill=INK)
    d.rectangle([x + s * 0.38, y + s * 0.38, x + s * 0.62, y + s * 0.62],
                fill=RED)
    for i in range(3):
        t = s * (0.32 + i * 0.18)
        d.line([(x + t, y + s * 0.08), (x + t, y + s * 0.2)], fill=INK,
               width=2)
        d.line([(x + t, y + s * 0.8), (x + t, y + s * 0.92)], fill=INK,
               width=2)


def icon_aid(d, x, y, s):
    d.rectangle([x + s * 0.12, y + s * 0.22, x + s * 0.88, y + s * 0.9],
                outline=INK, width=2)
    d.line([(x + s * 0.12, y + s * 0.36), (x + s * 0.88, y + s * 0.36)],
           fill=INK, width=2)
    d.rectangle([x + s * 0.44, y + s * 0.48, x + s * 0.56, y + s * 0.78],
                fill=RED)
    d.rectangle([x + s * 0.36, y + s * 0.56, x + s * 0.64, y + s * 0.68],
                fill=RED)


def icon_jet(d, x, y, s):
    d.polygon([(x + s * 0.15, y + s * 0.5), (x + s * 0.4, y + s * 0.3),
               (x + s * 0.9, y + s * 0.42), (x + s * 0.95, y + s * 0.5),
               (x + s * 0.9, y + s * 0.58), (x + s * 0.4, y + s * 0.7)],
              fill=RED)
    d.polygon([(x + s * 0.35, y + s * 0.32), (x + s * 0.48, y + s * 0.08),
               (x + s * 0.55, y + s * 0.32)], fill=RED)
    d.polygon([(x + s * 0.45, y + s * 0.62), (x + s * 0.6, y + s * 0.92),
               (x + s * 0.66, y + s * 0.62)], fill=RED)


def icon_scales(d, x, y, s):
    d.line([(x + s / 2, y + s * 0.1), (x + s / 2, y + s * 0.9)], fill=INK,
           width=2)
    d.line([(x + s * 0.15, y + s * 0.25), (x + s * 0.85, y + s * 0.25)],
           fill=INK, width=2)
    for cx in (x + s * 0.15, x + s * 0.85):
        d.line([(cx, y + s * 0.25), (cx, y + s * 0.45)], fill=INK, width=2)
        d.polygon([(cx - s * 0.13, y + s * 0.45), (cx + s * 0.13, y + s * 0.45),
                   (cx, y + s * 0.62)], fill=RED)
    d.line([(x + s * 0.3, y + s * 0.9), (x + s * 0.7, y + s * 0.9)], fill=INK,
           width=2)


def icon_cloud(d, x, y, s):
    d.ellipse([x + s * 0.1, y + s * 0.3, x + s * 0.45, y + s * 0.6],
              fill=INK)
    d.ellipse([x + s * 0.35, y + s * 0.15, x + s * 0.75, y + s * 0.6],
              fill=INK)
    d.ellipse([x + s * 0.6, y + s * 0.3, x + s * 0.9, y + s * 0.6],
              fill=INK)
    d.rectangle([x + s * 0.15, y + s * 0.45, x + s * 0.88, y + s * 0.62],
                fill=INK)
    d.polygon([(x + s * 0.55, y + s * 0.55), (x + s * 0.4, y + s * 0.85),
               (x + s * 0.52, y + s * 0.85), (x + s * 0.45, y + s * 0.95),
               (x + s * 0.68, y + s * 0.6)], fill=RED)


def icon_drone(d, x, y, s):
    d.rectangle([x + s * 0.38, y + s * 0.38, x + s * 0.62, y + s * 0.62],
                fill=INK)
    for cx, cy in ((0.16, 0.16), (0.84, 0.16), (0.16, 0.84), (0.84, 0.84)):
        d.line([(x + s * 0.5, y + s * 0.5), (x + s * cx, y + s * cy)],
               fill=INK, width=2)
        d.ellipse([x + s * cx - s * 0.1, y + s * cy - s * 0.1,
                   x + s * cx + s * 0.1, y + s * cy + s * 0.1],
                  outline=RED, width=2)


def icon_trade(d, x, y, s):
    d.line([(x + s * 0.1, y + s * 0.35), (x + s * 0.85, y + s * 0.35)],
           fill=RED, width=3)
    d.polygon([(x + s * 0.85, y + s * 0.35), (x + s * 0.65, y + s * 0.22),
               (x + s * 0.65, y + s * 0.48)], fill=RED)
    d.line([(x + s * 0.9, y + s * 0.65), (x + s * 0.15, y + s * 0.65)],
           fill=INK, width=3)
    d.polygon([(x + s * 0.15, y + s * 0.65), (x + s * 0.35, y + s * 0.52),
               (x + s * 0.35, y + s * 0.78)], fill=INK)


# ---- big drawn maps for row 1 ----

def map_kerch(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    d.polygon([(x, y), (x + w, y), (x + w, y + h * 0.28),
               (x + w * 0.62, y + h * 0.34), (x + w * 0.38, y + h * 0.28),
               (x, y + h * 0.34)], fill=LAND)
    d.polygon([(x, y + h), (x + w, y + h), (x + w, y + h * 0.66),
               (x + w * 0.6, y + h * 0.6), (x + w * 0.4, y + h * 0.66),
               (x, y + h * 0.6)], fill=LAND)
    by = y + h * 0.47
    d.line([(x + 6, by), (x + w * 0.42, by)], fill=INK, width=4)
    d.line([(x + w * 0.58, by + 14), (x + w - 6, by + 22)], fill=INK,
           width=4)
    d.line([(x + w * 0.42, by), (x + w * 0.5, by + 16)], fill=RED, width=3)
    d.line([(x + w * 0.5, by + 16), (x + w * 0.58, by + 14)], fill=RED,
           width=3)
    cx, cy = x + w * 0.5, by + 6
    d.line([(cx - 7, cy - 7), (cx + 7, cy + 7)], fill=RED, width=3)
    d.line([(cx - 7, cy + 7), (cx + 7, cy - 7)], fill=RED, width=3)
    f = fb(SANS_B, 11)
    d.text((x + 8, y + 4), "RUSSIA", font=f, fill=INK)
    d.text((x + 8, y + h - 16), "CRIMEA", font=f, fill=INK)
    d.text((x + w * 0.62, y + h * 0.52), "KERCH", font=f, fill=INK)
    d.text((x + w * 0.62, y + h * 0.52 + 13), "STRAIT", font=f, fill=INK)


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
    f = fb(SANS_B, 10)
    d.text((x + 8, y + 3), "IRAN", font=f, fill=INK)
    d.text((x + 8, y + h * 0.45), "BAHRAIN", font=f, fill=INK)
    # QESHM right of its island, HORMUZ bottom centre: the two labels
    # must not stack on each other at this small map height.
    d.text((x + w * 0.68, y + h * 0.42), "QESHM", font=f, fill=INK)
    d.text((x + w * 0.60, y + h * 0.78), "HORMUZ", font=f, fill=INK)


def map_quad(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
    fw, fh = (w - 40) // 4, max(20, h - 22)
    fy = y + 5
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
    f = fb(SANS_B, 10)
    for i, name in enumerate(("US", "INDIA", "JAPAN", "AUSTRALIA")):
        text_center(d, xs[i] + fw / 2, fy + fh + 3, name, f, INK)


# ---- schematic world map with numbered pins ----

LAND_BLOBS = [
    [(28, 18), (150, 14), (168, 46), (140, 78), (96, 92), (52, 84),
     (24, 56)],
    [(138, 108), (196, 104), (204, 150), (182, 208), (152, 196),
     (132, 140)],
    [(238, 26), (282, 22), (292, 44), (272, 66), (240, 58)],
    [(238, 76), (292, 72), (300, 110), (282, 164), (252, 158),
     (234, 110)],
    [(298, 20), (448, 16), (458, 60), (430, 108), (380, 118),
     (340, 96), (306, 66)],
    [(392, 168), (446, 164), (452, 188), (420, 204), (390, 192)],
]
# pin number -> (x, y) inside the map box (map box is 462 x 228)
PINS = {1: (296, 52), 2: (340, 96), 3: (424, 122), 4: (266, 132),
        5: (276, 70), 6: (78, 52), 7: (52, 78), 8: (306, 86),
        9: (440, 68), 10: (244, 46), 11: (30, 60), 12: (322, 110),
        13: (398, 52)}


def draw_world_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=SEA, outline=INK, width=1)
    sx, sy = w / 470.0, h / 228.0
    for blob in LAND_BLOBS:
        pts = [(x + px * sx, y + py * sy) for px, py in blob]
        d.polygon(pts, fill=LAND, outline=GREY)
    f = fb(SANS_B, 10)
    for num, (px, py) in sorted(PINS.items()):
        cx, cy = x + px * sx, y + py * sy
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=RED,
                  outline=CARD, width=1)
        text_center(d, cx, cy - 7, str(num), f, CARD)


# ---- story data (verified 17 Nov 2026 reporting only) ----

BIG = [
    ("EUROPE - UKRAINE WAR",
     "Ukraine says a Crimean Bridge road span fell into the sea",
     "Second strike in two days; Zelenskyy hails an 'unprecedented "
     "operation'. The Kremlin vows to rebuild.", "kerch"),
    ("MIDDLE EAST - IRAN WAR",
     "US strikes Iran as tankers burn in Hormuz",
     "Warplanes hit a missile site on Qeshm; 24 seafarers evacuated "
     "from the burning Tara Gas.", "gulf"),
    ("ASIA - DIPLOMACY",
     "Trump holds his first Quad summit, in Manila",
     "First Quad meeting since his return to office; due to meet Xi "
     "and Putin in China on Thursday.", "quad"),
]

MEDIUM = [
    ("AFRICA - HEALTH", "Ebola cases in DR Congo top 11,000, WHO says",
     "5,400 have died; WHO reviews the emergency status.", icon_virus),
    ("GLOBAL - CLIMATE", "COP31 talks grind on in Antalya",
     "Nations weigh a first draft; the talks end Friday.", icon_globe),
    ("AMERICAS - HEALTH", "US loses measles-free status",
     "PAHO cites a year of uninterrupted spread.", icon_cross),
    ("US - BUSINESS", "Nvidia's quarterly sales double to $115.8B",
     "Shares rise after the close; Q4 forecast near $130B.", icon_chip),
    ("MIDDLE EAST - GAZA", "Gaza aid call as winter rains flood shelters",
     "UK, Australia, Canada and Italy urge Israel to open crossings.",
     icon_aid),
]

SMALL = [
    ("ASIA - POLITICS", "Japan scrambles jets",
     "Russian aircraft violated airspace.", icon_jet),
    ("EUROPE - COURTS", "Depardieu admits sexual assault",
     "French actor drops his appeal in Paris.", icon_scales),
    ("TECH", "Apple outage fixed",
     "iCloud sign-ins and the App Store back up.", icon_cloud),
    ("MIDDLE EAST - ENERGY", "Houthis fire drones at Saudi pipeline",
     "Five drones aimed at Riyadh-area pumping stations.", icon_drone),
    ("ASIA - TRADE", "China rejects US chip curbs",
     "Beijing hits back at the cloud-access rule.", icon_trade),
]

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
                   "announced (16 Nov) - US chip-export rule (16 Nov).")

TAG_KERCH = ("CONFIRMED: Reuters-verified footage of the collapsed span.",
             TAG_GREEN)
TAG_IRAN = ("CLAIM: Iran says tankers hit mines in Hormuz - not "
            "independently verified.", TAG_AMBER)
TAG_HOUTHI = ("HOUTHI CLAIM - no Saudi confirmation.", TAG_AMBER)

ONE_LINERS = [
    "(as reported) Lebanon: Israeli airstrikes, shelling and detonations "
    "reported.",
    "Oman evacuates 24 seafarers from the burning gas tanker Tara Gas.",
    "UKMTO reports a second tanker strike north of Khasab, Oman.",
    "Zelenskyy: bridge strike answers Russian attacks on infrastructure.",
    "Wall Street: S&P 500 -1%, Dow -1.6%, Nasdaq -0.7%.",
    "Nvidia board will not reinstate Jensen Huang as CEO.",
    "Dubai airports: 50.4M passengers in 9 months, down 28.1%.",
    "Yemen: government forces pull back toward Aden as Houthis advance.",
    "Five EU states plan a migrant return hub in Rwanda.",
    "Grammy nominations: RAYE leads with 11, ROSAL\u00cdA has 9.",
    "Apple: iCloud sign-in and App Store incidents resolved.",
    "UN: winter rains deepen Gaza shelter crisis.",
    "Ebola: WHO emergency committee reviews the outbreak status.",
    "COP31: first draft of the cover decision out; talks end Friday.",
    "Trump: Asia trip opens with Quad summit in Manila.",
    "Houthis: five drones toward Saudi East-West pipeline.",
    "China: Foreign Ministry criticises the Nov 16 chip rule.",
    "US: measles elimination lost after a year of spread.",
]


def draw_tag(d, x, y, max_w, text, color, start=10):
    """Small verification tag: coloured square + bold text, wrapped."""
    font, lines, lh = fit_block(d, text, SANS_B, start, 8, max_w - 12,
                                2, 22)
    yy = y
    for ln in lines:
        d.rectangle([x, yy + 3, x + 7, yy + 10], fill=color)
        d.text((x + 11, yy), ln, font=font, fill=color)
        yy += lh
    return yy


def draw_big_panel(d, x, y, w, h, num, cat, headline, sub, kind, tag=None):
    ix, iy, iw, ih = panel(d, x, y, w, h)
    map_h = 48
    if kind == "kerch":
        map_kerch(d, ix, iy, iw, map_h)
    elif kind == "gulf":
        map_gulf(d, ix, iy, iw, map_h)
    else:
        map_quad(d, ix, iy, iw, map_h)
    ty = iy + map_h + 6
    d.text((ix, ty), f"{num}. {cat}", font=fb(SANS_B, 14), fill=RED)
    hy = ty + 20
    font, lines, lh = fit_block(d, headline, SANS_B, 23, 16, iw, 3, 54)
    for ln in lines:
        d.text((ix, hy), ln, font=font, fill=INK)
        hy += lh
    font2, lines2, lh2 = fit_block(d, sub, SANS, 15, 12, iw, 3, 42)
    sy = hy + 3
    for ln in lines2:
        d.text((ix, sy), ln, font=font2, fill=INK)
        sy += lh2
    if tag is not None:
        draw_tag(d, ix, sy + 3, iw, tag[0], tag[1])


def draw_small_panel(d, x, y, w, h, num, cat, headline, sub, icon,
                     head_start, head_min, head_lines, sub_start, sub_min,
                     sub_lines, icon_s, head_max, sub_max, tag=None,
                     tag_max=0):
    ix, iy, iw, ih = panel(d, x, y, w, h)
    icon(d, ix + iw - icon_s, iy, icon_s)
    cat_text = f"{num}. {cat}"
    cat_size = 13
    while (d.textlength(cat_text, font=fb(SANS_B, cat_size))
           > iw - icon_s - 6 and cat_size > 9):
        cat_size -= 1
    d.text((ix, iy), cat_text, font=fb(SANS_B, cat_size), fill=RED)
    # Headline starts below the icon so no text ever runs under it.
    hy = iy + icon_s + 6
    font, lines, lh = fit_block(d, headline, SANS_B, head_start, head_min,
                                iw, head_lines, head_max)
    for ln in lines:
        d.text((ix, hy), ln, font=font, fill=INK)
        hy += lh
    font2, lines2, lh2 = fit_block(d, sub, SANS, sub_start, sub_min, iw,
                                   sub_lines, sub_max)
    sy = hy + 3
    for ln in lines2:
        d.text((ix, sy), ln, font=font2, fill=INK)
        sy += lh2
    if tag is not None:
        draw_tag(d, ix, sy + 3, iw, tag[0], tag[1])


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, W - 11, H - 11], outline=INK, width=4)

    # Top kicker.
    d.text((16, 14), "THE WORLD'S NEWS IN ONE PICTURE",
           font=fb(SANS_B, 15), fill=RED)
    right = "13 STORIES - 5 CONTINENTS - ALL FROM TUESDAY"
    rw = d.textlength(right, font=fb(SANS_B, 15))
    d.text((1008 - rw, 14), right, font=fb(SANS_B, 15), fill=INK)
    d.line([(16, 34), (1008, 34)], fill=RED, width=2)

    # Banner, serif bold, as large as fits, with room below the descenders
    # so the tail of the "y" in "Tuesday" clears the rule underneath.
    size = 52
    while (d.textlength("Tuesday 17 November 2026", font=fb(SERIF_B, size))
           > 980 and size > 40):
        size -= 2
    text_center(d, W // 2, 38, "Tuesday 17 November 2026",
                fb(SERIF_B, size), INK)
    d.line([(16, 100), (1008, 100)], fill=RED, width=3)

    # 1. BY THE NUMBERS strip.
    cell_w = (1008 - 16) / 6
    for i, (num, label) in enumerate(NUMBERS):
        cx = 16 + i * cell_w
        text_center(d, cx + cell_w / 2, 106, num, fb(SANS_B, 22), INK)
        font, lines, lh = fit_block(d, label, SANS, 10, 9,
                                    cell_w - 12, 2, 24)
        ly2 = 132
        for ln in lines:
            text_center(d, cx + cell_w / 2, ly2, ln, font, GREY)
            ly2 += lh
        if i:
            d.line([(cx, 108), (cx, 152)], fill=GREY, width=1)

    # 2. WHY THIS DAY MATTERS line (serif; no italic serif on this VM,
    # so regular serif, centred).
    text_center(d, W // 2, 160, WHY_TEXT, fb(SERIF, 18), INK)

    # Row 1: three big panels (tags on panels 1 and 2).
    big_tags = [TAG_KERCH, TAG_IRAN, None]
    for i, (cat, head, sub, kind) in enumerate(BIG):
        draw_big_panel(d, 16 + i * 335, 186, 322, 220, i + 1, cat, head,
                       sub, kind, tag=big_tags[i])

    # 3. THE DAY'S THREAD line.
    label = "THE DAY'S THREAD: "
    lw = d.textlength(label, font=fb(SANS_B, 13))
    d.text((16, 412), label, font=fb(SANS_B, 13), fill=RED)
    d.text((16 + lw, 412), THREAD_TEXT, font=fb(SANS, 13), fill=INK)

    # Row 2: five medium panels.
    for i, (cat, head, sub, icon) in enumerate(MEDIUM):
        draw_small_panel(d, 16 + i * 200, 436, 190, 158, i + 4, cat, head,
                         sub, icon, 18, 14, 3, 14, 11, 3, 28, 53, 41)

    # Row 3: five small panels (tag on panel 12).
    for i, (cat, head, sub, icon) in enumerate(SMALL):
        num = i + 9
        if num == 12:
            draw_small_panel(d, 16 + i * 200, 600, 190, 126, num, cat,
                             head, sub, icon, 16, 12, 2, 13, 10, 2, 14,
                             30, 22, tag=TAG_HOUTHI, tag_max=20)
        else:
            draw_small_panel(d, 16 + i * 200, 600, 190, 126, num, cat,
                             head, sub, icon, 16, 13, 2, 13, 11, 2, 22,
                             39, 29)

    # Bottom left: world map with numbered pins.
    mx, my, mw, mh = 16, 732, 486, 216
    d.rectangle([mx, my, mx + mw, my + mh], fill=CARD, outline=INK, width=2)
    d.rectangle([mx, my, mx + mw, my + 5], fill=RED)
    section_title(d, mx + 12, my + 12, "WHERE IT HAPPENED")
    draw_world_map(d, mx + 12, my + 32, mw - 24, mh - 44)

    # Bottom right: numbered one-liners.
    lx, ly, lw, lh = 514, 732, 494, 216
    d.rectangle([lx, ly, lx + lw, ly + lh], fill=CARD, outline=INK, width=2)
    d.rectangle([lx, ly, lx + lw, ly + 5], fill=RED)
    section_title(d, lx + 12, ly + 12, "ALSO ON TUESDAY 17 NOVEMBER")
    list_top, list_h = ly + 32, lh - 36
    size = 11
    while size >= 9:
        font = fb(SANS, size)
        lh_px = int(size * 1.05)
        if (len(ONE_LINERS) * lh_px <= list_h and all(
                d.textlength(f"{i + 1}. {t}", font=font) <= lw - 24
                for i, t in enumerate(ONE_LINERS))):
            break
        size -= 1
    font = fb(SANS, size)
    lh_px = int(size * 1.05)
    yy = list_top
    for i, t in enumerate(ONE_LINERS):
        d.text((lx + 12, yy), f"{i + 1}. {t}", font=font, fill=INK)
        yy += lh_px

    # 5. DATE CHECK box.
    d.rectangle([16, 950, 1008, 984], outline=INK, width=2)
    d.rectangle([16, 950, 22, 984], fill=RED)
    d.text((30, 954), DATECHECK_TITLE, font=fb(SANS_B, 11), fill=INK)
    d.text((30, 968), DATECHECK_ITEMS, font=fb(SANS, 11), fill=INK)

    # Footer (with the tag legend on the second line).
    text_center(d, W // 2, 988,
                "Every story here happened or was first reported on Tuesday "
                "17 November 2026. Contested claims are marked as claims.",
                fb(SANS, 10), GREY)
    text_center(d, W // 2, 998,
                "Sources: Reuters, AP, PAHO, WHO, UN. Original drawings. "
                "Tags: CONFIRMED = verified by Reuters / AP / PAHO / WHO / "
                "UN; CLAIM = as stated by the source, not independently "
                "verified.",
                fb(SANS, 9), GREY)

    img.save(OUT, optimize=True)
    print("saved", OUT)


if __name__ == "__main__":
    main()
