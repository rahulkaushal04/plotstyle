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

    if violations:
        truncated = violations[:_MAX_VIOLATION_EXAMPLES]
        suffix = (
            f" … and {len(violations) - _MAX_VIOLATION_EXAMPLES} more."
            if len(violations) > _MAX_VIOLATION_EXAMPLES
            else ""
        )
        return [
            CheckResult(
                status=CheckStatus.FAIL,
                check_name="lines.min_weight",
                message=(
                    f"{len(violations)} element(s) below the "
                    f"{spec.metadata.name} minimum of {min_linewidth}pt: "
                    f"{'; '.join(truncated)}{suffix}"
                ),
                fix_suggestion=(
                    f"Set linewidth ≥ {min_linewidth}pt on all plotted lines. "
                    "Apply globally with "
                    f"mpl.rcParams['lines.linewidth'] = {min_linewidth}, or "
                    "per-line with the lw= keyword argument."
                ),
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
