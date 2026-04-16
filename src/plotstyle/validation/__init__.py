"""PlotStyle validation public API.

Exposes `validate` for running the full check suite against a Matplotlib
figure and returning a `ValidationReport`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.specs import registry
from plotstyle.validation.checks import run_all
from plotstyle.validation.report import ValidationReport

if TYPE_CHECKING:
    from matplotlib.figure import Figure

__all__: list[str] = ["validate"]


def validate(fig: Figure, *, journal: str) -> ValidationReport:
    """Validate a figure against a journal's publication specification.

    Runs every registered check (dimensions, typography, line weights,
    colour accessibility, and export settings) and aggregates the results.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to validate.
    journal : str
        Journal preset name (e.g. ``"nature"``).

    Returns
    -------
    ValidationReport
        Aggregated results with one ``CheckResult`` per check. Call
        ``str(report)`` for a human-readable summary, or test
        ``report.passed`` for a boolean verdict.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If *journal* is not registered in the spec registry.
    """
    spec = registry.get(journal)
    results = run_all(fig, spec)
    return ValidationReport(journal=spec.metadata.name, checks=results)
