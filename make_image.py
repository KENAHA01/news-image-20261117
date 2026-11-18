"""Draw the front page for news-image-20261117 (1024x1024 PNG).

Built on the 39-story rebuild (0fbc7a7) and the 8-point upgrade
(e37e493). This version applies 8 fixes, without changing the style
or the CONFIRMED/CLAIM tags:

1. List entries 18, 24, 25, 26, 27 are replaced with 5 unique
   17 November stories that do not repeat a card 1-15 event (JPMorgan
   service restored, UK West Bank sanctions, Xi-Carney tariff cuts,
   Mondlane trial, ULA Vulcan update). Grammy and the COP31 first
   draft are out. The Pentagon audit is NOT used: its report came
   out 16 Nov (Reuters 2026-11-16T22:50:44Z), so the Mondlane trial
   (opened 17 Nov) takes its place. Region counts are recomputed
   from the data; card 15 (An-12, Siberia) moves to ASIA.
2. Every illustration is drawn on its own layer and pasted, so it is
   clipped to its card box; the gap before THE DAY'S THREAD is wider.
3. The footer is raised and set at 8 px so both source lines read
   in full.
4. The illustration area has a fixed height in every card (big maps
   32 px, small scenes 38 px), so the category line, title and body
   start at the same y within a row.
5. The "Also on" list has a gap between region groups.
6. In card 2's Gulf map, the QESHM and HORMUZ labels are moved away
   from the lines and icons.
7. The 2048x2048 render is native, not an upscale: the layout code
   works in 1024 units and a ScaledDraw wrapper draws it at
   MAKEFUN_SCALE x resolution (see render_2048.py).
8. Card 10 uses a scales-of-justice scene (not a courthouse like
   card 14) and card 7 uses a rising-chart scene (not a chip like
   card 13).

Polish round (19 Nov 2026 ~05:03 WIB): card 3's flag area is 32 px
(flags 20 px, labels clear; the dots are removed from map_quad
because in a 28-32 px strip they sat on top of the labels) plus a
leaders caption; cards 1-2 labels clear of lines and icons; DATE
CHECK strip raised to 16 px; tags standardised to "[REGION] -
[TOPIC]" (small-card cat font 8 px so "MIDDLE EAST - ENERGY"
fits); list items 33, 36, 37 replaced with Asia/Africa stories
(Bangladesh garment protests, Uttarakhand bus crash, Tinubu frees
78 suspects); the unsourced "shares fall" (JPMorgan) and "faces up
to 24 years" (Mondlane) phrases removed, while Vulcan keeps "first
stage underperformed" because the title names ULA as its source.

Scene round (19 Nov 2026 ~05:17 WIB): all 15 card illustrations
are replaced by semi-realistic scenes rendered in code
(scenes.py, numpy + Pillow; no image model, no photo, no
downloaded asset, no face or person). One shared engine: gradient
sky with sunlight, fractal-noise clouds and smoke, atmospheric
haze, soft shadows, water reflection with ripples, glow, depth of
field, vignette and film grain; each scene renders at 2x and is
downscaled, with a fixed seed per card. The old pictogram
maps/scenes and their labels are gone; the location captions under
cards 1-3 stay. All text, layout, tags and data are unchanged, and
each scene is pasted exactly into its own box, so no text is
covered by an illustration.

A layout check runs before saving: it stops the program if any card
title or body shrank below its set size, if any card's content
overflows its frame, if the list does not fit, if two map pins
collide, or if any recorded text box overlaps another or leaves
the page.

The entry stays 1024x1024 (the bounty gate caps the file at 1024 px
and 1 MiB). The 2048x2048 render is a separate preview file
(entry-2048.png), drawn natively at 2x by render_2048.py; it is not
the submitted file.
"""

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coast import LAND_POLYS
from scenes import render_scene

# Render scale. 1 = the 1024x1024 entry; 2 = the native 2048x2048
# preview. The layout code below works in 1024 units; ScaledDraw
# scales the drawing to device pixels, and fb() scales the fonts, so
# the same code draws both resolutions natively (no upscaling).
SCALE = int(os.environ.get("MAKEFUN_SCALE", "1"))


def sc(v):
    """A 1024-unit layout value in device pixels."""
    return int(round(v * SCALE))


