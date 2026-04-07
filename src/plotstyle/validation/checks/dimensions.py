"""Dimension validation check.

This module registers :func:`check_dimensions`, which verifies that a figure's
physical size conforms to the single-column and double-column widths, and the
maximum height, specified by the target journal.

Tolerance
---------
An absolute tolerance of :data:`_TOLERANCE_MM` (1.0 mm by default) is applied
to all comparisons to accommodate floating-point and unit-conversion rounding
that occurs when constructing figures in inches (matplotlib's native unit) and
comparing against millimetre journal specifications.

Example
-------
    >>> from plotstyle.validation.checks.dimensions import check_dimensions
    >>> results = check_dimensions(fig, spec)
    >>> [r.check_name for r in results]
    ['dimensions.width', 'dimensions.height']
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.specs.units import Dimension
from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Absolute tolerance in millimetres for width and height comparisons.
# 1.0 mm is chosen to be tight enough to catch genuine size errors while
# absorbing inch → mm conversion rounding (2.54 cm/in introduces ~0.01 mm
# rounding per inch; a 7-inch figure accumulates ≈ 0.07 mm, well within 1 mm).
_TOLERANCE_MM: float = 1.0


# ---------------------------------------------------------------------------
# Registered check
# ---------------------------------------------------------------------------


@check
def check_dimensions(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate figure width and height against journal column specifications.

    Two sub-checks are performed:

    - **Width** — the figure's width must be within :data:`_TOLERANCE_MM` of
      either the single-column or double-column specification from *spec*.
      Any other width produces a ``FAIL``.
    - **Height** — the figure's height must not exceed the journal's maximum
      allowed height plus :data:`_TOLERANCE_MM`.  Exceeding this produces a
      ``FAIL``.

    Args:
        fig: The :class:`~matplotlib.figure.Figure` whose size is inspected.
            The figure's size is read via :meth:`~matplotlib.figure.Figure.get_size_inches`.
        spec: Journal specification providing ``dimensions.single_column_mm``,
            ``dimensions.double_column_mm``, and ``dimensions.max_height_mm``.

    Returns
    -------
        A list of exactly two :class:`~plotstyle.validation.report.CheckResult`
        objects — one for width (``"dimensions.width"``) and one for height
        (``"dimensions.height"``).

    Example:
        >>> results = check_dimensions(fig, spec)
        >>> results[0].check_name
        'dimensions.width'
        >>> results[1].check_name
        'dimensions.height'

    Notes
    -----
        - The figure's size is read in inches and converted to millimetres via
          :class:`~plotstyle.specs.units.Dimension` to avoid duplicating the
          unit-conversion constant.
        - ``constrained_layout`` or ``tight_layout`` adjustments do not alter
          the figure's *size* (only the subplot spacing), so the check is
          unaffected by layout engine settings.
    """
    results: list[CheckResult] = []

    # Convert from matplotlib's native inches to millimetres.
    width_in, height_in = fig.get_size_inches()
    width_mm: float = Dimension(width_in, "in").to_mm()
    height_mm: float = Dimension(height_in, "in").to_mm()

    single_mm: float = spec.dimensions.single_column_mm
    double_mm: float = spec.dimensions.double_column_mm
    max_h_mm: float = spec.dimensions.max_height_mm

    # ------------------------------------------------------------------
    # Width check — must match single- or double-column spec
    # ------------------------------------------------------------------
    single_ok = abs(width_mm - single_mm) <= _TOLERANCE_MM
    double_ok = abs(width_mm - double_mm) <= _TOLERANCE_MM

    if single_ok or double_ok:
        col_type = "single column" if single_ok else "double column"
        results.append(
            CheckResult(
                status=CheckStatus.PASS,
                check_name="dimensions.width",
                message=f"Figure width {width_mm:.1f}mm matches {col_type} spec ({single_mm if single_ok else double_mm}mm).",
            )
        )
    else:
        results.append(
            CheckResult(
                status=CheckStatus.FAIL,
                check_name="dimensions.width",
                message=(
                    f"Figure width {width_mm:.1f}mm does not match "
                    f"{spec.metadata.name} single-column ({single_mm}mm) "
                    f"or double-column ({double_mm}mm) specifications."
                ),
                fix_suggestion=(
                    f'Use plotstyle.figure("{spec.metadata.name.lower()}", columns=1) '
                    f"or set figsize to {single_mm}mm or {double_mm}mm width."
                ),
            )
        )

    # ------------------------------------------------------------------
    # Height check — must not exceed maximum
    # ------------------------------------------------------------------
    if height_mm <= max_h_mm + _TOLERANCE_MM:
        results.append(
            CheckResult(
                status=CheckStatus.PASS,
                check_name="dimensions.height",
                message=(
                    f"Figure height {height_mm:.1f}mm is within the "
                    f"{spec.metadata.name} maximum of {max_h_mm}mm."
                ),
            )
        )
    else:
        results.append(
            CheckResult(
                status=CheckStatus.FAIL,
                check_name="dimensions.height",
                message=(
                    f"Figure height {height_mm:.1f}mm exceeds the "
                    f"{spec.metadata.name} maximum of {max_h_mm}mm "
                    f"by {height_mm - max_h_mm:.1f}mm."
                ),
                fix_suggestion=(
                    f"Reduce figure height to ≤ {max_h_mm}mm. "
                    "Consider splitting the figure across multiple panels."
                ),
            )
        )

    return results
