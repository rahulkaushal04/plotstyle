"""
Overlay-only mode: apply style overlays without committing to a journal preset.

When you pass only overlay names to plotstyle.use() -- with no journal key --
PlotStyle adjusts the requested rcParams without applying any journal-specific
fonts, sizes, or column widths. This is useful for blog posts, presentations,
exploratory notebooks, or any context where journal compliance is not required.

In overlay-only mode:
- style.figure() creates a figure using Matplotlib's default width (6.4 in).
- style.subplots() works the same way; panels= is silently ignored.
- style.savefig() delegates directly to fig.savefig().
- style.palette(), style.validate(), and style.export_submission() raise
  RuntimeError because they require a journal spec.

Output:
    output/overlay_only_notebook.png
    output/overlay_only_minimal_grid.pdf
    output/overlay_only_presentation.pdf
    output/overlay_only_subplots.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

x = np.linspace(0, 2 * np.pi, 100)

# ==============================================================================
# 1. Notebook overlay only: larger figure and bigger fonts
# ==============================================================================
# Pass a list of overlay names with no journal key. style.spec will be None.

with plotstyle.use(["notebook"]) as style:
    print(f"Journal spec:  {style.spec}")  # None
    print(f"Style repr:    {style!r}")

    # figure() falls back to Matplotlib's default width (6.4 in x columns)
    fig, ax = style.figure(columns=1)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()

    # savefig() delegates directly to fig.savefig() in overlay-only mode
    style.savefig(fig, OUTPUT_DIR / "overlay_only_notebook.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

# ==============================================================================
# 2. Combine two overlays: minimal + grid
# ==============================================================================
# Overlays stack in declaration order; later overlays win on any rcParam conflict.

with plotstyle.use(["minimal", "grid"]) as style:
    fig, ax = style.figure()
    for i in range(3):
        ax.plot(x, np.sin(x + i * 0.8), label=f"Series {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    style.savefig(fig, OUTPUT_DIR / "overlay_only_minimal_grid.pdf")
    plt.close(fig)

# ==============================================================================
# 3. Presentation overlay: large text and thick lines for slides or posters
# ==============================================================================
# Use plt.subplots() (not style.figure()) so the overlay's figsize (10 x 7 in)
# takes effect. style.figure() always uses 6.4 in in overlay-only mode.

with plotstyle.use(["presentation"]) as style:
    fig, ax = plt.subplots()  # picks up the presentation figsize (10 x 7 in)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    style.savefig(fig, OUTPUT_DIR / "overlay_only_presentation.pdf")
    plt.close(fig)

# ==============================================================================
# 4. Multi-panel figure in overlay-only mode
# ==============================================================================
# style.subplots() works in overlay-only mode. panels= is silently ignored
# because there is no journal spec to drive label formatting.

with plotstyle.use(["notebook", "grid"]) as style:
    # squeeze=True gives a 1-D array so we can index axes[0] and axes[1]
    fig, axes = style.subplots(nrows=1, ncols=2, squeeze=True)
    axes[0].plot(x, np.sin(x))
    axes[0].set_title("sin(x)")
    axes[0].set_xlabel("x")
    axes[1].plot(x, np.cos(x))
    axes[1].set_title("cos(x)")
    axes[1].set_xlabel("x")
    style.savefig(fig, OUTPUT_DIR / "overlay_only_subplots.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

# ==============================================================================
# 5. Methods that require a journal spec raise RuntimeError
# ==============================================================================

with plotstyle.use(["notebook"]) as style:
    fig, ax = style.figure()
    ax.plot(x, np.sin(x))

    try:
        style.palette()
    except RuntimeError as e:
        print(f"\npalette() in overlay-only mode:\n  {e}")

    try:
        style.validate(fig)
    except RuntimeError as e:
        print(f"\nvalidate() in overlay-only mode:\n  {e}")

    plt.close(fig)
