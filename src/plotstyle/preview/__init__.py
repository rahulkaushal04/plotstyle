"""Preview tools for PlotStyle.

This sub-package provides two visual inspection utilities for exploring how a
journal style looks before committing to a final figure layout:

``gallery``
    Render a 2x2 grid of sample plots — line, scatter, bar, and histogram —
    sized and styled to match a journal's column-width and typography
    constraints.  Useful for quickly assessing a journal preset before
    creating production figures.

``preview_print_size``
    Display an existing figure at its approximate physical print size by
    temporarily scaling the figure DPI to match the monitor's pixel density.
    Useful for verifying that text and line weights are legible at the
    dimensions they will occupy in print.

Usage
-----
Both functions are re-exported at the top-level :mod:`plotstyle` package, so
the following are equivalent::

    # Via the top-level package (recommended):
    import plotstyle

    plotstyle.gallery("nature")
    plotstyle.preview_print_size(fig, journal="nature")

    # Via this sub-package directly:
    from plotstyle.preview import gallery, preview_print_size

    gallery("nature")
    preview_print_size(fig, journal="nature")

Notes
-----
Neither utility mutates global Matplotlib state after returning.  Both apply
any required rcParams changes in a scoped block and restore the prior state
unconditionally in a ``finally`` clause.
"""

from __future__ import annotations

from plotstyle.preview.gallery import gallery
from plotstyle.preview.print_size import preview_print_size

__all__: list[str] = [
    "gallery",
    "preview_print_size",
]
