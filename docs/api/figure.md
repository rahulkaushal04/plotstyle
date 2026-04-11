# Figures — `plotstyle.core.figure`

Dimension-aware figure and subplot creation.

## `figure`

```{eval-rst}
.. autofunction:: plotstyle.core.figure.figure
```

## `subplots`

```{eval-rst}
.. autofunction:: plotstyle.core.figure.subplots
```

## Usage

### Single-axis figure

```python
import plotstyle

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature", columns=1)
    ax.plot([1, 2, 3], [4, 5, 6])
    plotstyle.savefig(fig, "figure.pdf", journal="nature")
```

### Double-column figure

```python
with plotstyle.use("ieee"):
    fig, ax = plotstyle.figure("ieee", columns=2)
    ax.plot([1, 2, 3])
```

### Multi-panel figure with auto labels

```python
with plotstyle.use("science"):
    fig, axes = plotstyle.subplots("science", nrows=2, ncols=2, columns=2)
    for ax in axes.flat:
        ax.plot([1, 2, 3])
    # Each panel is labelled a, b, c, d per Science's style
```

### Suppress panel labels

```python
fig, axes = plotstyle.subplots("nature", nrows=1, ncols=3, panels=False)
```

### Custom aspect ratio

By default the golden ratio (φ ≈ 1.618) is used. Override it for square or
panoramic layouts:

```python
fig, ax = plotstyle.figure("nature", aspect=1.0)  # square figure
```

## Notes

- `columns` must be `1` (single-column) or `2` (double-column). Any other
  value raises `ValueError`.
- `subplots()` **always returns a 2-D ndarray** for the axes, even for
  `nrows=1, ncols=1`. Use `axes[0, 0]` to get the bare Axes, or iterate
  with `axes.flat`.
