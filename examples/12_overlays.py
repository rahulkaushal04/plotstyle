"""
Overlays: additive rcParam patches that layer on top of a journal preset.

Overlays let you fine-tune a figure without touching the base journal settings.
Pass overlay names alongside a journal key in the list given to plotstyle.use().

Categories:
  color      : change the color cycle (okabe-ito, tol-bright, safe-grayscale, ...)
  context    : adjust scale for a different medium (notebook, presentation, minimal)
  rendering  : control LaTeX / grid rendering (no-latex, grid, pgf, ...)
  plot-type  : optimise for a specific chart type (bar, scatter)
  script     : font configuration for non-Latin scripts (cjk-japanese, russian, ...)

Steps:
1. Context overlay: "minimal" for clean editorial figures.
2. Context overlay: "notebook" for Jupyter / interactive use.
3. Plot-type overlay: "bar" for bar charts.
4. Color overlay: replace the default journal palette with any named palette.
5. Rendering overlay: "grid" for subtle dashed grid lines.
6. Plot-type overlay: "scatter" and why to use with_markers=True for IEEE.
7. Inspect any overlay's rcParams programmatically.
8. List all available overlays, optionally filtered by category.

Output:
    overlay_minimal.pdf
    overlay_notebook.png
    overlay_bar.pdf
    overlay_color.pdf
    overlay_grid.pdf
"""

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

rng = np.random.default_rng(0)
x = np.linspace(0, 2 * np.pi, 100)

# ==============================================================================
# 1. Context overlay: minimal style (no top/right spines, no grid)
# ==============================================================================
# "minimal" strips the axes to a clean editorial look while keeping the
# journal's fonts, sizes, and line weights.

with plotstyle.use(["nature", "minimal"]) as style:
    fig, ax = style.figure(columns=1)
    for i, color in enumerate(style.palette(n=3)):
        ax.plot(x, np.sin(x + i * 0.5), color=color, label=f"Series {i + 1}")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    style.savefig(fig, "overlay_minimal.pdf")
    plt.close(fig)

# ==============================================================================
# 2. Context overlay: notebook scale (large figure, 14pt fonts)
# ==============================================================================
# "notebook" sets figure.figsize to 8x5.5in and bumps font sizes for Jupyter.
# Use plt.subplots() (not style.figure()) so the overlay's figsize applies;
# style.figure() always uses journal column dimensions.

with plotstyle.use(["nature", "notebook"]) as style:
    # plt.subplots() respects the rcParam figure.figsize set by the overlay.
    fig, ax = plt.subplots()
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    # Save as PNG for easy embedding in notebooks
    fig.savefig("overlay_notebook.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

print("Saved overlay_notebook.png")

# ==============================================================================
# 3. Plot-type overlay: bar chart optimisation
# ==============================================================================
# "bar" removes markers and sets a narrow patch border, which is recommended
# for bar charts in most journals.

categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
values = [1.00, 1.34, 0.87, 1.56]
errors = [0.05, 0.08, 0.06, 0.09]

with plotstyle.use(["nature", "bar"]) as style:
    fig, ax = style.figure(columns=1)
    colors = style.palette(n=len(categories))
    ax.bar(categories, values, yerr=errors, color=colors, capsize=3)
    ax.set_ylabel("Relative expression")
    ax.axhline(1.0, color="black", linewidth=0.5, linestyle="--")
    style.savefig(fig, "overlay_bar.pdf")
    plt.close(fig)

# ==============================================================================
# 4. Color overlay: replace the default journal palette
# ==============================================================================
# Each journal has a default palette (set automatically by use()). A color
# overlay replaces it. Here "tol-bright" overrides IEEE's default "safe-grayscale".

with plotstyle.use(["ieee", "tol-bright"]) as style:
    fig, ax = style.figure(columns=1)
    # Colors now come from tol-bright instead of safe-grayscale
    for i in range(4):
        ax.plot(x, np.sin(x + i * 0.5), label=f"Series {i + 1}")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    style.savefig(fig, "overlay_color.pdf")
    plt.close(fig)

# ==============================================================================
# 5. Rendering overlay: "grid" for subtle major grid lines
# ==============================================================================
# "grid" enables dashed major grid lines at alpha=0.3 without changing any
# other journal settings.

with plotstyle.use(["nature", "grid"]) as style:
    fig, ax = style.figure(columns=1)
    for i in range(3):
        ax.plot(x, np.sin(x + i * 0.7), label=f"Series {i + 1}")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    style.savefig(fig, "overlay_grid.pdf")
    plt.close(fig)

# ==============================================================================
# 6. Plot-type overlay: "scatter" and the IEEE line-style warning
# ==============================================================================
# "scatter" enables markers and removes connecting lines. When combined with
# "ieee" or "safe-grayscale", PlotStyle warns that IEEE figures rely on
# line-style differentiation for print accessibility. Use palette(with_markers=True)
# to keep per-series distinction visible.

with plotstyle.use(["ieee", "scatter"]) as style:
    fig, ax = style.figure(columns=1)
    rng_local = np.random.default_rng(42)
    for i, (color, _ls, marker) in enumerate(style.palette(n=3, with_markers=True)):
        xdata = rng_local.uniform(0, 10, 20)
        ydata = rng_local.uniform(0, 5, 20)
        ax.scatter(xdata, ydata, color=color, marker=marker, label=f"Group {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    plt.close(fig)

# ==============================================================================
# 7. Inspect an overlay's rcParams programmatically
# ==============================================================================

ov = plotstyle.overlay_registry.get("grid")
print(f"\nOverlay: {ov.name}  ({ov.category})")
print(f"Description: {ov.description}")
print(f"rcParams: {ov.rcparams}")

# ==============================================================================
# 8. List all available overlays, optionally by category
# ==============================================================================

print("\nAll overlays:")
for name in plotstyle.list_overlays():
    ov = plotstyle.overlay_registry.get(name)
    print(f"  [{ov.category:10}] {name:20}  {ov.description[:50]}")

print("\nContext overlays only:")
for name in plotstyle.list_overlays(category="context"):
    print(f"  {name}")
