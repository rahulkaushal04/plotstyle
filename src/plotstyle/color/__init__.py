"""Color and accessibility tools for PlotStyle."""

from plotstyle.color.accessibility import preview_colorblind
from plotstyle.color.grayscale import preview_grayscale
from plotstyle.color.palettes import palette

__all__: list[str] = [
    "palette",
    "preview_colorblind",
    "preview_grayscale",
]
