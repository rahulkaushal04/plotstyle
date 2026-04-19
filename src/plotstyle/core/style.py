"""Apply and restore journal style presets.

``use``
    Apply a journal preset (and optional overlays) and return a
    :class:`JournalStyle` handle that stores the prior rcParams state and
    exposes a context manager interface for automatic restoration.

``JournalStyle``
    A lightweight handle returned by :func:`use`.  Provides delegation methods
    (:meth:`~JournalStyle.figure`, :meth:`~JournalStyle.subplots`,
    :meth:`~JournalStyle.palette`, :meth:`~JournalStyle.validate`,
    :meth:`~JournalStyle.savefig`, :meth:`~JournalStyle.export_submission`)
    so the journal key never needs to be repeated within a ``with`` block.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Final

import matplotlib as mpl

from plotstyle.engine.rcparams import apply_overlays, build_rcparams
from plotstyle.specs import SpecNotFoundError, registry

if TYPE_CHECKING:
    import types
    from pathlib import Path

    import numpy as np
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from plotstyle.color.palettes import PaletteResult
    from plotstyle.overlays.schema import StyleOverlay
    from plotstyle.specs.schema import JournalSpec
    from plotstyle.validation.report import ValidationReport

__all__: list[str] = [
    "JournalStyle",
    "use",
]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_SEABORN_MISSING_WARNING: Final[str] = (
    "seaborn is not installed — 'seaborn_compatible=True' has no effect. "
    "Install seaborn to enable compatibility mode."
)

_GOLDEN_RATIO: Final[float] = (1.0 + 5.0**0.5) / 2.0
_DEFAULT_FIGURE_WIDTH: Final[float] = 6.4

# ---------------------------------------------------------------------------
# JournalStyle
# ---------------------------------------------------------------------------


class JournalStyle:
    """Handle returned by :func:`use` for managing applied style state.

    Stores the active journal specification (if any), a snapshot of the
    rcParams values in effect before :func:`use` was called, and the list of
    overlay keys that were applied.  Supports both explicit restoration via
    :meth:`restore` and automatic restoration via the context manager protocol.

    Attributes
    ----------
    spec : ~plotstyle.specs.schema.JournalSpec | None
        The journal specification that was applied, or ``None`` when
        :func:`use` was called with overlays only (no journal key).

    Notes
    -----
    When ``spec`` is ``None`` (overlay-only mode), the methods
    :meth:`validate`, :meth:`export_submission`, and :meth:`palette` are
    unavailable and will raise :exc:`RuntimeError`.  :meth:`figure` and
    :meth:`subplots` fall back to matplotlib's default figure size.

    Examples
    --------
    Journal + overlays::

        with plotstyle.use(["nature", "notebook"]) as style:
            fig, ax = style.figure(columns=1)
            ax.plot([1, 2, 3])

    Overlay-only (no journal spec)::

        with plotstyle.use(["notebook", "grid"]) as style:
            fig, ax = style.figure()
            ax.plot([1, 2, 3])
    """

    def __init__(
        self,
        spec: JournalSpec | None,
        previous_rcparams: dict[str, Any],
        *,
        seaborn_patched: bool = False,
        overlays: list[str] | None = None,
    ) -> None:
        self.spec: JournalSpec | None = spec
        self._previous_rcparams: dict[str, Any] = previous_rcparams
        self._seaborn_patched: bool = seaborn_patched
        self._overlays: list[str] = overlays or []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def restore(self) -> None:
        """Restore Matplotlib rcParams to their pre-style state.

        Re-applies the snapshot taken by :func:`use` before the journal
        preset was activated.  If seaborn was monkey-patched during style
        application, the original ``sns.set_theme`` function is also restored.

        Notes
        -----
        Called automatically when the context manager exits.  Safe to
        call more than once; subsequent calls are no-ops.
        """
        mpl.rcParams.update(self._previous_rcparams)

        if self._seaborn_patched:
            from plotstyle.integrations.seaborn import unpatch_seaborn

            unpatch_seaborn()
            self._seaborn_patched = False

    # ------------------------------------------------------------------
    # Delegation methods
    # ------------------------------------------------------------------

    def figure(
        self,
        *,
        columns: int = 1,
        aspect: float | None = None,
    ) -> tuple[Figure, Axes]:
        """Create a figure sized to this journal's column width.

        Delegates to :func:`~plotstyle.core.figure.figure` with the journal key
        bound from this style handle.  When no journal spec is set (overlay-only
        mode), falls back to matplotlib's default figure width (6.4 in).

        Parameters
        ----------
        columns : int
            Column span: ``1`` (default) for single-column,
            ``2`` for double-column width.
        aspect : float | None
            Width-to-height ratio.  Defaults to the golden ratio.

        Returns
        -------
        tuple[Figure, Axes]
        """
        if self.spec is None:
            import matplotlib.pyplot as plt

            if columns not in (1, 2):
                raise ValueError(f"'columns' must be 1 or 2, got {columns!r}.")
            width_in = _DEFAULT_FIGURE_WIDTH * columns
            ratio = aspect if aspect is not None else _GOLDEN_RATIO
            fig, ax = plt.subplots(figsize=(width_in, width_in / ratio), constrained_layout=True)
            return fig, ax

        from plotstyle.core.figure import figure as _figure

        return _figure(self.spec.key, columns=columns, aspect=aspect)

    def palette(
        self,
        n: int | None = None,
        *,
        with_markers: bool = False,
    ) -> PaletteResult:
        """Return colours from this journal's recommended palette.

        Parameters
        ----------
        n : int | None
            Number of colours to return.  When ``None`` (the default), all
            colours in the underlying palette are returned.  When *n* exceeds
            the palette size, colours cycle from the beginning.

        Delegates to :func:`~plotstyle.color.palettes.palette` with the journal
        key bound from this style handle.

        Raises
        ------
        RuntimeError
            If no journal spec is set (overlay-only mode).
        """
        if self.spec is None:
            raise RuntimeError(
                "palette() requires a journal spec. "
                "Include a journal key in the use() call, e.g. use(['nature', 'notebook'])."
            )

        from plotstyle.color.palettes import palette as _palette

        return _palette(self.spec.key, n=n, with_markers=with_markers)

    def validate(self, fig: Figure) -> ValidationReport:
        """Validate *fig* against this journal's publication specification.

        Delegates to :func:`~plotstyle.validation.validate` with the journal
        key bound from this style handle.

        Raises
        ------
        RuntimeError
            If no journal spec is set (overlay-only mode).
        """
        if self.spec is None:
            raise RuntimeError(
                "validate() requires a journal spec. "
                "Include a journal key in the use() call, e.g. use(['nature', 'notebook'])."
            )

        from plotstyle.validation import validate as _validate

        return _validate(fig, journal=self.spec.key)

    def subplots(
        self,
        nrows: int = 1,
        ncols: int = 1,
        *,
        columns: int = 1,
        panels: bool = True,
        aspect: float | None = None,
        squeeze: bool = False,
    ) -> tuple[Figure, np.ndarray | Axes]:
        """Create a multi-panel figure sized to this journal's column width.

        Delegates to :func:`~plotstyle.core.figure.subplots` with the journal
        key bound from this style handle.  When no journal spec is set
        (overlay-only mode), falls back to matplotlib's default figure width
        and panel labels are suppressed.

        Parameters
        ----------
        nrows : int
            Number of subplot rows.
        ncols : int
            Number of subplot columns.
        columns : int
            Column span: ``1`` (default) for single-column,
            ``2`` for double-column width.
        panels : bool
            When ``True`` (default), annotates each axes with a
            spec-accurate panel label.  Silently ignored in overlay-only mode.
        aspect : float | None
            Width-to-height ratio.  Defaults to the golden ratio.
        squeeze : bool
            When ``False`` (default), *axes* is always a 2-D ndarray.
        """
        if self.spec is None:
            import matplotlib.pyplot as plt
            import numpy as np

            if columns not in (1, 2):
                raise ValueError(f"'columns' must be 1 or 2, got {columns!r}.")
            width_in = _DEFAULT_FIGURE_WIDTH * columns
            ratio = aspect if aspect is not None else _GOLDEN_RATIO
            fig, axes_raw = plt.subplots(
                nrows,
                ncols,
                figsize=(width_in, width_in / ratio),
                constrained_layout=True,
            )
            if isinstance(axes_raw, np.ndarray):
                axes_2d = axes_raw.reshape(nrows, ncols)
            else:
                axes_2d = np.atleast_2d(np.array(axes_raw))

            if squeeze:
                if nrows == 1 and ncols == 1:
                    return fig, axes_2d[0, 0]
                if nrows == 1:
                    return fig, axes_2d[0]
                if ncols == 1:
                    return fig, axes_2d[:, 0]
            return fig, axes_2d

        from plotstyle.core.figure import subplots as _subplots

        return _subplots(
            self.spec.key,
            nrows,
            ncols,
            columns=columns,
            panels=panels,
            aspect=aspect,
            squeeze=squeeze,
        )

    def savefig(
        self,
        fig: Figure,
        path: str | Path,
        **kwargs: object,
    ) -> None:
        """Save *fig* with this journal's DPI and export settings.

        Delegates to :func:`~plotstyle.core.export.savefig` with the journal
        key bound from this style handle.  When no journal spec is set
        (overlay-only mode), delegates directly to
        :meth:`~matplotlib.figure.Figure.savefig`.

        Parameters
        ----------
        fig : Figure
            Matplotlib figure to save.
        path : str | Path
            Output file path.
        **kwargs : dict
            Forwarded to :meth:`~matplotlib.figure.Figure.savefig`.
        """
        if self.spec is None:
            fig.savefig(path, **kwargs)
            return

        from plotstyle.core.export import savefig as _savefig

        _savefig(fig, path, journal=self.spec.key, **kwargs)

    def export_submission(
        self,
        fig: Figure,
        stem: str,
        *,
        formats: list[str] | None = None,
        output_dir: str | Path = ".",
        author_surname: str | None = None,
        quiet: bool = False,
    ) -> list[Path]:
        """Export *fig* in multiple formats for journal submission.

        Raises
        ------
        RuntimeError
            If no journal spec is set (overlay-only mode).
        """
        if self.spec is None:
            raise RuntimeError(
                "export_submission() requires a journal spec. "
                "Include a journal key in the use() call, e.g. use(['nature', 'notebook'])."
            )

        from plotstyle.core.export import export_submission as _export_submission

        return _export_submission(
            fig,
            stem,
            formats=formats,
            journal=self.spec.key,
            output_dir=output_dir,
            author_surname=author_surname,
            quiet=quiet,
        )

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> JournalStyle:
        """Enter the context manager scope, returning *self*."""
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: types.TracebackType | None,
    ) -> None:
        """Restore rcParams; exceptions propagate normally."""
        self.restore()

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous string representation of this handle."""
        journal = self.spec.metadata.name if self.spec is not None else None
        parts = [f"journal={journal!r}"]
        if self._overlays:
            parts.append(f"overlays={self._overlays!r}")
        parts.append(f"seaborn_patched={self._seaborn_patched!r}")
        return f"JournalStyle({', '.join(parts)})"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_latex(latex: bool | str) -> None:
    """Raise :exc:`ValueError` for unsupported *latex* parameter values."""
    if latex is not True and latex is not False and latex != "auto":
        raise ValueError(
            f"'latex' must be True, False, or \"auto\", got {latex!r}. "
            'Use True to force LaTeX, False for MathText, or "auto" to '
            "enable LaTeX only when a binary is available on PATH."
        )


