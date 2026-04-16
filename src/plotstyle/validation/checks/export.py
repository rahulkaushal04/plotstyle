"""Export-readiness validation checks (font embedding, DPI) (internal, not part of public API).

Registers `check_export_settings` via the `check` decorator. Validates
``pdf.fonttype``, ``ps.fonttype``, and ``savefig.dpi`` against the journal's
minimum requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl

from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

_TRUETYPE_FONTTYPE: int = 42


@check
def check_export_settings(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate ``pdf.fonttype``, ``ps.fonttype``, and ``savefig.dpi`` rcParams.

    Parameters
    ----------
    fig : Figure
        The Matplotlib figure to validate.  Not used directly; the
        check reads global ``mpl.rcParams`` instead.
    spec : JournalSpec
        The journal specification supplying the minimum DPI requirement.

    Returns
    -------
    list[CheckResult]
        A list of three `CheckResult` instances: one for ``pdf.fonttype``, one
        for ``ps.fonttype``, and one for ``savefig.dpi``.
    """
    results: list[CheckResult] = []

    pdf_fonttype: Any = mpl.rcParams.get("pdf.fonttype")

    if pdf_fonttype == _TRUETYPE_FONTTYPE:
        results.append(
            CheckResult(
                status=CheckStatus.PASS,
                check_name="export.pdf_fonttype",
                message=f"pdf.fonttype = {_TRUETYPE_FONTTYPE} (TrueType fonts will be embedded in PDF output).",
            )
        )
    else:
        results.append(
            CheckResult(
                status=CheckStatus.FAIL,
                check_name="export.pdf_fonttype",
                message=(
                    f"pdf.fonttype = {pdf_fonttype!r}; must be {_TRUETYPE_FONTTYPE} "
                    "for TrueType font embedding. Type 3 fonts are rejected by "
                    "many journal submission systems."
                ),
                fix_suggestion=(
                    f"Call plotstyle.use() to apply all required rcParams, or set "
                    f"mpl.rcParams['pdf.fonttype'] = {_TRUETYPE_FONTTYPE} manually."
                ),
            )
        )

    ps_fonttype: Any = mpl.rcParams.get("ps.fonttype")

    if ps_fonttype == _TRUETYPE_FONTTYPE:
        results.append(
            CheckResult(
                status=CheckStatus.PASS,
                check_name="export.ps_fonttype",
                message=f"ps.fonttype = {_TRUETYPE_FONTTYPE} (TrueType fonts will be embedded in PostScript output).",
            )
        )
    else:
        results.append(
            CheckResult(
                status=CheckStatus.FAIL,
                check_name="export.ps_fonttype",
                message=(
                    f"ps.fonttype = {ps_fonttype!r}; must be {_TRUETYPE_FONTTYPE} "
                    "for TrueType font embedding in PostScript/EPS output."
                ),
                fix_suggestion=(
                    f"Call plotstyle.use() to apply all required rcParams, or set "
                    f"mpl.rcParams['ps.fonttype'] = {_TRUETYPE_FONTTYPE} manually."
                ),
            )
        )

    required_dpi: float = spec.export.min_dpi
    savefig_dpi: Any = mpl.rcParams.get("savefig.dpi", "figure")

    if isinstance(savefig_dpi, (int, float)) and savefig_dpi >= required_dpi:
        results.append(
            CheckResult(
                status=CheckStatus.PASS,
                check_name="export.dpi",
                message=(
                    f"savefig.dpi = {savefig_dpi} meets the "
                    f"{spec.metadata.name} minimum of {required_dpi} DPI."
                ),
            )
        )
    elif isinstance(savefig_dpi, (int, float)):
        results.append(
            CheckResult(
                status=CheckStatus.FAIL,
                check_name="export.dpi",
                message=(
                    f"savefig.dpi = {savefig_dpi}; "
                    f"{spec.metadata.name} requires ≥ {required_dpi} DPI. "
                    "The figure will be saved at insufficient resolution."
                ),
                fix_suggestion=(
                    f"Use plotstyle.savefig() which enforces {required_dpi} DPI, "
                    f"or set mpl.rcParams['savefig.dpi'] = {int(required_dpi)}."
                ),
            )
        )
    else:
        results.append(
            CheckResult(
                status=CheckStatus.WARN,
                check_name="export.dpi",
                message=(
                    f"savefig.dpi = {savefig_dpi!r}; "
                    f"{spec.metadata.name} requires ≥ {required_dpi} DPI. "
                    "The figure may be saved at insufficient resolution."
                ),
                fix_suggestion=(
                    f"Use plotstyle.savefig() which enforces {required_dpi} DPI, "
                    f"or set mpl.rcParams['savefig.dpi'] = {int(required_dpi)}."
                ),
            )
        )

    return results
