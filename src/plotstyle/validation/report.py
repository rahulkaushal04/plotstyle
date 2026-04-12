"""Validation report dataclasses for PlotStyle.

This module defines the data model for validation results produced by
:mod:`plotstyle.validation.checks`.  All output from the validation engine
flows through these classes before being consumed by callers or displayed
to users.

Class hierarchy
---------------
- :class:`CheckStatus` — Enumeration of the three possible outcomes for any
  single check: ``PASS``, ``FAIL``, or ``WARN``.
- :class:`CheckResult` — Immutable record representing one check outcome,
  including an optional human-readable fix suggestion.
- :class:`ValidationReport` — Aggregate container for a full validation run
  against a specific journal, with convenience properties for filtering and
  serialisation.

Example
-------
    >>> from plotstyle.validation.report import CheckStatus, CheckResult, ValidationReport
    >>> result = CheckResult(
    ...     status=CheckStatus.FAIL,
    ...     check_name="dimensions.width",
    ...     message="Figure width 100mm does not match Nature spec (88mm / 180mm).",
    ...     fix_suggestion='Use plotstyle.figure("nature", columns=1).',
    ... )
    >>> report = ValidationReport(journal="Nature", checks=[result])
    >>> report.passed
    False
    >>> print(report)  # renders a box-drawing ASCII table
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Status enumeration
# ---------------------------------------------------------------------------


class CheckStatus(enum.Enum):
    """Outcome of a single validation check.

    - ``PASS`` -- The check criterion was met; no action required.
    - ``FAIL`` -- The check criterion was *not* met; the figure is likely
      to be rejected or require revision by the journal.
    - ``WARN`` -- The check could not be verified conclusively, or the
      criterion is advisory rather than mandatory.  The figure may still
      be accepted, but the author should review the flagged item.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


# ---------------------------------------------------------------------------
# Single check result
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class CheckResult:
    """Immutable record describing the outcome of one validation check.

    Instances are produced exclusively by check functions registered via the
    ``check`` decorator in ``plotstyle.validation.checks._base`` and should
    not normally be constructed by user code.

    Attributes
    ----------
    status : CheckStatus
        The outcome of the check.
    check_name : str
        Dot-namespaced identifier for the check, e.g.
        ``"dimensions.width"`` or ``"color.grayscale"``.  Used as a
        stable key for programmatic filtering.
    message : str
        Human-readable description of the outcome.  For ``PASS``
        results this summarises what was verified; for ``FAIL`` / ``WARN``
        results it describes the specific problem found.
    fix_suggestion : str or None
        Optional actionable guidance for resolving a ``FAIL``
        or ``WARN`` result.  ``None`` for ``PASS`` results.

    Example:
        >>> result = CheckResult(
        ...     status=CheckStatus.WARN,
        ...     check_name="color.sole_differentiator",
        ...     message="Colour is the sole differentiator between data series.",
        ...     fix_suggestion="Add distinct markers or linestyles per series.",
        ... )
        >>> result.is_warning
        True
        >>> result.is_failure
        False
    """

    status: CheckStatus
    check_name: str
    message: str
    fix_suggestion: str | None = None

    @property
    def is_failure(self) -> bool:
        """Return ``True`` if this result has :attr:`CheckStatus.FAIL` status."""
        return self.status is CheckStatus.FAIL

    @property
    def is_warning(self) -> bool:
        """Return ``True`` if this result has :attr:`CheckStatus.WARN` status."""
        return self.status is CheckStatus.WARN


# ---------------------------------------------------------------------------
# Icons used in __str__ — defined once so they are easy to change
# ---------------------------------------------------------------------------

_STATUS_ICONS: dict[CheckStatus, str] = {
    CheckStatus.PASS: "✓ PASS",
    CheckStatus.FAIL: "✗ FAIL",
    CheckStatus.WARN: "⚠ WARN",
}

# Minimum total width of the rendered table (characters).
_TABLE_MIN_WIDTH: int = 56


