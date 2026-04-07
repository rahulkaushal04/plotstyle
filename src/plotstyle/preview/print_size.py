"""Print-size preview — display a figure at its approximate physical dimensions.

Provides :func:`preview_print_size`, which temporarily scales a figure's DPI
so that its on-screen rendering matches the physical column width it would
occupy in print.

Design notes
------------
**DPI scaling approach** — rather than resizing the figure canvas (which would
mutate the caller's figure permanently), this module adjusts the renderer DPI
for the duration of the preview window.  A higher DPI causes Matplotlib to
draw more pixels for the same canvas size, which on a monitor with known pixel
density produces an image at the correct physical scale.

The scaling relationship is::

    display_dpi = monitor_dpi x (target_width_in / current_width_in)

**Restoration guarantee** — a ``finally`` block in :func:`preview_print_size`
unconditionally removes the transient annotation and restores the figure's
original DPI after ``plt.show`` returns (or raises).  The caller's figure is
always left in the same state it was in before the call.

**Monitor DPI accuracy** — physical fidelity depends on *monitor_dpi*
matching the display's true pixel density.  The default of ``96.0`` is the
conventional value for Windows and many Linux desktops.  macOS Retina displays
typically require ``144`` (1x logical) or ``192`` (2x native Retina).  Use
``screeninfo`` or a similar library to query the true value programmatically.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__: list[str] = ["preview_print_size"]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Conventional monitor DPI for Windows and most Linux desktops.
# Used as the default when the caller does not specify monitor_dpi.
_DEFAULT_MONITOR_DPI: Final[float] = 96.0

# Unicode directional arrows that frame the physical-width annotation.
_LEFT_ARROW: Final[str] = "\u2190"  # ←
_RIGHT_ARROW: Final[str] = "\u2192"  # →

# Visual properties of the transient annotation added during preview.
# Centralised here so they can be adjusted without hunting through the
# function body.
_ANNOTATION_FONTSIZE: Final[int] = 7
_ANNOTATION_COLOR: Final[str] = "gray"
_ANNOTATION_ALPHA: Final[float] = 0.6
_ANNOTATION_Y: Final[float] = 0.01  # figure-normalised y coordinate

# Millimetres per inch — used to convert width_in → width_mm for the label
# when no journal spec is available.
_MM_PER_INCH: Final[float] = 25.4

# Valid column-span values; mirrored from plotstyle.core.figure for local
# validation without creating a cross-module import dependency.
_VALID_COLUMNS: Final[frozenset[int]] = frozenset({1, 2})

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_target_width(
    journal: str | None,
    columns: int,
    current_width_in: float,
) -> tuple[float, float]:
    """Resolve the target print width in inches and millimetres.

    When *journal* is provided, the width is read from the registered spec
    for the requested *columns* span.  When *journal* is ``None``, the
    figure's current width is used as the target (a 1:1 preview).

    Args:
        journal: Journal preset name, or ``None`` for a 1:1 preview.
        columns: Column span (``1`` or ``2``).  Only used when *journal*
            is not ``None``.
        current_width_in: The figure's current width in inches.  Used as
            the fallback target when *journal* is ``None``.

    Returns
    -------
        A ``(width_in, width_mm)`` tuple where *width_in* is the target
        physical width in inches and *width_mm* is the same value in
        millimetres (used for the annotation label).

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If *journal* is given but not
            registered in the spec registry.
    """
    if journal is not None:
        # Deferred imports keep these optional dependencies out of the module's
        # import-time footprint when the caller only needs the 1:1 path.
        from plotstyle.specs import registry
        from plotstyle.specs.units import Dimension

        spec = registry.get(journal)
        width_mm: float = (
            spec.dimensions.double_column_mm if columns == 2 else spec.dimensions.single_column_mm
        )
        width_in: float = Dimension(width_mm, "mm").to_inches()
    else:
        # 1:1 preview: the figure is already at the intended physical width.
        width_in = current_width_in
        width_mm = current_width_in * _MM_PER_INCH

    return width_in, width_mm


def _build_annotation_label(width_mm: float) -> str:
    """Build the physical-width annotation string.

    Formats the target width in millimetres, framed by Unicode arrows, so the
    viewer can confirm the figure is rendering at the correct print scale.

    Args:
        width_mm: Target physical width in millimetres.

    Returns
    -------
        Annotation string of the form ``"← 88 mm →"``.
    """
    return f"{_LEFT_ARROW} {width_mm:.0f} mm {_RIGHT_ARROW}"


def _validate_args(columns: int, monitor_dpi: float) -> None:
    """Raise :exc:`ValueError` for invalid *columns* or *monitor_dpi* values.

    Centralising argument validation here keeps :func:`preview_print_size`
    focused on its primary logic and ensures the error messages are consistent
    regardless of which argument triggers the check.

    Args:
        columns: Column-span value to validate.
        monitor_dpi: Monitor pixel density to validate.

    Raises
    ------
        ValueError: If *columns* is not in ``{1, 2}``.
        ValueError: If *monitor_dpi* is not a strictly positive number.
    """
    if columns not in _VALID_COLUMNS:
        raise ValueError(
            f"'columns' must be 1 (single-column) or 2 (double-column), got {columns!r}."
        )
    if monitor_dpi <= 0:
        raise ValueError(
            f"'monitor_dpi' must be a positive number, got {monitor_dpi!r}. "
            "Common values: 96 (Windows/Linux), 144 (macOS 1x), 192 (macOS 2x)."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def preview_print_size(
    fig: Figure,
    *,
    journal: str | None = None,
    columns: int = 1,
    monitor_dpi: float = _DEFAULT_MONITOR_DPI,
) -> None:
    """Display *fig* at its approximate actual physical print size.

    Temporarily adjusts the figure's DPI so that the on-screen rendering
    corresponds to the target physical column width at the monitor's pixel
    density.  After :func:`matplotlib.pyplot.show` returns, the transient
    annotation and the original DPI are restored — the caller's figure is
    left unchanged.

    When *journal* is provided, the target width is looked up from the
    journal spec for the requested *columns* span.  When *journal* is
    ``None``, the figure's current declared width is used as the target,
    effectively showing the figure at a 1:1 physical scale.

    Args:
        fig: Matplotlib figure to preview.  Not mutated after the call.
        journal: Optional journal preset name (e.g. ``"nature"``).  When
            provided, the figure is scaled to match the journal's column
            width in physical millimetres.
        columns: Column span for the journal width lookup: ``1`` (default)
            for single-column width, ``2`` for double-column width.
            Ignored when *journal* is ``None``.
        monitor_dpi: Physical pixel density of the display in
            dots-per-inch.  Defaults to ``96.0`` (Windows/Linux standard).
            Pass ``144`` for 1x macOS Retina or ``192`` for 2x Retina.

    Returns
    -------
        ``None``.  Side effect: :func:`matplotlib.pyplot.show` is called,
        which blocks until the display window is closed in interactive
        environments.

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If *journal* is given but not
            registered in the spec registry.
        ValueError: If *columns* is not ``1`` or ``2``.
        ValueError: If *monitor_dpi* is not a strictly positive number.
        ValueError: If the figure's current width is zero (degenerate state
            that makes DPI scaling undefined).

    Notes
    -----
        **DPI scaling** — the display DPI is computed as::

            display_dpi = monitor_dpi x (target_width_in / current_width_in)

        This scales the renderer so that the number of on-screen pixels
        matches what the monitor needs to render the figure at its true
        physical size.

        **Restoration** — a ``finally`` block guarantees that the annotation
        is removed and the original DPI is restored even if ``plt.show``
        raises an exception.

        **Import deferral** — ``matplotlib.pyplot`` is imported inside the
        function to avoid triggering the Matplotlib backend initialisation at
        module import time, which can cause issues in headless environments.

    Example::

        import matplotlib.pyplot as plt
        import plotstyle

        with plotstyle.use("nature"):
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])

        # Preview at Nature single-column width on a standard 96 DPI monitor:
        plotstyle.preview_print_size(fig, journal="nature")

        # Preview double-column on a 144 DPI macOS Retina display:
        plotstyle.preview_print_size(fig, journal="nature", columns=2, monitor_dpi=144)

        # 1:1 preview using the figure's declared width (no journal lookup):
        plotstyle.preview_print_size(fig, monitor_dpi=96)
    """
    # Deferred import: importing pyplot triggers backend initialisation, which
    # can emit warnings or fail entirely in headless CI environments.  Deferring
    # the import to call time means the module is safe to import anywhere.
    import matplotlib.pyplot as plt

    # Validate arguments before touching the figure so any error is raised with
    # the figure in an unmodified state.
    _validate_args(columns, monitor_dpi)

    current_width_in: float = fig.get_size_inches()[0]

    if current_width_in == 0:
        raise ValueError(
            "Figure has zero width; cannot compute a print-size scale factor. "
            "Ensure the figure has been created with a non-zero figsize."
        )

    # ── Resolve target physical dimensions ───────────────────────────────────
    target_width_in, width_mm = _resolve_target_width(journal, columns, current_width_in)

    # ── Compute and apply preview DPI ────────────────────────────────────────
    # Scaling DPI rather than the canvas size leaves the figure's declared
    # width unchanged, so the caller's object is not mutated.
    scale_factor: float = target_width_in / current_width_in
    display_dpi: float = monitor_dpi * scale_factor

    original_dpi: float = fig.dpi
    fig.set_dpi(display_dpi)

    # ── Transient annotation ─────────────────────────────────────────────────
    # Add a low-prominence label so the viewer can verify the physical scale
    # at a glance.  fontsize and alpha are kept small to avoid distracting from
    # the figure content.
    annotation_label: str = _build_annotation_label(width_mm)
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
        # Unconditionally remove the annotation and restore the original DPI
        # so the caller's figure is in exactly the same state as before the
        # preview call — even if plt.show() raised an exception.
        text_artist.remove()
        fig.set_dpi(original_dpi)
