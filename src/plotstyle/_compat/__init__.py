"""Compatibility adapters for integrating plotstyle with third-party libraries."""

from plotstyle._compat.mpl_style import (
    build_overlay_snapshot,
    build_style_snapshot,
    register_all_styles,
)

__all__: list[str] = [
    "build_overlay_snapshot",
    "build_style_snapshot",
    "register_all_styles",
]
