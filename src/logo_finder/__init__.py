"""Find a logo in a mosaic of icons. Crop, upscale, or animate the find."""
from logo_finder.matcher import Match, find_logo
from logo_finder.enhance import crop_and_upscale
from logo_finder.animator import animate_zoom

__all__ = ["Match", "find_logo", "crop_and_upscale", "animate_zoom"]
__version__ = "0.1.0"
