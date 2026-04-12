"""Export-readiness validation checks.

This module registers :func:`check_export_settings`, which verifies that
Matplotlib's global ``rcParams`` are configured for publication-quality output.

Checks performed
----------------
1. **PDF font embedding** (``pdf.fonttype``) — must be ``42`` (TrueType
   embedding).  Setting ``3`` embeds fonts as Type 3 outlines, which many
   journal submission systems reject.
2. **PostScript font embedding** (``ps.fonttype``) — same requirement as PDF.
3. **Save DPI** (``savefig.dpi``) — must be at least the minimum DPI
   specified in the journal's export spec.  A value of ``"figure"`` (the
   Matplotlib default) is treated as ``WARN`` because the resolution depends
   on the figure's screen DPI setting, which is typically 72-100 DPI — below
   the 300+ DPI required for print.

Why rcParams and not Figure properties?
----------------------------------------
Font embedding and output DPI are controlled globally via ``rcParams`` in
Matplotlib, not per-figure.  Checking them here ensures that the entire
export pipeline is configured correctly, not just the figure layout.

Example
-------
    >>> from plotstyle.validation.checks.export import check_export_settings
    >>> results = check_export_settings(fig, spec)
    >>> [r.check_name for r in results]
    ['export.pdf_fonttype', 'export.ps_fonttype', 'export.dpi']
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl

from plotstyle.validation.checks._base import check
from plotstyle.validation.report import CheckResult, CheckStatus

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# TrueType font embedding value for pdf.fonttype and ps.fonttype.
# Type 42 embeds complete TrueType outlines; Type 3 embeds bitmaps/outlines
# that many PDF pre-flight tools and journal submission systems reject.
_TRUETYPE_FONTTYPE: int = 42


# ---------------------------------------------------------------------------
# Registered check
# ---------------------------------------------------------------------------


@check
def check_export_settings(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Validate Matplotlib export rcParams against journal requirements.

    Inspects three global ``rcParams`` that control the quality and
    compatibility of saved figures:

    - ``pdf.fonttype`` — must be :data:`_TRUETYPE_FONTTYPE` (42).
    - ``ps.fonttype``  — must be :data:`_TRUETYPE_FONTTYPE` (42).
    - ``savefig.dpi``  — must be a numeric value ≥ ``spec.export.min_dpi``.

    Args:
        fig: The :class:`~matplotlib.figure.Figure` being validated.  Not used
            by this check (export settings are global), but required by the
            :data:`~plotstyle.validation.checks._base.CheckFunc` interface.
        spec: Journal specification providing ``export.min_dpi`` and
            ``metadata.name`` for error messages.

    Returns
    -------
        A list of exactly three :class:`~plotstyle.validation.report.CheckResult`
        objects in the order: ``pdf_fonttype``, ``ps_fonttype``, ``dpi``.

    Example:
        >>> import matplotlib as mpl
        >>> mpl.rcParams["pdf.fonttype"] = 42
        >>> mpl.rcParams["ps.fonttype"] = 42
        >>> mpl.rcParams["savefig.dpi"] = 300
        >>> results = check_export_settings(fig, spec)
        >>> all(r.status.value == "PASS" for r in results)
        True

    Notes
    -----
        - ``fig`` is explicitly discarded (``_ = fig``) to make it clear this
          is intentional rather than an oversight.  The variable binding is
          kept to satisfy the :data:`~plotstyle.validation.checks._base.CheckFunc`
          interface contract.
        - A ``savefig.dpi`` value of ``"figure"`` — Matplotlib's default —
          produces a ``WARN`` rather than a ``FAIL`` because the actual DPI
          is not deterministic at validation time; it depends on the screen or
          backend DPI when :meth:`~matplotlib.figure.Figure.savefig` is called.
    """
    # `fig` is intentionally unused; this check inspects global rcParams only.
    _ = fig

    results: list[CheckResult] = []

    # ------------------------------------------------------------------
    # 1. PDF font embedding
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 2. PostScript font embedding
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 3. Save DPI
    # ------------------------------------------------------------------
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
        # Numeric but below the journal minimum — provably insufficient DPI.
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
        # A non-numeric value (e.g., "figure") is a warning rather than a
        # hard failure because the actual DPI is resolved at save time and
        # may be overridden by an explicit dpi= kwarg in savefig().
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
