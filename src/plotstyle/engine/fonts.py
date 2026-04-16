"""Font detection, fallback selection, and PDF font verification.

``detect_available``
    Return the subset of font families installed on the current system.

``select_best``
    Return ``(font_name, is_exact_match)`` for the best available font in
    a journal specification.

``verify_embedded``
    Scan a PDF file for Type 3 font resources via heuristic byte search.
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

# PDF byte marker for Type 3 font resource declarations.
_TYPE3_MARKER: bytes = b"/Type3"


def _find_font_or_none(family: str) -> str | None:
    """Return the resolved font path for *family*, or ``None`` if not installed."""
    try:
        return font_manager.findfont(
            font_manager.FontProperties(family),
            fallback_to_default=False,
        )
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_available(families: list[str]) -> list[str]:
    """Return the subset of *families* installed on the current system, preserving order.

    Parameters
    ----------
    families : list[str]
        Font family names from most to least preferred.

    Returns
    -------
    list[str]
        Installed families in their original order; empty list when none found.
    """
    if not families:
        return []

    return [family for family in families if _find_font_or_none(family) is not None]


def select_best(spec: JournalSpec) -> tuple[str, bool]:
    """Return ``(font_name, is_exact_match)`` for the best available font in *spec*.

    Falls back to the spec's generic family (e.g. ``"sans-serif"``) when no
    preferred font is installed, emitting a
    :class:`~plotstyle._utils.warnings.FontFallbackWarning`.

    Parameters
    ----------
    spec : JournalSpec
        Journal specification with typography preferences.

    Returns
    -------
    tuple[str, bool]
        ``(font_name, is_exact_match)`` — ``is_exact_match`` is ``True`` only
        when the first-preference font was selected without substitution.
    """
    preferred_families = spec.typography.font_family
    available = detect_available(preferred_families)

    if available:
        selected = available[0]
        is_exact_match = selected == preferred_families[0]

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

    generic_fallback = spec.typography.font_fallback

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
    """Scan *pdf_path* for Type 3 fonts via heuristic byte search.

    Returns a list of issue dicts (``{"font": ..., "type": "Type3"}``), or an
    empty list when none are detected.  I/O errors emit a :class:`UserWarning`
    and return an empty list rather than raising.

    Parameters
    ----------
    pdf_path : Path
        PDF file to inspect.

    Returns
    -------
    list[dict[str, Any]]
        List of issue dicts; each dict has keys ``"font"`` (font name or
        heuristic placeholder) and ``"type"`` (``"Type3"``).  Empty list
        when no Type 3 fonts are detected or the file cannot be read.
    """
    issues: list[dict[str, Any]] = []

    try:
        raw_bytes = pdf_path.read_bytes()
    except OSError as exc:
        warnings.warn(
            f"Could not read {pdf_path!r} for font verification: {exc}",
            stacklevel=2,
        )
        return issues

    if _TYPE3_MARKER in raw_bytes:
        issues.append({"font": "(detected via heuristic)", "type": "Type3"})

    return issues
