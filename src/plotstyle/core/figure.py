"""Dimension-aware figure and subplot creation.

``figure``
    Create a single-axis figure whose dimensions conform to a journal spec.

``subplots``
    Create a multi-panel figure, optionally annotated with spec-accurate
    panel labels (a, b, c, …).

Both functions resolve the journal spec from the built-in registry and convert
physical column widths from millimetres to inches before delegating to
Matplotlib.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import matplotlib.pyplot as plt

from plotstyle.specs import registry
from plotstyle.specs.units import Dimension

if TYPE_CHECKING:
    import numpy as np
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

_GOLDEN_RATIO: Final[float] = (1 + 5**0.5) / 2
_VALID_COLUMNS: Final[frozenset[int]] = frozenset({1, 2})

# Standard panel-label position: just above and to the left of each axes box.
_LABEL_X: Final[float] = -0.1
_LABEL_Y: Final[float] = 1.05

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_columns(columns: int) -> None:
    """Raise :exc:`ValueError` if *columns* is not ``1`` or ``2``.

    Parameters
    ----------
    columns : int
        Column-span value to validate.

    Raises
    ------
    ValueError
        If *columns* is not in ``{1, 2}``.
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

    Parameters
    ----------
    journal : str
        Journal preset name (e.g. ``"nature"``).
    columns : int
        Column span: ``1`` for single-column width, ``2`` for
        double-column width.

    Returns
    -------
    float
        Figure width in inches.

    Raises
    ------
    ValueError
        If *columns* is not ``1`` or ``2``.
    plotstyle.specs.SpecNotFoundError
        If *journal* is not registered.
    """
    _validate_columns(columns)

    spec = registry.get(journal)
    width_mm = (
        spec.dimensions.double_column_mm if columns == 2 else spec.dimensions.single_column_mm
    )
    if width_mm is None:
        col = "double" if columns == 2 else "single"
        raise RuntimeError(
            f"{spec.metadata.name} does not publish {col}-column widths. "
            f"Specify the figure size manually with figsize= or consult "
            f"{spec.metadata.source_url} for the journal's size requirements."
        )
    return Dimension(width_mm, "mm").to_inches()


def _format_panel_label(index: int, spec: JournalSpec) -> str:
    """Format a single panel label string from a zero-based index and spec.

    The label style (case, parentheses, sentence capitalisation) is driven
    by :attr:`~plotstyle.specs.schema.TypographySpec.panel_label_case` on
    the journal spec.

    Parameters
    ----------
    index : int
        Zero-based panel index.  Index ``0`` maps to the letter
        ``"a"`` (or its styled equivalent), index ``1`` to ``"b"``,
        and so on.  Valid range is ``0`` to ``701`` inclusive.
    spec : JournalSpec
        Journal specification containing panel label formatting rules.

    Returns
    -------
    str
        Formatted panel label string (e.g. ``"a"``, ``"(B)"``, ``"A"``).

    Raises
    ------
    ValueError
        If *index* is >= 702 (beyond the two-character ``"zz"`` label).

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
    if index < 26:
        letter = chr(ord("a") + index)
    elif index < 702:
        i = index - 26
        letter = chr(ord("a") + i // 26) + chr(ord("a") + i % 26)
    else:
        raise ValueError(f"Panel index {index} exceeds the maximum supported label range (0-701).")
    case = spec.typography.panel_label_case

    match case:
        case "upper" | "title":
            return letter.upper()
        case "parens_lower":
            return f"({letter})"
        case "parens_upper":
            return f"({letter.upper()})"
        case "sentence":
            return letter.upper() if index == 0 else letter
        case _:
            # "lower" is the default; unknown values degrade gracefully.
            return letter


def _add_panel_labels(axes: np.ndarray, spec: JournalSpec) -> None:
    """Annotate every axes in *axes* with a spec-accurate panel label.

    Labels are placed just above and to the left of each axes bounding box,
    using the font size and weight from the journal spec.

    Parameters
    ----------
    axes : np.ndarray
        2-D ``ndarray`` of :class:`~matplotlib.axes.Axes` objects.
    spec : JournalSpec
        Journal specification defining label style, font size, and weight.
    """
    for idx, ax in enumerate(axes.flat):
        label = _format_panel_label(idx, spec)
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

    Parameters
    ----------
    width_in : float
        Figure width in inches.
    aspect : float | None
        Width-to-height ratio.  When ``None``, the golden ratio is
        used as the default.

    Returns
    -------
    tuple[float, float]
        A ``(width_in, height_in)`` tuple ready to be passed to
        ``plt.subplots(figsize=...)``.
    """
    ratio = aspect if aspect is not None else _GOLDEN_RATIO
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

    Parameters
    ----------
    journal : str
        Journal preset name (e.g. ``"nature"``).
    columns : int
        Column span: ``1`` (default) for single-column width,
        ``2`` for double-column (full-text) width.
    aspect : float | None
        Width-to-height ratio for the figure.  Defaults to the
        golden ratio (≈ 1.618) when ``None``.

    Returns
    -------
    tuple[Figure, Axes]
        A ``(fig, ax)`` tuple containing the new
        :class:`~matplotlib.figure.Figure` and its single
        :class:`~matplotlib.axes.Axes`.

    Raises
    ------
    ValueError
        If *columns* is not ``1`` or ``2``.
    plotstyle.specs.SpecNotFoundError
        If *journal* is not registered.

    Examples
    --------
    ::

        import plotstyle

        fig, ax = plotstyle.figure("nature")
        ax.plot([1, 2, 3], [4, 5, 6])
        plotstyle.savefig(fig, "figure.pdf", journal="nature")
    """
    width_in = _resolve_width(journal, columns)
    figsize = _compute_figsize(width_in, aspect)

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
    squeeze: bool = False,
) -> tuple[Figure, np.ndarray | Axes]:
    """Create a multi-panel figure sized to a journal's column width.

    Resolves the journal spec, sizes the figure to the requested column span,
    and optionally annotates each axes with a spec-accurate panel label
    (``a``, ``b``, ``c``, …).

    Parameters
    ----------
    journal : str
        Journal preset name (e.g. ``"nature"``).
    nrows : int
        Number of subplot rows.  Defaults to ``1``.
    ncols : int
        Number of subplot columns.  Defaults to ``1``.
    columns : int
        Column span: ``1`` (default) for single-column width,
        ``2`` for double-column (full-text) width.
    panels : bool
        When ``True`` (default), annotates each axes with a
        panel label styled according to the journal specification.
        Pass ``False`` to suppress labels entirely.
    aspect : float | None
        Width-to-height ratio for the whole figure.  Defaults to
        the golden ratio (≈ 1.618) when ``None``.
    squeeze : bool
        When ``False`` (default), *axes* is always a 2-D
        ``ndarray`` with shape ``(nrows, ncols)``.  When ``True``,
        dimensions of size 1 are removed, matching
        :func:`matplotlib.pyplot.subplots` behaviour: a single-panel
        figure returns a bare :class:`~matplotlib.axes.Axes`, a
        single-row or single-column grid returns a 1-D ``ndarray``,
        and larger grids return a 2-D ``ndarray``.

    Returns
    -------
    tuple[Figure, np.ndarray | Axes]
        A ``(fig, axes)`` tuple.  The shape of *axes* depends on *squeeze*
        (see above).

    Raises
    ------
    ValueError
        If *columns* is not ``1`` or ``2``.
    plotstyle.specs.SpecNotFoundError
        If *journal* is not registered.

    Notes
    -----
    **Default return shape**: by default this function always returns
    a 2-D ``ndarray``, including the ``nrows=1, ncols=1`` case.
    This lets callers use ``.flat`` iteration and ``axes[i, j]``
    indexing without special-casing single-panel figures.

    Pass ``squeeze=True`` for Matplotlib-compatible behaviour where
    size-1 dimensions are dropped.  This is useful when migrating
    existing code that writes ``for ax in axes`` over a single row.

    Examples
    --------
    Default (2-D ndarray, safe for any grid shape)::

        import plotstyle

        fig, axes = plotstyle.subplots("nature", nrows=2, ncols=2, columns=2)
        for ax in axes.flat:
            ax.plot([1, 2, 3])

    With ``squeeze=True``, Matplotlib-compatible iteration over a single row::

        fig, axes = plotstyle.subplots("nature", nrows=1, ncols=3, squeeze=True)
        for ax in axes:  # axes is 1-D here
            ax.plot([1, 2, 3])
    """
    spec = registry.get(journal)
    width_in = _resolve_width(journal, columns)
    figsize = _compute_figsize(width_in, aspect)

    # squeeze=False guarantees a 2-D ndarray for all (nrows, ncols) combinations.
    fig, axes_2d = plt.subplots(
        nrows,
        ncols,
        figsize=figsize,
        constrained_layout=True,
        squeeze=False,
    )

    if panels:
        _add_panel_labels(axes_2d, spec)

    if squeeze:
        if nrows == 1 and ncols == 1:
            return fig, axes_2d[0, 0]
        if nrows == 1:
            return fig, axes_2d[0]
        if ncols == 1:
            return fig, axes_2d[:, 0]

    return fig, axes_2d
