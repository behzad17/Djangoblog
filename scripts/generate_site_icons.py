#!/usr/bin/env python3
"""Generate Peyvand favicon/PWA assets from the icon-only master artwork."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "static" / "images" / "hero-mobile.png"
MASTER_PATH = ROOT / "static" / "icons" / "peyvand-icon-master.png"
OUT_DIR = ROOT / "static" / "icons"

ICON_CROP = (200, 0, 1400, 710)  # icon-only region in hero-mobile.png (no wordmark)


def _black_to_transparent(image: Image.Image) -> Image.Image:
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            if red < 20 and green < 20 and blue < 20:
                pixels[x, y] = (0, 0, 0, 0)
    return image


def extract_master(source: Path = DEFAULT_SOURCE) -> Image.Image:
    icon_raw = Image.open(source).convert("RGBA").crop(ICON_CROP)
    icon_raw = _black_to_transparent(icon_raw)
    bbox = icon_raw.getbbox()
    if not bbox:
        raise RuntimeError(f"No icon pixels found in {source}")
    icon = icon_raw.crop(bbox)

    width, height = icon.size
    side = max(width, height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(icon, ((side - width) // 2, (side - height) // 2), icon)
    return square.resize((1024, 1024), Image.Resampling.LANCZOS)


def fit_square(image: Image.Image, size: int) -> Image.Image:
    width, height = image.size
    scale = min(size / width, size / height)
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - new_width) // 2, (size - new_height) // 2), resized)
    return canvas


def generate(source: Path = DEFAULT_SOURCE) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = extract_master(source)
    master.save(MASTER_PATH)

    png_sizes = {
        "favicon-16x16.png": 16,
        "favicon-32x32.png": 32,
        "favicon-48x48.png": 48,
        "apple-touch-icon.png": 180,
        "android-chrome-192x192.png": 192,
        "android-chrome-512x512.png": 512,
        "mstile-150x150.png": 150,
    }
    for filename, size in png_sizes.items():
        fit_square(master, size).save(OUT_DIR / filename)

    ico_images = [fit_square(master, size) for size in (16, 32, 48)]
    ico_images[0].save(
        OUT_DIR / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=ico_images[1:],
    )


if __name__ == "__main__":
    generate()
