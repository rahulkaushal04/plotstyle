"""Apply and restore journal style presets.

``use``
    Apply a journal preset and return a :class:`JournalStyle` handle that
    stores the prior rcParams state and exposes a context manager interface
    for automatic restoration.

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

from plotstyle.engine.rcparams import build_rcparams
from plotstyle.specs import registry

if TYPE_CHECKING:
    import types
    from pathlib import Path

    import numpy as np
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from plotstyle.color.palettes import PaletteResult
    from plotstyle.specs.schema import JournalSpec
    from plotstyle.validation.report import ValidationReport

__all__: list[str] = [
    "JournalStyle",
    "use",
]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Warning constant for when seaborn_compatible=True but seaborn is absent.
_SEABORN_MISSING_WARNING: Final[str] = (
    "seaborn is not installed — 'seaborn_compatible=True' has no effect. "
    "Install seaborn to enable compatibility mode."
)

# ---------------------------------------------------------------------------
# JournalStyle
# ---------------------------------------------------------------------------


class JournalStyle:
    """Handle returned by :func:`use` for managing applied style state.

    Stores the active journal specification and a snapshot of the rcParams
    values that were in effect before :func:`use` was called.  Supports both
    explicit restoration via :meth:`restore` and automatic restoration via the
    context manager protocol (``with`` statement).

    Attributes
    ----------
    spec : ~plotstyle.specs.schema.JournalSpec
        The journal specification that was applied to ``mpl.rcParams``.

    Notes
    -----
    The rcParams snapshot is *surgical*: only the keys that were actually
    modified by :func:`use` are stored.  Keys absent from the snapshot were
    not changed and therefore do not need to be restored.

    :meth:`restore` is idempotent — calling it more than once is safe
    because ``mpl.rcParams.update`` with identical values has no observable
    effect.

    Examples
    --------
    Delegation methods — journal key is never repeated::

        with plotstyle.use("nature") as style:
            fig, ax = style.figure(columns=1)
            colors = style.palette(n=2)
            ax.plot([1, 2, 3], color=colors[0])
            report = style.validate(fig)
            style.savefig(fig, "figure.pdf")

    Manual restore (use when the context manager is impractical)::

        style = plotstyle.use("nature")
        try:
            fig, ax = style.figure()
            ax.plot([1, 2, 3])
        finally:
            style.restore()
    """

    def __init__(
        self,
        spec: JournalSpec,
        previous_rcparams: dict[str, Any],
        *,
        seaborn_patched: bool = False,
    ) -> None:
        """Initialise the style handle.

        Parameters
        ----------
        spec : JournalSpec
            The journal specification applied to ``mpl.rcParams``.
        previous_rcparams : dict[str, Any]
            Surgical snapshot of rcParams values prior to modification.
            Contains only the keys that were changed.
        seaborn_patched : bool
            ``True`` if the seaborn compatibility patch was applied.
            When ``True``, :meth:`restore` will also reverse the patch.
        """
        self.spec: JournalSpec = spec

        # Private: callers should not depend on the snapshot structure.
        self._previous_rcparams: dict[str, Any] = previous_rcparams
        self._seaborn_patched: bool = seaborn_patched

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
        bound from this style handle.  All keyword arguments are forwarded.

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
            A ``(fig, ax)`` tuple.

        Raises
        ------
        ValueError
            If *columns* is not ``1`` or ``2``.
        """
        from plotstyle.core.figure import figure as _figure

        return _figure(self.spec.key, columns=columns, aspect=aspect)

    def palette(
        self,
        n: int = 6,
        *,
        with_markers: bool = False,
    ) -> PaletteResult:
        """Return *n* colours from this journal's recommended palette.

        Delegates to :func:`~plotstyle.color.palettes.palette` with the journal
        key bound from this style handle.

        Parameters
        ----------
        n : int
            Number of colours to return (cycles if *n* exceeds the
            palette length).
        with_markers : bool
            When ``True``, return ``(colour, marker)`` pairs
            instead of plain colour strings.

        Returns
        -------
        PaletteResult
            A list of colour strings, or a list of ``(colour, marker)``
            tuples when *with_markers* is ``True``.
        """
        from plotstyle.color.palettes import palette as _palette

        return _palette(self.spec.key, n=n, with_markers=with_markers)

    def validate(self, fig: Figure) -> ValidationReport:
        """Validate *fig* against this journal's publication specification.

        Delegates to :func:`~plotstyle.validation.validate` with the journal
        key bound from this style handle.

        Parameters
        ----------
        fig : Figure
            The Matplotlib figure to validate.

        Returns
        -------
        ValidationReport
            A :class:`~plotstyle.validation.report.ValidationReport`.
        """
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
        key bound from this style handle.

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
            spec-accurate panel label (a, b, c, …).
        aspect : float | None
            Width-to-height ratio.  Defaults to the golden ratio.
        squeeze : bool
            When ``False`` (default), *axes* is always a 2-D
            :class:`numpy.ndarray` with shape ``(nrows, ncols)``.
            When ``True``, size-1 dimensions are dropped —
            matching :func:`matplotlib.pyplot.subplots` behaviour:
            a ``(1, 1)`` grid returns a bare
            :class:`~matplotlib.axes.Axes`, a single-row or
            single-column grid returns a 1-D ``ndarray``.

        Returns
        -------
        tuple[Figure, np.ndarray | Axes]
            A ``(fig, axes)`` tuple.  The shape of *axes* depends on
            *squeeze* (see above).

        Raises
        ------
        ValueError
            If *columns* is not ``1`` or ``2``.
        """
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
        key bound from this style handle.  All extra keyword arguments are
        forwarded to :meth:`~matplotlib.figure.Figure.savefig`.

        Parameters
        ----------
        fig : Figure
            Matplotlib figure to save.
        path : str | Path
            Output file path.
        **kwargs : dict
            Forwarded to :meth:`~matplotlib.figure.Figure.savefig`.

        Raises
        ------
        OSError
            If the output path is not writable.
        """
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

        Delegates to :func:`~plotstyle.core.export.export_submission` with the
        journal key bound from this style handle.

        Parameters
        ----------
        fig : Figure
            Matplotlib figure to export.
        stem : str
            Base filename stem shared by all output files (no extension).
        formats : list[str] | None
            Explicit format list (e.g. ``["pdf", "tiff"]``).
            Overrides the journal spec's preferred formats when supplied.
        output_dir : str | Path
            Directory to write output files into.  Created if it
            does not exist.  Defaults to the current working directory.
        author_surname : str | None
            Submitting author's surname, used by journals with
            surname-prefix filename conventions (currently only IEEE).
        quiet : bool
            When ``True``, per-file compliance summaries and the final
            submission manifest are not printed.  Type 3 font warnings
            are still emitted via :mod:`warnings` regardless of this flag.

        Returns
        -------
        list[Path]
            An ordered list of :class:`~pathlib.Path` objects, one per file
            created.

        Raises
        ------
        OSError
            If *output_dir* cannot be created or any file cannot be written.
        """
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
        """Enter the context manager scope.

        Returns
        -------
        JournalStyle
            *self*, enabling ``as style`` binding in ``with`` statements.
        """
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
        return (
            f"JournalStyle("
            f"journal={self.spec.metadata.name!r}, "
            f"seaborn_patched={self._seaborn_patched!r})"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_latex(latex: bool | str) -> None:
    """Raise :exc:`ValueError` for unsupported *latex* parameter values.

    Parameters
    ----------
    latex : bool | str
        The value to validate.

    Raises
    ------
    ValueError
        If *latex* is not ``True``, ``False``, or ``"auto"``.
    """
    if latex is not True and latex is not False and latex != "auto":
        raise ValueError(
            f"'latex' must be True, False, or \"auto\", got {latex!r}. "
            'Use True to force LaTeX, False for MathText, or "auto" to '
            "enable LaTeX only when a binary is available on PATH."
        )


def _snapshot_rcparams(keys: dict[str, Any]) -> dict[str, Any]:
    """Return the current rcParams values for *keys* that are present."""
    return {key: mpl.rcParams[key] for key in keys if key in mpl.rcParams}


def _apply_seaborn_patch(params: dict[str, Any]) -> bool:
    """Apply the seaborn compatibility patch, returning ``True`` on success.

    Emits a :class:`UserWarning` and returns ``False`` if seaborn is not
    installed.

    Parameters
    ----------
    params : dict[str, Any]
        The rcParams dict applied by :func:`use`, passed to
        :func:`~plotstyle.integrations.seaborn.capture_overrides`.

    Returns
    -------
    bool
        ``True`` if the patch was applied, ``False`` otherwise.
    """
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
    journal: str,
    *,
    latex: bool | str = False,
    seaborn_compatible: bool = False,
) -> JournalStyle:
    """Apply a journal-specific Matplotlib style preset.

    Looks up the journal specification from the built-in registry, builds the
    corresponding rcParams dict, snapshots the current values for all keys
    about to be changed, and applies the new params.

    Parameters
    ----------
    journal : str
        Journal preset name (e.g. ``"nature"``, ``"ieee"``).
        Case-insensitive; matched against the TOML file stems in the
        built-in specs directory.
    latex : bool | str
        LaTeX rendering mode:

        - ``False`` (default) — use Matplotlib's built-in MathText
          renderer.
        - ``True`` — force LaTeX; raises :exc:`RuntimeError` if no
          ``latex`` binary is found on ``PATH``.
        - ``"auto"`` — enable LaTeX when a binary is available, silently
          falling back to MathText otherwise.
    seaborn_compatible : bool
        When ``True``, monkey-patches
        ``seaborn.set_theme`` so that PlotStyle's rcParams survive
        subsequent seaborn theme changes.  Emits a :class:`UserWarning`
        and continues silently if seaborn is not installed.

    Returns
    -------
    JournalStyle
        A :class:`JournalStyle` handle providing access to the applied spec
        and allowing rcParams restoration via :meth:`~JournalStyle.restore`
        or the ``with`` statement.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If *journal* does not match any built-in or registered spec.
    ValueError
        If *latex* is not ``True``, ``False``, or ``"auto"``.
    RuntimeError
        If ``latex=True`` but no ``latex`` binary is found on ``PATH``.

    Notes
    -----
    Only the rcParams keys actually modified by this call are captured in
    the restoration snapshot.  Keys absent from ``mpl.rcParams`` at call
    time are silently skipped and will not be restored.

    Examples
    --------
    Context manager (preferred — guarantees restoration)::

        import plotstyle

        with plotstyle.use("nature") as style:
            fig, ax = style.figure(columns=1)
            colors = style.palette(n=3)
            ax.plot([1, 2, 3], color=colors[0])
            report = style.validate(fig)
            style.savefig(fig, "figure.pdf")
        # mpl.rcParams are restored automatically on exit.

    One-shot application with manual restore::

        style = plotstyle.use("nature")
        try:
            fig, ax = style.figure()
            ax.plot([1, 2, 3])
        finally:
            style.restore()
    """
    _validate_latex(latex)

    spec = registry.get(journal)
    params = build_rcparams(spec, latex=latex)
    previous = _snapshot_rcparams(params)

    mpl.rcParams.update(params)

    seaborn_patched = _apply_seaborn_patch(params) if seaborn_compatible else False

    return JournalStyle(
        spec=spec,
        previous_rcparams=previous,
        seaborn_patched=seaborn_patched,
    )
