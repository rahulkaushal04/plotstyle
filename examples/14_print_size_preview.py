"""
Print-size preview: see your figure at its actual physical size on screen.

plotstyle.preview_print_size() scales a figure's DPI so it appears at its
approximate physical dimensions on your monitor. This helps verify that text
is readable and lines are visible at the size the journal will print.

The monitor_dpi parameter should match your display:
  - 96 dpi : Windows / most Linux (default)
  - 144 dpi: macOS 1x logical DPI
  - 192 dpi: macOS 2x Retina

A size annotation is added temporarily; closing the window removes it and
restores the figure's original DPI.

Steps:
1. Create a figure with plotstyle.use() and style.figure().
2. Call plotstyle.preview_print_size() to open an interactive preview window.
3. The figure is displayed at its true physical size (e.g. 89 mm wide).
4. Close the preview window. The figure is restored to its original state.

Note: This example opens an interactive Matplotlib window. It cannot run in
headless (non-GUI) environments. Run it locally with a display.

Output: (interactive preview window)
"""

import numpy as np

import plotstyle

# ==============================================================================
# 1. Create a figure for Nature (89 mm single-column width)
# ==============================================================================

with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)

    x = np.linspace(0, 2 * np.pi, 200)
    colors = style.palette(n=2)
    ax.plot(x, np.sin(x), color=colors[0], label="sin(x)")
    ax.plot(x, np.cos(x), color=colors[1], label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()

    # Opens a window at the figure's true physical size (89 mm for Nature single-column).
    plotstyle.preview_print_size(fig, journal="nature", columns=1, monitor_dpi=96)

    # The figure is unchanged after preview_print_size returns.
    print(f"Figure size after preview: {fig.get_size_inches()}")
