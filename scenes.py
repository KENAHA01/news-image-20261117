"""Procedural semi-realistic scenes for news-image-20261117.

No image model, no photo, no downloaded asset: every scene is
rendered in code from numpy + Pillow. One shared engine gives all
15 cards the same look: gradient sky with a sun, clouds and smoke
from fractal noise, atmospheric haze, soft shadows, water reflection
with ripples, glow, depth of field, vignette and film grain. Each
scene is rendered at 2x and downscaled (LANCZOS). The random seed
is fixed per card, so every run renders byte-identical output.

A scene fills its whole strip (the card's illustration area) edge
to edge; there is no empty space inside it. Text is never drawn
here, so nothing can overlap it.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE_SEED = 20261117


# ------------------------------------------------------------------
# small numeric helpers (arrays are float64 in [0, 1], shape (H, W, 3))
# ------------------------------------------------------------------

def _rng(seed):
    return np.random.default_rng(seed)


def _fbm(w, h, seed, octaves=4, base=4):
    """Fractal Brownian motion noise in [0, 1], shape (h, w)."""
    rng = _rng(seed)
    total = np.zeros((h, w), dtype=np.float64)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        gw, gh = base * (2 ** o), max(2, base * (2 ** o) // 2)
        grid = rng.random((gh, gw))
        gimg = Image.fromarray((grid * 255).astype(np.uint8), mode="L")
        gimg = gimg.resize((w, h), Image.BILINEAR)
        total += amp * (np.asarray(gimg, dtype=np.float64) / 255.0)
        norm += amp
        amp *= 0.5
    return total / norm


def _vgrad(w, h, stops):
    """Vertical gradient. stops: [(pos 0..1, (r, g, b) 0..1), ...]."""
    ys = np.linspace(0.0, 1.0, h)
    cols = np.zeros((h, 3), dtype=np.float64)
    pos = [s[0] for s in stops]
    for c in range(3):
        vals = [s[1][c] for s in stops]
        cols[:, c] = np.interp(ys, pos, vals)
    return np.repeat(cols[:, None, :], w, axis=1)


def _smoothstep(x, lo, hi):
    t = np.clip((x - lo) / max(1e-9, hi - lo), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _add_glow(arr, cx, cy, r, color, strength=1.0):
    """Additive radial glow centred at (cx, cy) in pixels."""
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1.0, r)
    g = np.clip(1.0 - d, 0.0, 1.0) ** 2.0
    for c in range(3):
        arr[:, :, c] += g * color[c] * strength
    return arr


def _disc(arr, cx, cy, r, color):
    """Soft-edged bright disc (the sun)."""
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1.0, r)
    a = np.clip(1.0 - d, 0.0, 1.0)
    a = _smoothstep(a, 0.25, 0.95)
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1.0 - a) + color[c] * a
    return arr


def _clouds(arr, seed, cover=0.45, soft=0.18, color=(1.0, 1.0, 1.0),
            y0=0.0, y1=1.0, stretch=1.0, strength=1.0):
    """Blend fractal clouds over the band y0..y1 (fractions of height)."""
    h, w = arr.shape[:2]
    n = _fbm(w, h, seed, octaves=4, base=5)
    if stretch != 1.0:
        n = _fbm(w, max(2, int(h * stretch)), seed, octaves=4, base=5)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8))
                       .resize((w, h), Image.BILINEAR),
                       dtype=np.float64) / 255.0
    a = _smoothstep(n, cover, cover + soft) * strength
    band = np.zeros((h, 1))
    band[int(h * y0):int(h * y1)] = 1.0
    a = a * band
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1.0 - a) + color[c] * a
    return arr


def _haze(arr, color, amount, y0=0.0, y1=1.0):
    """Uniform atmospheric haze over the band y0..y1."""
    h, w = arr.shape[:2]
    m = np.zeros((h, 1))
    m[int(h * y0):int(h * y1)] = amount
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1.0 - m) + color[c] * m
    return arr


def _water(arr, y0, deep, shallow, sun_x=None, sun_color=(1.0, 0.75, 0.4),
           sun_w=0.10, seed=0, ripple=0.5):
    """Water below row y0 (fraction): dark gradient, a bright
    reflection column under the sun/fire, and ripple streaks."""
    h, w = arr.shape[:2]
    y0i = int(h * y0)
    water = _vgrad(w, h - y0i, [(0.0, shallow), (1.0, deep)])
    arr[y0i:, :, :] = water
    if sun_x is not None:
        yy, xx = np.mgrid[y0i:h, 0:w]
        rel = (yy - y0i) / max(1.0, h - y0i)
        wob = np.sin(rel * 22.0 + np.sin(rel * 47.0) * 1.5) * (6.0 + rel * 26.0)
        col = np.abs(xx - (sun_x + wob)) / (w * sun_w * (0.5 + rel))
        g = np.clip(1.0 - col, 0.0, 1.0) ** 2.0 * (1.0 - rel * 0.75)
        for c in range(3):
            arr[y0i:, :, c] += g * sun_color[c] * 0.9
    # ripple streaks: bright horizontal dashes from noise
    n = _fbm(w, h - y0i, seed + 5, octaves=3, base=6)
    streak = _smoothstep(n, 0.62, 0.80) * 0.22 * ripple
    for c in range(3):
        arr[y0i:, :, c] += streak * (0.9 if c == 0 else 0.85 if c == 1
                                     else 0.7)
    return arr


def _bokeh(img, seed, count, color=(1.0, 0.9, 0.7), rmin=4, rmax=14,
           alpha=70):
    """Out-of-focus light spots (depth of field) on a PIL image."""
    rng = _rng(seed)
    w, h = img.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(count):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h * 0.75)
        r = rng.uniform(rmin, rmax)
        a = int(alpha * rng.uniform(0.4, 1.0))
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=tuple(int(c * 255) for c in color) + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(layer)
    return img


def _vignette(arr, strength=0.22):
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - w / 2) / (w / 2)
    dy = (yy - h / 2) / (h / 2)
    d = np.clip(np.sqrt(dx * dx + dy * dy), 0.0, 1.4)
    f = 1.0 - strength * np.clip(d - 0.55, 0.0, 1.0) ** 2.0
    return arr * f[:, :, None]


def _grade(arr):
    """One shared cinematic grade for every card: warm highlights,
    cool shadows. Keeps a single palette and light style."""
    lum = arr.mean(axis=2, keepdims=True)
    warm = np.array([1.06, 1.0, 0.94])
    cool = np.array([0.94, 1.0, 1.06])
    wgt = np.clip(lum * 1.4 - 0.2, 0.0, 1.0)
    return np.clip(arr * (warm * wgt + cool * (1.0 - wgt)), 0.0, 1.0)


def _grain(arr, seed, amount=0.028):
    rng = _rng(seed)
    n = rng.normal(0.0, amount, arr.shape[:2])[:, :, None]
    return np.clip(arr + n, 0.0, 1.0)


def _finish(arr, seed):
    """Shared finish: grade, vignette, grain. Returns a PIL image."""
    arr = _grade(arr)
    arr = _vignette(arr, 0.20)
    arr = _grain(arr, seed + 99, 0.026)
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8),
                           mode="RGB")


def _pil(arr):
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8),
                           mode="RGB")


def _np(img):
    return np.asarray(img, dtype=np.float64) / 255.0


def _ci(col):
    """Float RGB tuple (0..1) -> int tuple (0..255) for PIL."""
    return tuple(int(round(c * 255)) for c in col)


def _soft_layer(w, h):
    """A transparent layer + draw, blurred a touch for soft edges."""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return layer, ImageDraw.Draw(layer)


def _paste_soft(base_img, layer, blur=1.2):
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base_img.alpha_composite(layer)
    return base_img


def _shadow(img, box, blur=4, alpha=90):
    """Soft drop shadow under an object: box (x0, y0, x1, y1)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=(0, 0, 0, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)
    return img


