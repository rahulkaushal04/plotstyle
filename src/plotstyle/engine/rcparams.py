"""Assemble a ``matplotlib.rcParams`` dict from a :class:`~plotstyle.specs.schema.JournalSpec`.

This module is the orchestration layer of the PlotStyle rendering engine.
:func:`build_rcparams` is the single public entry point: it delegates font
selection to :mod:`~plotstyle.engine.fonts`, optional LaTeX configuration to
:mod:`~plotstyle.engine.latex`, and combines the results with dimension and
typography values derived from a :class:`~plotstyle.specs.schema.JournalSpec`
into a flat ``dict`` ready for ``matplotlib.rcParams.update``.

Design notes
------------
- **Safety params** (:data:`SAFETY_PARAMS`) are always written and can never
  be downgraded by callers.  They force TrueType font embedding (``fonttype=42``)
  in both PDF and PostScript output, which is a hard requirement for virtually
  all modern journal submission portals.
- **LaTeX rendering** is opt-in and supports three modes — ``True``, ``False``,
  and ``"auto"`` — to accommodate environments where a ``latex`` binary may or
  may not be present.
- Figure height defaults to ``width / φ`` (the golden ratio) when not
  explicitly specified, producing a visually balanced layout without imposing a
  fixed aspect ratio on callers.

Constants
---------
SAFETY_PARAMS : frozenset[str]
    rcParam keys whose values must never be overridden; they guarantee TrueType
    font embedding in PDF and PS output.

_GOLDEN_RATIO : float
    Default figure aspect ratio (width ÷ height), approximately ``1.618``.

_DISPLAY_DPI : int
    Screen DPI for interactive rendering; kept intentionally lower than
    ``savefig.dpi`` to prioritise responsiveness over pixel density.

_FONTTYPE_TRUETYPE : int
    The ``fonttype`` value that instructs matplotlib to embed fonts as TrueType
    (Type 42) in PDF/PS output.  This is the only value accepted by most
    submission portals.

Public API
----------
- :data:`SAFETY_PARAMS`
- :func:`build_rcparams`

Raises
------
:class:`LatexNotFoundError`
    Raised by :func:`build_rcparams` when ``latex=True`` but no ``latex``
    binary is discoverable on ``PATH``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Literal

from plotstyle.engine.fonts import select_best
from plotstyle.engine.latex import configure_latex, detect_latex
from plotstyle.specs.units import Dimension

if TYPE_CHECKING:
    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "SAFETY_PARAMS",
    "LatexNotFoundError",
    "build_rcparams",
]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: rcParam keys that enforce TrueType font embedding (``fonttype=42``).
#: Written unconditionally by :func:`build_rcparams`; must not be downgraded.
#: Type 3 and Type 1 substitutes are rejected by most submission portals.
SAFETY_PARAMS: Final[frozenset[str]] = frozenset(
    {
        "pdf.fonttype",
        "ps.fonttype",
    }
)

# φ ≈ 1.618 — used as the default width-to-height aspect ratio because it is
# visually balanced and avoids the need to specify height explicitly for the
# majority of single-column figures.
_GOLDEN_RATIO: Final[float] = (1.0 + 5.0**0.5) / 2.0

# Screen DPI for the interactive renderer.  A value of 100 balances sharpness
# and responsiveness; export DPI is set independently from the journal spec.
_DISPLAY_DPI: Final[int] = 100

# PDF/PS fonttype value that signals TrueType (Type 42) embedding.  Named for
# clarity — bare integer literals at call sites are easy to misread.
_FONTTYPE_TRUETYPE: Final[int] = 42

# Type alias used to constrain the public ``latex`` parameter to its three
# valid sentinel values, enabling static analysis to catch invalid arguments.
_LatexMode = Literal[True, False, "auto"]

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class LatexNotFoundError(RuntimeError):
    """Raised when LaTeX rendering is explicitly requested but unavailable.

    This exception is a :class:`RuntimeError` subclass so that callers who
    already catch ``RuntimeError`` remain unaffected; callers that need finer
    control can catch :class:`LatexNotFoundError` directly.

    Args:
        message: Human-readable description of why LaTeX could not be found.
            Defaults to a generic installation hint when omitted.

    Example::

        try:
            params = build_rcparams(spec, latex=True)
        except LatexNotFoundError as exc:
            logger.warning("Falling back to MathText: %s", exc)
            params = build_rcparams(spec, latex=False)
    """

    _DEFAULT_MESSAGE: Final[str] = (
        "No 'latex' binary was found on PATH. "
        "Install TeX Live or MiKTeX, or pass latex='auto' to fall back silently."
    )

    def __init__(self, message: str = _DEFAULT_MESSAGE) -> None:
        super().__init__(message)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_latex_mode(latex: _LatexMode) -> bool:
    """Determine whether to enable LaTeX rendering given the requested mode.

    Centralises the three-way ``latex`` resolution logic so that
    :func:`build_rcparams` stays readable.  The validation of *latex* is
    intentionally performed by the caller before this function is invoked so
    that the error is attributed to the public API surface, not the helper.

    Args:
        latex: One of ``True``, ``False``, or ``"auto"``.

            - ``True``  — demand LaTeX; raise :class:`LatexNotFoundError` if
              no binary is found.
            - ``False`` — unconditionally disable LaTeX.
            - ``"auto"`` — enable LaTeX only when the binary is available;
              otherwise degrade silently to MathText.

    Returns
    -------
        ``True`` if LaTeX rendering should be enabled, ``False`` otherwise.

    Raises
    ------
        LatexNotFoundError: When ``latex=True`` and no ``latex`` binary exists
            on ``PATH``.
    """
    if latex is False:
        return False

    latex_available: bool = detect_latex()

    if latex is True and not latex_available:
        raise LatexNotFoundError()

    # latex == "auto": use LaTeX if present, MathText otherwise.
    return latex_available


def _compute_figure_size(spec: JournalSpec) -> tuple[float, float]:
    """Derive figure width and height in inches from a journal spec.

    Width is taken directly from
    :attr:`~plotstyle.specs.schema.DimensionSpec.single_column_mm` and
    converted to inches.  Height defaults to ``width / φ`` (the golden ratio),
    giving a balanced landscape orientation that works for the majority of
    scientific figures without requiring callers to specify both dimensions.

    Args:
        spec: Journal specification containing dimension information.

    Returns
    -------
        A ``(width_in, height_in)`` tuple, both values in inches.
    """
    width_in: float = Dimension(spec.dimensions.single_column_mm, "mm").to_inches()
    height_in: float = width_in / _GOLDEN_RATIO
    return width_in, height_in


def _compute_base_font_size(spec: JournalSpec) -> float:
    """Compute a safe default font size from the journal's permitted range.

    The midpoint of ``[min_font_pt, max_font_pt]`` is used because it sits
    within the valid band and avoids edge values that might trip automated
    validation checks at submission time.

    Args:
        spec: Journal specification containing typography constraints.

    Returns
    -------
        Font size in points (``float``).
    """
    return (spec.typography.min_font_pt + spec.typography.max_font_pt) / 2.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_rcparams(
    spec: JournalSpec,
    *,
    latex: _LatexMode = False,
) -> dict[str, Any]:
    """Build a complete ``matplotlib.rcParams`` mapping from a journal spec.

    Derives figure dimensions, typography, line styling, and export settings
    from *spec*.  Font selection is delegated to
    :mod:`~plotstyle.engine.fonts`; LaTeX configuration (when requested) is
    delegated to :mod:`~plotstyle.engine.latex`.

    Args:
        spec: Journal specification to translate into rcParams.
        latex: Controls LaTeX-based text rendering.  Must be one of:

            - ``False`` *(default)* — disable LaTeX; use matplotlib's built-in
              MathText engine instead.
            - ``True`` — require LaTeX; raises :class:`LatexNotFoundError` if
              no ``latex`` binary is found on ``PATH``.
            - ``"auto"`` — enable LaTeX when a ``latex`` binary is available
              on ``PATH``; silently fall back to MathText otherwise.

    Returns
    -------
        A ``dict[str, Any]`` suitable for ``matplotlib.rcParams.update``.
        The dict always contains the :data:`SAFETY_PARAMS` keys set to
        :data:`_FONTTYPE_TRUETYPE` (``42``) to guarantee TrueType font
        embedding regardless of caller-supplied overrides.

    Raises
    ------
        ValueError: If *latex* is not one of ``True``, ``False``, or
            ``"auto"``.  The message names the offending value and lists the
            accepted alternatives.
        LatexNotFoundError: If ``latex=True`` but no ``latex`` binary is
            discoverable on ``PATH``.

    Notes
    -----
        **Figure size** — width is taken from
        :attr:`~plotstyle.specs.schema.DimensionSpec.single_column_mm` and
        converted to inches; height defaults to ``width / φ`` (golden ratio).
        Override via ``matplotlib.rcParams["figure.figsize"]`` after calling
        this function if a non-default aspect ratio is needed.

        **Font size** — the midpoint of the journal's allowed font-size range
        is applied uniformly to axes titles, axis labels, tick labels, and
        legends.  Override individual keys after calling this function for
        fine-grained control.

        **Safety params** — ``pdf.fonttype=42`` and ``ps.fonttype=42`` are
        always present in the returned dict and should not be overridden;
        see :data:`SAFETY_PARAMS`.

        **Line weights** — ``lines.linewidth`` and ``axes.linewidth`` are
        clamped to physically reproducible minimums (``1.0 pt`` and ``0.5 pt``
        respectively); values below these thresholds routinely disappear in
        print.

    Example::

        from plotstyle.specs import registry
        from plotstyle.engine.rcparams import build_rcparams
        import matplotlib as mpl

        spec = registry.get("nature")
        params = build_rcparams(spec, latex="auto")
        mpl.rcParams.update(params)
    """
    # Validate *latex* up-front so the error message clearly identifies the
    # public parameter rather than surfacing inside an internal helper.
    if latex not in (True, False, "auto"):
        raise ValueError(f"Invalid latex value {latex!r}. Expected True, False, or 'auto'.")

    font_name, _font_meta = select_best(spec)
    width_in, height_in = _compute_figure_size(spec)
    font_size: float = _compute_base_font_size(spec)

    params: dict[str, Any] = {
        # ── Safety (non-negotiable) ──────────────────────────────────────────
        # fonttype=42 embeds fonts as TrueType in PDF/PS, required by virtually
        # all modern journal submission systems.  These keys must not be
        # removed or lowered — see SAFETY_PARAMS.
        "pdf.fonttype": _FONTTYPE_TRUETYPE,
        "ps.fonttype": _FONTTYPE_TRUETYPE,
        # ── DPI split ────────────────────────────────────────────────────────
        # Display DPI is kept low for interactive responsiveness; save DPI is
        # set to the journal's minimum to ensure print-quality export.
        "figure.dpi": _DISPLAY_DPI,
        "savefig.dpi": spec.export.min_dpi,
        # ── Figure dimensions ────────────────────────────────────────────────
        "figure.figsize": [width_in, height_in],
        # constrained_layout prevents axes labels from being clipped and is
        # safer than tight_layout for automated, non-interactive pipelines.
        "figure.constrained_layout.use": True,
        # ── Typography ───────────────────────────────────────────────────────
        "font.family": font_name,
        "font.size": font_size,
        "axes.titlesize": font_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size,
        "ytick.labelsize": font_size,
        "legend.fontsize": font_size,
        # ── Line weights ─────────────────────────────────────────────────────
        # Clamped to physically reproducible minimums; thinner lines routinely
        # vanish when the figure is rasterised for print.
        "lines.linewidth": max(spec.line.min_weight_pt, 1.0),
        "axes.linewidth": max(spec.line.min_weight_pt, 0.5),
        # ── SVG text handling ────────────────────────────────────────────────
        # "none" keeps text as editable SVG elements (preferable for figures
        # that will be touched up in Inkscape or Illustrator); "path" converts
        # text to vector outlines, which is more portable but loses editability.
        "svg.fonttype": "none" if spec.export.editable_text else "path",
        # ── Axes appearance ──────────────────────────────────────────────────
        # Grid lines are disabled by default; journals typically require clean,
        # uncluttered axes.  Callers can re-enable selectively after applying.
        "axes.grid": False,
    }

    use_latex: bool = _resolve_latex_mode(latex)

    if use_latex:
        # configure_latex may extend or override font.family and will inject
        # text.usetex=True together with an appropriate text.latex.preamble.
        params.update(configure_latex(spec))
    else:
        # Explicitly disable LaTeX so that a stale text.usetex=True from a
        # previous rcParams.update call does not silently persist.
        params["text.usetex"] = False

    return params
