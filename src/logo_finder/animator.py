"""Render a CSI-style zoom animation from a full mosaic into a located logo."""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from logo_finder.matcher import Match, find_logo


def _ease_in_out_cubic(t: float) -> float:
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def _pad_to_square(image: np.ndarray) -> tuple[np.ndarray, int, int]:
    """Pad ``image`` with black borders so width == height. Returns (padded, x_off, y_off)."""
    h, w = image.shape[:2]
    target = max(h, w)
    pad_top = (target - h) // 2
    pad_bottom = target - h - pad_top
    pad_left = (target - w) // 2
    pad_right = target - w - pad_left
    padded = cv2.copyMakeBorder(
        image, pad_top, pad_bottom, pad_left, pad_right,
        cv2.BORDER_CONSTANT, value=(0, 0, 0),
    )
    return padded, pad_left, pad_top


def animate_zoom(
    logo_path: str | Path,
    mosaic_path: str | Path,
    *,
    mp4_path: str | Path | None = None,
    gif_path: str | Path | None = None,
    fps: int = 30,
    duration_seconds: float = 3.5,
    hold_start_seconds: float = 0.4,
    hold_end_seconds: float = 1.0,
    output_size: int = 720,
    end_size: int = 120,
    gif_size: int = 400,
    gif_fps: int = 20,
    match: Match | None = None,
) -> Match:
    """Render a zoom-in animation that starts on the full mosaic and ends on the logo.

    At least one of ``mp4_path`` or ``gif_path`` must be provided.

    Args:
        logo_path: Path to the template (logo) image.
        mosaic_path: Path to the mosaic to search.
        mp4_path: If set, write an MP4 here.
        gif_path: If set, write a GIF here.
        fps: Frame rate of the MP4.
        duration_seconds: Total animation duration including holds.
        hold_start_seconds: How long to hold on the full mosaic before zooming.
        hold_end_seconds: How long to hold on the logo after zooming.
        output_size: Side length in pixels of the (square) MP4 output.
        end_size: Final viewport size in source-image pixels (smaller = tighter crop).
        gif_size: Side length of GIF output (typically smaller for file size).
        gif_fps: GIF frame rate.
        match: An existing ``Match`` to zoom into, skipping the template search.

    Returns:
        The ``Match`` that was zoomed into.
    """
    if mp4_path is None and gif_path is None:
        raise ValueError("Provide at least one of mp4_path or gif_path")

    if match is None:
        result = find_logo(logo_path, mosaic_path)
        assert isinstance(result, Match)
        match = result

    mosaic = cv2.imread(str(mosaic_path), cv2.IMREAD_COLOR)
    padded, x_off, y_off = _pad_to_square(mosaic)
    target = padded.shape[0]

    # Target the center of the located icon, adjusting for padding
    logo_cx = match.x + x_off + match.size / 2
    logo_cy = match.y + y_off + match.size / 2

    # Frame counts
    hold_start = max(0, int(hold_start_seconds * fps))
    hold_end = max(0, int(hold_end_seconds * fps))
    zoom_frames = max(2, int(duration_seconds * fps) - hold_start - hold_end)

    start_size = target
    start_cx = target / 2
    start_cy = target / 2

    log_start = math.log(start_size)
    log_end = math.log(end_size)

    def render(progress: float) -> np.ndarray:
        e = _ease_in_out_cubic(progress)
        # Log-interp on size keeps the perceived zoom rate constant
        size = math.exp(log_start + (log_end - log_start) * e)
        cx = start_cx + (logo_cx - start_cx) * e
        cy = start_cy + (logo_cy - start_cy) * e

        half = size / 2
        x0 = max(0, int(cx - half))
        y0 = max(0, int(cy - half))
        x1 = min(target, int(cx + half))
        y1 = min(target, int(cy + half))

        crop = padded[y0:y1, x0:x1]
        interp = cv2.INTER_AREA if size > output_size else cv2.INTER_CUBIC
        return cv2.resize(crop, (output_size, output_size), interpolation=interp)

    frames: list[np.ndarray] = []
    frames.extend(render(0.0) for _ in range(hold_start))
    frames.extend(render(i / (zoom_frames - 1)) for i in range(zoom_frames))
    frames.extend(render(1.0) for _ in range(hold_end))

    if mp4_path is not None:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(mp4_path), fourcc, fps, (output_size, output_size))
        for frame in frames:
            writer.write(frame)
        writer.release()

    if gif_path is not None:
        step = max(1, fps // gif_fps)
        gif_frames: list[Image.Image] = []
        for frame in frames[::step]:
            small = cv2.resize(frame, (gif_size, gif_size), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            gif_frames.append(Image.fromarray(rgb))
        gif_frames[0].save(
            str(gif_path),
            save_all=True,
            append_images=gif_frames[1:],
            duration=1000 // gif_fps,
            loop=0,
            optimize=True,
        )

    return match
