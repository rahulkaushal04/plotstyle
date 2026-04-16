"""
Multi-panel figure — 2x2 subplot grid with automatic panel labels.

Steps:
1. Apply a journal preset with plotstyle.use().
2. Create a multi-panel figure with plotstyle.subplots(); panel labels (a, b, c, d)
   are added automatically based on the journal spec.
3. Plot data in each panel using standard Matplotlib calls.
4. Save the figure.

Output: output/multi_panel_science.pdf
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

rng = np.random.default_rng(42)

# Build a 2x2 panel figure for Science
with plotstyle.use("science") as style:
    # columns=2 → full text width; panels=True adds (a), (b)... labels automatically
    fig, axes = style.subplots(nrows=2, ncols=2, columns=2)

    # Panel (a) — line plot
    x = np.linspace(0, 10, 100)
    axes[0, 0].plot(x, np.sin(x), label="sin")
    axes[0, 0].plot(x, np.cos(x), label="cos")
    axes[0, 0].set_xlabel("x")
    axes[0, 0].set_ylabel("f(x)")
    axes[0, 0].legend()

    # Panel (b) — scatter plot
    xs = rng.normal(0, 1, 60)
    ys = 0.7 * xs + rng.normal(0, 0.3, 60)
    axes[0, 1].scatter(xs, ys, s=12, alpha=0.7)
    axes[0, 1].set_xlabel("Variable X")
    axes[0, 1].set_ylabel("Variable Y")

    # Panel (c) — bar chart
    axes[1, 0].bar(["A", "B", "C", "D"], [3.2, 5.8, 4.1, 6.5])
    axes[1, 0].set_xlabel("Category")
    axes[1, 0].set_ylabel("Count")

    # Panel (d) — histogram
    axes[1, 1].hist(rng.normal(0, 1, 500), bins=25, edgecolor="white", linewidth=0.5)
    axes[1, 1].set_xlabel("Value")
    axes[1, 1].set_ylabel("Frequency")

    style.savefig(fig, OUTPUT_DIR / "multi_panel_science.pdf")

plt.close(fig)