def _snapshot_rcparams(keys: dict[str, Any]) -> dict[str, Any]:
    """Return the current rcParams values for *keys* that are present."""
    return {key: mpl.rcParams[key] for key in keys if key in mpl.rcParams}


def _warn_if_overlay_oversizes_journal(
    spec: JournalSpec,
    overlays: list[StyleOverlay],
) -> None:
    """Emit :class:`~plotstyle._utils.warnings.OverlaySizeWarning` when needed.

    Warns when an overlay's ``figure.figsize`` width exceeds the journal's
    double-column width.
    """
    from plotstyle._utils.warnings import OverlaySizeWarning
    from plotstyle.specs.units import Dimension

    journal_double_in = Dimension(spec.dimensions.double_column_mm, "mm").to_inches()

    for overlay in overlays:
        figsize = overlay.rcparams.get("figure.figsize")
        if figsize is None:
            continue
        overlay_width_in = figsize[0]
        if overlay_width_in > journal_double_in:
            warnings.warn(
                f"The '{overlay.key}' overlay sets figure.figsize width to "
                f"{overlay_width_in:.1f} in, which exceeds the '{spec.key}' "
                f"journal's double-column width ({journal_double_in:.2f} in). "
                "The figure will not conform to journal column dimensions.",
                OverlaySizeWarning,
                stacklevel=4,
            )


