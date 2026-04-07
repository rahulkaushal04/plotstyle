"""Shared figure-rasterisation helper for the color package.

Both :mod:`plotstyle.color.grayscale` and :mod:`plotstyle.color.accessibility`
require a pixel-level NumPy representation of a live matplotlib Figure before
applying channel transformations.  Centralising this conversion here ensures:

- A single, well-tested code path for rasterisation.
- No duplication of the Agg-backend buffer-reading logic.
- A stable internal contract that downstream modules can depend on.

Note
----
    This module is intentionally private (``_rendering``).  It is not part of
    the public API and may change without notice.  External code should not
    import from it directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from numpy.typing import NDArray


def _fig_to_rgb_array(fig: Figure) -> NDArray[np.uint8]:
    """Render a matplotlib Figure to a writeable RGB NumPy array.

    Uses the Agg (raster) backend to draw the figure into an in-memory RGBA
    buffer, then returns a *writeable* ``uint8`` copy with the alpha channel
    discarded.  Forcing ``canvas.draw()`` before reading the buffer guarantees
    that deferred artists (e.g., tight-layout adjustments) are fully committed
    to the pixel grid.

    Args:
        fig: A fully constructed :class:`~matplotlib.figure.Figure` instance.
            The figure must have an Agg canvas attached; interactive backends
            that do not expose ``buffer_rgba`` will raise ``AttributeError``.

    Returns
    -------
        A ``uint8`` array of shape ``(H, W, 3)`` representing the RGB pixels,
        where ``H = fig.get_size_inches()[1] * fig.dpi`` and
        ``W = fig.get_size_inches()[0] * fig.dpi``.

    Raises
    ------
        AttributeError: If *fig*'s canvas does not support ``buffer_rgba``
            (e.g., a non-Agg backend such as SVG or PDF).
        ValueError: If the buffer size does not match the expected dimensions,
            which can occur when DPI is not a positive finite number.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> ax.plot([0, 1], [0, 1])
        >>> rgb = _fig_to_rgb_array(fig)
        >>> rgb.shape  # (H, W, 3) — exact values depend on figure size/DPI
        (480, 640, 3)

    Notes
    -----
        - The returned array is a *copy*, so mutating it does not affect the
          figure's internal canvas buffer.
        - Alpha is stripped because downstream pixel transforms (grayscale,
          CVD simulation) operate exclusively in the RGB colour space.
    """
    # Commit all pending draw operations so the buffer reflects the final
    # rendered state of the figure, including layout engine adjustments.
    fig.canvas.draw()

    buf = fig.canvas.buffer_rgba()

    # Compute the expected pixel dimensions from the figure's logical size.
    # Using int() here truncates any floating-point rounding from size * dpi.
    height = int(fig.get_size_inches()[1] * fig.dpi)
    width = int(fig.get_size_inches()[0] * fig.dpi)

    rgba: NDArray[np.uint8] = np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 4)

    # Drop the alpha channel (index 3) and return a writeable copy so that
    # callers can safely modify pixel values in-place.
    return rgba[:, :, :3].copy()
