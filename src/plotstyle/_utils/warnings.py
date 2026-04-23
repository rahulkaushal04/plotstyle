"""Warning hierarchy for PlotStyle.

All warnings emitted by PlotStyle derive from :class:`PlotStyleWarning`.
Filter the entire family with ``warnings.filterwarnings("ignore", category=PlotStyleWarning)``.
"""

__all__: list[str] = [
    "FontFallbackWarning",
    "OverlaySizeWarning",
    "PaletteColorblindWarning",
    "PlotStyleWarning",
    "SpecAssumptionWarning",
]


class PlotStyleWarning(UserWarning):
    """Base class for all PlotStyle warnings."""


class FontFallbackWarning(PlotStyleWarning):
    """Emitted when a preferred journal font is unavailable and a fallback is used."""


class OverlaySizeWarning(PlotStyleWarning):
    """Emitted when a context overlay's figure size exceeds the journal's column width."""


class PaletteColorblindWarning(PlotStyleWarning):
    """Emitted when a non-colorblind-safe palette is used with a colorblind-required journal."""


class SpecAssumptionWarning(PlotStyleWarning):
    """Emitted when a journal spec uses library defaults for fields not in the official guidelines.

    Check ``spec.assumed_fields`` for the full list of affected fields, or call
    ``spec.is_official(field)`` to test a specific field.
    Suppress with ``warnings.filterwarnings("ignore", category=SpecAssumptionWarning)``.
    """