class ScaledDraw:
    """Wraps a PIL ImageDraw so layout code in 1024 units draws at
    SCALE x resolution. Coordinates and line widths are scaled up at
    draw time; measurements are scaled back down, so the layout code
    keeps seeing 1024-unit values."""

    def __init__(self, draw):
        self._d = draw

    def _s(self, v):
        return v * SCALE

    def _pts(self, xy):
        if isinstance(xy, (list, tuple)) and xy and isinstance(
                xy[0], (list, tuple)):
            return [(self._s(x), self._s(y)) for x, y in xy]
        return [self._s(v) for v in xy]

    def text(self, xy, text, font=None, fill=None, **kw):
        x, y = xy
        return self._d.text((self._s(x), self._s(y)), text, font=font,
                            fill=fill, **kw)

    def textlength(self, text, font=None, **kw):
        return self._d.textlength(text, font=font, **kw) / SCALE

    def textbbox(self, xy, text, font=None, **kw):
        x, y = xy
        box = self._d.textbbox((self._s(x), self._s(y)), text, font=font,
                               **kw)
        return tuple(v / SCALE for v in box)

    def line(self, xy, fill=None, width=1, **kw):
        return self._d.line(self._pts(xy), fill=fill,
                            width=self._s(width), **kw)

    def rectangle(self, xy, fill=None, outline=None, width=1, **kw):
        return self._d.rectangle(self._pts(xy), fill=fill, outline=outline,
                                 width=self._s(width), **kw)

    def polygon(self, xy, fill=None, outline=None, **kw):
        return self._d.polygon(self._pts(xy), fill=fill, outline=outline,
                               **kw)

    def ellipse(self, xy, fill=None, outline=None, width=1, **kw):
        return self._d.ellipse(self._pts(xy), fill=fill, outline=outline,
                               width=self._s(width), **kw)


def clipped_layer(img, x, y, w, h, draw_fn, bg):
    """Draw draw_fn on a separate layer the size of the box, then paste
    it, so the drawing is clipped to the box. draw_fn receives a
    ScaledDraw and the box origin (0, 0) in layout units."""
    layer = Image.new("RGB", (sc(w), sc(h)), bg)
    ld = ScaledDraw(ImageDraw.Draw(layer))
    draw_fn(ld, 0, 0, w, h)
    img.paste(layer, (sc(x), sc(y)))


W, H = 1024, 1024
OUT = (Path(__file__).resolve().parent
       / ("entry-2048.png" if SCALE == 2 else "entry.png"))

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

# Fonts ship in this repo (fonts/, with their licence in
# fonts/LICENSE-DejaVu.txt), so the program downloads nothing and
# renders the same anywhere.
_FONTS = Path(__file__).resolve().parent / "fonts"
SERIF = str(_FONTS / "DejaVuSerif.ttf")
SERIF_B = str(_FONTS / "DejaVuSerif-Bold.ttf")
SANS = str(_FONTS / "DejaVuSans.ttf")
SANS_B = str(_FONTS / "DejaVuSans-Bold.ttf")

TITLE_SIZE = 12      # card titles, cards 4-15
BODY_SIZE = 10       # card body text
BIG_TITLE_SIZE = 17  # card titles, cards 1-3 (about 1.4x TITLE_SIZE)
LIST_SIZE = 10       # "Also on" rows (>= BODY_SIZE)
LIST_HEAD_SIZE = 9   # region group headers in the list

_fonts = {}


def fb(path, size):
    """Font at a 1024-unit size, drawn at SCALE x resolution."""
    size = sc(size)
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

