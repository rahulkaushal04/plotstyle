# Seaborn Integration — `plotstyle.integrations.seaborn`

Keeps PlotStyle's rcParams intact when `sns.set_theme()` is called.

## `plotstyle_theme`

```{eval-rst}
.. autofunction:: plotstyle.integrations.seaborn.plotstyle_theme
```

## `patch_seaborn`

```{eval-rst}
.. autofunction:: plotstyle.integrations.seaborn.patch_seaborn
```

## `unpatch_seaborn`

```{eval-rst}
.. autofunction:: plotstyle.integrations.seaborn.unpatch_seaborn
```

## The problem

Both PlotStyle and Seaborn write to `matplotlib.rcParams`. When you call
`sns.set_theme()`, Seaborn resets fonts, sizes, and line widths — undoing
everything PlotStyle set. This module solves that conflict.

## Recommended usage

### Automatic patch (via context manager)

The easiest approach — pass `seaborn_compatible=True` to `plotstyle.use()`:

```python
import plotstyle
import seaborn as sns

with plotstyle.use("nature", seaborn_compatible=True) as style:
    sns.set_theme(style="ticks")
    # PlotStyle rcParams are reapplied automatically after set_theme()
    fig, ax = style.figure()
    sns.scatterplot(data=df, x="x", y="y", ax=ax)
```

The patch is removed when the `with` block ends.

### One-shot helper

For scripts where `sns.set_theme()` is called once upfront:

```python
from plotstyle.integrations.seaborn import plotstyle_theme

plotstyle_theme("nature", seaborn_style="ticks")
# Applies seaborn theme first, then overlays PlotStyle settings
```

## `capture_overrides`

```{eval-rst}
.. autofunction:: plotstyle.integrations.seaborn.capture_overrides
```

## `reapply_overrides`

```{eval-rst}
.. autofunction:: plotstyle.integrations.seaborn.reapply_overrides
```

## Notes

- Seaborn is imported lazily — this module can be imported without seaborn
  installed. `ImportError` is raised only when a function that requires it is
  called.
- The patch is **not thread-safe**.
- `patch_seaborn()` is idempotent — calling it more than once is safe.
- `capture_overrides()` and `reapply_overrides()` are called internally by
  `plotstyle.use(seaborn_compatible=True)`. You rarely need to call them
  directly.
