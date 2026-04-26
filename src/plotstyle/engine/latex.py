"""LaTeX binary detection and rcParams configuration.

``detect_latex``
    Return ``True`` when a ``latex`` executable is present on ``PATH``.

``detect_distribution``
    Return a string identifying the installed TeX distribution, or
    ``None`` when no LaTeX installation is found.

``configure_latex``
    Build the Matplotlib ``rcParams`` fragment required to enable
    LaTeX-based text rendering for a given
    :class:`~plotstyle.specs.schema.JournalSpec`.

All functions are read-only or pure; no side effects.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "LatexConfigurationError",
    "configure_latex",
    "detect_distribution",
    "detect_latex",
]

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class LatexConfigurationError(ValueError):
    """Raised when a JournalSpec cannot be translated into a valid LaTeX rcParams fragment."""


_PREAMBLE_SERIF: Final[str] = r"\usepackage{times}"
_PREAMBLE_SANS_SERIF: Final[str] = r"\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}"
_PREAMBLE_MONO: Final[str] = r"\usepackage{courier}\renewcommand{\familydefault}{\ttdefault}"

# Maps generic font families to PSNFSS preamble strings.
# Absent keys fall through to the LaTeX document-class default (Computer Modern).
_FALLBACK_TO_PREAMBLE: Final[dict[str, str]] = {
    "serif": _PREAMBLE_SERIF,
    "sans-serif": _PREAMBLE_SANS_SERIF,
    "monospace": _PREAMBLE_MONO,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _binary_exists(name: str) -> bool:
    """Return ``True`` when *name* resolves to an executable on ``PATH``."""
    return shutil.which(name) is not None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_latex() -> bool:
    """Return ``True`` if a ``latex`` executable is found on ``PATH``.

    Returns
    -------
    bool
        ``True`` if ``latex`` is found on ``PATH``; ``False`` otherwise.
    """
    return _binary_exists("latex")


def detect_distribution() -> str | None:
    """Detect the installed TeX distribution by probing known manager binaries.

    Probing order: ``tlmgr`` (TeX Live), ``miktex`` / ``mpm`` (MiKTeX),
    then ``latex`` alone (assumed TeX Live).

    Returns
    -------
    str | None
        ``"texlive"``, ``"miktex"``, or ``None`` when no LaTeX is found.

    Notes
    -----
    The ``"texlive"`` fallback when only ``latex`` is present is an
    assumption; it reflects the prevalence of TeX Live in CI environments.
    """
    if _binary_exists("tlmgr"):
        return "texlive"

    # MiKTeX ships two possible manager binaries depending on version.
    if _binary_exists("miktex") or _binary_exists("mpm"):
        return "miktex"

    if detect_latex():
        # latex binary present but no recognised manager; assume TeX Live.
        return "texlive"

    return None


def configure_latex(spec: JournalSpec) -> dict[str, Any]:
    """Build the ``rcParams`` fragment required for LaTeX-based text rendering.

    Parameters
    ----------
    spec : JournalSpec
        Journal specification whose ``typography.font_fallback`` drives
        font selection.

    Returns
    -------
    dict[str, Any]
        Ready to pass to ``mpl.rcParams.update()``.  Always includes
        ``"text.usetex": True`` and ``"font.family"``.  Also includes
        ``"text.latex.preamble"`` for the three generic CSS families
        (``"serif"``, ``"sans-serif"``, ``"monospace"``); other values
        leave preamble unset, defaulting to Computer Modern.

    Raises
    ------
    LatexConfigurationError
        If *spec* is missing ``typography.font_fallback`` or it is empty.
    """
    try:
        fallback = spec.typography.font_fallback
    except AttributeError as exc:
        raise LatexConfigurationError(
            f"JournalSpec is missing required 'typography.font_fallback' attribute: {exc}"
        ) from exc

    if not fallback:
        raise LatexConfigurationError(
            f"'typography.font_fallback' must be a non-empty string; got {fallback!r}."
        )

    params = {
        "text.usetex": True,
        "font.family": fallback,
    }

    preamble = _FALLBACK_TO_PREAMBLE.get(fallback)
    if preamble is not None:
        params["text.latex.preamble"] = preamble

    return params
