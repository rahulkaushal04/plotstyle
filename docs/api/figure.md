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

with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)
    ax.plot([1, 2, 3], [4, 5, 6])
    style.savefig(fig, "figure.pdf")
```

### Double-column figure

```python
with plotstyle.use("ieee") as style:
    fig, ax = style.figure(columns=2)
    ax.plot([1, 2, 3])
```

### Multi-panel figure with auto labels

```python
with plotstyle.use("science") as style:
    fig, axes = style.subplots(nrows=2, ncols=2, columns=2)
    for ax in axes.flat:
        ax.plot([1, 2, 3])
    # Each panel is labelled a, b, c, d — all current journal specs use lowercase
```

### Suppress panel labels

```python
with plotstyle.use("nature") as style:
    fig, axes = style.subplots(nrows=1, ncols=3, panels=False)
```

### Custom aspect ratio

By default the golden ratio (φ ≈ 1.618) is used. Override it for square or
panoramic layouts:

```python
with plotstyle.use("nature") as style:
    fig, ax = style.figure(aspect=1.0)  # square figure
```

## Notes

- `columns` must be `1` (single-column) or `2` (double-column). Any other
  value raises `ValueError`.
- `subplots()` **always returns a 2-D ndarray** by default, even for
  `nrows=1, ncols=1`. Use `axes[0, 0]` to get the bare Axes, or iterate
  with `axes.flat`.  Pass `squeeze=True` to drop size-1 dimensions and
  recover Matplotlib-compatible behaviour (`for ax in axes` over a single
  row).
