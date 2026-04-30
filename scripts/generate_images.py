"""Generate all static images used in README.md and the documentation.

Writes PNGs to docs/images/ and examples/output/. Run from the repository root:

    python scripts/generate_images.py

Images produced
---------------
docs/images/:
    quickstart_nature.png
    multi_panel_science.png
    palette_comparison.png
    accessibility_colorblind.png
    accessibility_grayscale.png
    gallery_nature.png
    gallery_ieee.png
    seaborn_scatter_nature.png
    overlay_bar.png

examples/output/:
    before_after.png
    quickstart_nature.png
    multi_panel_science.png
    palette_comparison.png
    palette_styled_ieee.png
    overlay_minimal.png
    overlay_notebook.png
    overlay_okabe_ito.png
    accessibility_colorblind.png
    accessibility_grayscale.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import plotstyle

ROOT = Path(__file__).resolve().parent.parent
DOCS_OUT = ROOT / "docs" / "images"
README_OUT = ROOT / "examples" / "output"

DOCS_OUT.mkdir(parents=True, exist_ok=True)
README_OUT.mkdir(parents=True, exist_ok=True)

DPI = 150
rng = np.random.default_rng(42)
x = np.linspace(0, 2 * np.pi, 200)

errors: list[str] = []


def save(name: str, fig: plt.Figure, *out_dirs: Path) -> None:
    """Save *fig* as a PNG to each directory in *out_dirs* and close it."""
    for out_dir in out_dirs:
        path = out_dir / name
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        print(f"  OK  {path.relative_to(ROOT)}")
    plt.close(fig)


def fail(name: str, exc: Exception) -> None:
    """Record a generation failure and print a summary line."""
    errors.append(f"{name}: {exc}")
    print(f"  FAIL  {name}: {exc}")


# ==============================================================================
# SHARED: quickstart_nature.png  ->  docs/images/  +  examples/output/
# ==============================================================================
try:
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        ax.plot(x, np.sin(x), label="sin(x)")
        ax.plot(x, np.cos(x), label="cos(x)")
        ax.set_xlabel("Phase (rad)")
        ax.set_ylabel("Amplitude (a.u.)")
        ax.legend()
    save("quickstart_nature.png", fig, DOCS_OUT, README_OUT)
except Exception as e:
    fail("quickstart_nature.png", e)

# ==============================================================================
# SHARED: palette_comparison.png  ->  docs/images/  +  examples/output/
# ==============================================================================
try:
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
    save("palette_comparison.png", fig, DOCS_OUT, README_OUT)
except Exception as e:
    fail("palette_comparison.png", e)

# ==============================================================================
# DOCS ONLY: multi_panel_science.png  ->  docs/images/
# Simple 2x2 sin/cos grid used in the concepts and multi-panel guide.
# ==============================================================================
try:
    x2 = np.linspace(0, 2 * np.pi, 100)
    with plotstyle.use("science") as style:
        fig, axes = style.subplots(nrows=2, ncols=2, columns=2)
        axes[0, 0].plot(x2, np.sin(x2))
        axes[0, 0].set_ylabel("sin(x)")
        axes[0, 1].plot(x2, np.cos(x2))
        axes[0, 1].set_ylabel("cos(x)")
        axes[1, 0].plot(x2, np.sin(2 * x2))
        axes[1, 0].set_ylabel("sin(2x)")
        axes[1, 1].plot(x2, np.cos(2 * x2))
        axes[1, 1].set_ylabel("cos(2x)")
        for ax in axes.flat:
            ax.set_xlabel("x")
    save("multi_panel_science.png", fig, DOCS_OUT)
except Exception as e:
    fail("multi_panel_science.png (docs)", e)

# ==============================================================================
# README ONLY: multi_panel_science.png  ->  examples/output/
# Richer 2x2 grid matching the README code snippet (line, scatter, bar, hist).
# ==============================================================================
try:
    x2 = np.linspace(0, 10, 100)
    with plotstyle.use("science") as style:
        fig, axes = style.subplots(nrows=2, ncols=2, columns=2)

        axes[0, 0].plot(x2, np.sin(x2), label="sin")
        axes[0, 0].plot(x2, np.cos(x2), label="cos")
        axes[0, 0].set_xlabel("x")
        axes[0, 0].set_ylabel("f(x)")
        axes[0, 0].legend()

        xs = rng.normal(0, 1, 60)
        ys = 0.7 * xs + rng.normal(0, 0.3, 60)
        axes[0, 1].scatter(xs, ys, s=12, alpha=0.7)
        axes[0, 1].set_xlabel("Variable X")
        axes[0, 1].set_ylabel("Variable Y")

        axes[1, 0].bar(["A", "B", "C", "D"], [3.2, 5.8, 4.1, 6.5])
        axes[1, 0].set_xlabel("Category")
        axes[1, 0].set_ylabel("Count")

        axes[1, 1].hist(rng.normal(0, 1, 500), bins=25, edgecolor="white", linewidth=0.5)
        axes[1, 1].set_xlabel("Value")
        axes[1, 1].set_ylabel("Frequency")

    save("multi_panel_science.png", fig, README_OUT)
except Exception as e:
    fail("multi_panel_science.png (readme)", e)

# ==============================================================================
# DOCS ONLY: accessibility_colorblind.png  ->  docs/images/
# Bar chart version used in the accessibility guide.
# ==============================================================================
try:
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        colors = style.palette(n=3)
        ax.bar([1, 2, 3], [4, 7, 2], color=colors)
        ax.set_ylabel("Value")
    cvd_fig = plotstyle.preview_colorblind(fig)
    plt.close(fig)
    save("accessibility_colorblind.png", cvd_fig, DOCS_OUT)
except Exception as e:
    fail("accessibility_colorblind.png (docs)", e)

# ==============================================================================
# DOCS ONLY: accessibility_grayscale.png  ->  docs/images/
# Bar chart version used in the accessibility guide.
# ==============================================================================
try:
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        colors = style.palette(n=3)
        ax.bar([1, 2, 3], [4, 7, 2], color=colors)
        ax.set_ylabel("Value")
    gray_fig = plotstyle.preview_grayscale(fig)
    plt.close(fig)
    save("accessibility_grayscale.png", gray_fig, DOCS_OUT)
except Exception as e:
    fail("accessibility_grayscale.png (docs)", e)

# ==============================================================================
# README ONLY: accessibility_colorblind.png  ->  examples/output/
# Line plot version used in the README accessibility section.
# Colors come from the automatic journal palette cycle - no explicit color= needed.
# ==============================================================================
try:
    x4 = np.linspace(0, 5, 80)
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        for i in range(4):
            ax.plot(x4, np.sin(x4 + i), linewidth=1.5, label=f"Series {i + 1}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Signal")
        ax.legend()
    cvd_fig = plotstyle.preview_colorblind(fig)
    plt.close(fig)
    save("accessibility_colorblind.png", cvd_fig, README_OUT)
except Exception as e:
    fail("accessibility_colorblind.png (readme)", e)

# ==============================================================================
# README ONLY: accessibility_grayscale.png  ->  examples/output/
# Line plot version used in the README accessibility section.
# Colors come from the automatic journal palette cycle - no explicit color= needed.
# ==============================================================================
try:
    x4 = np.linspace(0, 5, 80)
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        for i in range(4):
            ax.plot(x4, np.sin(x4 + i), linewidth=1.5, label=f"Series {i + 1}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Signal")
        ax.legend()
    gray_fig = plotstyle.preview_grayscale(fig)
    plt.close(fig)
    save("accessibility_grayscale.png", gray_fig, README_OUT)
except Exception as e:
    fail("accessibility_grayscale.png (readme)", e)

# ==============================================================================
# DOCS ONLY: gallery_nature.png  ->  docs/images/
# ==============================================================================
try:
    fig = plotstyle.gallery("nature", columns=1)
    save("gallery_nature.png", fig, DOCS_OUT)
except Exception as e:
    fail("gallery_nature.png", e)

# ==============================================================================
# DOCS ONLY: gallery_ieee.png  ->  docs/images/
# ==============================================================================
try:
    fig = plotstyle.gallery("ieee", columns=1)
    save("gallery_ieee.png", fig, DOCS_OUT)
except Exception as e:
    fail("gallery_ieee.png", e)

# ==============================================================================
# DOCS ONLY: seaborn_scatter_nature.png  ->  docs/images/
# ==============================================================================
try:
    df = pd.DataFrame(
        {
            "x": rng.normal(0, 1, 120),
            "y": rng.normal(0, 1, 120),
            "group": np.tile(["A", "B", "C"], 40),
        }
    )
    with plotstyle.use("nature", seaborn_compatible=True) as style:
        sns.set_theme(style="ticks")
        fig, ax = style.figure(columns=1)
        colors = style.palette(n=3)
        for i, (group, grp_df) in enumerate(df.groupby("group")):
            ax.scatter(
                grp_df["x"],
                grp_df["y"],
                color=colors[i],
                label=group,
                s=8,
                alpha=0.8,
            )
        ax.set_xlabel("Variable X")
        ax.set_ylabel("Variable Y")
        ax.legend(title="Group")
    save("seaborn_scatter_nature.png", fig, DOCS_OUT)
except Exception as e:
    fail("seaborn_scatter_nature.png", e)

# ==============================================================================
# DOCS ONLY: overlay_bar.png  ->  docs/images/
# ==============================================================================
try:
    categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
    values = [1.00, 1.34, 0.87, 1.56]
    errs = [0.05, 0.08, 0.06, 0.09]
    with plotstyle.use(["nature", "bar"]) as style:
        fig, ax = style.figure(columns=1)
        colors = style.palette(n=len(categories))
        ax.bar(categories, values, yerr=errs, color=colors, capsize=3)
        ax.set_ylabel("Relative expression")
        ax.axhline(1.0, color="black", linewidth=0.5, linestyle="--")
    save("overlay_bar.png", fig, DOCS_OUT)
except Exception as e:
    fail("overlay_bar.png", e)

# ==============================================================================
# README ONLY: before_after.png  ->  examples/output/
# Side-by-side: default Matplotlib (left) vs plotstyle.use("nature") (right).
#
# ax_right is created inside the plotstyle.use("nature") context so it inherits
# the nature rcParams (inward ticks, minor ticks, mirrored axes) at creation
# time. Matplotlib bakes tick settings into axes when they are created, so
# changing rcParams after the fact has no effect on already-existing axes.
# ==============================================================================
try:
    fig = plt.figure(figsize=(9, 3))
    fig.subplots_adjust(wspace=0.35)

    # Left panel: plain Matplotlib defaults. Created outside any style context
    # so it shows the default outward ticks and blue/orange colors.
    ax_left = fig.add_subplot(1, 2, 1)
    ax_left.plot(x, np.sin(x), label="sin(x)")
    ax_left.plot(x, np.cos(x), label="cos(x)")
    ax_left.set_xlabel("Phase (rad)")
    ax_left.set_ylabel("Amplitude (a.u.)")
    ax_left.set_title("Default Matplotlib", fontsize=10)
    ax_left.legend(fontsize=8)

    # Right panel: created inside the context so nature rcParams (inward ticks,
    # minor ticks, xtick.top, ytick.right) are active at axes creation time.
    # style.palette() is used instead of plotstyle.palette("nature", ...) since
    # the journal key is already bound to the style handle.
    with plotstyle.use("nature") as style:
        ax_right = fig.add_subplot(1, 2, 2)
        colors = style.palette(n=2)
        ax_right.plot(x, np.sin(x), color=colors[0], label="sin(x)")
        ax_right.plot(x, np.cos(x), color=colors[1], label="cos(x)")
        ax_right.set_xlabel("Phase (rad)")
        ax_right.set_ylabel("Amplitude (a.u.)")
        ax_right.set_title('plotstyle.use("nature")', fontsize=10)
        ax_right.legend(fontsize=8)

    save("before_after.png", fig, README_OUT)
except Exception as e:
    fail("before_after.png", e)

# ==============================================================================
# README ONLY: palette_styled_ieee.png  ->  examples/output/
# ==============================================================================
try:
    x3 = np.linspace(0, 2 * np.pi, 100)
    curves = [np.sin(x3 + i * 0.5) for i in range(4)]
    with plotstyle.use("ieee") as style:
        fig, ax = style.figure(columns=1)
        styled = style.palette(n=4, with_markers=True)
        for i, (color, ls, marker) in enumerate(styled):
            ax.plot(
                x3,
                curves[i],
                color=color,
                linestyle=ls,
                marker=marker,
                markevery=20,
                label=f"Series {i + 1}",
            )
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
    save("palette_styled_ieee.png", fig, README_OUT)
except Exception as e:
    fail("palette_styled_ieee.png", e)

# ==============================================================================
# README ONLY: overlay_minimal.png  ->  examples/output/
# ==============================================================================
try:
    with plotstyle.use(["nature", "minimal"]) as style:
        fig, ax = style.figure(columns=1)
        # Colors come from the automatic journal palette cycle.
        for i in range(3):
            ax.plot(x, np.sin(x + i * 0.5), label=f"Series {i + 1}")
        ax.set_xlabel("Phase (rad)")
        ax.set_ylabel("Amplitude")
        ax.legend()
    save("overlay_minimal.png", fig, README_OUT)
except Exception as e:
    fail("overlay_minimal.png", e)

# ==============================================================================
# README ONLY: overlay_notebook.png  ->  examples/output/
# ==============================================================================
try:
    with plotstyle.use(["nature", "notebook"]):
        fig, ax = plt.subplots()
        ax.plot(x, np.sin(x), label="sin(x)")
        ax.plot(x, np.cos(x), label="cos(x)")
        ax.set_xlabel("Phase (rad)")
        ax.set_ylabel("Amplitude")
        ax.legend()
    save("overlay_notebook.png", fig, README_OUT)
except Exception as e:
    fail("overlay_notebook.png", e)

# ==============================================================================
# README ONLY: overlay_okabe_ito.png  ->  examples/output/
# ==============================================================================
try:
    with plotstyle.use(["ieee", "okabe-ito"]) as style:
        fig, ax = style.figure(columns=1)
        for i in range(4):
            ax.plot(x, np.sin(x + i * 0.5), label=f"Series {i + 1}")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
    save("overlay_okabe_ito.png", fig, README_OUT)
except Exception as e:
    fail("overlay_okabe_ito.png", e)

# ==============================================================================
# Summary
# ==============================================================================
print()
docs_total = 9
readme_total = 10
print(f"docs/images/    : {docs_total} images")
print(f"examples/output/: {readme_total} images")
total = docs_total + readme_total - 2  # quickstart_nature and palette_comparison shared
ok = total - len(errors)
print(f"\nDone: {ok}/{total} unique renders, {len(errors)} failure(s)")
if errors:
    print("\nFailures:")
    for msg in errors:
        print(f"  - {msg}")
    sys.exit(1)
