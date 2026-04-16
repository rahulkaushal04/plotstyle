"""Color accessibility validation check (internal, not part of public API).

Registers `check_color_accessibility` via the `check` decorator. Checks for
red-green colour pairs, grayscale distinguishability, and
colour-as-sole-differentiator issues.
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

# Minimum HSV saturation below which hue is unreliable (treated as achromatic).
_MIN_SATURATION: float = 0.25

# Red wraps around 0 degrees, so it is split into [330, 360] and [0, 30].
_RED_HUE_RANGES: tuple[tuple[float, float], ...] = ((330.0, 360.0), (0.0, 30.0))
_GREEN_HUE_RANGE: tuple[float, float] = (80.0, 160.0)

_GRAYSCALE_THRESHOLD: float = 0.10
_MAX_VIOLATION_EXAMPLES: int = 5


def _extract_data_colors(fig: Figure) -> list[str]:
    """Extract deduplicated hex colour strings from plotted data elements.

    Walks Line2D, PathCollection (scatter), and BarContainer objects across all
    axes. Spine, tick, grid, and background colours are excluded.

    Parameters
    ----------
    fig : Figure
        The figure to inspect.

    Returns
    -------
    list[str]
        Deduplicated list of hex colour strings in encounter order.
    """
    colors: list[str] = []
    seen: set[str] = set()

    for ax in fig.get_axes():
        for line in ax.get_lines():
            c = to_hex(line.get_color())
            if c not in seen:
                seen.add(c)
                colors.append(c)

        for coll in ax.collections:
            try:
                face_colors = coll.get_facecolor()
            except (AttributeError, TypeError):
                continue
            for fc in face_colors:
                c = to_hex(fc[:3])
                if c not in seen:
                    seen.add(c)
                    colors.append(c)

        # Only BarContainer has per-patch get_facecolor(); skip other containers.
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
    """Return ``True`` if ``lo ≤ hue_deg ≤ hi`` (no wraparound)."""
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
    """Return ``True`` if *colors* contains both a red-hued and a green-hued entry."""
    has_red = False
    has_green = False

    for c in colors:
        r, g, b = to_rgb(c)
        h, s, _ = colorsys.rgb_to_hsv(r, g, b)

        if s < _MIN_SATURATION:
            continue

        hue_deg = h * 360.0
        has_red = has_red or _is_red_hue(hue_deg)
        has_green = has_green or _is_green_hue(hue_deg)

        if has_red and has_green:
            return True

    return False


def _find_grayscale_conflicts(
    colors: list[str],
    threshold: float = _GRAYSCALE_THRESHOLD,
) -> list[tuple[int, int]]:
    """Return ``(i, j)`` index pairs whose luminance delta is below *threshold*.

    Parameters
    ----------
    colors : list[str]
        List of hex colour strings to check.
    threshold : float
        Minimum luminance delta required to distinguish two colours
        in grayscale.  Defaults to :data:`_GRAYSCALE_THRESHOLD`.

    Returns
    -------
    list[tuple[int, int]]
        List of ``(i, j)`` index pairs (0-based) where the absolute luminance
        difference is below *threshold*.  Empty when all colour pairs are
        sufficiently distinct.
    """
    luminances: list[float] = [rgb_to_luminance(*to_rgb(c)) for c in colors]
    return [
        (i, j)
        for (i, j) in itertools.combinations(range(len(luminances)), 2)
        if abs(luminances[i] - luminances[j]) < threshold
    ]


def _color_only_differentiator(fig: Figure) -> bool:
    """Return ``True`` if any axes has multiple lines with identical linestyle and marker.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to inspect.

    Returns
    -------
    bool
        ``True`` if any axes has two or more lines that share the same
        linestyle and marker combination, meaning colour is the sole visual
        differentiator.  ``False`` if every axes uses distinct non-colour
        cues or has only one line.
    """
    for ax in fig.get_axes():
        lines = ax.get_lines()
        if len(lines) < 2:
            continue

        style_set: set[tuple[str, str]] = set()
        for line in lines:
            ls = str(line.get_linestyle())
            marker = str(line.get_marker())
            if marker in ("None", "none", ""):
                marker = "none"
            style_set.add((ls, marker))

        if len(style_set) == 1:
            return True

    return False


@check
def check_color_accessibility(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate colour accessibility: red-green pairs, grayscale safety, sole differentiator.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to validate.
    spec : JournalSpec
        The journal specification to check against.

    Returns
    -------
    list[CheckResult]
        A list of `CheckResult` instances, one per applicable sub-check.
    """
    results: list[CheckResult] = []
    data_colors = _extract_data_colors(fig)

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

    if spec.color.grayscale_required and len(data_colors) >= 2:
        conflicts = _find_grayscale_conflicts(data_colors)
        if conflicts:
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
