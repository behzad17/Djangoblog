#!/usr/bin/env python3
"""Generate Peyvand favicon/PWA assets from peyvand-icon-master.png."""

from __future__ import annotations

import io
import struct
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
MASTER_PATH = ROOT / "static" / "icons" / "peyvand-icon-master.png"
OUT_DIR = ROOT / "static" / "icons"

RESAMPLE = Image.Resampling.LANCZOS
WHITE_THRESHOLD = 250


def load_master(source: Path = MASTER_PATH) -> Image.Image:
    """Load the master icon and convert near-white background to transparency."""
    image = Image.open(source).convert("RGBA")
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]
            if red >= WHITE_THRESHOLD and green >= WHITE_THRESHOLD and blue >= WHITE_THRESHOLD:
                pixels[x, y] = (0, 0, 0, 0)
    return image


def _resize_lanczos(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    return image.resize(size, RESAMPLE)


def _progressive_downscale(image: Image.Image, target_size: int) -> Image.Image:
    """Downscale in steps for sharper small favicons."""
    current = image
    current_max = max(current.size)

    while current_max > target_size * 2:
        next_max = max(target_size, current_max // 2)
        scale = next_max / current_max
        next_size = (
            max(1, int(current.width * scale)),
            max(1, int(current.height * scale)),
        )
        current = _resize_lanczos(current, next_size)
        current_max = max(current.size)

    return _resize_lanczos(current, (target_size, target_size))


def _sharpen_small_icon(image: Image.Image, size: int) -> Image.Image:
    """Apply light unsharp masking tuned for favicon sizes."""
    if size <= 16:
        radius, percent, threshold = 0.6, 220, 1
    else:
        radius, percent, threshold = 0.8, 180, 2
    return image.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))


def fit_square(image: Image.Image, size: int, *, sharpen: bool = False) -> Image.Image:
    """Scale uniformly to fit inside a square canvas; pad with transparency."""
    width, height = image.size
    scale = min(size / width, size / height)
    new_width = max(1, int(round(width * scale)))
    new_height = max(1, int(round(height * scale)))

    if sharpen and size <= 32:
        # Supersample before final downscale for crisp pixel edges.
        supersample = size * 4
        working = Image.new("RGBA", (supersample, supersample), (0, 0, 0, 0))
        super_w = max(1, int(round(width * (supersample / max(width, height)))))
        super_h = max(1, int(round(height * (supersample / max(width, height)))))
        scaled = _progressive_downscale(image, max(super_w, super_h))
        scaled = _resize_lanczos(scaled, (super_w, super_h))
        working.paste(scaled, ((supersample - super_w) // 2, (supersample - super_h) // 2), scaled)
        resized = _progressive_downscale(working, size)
        resized = _sharpen_small_icon(resized, size)
    else:
        resized = _resize_lanczos(image, (new_width, new_height))

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(resized, ((size - resized.width) // 2, (size - resized.height) // 2), resized)
    return canvas


def save_ico(images: dict[int, Image.Image], path: Path) -> None:
    """Write a multi-size ICO with embedded PNG payloads (Windows Vista+)."""
    entries: list[tuple[int, bytes]] = []
    for size in sorted(images):
        icon = images[size]
        if icon.size != (size, size):
            icon = _resize_lanczos(icon, (size, size))
        buffer = io.BytesIO()
        icon.save(buffer, format="PNG", optimize=True)
        entries.append((size, buffer.getvalue()))

    count = len(entries)
    offset = 6 + (16 * count)
    with path.open("wb") as handle:
        handle.write(struct.pack("<HHH", 0, 1, count))
        for size, png_data in entries:
            width_byte = size if size < 256 else 0
            height_byte = size if size < 256 else 0
            handle.write(
                struct.pack(
                    "<BBBBHHII",
                    width_byte,
                    height_byte,
                    0,
                    0,
                    1,
                    32,
                    len(png_data),
                    offset,
                )
            )
            offset += len(png_data)
        for _, png_data in entries:
            handle.write(png_data)


def generate(source: Path = MASTER_PATH) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Master icon not found: {source}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master(source)

    png_sizes = {
        "favicon-16x16.png": (16, True),
        "favicon-32x32.png": (32, True),
        "favicon-48x48.png": (48, False),
        "apple-touch-icon.png": (180, False),
        "android-chrome-192x192.png": (192, False),
        "android-chrome-512x512.png": (512, False),
    }

    generated: dict[int, Image.Image] = {}
    for filename, (size, sharpen) in png_sizes.items():
        icon = fit_square(master, size, sharpen=sharpen)
        icon.save(OUT_DIR / filename, optimize=True)
        generated[size] = icon
        print(f"Wrote {filename} ({size}x{size})")

    save_ico({size: generated[size] for size in (16, 32, 48)}, OUT_DIR / "favicon.ico")
    print("Wrote favicon.ico (16, 32, 48)")


if __name__ == "__main__":
    generate()
