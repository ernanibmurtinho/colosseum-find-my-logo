"""Example: locate a logo, then crop+upscale and render a zoom animation."""
from pathlib import Path

from logo_finder import animate_zoom, crop_and_upscale, find_logo

LOGO = Path("logo.png")
MOSAIC = Path("mosaic.png")
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

# 1. Find it
match = find_logo(LOGO, MOSAIC)
print(f"Found at {match.center} (confidence {match.confidence:.3f}, {match.size}px)")

# 2. Get the top 3 candidates to sanity-check
candidates = find_logo(LOGO, MOSAIC, top_n=3)
for i, c in enumerate(candidates, 1):  # type: ignore[union-attr]
    print(f"  #{i}: confidence={c.confidence:.3f}")

# 3. Crop and upscale (pass the match to skip re-searching)
crop_and_upscale(LOGO, MOSAIC, OUT / "maximized.png", target_size=1024, match=match)

# 4. Animate the zoom
animate_zoom(
    LOGO, MOSAIC,
    mp4_path=OUT / "zoom.mp4",
    gif_path=OUT / "zoom.gif",
    match=match,
)
print("Done")
