"""Register plotstyle journal presets and overlays as native Matplotlib styles.

After ``import plotstyle``, all journal specs and overlays become available
through Matplotlib's built-in style API under the ``"plotstyle."`` prefix:

    plt.style.use("plotstyle.nature")
    plt.style.use(["plotstyle.nature", "plotstyle.notebook"])
    with plt.style.context("plotstyle.ieee"): ...

Discovery::

    [s for s in plt.style.available if s.startswith("plotstyle.")]

Registered styles are rcParam-only snapshots built with ``latex=False``.
For validation, export, and journal-aware figure sizing use
``plotstyle.use()`` instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plotstyle.overlays.schema import StyleOverlay
    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "build_overlay_snapshot",
    "build_style_snapshot",
    "register_all_styles",
]

_PREFIX = "plotstyle."


def build_style_snapshot(spec: JournalSpec, *, latex: bool = False) -> dict[str, Any]:
    """Return a flat rcParams dict for *spec* using ``latex=False`` by default.

    Font probing is skipped (``detect_fonts=False``) to avoid per-journal
    filesystem calls at import time; the spec's generic fallback family is
    used instead.  Warnings are suppressed for the same reason.

    Parameters
    ----------
    spec : JournalSpec
        Journal specification to convert.
    latex : bool
        Passed to :func:`~plotstyle.engine.rcparams.build_rcparams`.
        Defaults to ``False`` so registered styles have no LaTeX dependency.

    Returns
    -------
    dict[str, Any]
        Ready to inject into ``matplotlib.style.core.library``.
    """
    import warnings

    from plotstyle.engine.rcparams import build_rcparams

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return build_rcparams(spec, latex=latex, detect_fonts=False)


def build_overlay_snapshot(overlay: StyleOverlay) -> dict[str, Any]:
    """Return a flat rcParams dict for *overlay*.

    Parameters
    ----------
    overlay : StyleOverlay
        Overlay to convert.

    Returns
    -------
    dict[str, Any]
        Copy of the overlay's ``rcparams`` dict.  The special ``_palette``
        key is converted to ``axes.prop_cycle`` via cycler so the snapshot
        is valid as a Matplotlib style dict.
    """
    from cycler import cycler

    params = dict(overlay.rcparams)
    if "_palette" in params:
        colors = params.pop("_palette")
        params["axes.prop_cycle"] = cycler("color", colors)
    return params


def register_all_styles() -> None:
    """Inject all plotstyle journal presets and overlays into ``matplotlib.style.core.library``.

    Called once at ``import plotstyle``.  Re-calling is safe — existing keys
    are overwritten with identical values.  Wrapped in a broad ``try/except``
    in the caller so a matplotlib internal API change never breaks the import.
    """
    import contextlib

    import matplotlib.style.core as _mpl_style_core

    library: dict[str, Any] | None = getattr(_mpl_style_core, "library", None)
    if not isinstance(library, dict):
        return

    from plotstyle.overlays import overlay_registry
    from plotstyle.specs import registry

    for key in registry.list_available():
        with contextlib.suppress(Exception):
            library[f"{_PREFIX}{key}"] = build_style_snapshot(registry.get(key))

    for key in overlay_registry.list_available():
        with contextlib.suppress(Exception):
            library[f"{_PREFIX}{key}"] = build_overlay_snapshot(overlay_registry.get(key))

    available = getattr(_mpl_style_core, "available", None)
    if isinstance(available, list):
        available[:] = sorted(library.keys())
