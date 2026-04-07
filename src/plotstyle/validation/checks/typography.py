"""Typography validation check — font size compliance.

This module registers :func:`check_typography`, which verifies that every
visible text element in a figure falls within the minimum and maximum font
sizes specified by the target journal.

Text elements inspected
-----------------------
- Figure-level text (``fig.texts`` — suptitle, annotations added directly to
  the figure).
- Axes titles (``ax.title``).
- Axis labels (``ax.xaxis.label``, ``ax.yaxis.label``).
- Tick labels (``ax.get_xticklabels()``, ``ax.get_yticklabels()``).
- Legend text entries (from every legend attached to an axes).

Empty and whitespace-only text artists are skipped because they contribute no
visible content and should not be penalised for having a default font size that
might fall outside the permitted range.

Why font size matters
---------------------
Journals enforce minimum font sizes (typically 6-7 pt) to ensure legibility
after reduction to column width during typesetting.  Maximum sizes prevent
labels from dominating the figure area and clashing with the journal's body
text.

Example
-------
    >>> from plotstyle.validation.checks.typography import check_typography
    >>> results = check_typography(fig, spec)
    >>> results[0].check_name
    'typography.font_size'
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from matplotlib.text import Text

    from plotstyle.specs.schema import JournalSpec

# Maximum number of violation examples to include in the result message.
_MAX_VIOLATION_EXAMPLES: int = 5


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _gather_text_artists(fig: Figure) -> list[Text]:
    """Collect all relevant :class:`~matplotlib.text.Text` artists from *fig*.

    Includes figure-level text and all per-axes text elements that carry
    meaningful content labels: titles, axis labels, tick labels, and legend
    entries.

    Args:
        fig: The figure to inspect.

    Returns
    -------
        Flat list of :class:`~matplotlib.text.Text` instances in the order:
        figure texts → (for each axes) title, x-label, y-label, x-tick
        labels, y-tick labels, legend texts.

    Notes
    -----
        - Axes with empty titles or labels are included; the caller
          (:func:`check_typography`) is responsible for skipping
          whitespace-only entries.
        - The list may contain duplicates if an artist is somehow shared
          across axes; in practice this does not occur in normal figure
          construction.
    """
    texts: list[Text] = list(fig.texts)  # copy to avoid mutating fig.texts

    for ax in fig.get_axes():
        texts.append(ax.title)
        texts.append(ax.xaxis.label)
        texts.append(ax.yaxis.label)
        texts.extend(ax.get_xticklabels())
        texts.extend(ax.get_yticklabels())

        legend = ax.get_legend()
        if legend is not None:
            texts.extend(legend.get_texts())

    return texts


# ---------------------------------------------------------------------------
# Registered check
# ---------------------------------------------------------------------------


@check
def check_typography(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate all visible text elements against journal font size limits.

    Gathers every :class:`~matplotlib.text.Text` artist in *fig* (via
    :func:`_gather_text_artists`), skips empty/whitespace-only entries, and
    checks whether each artist's font size is within
    ``[spec.typography.min_font_pt, spec.typography.max_font_pt]``.

    Args:
        fig: The :class:`~matplotlib.figure.Figure` to inspect.  Should be
            fully composed before calling (tick labels may not be finalised
            until the figure is rendered or the layout engine has run).
        spec: Journal specification providing ``typography.min_font_pt``,
            ``typography.max_font_pt``, and ``metadata.name``.

    Returns
    -------
        A list containing exactly one :class:`~plotstyle.validation.report.CheckResult`
        with check name ``"typography.font_size"``.  Status is:

        - ``PASS`` — all non-empty text elements are within the allowed range.
        - ``FAIL`` — one or more text elements fall outside the range, with
          up to :data:`_MAX_VIOLATION_EXAMPLES` specific violations reported.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> ax.set_xlabel("Time (s)", fontsize=4)  # below most minimums
        >>> results = check_typography(fig, spec)
        >>> results[0].is_failure
        True

    Notes
    -----
        - Font size is read via :meth:`~matplotlib.text.Text.get_fontsize`,
          which returns the *effective* size in points after resolving any
          relative size strings (``"small"``, ``"large"``, etc.).
        - Tick labels are computed from the axes' locator/formatter when the
          figure is drawn; calling this check before ``fig.canvas.draw()`` may
          return empty tick-label strings, causing them to be skipped.  For
          accurate tick-label validation, call ``fig.canvas.draw()`` or use
          ``constrained_layout=True`` before validation.
    """
    min_pt: float = spec.typography.min_font_pt
    max_pt: float = spec.typography.max_font_pt

    violations: list[str] = []

    for text in _gather_text_artists(fig):
        content = text.get_text()

        # Skip artists that carry no visible content.
        if not content or not content.strip():
            continue

        font_size: float = text.get_fontsize()

        if font_size < min_pt:
            violations.append(f"{content!r}: {font_size:.1f}pt (< {min_pt}pt min)")
        elif font_size > max_pt:
            violations.append(f"{content!r}: {font_size:.1f}pt (> {max_pt}pt max)")

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
                check_name="typography.font_size",
                message=(
                    f"{len(violations)} text element(s) outside the "
                    f"{spec.metadata.name} range of {min_pt}-{max_pt}pt: "
                    f"{'; '.join(truncated)}{suffix}"
                ),
                fix_suggestion=(
                    f"Set all font sizes to {min_pt}-{max_pt}pt for "
                    f"{spec.metadata.name} compliance. Apply globally with "
                    f"mpl.rcParams['font.size'] = {min_pt}, or per-element "
                    "via the fontsize= keyword argument."
                ),
            )
        ]

    return [
        CheckResult(
            status=CheckStatus.PASS,
            check_name="typography.font_size",
            message=(
                f"All text elements are within the "
                f"{spec.metadata.name} range of {min_pt}-{max_pt}pt."
            ),
        )
    ]