def _warn_if_grayscale_palette_on_colorblind_journal(
    spec: JournalSpec,
    overlays: list[StyleOverlay],
) -> None:
    """Emit :class:`~plotstyle._utils.warnings.PaletteColorblindWarning` when needed.

    Warns when the ``safe-grayscale`` palette overlay is combined with a
    journal that requires colorblind-safe colours.
    """
    if not spec.color.colorblind_required:
        return

    from plotstyle._utils.warnings import PaletteColorblindWarning

    for overlay in overlays:
        if overlay.key == "safe-grayscale":
            warnings.warn(
                f"The 'safe-grayscale' palette overlay is used with '{spec.key}', "
                "which requires colorblind-safe colours. "
                "Grayscale palettes may not pass colorblind accessibility checks.",
                PaletteColorblindWarning,
                stacklevel=4,
            )
            break


def _warn_if_latex_sans_on_serif_journal(
    spec: JournalSpec,
    overlays: list[StyleOverlay],
) -> None:
    """Emit :class:`~plotstyle._utils.warnings.PlotStyleWarning` when needed.

    Warns when a rendering overlay requests a sans-serif LaTeX font family
    on a journal whose typography specifies a serif font.
    """
    from plotstyle._utils.warnings import PlotStyleWarning

    for overlay in overlays:
        if overlay.rendering is None:
            continue
        if overlay.rendering.get("font_family") == "sans-serif":
            if getattr(spec.typography, "font_fallback", None) == "serif":
                warnings.warn(
                    f"The '{overlay.key}' overlay uses a sans-serif LaTeX font, "
                    f"but '{spec.key}' specifies a serif font. "
                    "The sans-serif override may not meet the journal's typography requirements.",
                    PlotStyleWarning,
                    stacklevel=4,
                )
            break


