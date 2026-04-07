"""
Accessibility — colorblind simulation and grayscale print-safety checks.

Steps:
1. Build a figure using the Nature preset and its palette.
2. Simulate color-vision deficiency (deuteranopia, protanopia, tritanopia).
3. Simulate grayscale print using ITU-R BT.709 luminance weights.
4. Programmatically check whether all color pairs are distinguishable in grayscale.

Output:
    output/accessibility_colorblind.png
    output/accessibility_grayscale.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle
from plotstyle.color.grayscale import is_grayscale_safe, luminance_delta

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 1. Build a figure with multiple colored data series
# ==============================================================================

with plotstyle.use("nature"):
    colors = plotstyle.palette("nature", n=4)
    fig, ax = plotstyle.figure("nature", columns=1)
    x = np.linspace(0, 5, 80)
    for i, c in enumerate(colors):
        ax.plot(x, np.sin(x + i), color=c, linewidth=1.5, label=f"Series {i + 1}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal")
    ax.legend()

    # -- 2. Colorblind simulation ------------------------------------------------
    # Returns a new figure showing the original + one panel per CVD type.
    cvd_fig = plotstyle.preview_colorblind(fig)
    cvd_fig.savefig(OUTPUT_DIR / "accessibility_colorblind.png", dpi=150, bbox_inches="tight")
    plt.close(cvd_fig)

    # -- 3. Grayscale simulation -------------------------------------------------
    # Returns a new figure with the original on the left, grayscale on the right.
    gray_fig = plotstyle.preview_grayscale(fig)
    gray_fig.savefig(OUTPUT_DIR / "accessibility_grayscale.png", dpi=150, bbox_inches="tight")
    plt.close(gray_fig)

plt.close(fig)

# ==============================================================================
# 4. Programmatic grayscale safety check
# ==============================================================================

palette_colors = plotstyle.palette("nature", n=4)

# A threshold of 0.10 means every color pair must differ by at least 10% of
# the luminance scale to be distinguishable in black-and-white print.
safe = is_grayscale_safe(palette_colors, threshold=0.1)
print(f"Nature palette is grayscale-safe (threshold=0.1): {safe}")

# Pairwise luminance deltas — sorted ascending so the weakest pair is first.
deltas = luminance_delta(palette_colors)
print("Pairwise luminance deltas (ascending):")
for i, j, delta in deltas:
    print(f"  Color {i} vs Color {j}: delta = {delta:.3f}")
