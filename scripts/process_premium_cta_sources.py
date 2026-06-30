#!/usr/bin/env python3
"""Process premium CTA source PNGs: magenta key → 420×330 transparent WebP."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "static" / "images" / "premium-cta" / "sources"
OUT_DIR = ROOT / "static" / "images" / "premium-cta" / "icons"
MASTER_DIR = SRC_DIR / "masters"

W, H = 420, 330
PADDING = 0.11  # fraction of canvas — keeps badge/shadows inside frame


def is_magenta(r: int, g: int, b: int) -> float:
    """Return 0..1 how magenta-like the pixel is (1 = fully keyed out)."""
    if r < 120 or b < 120:
        return 0.0
    if g > min(r, b) * 0.55:
        return 0.0
    mag_strength = min(r, b) / 255.0
    green_penalty = max(0.0, 1.0 - g / max(min(r, b), 1))
    return min(1.0, mag_strength * green_penalty * 1.35)


def key_magenta(im: Image.Image, spill: int = 32) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            key = is_magenta(r, g, b)
            if key > 0.88:
                px[x, y] = (0, 0, 0, 0)
                continue
            if key > 0.25:
                alpha = int(255 * (1.0 - key))
                nr = int(r * (1 - key * 0.2) + 255 * key * 0.2 * (1 - key))
                ng = int(g * (1 - key * 0.65))
                nb = int(b * (1 - key * 0.2) + 255 * key * 0.2 * (1 - key))
                px[x, y] = (min(255, nr), min(255, ng), min(255, nb), alpha)
                continue
            # residual magenta spill on light surfaces
            if a > 0 and r > 170 and b > 170 and g < 150:
                t = min(1.0, (r + b) / 510.0)
                ng = min(255, g + spill)
                nr = int(r - (r - ng) * 0.35)
                nb = int(b - (b - ng) * 0.35)
                px[x, y] = (nr, ng, nb, a)
    return im


def fit_canvas(im: Image.Image) -> Image.Image:
    bbox = im.getbbox()
    if not bbox:
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cropped = im.crop(bbox)
    cw, ch = cropped.size
    max_w = int(W * (1 - PADDING * 2))
    max_h = int(H * (1 - PADDING * 2))
    scale = min(max_w / cw, max_h / ch)
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ox = (W - nw) // 2
    oy = (H - nh) // 2
    canvas.alpha_composite(resized, (ox, oy))
    return canvas


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
    mapping = {
        "articles": MASTER_DIR / "premium-cta-gen-articles.png",
        "publish": MASTER_DIR / "premium-cta-gen-publish.png",
        "experts": MASTER_DIR / "premium-cta-gen-experts.png",
        "business": MASTER_DIR / "premium-cta-gen-business.png",
        "events": MASTER_DIR / "premium-cta-gen-events.png",
        "links": MASTER_DIR / "premium-cta-gen-links.png",
    }
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, src in mapping.items():
        if not src.exists():
            raise FileNotFoundError(f"Missing source: {src}")
        print(f"Processing {name} from {src.name}...")
        raw = Image.open(src)
        keyed = key_magenta(raw)
        fitted = fit_canvas(keyed)
        png_src = SRC_DIR / f"{name}.png"
        webp_out = OUT_DIR / f"{name}.webp"
        fitted.save(png_src, "PNG")
        fitted.save(webp_out, "WEBP", quality=93, method=6, lossless=False)
        print(f"  -> {webp_out.name} {analyze(webp_out)}")

    print("Done.")


if __name__ == "__main__":
    main()
