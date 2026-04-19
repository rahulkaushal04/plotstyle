"""Warning hierarchy for PlotStyle.

All warnings emitted by PlotStyle derive from :class:`PlotStyleWarning`.
Filter the entire family with ``warnings.filterwarnings("ignore", category=PlotStyleWarning)``.
"""


class PlotStyleWarning(UserWarning):
    """Base class for all PlotStyle warnings."""


class FontFallbackWarning(PlotStyleWarning):
    """Emitted when a preferred journal font is unavailable and a fallback is used."""


class OverlaySizeWarning(PlotStyleWarning):
    """Emitted when a context overlay's figure size exceeds the journal's column width."""
