# Seaborn Integration

This guide shows how to use PlotStyle with Seaborn without one library
clobbering the other's settings.

## The problem

Both PlotStyle and Seaborn write to `matplotlib.rcParams`. When you call
`sns.set_theme()`, Seaborn resets fonts, sizes, and line widths — undoing
everything PlotStyle set.

## Solution 1: Automatic patch (recommended)

Pass `seaborn_compatible=True` to `plotstyle.use()`. This monkey-patches
`sns.set_theme` so that PlotStyle's rcParams are automatically reapplied after
every Seaborn theme call:

```python
import plotstyle
import seaborn as sns
import pandas as pd

df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 3, 5], "group": ["A", "A", "B", "B"]})

with plotstyle.use("nature", seaborn_compatible=True):
    sns.set_theme(style="ticks")
    # PlotStyle rcParams are restored automatically ✓

    fig, ax = plotstyle.figure("nature")
    sns.scatterplot(data=df, x="x", y="y", hue="group", ax=ax)
    plotstyle.savefig(fig, "seaborn_figure.pdf", journal="nature")
```

The patch is removed automatically when the `with` block exits.

## Solution 2: One-shot helper

If you only call `sns.set_theme()` once (typical in scripts):

```python
from plotstyle.integrations.seaborn import plotstyle_theme

plotstyle_theme("nature", seaborn_style="ticks")
# This applies the seaborn theme first, then layers PlotStyle params on top
```

## Solution 3: Manual control

For advanced use cases, manage the patch lifecycle explicitly:

```python
from plotstyle.integrations.seaborn import (
    capture_overrides,
    patch_seaborn,
    unpatch_seaborn,
)
from plotstyle.engine.rcparams import build_rcparams
from plotstyle.specs import registry

spec = registry.get("nature")
params = build_rcparams(spec)

capture_overrides(params)
patch_seaborn()

try:
    import seaborn as sns
    sns.set_theme(style="whitegrid")
    # PlotStyle params survive ✓
finally:
    unpatch_seaborn()
```

## Tips

- Always apply `plotstyle.use()` **before** `sns.set_theme()` when using the
  automatic patch.
- The patch is **idempotent** — calling `patch_seaborn()` twice does not
  double-wrap.
- The patch is **not thread-safe**. Avoid concurrent calls from multiple
  threads.
