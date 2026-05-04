"""
Style management: three patterns for controlling Matplotlib rcParams lifetime.

Steps:
1. Pattern 1 (recommended): Use plotstyle.use() as a context manager. rcParams
   are restored automatically when the block exits, even on exception.
2. Pattern 2: Call style.restore() manually inside a try/finally block.
3. Pattern 3: Values you set before calling use() are captured in a snapshot and
   restored on exit, so your customisations survive the styled block.

Output:
    ctx_nature.pdf
    manual_ieee.pdf
    ctx_science.pdf
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import plotstyle

x = np.linspace(0, 2 * np.pi, 100)

# ==============================================================================
# Pattern 1: Context manager (recommended)
# ==============================================================================
# The "as style" binding gives access to the active JournalSpec while inside
# the block. On exit, all plotstyle-modified rcParams are rolled back.

original_fontsize = mpl.rcParams["font.size"]

with plotstyle.use("nature") as style:
    print(f"Inside 'nature' block, journal: {style.spec.metadata.name}")
    fig, ax = style.figure(columns=1)
    ax.plot(x, np.sin(x))
    ax.set_xlabel("x")
    ax.set_ylabel("sin(x)")
    style.savefig(fig, "ctx_nature.pdf")
    plt.close(fig)

# Verify that rcParams were actually restored
print(f"Font size restored: {mpl.rcParams['font.size'] == original_fontsize}")

# ==============================================================================
# Pattern 2: Manual restore (use when a context manager is impractical)
# ==============================================================================
# Wrap in try/finally so restore() runs even on failure.

style = plotstyle.use("ieee")
try:
    fig, ax = style.figure(columns=1)
    ax.plot(x, np.cos(x))
    ax.set_xlabel("x")
    ax.set_ylabel("cos(x)")
    style.savefig(fig, "manual_ieee.pdf")
    plt.close(fig)
finally:
    style.restore()

# ==============================================================================
# Pattern 3: Pre-existing values survive the styled block
# ==============================================================================
# plotstyle snapshots whatever value a key had *before* use() was called, then
# restores it on exit.  So any value you set before the block comes back after it.

prev_linewidth = mpl.rcParams["lines.linewidth"]
mpl.rcParams["lines.linewidth"] = 3.0

with plotstyle.use("science") as style:
    fig, ax = style.figure(columns=1)
    ax.plot(x, np.tan(np.clip(x, 0.1, 3.0)))
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    style.savefig(fig, "ctx_science.pdf")
    plt.close(fig)

# plotstyle restored lines.linewidth to the value it had when use() was called (3.0)
print(f"Custom linewidth preserved: {mpl.rcParams['lines.linewidth'] == 3.0}")

# Restore to the value it had before this example ran
mpl.rcParams["lines.linewidth"] = prev_linewidth
