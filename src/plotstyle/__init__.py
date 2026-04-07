"""PlotStyle — scientific journal figure style presets for Matplotlib.

PlotStyle makes it trivial to produce publication-ready figures that conform
to the typographic and dimensional requirements of major academic journals.
A single :func:`use` call reconfigures Matplotlib's ``rcParams``; helper
functions handle figure sizing, colour palettes, accessibility previews,
validation, and submission-ready export.

Quick start
-----------
    >>> import matplotlib.pyplot as plt
    >>> import plotstyle
    >>>
    >>> plotstyle.use("nature")
    >>>
    >>> fig, ax = plotstyle.subplots(columns=1)
    >>> ax.plot([0, 1, 2], [0.2, 0.8, 0.4], color=plotstyle.palette("nature")[0])
    >>> ax.set_xlabel("Time (s)")
    >>> ax.set_ylabel("Signal (a.u.)")
    >>>
    >>> report = plotstyle.validate(fig, journal="nature")
    >>> print(report)
    >>>
    >>> plotstyle.savefig(fig, "figure1.pdf")

Package layout
--------------
The public API is re-exported here from the following sub-packages:

- :mod:`plotstyle.core.style`          — :func:`use`, :class:`JournalStyle`
- :mod:`plotstyle.core.figure`         — :func:`figure`, :func:`subplots`
- :mod:`plotstyle.core.export`         — :func:`savefig`, :func:`export_submission`
- :mod:`plotstyle.core.migrate`        — :func:`diff`, :func:`migrate`, :class:`SpecDiff`
- :mod:`plotstyle.color.palettes`      — :func:`palette`
- :mod:`plotstyle.color.accessibility` — :func:`preview_colorblind`
- :mod:`plotstyle.color.grayscale`     — :func:`preview_grayscale`
- :mod:`plotstyle.validation`          — :func:`validate`
- :mod:`plotstyle.specs`               — :data:`registry`
- :mod:`plotstyle.preview.gallery`     — :func:`gallery`
- :mod:`plotstyle.preview.print_size`  — :func:`preview_print_size`

Version
-------
The installed version is accessible as :data:`plotstyle.__version__`.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Package metadata
# ---------------------------------------------------------------------------
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

# ---------------------------------------------------------------------------
# Colour utilities
# ---------------------------------------------------------------------------
from plotstyle.color.accessibility import preview_colorblind
from plotstyle.color.grayscale import preview_grayscale
from plotstyle.color.palettes import palette

# ---------------------------------------------------------------------------
# Core — style application, figure construction, export, spec migration
# ---------------------------------------------------------------------------
from plotstyle.core.export import export_submission, savefig
from plotstyle.core.figure import figure, subplots
from plotstyle.core.migrate import SpecDiff, diff, migrate
from plotstyle.core.style import JournalStyle, use

# ---------------------------------------------------------------------------
# Seaborn integration
# ---------------------------------------------------------------------------
from plotstyle.integrations.seaborn import patch_seaborn, plotstyle_theme, unpatch_seaborn

# ---------------------------------------------------------------------------
# Preview helpers
# ---------------------------------------------------------------------------
from plotstyle.preview.gallery import gallery
from plotstyle.preview.print_size import preview_print_size

# ---------------------------------------------------------------------------
# Journal spec registry
# ---------------------------------------------------------------------------
from plotstyle.specs import registry

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
from plotstyle.validation import validate

try:
    __version__: str = _pkg_version("plotstyle")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

# ---------------------------------------------------------------------------
# Public API surface
# ---------------------------------------------------------------------------

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
