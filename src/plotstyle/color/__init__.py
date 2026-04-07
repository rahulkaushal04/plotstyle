"""Color and accessibility tools for PlotStyle.

This package provides a unified interface for working with journal-aware color
palettes, grayscale simulation, and colorblind accessibility previews.

Public API
----------
- :func:`~plotstyle.color.palettes.palette`
    Retrieve a journal-appropriate color palette, optionally with line style
    and marker annotations.

- :func:`~plotstyle.color.accessibility.preview_colorblind`
    Render a side-by-side figure panel simulating common color vision
    deficiencies (CVD) using the Machado et al. (2009) matrices.

- :func:`~plotstyle.color.grayscale.preview_grayscale`
    Render a side-by-side Original / Grayscale comparison figure using
    ITU-R BT.709 luminance weights.

Example
-------
    >>> import matplotlib.pyplot as plt
    >>> from plotstyle.color import palette, preview_colorblind, preview_grayscale
    >>> colors = palette("nature", n=4)
    >>> fig, ax = plt.subplots()
    >>> for i, c in enumerate(colors):
    ...     ax.plot([0, 1], [i, i], color=c)
    >>> preview_colorblind(fig)  # returns a new comparison figure
    >>> preview_grayscale(fig)  # returns a new comparison figure
"""

from __future__ import annotations

from plotstyle.color.accessibility import preview_colorblind
from plotstyle.color.grayscale import preview_grayscale
from plotstyle.color.palettes import palette

__all__: list[str] = [
    "palette",
    "preview_colorblind",
    "preview_grayscale",
]