# ------------------------------------------------------------------
# extra helpers used by the scenes
# ------------------------------------------------------------------

def _reflect(arr, y0, strength=0.42, seed=0, wobble=5.0):
    """Mirror the scene above the waterline y0 into the water below
    it, with a ripple wobble that grows with depth."""
    h, w = arr.shape[:2]
    y0i = int(h * y0)
    if y0i <= 1 or y0i >= h:
        return arr
    n = min(h - y0i, y0i)
    above = arr[:y0i][::-1][:n].copy()
    ys = np.arange(n)
    shift = (np.sin(ys * 0.30) * wobble * 0.5
             + np.sin(ys * 0.11 + 1.7) * wobble).astype(int)
    refl = np.empty_like(above)
    for i in range(n):
        refl[i] = np.roll(above[i], int(shift[i]), axis=0)
    fade = np.linspace(1.0, 0.22, n)[:, None, None]
    refl = refl * fade
    arr[y0i:y0i + n] = (arr[y0i:y0i + n] * (1.0 - strength)
                        + refl * strength)
    return arr


def _wavy(img, amp, wavelength, phase=0.0):
    """Wave a small flag image by shifting each column vertically."""
    a = np.asarray(img, dtype=np.float64)
    h, w = a.shape[:2]
    xs = np.arange(w)
    shift = (amp * np.sin(2.0 * np.pi * xs / wavelength + phase)).astype(int)
    out = np.zeros_like(a)
    for x in range(w):
        out[:, x] = np.roll(a[:, x], int(shift[x]), axis=0)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8),
                           mode=img.mode)


def _flag_us(w, h):
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    stripe = h / 13.0
    for i in range(13):
        if i % 2 == 0:
            d.rectangle([0, i * stripe, w, (i + 1) * stripe],
                        fill=(178, 34, 52))
    d.rectangle([0, 0, int(w * 0.4), int(stripe * 7)], fill=(60, 59, 110))
    return img


def _flag_in(w, h):
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h / 3], fill=(255, 153, 51))
    d.rectangle([0, 2 * h / 3, w, h], fill=(19, 136, 8))
    d.ellipse([w / 2 - h * 0.11, h / 2 - h * 0.11, w / 2 + h * 0.11,
               h / 2 + h * 0.11], outline=(0, 0, 128), width=1)
    return img


def _flag_jp(w, h):
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    r = h * 0.30
    d.ellipse([w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r],
              fill=(188, 0, 45))
    return img


