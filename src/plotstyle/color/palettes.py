"""Journal-aware colour palette engine with colorblind-safe defaults.

Provides named palettes tuned for each supported journal and utilities for
loading and cycling through them with optional marker pairing.

Public API
----------
:data:`JOURNAL_PALETTE_MAP`
    Maps each journal key to its recommended palette name.

:func:`load_palette`
    Load a raw colour list from a named palette JSON file.

:func:`palette`
    Return *n* colours (and optionally markers) from a journal's palette.

Exceptions
----------
:class:`PaletteNotFoundError`
    Raised when a requested palette JSON file cannot be found.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from plotstyle.specs import SpecNotFoundError

_DATA_DIR: Final[Path] = Path(__file__).parent / "data"

__all__: list[str] = [
    "JOURNAL_PALETTE_MAP",
    "PaletteNotFoundError",
    "load_palette",
    "palette",
]

JOURNAL_PALETTE_MAP: Final[dict[str, str]] = {
    "acs": "tol_bright",
    "cell": "okabe_ito",
    "elsevier": "tol_bright",
    "ieee": "safe_grayscale",
    "nature": "okabe_ito",
    "plos": "okabe_ito",
    "prl": "tol_muted",
    "science": "tol_vibrant",
    "springer": "tol_bright",
    "wiley": "tol_muted",
}

_LINESTYLES: Final[tuple[str, ...]] = ("-", "--", "-.", ":")
_MARKERS: Final[tuple[str, ...]] = ("o", "s", "^", "D", "v", "P")

_palette_cache: dict[str, list[str]] = {}

ColorList = list[str]
StyledColorList = list[tuple[str, str, str]]
PaletteResult = ColorList | StyledColorList


class PaletteNotFoundError(FileNotFoundError):
    """Raised when a requested palette JSON file does not exist."""


def _build_not_found_message(name: str) -> str:
    """Return a human-readable error message listing available palette names."""
    available = ", ".join(sorted(p.stem for p in _DATA_DIR.glob("*.json")))
    return f"Palette {name!r} not found in {_DATA_DIR}. Available palettes: {available or '(none)'}"


def load_palette(name: str) -> list[str]:
    """Load a colour palette from bundled JSON data, caching on first access.

    Parameters
    ----------
    name : str
        Palette key matching a JSON file stem in the bundled ``color/data/``
        directory (e.g. ``"okabe_ito"``, ``"tol_bright"``).

    Returns
    -------
    list[str]
        List of hex colour strings for the named palette.

    Raises
    ------
    PaletteNotFoundError
        If no JSON file matching *name* exists in the bundled data directory.
    """
    if name in _palette_cache:
        return _palette_cache[name]

    json_path = _DATA_DIR / f"{name}.json"
    if not json_path.is_file():
        raise PaletteNotFoundError(_build_not_found_message(name))

    with json_path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    colors = [str(c) for c in data["colors"]]
    _palette_cache[name] = colors
    return colors


def palette(
    journal: str,
    n: int | None = None,
    *,
    with_markers: bool = False,
) -> PaletteResult:
    """Return colours from the recommended palette for *journal*, cycling if needed.

    Parameters
    ----------
    journal : str
        Journal identifier (e.g. ``"nature"``, ``"ieee"``).
    n : int | None
        Number of colours to return.  When ``None`` (the default), all
        colours in the underlying palette are returned.  When *n* exceeds
        the palette size, colours cycle from the beginning.
    with_markers : bool
        When ``True``, each entry is a
        ``(color, linestyle, marker)`` tuple instead of a bare hex string.

    Returns
    -------
    PaletteResult
        A list of hex colour strings when *with_markers* is ``False``.
        A list of ``(color, linestyle, marker)`` tuples when *with_markers*
        is ``True``.

    Raises
    ------
    SpecNotFoundError
        If *journal* is not in :data:`JOURNAL_PALETTE_MAP`.
    ValueError
        If *n* is not a positive integer.
    """
    key = journal.lower()
    if key not in JOURNAL_PALETTE_MAP:
        raise SpecNotFoundError(journal, available=sorted(JOURNAL_PALETTE_MAP))

    palette_name = JOURNAL_PALETTE_MAP[key]
    colors = load_palette(palette_name)
    palette_len = len(colors)

    if n is None:
        count = palette_len
    else:
        if n < 1:
            raise ValueError(f"n must be a positive integer, got {n!r}.")
        count = n

    selected = [colors[i % palette_len] for i in range(count)]

    if not with_markers:
        return selected

    return [
        (
            color,
            _LINESTYLES[i % len(_LINESTYLES)],
            _MARKERS[i % len(_MARKERS)],
        )
        for i, color in enumerate(selected)
    ]
