"""PlotStyle validation public API.

This module exposes the single entry point for validating a Matplotlib figure
against a journal's publication requirements:

    :func:`validate` — resolve the journal spec, run all checks, and return a
    :class:`~plotstyle.validation.report.ValidationReport`.

Typical usage
-------------
    >>> import plotstyle
    >>> from plotstyle.validation import validate
    >>>
    >>> with plotstyle.use("nature"):
    ...     fig, ax = plotstyle.figure("nature", columns=1)
    ...     ax.plot([0, 1, 2], [0, 1, 0])
    >>> report = validate(fig, journal="nature")
    >>> print(report)
    >>> if not report.passed:
    ...     for failure in report.failures:
    ...         print(failure.check_name, "—", failure.fix_suggestion)

Integration notes
-----------------
- The ``journal`` argument is case-insensitive; it is normalised by
  :func:`~plotstyle.specs.registry.get` before the spec is fetched.
- All registered check functions (from :mod:`plotstyle.validation.checks`)
  are executed in one pass; there is no way to skip individual checks via
  this API.  For selective validation, call
  :func:`~plotstyle.validation.checks._base.get_registered_checks` directly
  and filter the list before passing to
  :func:`~plotstyle.validation.checks.run_all`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.specs import registry
from plotstyle.validation.checks import run_all
from plotstyle.validation.report import ValidationReport

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def validate(fig: Figure, *, journal: str) -> ValidationReport:
    """Validate a figure against a journal's publication specification.

    Resolves the named journal specification from the global registry, runs
    every registered validation check against *fig*, and returns the
    aggregated results as a :class:`~plotstyle.validation.report.ValidationReport`.

    Args:
        fig: The :class:`~matplotlib.figure.Figure` to inspect.  The figure
            should be fully composed (all artists added, layout applied) before
            calling this function, as some checks measure rendered properties
            such as text size and line width.
        journal: Case-insensitive journal identifier (e.g., ``"nature"``,
            ``"ieee"``, ``"science"``).  Must correspond to a spec registered
            in :mod:`plotstyle.specs.registry`.

    Returns
    -------
        A :class:`~plotstyle.validation.report.ValidationReport` summarising
        the outcome of every check.  Call
        :meth:`~plotstyle.validation.report.ValidationReport.passed` for
        a single boolean result, iterate
        :meth:`~plotstyle.validation.report.ValidationReport.failures` for
        actionable errors, or use
        :meth:`~plotstyle.validation.report.ValidationReport.to_dict` for
        programmatic access.

    Raises
    ------
        KeyError: If *journal* does not match any registered journal
            specification (propagated from
            :meth:`~plotstyle.specs.SpecRegistry.get`).

    Example:
        >>> from plotstyle.validation import validate
        >>> report = validate(fig, journal="nature")
        >>> print(report)
        >>> report.passed
        True

    Notes
    -----
        - The function is intentionally keyword-only for ``journal`` (enforced
          by the ``*`` in the signature) to prevent positional-argument
          confusion in call sites that pass multiple figures or specs.
        - Validation does not modify *fig* or any global Matplotlib state.
    """
    spec = registry.get(journal)
    results = run_all(fig, spec)
    return ValidationReport(journal=spec.metadata.name, checks=results)
