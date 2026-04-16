"""Assemble a ``matplotlib.rcParams`` dict from a :class:`~plotstyle.specs.schema.JournalSpec`.

:func:`build_rcparams` is the single public entry point.  :data:`SAFETY_PARAMS`
always sets ``fonttype=42`` (TrueType embedding) regardless of caller overrides.
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

#: rcParam keys that enforce TrueType font embedding; must not be downgraded.
SAFETY_PARAMS: Final[frozenset[str]] = frozenset(
    {
        "pdf.fonttype",
        "ps.fonttype",
    }
)

_GOLDEN_RATIO: Final[float] = (1.0 + 5.0**0.5) / 2.0
_DISPLAY_DPI: Final[int] = 100
_FONTTYPE_TRUETYPE: Final[int] = 42

_LatexMode = Literal[True, False, "auto"]

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class LatexNotFoundError(RuntimeError):
    """Raised when LaTeX rendering is explicitly requested but unavailable."""

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
    """Determine whether to enable LaTeX given the requested mode.

    Parameters
    ----------
    latex : _LatexMode
        LaTeX mode from :func:`build_rcparams`: ``True`` forces LaTeX
        (raises if unavailable), ``False`` disables it unconditionally,
        and ``"auto"`` enables it only if a binary is found.

    Returns
    -------
    bool
        ``True`` if LaTeX should be enabled, ``False`` otherwise.

    Raises
    ------
    LatexNotFoundError
        When ``latex=True`` and no ``latex`` binary is on ``PATH``.
    """
    if latex is False:
        return False

    latex_available = detect_latex()

    if latex is True and not latex_available:
        raise LatexNotFoundError()

    return latex_available


def _compute_figure_size(spec: JournalSpec) -> tuple[float, float]:
    """Return ``(width_in, height_in)`` for the spec's single-column width."""
    width_in = Dimension(spec.dimensions.single_column_mm, "mm").to_inches()
    height_in = width_in / _GOLDEN_RATIO
    return width_in, height_in


def _compute_base_font_size(spec: JournalSpec) -> float:
    """Return the midpoint of the spec's permitted font-size range."""
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

    Parameters
    ----------
    spec : JournalSpec
        Journal specification to translate into rcParams.
    latex : _LatexMode
        Controls LaTeX-based text rendering:

        - ``False`` *(default)* — use Matplotlib's MathText engine.
        - ``True`` — require LaTeX; raises :class:`LatexNotFoundError` if
          no ``latex`` binary is found on ``PATH``.
        - ``"auto"`` — enable LaTeX when available, fall back to MathText.

    Returns
    -------
    dict[str, Any]
        Ready for ``matplotlib.rcParams.update``.  Always includes
        :data:`SAFETY_PARAMS` set to ``42`` (TrueType embedding).

    Raises
    ------
    ValueError
        If *latex* is not ``True``, ``False``, or ``"auto"``.
    LatexNotFoundError
        If ``latex=True`` but no ``latex`` binary is found on ``PATH``.
    """
    if latex not in (True, False, "auto"):
        raise ValueError(f"Invalid latex value {latex!r}. Expected True, False, or 'auto'.")

    font_name, _font_meta = select_best(spec)
    width_in, height_in = _compute_figure_size(spec)
    font_size = _compute_base_font_size(spec)

    params = {
        "pdf.fonttype": _FONTTYPE_TRUETYPE,
        "ps.fonttype": _FONTTYPE_TRUETYPE,
        "figure.dpi": _DISPLAY_DPI,
        "savefig.dpi": spec.export.min_dpi,
        "figure.figsize": [width_in, height_in],
        "figure.constrained_layout.use": True,
        "font.family": font_name,
        "font.size": font_size,
        "axes.titlesize": font_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size,
        "ytick.labelsize": font_size,
        "legend.fontsize": font_size,
        # Clamped to physically reproducible minimums; thinner lines vanish in print.
        "lines.linewidth": max(spec.line.min_weight_pt, 1.0),
        "axes.linewidth": max(spec.line.min_weight_pt, 0.5),
        # "none" keeps text editable in SVG; "path" converts to outlines (more portable).
        "svg.fonttype": "none" if spec.export.editable_text else "path",
        "axes.grid": False,
    }

    use_latex = _resolve_latex_mode(latex)

    if use_latex:
        params.update(configure_latex(spec))
    else:
        params["text.usetex"] = False

    return params
