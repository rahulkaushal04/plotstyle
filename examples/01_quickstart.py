"""
Quickstart — publication-ready figure in under 10 lines.

Steps:
1. Apply a journal preset with plotstyle.use() to configure fonts and sizes.
2. Create a correctly-sized figure with plotstyle.figure().
3. Save with plotstyle.savefig() to embed fonts and enforce the required DPI.

Output: output/quickstart_nature.pdf
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# The context manager restores all modified rcParams when the block exits.
with plotstyle.use("nature") as style:
    # columns=1 → single-column width (89 mm); use columns=2 for full width
    fig, ax = style.figure(columns=1)

    x = np.linspace(0, 2 * np.pi, 200)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()

    # Enforces DPI >= 300 and embeds TrueType fonts
    style.savefig(fig, OUTPUT_DIR / "quickstart_nature.pdf")

plt.close(fig)
