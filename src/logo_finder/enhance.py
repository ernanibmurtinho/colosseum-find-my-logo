"""Crop the matched region from a mosaic and upscale it."""
from __future__ import annotations

from pathlib import Path

import cv2

from logo_finder.matcher import Match, find_logo


def crop_and_upscale(
    logo_path: str | Path,
    mosaic_path: str | Path,
    output_path: str | Path,
    *,
    target_size: int = 1024,
    padding: int = 0,
    interpolation: int = cv2.INTER_CUBIC,
    match: Match | None = None,
) -> Match:
    """Find the logo in the mosaic, crop the matched region, and write an upscaled image.

    Note that upscaling cannot recover detail that isn't in the source pixels — at a
    typical zoom factor (e.g. 68px → 1024px = ~15x) the output will be smooth but soft.
    For a crisp result, use the original full-resolution logo if you have it. For a
    "hallucinated detail" result, run the output through a super-resolution model
    (e.g. Real-ESRGAN).

    Args:
        logo_path: Path to the template (logo) image.
        mosaic_path: Path to the mosaic to search.
        output_path: Where to write the upscaled crop.
        target_size: Side length in pixels of the (square) output.
        padding: Extra pixels of mosaic to include around the matched region.
        interpolation: OpenCV interpolation flag for the upscale.
        match: An existing ``Match`` to use, skipping the template search.

    Returns:
        The ``Match`` that was used.
    """
    if match is None:
        result = find_logo(logo_path, mosaic_path)
        assert isinstance(result, Match)
        match = result

    mosaic = cv2.imread(str(mosaic_path), cv2.IMREAD_COLOR)
    h, w = mosaic.shape[:2]

    x0 = max(0, match.x - padding)
    y0 = max(0, match.y - padding)
    x1 = min(w, match.x + match.size + padding)
    y1 = min(h, match.y + match.size + padding)

    crop = mosaic[y0:y1, x0:x1]
    upscaled = cv2.resize(crop, (target_size, target_size), interpolation=interpolation)
    cv2.imwrite(str(output_path), upscaled)
    return match
