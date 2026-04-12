"""Grayscale simulation and luminance analysis for IEEE/print compliance.

Figures destined for black-and-white print media (IEEE journals, conference
proceedings, etc.) must remain interpretable when rendered in grayscale.  This
module provides two complementary tools:

1. **Luminance utilities** — compute relative luminance (ITU-R BT.709) for
   individual colours and pairwise luminance deltas for a palette, so that
   authors can programmatically verify print safety before submission.

2. **Visual preview** — render a side-by-side Original / Grayscale comparison
   figure so that authors can inspect their figure as a reader would see it in
   print.

Luminance formula (ITU-R BT.709)
---------------------------------
    L = 0.2126·R + 0.7152·G + 0.0722·B

where R, G, B are linear-light values in ``[0, 1]``.

Example
-------
    >>> from plotstyle.color.grayscale import luminance_delta, is_grayscale_safe, preview_grayscale
    >>> colors = ["#e41a1c", "#377eb8", "#4daf4a"]
    >>> is_grayscale_safe(colors, threshold=0.1)
    True
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> for c in colors:
    ...     ax.plot([0, 1], [0, 0], color=c)
    >>> comp = preview_grayscale(fig)
    >>> plt.show()
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

import numpy as np
from matplotlib.colors import to_rgb

from plotstyle.color._rendering import _fig_to_rgb_array

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# ITU-R BT.709 luminance coefficients (used in both pixel and per-colour paths)
# ---------------------------------------------------------------------------

# These weights are defined as named constants rather than bare literals so
# that the formula is self-documenting and easy to update if a different
# colour space (e.g., BT.2020) is ever required.
_LUMA_R: float = 0.2126
_LUMA_G: float = 0.7152
_LUMA_B: float = 0.0722


# ---------------------------------------------------------------------------
# Per-colour luminance utilities
# ---------------------------------------------------------------------------


def rgb_to_luminance(r: float, g: float, b: float) -> float:
    """Compute the relative luminance of a colour using ITU-R BT.709.

    Relative luminance is the perceptual brightness of a colour normalised to
    ``[0, 1]``, where 0 is absolute black and 1 is absolute white.

    Args:
        r: Red channel value in ``[0, 1]``.
        g: Green channel value in ``[0, 1]``.
        b: Blue channel value in ``[0, 1]``.

    Returns
    -------
        Relative luminance in ``[0, 1]``.

    Examples
    --------
        >>> rgb_to_luminance(1.0, 0.0, 0.0)  # pure red
        0.2126
        >>> rgb_to_luminance(1.0, 1.0, 1.0)  # white
        1.0
        >>> rgb_to_luminance(0.0, 0.0, 0.0)  # black
        0.0

    Notes
    -----
        - The formula assumes *linear-light* (gamma-decoded) values.
          Matplotlib's ``to_rgb`` returns sRGB values; for strict correctness
          these should be linearised first.  For palette-comparison purposes
          (is one colour darker than another?) the approximation is sufficient.
    """
    return _LUMA_R * r + _LUMA_G * g + _LUMA_B * b


def luminance_delta(colors: list[str]) -> list[tuple[int, int, float]]:
    """Compute pairwise luminance differences between a list of colours.

    All unique pairs ``(i, j)`` with ``i < j`` are evaluated.  The results are
    sorted in *ascending* order of delta so that the most problematic pair
    (smallest contrast) appears first — convenient for threshold checks.

    Args:
        colors: Sequence of colour specifiers accepted by
            :func:`matplotlib.colors.to_rgb` (hex strings such as
            ``"#FF0000"``, named colours such as ``"red"``, etc.).

    Returns
    -------
        List of ``(idx_a, idx_b, delta)`` triples where ``idx_a`` and
        ``idx_b`` are 0-based indices into *colors* and ``delta`` is the
        absolute luminance difference in ``[0, 1]``.  Sorted ascending by
        ``delta``.  Returns an empty list if *colors* has fewer than two
        elements.

    Raises
    ------
        ValueError: If any element of *colors* is not a valid matplotlib
            colour specifier (propagated from :func:`matplotlib.colors.to_rgb`).

    Example:
        >>> pairs = luminance_delta(["#ffffff", "#000000", "#888888"])
        >>> pairs[0]  # smallest delta — white vs grey or black vs grey
        (1, 2, ...)

    Notes
    -----
        - Luminance values are computed once per colour and reused across all
          pairs, giving ``O(N)`` conversions and ``O(N²)`` comparisons.
    """
    if len(colors) < 2:
        return []

    # Compute luminance for each colour exactly once.
    luminances: list[float] = [rgb_to_luminance(*to_rgb(c)) for c in colors]

    pairs: list[tuple[int, int, float]] = [
        (i, j, abs(luminances[i] - luminances[j]))
        for i, j in itertools.combinations(range(len(luminances)), 2)
    ]

    # Sort ascending so the pair with the least contrast is at index 0.
    pairs.sort(key=lambda t: t[2])
    return pairs


def is_grayscale_safe(colors: list[str], *, threshold: float = 0.1) -> bool:
    """Check whether all colours in a palette are distinguishable in grayscale.

    A palette is considered grayscale-safe when *every* pair of colours has a
    luminance difference of at least *threshold*.  The default threshold of
    0.10 (10 % of full scale) is a practical minimum for print legibility;
    stricter workflows may require 0.15 or higher.

    Args:
        colors: Sequence of colour specifiers (see :func:`luminance_delta`).
        threshold: Minimum required luminance difference between every pair,
            expressed as a fraction of full scale (``0.0`` - ``1.0``).
            Defaults to ``0.1``.

    Returns
    -------
        ``True`` if every pairwise luminance delta is ≥ *threshold*;
        ``False`` if any pair falls below the threshold.  Returns ``True``
        for palettes with fewer than two colours (trivially safe).

    Raises
    ------
        ValueError: If *threshold* is outside ``[0, 1]``.
        ValueError: Propagated from :func:`luminance_delta` for invalid colour
            specifiers.

    Example:
        >>> is_grayscale_safe(["#000000", "#ffffff"], threshold=0.1)
        True
        >>> is_grayscale_safe(["#aaaaaa", "#bbbbbb"], threshold=0.1)
        False

    Notes
    -----
        - Only the first element of the sorted pairs list is inspected because
          :func:`luminance_delta` returns pairs in ascending delta order; if
          the smallest delta meets the threshold, all others do too.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"threshold must be in [0, 1], got {threshold!r}.")

    pairs = luminance_delta(colors)

    # An empty list means zero or one colour — trivially safe.
    if not pairs:
        return True

    # The list is sorted ascending; check only the minimum-delta pair.
    return pairs[0][2] >= threshold