def _resolve_rendering_overlays(
    overlays: list[StyleOverlay],
    latex_kwarg: bool | str,
) -> tuple[bool | str, bool]:
    """Determine effective latex mode and PGF flag from rendering overlays.

    Kwarg wins when it is not the default ``False``; emits
    :class:`~plotstyle._utils.warnings.PlotStyleWarning` on conflict.

    Returns
    -------
    tuple[bool | str, bool]
        ``(effective_latex, pgf_mode)`` where *pgf_mode* is ``True`` when
        the PGF backend should be activated.
    """
    from plotstyle._utils.warnings import PlotStyleWarning

    rendering_overlays = [o for o in overlays if o.rendering is not None]

    if len(rendering_overlays) > 1:
        keys = [o.key for o in rendering_overlays]
        warnings.warn(
            f"Multiple rendering overlays specified: {keys!r}. Only '{keys[-1]}' takes effect.",
            PlotStyleWarning,
            stacklevel=4,
        )

    if not rendering_overlays:
        return latex_kwarg, False

    last = rendering_overlays[-1]
    overlay_latex_raw = last.rendering.get("latex", False)
    pgf_mode = overlay_latex_raw == "pgf"

    if latex_kwarg is not False:
        # Caller explicitly set latex=True or "auto" — kwarg wins.
        if overlay_latex_raw != latex_kwarg:
            warnings.warn(
                f"The '{last.key}' rendering overlay sets latex={overlay_latex_raw!r}, "
                f"but the explicit latex={latex_kwarg!r} kwarg takes precedence.",
                PlotStyleWarning,
                stacklevel=4,
            )
        return latex_kwarg, False

    # Overlay wins.
    if pgf_mode:
        return True, True
    return bool(overlay_latex_raw) if isinstance(
        overlay_latex_raw, bool
    ) else overlay_latex_raw, False


def _warn_if_scatter_loses_line_distinction(
    spec: JournalSpec | None,
    overlays: list[StyleOverlay],
) -> None:
    """Emit :class:`~plotstyle._utils.warnings.PlotStyleWarning` when needed.

    Warns when the ``scatter`` overlay removes line style differentiation that
    the IEEE journal or the ``safe-grayscale`` palette relies on for accessibility.
    """
    if not any(o.key == "scatter" for o in overlays):
        return

    from plotstyle._utils.warnings import PlotStyleWarning

    if spec is not None and spec.key == "ieee":
        warnings.warn(
            "The 'scatter' overlay sets lines.linestyle='none', removing line style "
            "differentiation. IEEE figures rely on line styles for print accessibility. "
            "Use palette(with_markers=True) to restore per-series distinction.",
            PlotStyleWarning,
            stacklevel=4,
        )
        return

    if any(o.key == "safe-grayscale" for o in overlays):
        warnings.warn(
            "The 'scatter' overlay sets lines.linestyle='none', but 'safe-grayscale' "
            "uses line style variation for accessibility. Line style differentiation will be lost.",
            PlotStyleWarning,
            stacklevel=4,
        )


