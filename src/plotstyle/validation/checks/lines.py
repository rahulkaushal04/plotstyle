"""Line weight validation check.

This module registers :func:`check_line_weights`, which verifies that every
:class:`~matplotlib.lines.Line2D` object and every axis spine in a figure
meets the journal's minimum line weight specification.

Why line weights matter
-----------------------
Many journals (particularly IEEE and physical-sciences publishers) specify a
minimum line weight — typically 0.5 pt — to ensure that figure elements remain
visible after the half-tone or rasterisation processes applied during printing.
Lines below this threshold can disappear or appear as artefacts in the final
publication.

Scope
-----
The check covers:

- **Line2D objects** — from ``ax.plot``, ``ax.step``, ``ax.axhline``, etc.
- **Axis spines** — the box borders drawn around each axes (``top``,
  ``bottom``, ``left``, ``right``).

Intentionally excluded: tick marks, grid lines, legend borders, and
collection/patch edges, because these are controlled separately and their
weight requirements vary more across journals.

Example
-------
    >>> from plotstyle.validation.checks.lines import check_line_weights
    >>> results = check_line_weights(fig, spec)
    >>> results[0].check_name
    'lines.min_weight'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

# Maximum number of violation examples to include in the result message
# before truncating with an implicit "and N more…" (not shown; the user is
# expected to inspect the figure systematically once they know a problem exists).
_MAX_VIOLATION_EXAMPLES: int = 5


@check
def check_line_weights(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate line and spine widths against the journal's minimum requirement.

    Iterates over every :class:`~matplotlib.lines.Line2D` and axis spine in
    *fig* and records any whose ``linewidth`` falls below
    ``spec.line.min_weight_pt``.

    Args:
        fig: The :class:`~matplotlib.figure.Figure` to inspect.
        spec: Journal specification providing ``line.min_weight_pt`` and
            ``metadata.name`` for error messages.

    Returns
    -------
        A list containing exactly one :class:`~plotstyle.validation.report.CheckResult`
        with check name ``"lines.min_weight"``.  The status is:

        - ``PASS`` — all inspected elements meet the minimum line weight.
        - ``FAIL`` — one or more elements are below the minimum, with up to
          :data:`_MAX_VIOLATION_EXAMPLES` offending names and widths listed.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> ax.plot([0, 1], [0, 1], lw=0.3)  # below most journal minimums
        >>> results = check_line_weights(fig, spec)
        >>> results[0].is_failure
        True

    Notes
    -----
        - Line labels are read from
          :meth:`~matplotlib.lines.Line2D.get_label`.  Auto-generated legend
          labels (``"_line0"``, ``"_collection0"``, etc.) start with
          ``"_"``, but the check reports them as ``"(unlabeled)"`` only when
          the label is empty or ``None`` — the underscore-prefixed auto-labels
          are included as-is so the user can identify the artist.
        - The tolerance applied to width comparisons is strict (``<`` rather
          than ``<=``) so that a line *exactly* at the minimum passes.
    """
    min_linewidth: float = spec.line.min_weight_pt
    violations: list[str] = []

    for ax in fig.get_axes():
        # --- Plotted Line2D objects ---
        for line in ax.get_lines():
            lw = line.get_linewidth()
            if lw < min_linewidth:
                # Prefer the user-set label; fall back to a generic descriptor.
                label = line.get_label() or "(unlabeled line)"
                violations.append(f"{label!r}: {lw:.2f}pt")

        # --- Axis spines (frame borders) ---
        for spine_name, spine in ax.spines.items():
            lw = spine.get_linewidth()
            if lw < min_linewidth:
                violations.append(f"spine '{spine_name}': {lw:.2f}pt")

    if violations:
        # Show only the first few violations to keep the message readable.
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
