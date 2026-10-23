#!/usr/bin/env python3
"""Build deterministic 2.5D layers for the Golden Gate motion proof."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "inkwash"
OUT = ROOT / "assets" / "motion-demo"

CONFIG = {
    "desktop": {
        "file": "golden-gate-desktop.jpg",
        "landmark_rect": (.25, .035, .54, .79),
        "foreground_edges": (.24, .77, .80),
    },
    "mobile": {
        "file": "golden-gate-mobile.jpg",
        "landmark_rect": (.09, .025, .82, .67),
        "foreground_edges": (.17, .84, .73),
    },
}


def feather(mask: np.ndarray, radius: float) -> np.ndarray:
    mask = cv2.GaussianBlur(mask, (0, 0), radius)
    return cv2.normalize(mask, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)


def transparent(rgb: np.ndarray, alpha: np.ndarray) -> Image.Image:
    return Image.fromarray(np.dstack((rgb, alpha)), "RGBA")


def build(variant: str, cfg: dict) -> None:
    src = cv2.imread(str(SRC / cfg["file"]), cv2.IMREAD_COLOR)
    if src is None:
        raise FileNotFoundError(SRC / cfg["file"])
    h, w = src.shape[:2]
    rgb = cv2.cvtColor(src, cv2.COLOR_BGR2RGB)
    x, y, rw, rh = cfg["landmark_rect"]
    rect = (round(x * w), round(y * h), round(rw * w), round(rh * h))

    grab = np.zeros((h, w), np.uint8)
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(src, grab, rect, bgd, fgd, 7, cv2.GC_INIT_WITH_RECT)
    landmark = np.where((grab == cv2.GC_FGD) | (grab == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    landmark = cv2.morphologyEx(landmark, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    landmark = feather(landmark, max(2.5, min(w, h) * .004))

    # Dark edge foliage/branches form a stronger foreground plane.
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    left, right, max_y = cfg["foreground_edges"]
    zones = np.zeros((h, w), np.uint8)
    zones[: round(max_y * h), : round(left * w)] = 255
    zones[: round(max_y * h), round(right * w) :] = 255
    dark = cv2.inRange(gray, 0, 142)
    foreground = cv2.bitwise_and(dark, zones)
    foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    foreground = feather(foreground, max(2.0, min(w, h) * .003))

    # Inpaint only a narrow hidden margin so parallax never exposes a duplicate edge.
    hard_landmark = (landmark > 85).astype(np.uint8) * 255
    hard_landmark = cv2.dilate(hard_landmark, np.ones((19, 19), np.uint8), iterations=1)
    background = cv2.inpaint(src, hard_landmark, 9, cv2.INPAINT_TELEA)
    background = cv2.GaussianBlur(background, (0, 0), 1.25)

    target = OUT / variant
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.iterdir():
        if stale.is_file():
            stale.unlink()
    cv2.imwrite(str(target / "background.jpg"), background, [cv2.IMWRITE_JPEG_QUALITY, 91])
    transparent(rgb, landmark).save(target / "landmark.webp", format="WEBP", quality=88, method=6)
    transparent(rgb, foreground).save(target / "foreground.webp", format="WEBP", quality=86, method=6)
    print(variant, w, h, target)


for name, config in CONFIG.items():
    build(name, config)