def _warn_if_script_fonts_missing(overlays: list[StyleOverlay]) -> None:
    """Emit :class:`~plotstyle._utils.warnings.FontFallbackWarning` when needed.

    Warns when a script overlay is applied and none of its required fonts are
    installed on the current system.
    """
    from plotstyle._utils.warnings import FontFallbackWarning
    from plotstyle.engine.fonts import check_overlay_fonts

    for overlay in overlays:
        if overlay.category != "script" or overlay.requires is None:
            continue
        status = check_overlay_fonts(overlay)
        if status and not any(status.values()):
            required = list(status)
            warnings.warn(
                f"The '{overlay.key}' script overlay requires fonts that are not installed: "
                f"{required!r}. "
                "Non-Latin characters may not render correctly. "
                "Install one of the listed fonts for this overlay to take effect.",
                FontFallbackWarning,
                stacklevel=4,
            )


def _apply_script_latex_preambles(
    params: dict[str, Any],
    overlays: list[StyleOverlay],
) -> None:
    """Append script overlay LaTeX preamble lines to ``params`` when LaTeX is active.

    Only runs when ``params["text.usetex"]`` is ``True``.  Lines from each
    script overlay's ``[script].latex_preamble`` list are appended to any
    existing ``text.latex.preamble`` value rather than replacing it.
    """
    if not params.get("text.usetex"):
        return

    for overlay in overlays:
        if overlay.script is None:
            continue
        preamble_lines: list[str] = overlay.script.get("latex_preamble", [])
        if not preamble_lines:
            continue
        existing = params.get("text.latex.preamble", "")
        addition = "\n".join(preamble_lines)
        params["text.latex.preamble"] = f"{existing}\n{addition}".strip() if existing else addition


