"""Render a 2x2 sample figure grid in a journal's style."""

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

_GALLERY_ASPECT: Final[float] = 0.9
_DEFAULT_SEED: Final[int] = 42
_VALID_COLUMNS: Final[frozenset[int]] = frozenset({1, 2})
_SCATTER_N: Final[int] = 80
_HIST_N: Final[int] = 500
_SCATTER_GROUPS: Final[list[str]] = ["A", "B", "C"]


def _sample_line_data() -> tuple[NDArray[np.float64], list[NDArray[np.float64]]]:
    """Return ``(x, ys)`` with four periodic curves over ``[0, 2π]``."""
    x = np.linspace(0, 2 * np.pi, 100)
    ys = [
        np.sin(x),
        np.cos(x),
        np.sin(2 * x) * 0.5,
        np.cos(2 * x) * 0.7,
    ]
    return x, ys


def _sample_scatter_data(
    seed: int = _DEFAULT_SEED,
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.str_]]:
    """Return ``(x, y, groups)`` for a noisy linear scatter across three groups."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, _SCATTER_N)
    y = 0.8 * x + rng.normal(0, 0.4, _SCATTER_N)
    groups = rng.choice(np.array(_SCATTER_GROUPS, dtype=str), size=_SCATTER_N)
    return x, y, groups


def _sample_bar_data() -> tuple[list[str], list[float], list[float]]:
    """Return ``(categories, values, errors)`` for a fixed bar-chart preview."""
    categories = ["Cat A", "Cat B", "Cat C", "Cat D"]
    values = [4.2, 7.1, 3.8, 5.9]
    errors = [0.5, 0.8, 0.3, 0.6]
    return categories, values, errors


def _sample_histogram_data(seed: int = _DEFAULT_SEED) -> NDArray[np.float64]:
    """Return a 1-D array of :data:`_HIST_N` standard-normal samples."""
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, _HIST_N)


def _draw_line_panel(ax: Axes) -> None:
    """Draw four periodic curves with a legend."""
    x, ys = _sample_line_data()
    for i, y in enumerate(ys):
        ax.plot(x, y, label=f"Series {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(fontsize="small")
    ax.set_title("Line Plot", fontsize="small")


def _draw_scatter_panel(ax: Axes) -> None:
    """Draw three labelled scatter groups."""
    x, y, groups = _sample_scatter_data()
    for group_label in np.unique(groups):
        mask = groups == group_label
        ax.scatter(x[mask], y[mask], label=str(group_label), s=15, alpha=0.8)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend(fontsize="small")
    ax.set_title("Scatter Plot", fontsize="small")


def _draw_bar_panel(ax: Axes) -> None:
    """Draw a bar chart with error bars."""
    categories, values, errors = _sample_bar_data()
    ax.bar(categories, values, yerr=errors, capsize=3)
    ax.set_ylabel("Value")
    ax.set_title("Bar Chart", fontsize="small")


def _draw_histogram_panel(ax: Axes) -> None:
    """Draw a histogram with 25 bins of standard-normal data."""
    data = _sample_histogram_data()
    ax.hist(data, bins=25, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Value")
    ax.set_ylabel("Count")
    ax.set_title("Histogram", fontsize="small")


_PANEL_DRAWERS: Final[list[Any]] = [
    _draw_line_panel,
    _draw_scatter_panel,
    _draw_bar_panel,
    _draw_histogram_panel,
]


def gallery(journal: str, *, columns: int = 1) -> Figure:
    """Return a 2x2 figure of sample plots styled to *journal*.

    rcParams are restored unconditionally after creation.

    Parameters
    ----------
    journal : str
        Journal preset name (e.g. ``"nature"``).
    columns : int
        Column span: ``1`` (default) or ``2``.

    Returns
    -------
    Figure
        A 2x2 :class:`~matplotlib.figure.Figure` with one line plot, one
        scatter plot, one bar chart, and one histogram, all styled to
        *journal*.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If *journal* is not registered.
    ValueError
        If *columns* is not ``1`` or ``2``.
    """
    if columns not in _VALID_COLUMNS:
        raise ValueError(
            f"'columns' must be 1 (single-column) or 2 (double-column), got {columns!r}."
        )

    style = use(journal)
    spec = style.spec

    width_mm = (
        spec.dimensions.double_column_mm if columns == 2 else spec.dimensions.single_column_mm
    )
    width_in = Dimension(width_mm, "mm").to_inches()
    height_in = width_in * _GALLERY_ASPECT

    try:
        fig, axes = plt.subplots(
            2,
            2,
            figsize=(width_in, height_in),
            constrained_layout=True,
        )

        for draw_panel, ax in zip(_PANEL_DRAWERS, axes.flat, strict=True):
            draw_panel(ax)

        fig.suptitle(
            f"{spec.metadata.name} Style Preview",
            fontsize=spec.typography.max_font_pt + 1,
            fontweight="bold",
        )

        return fig

    finally:
        style.restore()
