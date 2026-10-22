#!/usr/bin/env python3
"""Build non-generative monochrome retouches from licensed Wikimedia photos.

The pixels are cropped, resized, tone-mapped, sharpened, and textured only.
No generative model is used, so landmark geometry remains photographic.
"""
from __future__ import annotations

import hashlib
import io
import json
import random
import re
import shutil
import time
import urllib.request
import urllib.error
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "image-sources" / "real-photo-manifest.json"
SOURCE = ROOT / "assets" / "source"
OUTPUT = ROOT / "assets" / "retouched"

# Crop focus points: (horizontal, vertical), normalized 0..1.
FOCUS = {
    ("dnipro", "desktop"): (0.48, 0.50),
    ("dnipro", "mobile"): (0.52, 0.48),
    ("golden-gate", "desktop"): (0.50, 0.52),
    ("golden-gate", "mobile"): (0.50, 0.49),
    ("sophia", "desktop"): (0.50, 0.53),
    ("sophia", "mobile"): (0.50, 0.48),
    ("podil", "desktop"): (0.50, 0.54),
    ("podil", "mobile"): (0.50, 0.47),
    ("chimaeras", "desktop"): (0.50, 0.52),
    ("chimaeras", "mobile"): (0.50, 0.47),
    ("metro", "desktop"): (0.50, 0.50),
    ("metro", "mobile"): (0.50, 0.50),
    ("maidan", "desktop"): (0.50, 0.53),
    ("maidan", "mobile"): (0.27, 0.48),
}
SIZES = {"desktop": (2048, 1152), "mobile": (1152, 2048)}


URL_CACHE: dict[str, Path] = {}


def download(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 100_000:
        URL_CACHE[url] = target
        return
    cached = URL_CACHE.get(url)
    if cached and cached.exists():
        shutil.copy2(cached, target)
        return
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "KyivScrollStory/1.0 (github.com/oliviajohns5/kyiv-scroll-story)"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                target.write_bytes(response.read())
            URL_CACHE[url] = target
            return
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 4:
                raise
            time.sleep(12 * (attempt + 1))


def paper_noise(size: tuple[int, int], seed: str) -> Image.Image:
    rnd = random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16))
    small = Image.new("L", (max(1, size[0] // 5), max(1, size[1] // 5)))
    small.putdata([max(0, min(255, int(rnd.gauss(130, 22)))) for _ in range(small.width * small.height)])
    return small.resize(size, Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(0.55))


def retouch(source: Path, output: Path, size: tuple[int, int], focus: tuple[float, float], seed: str) -> None:
    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw).convert("RGB")

    image = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS, centering=focus)
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=(0.8, 0.8))
    gray = ImageEnhance.Contrast(gray).enhance(1.16)

    # Preserve photographic geometry while giving the image a hand-retouched ink finish.
    broad = gray.filter(ImageFilter.GaussianBlur(5.5))
    detail = ImageChops.subtract(gray, broad, scale=1.35, offset=128)
    detail = ImageEnhance.Contrast(detail).enhance(1.35)
    toned = ImageOps.colorize(gray, black="#0a0d0f", white="#eeeae0", mid="#8a8983", blackpoint=4, whitepoint=247)

    line = gray.filter(ImageFilter.FIND_EDGES)
    line = ImageOps.invert(ImageOps.autocontrast(line)).filter(ImageFilter.GaussianBlur(0.35))
    line_rgb = ImageOps.colorize(line, black="#06090b", white="#f1ede4")
    toned = Image.blend(toned, ImageChops.multiply(toned, line_rgb), 0.18)

    detail_rgb = ImageOps.colorize(detail, black="#141719", white="#ebe7dd")
    toned = Image.blend(toned, ImageChops.overlay(toned, detail_rgb), 0.13)

    texture = paper_noise(size, seed)
    texture_rgb = ImageOps.colorize(texture, black="#b9b5ac", white="#ffffff")
    toned = Image.blend(toned, ImageChops.multiply(toned, texture_rgb), 0.09)

    # Slight vignette improves text contrast without repainting the subject.
    mask = Image.new("L", size, 255)
    edge = Image.new("L", size, 0)
    edge.paste(255, (int(size[0] * .08), int(size[1] * .06), int(size[0] * .92), int(size[1] * .94)))
    edge = edge.filter(ImageFilter.GaussianBlur(int(min(size) * .14)))
    vignette = ImageOps.invert(edge)
    dark = Image.new("RGB", size, "#050708")
    toned = Image.composite(dark, toned, vignette.point(lambda p: int(p * .28)))

    toned = toned.filter(ImageFilter.UnsharpMask(radius=1.2, percent=85, threshold=3))
    output.parent.mkdir(parents=True, exist_ok=True)
    toned.save(output, "JPEG", quality=91, optimize=True, progressive=True)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text())
    SOURCE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for scene, variants in manifest["scenes"].items():
        for variant, record in variants.items():
            suffix = Path(record["url"].split("?")[0]).suffix or ".jpg"
            source = SOURCE / f"{scene}-{variant}{suffix}"
            output = OUTPUT / f"{scene}-{variant}.jpg"
            # Wikimedia explicitly recommends cached thumbnails for automated reuse.
            download_url = re.sub(r"/\d+px-", "/1920px-", record["thumb"].split("?")[0])
            download(download_url, source)
            retouch(source, output, SIZES[variant], FOCUS[(scene, variant)], f"{scene}-{variant}")
            print(f"{scene}/{variant}: {output.relative_to(ROOT)} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
