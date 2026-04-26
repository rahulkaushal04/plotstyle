"""Typography validation check: font size compliance (internal, not part of public API).

Registers `check_typography` via the `check` decorator. Validates all visible
text elements in a figure against the journal's permitted font-size range.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure
    from matplotlib.text import Text

    from plotstyle.specs.schema import JournalSpec

_MAX_VIOLATION_EXAMPLES: int = 5


def _gather_text_artists(fig: Figure) -> list[Text]:
    """Collect all Text artists from a figure.

    Traverses the figure-level text objects, then for every axes collects
    axis titles, axis labels, tick labels, and legend text items.

    Parameters
    ----------
    fig : Figure
        The figure to inspect.

    Returns
    -------
    list[Text]
        Flat list of `Text` objects, including both visible and zero-length text
        elements. The caller is responsible for filtering empty strings.
    """
    texts: list[Text] = list(fig.texts)

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


@check
def check_typography(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate all visible text elements against the journal's font size range.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to validate.
    spec : JournalSpec
        The journal specification supplying min and max font size.

    Returns
    -------
    list[CheckResult]
        A single-element list with a ``PASS`` result when all text is
        within range, or a ``FAIL`` result listing violating elements.
    """
    min_pt: float = spec.typography.min_font_pt
    max_pt: float = spec.typography.max_font_pt

    violations: list[str] = []

    for text in _gather_text_artists(fig):
        content = text.get_text()

        if not content or not content.strip():
            continue

        font_size: float = text.get_fontsize()

        if font_size < min_pt:
            violations.append(f"{content!r}: {font_size:.1f}pt (< {min_pt}pt min)")
        elif font_size > max_pt:
            violations.append(f"{content!r}: {font_size:.1f}pt (> {max_pt}pt max)")

    font_size_assumed = (
        "typography.min_font_pt" in spec.assumed_fields
        or "typography.max_font_pt" in spec.assumed_fields
    )

    if violations:
        truncated = violations[:_MAX_VIOLATION_EXAMPLES]
        suffix = (
            f" … and {len(violations) - _MAX_VIOLATION_EXAMPLES} more."
            if len(violations) > _MAX_VIOLATION_EXAMPLES
            else ""
        )
        if font_size_assumed:
            message = (
                f"{len(violations)} text element(s) outside the library-default "
                f"range of {min_pt}-{max_pt}pt "
                f"({spec.metadata.name} does not define official font size limits): "
                f"{'; '.join(truncated)}{suffix}"
            )
            fix = (
                f"Consider keeping font sizes within {min_pt}-{max_pt}pt as a "
                f"general guideline. Check {spec.metadata.source_url} for any "
                f"official {spec.metadata.name} typography requirements."
            )
        else:
            message = (
                f"{len(violations)} text element(s) outside the "
                f"{spec.metadata.name} range of {min_pt}-{max_pt}pt: "
                f"{'; '.join(truncated)}{suffix}"
            )
            fix = (
                f"Set all font sizes to {min_pt}-{max_pt}pt for "
                f"{spec.metadata.name} compliance. Apply globally with "
                f"mpl.rcParams['font.size'] = {min_pt}, or per-element "
                "via the fontsize= keyword argument."
            )
        return [
            CheckResult(
                status=CheckStatus.WARN if font_size_assumed else CheckStatus.FAIL,
                check_name="typography.font_size",
                message=message,
                fix_suggestion=fix,
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
