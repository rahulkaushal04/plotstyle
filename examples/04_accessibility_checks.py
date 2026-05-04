"""
Accessibility: colorblind simulation and grayscale print-safety checks.

Steps:
1. Build a figure using the Nature preset and its palette.
2. Simulate color vision deficiency (deuteranopia, protanopia, tritanopia).
3. Simulate grayscale print to check how the figure looks in black and white.

For programmatic luminance analysis (is_grayscale_safe, luminance_delta),
see 17_grayscale_safety.py.

Output:
    accessibility_colorblind.png
    accessibility_grayscale.png
"""

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

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
    cvd_fig.savefig("accessibility_colorblind.png", dpi=150, bbox_inches="tight")
    plt.close(cvd_fig)

    # Simulate grayscale print, important for journals like IEEE that print in black and white
    gray_fig = plotstyle.preview_grayscale(fig)
    gray_fig.savefig("accessibility_grayscale.png", dpi=150, bbox_inches="tight")
    plt.close(gray_fig)

plt.close(fig)
