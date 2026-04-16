"""
Color palettes — journal-specific, colorblind-safe color schemes.

Steps:
1. Get a list of hex colors with plotstyle.palette(journal, n=...).
2. Use with_markers=True to get (color, linestyle, marker) tuples for
   grayscale-safe plots (important for IEEE which prints in black-and-white).
3. Compare palettes for multiple journals side-by-side.

Output:
    output/palette_basic.pdf
    output/palette_styled_ieee.pdf
    output/palette_comparison.png
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
