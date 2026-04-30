"""Generate all static images used in the PlotStyle documentation.

Writes PNGs directly to docs/images/. Run from the repository root:

    python scripts/generate_docs_images.py

Images produced
---------------
    docs/images/quickstart_nature.png
    docs/images/multi_panel_science.png
    docs/images/palette_comparison.png
    docs/images/accessibility_colorblind.png
    docs/images/accessibility_grayscale.png
    docs/images/gallery_nature.png
    docs/images/gallery_ieee.png
    docs/images/seaborn_scatter_nature.png
    docs/images/overlay_bar.png
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

OUT = Path(__file__).resolve().parent.parent / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

DPI = 150
rng = np.random.default_rng(42)

errors: list[str] = []


def save(name: str, fig: plt.Figure) -> None:
    """Save *fig* as a PNG to the docs images directory and close it."""
    path = OUT / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ {path.relative_to(Path.cwd())}")


def fail(name: str, exc: Exception) -> None:
    """Record a generation failure for *name* and print a summary line."""
    errors.append(f"{name}: {exc}")
    print(f"  ✗ {name}: {exc}")


# ==============================================================================
# 1. quickstart_nature.png
# ==============================================================================
try:
    x = np.linspace(0, 2 * np.pi, 200)
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        ax.plot(x, np.sin(x), label="sin(x)")
        ax.plot(x, np.cos(x), label="cos(x)")
        ax.set_xlabel("Phase (rad)")
        ax.set_ylabel("Amplitude (a.u.)")
        ax.legend()
    save("quickstart_nature.png", fig)
except Exception as e:
    fail("quickstart_nature.png", e)

# ==============================================================================
# 2. multi_panel_science.png
# ==============================================================================
try:
    x = np.linspace(0, 2 * np.pi, 100)
    with plotstyle.use("science") as style:
        fig, axes = style.subplots(nrows=2, ncols=2, columns=2)
        axes[0, 0].plot(x, np.sin(x))
        axes[0, 0].set_ylabel("sin(x)")
        axes[0, 1].plot(x, np.cos(x))
        axes[0, 1].set_ylabel("cos(x)")
        axes[1, 0].plot(x, np.sin(2 * x))
        axes[1, 0].set_ylabel("sin(2x)")
        axes[1, 1].plot(x, np.cos(2 * x))
        axes[1, 1].set_ylabel("cos(2x)")
        for ax in axes.flat:
            ax.set_xlabel("x")
    save("multi_panel_science.png", fig)
except Exception as e:
    fail("multi_panel_science.png", e)

# ==============================================================================
# 3. palette_comparison.png
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
    save("palette_comparison.png", fig)
except Exception as e:
    fail("palette_comparison.png", e)

# ==============================================================================
# 4. accessibility_colorblind.png
# ==============================================================================
try:
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        colors = style.palette(n=3)
        ax.bar([1, 2, 3], [4, 7, 2], color=colors)
        ax.set_ylabel("Value")
    cvd_fig = plotstyle.preview_colorblind(fig)
    plt.close(fig)
    save("accessibility_colorblind.png", cvd_fig)
except Exception as e:
    fail("accessibility_colorblind.png", e)

# ==============================================================================
# 5. accessibility_grayscale.png
# ==============================================================================
try:
    with plotstyle.use("nature") as style:
        fig, ax = style.figure(columns=1)
        colors = style.palette(n=3)
        ax.bar([1, 2, 3], [4, 7, 2], color=colors)
        ax.set_ylabel("Value")
    gray_fig = plotstyle.preview_grayscale(fig)
    plt.close(fig)
    save("accessibility_grayscale.png", gray_fig)
except Exception as e:
    fail("accessibility_grayscale.png", e)

# ==============================================================================
# 6. gallery_nature.png
# ==============================================================================
try:
    fig = plotstyle.gallery("nature", columns=1)
    save("gallery_nature.png", fig)
except Exception as e:
    fail("gallery_nature.png", e)

# ==============================================================================
# 7. gallery_ieee.png
# ==============================================================================
try:
    fig = plotstyle.gallery("ieee", columns=1)
    save("gallery_ieee.png", fig)
except Exception as e:
    fail("gallery_ieee.png", e)

# ==============================================================================
# 8. seaborn_scatter_nature.png
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
            ax.scatter(grp_df["x"], grp_df["y"], color=colors[i], label=group, s=8, alpha=0.8)
        ax.set_xlabel("Variable X")
        ax.set_ylabel("Variable Y")
        ax.legend(title="Group")
    save("seaborn_scatter_nature.png", fig)
except Exception as e:
    fail("seaborn_scatter_nature.png", e)

# ==============================================================================
# 9. overlay_bar.png
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
    save("overlay_bar.png", fig)
except Exception as e:
    fail("overlay_bar.png", e)

# ==============================================================================
# Summary
# ==============================================================================
print()
total = 9
ok = total - len(errors)
print(f"Done: {ok}/{total} images generated in {OUT}")
if errors:
    print(f"\n{len(errors)} failure(s):")
    for msg in errors:
        print(f"  • {msg}")
    sys.exit(1)
