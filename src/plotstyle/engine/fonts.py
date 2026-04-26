"""Font detection, fallback selection, and PDF font verification.

``detect_available``
    Return the subset of font families installed on the current system.

``select_best``
    Return ``(font_name, is_exact_match)`` for the best available font in
    a journal specification.

``check_overlay_fonts``
    Return a ``{font_name: is_installed}`` mapping for fonts required by
    a style overlay.

``verify_embedded``
    Scan a PDF file for Type 3 font resources via heuristic byte search.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from matplotlib import font_manager

from plotstyle._utils.warnings import FontFallbackWarning, PlotStyleWarning

if TYPE_CHECKING:
    from pathlib import Path

    from plotstyle.overlays.schema import StyleOverlay
    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "check_overlay_fonts",
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
    ``FontFallbackWarning``.

    Parameters
    ----------
    spec : JournalSpec
        Journal specification with typography preferences.

    Returns
    -------
    tuple[str, bool]
        ``(font_name, is_exact_match)``: ``is_exact_match`` is ``True`` only
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
        f"Install {preferred_families[0]!r} for exact compliance."
        " If you recently installed it, rebuild matplotlib's font cache:"
        " matplotlib.font_manager._rebuild()"
        if preferred_families
        else ""
    )
    font_list = ", ".join(f"'{f}'" for f in preferred_families)
    warnings.warn(
        (f"Fonts {font_list} not found; using {generic_fallback!r} as fallback. {install_hint}"),
        FontFallbackWarning,
        stacklevel=2,
    )

    return generic_fallback, False


def check_overlay_fonts(overlay: StyleOverlay) -> dict[str, bool]:
    """Return a ``{font_name: is_installed}`` mapping for fonts required by *overlay*.

    Parameters
    ----------
    overlay : StyleOverlay
        Overlay to inspect.  When it has no ``[requires]`` section the
        returned dict is empty.

    Returns
    -------
    dict[str, bool]
        Each key is a font family name from ``overlay.requires["fonts"]``; the
        value is ``True`` when the font resolves on the current system.
    """
    if overlay.requires is None:
        return {}
    fonts: list[str] = overlay.requires.get("fonts", [])
    return {font: _find_font_or_none(font) is not None for font in fonts}


def verify_embedded(pdf_path: Path) -> list[dict[str, Any]]:
    """Scan *pdf_path* for Type 3 fonts via heuristic byte search.

    Uses a byte-pattern search for ``/Type3`` in the raw PDF data.  This is a
    *presence check*, not an enumeration; at most one issue dict is returned
    regardless of how many Type 3 fonts the file contains.  I/O errors emit a
    ``PlotStyleWarning`` and return an empty
    list rather than raising.

    Parameters
    ----------
    pdf_path : Path
        PDF file to inspect.

    Returns
    -------
    list[dict[str, Any]]
        A single-element list ``[{"font": "(detected via heuristic)",
        "type": "Type3"}]`` when the ``/Type3`` marker is found, or an empty
        list when not detected or the file cannot be read.
    """
    issues: list[dict[str, Any]] = []

    try:
        raw_bytes = pdf_path.read_bytes()
    except OSError as exc:
        warnings.warn(
            f"Could not read {pdf_path!r} for font verification: {exc}",
            PlotStyleWarning,
            stacklevel=2,
        )
        return issues

    if _TYPE3_MARKER in raw_bytes:
        issues.append({"font": "(detected via heuristic)", "type": "Type3"})

    return issues
