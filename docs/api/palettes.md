# Palettes: `plotstyle.color.palettes`

Journal-aware color palettes with colorblind-safe defaults.

## `palette`

```{eval-rst}
.. autofunction:: plotstyle.color.palettes.palette
```

## `apply_palette`

```{eval-rst}
.. autofunction:: plotstyle.color.palettes.apply_palette
```

## `load_palette`

```{eval-rst}
.. autofunction:: plotstyle.color.palettes.load_palette
```

## `list_palettes`

```{eval-rst}
.. autofunction:: plotstyle.color.palettes.list_palettes
```

## `JOURNAL_PALETTE_MAP`

```{eval-rst}
.. autodata:: plotstyle.color.palettes.JOURNAL_PALETTE_MAP
```

## Built-in palettes

| Palette name | Colors | Description |
|-------------|---------|-------------|
| `okabe-ito` | 8 | Okabe & Ito (2008), designed for color vision deficiencies |
| `tol-bright` | 7 | Paul Tol's bright qualitative scheme |
| `tol-muted` | 10 | Paul Tol's muted qualitative scheme |
| `tol-vibrant` | 7 | Paul Tol's vibrant qualitative scheme |
| `tol-light` | 9 | Paul Tol's light qualitative scheme |
| `tol-high-contrast` | 3 | Paul Tol's high-contrast scheme, optimised for print |
| `tol-rainbow-4` | 4 | Paul Tol's discrete rainbow (4 steps) |
| `tol-rainbow-6` | 6 | Paul Tol's discrete rainbow (6 steps) |
| `tol-rainbow-8` | 8 | Paul Tol's discrete rainbow (8 steps) |
| `tol-rainbow-10` | 10 | Paul Tol's discrete rainbow (10 steps) |
| `tol-rainbow-12` | 12 | Paul Tol's discrete rainbow (12 steps) |
| `safe-grayscale` | 6 | Luminance-separated for black-and-white print |

Names accept either hyphens (`tol-bright`) or underscores (`tol_bright`).

## Journal → palette mapping

`plotstyle.use(journal)` automatically sets the journal's recommended palette
as `axes.prop_cycle`. Plots draw from it without any `color=` argument. A color
overlay applied in the same `use()` call overrides this default.

| Journal | Default palette |
|---------|----------------|
| `nature`, `plos`, `cell` | `okabe-ito` |
| `acs`, `elsevier`, `springer` | `tol-bright` |
| `prl`, `wiley` | `tol-muted` |
| `science` | `tol-vibrant` |
| `ieee` | `safe-grayscale` |

## Usage

### Automatic default cycle

```python
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    ax.plot(x, np.sin(x))  # Okabe-Ito color #1 - no color= needed
    ax.plot(x, np.cos(x))  # Okabe-Ito color #2
```

### Get colors for a journal

```python
import plotstyle

colors = plotstyle.palette("nature", n=4)
# ['#E69F00', '#56B4E9', '#009E73', '#F0E442']
```

### Cycling

If you request more colors than the palette contains, they cycle:

```python
colors = plotstyle.palette("nature", n=12)  # repeats after 8
```

### With markers and linestyles

For print-safe differentiation (especially important for IEEE grayscale figures):

```python
styled = plotstyle.palette("ieee", n=4, with_markers=True)
for color, linestyle, marker in styled:
    ax.plot(x, y, color=color, linestyle=linestyle, marker=marker)
```

### Apply a palette to axes

```python
plotstyle.apply_palette("tol-bright")          # global (all new axes)
plotstyle.apply_palette("okabe-ito", ax=ax)    # single axes only
```

Applying a palette does **not** retroactively recolor artists that are
already drawn. Call `apply_palette()` before plotting to ensure the new cycle
is picked up from the first line.

### Load a palette directly

```python
from plotstyle.color.palettes import load_palette

colors = load_palette("tol-bright")   # ['#4477AA', '#EE6677', ...]
```

## Exceptions

- {class}`~plotstyle.specs.SpecNotFoundError`: raised when a journal key is
  not in `JOURNAL_PALETTE_MAP`.
- {class}`~plotstyle.color.palettes.PaletteNotFoundError`: raised when the
  JSON file for a palette does not exist.
- `TypeError`: raised by `palette()` when `n` is not an integer (e.g. a
  float or string).
- `ValueError`: raised by `palette()` when `n` is an integer but less than 1.

```{eval-rst}
.. autoclass:: plotstyle.color.palettes.PaletteNotFoundError
```
