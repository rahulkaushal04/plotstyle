"""Validation report data types returned by the PlotStyle validation layer.

Classes
-------
CheckStatus
    Enumeration of check outcomes: ``PASS``, ``FAIL``, or ``WARN``.
CheckResult
    Immutable record describing the outcome of a single check.
ValidationReport
    Aggregated collection of ``CheckResult`` instances from a full validation run.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

__all__: list[str] = [
    "CheckResult",
    "CheckStatus",
    "ValidationReport",
]


class CheckStatus(enum.Enum):
    """Outcome of a single validation check: ``PASS``, ``FAIL``, or ``WARN``."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass(slots=True)
class CheckResult:
    """Record describing the outcome of one validation check.

    Attributes
    ----------
    status : CheckStatus
        Outcome of the check.
    check_name : str
        Dot-namespaced identifier (e.g. ``"dimensions.width"``).
    message : str
        Human-readable description of the check outcome.
    fix_suggestion : str | None
        Actionable hint for resolving a failure or warning; ``None`` on pass.
    """

    status: CheckStatus
    check_name: str
    message: str
    fix_suggestion: str | None = None

    @property
    def is_failure(self) -> bool:
        """Return ``True`` when this result has ``FAIL`` status."""
        return self.status is CheckStatus.FAIL

    @property
    def is_warning(self) -> bool:
        """Return ``True`` when this result has ``WARN`` status."""
        return self.status is CheckStatus.WARN


_STATUS_ICONS: dict[CheckStatus, str] = {
    CheckStatus.PASS: "✓ PASS",
    CheckStatus.FAIL: "✗ FAIL",
    CheckStatus.WARN: "⚠ WARN",
}

_TABLE_MIN_WIDTH: int = 56


@dataclass(slots=True)
class ValidationReport:
    """Aggregated results of a full validation run against a journal spec.

    Attributes
    ----------
    journal : str
        Display name of the journal the figure was validated against.
    checks : list[CheckResult]
        Ordered results, one per registered check.
    """

    journal: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Return ``True`` if no check produced a ``FAIL`` status."""
        return not any(c.is_failure for c in self.checks)

    @property
    def failures(self) -> list[CheckResult]:
        """Return all results with ``FAIL`` status."""
        return [c for c in self.checks if c.is_failure]

    @property
    def warnings(self) -> list[CheckResult]:
        """Return all results with ``WARN`` status."""
        return [c for c in self.checks if c.is_warning]

    def to_dict(self) -> dict[str, Any]:
        """Serialise the report to a JSON-compatible dictionary.

        Returns
        -------
        dict[str, Any]
            Keys: ``"journal"``, ``"passed"``, ``"checks"``. Each entry in
            ``"checks"`` has ``"status"``, ``"check_name"``, ``"message"``,
            and ``"fix_suggestion"``.
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

    def __str__(self) -> str:
        """Render the report as a box-drawing table with a summary footer.

        Returns
        -------
        str
            Multi-line string with a header, one line per check, and a
            ``N/total passed, W warning(s), F failure(s)`` footer.
        """
        header = f" PlotStyle Validation Report: {self.journal} "
        width = max(len(header) + 4, _TABLE_MIN_WIDTH)
        col_width = width - 14

        lines: list[str] = [
            "┌" + "─" * (width - 2) + "┐",
            "│" + header.center(width - 2) + "│",
            "├" + "─" * 10 + "┬" + "─" * (width - 13) + "┤",
        ]

        for c in self.checks:
            msg = c.message if len(c.message) <= col_width else c.message[: col_width - 3] + "..."
            lines.append(
                "│ " + _STATUS_ICONS[c.status].ljust(8) + " │ " + msg.ljust(col_width) + "│"
            )

        lines.append("└" + "─" * 10 + "┴" + "─" * (width - 13) + "┘")

        n_pass = sum(1 for c in self.checks if c.status is CheckStatus.PASS)
        n_fail = len(self.failures)
        n_warn = len(self.warnings)
        total = len(self.checks)
        lines.append(f"{n_pass}/{total} checks passed, {n_warn} warning(s), {n_fail} failure(s)")

        return "\n".join(lines)
