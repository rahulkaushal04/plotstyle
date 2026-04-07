"""Seaborn compatibility layer for PlotStyle.

Provides utilities to combine seaborn themes with PlotStyle journal presets
without one clobbering the other.  Both libraries write to
``matplotlib.rcParams``; seaborn's ``set_theme`` resets everything it knows
about, which undoes PlotStyle's journal-specific overrides.  This module
resolves that conflict through two complementary strategies:

**Strategy 1 — Persistent monkey-patch** (``patch_seaborn`` / ``unpatch_seaborn``):
    Wraps ``sns.set_theme`` once so that every subsequent call automatically
    re-applies the captured PlotStyle params.  Activated by
    :func:`plotstyle.core.style.use` when ``seaborn_compatible=True``.

**Strategy 2 — One-shot helper** (``plotstyle_theme``):
    Applies a seaborn theme first, then layers PlotStyle params on top — no
    persistent patch required.  Suitable for scripts or notebooks where
    ``sns.set_theme`` is called only once.

Seaborn is imported lazily so this module can be loaded without seaborn
installed.  An :class:`ImportError` is raised only when a function that
actually requires seaborn is invoked.

Thread Safety
-------------
The two module-level globals (``_PLOTSTYLE_OVERRIDES`` and
``_ORIGINAL_SET_THEME``) track patch state across calls.  They are **not
thread-safe**; concurrent invocations of :func:`patch_seaborn` or
:func:`unpatch_seaborn`` from multiple threads may produce undefined state.

Public API
----------
- :func:`capture_overrides`
- :func:`reapply_overrides`
- :func:`patch_seaborn`
- :func:`unpatch_seaborn`
- :func:`plotstyle_theme`
"""

from __future__ import annotations

from typing import Any, ParamSpec

import matplotlib.pyplot as plt

from plotstyle.core.style import use

# Captures the variadic call signature of sns.set_theme for the transparent
# wrapper in patch_seaborn(), satisfying ANN401 without resorting to Any.
_P = ParamSpec("_P")

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

# Snapshot of rcParams that PlotStyle last applied via capture_overrides().
# Re-applied by reapply_overrides() whenever seaborn resets matplotlib's
# global rcParams.  None indicates that capture_overrides() has not yet been
# called.
_PLOTSTYLE_OVERRIDES: dict[str, Any] | None = None

# The original (unpatched) sns.set_theme callable.  Retained by patch_seaborn()
# so that unpatch_seaborn() can restore the exact original reference.  None
# indicates that the patch is not currently installed.
_ORIGINAL_SET_THEME: Any = None

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__: list[str] = [
    "capture_overrides",
    "patch_seaborn",
    "plotstyle_theme",
    "reapply_overrides",
    "unpatch_seaborn",
]


def capture_overrides(params: dict[str, Any]) -> None:
    """Store a snapshot of PlotStyle rcParams for later re-application.

    Called by :func:`plotstyle.core.style.use` when ``seaborn_compatible=True``
    is set.  The snapshot is consumed by :func:`reapply_overrides` to restore
    PlotStyle params after any subsequent ``seaborn.set_theme()`` call resets
    ``matplotlib.rcParams``.

    A shallow copy of *params* is stored, so the caller may safely mutate the
    original mapping after this function returns.

    Args:
        params: The rcParams dict that PlotStyle built and applied.  Keys must
            be valid ``matplotlib.rcParams`` parameter names; values must be
            accepted by ``matplotlib.pyplot.rcParams.update``.

    Example::

        from plotstyle.integrations.seaborn import capture_overrides

        capture_overrides({"font.size": 8, "axes.linewidth": 0.8})
    """
    global _PLOTSTYLE_OVERRIDES

    # Shallow copy is sufficient: rcParams values are scalars or short
    # sequences that matplotlib replaces (not mutates) on update.
    _PLOTSTYLE_OVERRIDES = params.copy()


def reapply_overrides() -> None:
    """Re-apply the stored PlotStyle rcParams to ``matplotlib.rcParams``.

    Intended to be called immediately after ``seaborn.set_theme()`` has reset
    matplotlib's global rcParams, restoring any journal-specific overrides that
    seaborn erased.

    This function is a no-op when:

    - :func:`capture_overrides` has not yet been called (``_PLOTSTYLE_OVERRIDES``
      is ``None``), or
    - the captured dict is empty (nothing to restore).

    Notes
    -----
    This function is injected into the seaborn call stack by
    :func:`patch_seaborn` and is not typically called directly from user code.

    Example::

        from plotstyle.integrations.seaborn import capture_overrides, reapply_overrides

        capture_overrides({"font.size": 8})
        reapply_overrides()  # matplotlib now has font.size = 8 again
    """
    # Guard against None (never captured) and {} (nothing to restore).
    # Skipping the plt.rcParams.update call entirely avoids a needless
    # matplotlib dict traversal when there is nothing to apply.
    if _PLOTSTYLE_OVERRIDES:
        plt.rcParams.update(_PLOTSTYLE_OVERRIDES)


