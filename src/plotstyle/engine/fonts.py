"""Font detection, fallback selection, and PDF font verification.

This module provides three public utilities for font management within the
PlotStyle engine:

``detect_available``
    Filters a list of font-family names to those installed on the current
    system, preserving the original preference order.

``select_best``
    Chooses the highest-priority available font for a journal spec, emitting
    a :class:`~plotstyle._utils.warnings.FontFallbackWarning` when the
    top-preference font cannot be found.

``verify_embedded``
    Performs a heuristic byte-level scan of a saved PDF to flag the presence
    of Type 3 fonts, which many submission portals reject.

Notes
-----
Font availability checks rely on :func:`matplotlib.font_manager.findfont`.
Results depend on the fonts installed on the host system at import time.
Matplotlib may cache font lookups; restart the Python process or call
:func:`matplotlib.font_manager.get_font` after installing new fonts to
ensure fresh results.

Type 3 fonts are device-dependent bitmaps embedded in PDFs. Many journal
submission portals reject them. Use ``pdf.fonttype=42`` (TrueType) in
``matplotlib.rcParams`` to avoid generating them.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from matplotlib import font_manager

from plotstyle._utils.warnings import FontFallbackWarning

if TYPE_CHECKING:
    from pathlib import Path

    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "detect_available",
    "select_best",
    "verify_embedded",
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Byte sequence used by the PDF specification to declare a Type 3 font
# resource block. Searching for this marker covers the vast majority of
# real-world PDFs without requiring a full PDF parser.
_TYPE3_MARKER: bytes = b"/Type3"


def _find_font_or_none(family: str) -> str | None:
    """Return the resolved font file path for *family*, or ``None`` if absent.

    Wraps :func:`~matplotlib.font_manager.findfont` and suppresses the
    ``ValueError`` it raises for unknown families, converting it to a
    ``None`` sentinel. The isolation into a dedicated function prevents the
    ``try/except`` block from living inside a list comprehension loop, which
    would incur unnecessary overhead on each iteration (see PEP 659 /
    ruff PERF203).

    Args:
        family: Font family name to look up (e.g. ``"Helvetica"``).

    Returns
    -------
        Absolute path string to the matched font file, or ``None`` when the
        family is not installed on the current system.

    Notes
    -----
    ``fallback_to_default=False`` is critical here: without it,
    :func:`~matplotlib.font_manager.findfont` silently returns the default
    font for any unknown family, making every lookup appear successful.
    """
    try:
        return font_manager.findfont(
            font_manager.FontProperties(family),
            fallback_to_default=False,
        )
    except ValueError:
        # findfont raises ValueError when the family cannot be located and
        # fallback_to_default is disabled. Treat this as "not installed".
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_available(families: list[str]) -> list[str]:
    """Return the subset of *families* that are installed on the current system.

    Probes each font family name using matplotlib's font manager and returns
    only those for which a corresponding font file can be located. The
    original preference order is preserved so that callers can safely take
    ``result[0]`` as the best available option.

    Args:
        families: Ordered list of font family names to probe, from most to
            least preferred (e.g. ``["Helvetica", "Arial", "DejaVu Sans"]``).

    Returns
    -------
        A (possibly empty) list of font family names whose corresponding font
        files were located by :mod:`matplotlib.font_manager`, in the same
        order as *families*. Returns an empty list when none are found.

    Example::

        available = detect_available(["Helvetica", "Arial", "DejaVu Sans"])
        # e.g. ["Arial", "DejaVu Sans"] on a system without Helvetica

    Notes
    -----
    Availability is determined by :func:`matplotlib.font_manager.findfont`
    with ``fallback_to_default=False``. Results reflect the fonts installed
    at the time matplotlib's font manager was last initialised. Installing
    new fonts without rebuilding the cache may yield stale results.
    """
    if not families:
        return []

    # Use a generator expression inside the list constructor to avoid building
    # an intermediate list of (family, path) pairs — only the names are needed.
    return [family for family in families if _find_font_or_none(family) is not None]


def select_best(spec: JournalSpec) -> tuple[str, bool]:
    """Select the highest-priority available font for a journal specification.

    Iterates through the spec's font preference list in order and selects the
    first family that is installed on the current system. Emits a
    :class:`~plotstyle._utils.warnings.FontFallbackWarning` whenever the
    selected font is not the top-preference, so callers and end-users are
    informed of the deviation from the journal's requirements.

    When *no* preferred font is installed at all, the spec's generic family
    (e.g. ``"sans-serif"``) is returned as a last resort, allowing matplotlib
    to resolve its own system default for that generic class.

    Args:
        spec: Journal specification containing typography preferences. Must
            expose ``spec.typography.font_family`` (ordered ``list[str]``),
            ``spec.typography.font_fallback`` (generic family string), and
            ``spec.metadata.name`` (human-readable journal name).

    Returns
    -------
        A two-tuple ``(font_name, is_exact_match)`` where:

        - *font_name* is the selected family string, suitable for direct
          assignment to ``matplotlib.rcParams["font.family"]``. May be a
          generic fallback such as ``"sans-serif"`` when no preferred font
          is available.
        - *is_exact_match* is ``True`` only when the first-preference font
          was found and selected without any compromise.

    Raises
    ------
        AttributeError: If *spec* does not expose the expected ``typography``
            or ``metadata`` attributes, indicating a malformed spec object.

    Example::

        font_name, exact = select_best(nature_spec)
        if not exact:
            print("Substituting font — figure may not meet journal guidelines.")
        mpl.rcParams["font.family"] = font_name

    Notes
    -----
    The warning is emitted at ``stacklevel=2`` so that it points to the
    call site in user code rather than to this function's internals.
    """
    preferred_families: list[str] = spec.typography.font_family
    available: list[str] = detect_available(preferred_families)

    if available:
        selected: str = available[0]
        # The top preference is the zeroth element; any other selection
        # means the ideal font is absent from the system.
        is_exact_match: bool = selected == preferred_families[0]

        if not is_exact_match:
            warnings.warn(
                (
                    f"{preferred_families[0]!r} not found. "
                    f"Using {selected!r} as substitute "
                    f"(acceptable for {spec.metadata.name})."
                ),
                FontFallbackWarning,
                stacklevel=2,
            )

        return selected, is_exact_match

    # No preferred font was found at all. Fall back to the generic family so
    # matplotlib can resolve its own system default (e.g. DejaVu Sans for
    # "sans-serif"). This guarantees a renderable figure even in minimal
    # environments, at the cost of potential guideline non-compliance.
    generic_fallback: str = spec.typography.font_fallback

    install_hint = (
        f"Install {preferred_families[0]!r} for exact compliance." if preferred_families else ""
    )
    warnings.warn(
        (
            f"None of {preferred_families!r} found. "
            f"Falling back to generic {generic_fallback!r}. "
            f"{install_hint}"
        ),
        FontFallbackWarning,
        stacklevel=2,
    )

    return generic_fallback, False


def verify_embedded(pdf_path: Path) -> list[dict[str, Any]]:
    """Check a PDF file for problematic font types via heuristic byte scan.

    Reads the raw PDF bytes and searches for markers indicating the presence
    of Type 3 fonts. Type 3 fonts are device-dependent bitmaps that many
    journal submission portals reject outright. This function provides a
    lightweight pre-submission check without requiring a full PDF parser.

    Args:
        pdf_path: Path to the PDF file to inspect. The file must exist and be
            readable by the current process. Symbolic links are followed.

    Returns
    -------
        A list of issue dictionaries, each with the following keys:

        - ``"font"`` (:class:`str`): Font identifier or ``"(detected via
          heuristic)"`` when the exact name cannot be extracted.
        - ``"type"`` (:class:`str`): Detected font type string. Currently
          only ``"Type3"`` is reported.

        An empty list indicates no problems were detected. A non-empty list
        should be treated as a warning that the PDF may be rejected.

    Raises
    ------
        This function does **not** raise on I/O errors. Instead, it emits a
        :class:`UserWarning` and returns an empty list, allowing the caller
        to continue without interruption. Raise-on-error behaviour can be
        added by the caller by checking the file before passing it in.

    Example::

        from pathlib import Path

        issues = verify_embedded(Path("figure.pdf"))
        if issues:
            for issue in issues:
                print(f"⚠  {issue['type']} font detected: {issue['font']}")
        else:
            print("No problematic fonts detected.")

    Notes
    -----
    **Detection is heuristic.** The function searches for the literal byte
    sequence ``/Type3`` in the raw PDF content. This catches the vast
    majority of real-world Type 3 font declarations but may produce false
    positives in PDFs with unusual internal structure (e.g. where ``/Type3``
    appears inside a content stream rather than a font resource dictionary).

    TrueType fonts embedded via ``pdf.fonttype=42`` appear as ``/TrueType``
    in the PDF stream and are intentionally not flagged — their presence is
    expected and desirable when PlotStyle's safety parameters are applied.

    For definitive font auditing, consider a dedicated PDF inspection tool
    such as ``pdffonts`` (Poppler) or ``PyMuPDF``.
    """
    issues: list[dict[str, Any]] = []

    try:
        raw_bytes: bytes = pdf_path.read_bytes()
    except OSError as exc:
        # Surface the I/O problem as a warning rather than an exception so
        # that a missing or unreadable file does not abort an otherwise
        # successful figure-export pipeline.
        warnings.warn(
            f"Could not read {pdf_path!r} for font verification: {exc}",
            stacklevel=2,
        )
        return issues

    # Heuristic: the PDF specification uses the /Type3 keyword within a font
    # resource dictionary to declare a Type 3 font. A byte-level substring
    # search is sufficient for well-formed PDFs and avoids the complexity and
    # dependency cost of a full PDF parser.
    if _TYPE3_MARKER in raw_bytes:
        issues.append({"font": "(detected via heuristic)", "type": "Type3"})

    return issues
