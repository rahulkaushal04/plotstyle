"""Check registry — discovers and executes all registered validation checks.

Imports all check sub-modules so their ``check``-decorated functions are
registered, then exposes `run_all` as the single entry-point for the full
check suite.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.validation.checks import (
    colors,  # noqa: F401
    dimensions,  # noqa: F401
    export,  # noqa: F401
    lines,  # noqa: F401
    typography,  # noqa: F401
)
from plotstyle.validation.checks._base import get_registered_checks

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec
    from plotstyle.validation.report import CheckResult

__all__: list[str] = ["run_all"]


def run_all(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Execute every registered validation check and return the aggregated results.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to validate.
    spec : JournalSpec
        The journal specification to validate *fig* against.

    Returns
    -------
    list[CheckResult]
        One ``CheckResult`` per check function, in registration order.
    """
    results: list[CheckResult] = []
    for check_fn in get_registered_checks():
        results.extend(check_fn(fig, spec))
    return results
