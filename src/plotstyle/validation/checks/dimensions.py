"""Dimension validation check (internal, not part of public API).

Registers `check_dimensions` via the `check` decorator. Verifies figure width
against single- and double-column specs and height against the journal's maximum.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.specs.units import Dimension
from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

_TOLERANCE_MM: float = 1.0


@check
def check_dimensions(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate figure width and height against journal column specifications.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to validate.
    spec : JournalSpec
        The journal specification to check against.

    Returns
    -------
    list[CheckResult]
        A list of two `CheckResult` instances: one for width compliance and one
        for height compliance.
    """
    results: list[CheckResult] = []

    width_in, height_in = fig.get_size_inches()
    width_mm: float = Dimension(width_in, "in").to_mm()
    height_mm: float = Dimension(height_in, "in").to_mm()

    single_mm = spec.dimensions.single_column_mm
    double_mm = spec.dimensions.double_column_mm
    max_h_mm = spec.dimensions.max_height_mm

    if single_mm is None or double_mm is None:
        results.append(
            CheckResult(
                status=CheckStatus.WARN,
                check_name="dimensions.width",
                message=(
                    f"{spec.metadata.name} does not publish column widths; "
                    f"width check skipped (figure is {width_mm:.1f}mm wide)."
                ),
                fix_suggestion=(
                    f"Consult {spec.metadata.source_url} for the journal's "
                    "official column width requirements."
                ),
            )
        )
    else:
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
                        f'Use plotstyle.figure("{spec.key}", columns=1) '
                        f"or set figsize to {single_mm}mm or {double_mm}mm width."
                    ),
                )
            )

    if max_h_mm is None:
        results.append(
            CheckResult(
                status=CheckStatus.WARN,
                check_name="dimensions.height",
                message=(
                    f"{spec.metadata.name} does not publish a maximum figure height; "
                    f"height check skipped (figure is {height_mm:.1f}mm tall)."
                ),
                fix_suggestion=(
                    f"Consult {spec.metadata.source_url} for the journal's "
                    "official height requirements."
                ),
            )
        )
    elif height_mm <= max_h_mm + _TOLERANCE_MM:
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
