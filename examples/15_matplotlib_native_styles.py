"""
Matplotlib native style integration: use PlotStyle presets with plt.style.

At import time, PlotStyle registers all journal presets and overlays as native
Matplotlib styles under a "plotstyle." prefix. This lets you use Matplotlib's
built-in style API for quick exploration.

Steps:
1. Import plotstyle to trigger style registration.
2. Use plt.style.use("plotstyle.<journal>") for a persistent style change.
3. Use plt.style.context("plotstyle.<journal>") for a scoped style change.
4. Combine journal and overlay styles in a list.
5. Discover all registered plotstyle styles.

Note: Registered styles are rcParam-only snapshots built without LaTeX.
For validation, export, and journal-aware figure sizing, use plotstyle.use()
instead. The native style integration is for quick exploration only.

Output:
    output/mpl_style_ieee.pdf
    output/mpl_style_nature_context.pdf
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle  # noqa: F401 - triggers style registration

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

x = np.linspace(0, 2 * np.pi, 100)

# ==============================================================================
# 1. Discover registered plotstyle styles
# ==============================================================================

ps_styles = sorted(s for s in plt.style.available if s.startswith("plotstyle."))
print(f"Registered plotstyle styles ({len(ps_styles)}):")
for name in ps_styles:
    print(f"  {name}")

# ==============================================================================
# 2. plt.style.use: persistent style change
# ==============================================================================
# This applies the style globally until another style is applied or Matplotlib
# is reconfigured. Good for scripts that use one journal throughout.

plt.style.use("plotstyle.ieee")

fig, ax = plt.subplots()
ax.plot(x, np.sin(x), label="sin(x)")
ax.plot(x, np.cos(x), label="cos(x)")
ax.set_xlabel("Phase (rad)")
ax.set_ylabel("Amplitude")
ax.legend()
fig.savefig(OUTPUT_DIR / "mpl_style_ieee.pdf")
plt.close(fig)
print(f"\nSaved: {OUTPUT_DIR / 'mpl_style_ieee.pdf'}")

# Reset to Matplotlib defaults
plt.style.use("default")

# ==============================================================================
# 3. plt.style.context: scoped style change
# ==============================================================================
# The style is applied only within the 'with' block. Matplotlib's rcParams
# are restored when the block exits.

with plt.style.context("plotstyle.nature"):
    fig, ax = plt.subplots()
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    fig.savefig(OUTPUT_DIR / "mpl_style_nature_context.pdf")
    plt.close(fig)

print(f"Saved: {OUTPUT_DIR / 'mpl_style_nature_context.pdf'}")

# ==============================================================================
# 4. Combine journal and overlay styles
# ==============================================================================
# Pass a list to use a journal base style with one or more overlays.

with plt.style.context(["plotstyle.nature", "plotstyle.notebook"]):
    fig, ax = plt.subplots()  # uses notebook's larger figsize
    ax.plot(x, np.sin(x))
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    plt.close(fig)

print("\nNote: plt.style only applies rcParams. For journal-aware figure")
print("sizing, validation, and export, use plotstyle.use() instead.")