# ---------------------------------------------------------------------------
# High-level preview helper
# ---------------------------------------------------------------------------


def preview_grayscale(fig: Figure) -> Figure:
    """Create a side-by-side Original / Grayscale comparison figure.

    Rasterises *fig* via the Agg backend and converts the pixel array to
    luminance grayscale using ITU-R BT.709 weights.  The comparison figure is
    sized so that both panels exactly match the source figure's pixel
    dimensions.

    Args:
        fig: Source :class:`~matplotlib.figure.Figure` to preview.
            Must use an Agg-compatible canvas (the default for non-interactive
            backends).

    Returns
    -------
        A *new* :class:`~matplotlib.figure.Figure` with two panels::

            [Original | Grayscale]

        The source figure is not modified.

    Raises
    ------
        AttributeError: If *fig*'s canvas does not support ``buffer_rgba``
            (non-Agg backends).

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from plotstyle.color.grayscale import preview_grayscale
        >>> fig, ax = plt.subplots()
        >>> ax.bar([1, 2, 3], [4, 7, 2], color=["#e41a1c", "#377eb8", "#4daf4a"])
        >>> comp = preview_grayscale(fig)
        >>> comp.savefig("grayscale_preview.png", dpi=150)

    Notes
    -----
        - The grayscale panel uses ``cmap="gray"`` with ``vmin=0`` and
          ``vmax=1`` to ensure the full dynamic range is displayed correctly
          regardless of the actual luminance spread in the figure.
        - ``tight_layout`` is applied with a small pad to minimise whitespace
          while keeping axis titles legible.
        - The returned figure is independent of *fig*; closing *fig* does not
          affect the comparison figure.
    """
    import matplotlib.pyplot as plt

    original: NDArray[np.uint8] = _fig_to_rgb_array(fig)

    # Convert to luminance grayscale using BT.709 coefficients.
    # Divide by 255 once on the weighted sum rather than normalising each
    # channel separately — equivalent but avoids two extra array allocations.
    gray: NDArray[np.float64] = (
        _LUMA_R * original[:, :, 0].astype(np.float64)
        + _LUMA_G * original[:, :, 1].astype(np.float64)
        + _LUMA_B * original[:, :, 2].astype(np.float64)
    ) / 255.0

    panel_h, panel_w = original.shape[:2]
    dpi: float = fig.dpi

    # Size the comparison figure so each panel preserves the source resolution.
    total_w: float = panel_w * 2 / dpi
    total_h: float = panel_h / dpi

    comp_fig, (ax_orig, ax_gray) = plt.subplots(1, 2, figsize=(total_w, total_h), dpi=dpi)

    ax_orig.imshow(original)
    ax_orig.set_title("Original", fontsize=8)
    ax_orig.axis("off")

    # vmin/vmax are set explicitly so that a figure dominated by a single
    # luminance value is not auto-contrast-stretched, preserving print fidelity.
    ax_gray.imshow(gray, cmap="gray", vmin=0.0, vmax=1.0)
    ax_gray.set_title("Grayscale", fontsize=8)
    ax_gray.axis("off")

    comp_fig.tight_layout(pad=0.5)
    return comp_fig
