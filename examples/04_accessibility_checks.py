"""
Accessibility: colorblind simulation and grayscale print-safety checks.

Steps:
1. Build a figure using the Nature preset and its palette.
2. Simulate color-vision deficiency (deuteranopia, protanopia, tritanopia).
3. Apply CVD simulation directly to an image array using simulate_cvd + CVDType.
4. Simulate grayscale print using ITU-R BT.709 luminance weights.
5. Programmatically check whether all color pairs are distinguishable in grayscale.

Output:
    output/accessibility_colorblind.png
    output/accessibility_deuteranopia.png
    output/accessibility_grayscale.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle
from plotstyle.color.accessibility import CVDType, simulate_cvd
from plotstyle.color.grayscale import is_grayscale_safe, luminance_delta

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 1. Build a figure with multiple colored data series
# ==============================================================================

with plotstyle.use("nature") as style:
    colors = style.palette(n=4)
    fig, ax = style.figure(columns=1)
    x = np.linspace(0, 5, 80)
    for i, c in enumerate(colors):
        ax.plot(x, np.sin(x + i), color=c, linewidth=1.5, label=f"Series {i + 1}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal")
    ax.legend()

    # -- 2. Colorblind simulation (high-level) -----------------------------------
    # Returns a new figure showing Original + Deuteranopia + Protanopia + Tritanopia.
    cvd_fig = plotstyle.preview_colorblind(fig)
    cvd_fig.savefig(OUTPUT_DIR / "accessibility_colorblind.png", dpi=150, bbox_inches="tight")
    plt.close(cvd_fig)

    # -- 3. Low-level CVD simulation via simulate_cvd + CVDType -----------------
    # Render the figure to an RGB array and apply a single CVD matrix directly.
    # CVDType members: DEUTERANOPIA, PROTANOPIA, TRITANOPIA.
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height(physical=True)
    rgba = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(h, w, 4)
    rgb = rgba[:, :, :3].copy()  # (H, W, 3) uint8

    deut_rgb = simulate_cvd(rgb, CVDType.DEUTERANOPIA)  # float64 in [0, 1]

    deut_fig, axes = plt.subplots(1, 2, figsize=(7, 2.5))
    axes[0].imshow(rgb)
    axes[0].set_title("Original")
    axes[0].axis("off")
    axes[1].imshow(deut_rgb)
    axes[1].set_title(f"Simulated: {CVDType.DEUTERANOPIA.value}")
    axes[1].axis("off")
    deut_fig.tight_layout()
    deut_fig.savefig(OUTPUT_DIR / "accessibility_deuteranopia.png", dpi=150, bbox_inches="tight")
    plt.close(deut_fig)

    # -- 4. Grayscale simulation -------------------------------------------------
    # Returns a new figure with the original on the left, grayscale on the right.
    gray_fig = plotstyle.preview_grayscale(fig)
    gray_fig.savefig(OUTPUT_DIR / "accessibility_grayscale.png", dpi=150, bbox_inches="tight")
    plt.close(gray_fig)

plt.close(fig)

# ==============================================================================
# 5. Programmatic grayscale safety check
# ==============================================================================

palette_colors = plotstyle.palette("nature", n=4)

# A threshold of 0.10 means every color pair must differ by at least 10% of
# the luminance scale to be distinguishable in black-and-white print.
safe = is_grayscale_safe(palette_colors, threshold=0.1)
print(f"Nature palette is grayscale-safe (threshold=0.1): {safe}")

# Pairwise luminance deltas, sorted ascending so the weakest pair is first.
deltas = luminance_delta(palette_colors)
print("Pairwise luminance deltas (ascending):")
for i, j, delta in deltas:
    print(f"  Color {i} vs Color {j}: delta = {delta:.3f}")
