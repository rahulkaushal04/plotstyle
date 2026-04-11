# Multi-Panel Figures

This guide shows how to create multi-panel figures with automatic panel labels
that match your target journal's conventions.

## Basic 2×2 grid

```python
import numpy as np
import plotstyle

with plotstyle.use("science"):
    fig, axes = plotstyle.subplots("science", nrows=2, ncols=2, columns=2)

    x = np.linspace(0, 2 * np.pi, 100)

    axes[0, 0].plot(x, np.sin(x))
    axes[0, 0].set_ylabel("sin(x)")

    axes[0, 1].plot(x, np.cos(x))
    axes[0, 1].set_ylabel("cos(x)")

    axes[1, 0].plot(x, np.sin(2 * x))
    axes[1, 0].set_ylabel("sin(2x)")

    axes[1, 1].plot(x, np.cos(2 * x))
    axes[1, 1].set_ylabel("cos(2x)")

    plotstyle.savefig(fig, "multi_panel.pdf", journal="science")
```

Each panel is automatically labelled in the style dictated by the journal spec
(for Science: **A**, **B**, **C**, **D**; for Nature: **a**, **b**, **c**, **d**).

## Panel label styles by journal

Different journals use different label conventions:

| Journal | Style | Example |
|---------|-------|---------|
| Nature | bold lowercase | a, b, c |
| Science | bold uppercase | A, B, C |
| IEEE | normal parenthesised lowercase | (a), (b), (c) |
| Cell | bold uppercase | A, B, C |
| ACS | bold lowercase | a, b, c |

PlotStyle handles this automatically based on the journal spec's
`panel_label_case` field.

## Suppress panel labels

If you want to manage labels yourself:

```python
fig, axes = plotstyle.subplots("nature", nrows=1, ncols=3, panels=False)
```

## Single-column vs double-column

```python
# Narrow (single column) — fits in the text column
fig, axes = plotstyle.subplots("nature", nrows=1, ncols=2, columns=1)

# Wide (double column) — spans the full page width
fig, axes = plotstyle.subplots("nature", nrows=1, ncols=2, columns=2)
```

## Custom aspect ratio

The default aspect ratio is the golden ratio (φ ≈ 1.618). For square panels:

```python
fig, axes = plotstyle.subplots("nature", nrows=2, ncols=2, aspect=1.0)
```

## Iterating over axes

`subplots()` always returns a 2-D ndarray, even for single-panel figures:

```python
fig, axes = plotstyle.subplots("nature", nrows=2, ncols=3)

# Flat iteration
for ax in axes.flat:
    ax.plot([1, 2, 3])

# Indexed access
axes[0, 0].set_title("Top-left")
axes[1, 2].set_title("Bottom-right")

# Single-panel case
fig, axes = plotstyle.subplots("nature", nrows=1, ncols=1)
ax = axes[0, 0]  # always use indexing
```