def _flag_au(w, h):
    img = Image.new("RGB", (w, h), (0, 40, 104))
    d = ImageDraw.Draw(img)
    # Union Jack canton, simplified to a cross + diagonals
    cw, ch = int(w * 0.5), int(h * 0.5)
    d.rectangle([0, 0, cw, ch], fill=(0, 40, 104))
    d.line([(0, 0), (cw, ch)], fill=(255, 255, 255), width=2)
    d.line([(0, ch), (cw, 0)], fill=(255, 255, 255), width=2)
    d.line([(cw // 2, 0), (cw // 2, ch)], fill=(255, 255, 255), width=2)
    d.line([(0, ch // 2), (cw, ch // 2)], fill=(255, 255, 255), width=2)
    for sx, sy in ((0.72, 0.30), (0.85, 0.62), (0.68, 0.78)):
        x, y = w * sx, h * sy
        d.line([(x - 3, y), (x + 3, y)], fill=(255, 255, 255), width=1)
        d.line([(x, y - 3), (x, y + 3)], fill=(255, 255, 255), width=1)
    return img


# ------------------------------------------------------------------
# scenes 1-8
# ------------------------------------------------------------------

def _scene_1(W, H, seed):
    """Kerch Bridge at foggy dawn: a road span has fallen into the
    sea, steel pillars bent, smoke and spray."""
    arr = _vgrad(W, H, [(0.0, (0.48, 0.54, 0.62)),
                        (0.45, (0.88, 0.74, 0.55)),
                        (0.55, (0.45, 0.48, 0.50)),
                        (1.0, (0.12, 0.16, 0.18))])
    _add_glow(arr, W * 0.30, H * 0.42, W * 0.30, (1.0, 0.82, 0.55), 0.6)
    _disc(arr, W * 0.30, H * 0.40, max(3.0, H * 0.10), (1.0, 0.90, 0.70))
    _clouds(arr, seed + 1, cover=0.55, soft=0.22,
            color=(0.92, 0.88, 0.82), y0=0.0, y1=0.42, strength=0.5)
    # water base (dark, cold)
    y0 = 0.52
    y0i = int(H * y0)
    arr[y0i:] = _vgrad(W, H - y0i, [(0.0, (0.42, 0.47, 0.47)),
                                    (1.0, (0.10, 0.13, 0.15))])
    img = _pil(arr).convert("RGBA")
    # bridge: deck across, a span fallen in the middle-left
    layer, d = _soft_layer(W, H)
    deck_y = int(H * 0.44)
    deck_col = (22, 28, 34, 255)
    dt = max(3, H // 10)
    # left deck (intact)
    d.polygon([(0, deck_y - dt), (int(W * 0.38), deck_y - dt),
               (int(W * 0.38), deck_y + dt), (0, deck_y + dt)], fill=deck_col)
    # right deck (intact)
    d.polygon([(int(W * 0.62), deck_y - dt), (W, deck_y - dt),
               (W, deck_y + dt), (int(W * 0.62), deck_y + dt)], fill=deck_col)
    # fallen span: a wide slab sloping down into the water
    d.polygon([(int(W * 0.38), deck_y - dt), (int(W * 0.50), deck_y + 2),
               (int(W * 0.54), int(H * 0.82)), (int(W * 0.44), int(H * 0.82))],
              fill=(16, 22, 28, 255))
    # bent steel pillars, bowed outward
    for fx, bend in ((0.16, 8), (0.30, -6), (0.72, 7), (0.88, -8)):
        x = int(W * fx)
        d.line([(x, deck_y + dt), (x + bend, int(H * 0.52))],
               fill=deck_col, width=max(2, H // 12))
    # warm rim light along the deck top
    d.line([(0, deck_y - dt), (int(W * 0.38), deck_y - dt)],
           fill=(255, 200, 140, 200), width=1)
    d.line([(int(W * 0.62), deck_y - dt), (W, deck_y - dt)],
           fill=(255, 200, 140, 200), width=1)
    # spray where the span fell: bright foam + droplets
    rng = _rng(seed + 7)
    for _ in range(40):
        x = int(W * 0.50 + rng.normal(0, W * 0.035))
        y = int(H * (0.54 + rng.random() * 0.12))
        r = int(rng.uniform(1, max(2, H * 0.07)))
        d.ellipse([x - r, y - r, x + r, y + r],
                  fill=(240, 245, 245, int(rng.uniform(140, 230))))
    img = _paste_soft(img, layer, blur=0.8)
    arr = _np(img.convert("RGB"))
    # smoke plume from the collapse
    n = _fbm(W, H, seed + 3, octaves=4, base=5)
    smoke = _smoothstep(n, 0.52, 0.75)
    band = np.zeros((H, 1))
    band[:int(H * 0.45)] = 1.0
    xs = np.linspace(0, 1, W)[None, :]
    plume = np.clip(1.0 - np.abs(xs - 0.50) / 0.16, 0, 1)
    a = smoke * band * plume * 0.55
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1 - a) + (0.45, 0.45, 0.46)[c] * a
    # reflect the deck + dawn light in the water
    arr = _reflect(arr, y0, strength=0.30, seed=seed + 11, wobble=4.0)
    _add_glow(arr, W * 0.30, H * 0.62, W * 0.10, (1.0, 0.85, 0.60), 0.35)
    _haze(arr, (0.72, 0.72, 0.70), 0.10, y0=0.0, y1=0.5)
    return _finish(arr, seed)


def _scene_2(W, H, seed):
    """Night at sea: a tanker burns, orange light on the water, a
    smoke trail, flashes in the sky."""
    arr = _vgrad(W, H, [(0.0, (0.02, 0.03, 0.07)),
                        (0.45, (0.05, 0.07, 0.14)),
                        (0.55, (0.08, 0.09, 0.15)),
                        (1.0, (0.02, 0.03, 0.06))])
    # stars
    rng = _rng(seed + 2)
    for _ in range(40):
        x = int(rng.uniform(0, W))
        y = int(rng.uniform(0, H * 0.35))
        v = rng.uniform(0.4, 1.0)
        r = 1 if rng.random() < 0.8 else 2
        arr[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] += v * 0.5
    # distant flash on the horizon
    _add_glow(arr, W * 0.82, H * 0.46, W * 0.12, (1.0, 0.75, 0.45), 0.5)
    # water base
    y0 = 0.52
    y0i = int(H * y0)
    arr[y0i:] = _vgrad(W, H - y0i, [(0.0, (0.05, 0.07, 0.10)),
                                    (1.0, (0.01, 0.02, 0.04))])
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # tanker silhouette, centre-left
    hx0, hx1 = int(W * 0.30), int(W * 0.68)
    hy = int(H * 0.50)
    d.polygon([(hx0, hy - 4), (hx1, hy - 4), (hx1 - 8, hy + 6),
               (hx0 + 8, hy + 6)], fill=(8, 9, 12, 255))
    # superstructure + funnel
    d.rectangle([int(W * 0.56), hy - 16, int(W * 0.63), hy - 4],
                fill=(10, 11, 15, 255))
    d.rectangle([int(W * 0.60), hy - 22, int(W * 0.63), hy - 16],
                fill=(12, 12, 16, 255))
    # flames on deck
    for fx, fh, fw in ((0.36, 0.20, 0.05), (0.44, 0.28, 0.06),
                       (0.52, 0.16, 0.04)):
        x = int(W * fx)
        top = int(hy - H * fh)
        d.polygon([(x - int(W * fw), hy - 4), (x, top),
                   (x + int(W * fw), hy - 4)], fill=(255, 140, 40, 255))
        d.polygon([(x - int(W * fw * 0.5), hy - 4), (x, top + int(H * 0.08)),
                   (x + int(W * fw * 0.5), hy - 4)],
                  fill=(255, 220, 120, 255))
    img = _paste_soft(img, layer, blur=0.8)
    arr = _np(img.convert("RGB"))
    # fire glow + reflection column in the water
    _add_glow(arr, W * 0.46, H * 0.48, W * 0.22, (1.0, 0.55, 0.15), 0.9)
    _add_glow(arr, W * 0.46, H * 0.48, W * 0.08, (1.0, 0.85, 0.45), 1.0)
    arr = _reflect(arr, y0, strength=0.35, seed=seed + 11, wobble=5.0)
    # orange reflection column under the fire
    yy, xx = np.mgrid[0:H, 0:W]
    rel = np.clip((yy - y0i) / max(1.0, H - y0i), 0, 1)
    wob = np.sin(rel * 20.0) * (4.0 + rel * 22.0)
    col = np.abs(xx - (W * 0.46 + wob)) / (W * 0.06 * (0.5 + rel))
    g = np.clip(1.0 - col, 0, 1) ** 2.0 * (1.0 - rel * 0.7)
    g[yy < y0i] = 0
    for c, v in enumerate((1.0, 0.55, 0.18)):
        arr[:, :, c] += g * v * 0.85
    # smoke trail, lit orange from below
    n = _fbm(W, H, seed + 3, octaves=4, base=5)
    smoke = _smoothstep(n, 0.55, 0.78)
    band = np.zeros((H, 1))
    band[:int(H * 0.48)] = 1.0
    xs = np.linspace(0, 1, W)[None, :]
    plume = np.clip(1.0 - np.abs(xs - 0.55) / 0.30, 0, 1)
    a = smoke * band * plume * 0.55
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1 - a) + (0.10, 0.09, 0.10)[c] * a
    _add_glow(arr, W * 0.50, H * 0.30, W * 0.20, (1.0, 0.5, 0.15), 0.25)
    return _finish(arr, seed)


def _scene_3(W, H, seed):
    """Conference hall: four podiums, four waving cloth flags,
    spotlights, a glossy floor."""
    arr = _vgrad(W, H, [(0.0, (0.16, 0.12, 0.08)),
                        (0.55, (0.42, 0.32, 0.20)),
                        (0.72, (0.30, 0.22, 0.14)),
                        (1.0, (0.10, 0.08, 0.06))])
    # warm spotlights from above
    for fx in (0.14, 0.38, 0.62, 0.86):
        _add_glow(arr, W * fx, 0, W * 0.10, (1.0, 0.88, 0.62), 0.5)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # light cones
    for fx in (0.14, 0.38, 0.62, 0.86):
        x = int(W * fx)
        d.polygon([(x - 4, 0), (x + 4, 0), (x + int(W * 0.06), int(H * 0.62)),
                   (x - int(W * 0.06), int(H * 0.62))],
                  fill=(255, 225, 160, 26))
    # wall panels
    d.rectangle([0, int(H * 0.52), W, int(H * 0.56)], fill=(60, 44, 28, 255))
    flags = [_flag_us, _flag_in, _flag_jp, _flag_au]
    fw, fh = int(W * 0.17), int(H * 0.30)
    floor_y = int(H * 0.72)
    for i, mk in enumerate(flags):
        cx = int(W * (0.14 + i * 0.24))
        # pole
        d.line([(cx, int(H * 0.10)), (cx, floor_y)], fill=(90, 70, 40, 255),
               width=max(1, W // 300))
        fimg = mk(fw, fh).convert("RGBA")
        fimg = _wavy(fimg, amp=max(1.0, H * 0.03), wavelength=max(8.0, fw * 0.9),
                     phase=i * 1.3)
        img.paste(fimg, (cx + 2, int(H * 0.12)), fimg)
    # glossy floor: soft vertical smears of the flag colours
    fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl)
    for i, col in enumerate(((178, 34, 52), (255, 153, 51),
                             (188, 0, 45), (0, 40, 104))):
        cx = int(W * (0.14 + i * 0.24))
        fd.rectangle([cx - 3, floor_y, cx + int(fw * 0.5), H],
                     fill=col + (36,))
    fl = fl.filter(ImageFilter.GaussianBlur(max(1, H // 12)))
    img.alpha_composite(fl)
    # podiums
    layer2, d2 = _soft_layer(W, H)
    for i in range(4):
        cx = int(W * (0.14 + i * 0.24))
        pw = int(W * 0.10)
        top = int(H * 0.60)
        d2.polygon([(cx - pw // 2, top), (cx + pw // 2, top),
                    (cx + pw // 2 - 4, floor_y), (cx - pw // 2 + 4, floor_y)],
                   fill=(52, 36, 22, 255))
        d2.rectangle([cx - pw // 2, top - 3, cx + pw // 2, top],
                     fill=(96, 68, 40, 255))
        d2.line([(cx + pw // 2 - 4, top - 3), (cx + pw // 2 + 2, top - 10)],
                fill=(180, 180, 180, 255), width=1)
    img = _paste_soft(img, layer, blur=1.0)
    img = _paste_soft(img, layer2, blur=0.8)
    # soft shadows under the podiums
    for i in range(4):
        cx = int(W * (0.14 + i * 0.24))
        img = _shadow(img, (cx - int(W * 0.07), floor_y - 2,
                            cx + int(W * 0.07), floor_y + 3),
                      blur=3, alpha=110)
    arr = _np(img.convert("RGB"))
    return _finish(arr, seed)


def _scene_4(W, H, seed):
    """Field hospital tent on foggy green hills, red cross sign,
    damp vapour."""
    arr = _vgrad(W, H, [(0.0, (0.78, 0.82, 0.78)),
                        (0.45, (0.72, 0.76, 0.70)),
                        (1.0, (0.32, 0.42, 0.30))])
    _add_glow(arr, W * 0.78, H * 0.18, W * 0.25, (1.0, 0.95, 0.80), 0.4)
    _clouds(arr, seed + 1, cover=0.55, soft=0.25,
            color=(0.95, 0.95, 0.93), y0=0.0, y1=0.30, strength=0.6)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # layered hills, hazier toward the back
    for (y0, amp, col) in ((0.42, 0.10, (0.62, 0.68, 0.58)),
                           (0.55, 0.12, (0.48, 0.56, 0.44)),
                           (0.68, 0.10, (0.36, 0.46, 0.34))):
        pts = [(0, H)]
        for x in range(0, W + 1, max(4, W // 40)):
            yy = H * y0 + np.sin(x / W * 6.0 + y0 * 20) * H * amp * 0.4
            pts.append((x, int(yy)))
        pts.append((W, H))
        d.polygon(pts, fill=_ci(col) + (255,))
    # tent: A-frame, cream, centre-left
    tx, ty = int(W * 0.34), int(H * 0.62)
    tw, th = int(W * 0.30), int(H * 0.34)
    d.polygon([(tx - tw // 2, ty), (tx, ty - th), (tx + tw // 2, ty)],
              fill=(238, 232, 214, 255))
    d.polygon([(tx, ty - th), (tx + tw // 2, ty), (tx + tw // 4, ty)],
              fill=(214, 206, 186, 255))
    d.line([(tx - tw // 2, ty), (tx, ty - th)], fill=(255, 250, 238, 255),
           width=2)
    # red cross sign
    sx, sy = tx, int(ty - th * 0.45)
    r = max(2, int(H * 0.07))
    d.rectangle([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 255, 255))
    d.rectangle([sx - r // 3, sy - r, sx + r // 3, sy + r],
                fill=(200, 30, 30, 255))
    d.rectangle([sx - r, sy - r // 3, sx + r, sy + r // 3],
                fill=(200, 30, 30, 255))
    img = _paste_soft(img, layer, blur=0.8)
    img = _shadow(img, (tx - tw // 2, ty - 1, tx + tw // 2, ty + 3),
                  blur=3, alpha=80)
    arr = _np(img.convert("RGB"))
    # damp vapour drifting across the hills
    n = _fbm(W, H, seed + 4, octaves=4, base=5)
    vap = _smoothstep(n, 0.58, 0.80) * 0.35
    band = np.zeros((H, 1))
    band[int(H * 0.35):int(H * 0.85)] = 1.0
    a = vap * band
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1 - a) + (0.88, 0.90, 0.88)[c] * a
    _haze(arr, (0.82, 0.85, 0.80), 0.16, y0=0.0, y1=0.6)
    return _finish(arr, seed)


def _scene_5(W, H, seed):
    """Wind turbines and gas pipes on a mountain coast at sunrise."""
    arr = _vgrad(W, H, [(0.0, (0.45, 0.55, 0.72)),
                        (0.42, (0.98, 0.72, 0.42)),
                        (0.55, (0.55, 0.48, 0.44)),
                        (1.0, (0.16, 0.22, 0.26))])
    _add_glow(arr, W * 0.62, H * 0.46, W * 0.30, (1.0, 0.75, 0.40), 0.7)
    _disc(arr, W * 0.62, H * 0.44, max(3.0, H * 0.09), (1.0, 0.88, 0.62))
    _clouds(arr, seed + 1, cover=0.5, soft=0.22,
            color=(1.0, 0.85, 0.70), y0=0.05, y1=0.38, strength=0.55)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # mountain coast, layered
    for (y0, amp, col) in ((0.48, 0.08, (0.42, 0.44, 0.52)),
                           (0.60, 0.10, (0.28, 0.32, 0.38))):
        pts = [(0, H)]
        for x in range(0, W + 1, max(4, W // 40)):
            yy = H * y0 + np.sin(x / W * 5.0 + y0 * 30) * H * amp
            pts.append((x, int(yy)))
        pts.append((W, H))
        d.polygon(pts, fill=_ci(col) + (255,))
    # sea strip with sunrise reflection
    sy = int(H * 0.66)
    d.rectangle([0, sy, W, H], fill=(0, 0, 0, 0))
    # wind turbines on the ridge
    for fx, s in ((0.22, 1.0), (0.42, 0.85), (0.80, 0.95)):
        x = int(W * fx)
        top = int(H * (0.60 - 0.30 * s))
        base = int(H * 0.68)
        d.line([(x, base), (x, top)], fill=(245, 245, 240, 255),
               width=max(2, int(H * 0.03)))
        bl = int(H * 0.16 * s)
        for ang in (90, 210, 330):
            a = np.deg2rad(ang + 25)
            d.line([(x, top), (x + int(np.cos(a) * bl),
                               top + int(np.sin(a) * bl))],
                   fill=(250, 250, 245, 255), width=max(1, int(H * 0.02)))
        d.ellipse([x - 3, top - 3, x + 3, top + 3], fill=(250, 250, 245, 255))
    # gas pipeline along the shore
    py = int(H * 0.74)
    d.rectangle([0, py, W, py + max(2, H // 16)], fill=(70, 66, 60, 255))
    d.line([(0, py), (W, py)], fill=(255, 190, 120, 200), width=1)
    for fx in (0.15, 0.45, 0.75):
        x = int(W * fx)
        d.rectangle([x - 2, py + max(2, H // 16), x + 2, int(H * 0.86)],
                    fill=(60, 56, 50, 255))
    img = _paste_soft(img, layer, blur=0.8)
    arr = _np(img.convert("RGB"))
    # sea: dark water with the sunrise column
    y0 = 0.66
    y0i = int(H * y0)
    arr[y0i:] = _vgrad(W, H - y0i, [(0.0, (0.30, 0.34, 0.38)),
                                    (1.0, (0.08, 0.10, 0.13))])
    # re-draw the pipeline over the water (it sits on the shore line)
    img = _pil(arr).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, py, W, py + max(2, H // 16)], fill=(70, 66, 60, 255))
    d.line([(0, py), (W, py)], fill=(255, 190, 120, 200), width=1)
    for fx in (0.15, 0.45, 0.75):
        x = int(W * fx)
        d.rectangle([x - 2, py + max(2, H // 16), x + 2, int(H * 0.86)],
                    fill=(60, 56, 50, 255))
    arr = _np(img.convert("RGB"))
    arr = _reflect(arr, y0, strength=0.28, seed=seed + 11, wobble=4.0)
    _add_glow(arr, W * 0.62, H * 0.72, W * 0.08, (1.0, 0.75, 0.40), 0.5)
    return _finish(arr, seed)


def _scene_6(W, H, seed):
    """Vaccine ampoule and syringe close-up on a table, bokeh
    background, glass reflection."""
    arr = _vgrad(W, H, [(0.0, (0.16, 0.18, 0.24)),
                        (0.6, (0.24, 0.26, 0.32)),
                        (1.0, (0.10, 0.11, 0.14))])
    _add_glow(arr, W * 0.80, H * 0.25, W * 0.25, (0.9, 0.95, 1.0), 0.35)
    img = _pil(arr).convert("RGBA")
    img = _bokeh(img, seed + 1, count=14, color=(1.0, 0.9, 0.7),
                 rmin=max(3, H // 14), rmax=max(6, H // 6), alpha=60)
    img = _bokeh(img, seed + 2, count=8, color=(0.65, 0.8, 1.0),
                 rmin=max(3, H // 14), rmax=max(6, H // 7), alpha=50)
    # table surface
    d = ImageDraw.Draw(img)
    ty = int(H * 0.72)
    d.rectangle([0, ty, W, H], fill=(52, 56, 64, 255))
    d.line([(0, ty), (W, ty)], fill=(200, 205, 215, 160), width=1)
    layer, d = _soft_layer(W, H)
    # ampoule: glass vial, standing left, larger so it reads
    ax = int(W * 0.28)
    aw, ah = int(W * 0.12), int(H * 0.60)
    ay = ty - ah
    d.rounded_rectangle([ax - aw // 2, ay, ax + aw // 2, ty],
                        radius=max(2, aw // 3), fill=(205, 220, 230, 225))
    d.rectangle([ax - aw // 4, ay - int(H * 0.10), ax + aw // 4, ay],
                fill=(205, 220, 230, 225))
    d.rounded_rectangle([ax - aw // 2 + 2, ay + ah // 2, ax + aw // 2 - 2,
                         ty - 2], radius=2, fill=(110, 165, 200, 170))
    d.line([(ax - aw // 2 + 2, ay + 4), (ax - aw // 2 + 2, ty - 4)],
           fill=(255, 255, 255, 235), width=2)
    # syringe: lying diagonally, right side, thick barrel
    sx0, sy0 = int(W * 0.46), int(ty - H * 0.08)
    sx1, sy1 = int(W * 0.92), int(ty - H * 0.30)
    bw = max(6, H // 5)
    d.line([(sx0, sy0), (sx1, sy1)], fill=(215, 225, 235, 245), width=bw)
    d.line([(sx0, sy0 - bw // 3), (sx1, sy1 - bw // 3)],
           fill=(255, 255, 255, 200), width=max(1, bw // 4))
    # plunger + needle
    d.line([(sx0 - 8, sy0 + 3), (sx0 + 2, sy0 - 1)], fill=(240, 240, 240, 255),
           width=max(3, H // 10))
    d.line([(sx1, sy1), (sx1 + int(W * 0.06), sy1 - int(H * 0.06))],
           fill=(220, 225, 230, 255), width=1)
    # measurement ticks on the barrel
    for t in np.linspace(0.15, 0.85, 5):
        x = int(sx0 + (sx1 - sx0) * t)
        y = int(sy0 + (sy1 - sy0) * t)
        d.line([(x, y - 3), (x, y + 3)], fill=(90, 100, 110, 200), width=1)
    img = _paste_soft(img, layer, blur=0.7)
    # soft reflections on the table
    arr = _np(img.convert("RGB"))
    _add_glow(arr, W * 0.30, H * 0.80, W * 0.08, (0.7, 0.8, 0.9), 0.25)
    return _finish(arr, seed)


def _scene_7(W, H, seed):
    """Die chip close-up: metal circuit traces, metallic reflection,
    green light."""
    arr = _vgrad(W, H, [(0.0, (0.03, 0.04, 0.05)),
                        (1.0, (0.05, 0.06, 0.08))])
    _add_glow(arr, W * 0.85, H * 0.10, W * 0.30, (0.2, 0.9, 0.45), 0.5)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # the die fills the frame
    d.rectangle([0, 0, W, H], fill=(16, 19, 24, 255))
    # circuit traces: a grid of metallic lines + pads
    rng = _rng(seed + 3)
    for gy in range(1, 5):
        y = int(H * gy / 5)
        d.line([(0, y), (W, y)], fill=(120, 110, 80, 255), width=1)
    for gx in range(1, 9):
        x = int(W * gx / 9)
        d.line([(x, 0), (x, H)], fill=(120, 110, 80, 255), width=1)
    for _ in range(26):
        x = int(rng.uniform(0, W))
        y = int(rng.uniform(0, H))
        s = int(rng.uniform(2, max(3, H // 10)))
        col = (200, 170, 90, 255) if rng.random() < 0.5 else (170, 180, 190, 255)
        d.rectangle([x, y, x + s, y + s], fill=col)
    # a denser logic block, centre-left
    bx, by = int(W * 0.30), int(H * 0.28)
    bw, bh = int(W * 0.34), int(H * 0.44)
    d.rectangle([bx, by, bx + bw, by + bh], outline=(150, 160, 170, 255),
                width=1)
    for i in range(6):
        y = by + int(bh * (i + 1) / 7)
        d.line([(bx + 3, y), (bx + bw - 3, y)], fill=(190, 160, 90, 255),
               width=1)
    for i in range(8):
        x = bx + int(bw * (i + 1) / 9)
        d.line([(x, by + 3), (x, by + bh - 3)], fill=(160, 170, 180, 255),
               width=1)
    # metallic diagonal reflection
    d.polygon([(int(W * 0.55), 0), (int(W * 0.75), 0), (int(W * 0.35), H),
               (int(W * 0.15), H)], fill=(255, 255, 255, 26))
    img = _paste_soft(img, layer, blur=0.6)
    arr = _np(img.convert("RGB"))
    _add_glow(arr, W * 0.85, H * 0.12, W * 0.22, (0.25, 0.95, 0.5), 0.45)
    return _finish(arr, seed)


def _scene_8(W, H, seed):
    """A row of refugee tents in the rain, mud and puddles reflecting
    the sky, an aid truck in the distance."""
    arr = _vgrad(W, H, [(0.0, (0.32, 0.34, 0.36)),
                        (0.45, (0.52, 0.54, 0.54)),
                        (1.0, (0.30, 0.27, 0.24))])
    _clouds(arr, seed + 1, cover=0.6, soft=0.25,
            color=(0.62, 0.63, 0.63), y0=0.0, y1=0.30, strength=0.7)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # muddy ground
    gy = int(H * 0.58)
    d.rectangle([0, gy, W, H], fill=(88, 74, 60, 255))
    # tents receding to the right
    for i, (fx, s) in enumerate(((0.12, 1.0), (0.34, 0.8), (0.54, 0.62),
                                 (0.72, 0.48))):
        x = int(W * fx)
        tw = int(W * 0.20 * s)
        th = int(H * 0.34 * s)
        d.polygon([(x - tw // 2, gy), (x, gy - th), (x + tw // 2, gy)],
                  fill=(168, 158, 138, 255))
        d.polygon([(x, gy - th), (x + tw // 2, gy), (x + tw // 4, gy)],
                  fill=(138, 128, 110, 255))
    # aid truck in the distance, right
    tx, ty = int(W * 0.86), int(H * 0.56)
    d.rectangle([tx - 14, ty - 10, tx + 14, ty], fill=(120, 110, 90, 255))
    d.rectangle([tx + 14, ty - 7, tx + 22, ty], fill=(110, 100, 82, 255))
    d.ellipse([tx - 10, ty - 2, tx - 4, ty + 4], fill=(20, 20, 20, 255))
    d.ellipse([tx + 4, ty - 2, tx + 10, ty + 4], fill=(20, 20, 20, 255))
    d.ellipse([tx + 18, ty - 1, tx + 21, ty + 2], fill=(255, 220, 140, 255))
    # puddles reflecting the grey sky
    for (fx, fw) in ((0.22, 0.16), (0.55, 0.20), (0.80, 0.12)):
        x = int(W * fx)
        pw = int(W * fw)
        py = int(H * (0.72 + 0.10 * (fx % 0.5)))
        d.ellipse([x - pw // 2, py - 3, x + pw // 2, py + 3],
                  fill=(150, 158, 162, 220))
        d.ellipse([x - pw // 3, py - 1, x + pw // 3, py + 1],
                  fill=(190, 196, 198, 200))
    img = _paste_soft(img, layer, blur=0.8)
    arr = _np(img.convert("RGB"))
    # rain streaks, diagonal, slightly blurred
    rain = np.zeros((H, W))
    rng = _rng(seed + 6)
    for _ in range(90):
        x = int(rng.uniform(0, W))
        y = int(rng.uniform(0, H))
        ln = int(rng.uniform(H * 0.10, H * 0.22))
        rain[max(0, y):min(H, y + ln), x] += 0.35
    rain_img = Image.fromarray((np.clip(rain, 0, 1) * 255).astype(np.uint8))
    rain_img = rain_img.filter(ImageFilter.GaussianBlur(0.6))
    rain = np.asarray(rain_img, dtype=np.float64) / 255.0
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + rain * 0.25, 0, 1)
    return _finish(arr, seed)


def _scene_9(W, H, seed):
    """Two fighter jets in formation above a sea of clouds, dusk
    light, condensation trails."""
    arr = _vgrad(W, H, [(0.0, (0.10, 0.14, 0.30)),
                        (0.35, (0.45, 0.30, 0.42)),
                        (0.48, (0.95, 0.60, 0.35)),
                        (1.0, (0.55, 0.48, 0.50))])
    _add_glow(arr, W * 0.68, H * 0.44, W * 0.28, (1.0, 0.65, 0.35), 0.6)
    _disc(arr, W * 0.68, H * 0.42, max(3.0, H * 0.08), (1.0, 0.85, 0.60))
    # sea of clouds: textured billows, warm on top
    n = _fbm(W, H, seed + 1, octaves=5, base=4)
    cy0 = int(H * 0.48)
    cloud = _smoothstep(n, 0.42, 0.62)
    # the cloud top edge is a wavy line
    top = np.array([cy0 + int(np.sin(x / W * 9.0 + 0.7) * H * 0.05)
                    for x in range(W)])
    yy = np.arange(H)[:, None]
    below = (yy >= top[None, :]).astype(float)
    a = cloud * below
    # warm light on the cloud tops, shadowed below
    warm = np.clip(1.0 - (yy - top[None, :]) / max(1.0, H * 0.3), 0, 1)
    warm_rgb = (1.0, 0.75, 0.5)
    shadow_rgb = (0.55, 0.50, 0.55)
    for c in range(3):
        arr[:, :, c] = (arr[:, :, c] * (1 - a)
                        + (warm_rgb[c] * warm
                           + shadow_rgb[c] * (1 - warm)) * a)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # condensation trails, fading behind the jets
    for (jy, off) in ((0.30, 0.0), (0.38, 0.06)):
        y = int(H * jy)
        x0 = int(W * (0.30 + off))
        x1 = int(W * (0.58 + off))
        d.line([(x0, y), (x1, y + 2)], fill=(255, 255, 255, 150), width=2)
        d.line([(x0, y + 3), (x1, y + 5)], fill=(255, 255, 255, 90), width=1)
    # two jets in formation, dark silhouettes
    for (jx, jy, s) in ((0.62, 0.30, 1.0), (0.70, 0.38, 0.82)):
        x, y = int(W * jx), int(H * jy)
        L = int(W * 0.075 * s)
        d.polygon([(x - L, y), (x + L // 2, y - 2), (x + L, y),
                   (x + L // 2, y + 2)], fill=(12, 12, 16, 255))
        d.polygon([(x, y - 2), (x + int(L * 0.45), y - int(L * 0.42)),
                   (x + int(L * 0.55), y - 2)], fill=(12, 12, 16, 255))
        d.polygon([(x, y + 2), (x + int(L * 0.45), y + int(L * 0.42)),
                   (x + int(L * 0.55), y + 2)], fill=(12, 12, 16, 255))
        d.polygon([(x - L, y - 1), (x - int(L * 0.75), y - int(L * 0.30)),
                   (x - int(L * 0.70), y - 1)], fill=(12, 12, 16, 255))
    img = _paste_soft(img, layer, blur=0.6)
    arr = _np(img.convert("RGB"))
    return _finish(arr, seed)


def _scene_10(W, H, seed):
    """Wooden judge gavel and court table close-up, thin depth of
    field, window light."""
    arr = _vgrad(W, H, [(0.0, (0.20, 0.17, 0.13)),
                        (0.6, (0.32, 0.27, 0.20)),
                        (1.0, (0.12, 0.10, 0.08))])
    # window light, top-left
    _add_glow(arr, W * 0.18, H * 0.15, W * 0.30, (1.0, 0.9, 0.7), 0.55)
    img = _pil(arr)
    img = img.filter(ImageFilter.GaussianBlur(max(1, H // 10)))
    img = img.convert("RGBA")
    # window frame, softly blurred
    d = ImageDraw.Draw(img)
    d.rectangle([int(W * 0.06), int(H * 0.04), int(W * 0.30), int(H * 0.55)],
                fill=(235, 215, 170, 200))
    d.line([(int(W * 0.18), int(H * 0.04)), (int(W * 0.18), int(H * 0.55))],
           fill=(90, 70, 50, 200), width=2)
    img = img.filter(ImageFilter.GaussianBlur(max(1, H // 16)))
    d = ImageDraw.Draw(img)
    # table: polished dark wood
    ty = int(H * 0.62)
    d.rectangle([0, ty, W, H], fill=(58, 38, 24, 255))
    d.rectangle([0, ty, W, ty + 2], fill=(150, 105, 60, 255))
    layer, d = _soft_layer(W, H)
    # sounding block
    bx, by = int(W * 0.42), int(H * 0.74)
    br = int(W * 0.11)
    d.ellipse([bx - br, by - br // 3, bx + br, by + br // 3],
              fill=(96, 62, 34, 255))
    d.ellipse([bx - br, by - br // 3, bx + br, by - br // 3 + 3],
              fill=(140, 95, 55, 255))
    # gavel: head + handle, diagonal, warm wood lit by the window
    hx, hy = bx, by - int(H * 0.06)
    ang = np.deg2rad(-18)
    ca, sa = np.cos(ang), np.sin(ang)
    def rot(px, py):
        return (hx + px * ca - py * sa, hy + px * sa + py * ca)
    hw, hh = int(W * 0.16), int(H * 0.20)
    head = [rot(-hw, -hh), rot(hw, -hh), rot(hw, hh), rot(-hw, hh)]
    d.polygon(head, fill=(168, 118, 66, 255))
    d.polygon([rot(-hw, -hh), rot(hw, -hh), rot(hw, -hh + 4),
               rot(-hw, -hh + 4)], fill=(222, 168, 104, 255))
    # handle
    hl = int(W * 0.32)
    d.polygon([rot(hw - 4, -4), rot(hw + hl, -4), rot(hw + hl, 4),
               rot(hw - 4, 4)], fill=(140, 96, 54, 255))
    # wood grain streaks on the head
    for t in (-0.5, 0.0, 0.5):
        p0 = rot(-hw + 3, int(hh * t))
        p1 = rot(hw - 3, int(hh * t))
        d.line([p0, p1], fill=(90, 58, 30, 160), width=1)
    img = _paste_soft(img, layer, blur=0.6)
    img = _shadow(img, (bx - br, by + br // 4, bx + br, by + br // 2),
                  blur=3, alpha=100)
    arr = _np(img.convert("RGB"))
    _add_glow(arr, W * 0.42, H * 0.68, W * 0.14, (1.0, 0.85, 0.6), 0.3)
    return _finish(arr, seed)


def _scene_11(W, H, seed):
    """Phone with a cloud icon and a loading spinner, glossy screen
    and reflection."""
    arr = _vgrad(W, H, [(0.0, (0.22, 0.22, 0.26)),
                        (0.6, (0.30, 0.30, 0.34)),
                        (1.0, (0.12, 0.12, 0.15))])
    img = _pil(arr).convert("RGBA")
    img = _bokeh(img, seed + 1, count=10, color=(1.0, 0.9, 0.7),
                 rmin=max(3, H // 14), rmax=max(6, H // 6), alpha=55)
    d = ImageDraw.Draw(img)
    # surface
    ty = int(H * 0.78)
    d.rectangle([0, ty, W, H], fill=(40, 40, 46, 255))
    d.line([(0, ty), (W, ty)], fill=(180, 185, 195, 140), width=1)
    layer, d = _soft_layer(W, H)
    # phone, standing centre, slight tilt
    px, py = int(W * 0.50), int(H * 0.10)
    pw, ph = int(W * 0.26), int(H * 0.72)
    d.rounded_rectangle([px - pw // 2, py, px + pw // 2, py + ph],
                        radius=max(3, pw // 8), fill=(18, 18, 22, 255))
    d.rounded_rectangle([px - pw // 2 + 3, py + 3, px + pw // 2 - 3,
                         py + ph - 3], radius=max(2, pw // 10),
                        fill=(90, 140, 200, 255))
    # screen gradient
    for yy in range(py + 3, py + ph - 3):
        t = (yy - py) / max(1, ph)
        col = (int(90 + 60 * t), int(140 + 40 * t), int(200 + 30 * t), 255)
        d.line([(px - pw // 2 + 3, yy), (px + pw // 2 - 3, yy)], fill=col)
    # cloud icon
    cx, cy = px, py + int(ph * 0.34)
    cr = max(3, int(pw * 0.16))
    d.ellipse([cx - cr, cy - cr // 2, cx + cr, cy + cr // 2],
              fill=(255, 255, 255, 255))
    d.ellipse([cx - cr // 2, cy - cr, cx + cr // 2, cy + cr // 2],
              fill=(255, 255, 255, 255))
    # loading spinner: an arc below the cloud
    sx, sy = px, py + int(ph * 0.62)
    sr = max(4, int(pw * 0.16))
    d.arc([sx - sr, sy - sr, sx + sr, sy + sr], start=200, end=20,
          fill=(255, 255, 255, 255), width=max(2, H // 18))
    d.ellipse([sx + int(sr * 0.9), sy - 2, sx + int(sr * 0.9) + 3, sy + 1],
              fill=(255, 255, 255, 255))
    # glossy streak across the screen
    d.polygon([(px - pw // 2 + 4, py + ph - 4),
               (px - pw // 2 + int(pw * 0.35), py + 3),
               (px - pw // 2 + int(pw * 0.55), py + 3),
               (px - pw // 2 + int(pw * 0.20), py + ph - 4)],
              fill=(255, 255, 255, 40))
    img = _paste_soft(img, layer, blur=0.6)
    # reflection of the phone on the surface
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    rd.rounded_rectangle([px - pw // 2, ty, px + pw // 2, ty + int(ph * 0.22)],
                         radius=max(2, pw // 10), fill=(90, 140, 200, 70))
    refl = refl.filter(ImageFilter.GaussianBlur(max(1, H // 20)))
    img.alpha_composite(refl)
    img = _shadow(img, (px - pw // 2, ty - 2, px + pw // 2, ty + 3),
                  blur=3, alpha=110)
    arr = _np(img.convert("RGB"))
    _add_glow(arr, W * 0.50, H * 0.40, W * 0.16, (0.55, 0.75, 1.0), 0.4)
    return _finish(arr, seed)


def _scene_12(W, H, seed):
    """Oil pipeline in the desert at dusk, pumping station, drone
    silhouettes in the sky."""
    arr = _vgrad(W, H, [(0.0, (0.22, 0.16, 0.34)),
                        (0.40, (0.85, 0.45, 0.28)),
                        (0.52, (0.98, 0.62, 0.30)),
                        (1.0, (0.45, 0.30, 0.20))])
    _add_glow(arr, W * 0.30, H * 0.48, W * 0.26, (1.0, 0.65, 0.30), 0.65)
    _disc(arr, W * 0.30, H * 0.46, max(3.0, H * 0.08), (1.0, 0.82, 0.55))
    _clouds(arr, seed + 1, cover=0.5, soft=0.22,
            color=(0.95, 0.70, 0.55), y0=0.05, y1=0.35, strength=0.5)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # dunes
    for (y0, amp, col) in ((0.52, 0.08, (0.72, 0.52, 0.34)),
                           (0.66, 0.10, (0.58, 0.40, 0.26))):
        pts = [(0, H)]
        for x in range(0, W + 1, max(4, W // 40)):
            yy = H * y0 + np.sin(x / W * 4.0 + y0 * 25) * H * amp
            pts.append((x, int(yy)))
        pts.append((W, H))
        d.polygon(pts, fill=_ci(col) + (255,))
    # pumping station, mid-distance right
    sx = int(W * 0.72)
    sy = int(H * 0.60)
    d.rectangle([sx, sy - int(H * 0.14), sx + int(W * 0.10), sy],
                fill=(52, 44, 38, 255))
    d.ellipse([sx + 4, sy - int(H * 0.20), sx + int(W * 0.05),
               sy - int(H * 0.14)], fill=(70, 60, 50, 255))
    d.rectangle([sx + int(W * 0.11), sy - int(H * 0.10),
                 sx + int(W * 0.15), sy], fill=(60, 52, 44, 255))
    # pipeline across the frame
    py = int(H * 0.72)
    d.rectangle([0, py, W, py + max(2, H // 14)], fill=(48, 42, 36, 255))
    d.line([(0, py), (W, py)], fill=(255, 180, 110, 220), width=1)
    for fx in (0.12, 0.38, 0.64, 0.90):
        x = int(W * fx)
        d.rectangle([x - 2, py + max(2, H // 14), x + 2, int(H * 0.88)],
                    fill=(40, 34, 28, 255))
    # drones in the sky
    for (fx, fy, s) in ((0.55, 0.16, 1.0), (0.68, 0.10, 0.8),
                        (0.80, 0.22, 0.9)):
        x, y = int(W * fx), int(H * fy)
        r = max(2, int(W * 0.012 * s))
        d.line([(x - r * 2, y - r), (x + r * 2, y + r)], fill=(10, 8, 12, 255),
               width=1)
        d.line([(x - r * 2, y + r), (x + r * 2, y - r)], fill=(10, 8, 12, 255),
               width=1)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(10, 8, 12, 255))
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(255, 80, 60, 255))
    img = _paste_soft(img, layer, blur=0.8)
    arr = _np(img.convert("RGB"))
    return _finish(arr, seed)


def _scene_13(W, H, seed):
    """Silicon wafer with rainbow diffraction sheen and light
    reflection."""
    arr = _vgrad(W, H, [(0.0, (0.04, 0.04, 0.06)),
                        (1.0, (0.07, 0.07, 0.10))])
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # the wafer fills the frame: a large circle, mostly out of frame
    cx, cy = int(W * 0.50), int(H * 1.15)
    R = int(W * 0.62)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(28, 30, 38, 255))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(120, 125, 140, 255),
              width=2)
    img = _paste_soft(img, layer, blur=0.6)
    arr = _np(img.convert("RGB"))
    # rainbow diffraction: interference bands across the wafer
    yy, xx = np.mgrid[0:H, 0:W]
    ph = (xx / W * 3.0 + yy / H * 1.5 + np.sin(xx / W * 9.0) * 0.35)
    r = 0.5 + 0.5 * np.sin(ph * 6.283)
    g = 0.5 + 0.5 * np.sin(ph * 6.283 + 2.094)
    b = 0.5 + 0.5 * np.sin(ph * 6.283 + 4.188)
    # only on the wafer disc: a sheen, not a solid rainbow
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / R
    mask = np.clip(1.0 - dist, 0, 1) ** 0.5 * 0.32
    for c, ch in enumerate((r, g, b)):
        arr[:, :, c] = arr[:, :, c] * (1 - mask) + ch * mask
    # faint die grid on the wafer
    for gx in range(1, 12):
        x = int(W * gx / 12)
        arr[:, x - 1:x + 1] = arr[:, x - 1:x + 1] * 0.7 + 0.12
    for gy in range(1, 5):
        y = int(H * gy / 5)
        arr[y - 1:y + 1, :] = arr[y - 1:y + 1, :] * 0.7 + 0.12
    # bright specular reflection
    _add_glow(arr, W * 0.32, H * 0.28, W * 0.16, (1.0, 1.0, 1.0), 0.7)
    _disc(arr, W * 0.32, H * 0.28, max(2.0, H * 0.06), (1.0, 1.0, 1.0))
    return _finish(arr, seed)


def _scene_14(W, H, seed):
    """Government building with pillars under a vast steppe sky,
    dramatic clouds."""
    arr = _vgrad(W, H, [(0.0, (0.35, 0.48, 0.66)),
                        (0.45, (0.75, 0.78, 0.82)),
                        (0.60, (0.78, 0.72, 0.58)),
                        (1.0, (0.42, 0.38, 0.26))])
    _add_glow(arr, W * 0.72, H * 0.30, W * 0.30, (1.0, 0.9, 0.7), 0.55)
    _clouds(arr, seed + 1, cover=0.42, soft=0.20,
            color=(1.0, 1.0, 1.0), y0=0.0, y1=0.42, strength=0.85)
    _clouds(arr, seed + 2, cover=0.62, soft=0.18,
            color=(0.55, 0.56, 0.60), y0=0.18, y1=0.48, strength=0.5)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    # steppe: flat golden grass to the horizon
    hy = int(H * 0.58)
    d.rectangle([0, hy, W, H], fill=(0, 0, 0, 0))
    pts = [(0, H), (0, hy + 4)]
    for x in range(0, W + 1, max(4, W // 40)):
        pts.append((x, int(hy + np.sin(x / W * 5.0) * 2)))
    pts.append((W, H))
    d.polygon(pts, fill=(168, 148, 92, 255))
    # the building: pediment + row of pillars, centre, larger
    bx = int(W * 0.50)
    bw = int(W * 0.52)
    base = int(H * 0.90)
    top = int(H * 0.56)
    d.polygon([(bx - bw // 2, top), (bx + bw // 2, top), (bx, top - int(H * 0.10))],
              fill=(232, 224, 204, 255))
    d.rectangle([bx - bw // 2, top, bx + bw // 2, base],
                fill=(214, 204, 182, 255))
    d.rectangle([bx - bw // 2 - 4, base, bx + bw // 2 + 4, base + 4],
                fill=(190, 178, 152, 255))
    # pillars
    for i in range(5):
        x = int(bx - bw // 2 + bw * (i + 0.5) / 5)
        d.rectangle([x - 3, top + 2, x + 3, base], fill=(240, 232, 212, 255))
        d.line([(x - 3, top + 2), (x - 3, base)], fill=(255, 250, 235, 255),
               width=1)
    # long shadows on the grass
    d.polygon([(bx - bw // 2, base + 4), (bx + bw // 2, base + 4),
               (bx + bw // 2 + int(W * 0.10), H),
               (bx - bw // 2 - int(W * 0.06), H)], fill=(120, 105, 62, 160))
    img = _paste_soft(img, layer, blur=0.8)
    arr = _np(img.convert("RGB"))
    _haze(arr, (0.85, 0.85, 0.82), 0.12, y0=0.45, y1=0.62)
    return _finish(arr, seed)


def _scene_15(W, H, seed):
    """Snowy taiga forest, a smoke plume from a small plane wreck
    in the distance, cold fog."""
    arr = _vgrad(W, H, [(0.0, (0.62, 0.68, 0.74)),
                        (0.45, (0.72, 0.76, 0.78)),
                        (1.0, (0.82, 0.84, 0.86))])
    _clouds(arr, seed + 1, cover=0.6, soft=0.25,
            color=(0.92, 0.93, 0.94), y0=0.0, y1=0.28, strength=0.6)
    img = _pil(arr).convert("RGBA")
    layer, d = _soft_layer(W, H)
    rng = _rng(seed + 3)
    # layered forest: back row small and hazy, front row large
    for (y0, smin, smax, col) in ((0.42, 0.05, 0.09, (0.42, 0.52, 0.50)),
                                  (0.55, 0.08, 0.14, (0.28, 0.40, 0.36)),
                                  (0.68, 0.13, 0.20, (0.16, 0.28, 0.24))):
        for _ in range(16):
            x = int(rng.uniform(0, W))
            s = rng.uniform(smin, smax)
            tw = int(W * s)
            th = int(H * s * 2.2)
            yb = int(H * y0 + rng.uniform(0, H * 0.12))
            d.polygon([(x - tw // 2, yb), (x, yb - th), (x + tw // 2, yb)],
                      fill=_ci(col) + (255,))
            # snow on the branches
            for k in (0.35, 0.6, 0.85):
                yy = int(yb - th * k)
                ww = int(tw * (1 - k) * 0.5)
                d.line([(x - ww, yy), (x + ww, yy)],
                       fill=(235, 240, 242, 200), width=1)
    # snow ground
    d.rectangle([0, int(H * 0.82), W, H], fill=(228, 234, 238, 255))
    # the wreck: a small dark shape in the mid-distance
    wx, wy = int(W * 0.62), int(H * 0.66)
    d.polygon([(wx - 12, wy), (wx + 10, wy - 4), (wx + 16, wy + 2),
               (wx - 6, wy + 4)], fill=(22, 22, 24, 255))
    d.polygon([(wx + 8, wy - 4), (wx + 20, wy - 12), (wx + 22, wy - 8),
               (wx + 12, wy)], fill=(30, 30, 32, 255))
    img = _paste_soft(img, layer, blur=0.8)
    arr = _np(img.convert("RGB"))
    # smoke plume from the wreck, drifting
    n = _fbm(W, H, seed + 5, octaves=4, base=5)
    smoke = _smoothstep(n, 0.55, 0.78)
    band = np.zeros((H, 1))
    band[:int(H * 0.62)] = 1.0
    xs = np.linspace(0, 1, W)[None, :]
    plume = np.clip(1.0 - np.abs(xs - 0.62) / 0.20, 0, 1)
    a = smoke * band * plume * 0.5
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1 - a) + (0.25, 0.25, 0.26)[c] * a
    # cold fog between the trees
    n2 = _fbm(W, H, seed + 6, octaves=4, base=5)
    fog = _smoothstep(n2, 0.60, 0.82) * 0.30
    band2 = np.zeros((H, 1))
    band2[int(H * 0.45):int(H * 0.85)] = 1.0
    a2 = fog * band2
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1 - a2) + (0.85, 0.88, 0.90)[c] * a2
    return _finish(arr, seed)


# ------------------------------------------------------------------
# public entry point
# ------------------------------------------------------------------

_SCENES = {
    1: _scene_1, 2: _scene_2, 3: _scene_3, 4: _scene_4, 5: _scene_5,
    6: _scene_6, 7: _scene_7, 8: _scene_8, 9: _scene_9, 10: _scene_10,
    11: _scene_11, 12: _scene_12, 13: _scene_13, 14: _scene_14,
    15: _scene_15,
}


def render_scene(card_id, w, h):
    """Render card_id's scene at (w, h) device pixels.

    Renders at 2x and downscales (LANCZOS) for antialiasing. The
    seed is fixed per card, so the result is deterministic.
    """
    W, H = max(2, int(w) * 2), max(2, int(h) * 2)
    seed = BASE_SEED + int(card_id) * 7919
    img = _SCENES[int(card_id)](W, H, seed)
    return img.resize((int(w), int(h)), Image.LANCZOS)