def patch_seaborn() -> None:
    """Monkey-patch ``seaborn.set_theme`` so PlotStyle params survive its calls.

    Wraps ``sns.set_theme`` with a thin closure that calls
    :func:`reapply_overrides` immediately after seaborn has finished resetting
    ``matplotlib.rcParams``.  All subsequent calls to ``sns.set_theme(...)``
    — regardless of arguments — therefore end with the captured PlotStyle
    params in effect.

    Calling this function when the patch is already installed is a safe no-op;
    double-wrapping is explicitly prevented to ensure :func:`unpatch_seaborn`
    always restores the correct original callable.

    Raises
    ------
        ImportError: If seaborn is not installed in the current environment.

    Notes
    -----
    To remove the patch and restore the original ``sns.set_theme``, call
    :func:`unpatch_seaborn`.  The patch is also removed automatically when
    the :class:`~plotstyle.core.style.JournalStyle` context manager exits.

    Example::

        import seaborn as sns
        from plotstyle.integrations.seaborn import capture_overrides, patch_seaborn

        capture_overrides({"font.size": 8})
        patch_seaborn()

        # PlotStyle params are restored automatically after each set_theme call.
        sns.set_theme(style="ticks")
    """
    global _ORIGINAL_SET_THEME

    import seaborn as sns  # Deferred import — raises ImportError if absent.

    # Guard against double-patching: wrapping an already-wrapped callable would
    # cause unpatch_seaborn() to restore the wrapper instead of the original.
    if _ORIGINAL_SET_THEME is not None:
        return

    _ORIGINAL_SET_THEME = sns.set_theme

    # ParamSpec captures the exact call signature of the original set_theme so
    # the wrapper is transparent to type checkers without requiring Any on the
    # variadic parameters (which would violate ANN401).
    def _patched_set_theme(*args: _P.args, **kwargs: _P.kwargs) -> None:
        """Delegate to the original seaborn set_theme, then restore PlotStyle params."""
        _ORIGINAL_SET_THEME(*args, **kwargs)
        reapply_overrides()

    # Replace the module-level attribute so all callers — including those who
    # imported sns.set_theme directly before patching — see the wrapper via
    # the sns namespace.
    sns.set_theme = _patched_set_theme  # type: ignore[assignment]


def unpatch_seaborn() -> None:
    """Restore the original ``seaborn.set_theme`` callable.

    Reverses the effect of :func:`patch_seaborn`, putting ``sns.set_theme``
    back to the exact callable that was in place before patching.

    If :func:`patch_seaborn` was never called, or has already been reversed,
    this function is a safe no-op.

    Notes
    -----
    After unpatching, future calls to ``sns.set_theme(...)`` will no longer
    re-apply PlotStyle params.  To reinstate the behaviour, call
    :func:`patch_seaborn` again after a new :func:`~plotstyle.core.style.use`
    invocation.

    Example::

        from plotstyle.integrations.seaborn import patch_seaborn, unpatch_seaborn

        patch_seaborn()
        # ... use seaborn with PlotStyle compatibility ...
        unpatch_seaborn()
        # sns.set_theme is now fully restored.
    """
    global _ORIGINAL_SET_THEME

    # Nothing to restore if the patch was never installed (or was already
    # reversed by a prior call to this function).
    if _ORIGINAL_SET_THEME is None:
        return

    import seaborn as sns  # Deferred import — only reached when patched.

    sns.set_theme = _ORIGINAL_SET_THEME  # type: ignore[assignment]
    _ORIGINAL_SET_THEME = None  # Reset sentinel so re-patching is allowed.


def plotstyle_theme(
    journal: str,
    *,
    seaborn_style: str = "ticks",
    seaborn_context: str = "paper",
) -> None:
    """Apply a seaborn theme and a PlotStyle journal preset in the correct order.

    Applies the seaborn theme **first**, then overlays PlotStyle journal
    parameters on top.  This ordering guarantees that journal-specific
    typography, line weights, and figure dimensions always take precedence
    over seaborn's aesthetic defaults when the two conflict.

    This is the recommended one-shot helper for users who want seaborn
    aesthetics alongside journal-compliant styling without installing a
    persistent monkey-patch.

    Args:
        journal: Journal preset name recognised by
            :func:`~plotstyle.specs.registry.get` (e.g. ``"nature"`` or
            ``"ieee"``).
        seaborn_style: Seaborn aesthetic style forwarded to
            ``sns.set_theme(style=...)``.  Accepted values are
            ``"darkgrid"``, ``"whitegrid"``, ``"dark"``, ``"white"``, and
            ``"ticks"``.  Defaults to ``"ticks"``.
        seaborn_context: Seaborn scaling context forwarded to
            ``sns.set_theme(context=...)``.  Accepted values are
            ``"paper"``, ``"notebook"``, ``"talk"``, and ``"poster"``.
            Defaults to ``"paper"``.

    Raises
    ------
        ImportError: If seaborn is not installed in the current environment.
        ValueError: If *journal* is not a recognised PlotStyle preset (raised
            by :func:`~plotstyle.core.style.use` internally).

    Notes
    -----
    Unlike :func:`~plotstyle.core.style.use` with ``seaborn_compatible=True``,
    this helper does **not** install a persistent monkey-patch on
    ``sns.set_theme``.  It applies both themes once in the correct order.
    If PlotStyle params must survive *future* ``sns.set_theme(...)`` calls,
    use :func:`~plotstyle.core.style.use` with ``seaborn_compatible=True``
    instead.

    Example::

        import plotstyle.integrations.seaborn as ps_sns

        # Minimal usage — defaults to style="ticks", context="paper":
        ps_sns.plotstyle_theme("nature")

        # Explicit seaborn settings:
        ps_sns.plotstyle_theme(
            "ieee",
            seaborn_style="whitegrid",
            seaborn_context="paper",
        )
    """
    import seaborn as sns  # Deferred import — raises ImportError if absent.

    # Step 1: Let seaborn establish its own rcParams (axes style, font scales,
    # palette, etc.).  This intentionally resets any pre-existing params so
    # the seaborn baseline is clean before PlotStyle layers on top.
    sns.set_theme(style=seaborn_style, context=seaborn_context)

    # Step 2: Overlay journal-specific params, winning any conflicts with
    # seaborn's defaults (font sizes, line weights, figure dimensions, etc.).
    use(journal)
