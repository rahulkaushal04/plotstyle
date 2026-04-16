"""Seaborn compatibility layer for PlotStyle.

Wraps ``sns.set_theme`` to re-apply PlotStyle journal params after seaborn
resets ``matplotlib.rcParams``.  Seaborn is imported lazily.
"""

from __future__ import annotations

from typing import Any, ParamSpec

import matplotlib.pyplot as plt

from plotstyle.core.style import use

_P = ParamSpec("_P")

_PLOTSTYLE_OVERRIDES: dict[str, Any] | None = None
_ORIGINAL_SET_THEME: Any = None

__all__: list[str] = [
    "capture_overrides",
    "patch_seaborn",
    "plotstyle_theme",
    "reapply_overrides",
    "unpatch_seaborn",
]


def capture_overrides(params: dict[str, Any]) -> None:
    """Store a shallow copy of *params* for later re-application by :func:`reapply_overrides`.

    Parameters
    ----------
    params : dict[str, Any]
        The rcParams dict to re-apply after any ``seaborn.set_theme`` call.
    """
    global _PLOTSTYLE_OVERRIDES

    _PLOTSTYLE_OVERRIDES = params.copy()


def reapply_overrides() -> None:
    """Re-apply the stored PlotStyle rcParams; no-op if none were captured."""
    if _PLOTSTYLE_OVERRIDES:
        plt.rcParams.update(_PLOTSTYLE_OVERRIDES)


def patch_seaborn() -> None:
    """Wrap ``sns.set_theme`` so PlotStyle params are re-applied after each call.

    No-op if the patch is already installed.

    Raises
    ------
    ImportError
        If seaborn is not installed.
    """
    global _ORIGINAL_SET_THEME

    import seaborn as sns

    if _ORIGINAL_SET_THEME is not None:
        return

    _ORIGINAL_SET_THEME = sns.set_theme

    def _patched_set_theme(*args: _P.args, **kwargs: _P.kwargs) -> None:
        _ORIGINAL_SET_THEME(*args, **kwargs)
        reapply_overrides()

    sns.set_theme = _patched_set_theme  # type: ignore[assignment]


def unpatch_seaborn() -> None:
    """Restore the original ``sns.set_theme``; no-op if not patched."""
    global _ORIGINAL_SET_THEME

    if _ORIGINAL_SET_THEME is None:
        return

    import seaborn as sns

    sns.set_theme = _ORIGINAL_SET_THEME  # type: ignore[assignment]
    _ORIGINAL_SET_THEME = None


def plotstyle_theme(
    journal: str,
    *,
    seaborn_style: str = "ticks",
    seaborn_context: str = "paper",
) -> None:
    """Apply a seaborn theme then overlay *journal* params on top.

    One-shot alternative to :func:`patch_seaborn`; does not install a
    persistent monkey-patch.

    Parameters
    ----------
    journal : str
        Journal preset name (e.g. ``"nature"``).
    seaborn_style : str
        Forwarded to ``sns.set_theme(style=...)``.
    seaborn_context : str
        Forwarded to ``sns.set_theme(context=...)``.

    Raises
    ------
    ImportError
        If seaborn is not installed.
    """
    import seaborn as sns

    sns.set_theme(style=seaborn_style, context=seaborn_context)
    use(journal)
