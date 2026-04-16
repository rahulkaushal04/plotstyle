# Color Palettes

How to choose and use colorblind-safe palettes for your journal figures.

## Get colours for a journal

```python
import plotstyle

colors = plotstyle.palette("nature", n=4)
# ['#E69F00', '#56B4E9', '#009E73', '#F0E442']
```

Use them directly in your plots:

```python
import numpy as np

with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    x = np.linspace(0, 10, 100)
    colors = style.palette(n=3)

    ax.plot(x, np.sin(x), color=colors[0], label="sin(x)")
    ax.plot(x, np.cos(x), color=colors[1], label="cos(x)")
    ax.plot(x, np.sin(x + 1), color=colors[2], label="sin(x+1)")
    ax.legend()
```

**Output:**

![Palette comparison across journals](../images/palette_comparison.png)

## Add markers and linestyles

For journals that require grayscale-safe figures, use `with_markers=True`.
This returns `(color, linestyle, marker)` tuples so series remain
distinguishable in black-and-white print:

```python
styled = style.palette(n=4, with_markers=True)

for i, (color, ls, marker) in enumerate(styled):
    ax.plot(x, np.sin(x + i), color=color, linestyle=ls,
            marker=marker, markevery=10, label=f"Series {i+1}")
```

## Which palette does each journal get?

| Journal | Palette | Why |
|---------|---------|-----|
| Nature, PLOS, Cell | Okabe–Ito | Most widely used colorblind-safe palette |
| ACS, Elsevier, Springer | Tol Bright | High contrast on white backgrounds |
| PRL, Wiley | Tol Muted | Softer tones for dense plots |
| Science | Tol Vibrant | High contrast for small figures |
| IEEE | Safe Grayscale | Distinguishable in black-and-white print |

## Check if colours are grayscale-safe

```python
from plotstyle.color.grayscale import is_grayscale_safe

colors = plotstyle.palette("nature", n=4)
print(is_grayscale_safe(colors))  # True or False
```

See the [Accessibility guide](accessibility.md) for more.

## Load a palette by name

If you want a specific palette regardless of journal:

```python
from plotstyle.color.palettes import load_palette

colors = load_palette("tol_vibrant")
```

Available palettes: `okabe_ito`, `tol_bright`, `tol_muted`, `tol_vibrant`,
`safe_grayscale`.
