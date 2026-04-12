# Style — `plotstyle.core.style`

Apply and restore journal style presets.

## `use`

```{eval-rst}
.. autofunction:: plotstyle.core.style.use
```

## `JournalStyle`

```{eval-rst}
.. autoclass:: plotstyle.core.style.JournalStyle
   :members:
   :special-members: __enter__, __exit__
```

## Usage

### Context manager (recommended)

```python
import plotstyle

with plotstyle.use("nature") as style:
    print(style.spec.metadata.name)  # "Nature"
    fig, ax = plotstyle.figure("nature")
    ax.plot([1, 2, 3])
# rcParams restored automatically
```

### Manual restore

```python
style = plotstyle.use("nature")
try:
    fig, ax = plotstyle.figure("nature")
    ax.plot([1, 2, 3])
finally:
    style.restore()
```

### Seaborn-compatible mode

When working with Seaborn, pass `seaborn_compatible=True` so that
`sns.set_theme()` calls don't clobber PlotStyle's settings:

```python
with plotstyle.use("nature", seaborn_compatible=True):
    import seaborn as sns
    sns.set_theme(style="ticks")
    # PlotStyle rcParams are automatically reapplied after set_theme()
```
