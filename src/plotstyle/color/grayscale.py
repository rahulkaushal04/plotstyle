"""Grayscale simulation and luminance analysis for print compliance.

Luminance formula: $L = 0.2126 R + 0.7152 G + 0.0722 B$ (ITU-R BT.709).
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Final

import numpy as np
from matplotlib.colors import to_rgb

from plotstyle.color._rendering import _fig_to_rgb_array

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__: list[str] = [
    "is_grayscale_safe",
    "luminance_delta",
    "preview_grayscale",
    "rgb_to_luminance",
]


# ITU-R BT.709 luminance coefficients.
_LUMA_R: Final[float] = 0.2126
_LUMA_G: Final[float] = 0.7152
_LUMA_B: Final[float] = 0.0722


# ---------------------------------------------------------------------------
# Per-colour luminance utilities
# ---------------------------------------------------------------------------


def rgb_to_luminance(r: float, g: float, b: float) -> float:
    """Return the ITU-R BT.709 relative luminance for linear-light RGB values in ``[0, 1]``.

    Parameters
    ----------
    r : float
        Red channel value in ``[0, 1]``.
    g : float
        Green channel value in ``[0, 1]``.
    b : float
        Blue channel value in ``[0, 1]``.

    Returns
    -------
    float
        Relative luminance in ``[0, 1]``.
    """
    return _LUMA_R * r + _LUMA_G * g + _LUMA_B * b


def luminance_delta(colors: list[str]) -> list[tuple[int, int, float]]:
    """Return pairwise luminance deltas for *colors*, sorted ascending by delta.

    Parameters
    ----------
    colors : list[str]
        Matplotlib colour specifiers.

    Returns
    -------
    list[tuple[int, int, float]]
        ``(idx_a, idx_b, delta)`` triples sorted by ascending delta.
        Empty when *colors* has fewer than two elements.
    """
    if len(colors) < 2:
        return []

    luminances = [rgb_to_luminance(*to_rgb(c)) for c in colors]

    pairs = [
        (i, j, abs(luminances[i] - luminances[j]))
        for i, j in itertools.combinations(range(len(luminances)), 2)
    ]

    pairs.sort(key=lambda t: t[2])
    return pairs


def is_grayscale_safe(colors: list[str], *, threshold: float = 0.1) -> bool:
    """Return ``True`` if every colour pair in *colors* has a luminance delta ≥ *threshold*.

    Parameters
    ----------
    colors : list[str]
        Matplotlib colour specifiers.
    threshold : float
        Minimum luminance difference in ``[0, 1]``.

    Returns
    -------
    bool
        ``True`` if every colour pair has a luminance delta ≥ *threshold*.

    Raises
    ------
    ValueError
        If *threshold* is outside ``[0, 1]``.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be in [0, 1], got {threshold!r}.")

    pairs = luminance_delta(colors)

    if not pairs:
        return True

    return pairs[0][2] >= threshold


# ---------------------------------------------------------------------------
# High-level preview helper
# ---------------------------------------------------------------------------


def preview_grayscale(fig: Figure) -> Figure:
    """Return a new figure showing *fig* side-by-side with its grayscale equivalent.

    Parameters
    ----------
    fig : Figure
        Source figure (must use an Agg canvas).

    Returns
    -------
    Figure
        Two-panel figure: original (left) and grayscale (right).
    """
    import matplotlib.pyplot as plt

    original = _fig_to_rgb_array(fig)

    # Apply BT.709 luminance weights via dot product and normalise from uint8
    gray = np.dot(original.astype(np.float64), [_LUMA_R, _LUMA_G, _LUMA_B]) / 255.0

    panel_h, panel_w = original.shape[:2]
    dpi = fig.dpi
    total_w = panel_w * 2 / dpi
    total_h = panel_h / dpi

    comp_fig, (ax_orig, ax_gray) = plt.subplots(1, 2, figsize=(total_w, total_h), dpi=dpi)

    ax_orig.imshow(original)
    ax_orig.set_title("Original", fontsize=8)
    ax_orig.axis("off")

    ax_gray.imshow(gray, cmap="gray", vmin=0.0, vmax=1.0)
    ax_gray.set_title("Grayscale", fontsize=8)
    ax_gray.axis("off")

    comp_fig.tight_layout(pad=0.5)
    return comp_fig
