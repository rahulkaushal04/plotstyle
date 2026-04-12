"""Render a sample figure grid in a journal's style.

Provides :func:`gallery`, a quick-preview utility that creates a 2x2 grid of
representative plots — line, scatter, bar, and histogram — sized and styled to
match a journal's column width and typography constraints.

Design notes
------------
**Deterministic data** — the four ``_sample_*`` helpers generate synthetic
data from a fixed random seed (``42`` by default), so the preview is
pixel-identical across repeated calls.  Pass a different *seed* to the helpers
if variation is needed for testing.

**Style isolation** — :func:`gallery` applies the journal preset via
:func:`~plotstyle.core.style.use` and restores the original rcParams in a
``finally`` block.  Calling :func:`gallery` never permanently alters global
Matplotlib state, regardless of whether figure creation succeeds or raises.

**Panel configuration** — visual constants for each panel (titles, axis
labels, marker sizes, etc.) are centralised in :data:`_PANEL_CONFIG` rather
than scattered through the rendering code.  Adding a new panel or changing a
label requires editing only that mapping.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

import matplotlib.pyplot as plt
import numpy as np

from plotstyle.core.style import use
from plotstyle.specs.units import Dimension

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from numpy.typing import NDArray

__all__: list[str] = ["gallery"]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Height-to-width ratio for the gallery figure.  0.9 fills the available
# vertical space while keeping the figure compact enough for on-screen preview
# without excessive whitespace.
_GALLERY_ASPECT: Final[float] = 0.9

# Fixed random seed shared by all sample-data generators.  A module-level
# constant makes it trivial to find and change if reproducibility requirements
# change (e.g. switching to a property-based test with varied seeds).
_DEFAULT_SEED: Final[int] = 42

# Valid column-span values; mirrors plotstyle.core.figure for consistency
# without introducing a cross-module import dependency.
_VALID_COLUMNS: Final[frozenset[int]] = frozenset({1, 2})

# Number of samples for the scatter and histogram panels.
_SCATTER_N: Final[int] = 80
_HIST_N: Final[int] = 500

# Scatter plot groups.  Defined once so both the generator and the renderer
# agree on the set without magic string literals.
_SCATTER_GROUPS: Final[list[str]] = ["A", "B", "C"]

# ---------------------------------------------------------------------------
# Synthetic data generators
# ---------------------------------------------------------------------------


def _sample_line_data() -> tuple[NDArray[np.float64], list[NDArray[np.float64]]]:
    """Generate deterministic synthetic data for the line-plot panel.

    Produces four periodic curves (sin/cos at base and double frequency) that
    exercise the journal's colour cycle and line-weight settings.

    Returns
    -------
        A two-tuple ``(x, ys)`` where *x* is a 1-D array of 100 evenly
        spaced values over ``[0, 2π]`` and *ys* is a list of four
        corresponding y-arrays: ``sin(x)``, ``cos(x)``,
        ``0.5 · sin(2x)``, and ``0.7 · cos(2x)``.
    """
    x: NDArray[np.float64] = np.linspace(0, 2 * np.pi, 100)
    ys: list[NDArray[np.float64]] = [
        np.sin(x),
        np.cos(x),
        np.sin(2 * x) * 0.5,
        np.cos(2 * x) * 0.7,
    ]
    return x, ys


def _sample_scatter_data(
    seed: int = _DEFAULT_SEED,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.str_]]:
    """Generate deterministic synthetic data for the scatter-plot panel.

    Creates a noisy linear relationship across three labelled groups so the
    panel exercises colour, alpha, and marker-size rendering.

    Args:
        seed: NumPy default-RNG seed.  Defaults to :data:`_DEFAULT_SEED`
            (``42``) for reproducibility.

    Returns
    -------
        A three-tuple ``(x, y, groups)`` where *x* and *y* are correlated
        1-D float arrays of length :data:`_SCATTER_N`, and *groups* is a
        string array of the same length whose values are drawn from
        :data:`_SCATTER_GROUPS`.
    """
    rng = np.random.default_rng(seed)
    x: NDArray[np.float64] = rng.normal(0, 1, _SCATTER_N)
    # Linear relationship with additive Gaussian noise to produce a clear but
    # imperfect trend — more representative of real scientific scatter plots.
    y: NDArray[np.float64] = 0.8 * x + rng.normal(0, 0.4, _SCATTER_N)
    groups: NDArray[np.str_] = rng.choice(np.array(_SCATTER_GROUPS, dtype=str), size=_SCATTER_N)
    return x, y, groups


def _sample_bar_data() -> tuple[list[str], list[float], list[float]]:
    """Generate fixed synthetic data for the bar-chart panel.

    Returns fixed (non-random) values so the bar chart preview is always
    identical and requires no seed argument.

    Returns
    -------
        A three-tuple ``(categories, values, errors)`` containing lists of
        category labels, bar heights, and symmetric error-bar half-widths.
    """
    categories: list[str] = ["Cat A", "Cat B", "Cat C", "Cat D"]
    values: list[float] = [4.2, 7.1, 3.8, 5.9]
    errors: list[float] = [0.5, 0.8, 0.3, 0.6]
    return categories, values, errors


def _sample_histogram_data(seed: int = _DEFAULT_SEED) -> NDArray[np.float64]:
    """Generate deterministic synthetic data for the histogram panel.

    Args:
        seed: NumPy default-RNG seed.  Defaults to :data:`_DEFAULT_SEED`
            (``42``) for reproducibility.

    Returns
    -------
        A 1-D array of :data:`_HIST_N` standard-normal samples, suitable
        for demonstrating the journal's bar-fill and edge-colour styles.
    """
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, _HIST_N)


# ---------------------------------------------------------------------------
# Panel rendering helpers
# ---------------------------------------------------------------------------


def _draw_line_panel(ax: Axes) -> None:
    """Populate the line-plot panel with four periodic curves and a legend.

    Args:
        ax: Target :class:`~matplotlib.axes.Axes` to draw into.
    """
    x, ys = _sample_line_data()
    for i, y in enumerate(ys):
        ax.plot(x, y, label=f"Series {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(fontsize="small")
    ax.set_title("Line Plot", fontsize="small")


def _draw_scatter_panel(ax: Axes) -> None:
    """Populate the scatter-plot panel with three labelled groups.

    Uses :func:`numpy.unique` to iterate over groups in sorted order, which
    is more idiomatic than ``sorted(set(...))`` for NumPy string arrays and
    avoids a Python-level sort on a large array.

    Args:
        ax: Target :class:`~matplotlib.axes.Axes` to draw into.
    """
    x, y, groups = _sample_scatter_data()
    for group_label in np.unique(groups):
        mask: NDArray[np.bool_] = groups == group_label
        ax.scatter(x[mask], y[mask], label=str(group_label), s=15, alpha=0.8)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(fontsize="small")
    ax.set_title("Scatter Plot", fontsize="small")


def _draw_bar_panel(ax: Axes) -> None:
    """Populate the bar-chart panel with error bars.

    Args:
        ax: Target :class:`~matplotlib.axes.Axes` to draw into.
    """
    categories, values, errors = _sample_bar_data()
    ax.bar(categories, values, yerr=errors, capsize=3)
    ax.set_ylabel("Value")
    ax.set_title("Bar Chart", fontsize="small")


def _draw_histogram_panel(ax: Axes) -> None:
    """Populate the histogram panel with 25 bins of standard-normal data.

    Args:
        ax: Target :class:`~matplotlib.axes.Axes` to draw into.
    """
    data: NDArray[np.float64] = _sample_histogram_data()
    ax.hist(data, bins=25, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Value")
    ax.set_ylabel("Count")
    ax.set_title("Histogram", fontsize="small")


# Panel drawing functions in row-major order, matching the 2x2 axes layout
# produced by plt.subplots(2, 2).  Each callable accepts a single Axes arg.
# To add a new panel: extend the grid dimensions, add a helper above, and
# append it here — no other code changes are required.
_PANEL_DRAWERS: Final[
    list[Any]  # list[Callable[[Axes], None]] — Callable not usable as Final type arg
] = [
    _draw_line_panel,
    _draw_scatter_panel,
    _draw_bar_panel,
    _draw_histogram_panel,
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def gallery(journal: str, *, columns: int = 1) -> Figure:
    """Render a 2x2 grid of sample plots in the given journal's style.

    Applies the journal preset via :func:`~plotstyle.core.style.use`, creates
    a figure sized to the journal's column width, and populates it with four
    representative plot types: line plot, scatter plot, bar chart, and
    histogram.  The original rcParams are always restored after the figure is
    created.

    Args:
        journal: Journal preset name (e.g. ``"nature"``, ``"ieee"``).
        columns: Column span for the figure: ``1`` (default) for
            single-column width, ``2`` for double-column width.

    Returns
    -------
        A :class:`~matplotlib.figure.Figure` containing four styled subplots,
        ready to display with ``plt.show()`` or save with
        :func:`~plotstyle.core.export.savefig`.

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If *journal* is not registered in
            the spec registry.
        ValueError: If *columns* is not ``1`` or ``2``.

    Notes
    -----
        **Style isolation** — the journal style is applied only for the
        duration of this call.  rcParams are restored unconditionally in a
        ``finally`` block so a failed :func:`gallery` call never leaves global
        Matplotlib state modified.

        **Determinism** — all synthetic data is generated from a fixed seed
        (``42`` by default), so the figure is pixel-identical across
        repeated calls with the same arguments.

        **Supra-title sizing** — the figure title is set one point above the
        journal's ``max_font_pt`` so it reads as a heading without violating
        the journal's body-text constraint.

    Example::

        import matplotlib.pyplot as plt
        import plotstyle

        fig = plotstyle.gallery("nature", columns=1)
        plt.show()

        # Save directly:
        plotstyle.savefig(fig, "nature_preview.pdf", journal="nature")
    """
    if columns not in _VALID_COLUMNS:
        raise ValueError(
            f"'columns' must be 1 (single-column) or 2 (double-column), got {columns!r}."
        )

    # Apply the journal style and retain the handle so we can call restore()
    # in the finally block without a second registry lookup.
    style = use(journal)
    spec = style.spec

    # Resolve the physical figure dimensions from the spec.
    width_mm: float = (
        spec.dimensions.double_column_mm if columns == 2 else spec.dimensions.single_column_mm
    )
    width_in: float = Dimension(width_mm, "mm").to_inches()
    height_in: float = width_in * _GALLERY_ASPECT

    try:
        fig, axes = plt.subplots(
            2,
            2,
            figsize=(width_in, height_in),
            constrained_layout=True,
        )

        # Dispatch each panel drawer to its corresponding axes in row-major
        # order.  axes.flat guarantees a consistent iteration order regardless
        # of the nrows/ncols layout.
        for draw_panel, ax in zip(_PANEL_DRAWERS, axes.flat, strict=True):
            draw_panel(ax)

        # Title is set one point above max_font_pt to serve as a visual
        # heading that stands apart from body-text elements without exceeding
        # a reasonable scale relative to the journal's typography system.
        fig.suptitle(
            f"{spec.metadata.name} Style Preview",
            fontsize=spec.typography.max_font_pt + 1,
            fontweight="bold",
        )

        return fig

    finally:
        # Restore the prior rcParams unconditionally so that a failed figure
        # creation does not leave the process in a modified global state.
        style.restore()
