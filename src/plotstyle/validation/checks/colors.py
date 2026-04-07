"""Color accessibility validation check.

This module registers a single check function,
:func:`check_color_accessibility`, via the ``@check`` decorator.

The check performs three independent inspections:

1. **Red-green pair detection** — flags ``WARN`` if the journal prohibits
   red-green colour combinations and the figure contains both a red-hued and
   a green-hued data element.

2. **Grayscale distinguishability** — flags ``WARN`` if the journal requires
   grayscale-readable figures and any two data colours have a luminance
   difference below 0.10 (10 % of full scale).

3. **Colour-only differentiator** — flags ``WARN`` when multiple data series
   in an axes share the same linestyle and marker, making colour the only
   visual cue to distinguish them.

Colour extraction
-----------------
:func:`_extract_data_colors` walks :class:`~matplotlib.lines.Line2D`,
:class:`~matplotlib.collections.PathCollection` (scatter), and
:class:`~matplotlib.container.BarContainer` objects across all axes.
Background, spine, and tick colours are deliberately excluded because they
are not data encodings.

Hue classification
------------------
HSV hue is used for red/green classification because it is more stable than
raw RGB channel comparisons when saturation varies.  Colours with HSV
saturation below 0.25 are treated as achromatic (grey) and excluded from hue
checks, avoiding false positives from nearly-white or nearly-black data marks.
"""

from __future__ import annotations

import colorsys
import itertools
from typing import TYPE_CHECKING

from matplotlib.colors import to_hex, to_rgb
from matplotlib.container import BarContainer

from plotstyle.color.grayscale import rgb_to_luminance
from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum HSV saturation for a colour to be considered chromatic.
# Below this threshold the hue is unreliable and the colour is treated as grey.
_MIN_SATURATION: float = 0.25

# Hue ranges (degrees, 0-360) for red and green classification.
# Red wraps around 0 degrees, so it is split into [330, 360] union [0, 30].
_RED_HUE_RANGES: tuple[tuple[float, float], ...] = ((330.0, 360.0), (0.0, 30.0))
_GREEN_HUE_RANGE: tuple[float, float] = (80.0, 160.0)

# Minimum luminance difference required for two colours to be distinguishable
# in grayscale.  Matches the threshold used in is_grayscale_safe().
_GRAYSCALE_THRESHOLD: float = 0.10

# Maximum number of violation examples included in a single check message
# to avoid overwhelming terminal output.
_MAX_VIOLATION_EXAMPLES: int = 5


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_data_colors(fig: Figure) -> list[str]:
    """Extract deduplicated hex colour strings from plotted data elements.

    Walks :class:`~matplotlib.lines.Line2D`, :class:`~matplotlib.collections.
    PathCollection` (scatter plots), and :class:`~matplotlib.container.
    BarContainer` objects across all axes.  Spine, tick, grid, and background
    colours are excluded because they are not data encodings.

    Args:
        fig: The figure to inspect.

    Returns
    -------
        Deduplicated list of hex colour strings in encounter order.
    """
    colors: list[str] = []
    seen: set[str] = set()

    for ax in fig.get_axes():
        # --- Line2D objects (ax.plot, ax.step, etc.) ---
        for line in ax.get_lines():
            c = to_hex(line.get_color())
            if c not in seen:
                seen.add(c)
                colors.append(c)

        # --- PathCollection (ax.scatter) ---
        for coll in ax.collections:
            try:
                face_colors = coll.get_facecolor()
            except (AttributeError, TypeError):
                # Some collection subclasses don't implement get_facecolor.
                continue
            for fc in face_colors:
                # fc is an RGBA array; take only the RGB channels.
                c = to_hex(fc[:3])
                if c not in seen:
                    seen.add(c)
                    colors.append(c)

        # --- BarContainer (ax.bar) ---
        # ax.containers can hold BarContainer, ErrorbarContainer, StemContainer,
        # etc.  Only BarContainer items are patches with get_facecolor(); other
        # types (e.g. ErrorbarContainer) yield None or Line2D artists and must
        # be skipped to avoid AttributeError.
        for container in ax.containers:
            if not isinstance(container, BarContainer):
                continue
            for patch in container:
                c = to_hex(patch.get_facecolor()[:3])
                if c not in seen:
                    seen.add(c)
                    colors.append(c)

    return colors


