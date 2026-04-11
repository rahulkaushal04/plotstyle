# Color Palettes

This guide covers choosing and using colorblind-safe palettes for your journal
figures.

## Quick palette access

```python
import plotstyle

colors = plotstyle.palette("nature", n=4)
# Returns hex strings: ['#E69F00', '#56B4E9', '#009E73', '#F0E442']
```

Use these directly in your plots:

```python
import numpy as np

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
    x = np.linspace(0, 10, 100)
    colors = plotstyle.palette("nature", n=3)

    ax.plot(x, np.sin(x), color=colors[0], label="sin(x)")
    ax.plot(x, np.cos(x), color=colors[1], label="cos(x)")
    ax.plot(x, np.sin(x + 1), color=colors[2], label="sin(x+1)")
    ax.legend()
```

## Palettes with markers and linestyles

For IEEE and other journals that require grayscale-safe figures, use
`with_markers=True` to get distinct markers and linestyles alongside colours:

```python
styled = plotstyle.palette("ieee", n=4, with_markers=True)
# Returns: [(color, linestyle, marker), ...]

with plotstyle.use("ieee"):
    fig, ax = plotstyle.figure("ieee")
    x = np.linspace(0, 10, 50)

    for i, (color, ls, marker) in enumerate(styled):
        ax.plot(x, np.sin(x + i), color=color, linestyle=ls,
                marker=marker, markevery=10, label=f"Series {i+1}")
    ax.legend()
```

## Which palette does each journal get?

PlotStyle maps each journal to a palette optimised for its requirements:

| Journal | Palette | Why |
|---------|---------|-----|
| Nature, PLOS, Cell | Okabe–Ito | Most-cited colorblind-safe palette |
| ACS, Elsevier, Springer | Tol Bright | High chroma, good on white backgrounds |
| PRL, Wiley | Tol Muted | Softer tones for dense plots |
| Science | Tol Vibrant | High contrast for smaller figures |
| IEEE | Safe Grayscale | Luminance-separated for B&W print |

## Checking grayscale safety

```python
from plotstyle.color.grayscale import is_grayscale_safe

colors = plotstyle.palette("nature", n=4)
print(is_grayscale_safe(colors))  # True or False
```

See the [Accessibility guide](accessibility.md) for more detail.

## Loading palettes directly

If you want a specific palette regardless of journal:

```python
from plotstyle.color.palettes import load_palette

colors = load_palette("tol_vibrant")
```

Available: `okabe_ito`, `tol_bright`, `tol_muted`, `tol_vibrant`,
`safe_grayscale`.
