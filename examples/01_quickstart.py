"""
Quickstart: publication-ready figure in under 10 lines.

Steps:
1. Apply a journal preset with plotstyle.use() to configure fonts, sizes,
   and the default color cycle (set to the journal's recommended palette).
2. Create a correctly-sized figure with plotstyle.figure().
3. Save with plotstyle.savefig() to embed fonts and enforce the required DPI.

Note: plotstyle.use("nature") automatically sets the Okabe-Ito palette as
the default axes.prop_cycle. The ax.plot() calls below draw from it without
any color= argument needed.

Output: quickstart_nature.pdf
"""

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

# The context manager restores all modified rcParams when the block exits.
with plotstyle.use("nature") as style:
    # columns=1 → single-column width (89 mm); use columns=2 for full width
    fig, ax = style.figure(columns=1)

    x = np.linspace(0, 2 * np.pi, 200)
    # Colors come from the Okabe-Ito palette (set automatically by use("nature"))
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()

    # Enforces DPI >= 300 and embeds TrueType fonts
    style.savefig(fig, "quickstart_nature.pdf")

plt.close(fig)
