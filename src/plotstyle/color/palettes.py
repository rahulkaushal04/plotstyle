"""Journal-aware color palette engine with colorblind-safe defaults.

This module maps academic journal identifiers to curated, perceptually
optimised colour palettes and exposes a single high-level :func:`palette`
function for retrieving those colours.

All built-in palettes are stored as JSON files under the ``data/`` sub-package
directory co-located with this module.  Palette data is loaded lazily on first
access and cached in memory for the lifetime of the process.

Supported journals
------------------
The :data:`JOURNAL_PALETTE_MAP` constant maps each journal identifier to its
recommended palette name.  The following journals are supported out of the
box:

    ``"acs"``, ``"cell"``, ``"elsevier"``, ``"ieee"``, ``"nature"``,
    ``"plos"``, ``"prl"``, ``"science"``, ``"springer"``, ``"wiley"``

Palette families
----------------
- **okabe_ito**    — 8-colour palette designed for colorblind accessibility
  (Okabe & Ito, 2002).
- **tol_bright**   — Paul Tol's bright qualitative scheme.
- **tol_muted**    — Paul Tol's muted qualitative scheme.
- **tol_vibrant**  — Paul Tol's vibrant qualitative scheme.
- **safe_grayscale** — Luminance-separated palette for black-and-white print.

Example
-------
    >>> from plotstyle.color.palettes import palette
    >>> colors = palette("nature", n=4)
    >>> print(colors)
    ['#E69F00', '#56B4E9', '#009E73', '#F0E442']

    >>> styled = palette("ieee", n=3, with_markers=True)
    >>> for color, ls, marker in styled:
    ...     ax.plot(x, y, color=color, linestyle=ls, marker=marker)
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_DATA_DIR: Path = Path(__file__).parent / "data"

#: Maps lowercase journal identifiers to the palette name whose JSON file
#: lives in ``_DATA_DIR``.  New journals can be added here without touching
#: any other logic in this module.
JOURNAL_PALETTE_MAP: dict[str, str] = {
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

# Default linestyle and marker sequences for ``with_markers=True``.
# Using short tuples rather than lists signals that these are fixed sequences.
_LINESTYLES: tuple[str, ...] = ("-", "--", "-.", ":")
_MARKERS: tuple[str, ...] = ("o", "s", "^", "D", "v", "P")

# Module-level palette cache: palette name → list of hex colour strings.
# Populated lazily by :func:`load_palette`; never evicted during a process run.
_palette_cache: dict[str, list[str]] = {}

# Public type alias for the two possible return types of :func:`palette`.
ColorList = list[str]
StyledColorList = list[tuple[str, str, str]]
PaletteResult = ColorList | StyledColorList


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class PaletteNotFoundError(FileNotFoundError):
    """Raised when a requested palette JSON file does not exist.

    Extends :exc:`FileNotFoundError` so that callers who catch the built-in
    exception continue to work without modification.
    """


class UnknownJournalError(KeyError):
    """Raised when the caller passes a journal identifier not in :data:`JOURNAL_PALETTE_MAP`.

    Extends :exc:`KeyError` to preserve backward-compatible ``except KeyError``
    handling while providing a more descriptive error message.
    """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_not_found_message(name: str) -> str:
    """Return a human-readable error message listing available palettes.

    Separated into its own function so the glob is executed only when an
    error actually occurs, not on every failed cache lookup.
    """
    available = ", ".join(sorted(p.stem for p in _DATA_DIR.glob("*.json")))
    return f"Palette {name!r} not found in {_DATA_DIR}. Available palettes: {available or '(none)'}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_palette(name: str) -> list[str]:
    """Load a colour palette from the bundled JSON data files.

    Palette data is cached after the first successful load; subsequent calls
    for the same *name* return the cached list without re-reading disk.

    Each JSON file must contain a top-level ``"colors"`` key whose value is a
    list of hex colour strings (e.g., ``["#E69F00", "#56B4E9", ...]``).

    Args:
        name: Palette identifier matching the stem of a ``.json`` file inside
            the ``data/`` sub-directory (e.g., ``"okabe_ito"``).

    Returns
    -------
        List of hex colour strings in the order defined by the JSON file.

    Raises
    ------
        PaletteNotFoundError: If no ``<name>.json`` file exists in the data
            directory.  The error message lists all available palettes.
        KeyError: If the JSON file exists but does not contain a ``"colors"``
            key.
        json.JSONDecodeError: If the JSON file is malformed.

    Example:
        >>> colors = load_palette("okabe_ito")
        >>> colors[0]
        '#E69F00'

    Notes
    -----
        - The cache is process-scoped; it is not shared across workers in a
          multiprocessing context.  Each worker loads palettes independently.
        - Palette files are expected to be small (< 1 KB); no streaming or
          chunked loading is applied.
    """
    if name in _palette_cache:
        return _palette_cache[name]

    json_path: Path = _DATA_DIR / f"{name}.json"
    if not json_path.is_file():
        raise PaletteNotFoundError(_build_not_found_message(name))

    with json_path.open(encoding="utf-8") as fh:
        data: dict[str, object] = json.load(fh)

    # Explicit cast to str guards against JSON files where colour values are
    # stored as integers (e.g., 0xFF0000) rather than strings.
    colors: list[str] = [str(c) for c in data["colors"]]  # type: ignore[union-attr]
    _palette_cache[name] = colors
    return colors


def palette(
    journal: str,
    n: int = 6,
    *,
    with_markers: bool = False,
) -> PaletteResult:
    """Return *n* colours from the recommended palette for *journal*.

    Colours are cycled if *n* exceeds the palette's length (most palettes
    contain 7-10 colours).  When *with_markers* is ``True``, line style and
    marker annotations are returned alongside each colour so that callers can
    create publication-ready line plots in a single iteration.

    Args:
        journal: Journal identifier string (case-insensitive).  Must be a key
            in :data:`JOURNAL_PALETTE_MAP`.
        n: Number of colours to return.  Must be a positive integer.  Cycles
            through the palette if *n* exceeds its length.  Defaults to ``6``.
        with_markers: If ``True``, return a list of
            ``(colour, linestyle, marker)`` tuples instead of bare hex strings.
            Line styles and markers are also cycled independently.
            Defaults to ``False``.

    Returns
    -------
        A :data:`ColorList` (``list[str]``) of hex colour strings when
        *with_markers* is ``False``, or a :data:`StyledColorList`
        (``list[tuple[str, str, str]]``) of ``(colour, linestyle, marker)``
        tuples when *with_markers* is ``True``.

    Raises
    ------
        UnknownJournalError: If *journal* (lowercased) is not present in
            :data:`JOURNAL_PALETTE_MAP`.  The error message lists all known
            journal identifiers.
        ValueError: If *n* is not a positive integer.
        PaletteNotFoundError: Propagated from :func:`load_palette` if the
            mapped palette file is missing.

    Example:
        >>> colors = palette("nature", n=4)
        >>> len(colors)
        4
        >>> styled = palette("ieee", n=3, with_markers=True)
        >>> styled[0]  # e.g., ('#000000', '-', 'o')
        ('#000000', '-', 'o')

    Notes
    -----
        - Journal identifiers are normalised to lowercase before lookup, so
          ``"Nature"``, ``"NATURE"``, and ``"nature"`` are all equivalent.
        - The cycling behaviour for *n* > palette length uses modular indexing
          rather than ``itertools.cycle`` to avoid consuming an unbounded
          iterator and to keep the implementation stateless.
    """
    if n < 1:
        raise ValueError(f"n must be a positive integer, got {n!r}.")

    key: str = journal.lower()
    if key not in JOURNAL_PALETTE_MAP:
        known = ", ".join(sorted(JOURNAL_PALETTE_MAP))
        raise UnknownJournalError(f"Unknown journal {journal!r}. Known journals: {known}")

    palette_name: str = JOURNAL_PALETTE_MAP[key]
    colors: list[str] = load_palette(palette_name)
    palette_len: int = len(colors)

    # Cycle colours modularly if n exceeds the palette length.
    selected: list[str] = [colors[i % palette_len] for i in range(n)]

    if not with_markers:
        return selected

    # Pair each colour with an independently cycled line style and marker.
    return [
        (
            color,
            _LINESTYLES[i % len(_LINESTYLES)],
            _MARKERS[i % len(_MARKERS)],
        )
        for i, color in enumerate(selected)
    ]