def _hue_in_range(hue_deg: float, lo: float, hi: float) -> bool:
    """Return ``True`` if *hue_deg* lies within the ``[lo, hi]`` interval.

    The interval does **not** wrap around 0°; callers are responsible for
    splitting wrap-around ranges into two disjoint calls (see
    :func:`_is_red_hue` for an example).

    Args:
        hue_deg: Hue in degrees, range ``[0, 360)``.
        lo: Lower bound of the hue range (inclusive).
        hi: Upper bound of the hue range (inclusive).

    Returns
    -------
        ``True`` if ``lo ≤ hue_deg ≤ hi``.
    """
    return lo <= hue_deg <= hi


def _is_red_hue(hue_deg: float) -> bool:
    """Return ``True`` if *hue_deg* falls in a red hue range.

    Red wraps around 0 degrees, so the check covers ``[330, 360] union [0, 30]``.
    """
    return any(_hue_in_range(hue_deg, lo, hi) for lo, hi in _RED_HUE_RANGES)


def _is_green_hue(hue_deg: float) -> bool:
    """Return ``True`` if *hue_deg* falls in the green hue range ``[80°, 160°]``."""
    lo, hi = _GREEN_HUE_RANGE
    return _hue_in_range(hue_deg, lo, hi)


def _has_red_green_pair(colors: list[str]) -> bool:
    """Return ``True`` if *colors* contains both a red-hued and a green-hued entry.

    Achromatic colours (HSV saturation < :data:`_MIN_SATURATION`) are excluded
    from hue classification to avoid false positives from near-grey data marks.

    Args:
        colors: List of hex colour strings to inspect.

    Returns
    -------
        ``True`` if at least one red-hued and one green-hued colour are present.
    """
    has_red = False
    has_green = False

    for c in colors:
        r, g, b = to_rgb(c)
        h, s, _ = colorsys.rgb_to_hsv(r, g, b)

        # Skip near-grey colours where hue is unreliable.
        if s < _MIN_SATURATION:
            continue

        hue_deg = h * 360.0
        has_red = has_red or _is_red_hue(hue_deg)
        has_green = has_green or _is_green_hue(hue_deg)

        # Short-circuit as soon as both are found.
        if has_red and has_green:
            return True

    return False


def _find_grayscale_conflicts(
    colors: list[str],
    threshold: float = _GRAYSCALE_THRESHOLD,
) -> list[tuple[int, int]]:
    """Return index pairs whose luminance difference is below *threshold*.

    Args:
        colors: List of hex colour strings.
        threshold: Minimum required luminance difference (``[0, 1]``).

    Returns
    -------
        List of ``(i, j)`` pairs (``i < j``) where the luminance delta is
        below *threshold*.  Empty when all pairs are sufficiently distinct.
    """
    luminances: list[float] = [rgb_to_luminance(*to_rgb(c)) for c in colors]
    return [
        (i, j)
        for (i, j) in itertools.combinations(range(len(luminances)), 2)
        if abs(luminances[i] - luminances[j]) < threshold
    ]


def _color_only_differentiator(fig: Figure) -> bool:
    """Return ``True`` if colour is the sole visual cue between data series.

    Inspects all axes: if any axis has two or more ``Line2D`` objects that
    all share the same ``(linestyle, marker)`` combination, colour is the
    only differentiator and the function returns ``True``.

    Args:
        fig: The figure to inspect.

    Returns
    -------
        ``True`` if at least one axes has multiple lines with identical
        linestyle and marker; ``False`` otherwise.
    """
    for ax in fig.get_axes():
        lines = ax.get_lines()
        if len(lines) < 2:
            continue

        style_set: set[tuple[str, str]] = set()
        for line in lines:
            ls = str(line.get_linestyle())
            # Normalise absent-marker variants to a single sentinel string.
            marker = str(line.get_marker())
            if marker in ("None", "none", ""):
                marker = "none"
            style_set.add((ls, marker))

        # One unique (linestyle, marker) combo for all lines → colour-only.
        if len(style_set) == 1:
            return True

    return False


# ---------------------------------------------------------------------------
# Registered check
# ---------------------------------------------------------------------------


