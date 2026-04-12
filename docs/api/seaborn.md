# Seaborn Integration — `plotstyle.integrations.seaborn`

Compatibility layer ensuring PlotStyle's rcParams survive `sns.set_theme()`.

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

## `capture_overrides`

```{eval-rst}
.. autofunction:: plotstyle.integrations.seaborn.capture_overrides
```

## `reapply_overrides`

```{eval-rst}
.. autofunction:: plotstyle.integrations.seaborn.reapply_overrides
```

## The problem

Both PlotStyle and Seaborn write to `matplotlib.rcParams`. When you call
`sns.set_theme()`, Seaborn resets everything it knows about — including the
journal-specific fonts, sizes, and line widths that PlotStyle set. This module
solves that conflict.

## Two strategies

### Strategy 1: Automatic patch (persistent)

Use the `seaborn_compatible` flag on `plotstyle.use()`:

```python
import plotstyle
import seaborn as sns

with plotstyle.use("nature", seaborn_compatible=True):
    sns.set_theme(style="ticks")
    # PlotStyle rcParams restored automatically after set_theme()
    fig, ax = plotstyle.figure("nature")
    sns.scatterplot(data=df, x="x", y="y", ax=ax)
```

This monkey-patches `sns.set_theme` for the duration of the `with` block. The
original `set_theme` is restored when the block exits.

### Strategy 2: One-shot helper

For scripts where `sns.set_theme()` is called once:

```python
from plotstyle.integrations.seaborn import plotstyle_theme

plotstyle_theme("nature", seaborn_style="ticks")
# Applies seaborn theme first, then layers PlotStyle params on top
```

## Notes

- Seaborn is imported lazily. This module can be imported without seaborn
  installed; `ImportError` is raised only when a function that requires it is
  called.
- The patch is **not thread-safe**. Concurrent calls to `patch_seaborn` /
  `unpatch_seaborn` from multiple threads may produce undefined state.
- `patch_seaborn()` is idempotent — calling it twice does not double-wrap.
