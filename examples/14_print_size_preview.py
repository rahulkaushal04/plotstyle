"""
Print-size preview: see your figure at its actual physical size on screen.

plotstyle.preview_print_size() scales a figure's DPI so it appears at its
approximate physical dimensions on your monitor. This helps verify that text
is readable and lines are visible at the size the journal will print.

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

    # -- 2. Preview at physical print size ------------------------------------
    # This opens a Matplotlib window where the figure appears at its actual
    # printed size (89 mm wide for Nature single-column).
    #
    # The monitor_dpi parameter should match your display:
    #   - 96  → Windows / most Linux (default)
    #   - 144 → macOS 1x logical
    #   - 192 → macOS 2x Retina
    #
    # An annotation is temporarily added showing the target width in mm.
    # After you close the window, the annotation is removed and the figure's
    # DPI is restored automatically.

    plotstyle.preview_print_size(fig, journal="nature", columns=1, monitor_dpi=96)

    # The figure is unchanged after preview_print_size returns.
    print(f"Figure size after preview: {fig.get_size_inches()}")
