#!/usr/bin/env python3
"""Generate standalone premium CTA illustrations (420×330 RGBA WebP).

Designed as a cohesive pack — not crops from legacy hero artwork.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "static" / "images" / "premium-cta" / "icons"
SRC_DIR = ROOT / "static" / "images" / "premium-cta" / "sources"

W, H = 420, 330
SCALE = 4  # supersample for crisp edges


# Peyvand-aligned palette (matches legacy 3D hero art direction)
NAVY = (27, 85, 131)
NAVY_DARK = (11, 45, 74)
NAVY_MID = (23, 53, 82)
TAN = (201, 149, 94)
TAN_DARK = (166, 118, 68)
TAN_LIGHT = (232, 196, 150)
CREAM = (255, 252, 245)
PAPER = (248, 244, 236)
BLUE = (43, 123, 191)
BLUE_DARK = (27, 85, 131)
GOLD = (245, 197, 66)
GOLD_DARK = (232, 168, 32)
ORANGE = (245, 160, 80)
ORANGE_DARK = (232, 120, 48)
RED = (232, 69, 69)
RED_DARK = (201, 48, 48)
WHITE = (255, 255, 255)
SILVER = (196, 204, 214)
GREEN = (91, 199, 100)
GREEN_DARK = (67, 168, 76)
SHADOW = (11, 45, 74, 72)


def _size(w: int = W, h: int = H) -> tuple[int, int]:
    return w * SCALE, h * SCALE


def _canvas() -> Image.Image:
    return Image.new("RGBA", _size(), (0, 0, 0, 0))


def _draw(size: Image.Image) -> ImageDraw.ImageDraw:
    return ImageDraw.Draw(size)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _lerp_color(c1: tuple[int, ...], c2: tuple[int, ...], t: float) -> tuple[int, int, int]:
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


def linear_gradient(size: tuple[int, int], c1: tuple[int, int, int], c2: tuple[int, int, int], vertical: bool = True) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = y / max(h - 1, 1) if vertical else x / max(w - 1, 1)
            r, g, b = _lerp_color(c1, c2, t)
            px[x, y] = (r, g, b, 255)
    return img


def radial_gradient(size: tuple[int, int], inner: tuple[int, int, int], outer: tuple[int, int, int]) -> Image.Image:
    w, h = size
    cx, cy = w / 2, h / 2
    max_r = math.hypot(cx, cy)
    img = Image.new("RGBA", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = min(math.hypot(x - cx, y - cy) / max_r, 1.0)
            r, g, b = _lerp_color(inner, outer, t)
            px[x, y] = (r, g, b, 255)
    return img


def rounded_shape(
    box: tuple[int, int, int, int],
    radius: int,
    fill: Image.Image | tuple[int, int, int, int],
) -> Image.Image:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    shape = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if isinstance(fill, tuple):
        fill_img = Image.new("RGBA", (w, h), fill)
    else:
        fill_img = fill.resize((w, h), Image.Resampling.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    shape.paste(fill_img, (0, 0), mask)
    return shape


def paste(canvas: Image.Image, layer: Image.Image, xy: tuple[int, int]) -> None:
    canvas.alpha_composite(layer, xy)


def glossy_spot(canvas: Image.Image, cx: int, cy: int, rw: int, rh: int, alpha: int = 55) -> None:
    spot = Image.new("RGBA", (rw * 2, rh * 2), (0, 0, 0, 0))
    ImageDraw.Draw(spot).ellipse((0, 0, rw * 2 - 1, rh * 2 - 1), fill=(255, 255, 255, alpha))
    spot = spot.filter(ImageFilter.GaussianBlur(int(6 * SCALE)))
    paste(canvas, spot, (cx - rw, cy - rh))


def stroke_ring(canvas: Image.Image, cx: int, cy: int, r: int, thickness: int, color: tuple[int, int, int]) -> None:
    pad = thickness + int(8 * SCALE)
    size = (r * 2 + pad * 2, r * 2 + pad * 2)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bbox = (pad, pad, pad + r * 2, pad + r * 2)
    d.ellipse(bbox, outline=(*color, 255), width=thickness)
    paste(canvas, layer, (cx - pad - r, cy - pad - r))


def drop_shadow(canvas: Image.Image, box: tuple[int, int, int, int], blur: int = 18, offset: tuple[int, int] = (0, 10), color: tuple[int, int, int, int] = SHADOW) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((0, h // 4, w, h), fill=color)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur * SCALE))
    paste(canvas, shadow, (x0 + offset[0], y0 + offset[1]))


def draw_articles() -> Image.Image:
    c = _canvas()
    cx, cy = _size()[0] // 2, _size()[1] // 2
    board_w, board_h = int(200 * SCALE), int(250 * SCALE)
    x0 = cx - board_w // 2 - int(8 * SCALE)
    y0 = cy - board_h // 2 + int(6 * SCALE)
    drop_shadow(c, (x0, y0 + board_h - int(30 * SCALE), x0 + board_w, y0 + board_h + int(20 * SCALE)))

    board = rounded_shape(
        (x0, y0, x0 + board_w, y0 + board_h),
        int(22 * SCALE),
        linear_gradient((board_w, board_h), TAN_LIGHT, TAN_DARK),
    )
    paste(c, board, (x0, y0))

    clip_w, clip_h = int(86 * SCALE), int(34 * SCALE)
    clip_x = x0 + board_w // 2 - clip_w // 2
    clip_y = y0 - int(8 * SCALE)
    clip = rounded_shape(
        (clip_x, clip_y, clip_x + clip_w, clip_y + clip_h),
        int(10 * SCALE),
        linear_gradient((clip_w, clip_h), SILVER, (140, 148, 158)),
    )
    paste(c, clip, (clip_x, clip_y))

    paper_m = int(18 * SCALE)
    paper_box = (x0 + paper_m, y0 + int(28 * SCALE), x0 + board_w - paper_m, y0 + board_h - int(20 * SCALE))
    pw, ph = paper_box[2] - paper_box[0], paper_box[3] - paper_box[1]
    paper = rounded_shape(paper_box, int(14 * SCALE), linear_gradient((pw, ph), WHITE, PAPER))
    paste(c, paper, (paper_box[0], paper_box[1]))
    d = _draw(c)
    line_y = paper_box[1] + int(28 * SCALE)
    for i, lw in enumerate((0.78, 0.92, 0.66, 0.84)):
        lw_px = int((paper_box[2] - paper_box[0] - int(36 * SCALE)) * lw)
        d.rounded_rectangle(
            (paper_box[0] + int(18 * SCALE), line_y, paper_box[0] + int(18 * SCALE) + lw_px, line_y + int(10 * SCALE)),
            radius=int(5 * SCALE),
            fill=NAVY_MID,
        )
        line_y += int(24 * SCALE)

    # Pen
    pen_len = int(170 * SCALE)
    pen_w = int(22 * SCALE)
    pen = Image.new("RGBA", (pen_len, pen_w * 3), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pen)
    pd.rounded_rectangle((0, pen_w, pen_len - int(28 * SCALE), pen_w * 2), radius=int(10 * SCALE), fill=BLUE)
    pd.polygon(
        [
            (pen_len - int(28 * SCALE), pen_w),
            (pen_len, pen_w * 1.5),
            (pen_len - int(28 * SCALE), pen_w * 2),
        ],
        fill=NAVY_DARK,
    )
    pd.rounded_rectangle((int(12 * SCALE), pen_w - int(4 * SCALE), int(42 * SCALE), pen_w * 2 + int(4 * SCALE)), radius=int(6 * SCALE), fill=TAN)
    pen = pen.rotate(-38, expand=True, resample=Image.Resampling.BICUBIC)
    paste(c, pen, (x0 + int(95 * SCALE), y0 + int(72 * SCALE)))
    glossy_spot(c, x0 + int(48 * SCALE), y0 + int(42 * SCALE), int(36 * SCALE), int(18 * SCALE))
    return c


def draw_publish() -> Image.Image:
    c = _canvas()
    cx, cy = _size()[0] // 2, _size()[1] // 2
    doc_w, doc_h = int(175 * SCALE), int(210 * SCALE)
    x0 = cx - doc_w // 2 - int(24 * SCALE)
    y0 = cy - doc_h // 2 + int(10 * SCALE)
    drop_shadow(c, (x0, y0 + doc_h - int(24 * SCALE), x0 + doc_w, y0 + doc_h + int(16 * SCALE)))

    doc = rounded_shape(
        (x0, y0, x0 + doc_w, y0 + doc_h),
        int(20 * SCALE),
        linear_gradient((doc_w, doc_h), (52, 98, 138), NAVY_DARK),
    )
    paste(c, doc, (x0, y0))
    fold = Image.new("RGBA", (int(48 * SCALE), int(48 * SCALE)), (0, 0, 0, 0))
    ImageDraw.Draw(fold).polygon([(0, 0), (int(48 * SCALE), 0), (0, int(48 * SCALE))], fill=(18, 58, 92))
    paste(c, fold, (x0 + doc_w - int(48 * SCALE), y0))

    d = _draw(c)
    ly = y0 + int(42 * SCALE)
    for lw in (0.7, 0.85, 0.6):
        wline = int(doc_w * lw * 0.55)
        d.rounded_rectangle(
            (x0 + int(22 * SCALE), ly, x0 + int(22 * SCALE) + wline, ly + int(8 * SCALE)),
            radius=int(4 * SCALE),
            fill=(120, 168, 204),
        )
        ly += int(22 * SCALE)

    pencil_len = int(200 * SCALE)
    pencil = Image.new("RGBA", (pencil_len, int(34 * SCALE)), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pencil)
    pd.rounded_rectangle((int(36 * SCALE), int(6 * SCALE), pencil_len - int(18 * SCALE), int(28 * SCALE)), radius=int(8 * SCALE), fill=GOLD)
    pd.rounded_rectangle((0, int(4 * SCALE), int(36 * SCALE), int(30 * SCALE)), radius=int(8 * SCALE), fill=(236, 140, 140))
    pd.polygon(
        [
            (pencil_len - int(18 * SCALE), int(6 * SCALE)),
            (pencil_len, int(17 * SCALE)),
            (pencil_len - int(18 * SCALE), int(28 * SCALE)),
        ],
        fill=NAVY_DARK,
    )
    pd.rounded_rectangle((int(44 * SCALE), 0, int(68 * SCALE), int(34 * SCALE)), radius=int(4 * SCALE), fill=TAN_DARK)
    pencil = pencil.rotate(-32, expand=True, resample=Image.Resampling.BICUBIC)
    paste(c, pencil, (x0 + int(58 * SCALE), y0 - int(18 * SCALE)))
    return c


def draw_experts() -> Image.Image:
    c = _canvas()
    cx, cy = _size()[0] // 2, _size()[1] // 2
    bw, bh = int(220 * SCALE), int(150 * SCALE)
    x0, y0 = cx - bw // 2, cy - bh // 2 + int(6 * SCALE)
    drop_shadow(c, (x0, y0 + bh - int(4 * SCALE), x0 + bw, y0 + bh + int(30 * SCALE)))

    bubble_h = bh + int(36 * SCALE)
    bubble = Image.new("RGBA", (bw, bubble_h), (0, 0, 0, 0))
    bubble_g = rounded_shape((0, 0, bw, bh), int(34 * SCALE), linear_gradient((bw, bh), (255, 196, 140), ORANGE_DARK))
    paste(bubble, bubble_g, (0, 0))
    bd = ImageDraw.Draw(bubble)
    bd.polygon(
        [
            (int(54 * SCALE), bh - int(10 * SCALE)),
            (int(30 * SCALE), bh + int(30 * SCALE)),
            (int(88 * SCALE), bh - int(4 * SCALE)),
        ],
        fill=ORANGE_DARK,
    )
    paste(c, bubble, (x0, y0))

    d = _draw(c)
    dot_y = y0 + int(58 * SCALE)
    dot_r = int(16 * SCALE)
    for dx in (int(56 * SCALE), int(98 * SCALE), int(140 * SCALE)):
        d.ellipse((x0 + dx, dot_y, x0 + dx + dot_r, dot_y + dot_r), fill=NAVY_DARK)

    badge = int(78 * SCALE)
    bx = x0 + bw - badge - int(8 * SCALE)
    by = y0 + int(18 * SCALE)
    badge_img = rounded_shape(
        (bx, by, bx + badge, by + badge),
        int(18 * SCALE),
        linear_gradient((badge, badge), (42, 98, 142), NAVY_DARK),
    )
    paste(c, badge_img, (bx, by))
    d.arc((bx + int(20 * SCALE), by + int(14 * SCALE), bx + int(58 * SCALE), by + int(52 * SCALE)), 205, 335, fill=WHITE, width=int(5 * SCALE))
    d.line((bx + int(39 * SCALE), by + int(48 * SCALE), bx + int(39 * SCALE), by + int(56 * SCALE)), fill=WHITE, width=int(5 * SCALE))
    d.ellipse((bx + int(35 * SCALE), by + int(58 * SCALE), bx + int(43 * SCALE), by + int(66 * SCALE)), fill=WHITE)
    return c


def draw_business() -> Image.Image:
    c = _canvas()
    cx, cy = _size()[0] // 2, _size()[1] // 2
    bw, bh = int(250 * SCALE), int(175 * SCALE)
    x0, y0 = cx - bw // 2, cy - bh // 2 + int(18 * SCALE)
    drop_shadow(c, (x0, y0 + bh - int(8 * SCALE), x0 + bw, y0 + bh + int(24 * SCALE)))

    # Awning with rounded top mask
    aw_h = int(52 * SCALE)
    stripes = Image.new("RGBA", (bw, aw_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stripes)
    stripe = int(26 * SCALE)
    for i in range(0, bw, stripe):
        color = RED if (i // stripe) % 2 == 0 else WHITE
        sd.rectangle((i, 0, i + stripe, aw_h - int(12 * SCALE)), fill=color)
    sd.polygon([(0, aw_h - int(12 * SCALE)), (bw, aw_h - int(12 * SCALE)), (bw, aw_h), (0, aw_h)], fill=TAN_DARK)
    aw_mask = Image.new("L", (bw, aw_h), 0)
    ImageDraw.Draw(aw_mask).rounded_rectangle((0, 0, bw - 1, aw_h - 1), radius=int(12 * SCALE), fill=255)
    aw = Image.new("RGBA", (bw, aw_h), (0, 0, 0, 0))
    aw.paste(stripes, (0, 0), aw_mask)
    paste(c, aw, (x0, y0))

    body = rounded_shape(
        (x0, y0 + aw_h - int(6 * SCALE), x0 + bw, y0 + bh),
        int(16 * SCALE),
        linear_gradient((bw, bh - aw_h), TAN_LIGHT, TAN_DARK),
    )
    paste(c, body, (x0, y0 + aw_h - int(6 * SCALE)))

    d = _draw(c)
    win_x = x0 + int(32 * SCALE)
    win_y = y0 + aw_h + int(24 * SCALE)
    win_w, win_h = int(78 * SCALE), int(72 * SCALE)
    d.rounded_rectangle((win_x, win_y, win_x + win_w, win_y + win_h), radius=int(10 * SCALE), fill=NAVY_DARK)
    d.rounded_rectangle((win_x + int(8 * SCALE), win_y + int(8 * SCALE), win_x + win_w - int(8 * SCALE), win_y + win_h - int(8 * SCALE)), radius=int(6 * SCALE), fill=(72, 128, 168))

    door_x = x0 + bw - int(32 * SCALE) - int(64 * SCALE)
    door_y = y0 + aw_h + int(18 * SCALE)
    d.rounded_rectangle((door_x, door_y, door_x + int(64 * SCALE), y0 + bh - int(14 * SCALE)), radius=int(10 * SCALE), fill=NAVY_MID)
    d.ellipse((door_x + int(48 * SCALE), door_y + int(52 * SCALE), door_x + int(56 * SCALE), door_y + int(60 * SCALE)), fill=GOLD)

    # Plants
    for px in (x0 + int(18 * SCALE), x0 + bw - int(42 * SCALE)):
        d.ellipse((px, y0 + bh - int(28 * SCALE), px + int(24 * SCALE), y0 + bh - int(6 * SCALE)), fill=GREEN_DARK)
        d.ellipse((px - int(6 * SCALE), y0 + bh - int(42 * SCALE), px + int(30 * SCALE), y0 + bh - int(18 * SCALE)), fill=GREEN)
    return c


def draw_events() -> Image.Image:
    c = _canvas()
    cx, cy = _size()[0] // 2, _size()[1] // 2
    cw, ch = int(210 * SCALE), int(220 * SCALE)
    x0, y0 = cx - cw // 2, cy - ch // 2 + int(8 * SCALE)
    drop_shadow(c, (x0, y0 + ch - int(16 * SCALE), x0 + cw, y0 + ch + int(22 * SCALE)))

    cal = rounded_shape(
        (x0, y0, x0 + cw, y0 + ch),
        int(22 * SCALE),
        linear_gradient((cw, ch), WHITE, (232, 236, 242)),
    )
    paste(c, cal, (x0, y0))

    head_h = int(58 * SCALE)
    head = rounded_shape(
        (x0, y0, x0 + cw, y0 + head_h),
        int(22 * SCALE),
        linear_gradient((cw, head_h), (255, 120, 120), RED_DARK),
    )
    paste(c, head, (x0, y0))

    d = _draw(c)
    for rx in (x0 + int(48 * SCALE), x0 + cw - int(48 * SCALE)):
        d.rounded_rectangle((rx - int(10 * SCALE), y0 - int(18 * SCALE), rx + int(10 * SCALE), y0 + int(12 * SCALE)), radius=int(8 * SCALE), fill=SILVER)
        d.ellipse((rx - int(12 * SCALE), y0 - int(20 * SCALE), rx + int(12 * SCALE), y0 + int(4 * SCALE)), outline=(120, 128, 138), width=int(3 * SCALE))

    grid_x0 = x0 + int(24 * SCALE)
    grid_y0 = y0 + head_h + int(20 * SCALE)
    cell = int(34 * SCALE)
    gap = int(10 * SCALE)
    for row in range(4):
        for col in range(5):
            gx = grid_x0 + col * (cell + gap)
            gy = grid_y0 + row * (cell + gap)
            shade = (210, 216, 226) if (row + col) % 2 else (188, 196, 210)
            d.rounded_rectangle((gx, gy, gx + cell, gy + cell), radius=int(8 * SCALE), fill=shade)
    return c


def draw_links() -> Image.Image:
    c = _canvas()
    cx, cy = _size()[0] // 2, _size()[1] // 2
    drop_shadow(c, (cx - int(110 * SCALE), cy + int(54 * SCALE), cx + int(110 * SCALE), cy + int(88 * SCALE)))

    thick = int(18 * SCALE)
    stroke_ring(c, cx - int(52 * SCALE), cy - int(6 * SCALE), int(48 * SCALE), thick, GOLD_DARK)
    stroke_ring(c, cx - int(52 * SCALE), cy - int(6 * SCALE), int(48 * SCALE), max(thick // 2, int(8 * SCALE)), GOLD)
    stroke_ring(c, cx + int(24 * SCALE), cy + int(18 * SCALE), int(48 * SCALE), thick, NAVY_DARK)
    stroke_ring(c, cx + int(24 * SCALE), cy + int(18 * SCALE), int(48 * SCALE), max(thick // 2, int(8 * SCALE)), (88, 158, 220))
    glossy_spot(c, cx - int(72 * SCALE), cy - int(28 * SCALE), int(22 * SCALE), int(12 * SCALE))
    return c


ICONS = {
    "articles": draw_articles,
    "publish": draw_publish,
    "experts": draw_experts,
    "business": draw_business,
    "events": draw_events,
    "links": draw_links,
}


def downscale(img: Image.Image) -> Image.Image:
    return img.resize((W, H), Image.Resampling.LANCZOS)


def analyze(path: Path) -> dict:
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    white_fringe = near_white = 0
    min_x, min_y, max_x, max_y = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 20:
                min_x, min_y = min(min_x, x), min(min_y, y)
                max_x, max_y = max(max_x, x), max(max_y, y)
            if 0 < a < 255 and r > 200 and g > 200 and b > 200:
                white_fringe += 1
            if a > 128 and r > 240 and g > 240 and b > 240:
                near_white += 1
    return {
        "size": (w, h),
        "bbox": (min_x, min_y, max_x, max_y),
        "white_fringe": white_fringe,
        "near_white_opaque": near_white,
        "clipped": (min_x <= 2, max_x >= w - 3, min_y <= 2, max_y >= h - 3),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SRC_DIR.mkdir(parents=True, exist_ok=True)

    for name, fn in ICONS.items():
        print(f"Generating {name}...")
        img = downscale(fn())
        png_path = SRC_DIR / f"{name}.png"
        webp_path = OUT_DIR / f"{name}.webp"
        img.save(png_path, "PNG")
        img.save(webp_path, "WEBP", quality=92, method=6)
        stats = analyze(webp_path)
        print(f"  -> {webp_path.name} {stats}")

    print("Done.")


if __name__ == "__main__":
    main()
