"""Colorblind simulation using Machado et al. (2009) severity-1.0 matrices.

Provides tools for simulating how figures appear to viewers with colour
vision deficiencies (CVD) and for generating side-by-side preview panels.

Public API
----------
:class:`CVDType`
    Enumeration of the three supported CVD variants: deuteranopia,
    protanopia, and tritanopia.

:data:`SIMULATION_MATRICES`
    Raw 3x3 transformation matrices keyed by :class:`CVDType`.

:func:`simulate_cvd`
    Apply a CVD simulation matrix to an RGB image array.

:func:`preview_colorblind`
    Return a new figure with side-by-side CVD-simulated panels.

Exceptions
----------
:class:`CVDSimulationError`
    Raised when *image* has an unexpected shape.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Final

import numpy as np

from plotstyle.color._rendering import _fig_to_rgb_array

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from numpy.typing import NDArray

__all__: list[str] = [
    "SIMULATION_MATRICES",
    "CVDSimulationError",
    "CVDType",
    "preview_colorblind",
    "simulate_cvd",
]


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class CVDSimulationError(ValueError):
    """Raised when a CVD simulation cannot be completed due to an unexpected image shape."""


# ---------------------------------------------------------------------------
# CVD type enumeration
# ---------------------------------------------------------------------------


class CVDType(str, enum.Enum):
    """Colour vision deficiency types supported by the simulation engine.

    Variants: ``DEUTERANOPIA``, ``PROTANOPIA``, ``TRITANOPIA``.
    """

    DEUTERANOPIA = "deuteranopia"
    PROTANOPIA = "protanopia"
    TRITANOPIA = "tritanopia"


# ---------------------------------------------------------------------------
# Simulation matrices (Machado et al., 2009 — severity = 1.0)
# ---------------------------------------------------------------------------

#: Raw 3x3 CVD simulation matrices keyed by :class:`CVDType` (Machado et al., 2009, severity = 1.0).
SIMULATION_MATRICES: Final[dict[CVDType, list[list[float]]]] = {
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

_SIMULATION_MATRICES_NP: Final[dict[CVDType, NDArray[np.float64]]] = {
    cvd: np.array(matrix, dtype=np.float64) for cvd, matrix in SIMULATION_MATRICES.items()
}


# ---------------------------------------------------------------------------
# Core simulation function
# ---------------------------------------------------------------------------


def simulate_cvd(
    image: NDArray[np.floating | np.integer],
    cvd_type: CVDType,
) -> NDArray[np.float64]:
    """Apply *cvd_type* simulation to an RGB image array of shape ``(H, W, 3)``.

    Parameters
    ----------
    image : NDArray[np.floating | np.integer]
        RGB array; ``uint8`` values are normalised to ``[0, 1]`` automatically.
    cvd_type : CVDType
        CVD variant to simulate.

    Returns
    -------
    NDArray[np.float64]
        ``float64`` array of shape ``(H, W, 3)`` with values in ``[0, 1]``.

    Raises
    ------
    CVDSimulationError
        If *image* shape is not ``(H, W, 3)``.
    """
    arr = np.asarray(image)
    needs_normalize = np.issubdtype(arr.dtype, np.integer)
    img = np.asarray(arr, dtype=np.float64)

    if img.ndim != 3 or img.shape[2] != 3:
        raise CVDSimulationError(
            f"Expected an RGB image with shape (H, W, 3), got shape {img.shape}."
        )

    if needs_normalize:
        img /= 255.0

    result = img @ _SIMULATION_MATRICES_NP[cvd_type].T
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
    """Return a new figure with side-by-side CVD simulations of *fig*.

    Parameters
    ----------
    fig : Figure
        Source figure (must use an Agg canvas).
    cvd_types : list[CVDType] | None
        CVD variants to show.  Defaults to all three types.

    Returns
    -------
    Figure
        New figure laid out as ``[Original | <cvd_types...>]``.
    """
    import matplotlib.pyplot as plt

    active_cvd_types = cvd_types if cvd_types is not None else list(CVDType)
    original = _fig_to_rgb_array(fig)

    ncols = 1 + len(active_cvd_types)
    panel_h, panel_w = original.shape[:2]
    dpi = fig.dpi
    total_w = panel_w * ncols / dpi
    total_h = panel_h / dpi

    comp_fig, axes = plt.subplots(1, ncols, figsize=(total_w, total_h), dpi=dpi)

    if ncols == 1:
        axes = [axes]

    axes[0].imshow(original)
    axes[0].set_title("Original", fontsize=8)
    axes[0].axis("off")

    for ax, cvd in zip(axes[1:], active_cvd_types, strict=False):
        simulated: NDArray[np.float64] = simulate_cvd(original, cvd)
        ax.imshow(simulated)
        ax.set_title(cvd.value.capitalize(), fontsize=8)
        ax.axis("off")

    comp_fig.tight_layout(pad=0.5)
    return comp_fig
