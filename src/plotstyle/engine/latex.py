"""LaTeX binary detection and rcParams configuration.

This module handles everything LaTeX-related in the PlotStyle rendering
pipeline.  It is intentionally side-effect-free: every public function
either queries the environment (read-only) or builds a plain ``dict``
that the caller is responsible for applying.

Public API
----------
detect_latex
    Return ``True`` when a ``latex`` executable is present on ``PATH``.

detect_distribution
    Return a string identifying the installed TeX distribution, or
    ``None`` when no LaTeX installation is found.

configure_latex
    Build the Matplotlib ``rcParams`` fragment required to enable
    LaTeX-based text rendering for a given :class:`~plotstyle.specs.schema.JournalSpec`.

Design notes
------------
* All binary detection delegates to :func:`shutil.which`, which honours
  the ``PATH`` variable at call time.  Results may therefore differ
  between interactive shells and headless CI environments.
* The ``detect_distribution`` heuristic is a *best-effort* probe, not a
  definitive identification.  Callers should treat the result as a hint.
* ``configure_latex`` is a pure function: same input always produces the
  same output, making it straightforward to test and cache.

Raises
------
:class:`LatexConfigurationError`
    Raised by :func:`configure_latex` when the supplied
    :class:`~plotstyle.specs.schema.JournalSpec` is missing required
    typography attributes.
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
    """Raised when a JournalSpec cannot be translated into a valid LaTeX rcParams fragment.

    Inherits from :class:`ValueError` so callers that already catch broad
    configuration errors do not need to import this class explicitly.

    Example
    -------
    ::

        try:
            params = configure_latex(spec)
        except LatexConfigurationError as exc:
            logger.error("Bad spec: %s", exc)
    """


# ---------------------------------------------------------------------------
# Internal constants — LaTeX preamble fragments
# ---------------------------------------------------------------------------

# Each constant encodes the minimal LaTeX preamble needed to activate a
# standard PSNFSS font package.  They are intentionally kept as narrow,
# single-responsibility snippets so they can be composed later if needed.

_PREAMBLE_SERIF: Final[str] = r"\usepackage{times}"
"""Activates the *Times Roman* clone via the ``times`` PSNFSS package."""

_PREAMBLE_SANS_SERIF: Final[str] = r"\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}"
"""Activates the *Helvetica* clone and promotes it to the document default."""

_PREAMBLE_MONO: Final[str] = r"\usepackage{courier}\renewcommand{\familydefault}{\ttdefault}"
"""Activates *Courier* and promotes it to the document default."""

# Maps the three CSS-style generic font families recognised by Matplotlib to
# their corresponding PSNFSS preamble strings.  Any font_fallback value
# absent from this mapping falls through silently: LaTeX will use the
# document-class default, which is usually Computer Modern.
_FALLBACK_TO_PREAMBLE: Final[dict[str, str]] = {
    "serif": _PREAMBLE_SERIF,
    "sans-serif": _PREAMBLE_SANS_SERIF,
    "monospace": _PREAMBLE_MONO,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _binary_exists(name: str) -> bool:
    """Return ``True`` when *name* resolves to an executable on ``PATH``.

    Args:
        name: The bare executable name to probe (e.g. ``"latex"``).

    Returns
    -------
        ``True`` if :func:`shutil.which` finds *name*, ``False`` otherwise.

    Notes
    -----
    This thin wrapper exists so the rest of the module reads more like
    prose and so that unit tests can patch a single call site.
    """
    return shutil.which(name) is not None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_latex() -> bool:
    """Check whether a LaTeX executable is available on the system ``PATH``.

    The check is deliberately lightweight — it does *not* invoke LaTeX or
    verify that the installation is functional.  Use it as a fast guard
    before attempting LaTeX-dependent operations.

    Returns
    -------
        ``True`` if ``latex`` is found on ``PATH``; ``False`` otherwise.

    Example
    -------
    ::

        if detect_latex():
            mpl.rcParams.update(configure_latex(spec))
        else:
            logger.warning("LaTeX not found; falling back to Matplotlib fonts.")
    """
    return _binary_exists("latex")


def detect_distribution() -> str | None:
    """Detect the installed TeX distribution by probing known manager binaries.

    The probing order is:

    1. ``tlmgr``   → TeX Live (most common in Linux / macOS / CI).
    2. ``miktex``  → MiKTeX ≥ 21 (Windows / cross-platform installer).
    3. ``mpm``     → MiKTeX ≤ 20 legacy package manager.
    4. ``latex``   → present but manager unknown; *assumed* TeX Live.
    5. Nothing     → no LaTeX installation detected.

    Returns
    -------
        ``"texlive"`` when TeX Live is detected or assumed.
        ``"miktex"`` when MiKTeX is detected.
        ``None`` when no LaTeX binary is found at all.

    Notes
    -----
    The ``"texlive"`` fallback in step 4 is an *assumption*, not a
    guarantee.  It reflects the statistical reality that TeX Live dominates
    CI and server environments.  Callers should treat the return value as a
    hint and handle unexpected distributions gracefully.

    Example
    -------
    ::

        dist = detect_distribution()
        match dist:
            case "texlive":
                install_package_texlive(pkg)
            case "miktex":
                install_package_miktex(pkg)
            case None:
                raise RuntimeError("No LaTeX installation found.")
    """
    if _binary_exists("tlmgr"):
        return "texlive"

    # MiKTeX ships two possible manager binaries depending on version.
    # Check both before concluding MiKTeX is absent.
    if _binary_exists("miktex") or _binary_exists("mpm"):
        return "miktex"

    if detect_latex():
        # A ``latex`` binary exists but no recognised distribution manager
        # was found.  This occurs in minimal container images (e.g. texlive-
        # base without tlmgr) and some manual installs.  TeX Live is the most
        # conservative assumption in server/CI contexts.
        return "texlive"

    # No LaTeX toolchain is present at all.
    return None


def configure_latex(spec: JournalSpec) -> dict[str, Any]:
    """Build the ``rcParams`` fragment required for LaTeX-based text rendering.

    Reads the ``font_fallback`` field from *spec*'s typography sub-spec and
    produces a ``dict`` suitable for passing directly to
    :func:`matplotlib.rcParams.update`.

    The returned mapping always contains:

    * ``"text.usetex": True`` — activates the LaTeX text renderer.
    * ``"font.family": <font_fallback>`` — sets the Matplotlib font family.

    When *font_fallback* is one of ``"serif"``, ``"sans-serif"``, or
    ``"monospace"``, the mapping additionally contains:

    * ``"text.latex.preamble": <preamble>`` — loads the matching PSNFSS
      font package and, where necessary, promotes it to the document default.

    Args:
        spec: A fully populated
            :class:`~plotstyle.specs.schema.JournalSpec` whose
            ``typography.font_fallback`` attribute drives font selection.

    Returns
    -------
        A ``dict[str, Any]`` ready to be merged into the broader rcParams
        dict (e.g. via ``rcParams.update(configure_latex(spec))``).

    Raises
    ------
        LatexConfigurationError: When *spec* is missing the
            ``typography`` attribute or when ``font_fallback`` is an
            empty string, indicating a malformed specification.

    Notes
    -----
    Font families not present in the internal mapping table (anything
    other than the three generic families above) produce no
    ``text.latex.preamble`` entry.  LaTeX will then use the document-class
    default font, typically *Computer Modern*.

    Example
    -------
    ::

        import matplotlib as mpl
        from plotstyle.engine.latex import configure_latex

        params = configure_latex(spec)
        mpl.rcParams.update(params)
    """
    # Guard against structurally incomplete specs before accessing nested
    # attributes — provides a clear error rather than an AttributeError.
    try:
        fallback: str = spec.typography.font_fallback
    except AttributeError as exc:
        raise LatexConfigurationError(
            f"JournalSpec is missing required 'typography.font_fallback' attribute: {exc}"
        ) from exc

    if not fallback:
        raise LatexConfigurationError(
            f"'typography.font_fallback' must be a non-empty string; got {fallback!r}."
        )

    params: dict[str, Any] = {
        "text.usetex": True,
        "font.family": fallback,
    }

    # Look up the PSNFSS preamble for this generic family.  An absent key
    # is intentional: unmapped families (e.g. a specific PostScript family
    # name) fall through to the LaTeX document-class default.
    preamble: str | None = _FALLBACK_TO_PREAMBLE.get(fallback)
    if preamble is not None:
        params["text.latex.preamble"] = preamble

    return params