# ---------------------------------------------------------------------------
# Aggregate report
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ValidationReport:
    """Aggregated results of a full validation run against a journal spec.

    Produced by :func:`~plotstyle.validation.validate` and contains one
    :class:`CheckResult` per registered check function.

    Attributes
    ----------
    journal : str
        Display name of the journal that was validated against
        (e.g., ``"Nature"`` or ``"IEEE Transactions"``).
    checks : list
        Ordered list of :class:`CheckResult` objects, one per check
        executed.  Ordering follows the registration order of checks in
        ``plotstyle.validation.checks``.

    Example:
        >>> report = ValidationReport(journal="Nature", checks=[...])
        >>> if not report.passed:
        ...     for failure in report.failures:
        ...         print(failure.message, failure.fix_suggestion)
    """

    journal: str
    checks: list[CheckResult] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def passed(self) -> bool:
        """Return ``True`` if *no* check produced a :attr:`CheckStatus.FAIL`.

        ``WARN`` results do not affect this property; a report with warnings
        but no failures is still considered passing.

        Example:
            >>> report.passed
            True
        """
        return not any(c.is_failure for c in self.checks)

    @property
    def failures(self) -> list[CheckResult]:
        """Return all :class:`CheckResult` objects with ``FAIL`` status.

        Returns an empty list when the report has no failures.

        Example:
            >>> [f.check_name for f in report.failures]
            ['dimensions.width']
        """
        return [c for c in self.checks if c.is_failure]

    @property
    def warnings(self) -> list[CheckResult]:
        """Return all :class:`CheckResult` objects with ``WARN`` status.

        Returns an empty list when the report has no warnings.
        """
        return [c for c in self.checks if c.is_warning]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the report to a JSON-compatible dictionary.

        The returned dict is suitable for ``json.dumps``, logging pipelines,
        and programmatic downstream processing.

        Returns
        -------
        dict
            A dictionary with the following keys:

            - ``"journal"`` (:class:`str`) — the journal display name.
            - ``"passed"`` (:class:`bool`) — overall pass/fail outcome.
            - ``"checks"`` (:class:`list`) — one entry per :class:`CheckResult`
              with keys ``status``, ``check_name``, ``message``, and
              ``fix_suggestion``.

        Examples
        --------
            >>> import json
            >>> print(json.dumps(report.to_dict(), indent=2))
        """
        return {
            "journal": self.journal,
            "passed": self.passed,
            "checks": [
                {
                    "status": c.status.value,
                    "check_name": c.check_name,
                    "message": c.message,
                    "fix_suggestion": c.fix_suggestion,
                }
                for c in self.checks
            ],
        }

    # ------------------------------------------------------------------
    # Human-readable rendering
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        """Render the report as a box-drawing table with a summary footer.

        Long messages are truncated with an ellipsis to fit the table column.
        The table width is set to the maximum of the header length plus
        padding and :data:`_TABLE_MIN_WIDTH`, so the table always has a
        sensible minimum width even for very short journal names.

        Returns
        -------
            A multi-line string suitable for printing to a terminal.

        Example:
            >>> print(report)
            ┌──────────────────────────────────────────────────┐
            │    PlotStyle Validation Report — Nature          │
            ├──────────┬───────────────────────────────────────┤
            │ ✓ PASS   │ Figure width: 88.0mm (single column)  │
            │ ✗ FAIL   │ pdf.fonttype = 3 (should be 42)       │
            └──────────┴───────────────────────────────────────┘
            1/2 checks passed, 0 warning(s), 1 failure(s)
        """
        header = f" PlotStyle Validation Report — {self.journal} "
        # Ensure the table is at least _TABLE_MIN_WIDTH characters wide,
        # and at least wide enough to contain the header with 2 chars of
        # padding on each side.
        width = max(len(header) + 4, _TABLE_MIN_WIDTH)

        # Column available for the message field after the status icon cell.
        # Layout: "│ " (2) + icon (8) + " │ " (3) + message + "│" (1) = 14 overhead.
        col_width = width - 14

        lines: list[str] = [
            "┌" + "─" * (width - 2) + "┐",
            "│" + header.center(width - 2) + "│",
            "├" + "─" * 10 + "┬" + "─" * (width - 13) + "┤",
        ]

        for c in self.checks:
            icon = _STATUS_ICONS[c.status]
            msg = c.message
            # Truncate to prevent line wrapping in terminals.
            if len(msg) > col_width:
                msg = msg[: col_width - 3] + "..."
            lines.append("│ " + icon.ljust(8) + " │ " + msg.ljust(col_width) + "│")

        lines.append("└" + "─" * 10 + "┴" + "─" * (width - 13) + "┘")

        # Summary counts
        n_pass = sum(1 for c in self.checks if c.status is CheckStatus.PASS)
        n_fail = len(self.failures)
        n_warn = len(self.warnings)
        total = len(self.checks)
        lines.append(f"{n_pass}/{total} checks passed, {n_warn} warning(s), {n_fail} failure(s)")

        return "\n".join(lines)
