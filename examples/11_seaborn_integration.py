"""
Seaborn integration: keep PlotStyle settings intact through sns.set_theme().

Seaborn and PlotStyle both write to matplotlib.rcParams. Calling
sns.set_theme() after plotstyle.use() resets fonts, sizes, and line widths.
PlotStyle provides two ways to prevent this.

Steps:
1. Pattern 1 (recommended): pass seaborn_compatible=True to plotstyle.use().
   PlotStyle's settings are reapplied automatically after every sns.set_theme() call.
2. Pattern 2: use plotstyle_theme() for a one-shot combined setup.

Output:
    output/seaborn_scatter_nature.pdf
    output/seaborn_violin_ieee.pdf
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

rng = np.random.default_rng(42)

# ==============================================================================
# Pattern 1: seaborn_compatible=True (recommended)
# ==============================================================================
# Pass seaborn_compatible=True so that any sns.set_theme() call inside the
# block reapplies plotstyle's rcParams on top of seaborn's changes.

df = pd.DataFrame(
    {
        "x": rng.normal(0, 1, 120),
        "y": rng.normal(0, 1, 120),
        "group": np.tile(["A", "B", "C"], 40),
    }
)

with plotstyle.use("nature", seaborn_compatible=True) as style:
    sns.set_theme(style="ticks")  # plotstyle settings survive this call

    fig, ax = style.figure(columns=1)
    colors = style.palette(n=3)

    for i, (group, grp_df) in enumerate(df.groupby("group")):
        ax.scatter(grp_df["x"], grp_df["y"], color=colors[i], label=group, s=8, alpha=0.8)

    ax.set_xlabel("Variable X")
    ax.set_ylabel("Variable Y")
    ax.legend(title="Group")

    style.savefig(fig, OUTPUT_DIR / "seaborn_scatter_nature.pdf")
    plt.close(fig)

# ==============================================================================
# Pattern 2: plotstyle_theme(): one-shot combined setup
# ==============================================================================
# plotstyle_theme() applies the seaborn theme first, then overlays PlotStyle's
# journal rcParams on top. Use this when sns.set_theme() is called once upfront.

from plotstyle.integrations.seaborn import plotstyle_theme  # noqa: E402

plotstyle_theme("ieee", seaborn_style="ticks", seaborn_context="paper")

data = pd.DataFrame(
    {
        "value": rng.normal(0, 1, 200).tolist() + rng.normal(0.5, 1, 200).tolist(),
        "group": ["Method A"] * 200 + ["Method B"] * 200,
    }
)

style = plotstyle.use("ieee")
try:
    fig, ax = style.figure(columns=1)
    sns.violinplot(data=data, x="group", y="value", hue="group", ax=ax, legend=False, linewidth=0.8)
    ax.set_xlabel("Method")
    ax.set_ylabel("Score")
    style.savefig(fig, OUTPUT_DIR / "seaborn_violin_ieee.pdf")
    plt.close(fig)
finally:
    style.restore()
