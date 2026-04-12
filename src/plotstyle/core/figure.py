"""Dimension-aware figure and subplot creation.

This module provides drop-in replacements for :func:`matplotlib.pyplot.figure`
and :func:`matplotlib.pyplot.subplots` that automatically size figures to
match a journal's column-width constraints.

``figure``
    Create a single-axis figure whose dimensions conform to a journal spec.

``subplots``
    Create a multi-panel figure, optionally annotated with spec-accurate
    panel labels (a, b, c, …).

Both functions resolve the journal spec from the built-in registry and convert
physical column widths from millimetres to inches before delegating to
Matplotlib.

Design notes
------------
The golden ratio (φ ≈ 1.618) is used as the default aspect ratio because it
produces visually balanced figures without requiring explicit height
specification.  Pass *aspect* to override it for any figure where a different
proportion is preferred (e.g. square plots or wide panoramic layouts).

Panel label normalisation
~~~~~~~~~~~~~~~~~~~~~~~~~
:func:`subplots` always returns an ``ndarray`` for the axes argument —
including the ``nrows=1, ncols=1`` case — so that callers can use ``.flat``
iteration and ``[i, j]`` indexing uniformly.  This diverges slightly from
vanilla Matplotlib, which returns a bare :class:`~matplotlib.axes.Axes` for
the single-panel case; the difference is intentional and documented on the
:func:`subplots` return value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import matplotlib.pyplot as plt
import numpy as np

from plotstyle.specs import registry
from plotstyle.specs.units import Dimension

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "figure",
    "subplots",
]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# The golden ratio φ = (1 + √5) / 2 ≈ 1.618.  Used as the default
# width-to-height aspect ratio; it is widely considered the most visually
# harmonious rectangle proportion and is a common default in scientific figure
# guidelines.
_GOLDEN_RATIO: Final[float] = (1 + 5**0.5) / 2

# Valid column-span values accepted by the public API.  Stored as a frozenset
# so membership tests are O(1) and the collection is clearly immutable.
_VALID_COLUMNS: Final[frozenset[int]] = frozenset({1, 2})

# Axes-normalised coordinates for panel label placement.  Placing labels
# slightly outside the axes box (negative x, y > 1) is the dominant
# convention in multi-panel scientific figures and avoids overlap with axis
# ticks and tick labels.
_LABEL_X: Final[float] = -0.1
_LABEL_Y: Final[float] = 1.05

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_columns(columns: int) -> None:
    """Raise :exc:`ValueError` if *columns* is not a supported span value.

    Centralising this check avoids duplicating the error message across
    :func:`_resolve_width` and any future callers that accept a *columns*
    parameter.

    Args:
        columns: Column-span value to validate.

    Raises
    ------
        ValueError: If *columns* is not in ``{1, 2}``.
    """
    if columns not in _VALID_COLUMNS:
        raise ValueError(
            f"'columns' must be 1 (single-column) or 2 (double-column), "
            f"got {columns!r}. "
            "Check the journal spec for supported column widths."
        )


def _resolve_width(journal: str, columns: int) -> float:
    """Resolve the figure width in inches for a journal and column span.

    Fetches the journal spec from the registry, selects the appropriate
    physical column width in millimetres, and converts it to inches using
    :class:`~plotstyle.specs.units.Dimension`.

    Args:
        journal: Journal preset name (e.g. ``"nature"``).
        columns: Column span: ``1`` for single-column width, ``2`` for
            double-column width.

    Returns
    -------
        Figure width in inches.

    Raises
    ------
        ValueError: If *columns* is not ``1`` or ``2``.
        plotstyle.specs.SpecNotFoundError: If *journal* is not registered.
    """
    _validate_columns(columns)

    spec: JournalSpec = registry.get(journal)

    # Select the physical width from the spec based on the column span.
    # Double-column figures span the full text width; single-column figures
    # span only the narrower inset width.
    width_mm: float = (
        spec.dimensions.double_column_mm if columns == 2 else spec.dimensions.single_column_mm
    )

    return Dimension(width_mm, "mm").to_inches()


def _format_panel_label(index: int, spec: JournalSpec) -> str:
    """Format a single panel label string from a zero-based index and spec.

    The label style (case, parentheses, sentence capitalisation) is driven
    by :attr:`~plotstyle.specs.schema.TypographySpec.panel_label_case` on
    the journal spec.

    Args:
        index: Zero-based panel index.  Index ``0`` maps to the letter
            ``"a"`` (or its styled equivalent), index ``1`` to ``"b"``,
            and so on.  Valid range is ``0`` to ``701`` inclusive.
        spec: Journal specification containing panel label formatting rules.

    Returns
    -------
        Formatted panel label string (e.g. ``"a"``, ``"(B)"``, ``"A"``).

    Raises
    ------
        ValueError: If *index* is >= 702 (beyond the two-character ``"zz"``
            label).

    Notes
    -----
        Supported ``panel_label_case`` values and their output:

        ================  =========================================
        Value             Output for indices 0, 1, 2
        ================  =========================================
        ``"lower"``       ``a``, ``b``, ``c``
        ``"upper"``       ``A``, ``B``, ``C``
        ``"title"``       ``A``, ``B``, ``C`` (alias for upper)
        ``"parens_lower"``  ``(a)``, ``(b)``, ``(c)``
        ``"parens_upper"``  ``(A)``, ``(B)``, ``(C)``
        ``"sentence"``    ``A``, ``b``, ``c`` (first only capitalised)
        ================  =========================================

        Any unrecognised value falls back to ``"lower"``.
    """
    # Derive the base lowercase letter(s) from the zero-based index.
    # Indices 0-25 map to a-z; indices 26-701 produce two-character labels
    # (aa, ab, ..., zz).  Index 702+ would overflow beyond 'z' in the first
    # character, so we reject it explicitly.
    if index < 26:
        letter: str = chr(ord("a") + index)
    elif index < 702:
        i = index - 26
        letter = chr(ord("a") + i // 26) + chr(ord("a") + i % 26)
    else:
        raise ValueError(f"Panel index {index} exceeds the maximum supported label range (0-701).")
    case: str = spec.typography.panel_label_case

    match case:
        case "upper" | "title":
            return letter.upper()
        case "parens_lower":
            return f"({letter})"
        case "parens_upper":
            return f"({letter.upper()})"
        case "sentence":
            # Sentence case: capitalise only the first panel, mirroring
            # the convention used in journals such as Cell and eLife.
            return letter.upper() if index == 0 else letter
        case _:
            # "lower" is the explicit default; unknown values fall through
            # here rather than raising so that newer spec fields added in
            # future schema versions degrade gracefully.
            return letter


def _add_panel_labels(axes: np.ndarray, spec: JournalSpec) -> None:
    """Annotate every axes in *axes* with a spec-accurate panel label.

    Labels are placed at a fixed position just above and to the left of each
    axes bounding box, using the font size and weight prescribed by the
    journal spec.  This position (``x=-0.1, y=1.05`` in axes-normalised
    coordinates) is the most common convention across biology and physics
    journals.

    Args:
        axes: 2-D ``ndarray`` of :class:`~matplotlib.axes.Axes` objects.
            Must support ``.flat`` iteration (i.e. be the output of
            :func:`numpy.atleast_2d` or equivalent).
        spec: Journal specification defining label style, font size, and
            font weight.

    Notes
    -----
        The function mutates each axes in-place by calling
        :meth:`~matplotlib.axes.Axes.text`.  It returns ``None``; callers
        that need to manipulate the label :class:`~matplotlib.text.Text`
        objects after the fact should call :func:`_format_panel_label`
        directly and manage text placement themselves.
    """
    for idx, ax in enumerate(axes.flat):
        label: str = _format_panel_label(idx, spec)
        ax.text(
            _LABEL_X,
            _LABEL_Y,
            label,
            transform=ax.transAxes,
            fontsize=spec.typography.panel_label_pt,
            fontweight=spec.typography.panel_label_weight,
            va="bottom",
            ha="right",
        )


def _compute_figsize(width_in: float, aspect: float | None) -> tuple[float, float]:
    """Compute ``(width, height)`` in inches given a width and optional aspect.

    Args:
        width_in: Figure width in inches.
        aspect: Width-to-height ratio.  When ``None``, the golden ratio is
            used as the default.

    Returns
    -------
        A ``(width_in, height_in)`` tuple ready to be passed to
        ``plt.subplots(figsize=...)``.
    """
    ratio: float = aspect if aspect is not None else _GOLDEN_RATIO
    return width_in, width_in / ratio


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def figure(
    journal: str,
    *,
    columns: int = 1,
    aspect: float | None = None,
) -> tuple[Figure, Axes]:
    """Create a single-axis figure sized to a journal's column width.

    Resolves the journal spec from the registry, converts the physical column
    width from millimetres to inches, and creates a Matplotlib figure with
    ``constrained_layout`` enabled so that labels and titles fit within the
    exported dimensions.

    Args:
        journal: Journal preset name (e.g. ``"nature"``).
        columns: Column span: ``1`` (default) for single-column width,
            ``2`` for double-column (full-text) width.
        aspect: Width-to-height ratio for the figure.  Defaults to the
            golden ratio (≈ 1.618) when ``None``.

    Returns
    -------
        A ``(fig, ax)`` tuple containing the new
        :class:`~matplotlib.figure.Figure` and its single
        :class:`~matplotlib.axes.Axes`.

    Raises
    ------
        ValueError: If *columns* is not ``1`` or ``2``.
        plotstyle.specs.SpecNotFoundError: If *journal* is not registered.

    Example::

        import plotstyle

        fig, ax = plotstyle.figure("nature")
        ax.plot([1, 2, 3], [4, 5, 6])
        plotstyle.savefig(fig, "figure.pdf", journal="nature")
    """
    width_in: float = _resolve_width(journal, columns)
    figsize: tuple[float, float] = _compute_figsize(width_in, aspect)

    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    return fig, ax


def subplots(
    journal: str,
    nrows: int = 1,
    ncols: int = 1,
    *,
    columns: int = 1,
    panels: bool = True,
    aspect: float | None = None,
) -> tuple[Figure, np.ndarray]:
    """Create a multi-panel figure sized to a journal's column width.

    Resolves the journal spec, sizes the figure to the requested column span,
    and optionally annotates each axes with a spec-accurate panel label
    (``a``, ``b``, ``c``, …).

    Args:
        journal: Journal preset name (e.g. ``"nature"``).
        nrows: Number of subplot rows.  Defaults to ``1``.
        ncols: Number of subplot columns.  Defaults to ``1``.
        columns: Column span: ``1`` (default) for single-column width,
            ``2`` for double-column (full-text) width.
        panels: When ``True`` (default), annotates each axes with a
            panel label styled according to the journal specification.
            Pass ``False`` to suppress labels entirely.
        aspect: Width-to-height ratio for the whole figure.  Defaults to
            the golden ratio (≈ 1.618) when ``None``.

    Returns
    -------
        A ``(fig, axes)`` tuple where *axes* is always a 2-D
        :class:`numpy.ndarray` of :class:`~matplotlib.axes.Axes` objects
        with shape ``(nrows, ncols)``.

    Raises
    ------
        ValueError: If *columns* is not ``1`` or ``2``.
        plotstyle.specs.SpecNotFoundError: If *journal* is not registered.

    Notes
    -----
        **Return-shape divergence from Matplotlib** — unlike
        :func:`matplotlib.pyplot.subplots`, this function *always* returns
        a 2-D ``ndarray``, including the ``nrows=1, ncols=1`` case.
        This guarantees that callers can use ``.flat`` iteration and
        ``axes[i, j]`` indexing without special-casing the single-panel
        path.  Access the bare :class:`~matplotlib.axes.Axes` via
        ``axes[0, 0]`` when needed.

    Example::

        import plotstyle

        fig, axes = plotstyle.subplots("nature", nrows=2, ncols=2, columns=2)
        for ax in axes.flat:
            ax.plot([1, 2, 3])
    """
    spec: JournalSpec = registry.get(journal)
    width_in: float = _resolve_width(journal, columns)
    figsize: tuple[float, float] = _compute_figsize(width_in, aspect)

    fig, axes_raw = plt.subplots(
        nrows,
        ncols,
        figsize=figsize,
        constrained_layout=True,
    )

    # Normalise the axes return value to a 2-D ndarray so that panel label
    # placement and downstream callers can always rely on a consistent shape.
    #
    # Matplotlib returns:
    #   - a bare Axes   when nrows=1 and ncols=1
    #   - a 1-D ndarray when nrows=1 xor ncols=1
    #   - a 2-D ndarray when nrows > 1 and ncols > 1
    #
    # reshape(nrows, ncols) handles the 1-D case correctly for both
    # nrows>1,ncols=1 and nrows=1,ncols>1; the bare-Axes case requires
    # wrapping in a nested list first so that atleast_2d produces (1, 1).
    if isinstance(axes_raw, np.ndarray):
        axes_2d: np.ndarray = axes_raw.reshape(nrows, ncols)
    else:
        # Single bare Axes — wrap in a 2-D array to yield shape (1, 1).
        axes_2d = np.atleast_2d(np.array(axes_raw))

    if panels:
        _add_panel_labels(axes_2d, spec)

    return fig, axes_2d
