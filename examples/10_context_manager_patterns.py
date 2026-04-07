"""
Style management — three patterns for controlling Matplotlib rcParams lifetime.

Steps:
1. Pattern 1 (recommended): Use plotstyle.use() as a context manager — rcParams
   are restored automatically when the block exits, even on exception.
2. Pattern 2: Call style.restore() manually inside a try/finally block.
3. Pattern 3: Values you set before calling use() are captured in a snapshot and
   restored on exit — so your customisations survive the styled block.

Output:
    output/ctx_nature.pdf
    output/manual_ieee.pdf
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

x = np.linspace(0, 2 * np.pi, 100)

# ==============================================================================
# Pattern 1: Context manager (recommended)
# ==============================================================================
# The "as style" binding gives access to the active JournalSpec while inside
# the block. On exit, all plotstyle-modified rcParams are rolled back.

original_fontsize = mpl.rcParams["font.size"]

with plotstyle.use("nature") as style:
    print(f"Inside 'nature' block — journal: {style.spec.metadata.name}")
    fig, ax = plotstyle.figure("nature")
    ax.plot(x, np.sin(x))
    ax.set_xlabel("x")
    ax.set_ylabel("sin(x)")
    plotstyle.savefig(fig, OUTPUT_DIR / "ctx_nature.pdf", journal="nature")
    plt.close(fig)

# Verify that rcParams were actually restored
print(f"Font size restored: {mpl.rcParams['font.size'] == original_fontsize}")

# ==============================================================================
# Pattern 2: Manual restore (use when a context manager is impractical)
# ==============================================================================
# Wrap in try/finally so restore() runs even on failure.

style = plotstyle.use("ieee")
try:
    fig, ax = plotstyle.figure("ieee")
    ax.plot(x, np.cos(x))
    ax.set_xlabel("x")
    ax.set_ylabel("cos(x)")
    plotstyle.savefig(fig, OUTPUT_DIR / "manual_ieee.pdf", journal="ieee")
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

with plotstyle.use("science"):
    fig, ax = plotstyle.figure("science")
    ax.plot(x, np.tan(np.clip(x, 0.1, 3.0)))
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    plt.close(fig)

# plotstyle restored lines.linewidth to the value it had when use() was called (3.0)
print(f"Custom linewidth preserved: {mpl.rcParams['lines.linewidth'] == 3.0}")

# Restore to the value it had before this example ran
mpl.rcParams["lines.linewidth"] = prev_linewidth
