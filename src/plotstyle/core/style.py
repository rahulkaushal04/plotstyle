"""Apply and restore journal style presets.

This module provides the primary entry point for configuring Matplotlib to
match a journal's figure-submission guidelines.

``use``
    Apply a journal preset and return a :class:`JournalStyle` handle that
    stores the prior rcParams state and exposes a context manager interface
    for automatic restoration.

``JournalStyle``
    A lightweight handle returned by :func:`use`.  Stores the active
    :class:`~plotstyle.specs.schema.JournalSpec` and a snapshot of the
    rcParams values that were in effect before the style was applied, so
    they can be restored with :meth:`~JournalStyle.restore` or via the
    ``with`` statement.

Design notes
------------
**Surgical snapshots** — only the rcParams keys that :func:`use` modifies
are captured in the restoration snapshot.  This means :meth:`~JournalStyle.restore`
will not clobber unrelated rcParam changes the caller may have made before or
during the styled block.

**Seaborn compatibility** — the optional ``seaborn_compatible`` mode
monkey-patches ``seaborn.set_theme`` so that PlotStyle's rcParams survive
subsequent calls to that function.  See :mod:`plotstyle.integrations.seaborn`
for implementation details.  The patch is reversed automatically when
:meth:`~JournalStyle.restore` is called.

**Exception safety** — when :class:`JournalStyle` is used as a context
manager, :meth:`~JournalStyle.restore` is always called in ``__exit__``
regardless of whether an exception was raised inside the ``with`` block.
Exceptions propagate normally; they are never suppressed.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, Final

import matplotlib as mpl

from plotstyle.engine.rcparams import build_rcparams
from plotstyle.specs import registry

if TYPE_CHECKING:
    import types

    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "JournalStyle",
    "use",
]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Warning message emitted when seaborn_compatible=True but seaborn is absent.
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
        spec: The :class:`~plotstyle.specs.schema.JournalSpec` that was
            applied to ``mpl.rcParams``.

    Notes
    -----
        The rcParams snapshot is *surgical*: only the keys that were actually
        modified by :func:`use` are stored.  Keys absent from the snapshot were
        not changed and therefore do not need to be restored.

        :meth:`restore` is idempotent — calling it more than once is safe
        because ``mpl.rcParams.update`` with identical values has no observable
        effect.

    Example::

        # Context manager (recommended — guarantees restoration):
        with plotstyle.use("nature") as style:
            print(style.spec.metadata.name)  # "Nature"
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])
        # mpl.rcParams are restored here automatically.

        # Manual restore (use when the context manager is impractical):
        style = plotstyle.use("nature")
        try:
            fig, ax = plt.subplots()
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

        This constructor is not part of the public API; use :func:`use` to
        create :class:`JournalStyle` instances.

        Args:
            spec: The journal specification applied to ``mpl.rcParams``.
            previous_rcparams: Surgical snapshot of rcParams values prior to
                modification.  Contains only the keys that were changed.
            seaborn_patched: ``True`` if
                :func:`~plotstyle.integrations.seaborn.patch_seaborn` was
                called during style application.  When ``True``,
                :meth:`restore` will also call
                :func:`~plotstyle.integrations.seaborn.unpatch_seaborn` to
                reverse the monkey-patch.
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
            # Deferred import: seaborn is an optional dependency and may not
            # be installed.  The patch flag is only True when the import
            # succeeded during __init__, so this call is safe.
            from plotstyle.integrations.seaborn import unpatch_seaborn

            unpatch_seaborn()
            # Reset the flag so repeated restore() calls do not re-invoke
            # unpatch_seaborn unnecessarily.
            self._seaborn_patched = False

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> JournalStyle:
        """Enter the context manager scope.

        Returns
        -------
            *self*, enabling ``as style`` binding in ``with`` statements.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit the context manager and restore rcParams.

        Calls :meth:`restore` unconditionally so the prior rcParams state is
        always recovered, even when an exception was raised inside the
        ``with`` block.  Exceptions are never suppressed — returning ``None``
        (implicitly ``False``) allows them to propagate normally.

        Args:
            exc_type: Exception class, or ``None`` if no exception occurred.
            exc_val: Exception instance, or ``None``.
            exc_tb: Traceback object, or ``None``.
        """
        self.restore()

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous string representation of this handle.

        Returns
        -------
            A string of the form
            ``JournalStyle(journal='Nature', seaborn_patched=False)``.
        """
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

    Centralising validation here keeps :func:`use` uncluttered and makes the
    error message consistently actionable regardless of where validation is
    triggered.

    Args:
        latex: The value to validate.

    Raises
    ------
        ValueError: If *latex* is not ``True``, ``False``, or ``"auto"``.
    """
    if latex is not True and latex is not False and latex != "auto":
        raise ValueError(
            f"'latex' must be True, False, or \"auto\", got {latex!r}. "
            'Use True to force LaTeX, False for MathText, or "auto" to '
            "enable LaTeX only when a binary is available on PATH."
        )


def _snapshot_rcparams(keys: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow snapshot of the current values for the given keys.

    Only keys that are already present in ``mpl.rcParams`` are included.
    Missing keys are silently skipped so the function remains forward-
    compatible with Matplotlib versions that add or remove parameters.

    Args:
        keys: A mapping whose keys are ``mpl.rcParams`` key names to capture.
            The values are ignored; only the keys are used for the lookup.

    Returns
    -------
        A ``dict`` mapping each present key to its current value in
        ``mpl.rcParams``.
    """
    return {key: mpl.rcParams[key] for key in keys if key in mpl.rcParams}