# ------------------------------------------------------------------
# Illustrations: the 15 card scenes are rendered in code by
# scenes.py (numpy + Pillow, no photo, no model, no downloaded
# asset). Each scene is a full-bleed semi-realistic render: gradient
# sky, fractal-noise clouds/smoke, haze, soft shadows, water
# reflection, glow, depth of field, vignette and film grain, drawn
# at 2x and downscaled. The old pictogram maps/scenes are gone.
# ------------------------------------------------------------------


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
    layer = Image.new("RGB", (sc(w), sc(h)), SEA)
    ld = ScaledDraw(ImageDraw.Draw(layer))

    def proj(lon, lat):
        return ((lon + 180) / 360 * w, (85 - lat) / 145 * h)

    for poly in LAND_POLYS:
        pts = [proj(lon, lat) for lon, lat in poly]
        ld.polygon(pts, fill=LAND, outline=INK)
    img.paste(layer, (sc(x), sc(y)))
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
     "title": "Part of the Crimea bridge roadway plunges into the sea",
     "summary": "Struck a second day in a row. Kyiv calls it a first of its "
     "kind; Moscow promises a rebuild.",
     "status": "CONFIRMED", "event": "kerch-bridge",
     "cat": "EUROPE - UKRAINE WAR", "scene": "kerch", "source": "R",
     "caption": "The strait that joins Crimea and Russia",
     "tag": "CONFIRMED: Reuters-checked footage shows the span down."},
    {"id": 2, "region": "MIDDLE EAST",
     "title": "American jets hit Iran while tankers burn off Hormuz",
     "summary": "A missile site on Qeshm was hit; 24 crew were taken off the "
     "burning Tara Gas.",
     "status": "CLAIM", "event": "us-strikes-iran",
     "cat": "MIDDLE EAST - IRAN WAR", "scene": "gulf", "source": "AP",
     "caption": "The strait that runs between Iran and Oman",
     "tag": "CLAIM: Iran blames mines in Hormuz for the tanker hits - not "
     "checked on its own."},
    {"id": 3, "region": "ASIA",
     "title": "Trump gathers the Quad in Manila for the first time",
     "summary": "The first Quad gathering of his new term; Xi and Putin are "
     "next, in China on Thursday.",
     "status": "none", "event": "quad-summit-manila",
     "cat": "ASIA - DIPLOMACY", "scene": "quad", "source": "AP",
     "map_h": 32,
     "caption": "Manila, where ASEAN and the Quad both met",
     "caption2": "Leading the Quad: Trump, Modi, Takaichi, Albanese."},
    {"id": 4, "region": "AFRICA",
     "title": "Congo Ebola: 11,000 cases",
     "summary": "WHO counts 5,400 dead; status under review.",
     "status": "none", "event": "ebola-dr-congo",
     "cat": "AFRICA - HEALTH", "scene": "ebola", "source": "WHO"},
    {"id": 5, "region": "WORLD",
     "title": "Antalya climate talks reach a first draft",
     "summary": "An opening text is on the table; talks end Friday.",
     "status": "none", "event": "cop31-talks",
     "cat": "WORLD - CLIMATE", "scene": "cop31", "source": "AP"},
    {"id": 6, "region": "AMERICAS",
     "title": "US measles-free standing lost",
     "summary": "PAHO points to a full year of spread.",
     "status": "none", "event": "us-measles-status",
     "cat": "AMERICAS - HEALTH", "scene": "measles", "source": "PAHO"},
    {"id": 7, "region": "AMERICAS",
     "title": "Nvidia doubles to $115.8bn",
     "summary": "Shares rose late; next quarter near $130bn.",
     "status": "none", "event": "nvidia-earnings",
     "cat": "US - BUSINESS", "scene": "chart", "source": "AP"},
    {"id": 8, "region": "MIDDLE EAST",
     "title": "Rain floods shelters across Gaza",
     "summary": "Four allies press Israel to open the crossings.",
     "status": "none", "event": "gaza-aid-call",
     "cat": "MIDDLE EAST - GAZA", "scene": "gaza", "source": "AP"},
    {"id": 9, "region": "ASIA",
     "title": "Japan sends jets up after airspace breach",
     "summary": "Russian planes entered Japanese airspace.",
     "status": "none", "event": "japan-jets",
     "cat": "ASIA - POLITICS", "scene": "japan", "source": "AP"},
    {"id": 10, "region": "EUROPE",
     "title": "Depardieu concedes assault, ends appeal",
     "summary": "The French actor withdrew his Paris appeal.",
     "status": "none", "event": "depardieu-appeal",
     "cat": "EUROPE - COURTS", "scene": "scales", "source": "AP"},
    {"id": 11, "region": "AMERICAS",
     "title": "Apple restores iCloud and App Store",
     "summary": "Sign-ins and the store are working again.",
     "status": "none", "event": "apple-outage",
     "cat": "AMERICAS - TECH", "scene": "apple", "source": "AP"},
    {"id": 12, "region": "MIDDLE EAST",
     "title": "Drones strike a Saudi oil pipeline",
     "summary": "Five drones hit pumping stations near Riyadh.",
     "status": "CLAIM", "event": "houthi-drones-saudi",
     "cat": "MIDDLE EAST - ENERGY", "scene": "houthi", "source": "R",
     "tag": "HOUTHI CLAIM - no Riyadh confirmation."},
    {"id": 13, "region": "ASIA",
     "title": "Beijing pushes back on US chip limits",
     "summary": "China answered the new cloud-access restriction.",
     "status": "none", "event": "china-chip-curbs",
     "cat": "ASIA - TRADE", "scene": "china", "source": "R"},
    {"id": 14, "region": "ASIA",
     "title": "Mongolia's president steps down",
     "summary": "He denies a $25m bribe claim; parliament must agree.",
     "status": "none", "event": "mongolia-resignation",
     "cat": "ASIA - POLITICS", "scene": "mongolia", "source": "AP"},
    {"id": 15, "region": "ASIA",
     "title": "Siberia plane crash kills 19",
     "summary": "An An-12 came down near Kemerovo; officials blame a fault.",
     "status": "none", "event": "an12-crash",
     "cat": "ASIA - AIR CRASH", "scene": "an12", "source": "AP"},
    {"id": 16, "region": "MIDDLE EAST",
     "title": "(as reported) Lebanon: Israeli strikes, shelling and blasts.",
     "summary": "Israeli strikes, shelling and blasts were reported in Lebanon.",
     "status": "none", "event": "lebanon-strikes", "source": "R"},
    {"id": 17, "region": "MIDDLE EAST",
     "title": "A second tanker was hit north of Khasab, Oman, UKMTO says.",
     "summary": "UKMTO said a second tanker was hit north of Khasab, Oman.",
     "status": "none", "event": "second-tanker-khasab", "source": "UKMTO"},
    {"id": 18, "region": "AMERICAS",
     "title": "JPMorgan: services back after Monday's outage.",
     "summary": "Chase said services were back to normal after Monday's "
     "software bug.",
     "status": "none", "event": "jpmorgan-outage", "source": "AP"},
    {"id": 19, "region": "AMERICAS",
     "title": "US stocks slide: S&P 500 -1%, Dow -1.6%, Nasdaq -0.7%.",
     "summary": "US stocks slid: the S&P 500 fell 1%, the Dow 1.6% and the "
     "Nasdaq 0.7%.",
     "status": "none", "event": "wall-street-falls", "source": "AP"},
    {"id": 20, "region": "AMERICAS",
     "title": "Nvidia's board rules out bringing Huang back as chief.",
     "summary": "Nvidia's board ruled out bringing Jensen Huang back as chief "
     "executive.",
     "status": "none", "event": "nvidia-board-ceo", "source": "AP"},
    {"id": 21, "region": "MIDDLE EAST",
     "title": "Dubai airports handled 50.4m travellers in nine months, 28.1% "
     "fewer.",
     "summary": "Dubai airports handled 50.4 million travellers in nine months, "
     "28.1% fewer than before.",
     "status": "none", "event": "dubai-airports", "source": "AP"},
    {"id": 22, "region": "MIDDLE EAST",
     "title": "Yemen's army falls back toward Aden as Houthi fighters push "
     "on.",
     "summary": "Yemen's army fell back toward Aden as Houthi fighters pushed "
     "on.",
     "status": "none", "event": "yemen-pullback", "source": "AP"},
    {"id": 23, "region": "EUROPE",
     "title": "Five EU countries plan a Rwanda hub for returning migrants.",
     "summary": "Five EU countries plan a hub in Rwanda for returning migrants.",
     "status": "none", "event": "eu-rwanda-hub", "source": "AP"},
    {"id": 24, "region": "EUROPE",
     "title": "Britain sanctions 8 firms over West Bank building, plus an "
     "aid-blocker.",
     "summary": "Britain froze the assets of eight firms building in the West "
     "Bank, and of Tzav 9, which blocks Gaza aid.",
     "status": "none", "event": "uk-westbank-sanctions", "source": "AP"},
    {"id": 25, "region": "ASIA",
     "title": "Xi and Carney agree to cut tariffs; China loosens curbs on "
     "Canadian pork and seafood.",
     "summary": "China will cut tariffs on C$400m of Canadian pork and seafood; "
     "Canada extends steel and aluminium relief.",
     "status": "none", "event": "xi-carney-tariffs", "source": "R"},
    {"id": 26, "region": "AFRICA",
     "title": "Mondlane stands trial in Mozambique on five charges.",
     "summary": "Opposition leader Venancio Mondlane stands trial on five "
     "charges over the deadly 2024 election protests.",
     "status": "none", "event": "mondlane-trial", "source": "AP"},
    {"id": 27, "region": "AMERICAS",
     "title": "ULA: Vulcan's first stage fell short; 40 Amazon satellites "
     "lost.",
     "summary": "ULA said the first stage fell short just after liftoff in "
     "Sunday's failure.",
     "status": "none", "event": "vulcan-failure", "source": "AP"},
    {"id": 28, "region": "OCEANIA",
     "title": "Cyclone Xavier hits the Northern Cook Islands.",
     "summary": "Cyclone Xavier hit the Northern Cook Islands.",
     "status": "none", "event": "cyclone-xavier", "source": "AP"},
    {"id": 29, "region": "WORLD",
     "title": "Voyager 1 nears a light-day from Earth; it crosses early "
     "Wednesday.",
     "summary": "Voyager 1 nears one light-day from Earth and crosses early "
     "Wednesday.",
     "status": "none", "event": "voyager-1", "source": "NASA"},
    {"id": 30, "region": "AFRICA",
     "title": "UN confirms 2,230 civilian deaths in Sudan, most by drone.",
     "summary": "The UN confirmed 2,230 civilian deaths in Sudan, most caused "
     "by drones.",
     "status": "none", "event": "sudan-civilian-deaths", "source": "UN"},
    {"id": 31, "region": "MIDDLE EAST",
     "title": "Israel: Kahana wins Knesset speaker vote, 66-52.",
     "summary": "Matan Kahana won the Knesset speaker vote by 66 to 52.",
     "status": "none", "event": "kahana-speaker", "source": "AP"},
    {"id": 32, "region": "EUROPE",
     "title": "Moldova closes its skies as 7 drones enter; 5 come down by "
     "villages.",
     "summary": "Moldova closed its airspace as seven drones entered; five came "
     "down near villages.",
     "status": "none", "event": "moldova-drones", "source": "AP"},
    {"id": 33, "region": "ASIA",
     "title": "Bangladesh: police use tear gas on garment workers seeking "
     "higher pay.",
     "summary": "Police used tear gas on garment workers around Dhaka seeking a "
     "Tk 30,000 minimum wage, up from Tk 12,500.",
     "status": "none", "event": "bangladesh-garment-protests", "source": "TH"},
    {"id": 34, "region": "EUROPE",
     "title": "France: 146,000 join wage protests; unions want higher pay.",
     "summary": "Wage protests drew 146,000 people across France; 28,000 "
     "marched in Paris.",
     "status": "none", "event": "france-wage-protests", "source": "LM"},
    {"id": 35, "region": "EUROPE",
     "title": "Russia: no place for Europe at the next Ukraine talks, aide "
     "says.",
     "summary": "Moscow has not agreed to a European role in the next round of "
     "Ukraine talks, aide Yuri Ushakov said.",
     "status": "none", "event": "russia-europe-talks", "source": "R"},
    {"id": 36, "region": "ASIA",
     "title": "India: bus plunges 100m into a Uttarakhand gorge; 8 dead, 26 "
     "hurt.",
     "summary": "A bus carrying 34 people plunged 100 metres into a gorge near "
     "Gular bridge in Tehri Garhwal early Tuesday; 8 were killed and "
     "26 hurt.",
     "status": "none", "event": "uttarakhand-bus-crash", "source": "PTI"},
    {"id": 37, "region": "AFRICA",
     "title": "Nigeria: Tinubu pardons 78 suspects held over the convoy "
     "attack.",
     "summary": "President Tinubu pardoned 78 suspects arrested over the "
     "stoning of his convoy in Abuja on Friday.",
     "status": "none", "event": "tinubu-frees-suspects", "source": "AP"},
    {"id": 38, "region": "WORLD",
     "title": "Pattinson picked as the next James Bond.",
     "summary": "British actor Robert Pattinson was picked as the next James "
     "Bond.",
     "status": "none", "event": "pattinson-james-bond", "source": "AP"},
    {"id": 39, "region": "ASIA",
     "title": "Dhaka leads the world's most polluted cities; AQI 292.",
     "summary": "Dhaka led the world's most polluted cities on Tuesday morning, "
     "with an AQI of 292.",
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

WHY_TEXT = ("A bridge falls to the sea, tankers burn, and a 26-year run "
            "of good health news ends.")

THREAD_TEXT = ("Russia struck Kyiv's two Dnipro crossings on Monday; on "
               "Tuesday, Ukraine brought down the Kerch road span in reply.")

DATECHECK_TEXT = ("DATES CHECKED - not from 17 Nov: COP31's first draft "
                  "(16 Nov) - Grammy nominations (16 Nov) - US chip-export "
                  "rule (16 Nov) - Guinea gold-mining sentences (16 Nov).")


# ---- card drawers (uniform title 12 px, body 10 px; big titles 17 px) ----

CARD_BOUNDS = []


def draw_source(d, ix, iy, iw, ih, source, group):
    """Source initials at the card's bottom-right corner."""
    f = fb(SANS, 8)
    tw = d.textlength(source, font=f)
    tbox(d, ix + iw - tw, iy + ih - 10, source, f, GREY, group,
         label="source")


def draw_big_panel(img, d, x, y, w, h, story):
    num = story["id"]
    group = f"card{num}"
    ix, iy, iw, ih = panel(d, x, y, w, h)
    CARD_BOUNDS.append((group, ix, iy, ix + iw, iy + ih))
    region_col = REGION_COLORS[story["region"]]
    tag = TAG_BY_ID.get(num)
    font, lines, lh = fit_block(d, story["title"], SANS_B, BIG_TITLE_SIZE,
                                BIG_TITLE_SIZE, iw, 2, 38,
                                label=f"big title {num}", strict=True)
    font2, lines2, lh2 = fit_block(d, story["summary"], SANS, BODY_SIZE,
                                   BODY_SIZE, iw, 3, 33,
                                   label=f"big sub {num}", strict=True)
    # Fixed illustration height: the rendered scene is 28 px in big
    # cards, except card 3 (conference hall), whose scene is 32 px.
    # The scene is a full-bleed render pasted exactly into its box,
    # so it cannot overlap any text.
    map_h = story.get("map_h", 28)
    HEIGHT_LOG.append((f"big card {num} scene-min", map_h, 28))
    img.paste(render_scene(num, sc(iw), sc(map_h)), (sc(ix), sc(iy)))
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
    # Extra caption, only where the story carries one (card 3): fills
    # the empty space under the body text.
    caption2 = story.get("caption2")
    if caption2:
        tbox(d, ix, sy + 6, caption2, fb(SANS, 9), GREY, group,
             label="caption2")
        sy += 6 + 10
    if tag is not None:
        draw_tag(d, ix, sy + 3, iw, tag[0], tag[1], group)
    draw_source(d, ix, iy, iw, ih, story["source"], group)
    content_h = (map_h + 8 + 3 + 15 + len(lines) * lh + 3
                 + len(lines2) * lh2 + (16 if caption2 else 0)
                 + 3 + (20 if tag else 0))
    HEIGHT_LOG.append((f"big card {num}", content_h, ih))


def draw_small_panel(img, d, x, y, w, h, story):
    num = story["id"]
    group = f"card{num}"
    ix, iy, iw, ih = panel(d, x, y, w, h)
    CARD_BOUNDS.append((group, ix, iy, ix + iw, iy + ih))
    region_col = REGION_COLORS[story["region"]]
    _, t_lines, t_lh = fit_block(d, story["title"], SANS_B, TITLE_SIZE,
                                 TITLE_SIZE, iw, 3, 42,
                                 label=f"title {num}", strict=True)
    _, s_lines, s_lh = fit_block(d, story["summary"], SANS, BODY_SIZE,
                                 BODY_SIZE, iw, 3, 36,
                                 label=f"sub {num}", strict=True)
    tag = TAG_BY_ID.get(num)
    text_h = (4 + 16 + len(t_lines) * t_lh + 3 + len(s_lines) * s_lh
              + (3 + 20 if tag else 0))
    # Fixed illustration height (point 4): the scene is 34 px in every
    # small card, so the category, title and body start at the same y
    # within a row. The scene is a full-bleed render pasted exactly
    # into its box, so it cannot overlap any text.
    scene_h = 34
    HEIGHT_LOG.append((f"small card {num} scene", scene_h, 34))
    img.paste(render_scene(num, sc(iw), sc(scene_h)), (sc(ix), sc(iy)))
    cy = iy + scene_h + 4
    # 8 px (was 9): the standardised "MIDDLE EAST - ENERGY" tag is
    # too wide for a 134 px card at 9 px.
    tbox(d, ix, cy, f"{num}. {story['cat']}", fb(SANS_B, 8), region_col,
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

    img = Image.new("RGB", (sc(W), sc(H)), PAPER)
    d = ScaledDraw(ImageDraw.Draw(img))
    d.rectangle([10, 10, W - 11, H - 11], outline=INK, width=4)

    # Top kicker (story count and region count come from the list).
    tbox(d, 16, 14, "A DAY OF WORLD NEWS, IN ONE FRAME", fb(SANS_B, 13),
         RED, "header", label="kicker")
    rw = d.textlength(kicker_right, font=fb(SANS_B, 13))
    tbox(d, 1008 - rw, 14, kicker_right, fb(SANS_B, 13), INK, "header",
         label="kicker-right")
    d.line([(16, 31), (1008, 31)], fill=RED, width=2)

    # Banner, serif bold, as large as fits, with room below the descenders
    # so the tail of the "y" in "Tuesday" clears the rule underneath.
    size = 30
    while (d.textlength("Tuesday 17 November 2026", font=fb(SERIF_B, size))
           > 980 and size > 28):
        size -= 2
    tbox_c(d, W // 2, 33, "Tuesday 17 November 2026", fb(SERIF_B, size),
           INK, "header", label="banner")
    d.line([(16, 65), (1008, 65)], fill=RED, width=3)

    # Region-counts bar, computed from STORIES, each segment in its
    # region colour.
    seg_font = fb(SANS_B, 10)
    segs = [(f"{r} {counts[r]}", REGION_COLORS[r]) for r in REGIONS]
    sep_w = d.textlength(" - ", font=seg_font)
    total = sum(d.textlength(t, font=seg_font) for t, _ in segs)
    total += sep_w * (len(segs) - 1)
    sx = (W - total) / 2
    for i, (text, col) in enumerate(segs):
        tbox(d, sx, 69, text, seg_font, col, "header", label="region-bar")
        sx += d.textlength(text, font=seg_font)
        if i < len(segs) - 1:
            tbox(d, sx, 69, " - ", seg_font, GREY, "header", label="sep")
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
                d.polygon([(ax, 81 + 9), (ax + 10, 81 + 9),
                           (ax + 5, 81 + 1)], fill=col)
            else:
                d.polygon([(ax, 81 + 1), (ax + 10, 81 + 1),
                           (ax + 5, 81 + 9)], fill=col)
            tbox(d, ax + 16, 81, num, nfont, col, "numbers", label="num")
        else:
            tbox_c(d, cx + cell_w / 2, 81, num, nfont, col, "numbers",
                   label="num")
        font, lines, lh = fit_block(d, label, SANS, 7, 7, cell_w - 12,
                                    2, 16, label=f"number label {i}")
        if len(lines) > 2:
            sys.exit(f"number label {i} needs {len(lines)} lines")
        ly2 = 96
        for ln in lines:
            tbox_c(d, cx + cell_w / 2, ly2, ln, font, GREY, "numbers",
                   label="num-label")
            ly2 += lh
        if i:
            d.line([(cx, 83), (cx, 108)], fill=GREY, width=1)

    # 2. WHY THIS DAY MATTERS line (serif; no italic serif on this VM,
    # so regular serif, centred).
    tbox_c(d, W // 2, 108, WHY_TEXT, fb(SERIF, 10), INK, "header",
           label="why")

    # Row 1: three big panels.
    for i in range(3):
        draw_big_panel(img, d, 16 + i * 335, 122, 322, 164, CARDS[i])

    # 3. THE DAY'S THREAD line (wider gap above it, point 2).
    label = "HOW THE DAY UNFOLDED: "
    lw = d.textlength(label, font=fb(SANS_B, 10))
    tbox(d, 16, 294, label, fb(SANS_B, 10), RED, "header", label="thread")
    tbox(d, 16 + lw, 294, THREAD_TEXT, fb(SANS, 10), INK, "header",
         label="thread-text")

    # Row 2: six medium panels.
    for i in range(6):
        draw_small_panel(img, d, 16 + i * 165, 307, 158, 146, CARDS[3 + i])

    # Row 3: six small panels.
    for i in range(6):
        draw_small_panel(img, d, 16 + i * 165, 456, 158, 158, CARDS[9 + i])

    # Bottom left: world map with numbered pins + region legend.
    mx, my, mw, mh = 16, 619, 486, 348
    d.rectangle([mx, my, mx + mw, my + mh], fill=CARD, outline=INK, width=2)
    d.rectangle([mx, my, mx + mw, my + 5], fill=RED)
    section_title(d, mx + 12, my + 12, "WHERE THE STORIES SIT")
    draw_world_map(img, d, mx + 12, my + 32, mw - 24, 296)
    leg_font = fb(SANS_B, 8)
    leg_w = 0
    for r in REGIONS:
        leg_w += 6 + 4 + d.textlength(r, font=leg_font)
    leg_w += 8 * (len(REGIONS) - 1)
    lx_leg = mx + mw / 2 - leg_w / 2
    for i, r in enumerate(REGIONS):
        d.ellipse([lx_leg, my + 334, lx_leg + 6, my + 340],
                  fill=REGION_COLORS[r])
        tbox(d, lx_leg + 10, my + 333, r, leg_font, REGION_COLORS[r],
             "map", label="legend")
        lx_leg += 6 + 4 + d.textlength(r, font=leg_font) + 8

    # Bottom right: "Also on" list, grouped by region, ids 16-39,
    # with a gap between region groups (point 5).
    lx, ly, lw, lh = 514, 619, 494, 348
    d.rectangle([lx, ly, lx + lw, ly + lh], fill=CARD, outline=INK, width=2)
    d.rectangle([lx, ly, lx + lw, ly + 5], fill=RED)
    section_title(d, lx + 12, ly + 12, "THE REST OF TUESDAY, 17 NOVEMBER")
    list_top, list_h = ly + 30, lh - 34
    yy = list_top
    for gi, (region, items) in enumerate(ALSO_BY_REGION):
        col = REGION_COLORS[region]
        tbox(d, lx + 12, yy, region, fb(SANS_B, LIST_HEAD_SIZE), col,
             "list", label="head")
        yy += 8
        for s in items:
            d.ellipse([lx + 12, yy + 1, lx + 18, yy + 7], fill=col)
            tbox(d, lx + 24, yy, f"{s['id']}. {s['title']}",
                 fb(SANS, LIST_SIZE), INK, "list", label="row")
            yy += 10
        if gi < len(ALSO_BY_REGION) - 1:
            yy += 3
    HEIGHT_LOG.append(("list", yy - list_top, list_h))

    # 5. DATE CHECK, one line, in a taller strip (16 px) so the text
    # sits clear of the box lines.
    d.rectangle([16, 970, 1008, 986], outline=INK, width=2)
    d.rectangle([16, 970, 22, 986], fill=RED)
    tbox(d, 30, 974, DATECHECK_TEXT, fb(SANS, 8), INK, "footer",
         label="datecheck")

    # Footer (with the tag legend on the second line), raised and set
    # at 8 px so both source lines read in full (point 3).
    tbox_c(d, W // 2, 990,
           "Each item below took place, or was first reported, on Tuesday "
           "17 November 2026. Anything still disputed is labelled a claim.",
           fb(SANS, 8), GREY, "footer", label="footer1")
    tbox_c(d, W // 2, 999,
           "Reporting: Reuters, AP, PAHO, WHO, UN, Le Monde, CNN, UNB, "
           "UKMTO, NASA. Pictures drawn for this page. CONFIRMED = "
           "verified by a wire; CLAIM = the source's word, not "
           "checked alone.",
           fb(SANS, 8), GREY, "footer", label="footer2")

    check_layout()
    img.save(OUT, optimize=True)
    print("saved", OUT)


if __name__ == "__main__":
    main()
