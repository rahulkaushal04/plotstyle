"""Colorblind simulation engine using Machado et al. (2009) matrices.

This module provides tools for simulating color vision deficiencies (CVD) on
matplotlib figures.  Simulations are performed entirely in NumPy — no external
imaging libraries (e.g., Pillow) are required.

Supported deficiency types (via :class:`CVDType`):
    - **Deuteranopia** — reduced sensitivity to green light (~6 % of males).
    - **Protanopia**   — reduced sensitivity to red light  (~2 % of males).
    - **Tritanopia**   — reduced sensitivity to blue light (< 0.01 % of population).

The simulation matrices are taken from:

    Machado, G. M., Oliveira, M. M., & Fernandes, L. A. (2009).
    *A Physiologically-based Model for Simulation of Color Vision Deficiency*.
    IEEE Transactions on Visualization and Computer Graphics, 15(6), 1291-1298.
    https://doi.org/10.1109/TVCG.2009.113

All matrices correspond to severity = 1.0 (complete dichromacy).

Example
-------
    >>> import matplotlib.pyplot as plt
    >>> from plotstyle.color.accessibility import preview_colorblind, CVDType
    >>> fig, ax = plt.subplots()
    >>> ax.scatter([1, 2, 3], [4, 5, 6], c=["#e41a1c", "#377eb8", "#4daf4a"])
    >>> comp = preview_colorblind(fig, cvd_types=[CVDType.DEUTERANOPIA])
    >>> plt.show()
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

import numpy as np

from plotstyle.color._rendering import _fig_to_rgb_array

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class CVDSimulationError(ValueError):
    """Raised when a CVD simulation cannot be completed.

    This exception wraps lower-level errors (e.g., unexpected image shapes or
    unsupported CVD types) with a more actionable message for callers.
    """


# ---------------------------------------------------------------------------
# CVD type enumeration
# ---------------------------------------------------------------------------


class CVDType(str, enum.Enum):
    """Enumeration of supported colour vision deficiency types.

    Inheriting from ``str`` allows instances to be used wherever a plain
    string is expected (e.g., as a dictionary key or in a log message) without
    an explicit ``.value`` access.

    Members:
        DEUTERANOPIA: Deficiency in M-cone (green) response.
        PROTANOPIA:   Deficiency in L-cone (red) response.
        TRITANOPIA:   Deficiency in S-cone (blue) response.
    """

    DEUTERANOPIA = "deuteranopia"
    PROTANOPIA = "protanopia"
    TRITANOPIA = "tritanopia"


# ---------------------------------------------------------------------------
# Simulation matrices (Machado et al., 2009 — severity = 1.0)
# ---------------------------------------------------------------------------

# Each 3x3 matrix transforms *linear* sRGB tristimulus values into the
# corresponding dichromatic colour space.  Rows correspond to output R, G, B
# channels; columns correspond to input R, G, B channels.
#
# These constants are defined at module level so that they are instantiated
# once and shared across all calls to ``simulate_cvd``.
SIMULATION_MATRICES: dict[CVDType, list[list[float]]] = {
    CVDType.DEUTERANOPIA: [
        [0.367, 0.861, -0.228],
        [0.280, 0.673, 0.047],
        [-0.012, 0.043, 0.969],
    ],
    CVDType.PROTANOPIA: [
        [0.152, 1.053, -0.205],
        [0.115, 0.786, 0.099],
        [-0.004, -0.048, 1.052],
    ],
    CVDType.TRITANOPIA: [
        [1.256, -0.077, -0.179],
        [-0.078, 0.931, 0.148],
        [0.005, 0.691, 0.304],
    ],
}

# Pre-compute numpy arrays from the nested lists once at import time so that
# ``simulate_cvd`` avoids redundant ``np.array`` construction on every call.
_SIMULATION_MATRICES_NP: dict[CVDType, NDArray[np.float64]] = {
    cvd: np.array(matrix, dtype=np.float64) for cvd, matrix in SIMULATION_MATRICES.items()
}


# ---------------------------------------------------------------------------
# Core simulation function
# ---------------------------------------------------------------------------


def simulate_cvd(
    image: NDArray[np.floating | np.integer],
    cvd_type: CVDType,
) -> NDArray[np.float64]:
    """Apply a colour vision deficiency simulation to an RGB image array.

    The input image is first normalised to the ``[0, 1]`` float range (if
    provided as ``uint8``), then each pixel's RGB triplet is multiplied by the
    corresponding Machado et al. simulation matrix.  The result is clipped to
    ``[0, 1]`` to handle any out-of-gamut values introduced by the transform.

    Args:
        image: RGB image array with shape ``(H, W, 3)``.
            Accepts either ``float`` values in ``[0, 1]`` or ``uint8`` values
            in ``[0, 255]``.  Other dtypes are cast to ``float64`` and assumed
            to already be in the ``[0, 1]`` range.
        cvd_type: The :class:`CVDType` variant to simulate.

    Returns
    -------
        Simulated image as a ``float64`` array with shape ``(H, W, 3)`` and
        values in ``[0, 1]``.

    Raises
    ------
        plotstyle.color.accessibility.CVDSimulationError: If *image* does not
            have exactly three channels (last dimension != 3) or if its number
            of dimensions is not 3.

    Example:
        >>> import numpy as np
        >>> img = np.random.rand(100, 100, 3).astype(np.float32)
        >>> result = simulate_cvd(img, CVDType.PROTANOPIA)
        >>> result.shape
        (100, 100, 3)
        >>> result.dtype
        dtype('float64')

    Notes
    -----
        - The matrices assume *linear* sRGB input.  Matplotlib's Agg renderer
          outputs gamma-encoded sRGB (approximately gamma 2.2), so simulation
          results are an approximation rather than a physically exact model.
          For publication-quality accuracy, linearise the input before calling
          this function.
        - The matrix multiplication is vectorised over the spatial dimensions
          via ``@ matrix.T``, giving an ``O(H * W)`` operation without Python
          loops.
    """
    needs_normalize = np.issubdtype(np.asarray(image).dtype, np.integer)
    img = np.asarray(image, dtype=np.float64)

    if img.ndim != 3 or img.shape[2] != 3:
        raise CVDSimulationError(
            f"Expected an RGB image with shape (H, W, 3), got shape {img.shape}."
        )

    # Normalise integer images (values in [0, 255]) to the [0, 1] float range.
    if needs_normalize:
        img = img / 255.0

    matrix: NDArray[np.float64] = _SIMULATION_MATRICES_NP[cvd_type]

    # Batch matrix-vector multiply: each (3,) pixel is transformed by matrix.
    # Using ``@ matrix.T`` avoids an explicit reshape and leverages BLAS.
    result: NDArray[np.float64] = img @ matrix.T

    # Clip to [0, 1] in-place to handle gamut violations from the linear
    # transform without allocating a new array.
    np.clip(result, 0.0, 1.0, out=result)
    return result


# ---------------------------------------------------------------------------
# High-level preview helper
# ---------------------------------------------------------------------------


def preview_colorblind(
    fig: Figure,
    *,
    cvd_types: list[CVDType] | None = None,
) -> Figure:
    """Create a side-by-side comparison figure under CVD simulations.

    Renders the source figure once via the Agg backend, then applies each
    requested CVD simulation to the resulting pixel array.  All panels are
    laid out in a single row so that differences are immediately visible.

    The output layout is::

        [ Original | <cvd_types[0]> | <cvd_types[1]> | ... ]

    Args:
        fig: Source :class:`~matplotlib.figure.Figure` to simulate.
            Must use an Agg-compatible canvas (the default for non-interactive
            backends).
        cvd_types: List of :class:`CVDType` variants to include.  Defaults to
            all three types: ``[DEUTERANOPIA, PROTANOPIA, TRITANOPIA]``.

    Returns
    -------
        A *new* :class:`~matplotlib.figure.Figure` containing one panel per
        CVD type plus the original.  The source figure is not modified.

    Raises
    ------
        plotstyle.color.accessibility.CVDSimulationError: Propagated from
            :func:`simulate_cvd` if the rasterised image has an unexpected
            shape.
        AttributeError: If *fig*'s canvas does not support ``buffer_rgba``
            (non-Agg backends).

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from plotstyle.color.accessibility import preview_colorblind
        >>> fig, ax = plt.subplots()
        >>> ax.plot([0, 1, 2], [0, 1, 0], color="#e41a1c")
        >>> comp = preview_colorblind(fig)
        >>> comp.savefig("cvd_preview.png", dpi=150)

    Notes
    -----
        - The comparison figure is sized so that each panel matches the source
          figure's pixel dimensions exactly, preventing any implicit rescaling.
        - ``tight_layout`` is applied with a small pad to reduce whitespace
          between panels while keeping axis titles legible.
        - The returned figure is independent of *fig*; closing *fig* does not
          affect the comparison figure.
    """
    import matplotlib.pyplot as plt

    # Fall back to all supported CVD types when the caller does not specify.
    active_cvd_types: list[CVDType] = cvd_types if cvd_types is not None else list(CVDType)

    # Rasterise the source figure once; reuse the array for all simulations.
    original: NDArray[np.uint8] = _fig_to_rgb_array(fig)

    ncols: int = 1 + len(active_cvd_types)
    panel_h, panel_w = original.shape[:2]
    dpi: float = fig.dpi

    # Size the comparison figure so each panel has the same pixel dimensions
    # as the source figure.
    total_w: float = panel_w * ncols / dpi
    total_h: float = panel_h / dpi

    comp_fig, axes = plt.subplots(1, ncols, figsize=(total_w, total_h), dpi=dpi)

    # ``plt.subplots`` returns a bare Axes (not a list) when ncols == 1;
    # wrap it so the loop below can treat both cases uniformly.
    if ncols == 1:
        axes = [axes]

    # Panel 0: unmodified original.
    axes[0].imshow(original)
    axes[0].set_title("Original", fontsize=8)
    axes[0].axis("off")

    # Panels 1-N: one simulated variant per requested CVD type.
    for ax, cvd in zip(axes[1:], active_cvd_types, strict=False):
        simulated: NDArray[np.float64] = simulate_cvd(original, cvd)
        ax.imshow(simulated)
        ax.set_title(cvd.value.capitalize(), fontsize=8)
        ax.axis("off")

    comp_fig.tight_layout(pad=0.5)
    return comp_fig
