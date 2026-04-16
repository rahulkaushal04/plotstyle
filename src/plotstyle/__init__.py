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
from plotstyle.color.palettes import palette
from plotstyle.core.export import export_submission, savefig
from plotstyle.core.figure import figure, subplots
from plotstyle.core.migrate import SpecDiff, diff, migrate
from plotstyle.core.style import JournalStyle, use
from plotstyle.integrations.seaborn import patch_seaborn, plotstyle_theme, unpatch_seaborn
from plotstyle.preview.gallery import gallery
from plotstyle.preview.print_size import preview_print_size
from plotstyle.specs import registry
from plotstyle.validation import validate

try:
    __version__: str = _pkg_version("plotstyle")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__: list[str] = [
    "JournalStyle",
    "SpecDiff",
    "__version__",
    "diff",
    "export_submission",
    "figure",
    "gallery",
    "migrate",
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
