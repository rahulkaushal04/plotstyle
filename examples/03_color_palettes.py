"""
Color palettes — journal-specific, colorblind-safe color schemes.

Steps:
1. Get a list of hex colors with plotstyle.palette(journal, n=...).
2. Use with_markers=True to get (color, linestyle, marker) tuples for
   grayscale-safe plots (important for IEEE which prints in black-and-white).
3. Compare palettes for multiple journals side-by-side.
4. Apply a palette to the default color cycle with plotstyle.apply_palette().
5. List all available palettes with plotstyle.list_palettes().

Output:
    output/palette_basic.pdf
    output/palette_styled_ieee.pdf
    output/palette_comparison.png
    output/palette_apply_cycle.pdf
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 1. Basic palette — list of hex color strings
# ==============================================================================

colors = plotstyle.palette("nature", n=4)
print("Nature palette (4 colors):", colors)

x = np.linspace(0, 6, 100)

with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)
    for i, color in enumerate(colors):
        ax.plot(x, np.sin(x + i * 0.5), color=color, label=f"Series {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    style.savefig(fig, OUTPUT_DIR / "palette_basic.pdf")
    plt.close(fig)

# ==============================================================================
# 2. Styled tuples — (color, linestyle, marker) for grayscale-safe line plots
# ==============================================================================

# with_markers=True is important for IEEE, which prints in grayscale.
# Each series gets a unique combination of color, linestyle, and marker.
styled = plotstyle.palette("ieee", n=4, with_markers=True)

with plotstyle.use("ieee") as style:
    fig, ax = style.figure(columns=1)
    for i, (color, ls, marker) in enumerate(styled):
        ax.plot(
            x,
            np.cos(x + i * 0.8),
            color=color,
            linestyle=ls,
            marker=marker,
            markevery=15,
            label=f"Channel {i + 1}",
        )
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (mV)")
    ax.legend()
    style.savefig(fig, OUTPUT_DIR / "palette_styled_ieee.pdf")
    plt.close(fig)

# ==============================================================================
# 3. Cross-journal palette comparison
# ==============================================================================

journals = ["nature", "science", "ieee", "acs"]
fig, axes_raw = plt.subplots(len(journals), 1, figsize=(6, 0.6 * len(journals)))
for ax, journal in zip(axes_raw, journals, strict=False):
    pal = plotstyle.palette(journal, n=8)
    for i, c in enumerate(pal):
        ax.barh(0, 1, left=i, color=c, edgecolor="none", height=0.8)
    ax.set_xlim(0, 8)
    ax.set_yticks([])
    ax.set_ylabel(journal, rotation=0, ha="right", va="center")
    ax.set_xticks([])
fig.suptitle("Journal Color Palettes")
fig.tight_layout()
fig.savefig(OUTPUT_DIR / "palette_comparison.png", dpi=150)
plt.close(fig)

# ==============================================================================
# 4. apply_palette — set the default color cycle for automatic coloring
# ==============================================================================
# apply_palette() sets axes.prop_cycle so every subsequent plot() call picks
# colors from the named palette automatically — no color= kwarg needed.
# Call it BEFORE plotting; it does not retroactively recolor existing artists.

with plotstyle.use("nature") as style:
    # squeeze=True drops the length-1 row dimension so we get a 1-D array
    fig, axes = style.subplots(nrows=1, ncols=2, columns=2, panels=False, squeeze=True)
    ax_global, ax_local = axes

    # Left panel: tol-bright cycle applied to this axes before plotting
    plotstyle.apply_palette("tol-bright", ax=ax_global)
    for i in range(4):
        ax_global.plot(x, np.sin(x + i * 0.6), label=f"S{i + 1}")
    ax_global.set_title("tol-bright cycle")
    ax_global.set_xlabel("x")
    ax_global.legend(fontsize=5)

    # Right panel: okabe-ito applied to a different single axes
    plotstyle.apply_palette("okabe-ito", ax=ax_local)
    for i in range(4):
        ax_local.plot(x, np.cos(x + i * 0.6), label=f"S{i + 1}")
    ax_local.set_title("okabe-ito cycle")
    ax_local.set_xlabel("x")
    ax_local.legend(fontsize=5)

    style.savefig(fig, OUTPUT_DIR / "palette_apply_cycle.pdf")
    plt.close(fig)

# ==============================================================================
# 5. list_palettes — discover all built-in palette names
# ==============================================================================

available = plotstyle.list_palettes()
print(f"\nAvailable palettes ({len(available)}):")
for name in available:
    print(f"  {name}")
