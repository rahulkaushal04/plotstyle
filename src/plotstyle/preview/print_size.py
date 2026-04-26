"""Print-size preview: display a figure at its approximate physical print dimensions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__: list[str] = ["preview_print_size"]

_DEFAULT_MONITOR_DPI: Final[float] = 96.0
_LEFT_ARROW: Final[str] = "\u2190"  # ←
_RIGHT_ARROW: Final[str] = "\u2192"  # →
_ANNOTATION_FONTSIZE: Final[int] = 7
_ANNOTATION_COLOR: Final[str] = "gray"
_ANNOTATION_ALPHA: Final[float] = 0.6
_ANNOTATION_Y: Final[float] = 0.01
_MM_PER_INCH: Final[float] = 25.4
_VALID_COLUMNS: Final[frozenset[int]] = frozenset({1, 2})


def _resolve_target_width(
    journal: str | None,
    columns: int,
    current_width_in: float,
) -> tuple[float, float]:
    """Return ``(width_in, width_mm)`` for the target print width.

    Uses the journal spec when provided; falls back to *current_width_in* for a 1:1 preview.
    """
    if journal is not None:
        from plotstyle.specs import registry
        from plotstyle.specs.units import Dimension

        spec = registry.get(journal)
        width_mm = (
            spec.dimensions.double_column_mm if columns == 2 else spec.dimensions.single_column_mm
        )
        width_in = Dimension(width_mm, "mm").to_inches()
    else:
        width_in = current_width_in
        width_mm = current_width_in * _MM_PER_INCH

    return width_in, width_mm


def _build_annotation_label(width_mm: float) -> str:
    """Return an annotation string of the form ``"← 88 mm →"``."""
    return f"{_LEFT_ARROW} {width_mm:.0f} mm {_RIGHT_ARROW}"


def _validate_args(columns: int, monitor_dpi: float) -> None:
    """Raise :exc:`ValueError` if *columns* or *monitor_dpi* are invalid."""
    if columns not in _VALID_COLUMNS:
        raise ValueError(
            f"'columns' must be 1 (single-column) or 2 (double-column), got {columns!r}."
        )
    if monitor_dpi <= 0:
        raise ValueError(
            f"'monitor_dpi' must be a positive number, got {monitor_dpi!r}. "
            "Common values: 96 (Windows/Linux), 144 (macOS 1x), 192 (macOS 2x)."
        )


def preview_print_size(
    fig: Figure,
    *,
    journal: str | None = None,
    columns: int = 1,
    monitor_dpi: float = _DEFAULT_MONITOR_DPI,
) -> None:
    """Display *fig* at its approximate physical print size, then restore it.

    Scales the figure's DPI so on-screen pixels match the physical column width,
    adds a transient ``"← W mm →"`` annotation, and calls ``plt.show()``.
    The annotation and original DPI are restored unconditionally on return.

    Parameters
    ----------
    fig : Figure
        Figure to preview.  Not mutated after the call.
    journal : str | None
        Optional journal preset; determines target column width.
        ``None`` uses the figure's current width (1:1 preview).
    columns : int
        Column span: ``1`` (default) or ``2``.
    monitor_dpi : float
        Display pixel density.  Defaults to ``96.0`` (Windows/Linux).

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If *journal* is not registered.
    ValueError
        If *columns* is not ``1`` or ``2``, *monitor_dpi* ≤ 0,
        or the figure has zero width.
    """
    import matplotlib.pyplot as plt

    _validate_args(columns, monitor_dpi)

    current_width_in = fig.get_size_inches()[0]

    if current_width_in == 0:
        raise ValueError(
            "Figure has zero width; cannot compute a print-size scale factor. "
            "Ensure the figure has been created with a non-zero figsize."
        )

    target_width_in, width_mm = _resolve_target_width(journal, columns, current_width_in)

    scale_factor = target_width_in / current_width_in
    display_dpi = monitor_dpi * scale_factor

    original_dpi = fig.dpi
    fig.set_dpi(display_dpi)

    annotation_label = _build_annotation_label(width_mm)
    text_artist = fig.text(
        0.5,
        _ANNOTATION_Y,
        annotation_label,
        ha="center",
        va="bottom",
        fontsize=_ANNOTATION_FONTSIZE,
        color=_ANNOTATION_COLOR,
        alpha=_ANNOTATION_ALPHA,
    )

    try:
        plt.show()
    finally:
        text_artist.remove()
        fig.set_dpi(original_dpi)
