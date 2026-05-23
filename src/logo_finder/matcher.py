"""Multi-scale template matching to locate a logo in a mosaic of icons."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class Match:
    """A located template instance in the haystack image."""

    x: int
    """Top-left x coordinate in the mosaic."""

    y: int
    """Top-left y coordinate in the mosaic."""

    size: int
    """Side length the template was resized to for this match."""

    confidence: float
    """Normalized cross-correlation score in [-1, 1]. >0.9 is a strong match."""

    @property
    def center(self) -> tuple[int, int]:
        """Pixel center of the matched region."""
        return (self.x + self.size // 2, self.y + self.size // 2)

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        """Bounding box as (x0, y0, x1, y1)."""
        return (self.x, self.y, self.x + self.size, self.y + self.size)


def _load_color(path: str | Path) -> np.ndarray:
    # Color (BGR) matching: a logo's distinctive hues (e.g. a white mark + blue
    # underline) disambiguate it from same-shaped icons that grayscale conflates.
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image at {path}")
    return img


def find_logo(
    logo_path: str | Path,
    mosaic_path: str | Path,
    *,
    min_scale: int = 50,
    max_scale: int = 110,
    scale_step: int = 2,
    top_n: int = 1,
) -> Match | list[Match]:
    """Locate ``logo_path`` inside ``mosaic_path`` using multi-scale template matching.

    Args:
        logo_path: Path to the template image (the logo to find).
        mosaic_path: Path to the haystack image (the mosaic).
        min_scale: Smallest template size to try, in pixels (assumes square templates).
        max_scale: Largest template size to try, exclusive.
        scale_step: Step between scale attempts.
        top_n: How many distinct matches to return. ``1`` returns a single ``Match``;
            anything else returns a list. Non-maximum suppression is applied between
            matches at the best scale.

    Returns:
        A single ``Match`` if ``top_n == 1``, otherwise a list of up to ``top_n`` matches
        sorted by descending confidence.
    """
    logo = _load_color(logo_path)
    mosaic = _load_color(mosaic_path)

    best_conf = -1.0
    best_scale = min_scale
    best_loc = (0, 0)

    for size in range(min_scale, max_scale, scale_step):
        if size > min(mosaic.shape[:2]):  # H,W only — not the color-channel dim
            break
        template = cv2.resize(logo, (size, size), interpolation=cv2.INTER_AREA)
        result = cv2.matchTemplate(mosaic, template, cv2.TM_CCOEFF_NORMED)
        _, conf, _, loc = cv2.minMaxLoc(result)
        if conf > best_conf:
            best_conf = float(conf)
            best_scale = size
            best_loc = loc

    if top_n == 1:
        return Match(x=best_loc[0], y=best_loc[1], size=best_scale, confidence=best_conf)

    # For top_n > 1: re-run at the winning scale and apply non-max suppression
    template = cv2.resize(logo, (best_scale, best_scale), interpolation=cv2.INTER_AREA)
    result = cv2.matchTemplate(mosaic, template, cv2.TM_CCOEFF_NORMED).copy()

    matches: list[Match] = []
    for _ in range(top_n):
        _, conf, _, loc = cv2.minMaxLoc(result)
        matches.append(Match(x=loc[0], y=loc[1], size=best_scale, confidence=float(conf)))
        # Suppress a region around this match so the next argmax is a different icon
        x, y = loc
        r = best_scale
        y0, y1 = max(0, y - r), min(result.shape[0], y + r)
        x0, x1 = max(0, x - r), min(result.shape[1], x + r)
        result[y0:y1, x0:x1] = -1.0

    return matches
