"""Shared figure-rasterisation helper for the color package (internal).

Used by :mod:`~plotstyle.color.accessibility` and
:mod:`~plotstyle.color.grayscale`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from numpy.typing import NDArray


def _fig_to_rgb_array(fig: Figure) -> NDArray[np.uint8]:
    """Render a Matplotlib figure to a writeable uint8 RGB array.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to render.

    Returns
    -------
    NDArray[np.uint8]
        Array of shape ``(H, W, 3)`` in RGB order.
    """
    fig.canvas.draw()

    # physical=True matches the buffer_rgba() byte count on HiDPI/Retina screens.
    width, height = fig.canvas.get_width_height(physical=True)

    # buffer_rgba() returns a read-only memoryview; .copy() makes it writeable
    rgba = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(height, width, 4)
    return rgba[:, :, :3].copy()
