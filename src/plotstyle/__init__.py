"""PlotStyle — scientific journal figure style presets for Matplotlib.

Key entry points: ``figure`` / ``subplots`` to create journal-sized figures,
``use`` to apply a journal's rcParams preset, ``validate`` to check a figure
against submission requirements, ``palette`` for colorblind-safe colours, and
``export_submission`` / ``savefig`` to produce submission-ready files.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from plotstyle.color.accessibility import preview_colorblind
from plotstyle.color.grayscale import preview_grayscale
from plotstyle.color.palettes import apply_palette, list_palettes, palette
from plotstyle.core.export import export_submission, savefig
from plotstyle.core.figure import figure, subplots
from plotstyle.core.migrate import SpecDiff, diff, migrate
from plotstyle.core.style import JournalStyle, use
from plotstyle.engine.latex import detect_latex
from plotstyle.integrations.seaborn import patch_seaborn, plotstyle_theme, unpatch_seaborn
from plotstyle.overlays import OverlayRegistry, overlay_registry
from plotstyle.preview.gallery import gallery
from plotstyle.preview.print_size import preview_print_size
from plotstyle.specs import registry
from plotstyle.validation import validate


def list_overlays(category: str | None = None) -> list[str]:
    """List all available style overlay keys.

    Parameters
    ----------
    category : str | None
        When provided, only overlays whose ``category`` matches are returned.
        Valid values: ``"color"``, ``"context"``, ``"rendering"``,
        ``"script"``, ``"plot-type"``.

    Returns
    -------
    list[str]
        Alphabetically sorted list of overlay keys.
    """
    return overlay_registry.list_available(category=category)


try:
    __version__: str = _pkg_version("plotstyle")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

try:
    from plotstyle._compat.mpl_style import register_all_styles as _register_mpl_styles

    _register_mpl_styles()
except ImportError:
    pass
except Exception as _exc:
    import warnings as _warnings

    _warnings.warn(
        f"plotstyle: failed to register matplotlib styles: {_exc}",
        RuntimeWarning,
        stacklevel=2,
    )

__all__: list[str] = [
    "JournalStyle",
    "OverlayRegistry",
    "SpecDiff",
    "__version__",
    "apply_palette",
    "detect_latex",
    "diff",
    "export_submission",
    "figure",
    "gallery",
    "list_overlays",
    "list_palettes",
    "migrate",
    "overlay_registry",
    "palette",
    "patch_seaborn",
    "plotstyle_theme",
    "preview_colorblind",
    "preview_grayscale",
    "preview_print_size",
    "registry",
    "savefig",
    "subplots",
    "unpatch_seaborn",
    "use",
    "validate",
]
