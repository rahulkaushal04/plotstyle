# Seaborn Integration

How to use PlotStyle with Seaborn without one overriding the other.

## The problem

Both PlotStyle and Seaborn write to `matplotlib.rcParams`. When you call
`sns.set_theme()`, Seaborn resets fonts, sizes, and line widths — undoing
everything PlotStyle set.

## Solution 1: Automatic patch (recommended)

Pass `seaborn_compatible=True` to `plotstyle.use()`. This makes PlotStyle's
settings survive any `sns.set_theme()` calls:

```python
import plotstyle
import seaborn as sns
import pandas as pd

df = pd.DataFrame({
    "x": [1, 2, 3, 4],
    "y": [2, 4, 3, 5],
    "group": ["A", "A", "B", "B"],
})

with plotstyle.use("nature", seaborn_compatible=True) as style:
    sns.set_theme(style="ticks")   # PlotStyle settings are preserved

    fig, ax = style.figure()
    sns.scatterplot(data=df, x="x", y="y", hue="group", ax=ax)
    style.savefig(fig, "seaborn_figure.pdf")
```

The patch is removed automatically when the `with` block ends.

## Solution 2: One-shot helper

If you only need to call `sns.set_theme()` once:

```python
from plotstyle.integrations.seaborn import plotstyle_theme

plotstyle_theme("nature", seaborn_style="ticks")
# Applies the seaborn theme first, then overlays PlotStyle settings
```

## Tips

- Apply `plotstyle.use()` **before** `sns.set_theme()` when using the patch.
- Calling `patch_seaborn()` more than once is safe — it won't double-wrap.
- The patch is **not thread-safe**. Avoid concurrent use from multiple threads.
