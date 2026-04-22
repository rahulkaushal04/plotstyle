"""Line weight validation check (internal, not part of public API).

Registers `check_line_weights` via the `check` decorator. Inspects all Line2D
objects and spines against the journal's minimum line-weight constraint.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

_MAX_VIOLATION_EXAMPLES: int = 5


@check
def check_line_weights(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate all Line2D and spine widths against the journal's minimum line weight.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to validate.
    spec : JournalSpec
        The journal specification supplying the minimum line weight.

    Returns
    -------
    list[CheckResult]
        A single-element list with a ``PASS`` result when all lines meet
        the minimum weight, or a ``FAIL`` result listing violating elements.
    """
    min_linewidth: float = spec.line.min_weight_pt
    violations: list[str] = []

    for ax in fig.get_axes():
        for line in ax.get_lines():
            lw = line.get_linewidth()
            if lw < min_linewidth:
                label = line.get_label() or "(unlabeled line)"
                violations.append(f"{label!r}: {lw:.2f}pt")

        for spine_name, spine in ax.spines.items():
            lw = spine.get_linewidth()
            if lw < min_linewidth:
                violations.append(f"spine '{spine_name}': {lw:.2f}pt")

    line_weight_assumed = "line.min_weight_pt" in spec.assumed_fields

    if violations:
        truncated = violations[:_MAX_VIOLATION_EXAMPLES]
        suffix = (
            f" … and {len(violations) - _MAX_VIOLATION_EXAMPLES} more."
            if len(violations) > _MAX_VIOLATION_EXAMPLES
            else ""
        )
        if line_weight_assumed:
            message = (
                f"{len(violations)} element(s) below the library-default minimum "
                f"of {min_linewidth}pt "
                f"({spec.metadata.name} does not define an official minimum line weight): "
                f"{'; '.join(truncated)}{suffix}"
            )
            fix = (
                f"Consider keeping line weights at or above {min_linewidth}pt as a "
                f"general guideline. Check {spec.metadata.source_url} for any "
                f"official {spec.metadata.name} line weight requirements."
            )
        else:
            message = (
                f"{len(violations)} element(s) below the "
                f"{spec.metadata.name} minimum of {min_linewidth}pt: "
                f"{'; '.join(truncated)}{suffix}"
            )
            fix = (
                f"Set linewidth ≥ {min_linewidth}pt on all plotted lines. "
                "Apply globally with "
                f"mpl.rcParams['lines.linewidth'] = {min_linewidth}, or "
                "per-line with the lw= keyword argument."
            )
        return [
            CheckResult(
                status=CheckStatus.WARN if line_weight_assumed else CheckStatus.FAIL,
                check_name="lines.min_weight",
                message=message,
                fix_suggestion=fix,
            )
        ]

    return [
        CheckResult(
            status=CheckStatus.PASS,
            check_name="lines.min_weight",
            message=(
                f"All plotted lines and spines meet the "
                f"{spec.metadata.name} minimum line weight of {min_linewidth}pt."
            ),
        )
    ]