def _apply_seaborn_patch(params: dict[str, Any]) -> bool:
    """Attempt to apply the seaborn compatibility patch.

    Imports and calls :func:`~plotstyle.integrations.seaborn.patch_seaborn`
    so that PlotStyle's rcParams survive subsequent ``seaborn.set_theme``
    calls.  Emits a :class:`UserWarning` and returns ``False`` if seaborn is
    not installed.

    Args:
        params: The rcParams dict that was applied by :func:`use`.  Passed
            to :func:`~plotstyle.integrations.seaborn.capture_overrides` so
            the patch knows which keys to protect.

    Returns
    -------
        ``True`` if the patch was applied successfully, ``False`` otherwise.
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
    corresponding rcParams dict via
    :func:`~plotstyle.engine.rcparams.build_rcparams`, snapshots the current
    values for all keys about to be changed, and applies the new params.

    Args:
        journal: Journal preset name (e.g. ``"nature"``, ``"ieee"``).
            Case-insensitive; matched against the TOML file stems in the
            built-in specs directory.
        latex: LaTeX rendering mode:

            - ``False`` (default) — use Matplotlib's built-in MathText
              renderer.
            - ``True`` — force LaTeX; raises :exc:`RuntimeError` if no
              ``latex`` binary is found on ``PATH``.
            - ``"auto"`` — enable LaTeX when a binary is available, silently
              falling back to MathText otherwise.
        seaborn_compatible: When ``True``, monkey-patches
            ``seaborn.set_theme`` so that PlotStyle's rcParams survive
            subsequent seaborn theme changes.  Emits a :class:`UserWarning`
            and continues silently if seaborn is not installed.

    Returns
    -------
        A :class:`JournalStyle` handle providing access to the applied spec
        and allowing rcParams restoration via :meth:`~JournalStyle.restore`
        or the ``with`` statement.

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If *journal* does not match any
            built-in or registered spec.
        ValueError: If *latex* is not ``True``, ``False``, or ``"auto"``.
        RuntimeError: If ``latex=True`` but no ``latex`` binary is found on
            ``PATH``.

    Notes
    -----
        Only the rcParams keys actually modified by this call are captured in
        the restoration snapshot.  Keys absent from ``mpl.rcParams`` at call
        time are silently skipped and will not be restored.

    Example::

        import plotstyle
        import matplotlib.pyplot as plt

        # Context manager (preferred — guarantees restoration):
        with plotstyle.use("ieee", latex="auto") as style:
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])
            print(style.spec.metadata.name)  # "IEEE"
        # mpl.rcParams are restored automatically on exit.

        # One-shot application with manual restore:
        style = plotstyle.use("nature")
        try:
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])
        finally:
            style.restore()
    """
    # Validate *latex* before touching rcParams so any error is raised before
    # any side effects occur, leaving the global state unchanged.
    _validate_latex(latex)

    spec: JournalSpec = registry.get(journal)
    params: dict[str, Any] = build_rcparams(spec, latex=latex)

    # Snapshot only the keys that will be overwritten so restore() is surgical
    # and does not disturb rcParams that this call never touched.
    previous: dict[str, Any] = _snapshot_rcparams(params)

    mpl.rcParams.update(params)

    # Apply the seaborn compatibility patch when requested.  The result
    # (True/False) is forwarded to JournalStyle so restore() knows whether to
    # reverse the patch on exit.
    seaborn_patched: bool = _apply_seaborn_patch(params) if seaborn_compatible else False

    return JournalStyle(
        spec=spec,
        previous_rcparams=previous,
        seaborn_patched=seaborn_patched,
    )