@check
def check_color_accessibility(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate colour usage against journal accessibility requirements.

    Performs three independent sub-checks and returns one
    :class:`~plotstyle.validation.report.CheckResult` per applicable check:

    1. **Red-green pair detection** — skipped if the journal's
       ``spec.color.avoid_combinations`` does not list ``["red", "green"]``.
    2. **Grayscale distinguishability** — skipped if
       ``spec.color.grayscale_required`` is ``False`` or fewer than two
       data colours are present.
    3. **Colour-only differentiator** — always executed; emits ``WARN`` when
       multiple lines share linestyle and marker.

    Args:
        fig: The :class:`~matplotlib.figure.Figure` to inspect.
        spec: Journal specification defining colour accessibility constraints.

    Returns
    -------
        List of :class:`~plotstyle.validation.report.CheckResult` objects,
        one per applicable sub-check.  Checks that are skipped produce no
        result entry.

    Example:
        >>> results = check_color_accessibility(fig, spec)
        >>> [r.check_name for r in results]
        ['color.red_green', 'color.grayscale', 'color.sole_differentiator']
    """
    results: list[CheckResult] = []
    data_colors = _extract_data_colors(fig)

    # ------------------------------------------------------------------
    # 1. Red-green pair detection
    # ------------------------------------------------------------------
    avoid = spec.color.avoid_combinations
    rg_prohibited = any(set(combo) == {"red", "green"} for combo in avoid)

    if rg_prohibited:
        if _has_red_green_pair(data_colors):
            results.append(
                CheckResult(
                    status=CheckStatus.WARN,
                    check_name="color.red_green",
                    message=(
                        f"Red-green colour pair detected. "
                        f"{spec.metadata.name} prohibits red-green combinations "
                        f"as they are indistinguishable for deuteranopes."
                    ),
                    fix_suggestion=(
                        "Replace red/green with a colorblind-safe pair such as "
                        "blue/orange, or use plotstyle.palette() which selects "
                        "the journal's default accessible palette."
                    ),
                )
            )
        else:
            results.append(
                CheckResult(
                    status=CheckStatus.PASS,
                    check_name="color.red_green",
                    message="No red-green colour pair detected.",
                )
            )

    # ------------------------------------------------------------------
    # 2. Grayscale distinguishability
    # ------------------------------------------------------------------
    if spec.color.grayscale_required and len(data_colors) >= 2:
        conflicts = _find_grayscale_conflicts(data_colors)
        if conflicts:
            # Format the first few conflicting pairs for the message.
            pair_strs = [f"({i},{j})" for i, j in conflicts[:_MAX_VIOLATION_EXAMPLES]]
            results.append(
                CheckResult(
                    status=CheckStatus.WARN,
                    check_name="color.grayscale",
                    message=(
                        f"Colour pairs {', '.join(pair_strs)} have luminance "
                        f"difference < {_GRAYSCALE_THRESHOLD:.0%} and are "
                        f"indistinguishable in grayscale. "
                        f"{spec.metadata.name} requires grayscale-readable figures."
                    ),
                    fix_suggestion=(
                        "Choose colours with greater luminance contrast, or use "
                        "plotstyle.palette() which provides a grayscale-safe set "
                        "for each journal."
                    ),
                )
            )
        else:
            results.append(
                CheckResult(
                    status=CheckStatus.PASS,
                    check_name="color.grayscale",
                    message=(
                        f"All colour pairs differ by ≥ {_GRAYSCALE_THRESHOLD:.0%} "
                        "luminance; figure is grayscale-readable."
                    ),
                )
            )

    # ------------------------------------------------------------------
    # 3. Colour-only differentiator
    # ------------------------------------------------------------------
    if _color_only_differentiator(fig):
        results.append(
            CheckResult(
                status=CheckStatus.WARN,
                check_name="color.sole_differentiator",
                message=(
                    "One or more axes contain multiple data series distinguished "
                    "solely by colour (identical linestyle and marker). "
                    "Colour-blind readers may not be able to tell them apart."
                ),
                fix_suggestion=(
                    "Use plotstyle.palette(journal, n, with_markers=True) to "
                    "automatically assign distinct markers and linestyles, or "
                    "set them explicitly per series."
                ),
            )
        )

    return results