def _apply_seaborn_patch(params: dict[str, Any]) -> bool:
    """Apply the seaborn compatibility patch, returning ``True`` on success."""
    try:
        from plotstyle.integrations.seaborn import capture_overrides, patch_seaborn

        capture_overrides(params)
        patch_seaborn()
        return True
    except ImportError:
        warnings.warn(_SEABORN_MISSING_WARNING, stacklevel=3)
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def use(
    style: str | list[str],
    *,
    latex: bool | str = False,
    seaborn_compatible: bool = False,
) -> JournalStyle:
    """Apply a journal-specific Matplotlib style preset, with optional overlays.

    Accepts either a single journal name (backward-compatible) or a list of
    keys that may include one journal name and any number of overlay names.
    Overlays are applied in declaration order on top of the journal's base
    rcParams; the last overlay wins on any key conflict.

    Parameters
    ----------
    style : str | list[str]
        A journal preset name (e.g. ``"nature"``), or a list that may
        contain one journal name and/or any number of overlay names.

    Examples
    --------
        - ``"nature"`` — journal only (backward-compatible)
        - ``["nature", "notebook"]`` — journal + overlay
        - ``["nature", "no-latex", "grid"]`` — journal + multiple overlays
        - ``["notebook", "grid"]`` — overlays only (no journal spec)
        - ``[]`` — empty; no rcParams changed
    latex : bool | str
        LaTeX rendering mode:

        - ``False`` (default) — use Matplotlib's built-in MathText renderer.
        - ``True`` — force LaTeX; raises :exc:`RuntimeError` if no
          ``latex`` binary is found on ``PATH``.  Overrides a ``no-latex``
          overlay.
        - ``"auto"`` — enable LaTeX when a binary is available, silently
          falling back to MathText otherwise.
    seaborn_compatible : bool
        When ``True``, monkey-patches ``seaborn.set_theme`` so that
        PlotStyle's rcParams survive subsequent seaborn theme changes.

    Returns
    -------
    JournalStyle
        A handle providing access to the applied spec and allowing rcParams
        restoration via :meth:`~JournalStyle.restore` or the ``with``
        statement.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If a single journal name is given and is not found in the registry.
    plotstyle.overlays.OverlayNotFoundError
        If a list is given and an item is not found in either the journal
        registry or the overlay registry.
    ValueError
        If more than one journal key is present in *style*, or if *latex* is
        not ``True``, ``False``, or ``"auto"``.
    RuntimeError
        If ``latex=True`` but no ``latex`` binary is found on ``PATH``.

    Notes
    -----
    Only the rcParams keys actually modified by this call are captured in the
    restoration snapshot.

    Examples
    --------
    Backward-compatible single-journal call::

        with plotstyle.use("nature") as style:
            fig, ax = style.figure()

    Journal with overlays::

        with plotstyle.use(["nature", "notebook"]) as style:
            fig, ax = style.figure()

    Overlay-only (no journal spec)::

        with plotstyle.use(["notebook", "grid"]) as style:
            fig, ax = style.figure()
    """
    _validate_latex(latex)

    from plotstyle.engine.rcparams import _resolve_latex_mode
    from plotstyle.overlays import OverlayNotFoundError, overlay_registry

    is_single_string = isinstance(style, str)
    items: list[str] = [style] if is_single_string else list(style)

    journal_key: str | None = None
    resolved_overlays: list[StyleOverlay] = []
    overlay_keys: list[str] = []

    for item in items:
        if item in registry:
            if journal_key is not None:
                raise ValueError(
                    f"Only one journal preset may be specified; "
                    f"got multiple: {journal_key!r} and {item!r}."
                )
            journal_key = item
        elif item in overlay_registry:
            resolved_overlays.append(overlay_registry.get(item))
            overlay_keys.append(item.lower())
        else:
            if is_single_string:
                # Maintain backward compatibility: single string → SpecNotFoundError.
                raise SpecNotFoundError(item, available=registry.list_available())
            raise OverlayNotFoundError(
                item,
                available=overlay_registry.list_available(),
                journals=registry.list_available(),
            )

    effective_latex, pgf_mode = _resolve_rendering_overlays(resolved_overlays, latex)

    if journal_key is not None:
        spec = registry.get(journal_key)
        params = build_rcparams(spec, latex=effective_latex)
    else:
        spec = None
        use_latex = _resolve_latex_mode(effective_latex)
        params = {"text.usetex": use_latex}

    if resolved_overlays:
        params = apply_overlays(params, resolved_overlays)
        if spec is not None:
            _warn_if_overlay_oversizes_journal(spec, resolved_overlays)
            _warn_if_grayscale_palette_on_colorblind_journal(spec, resolved_overlays)
            _warn_if_latex_sans_on_serif_journal(spec, resolved_overlays)
        _warn_if_script_fonts_missing(resolved_overlays)
        _warn_if_scatter_loses_line_distinction(spec, resolved_overlays)

    # Apply font_family overrides from rendering overlays (e.g. latex-sans).
    for overlay in resolved_overlays:
        if overlay.rendering is None:
            continue
        font_family = overlay.rendering.get("font_family")
        if font_family is not None:
            from plotstyle.engine.latex import _FALLBACK_TO_PREAMBLE

            params["font.family"] = font_family
            preamble = _FALLBACK_TO_PREAMBLE.get(font_family)
            if preamble is not None:
                params["text.latex.preamble"] = preamble

    # Activate PGF backend when a pgf rendering overlay was requested.
    # Setting rcParams["backend"] after pyplot import has no effect; switch_backend is required.
    if pgf_mode:
        try:
            import matplotlib.pyplot as plt

            plt.switch_backend("pgf")
        except Exception as exc:
            from plotstyle._utils.warnings import PlotStyleWarning

            warnings.warn(
                f"Could not activate the PGF backend: {exc}. "
                "Call matplotlib.use('pgf') before importing pyplot.",
                PlotStyleWarning,
                stacklevel=2,
            )

    # latex=True kwarg always wins over any overlay that might disable it.
    if latex is True:
        params["text.usetex"] = True

    # Append script overlay LaTeX preambles after all other params are settled.
    if resolved_overlays:
        _apply_script_latex_preambles(params, resolved_overlays)

    previous = _snapshot_rcparams(params)
    mpl.rcParams.update(params)

    seaborn_patched = _apply_seaborn_patch(params) if seaborn_compatible else False

    return JournalStyle(
        spec=spec,
        previous_rcparams=previous,
        seaborn_patched=seaborn_patched,
        overlays=overlay_keys,
    )
