"""
Accessibility: colorblind simulation and grayscale print-safety checks.

Steps:
1. Build a figure using the Nature preset and its palette.
2. Simulate color vision deficiency (deuteranopia, protanopia, tritanopia).
3. Simulate grayscale print to check how the figure looks in black and white.
4. Check programmatically whether the palette is safe for grayscale printing.

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

# Build a figure with multiple colored series (the type where accessibility matters most)
with plotstyle.use("nature") as style:
    colors = style.palette(n=4)
    fig, ax = style.figure(columns=1)
    x = np.linspace(0, 5, 80)
    for i, c in enumerate(colors):
        ax.plot(x, np.sin(x + i), color=c, linewidth=1.5, label=f"Series {i + 1}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal")
    ax.legend()

    # Simulate color vision deficiency: original + deuteranopia + protanopia + tritanopia
    cvd_fig = plotstyle.preview_colorblind(fig)
    cvd_fig.savefig(OUTPUT_DIR / "accessibility_colorblind.png", dpi=150, bbox_inches="tight")
    plt.close(cvd_fig)

    # Simulate grayscale print, important for journals like IEEE that print in black and white
    gray_fig = plotstyle.preview_grayscale(fig)
    gray_fig.savefig(OUTPUT_DIR / "accessibility_grayscale.png", dpi=150, bbox_inches="tight")
    plt.close(gray_fig)

plt.close(fig)

# Check programmatically whether the palette is safe for grayscale printing
palette_colors = plotstyle.palette("nature", n=4)

# Threshold of 0.10 means every pair must differ by at least 10% of the luminance scale
safe = is_grayscale_safe(palette_colors, threshold=0.1)
print(f"Nature palette grayscale-safe (threshold=0.1): {safe}")

# Pairwise luminance deltas, sorted ascending so the weakest pair is first
deltas = luminance_delta(palette_colors)
print("Pairwise luminance deltas (ascending):")
for i, j, delta in deltas:
    status = "pass" if delta >= 0.1 else "fail"
    print(f"  [{status}] Color {i} vs Color {j}: delta = {delta:.3f}")
