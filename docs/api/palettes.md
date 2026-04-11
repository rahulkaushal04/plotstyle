# Palettes — `plotstyle.color.palettes`

Journal-aware colour palettes with colorblind-safe defaults.

## `palette`

```{eval-rst}
.. autofunction:: plotstyle.color.palettes.palette
```

## `load_palette`

```{eval-rst}
.. autofunction:: plotstyle.color.palettes.load_palette
```

## `JOURNAL_PALETTE_MAP`

```{eval-rst}
.. autodata:: plotstyle.color.palettes.JOURNAL_PALETTE_MAP
```

## Built-in palettes

| Palette name | Colours | Description |
|-------------|---------|-------------|
| `okabe_ito` | 8 | Okabe & Ito (2002) — designed for colour vision deficiencies |
| `tol_bright` | 7 | Paul Tol's bright qualitative scheme |
| `tol_muted` | 7 | Paul Tol's muted qualitative scheme |
| `tol_vibrant` | 7 | Paul Tol's vibrant qualitative scheme |
| `safe_grayscale` | 5 | Luminance-separated for black-and-white print |

## Journal → palette mapping

| Journal | Default palette |
|---------|----------------|
| `nature`, `plos`, `cell` | `okabe_ito` |
| `acs`, `elsevier`, `springer` | `tol_bright` |
| `prl`, `wiley` | `tol_muted` |
| `science` | `tol_vibrant` |
| `ieee` | `safe_grayscale` |

## Usage

### Get colours for a journal

```python
import plotstyle

colors = plotstyle.palette("nature", n=4)
# ['#E69F00', '#56B4E9', '#009E73', '#F0E442']
```

### Cycling

If you request more colours than the palette contains, they cycle:

```python
colors = plotstyle.palette("nature", n=12)  # repeats after 8
```

### With markers and linestyles

For print-safe differentiation (especially important for IEEE grayscale
figures):

```python
styled = plotstyle.palette("ieee", n=4, with_markers=True)
for color, linestyle, marker in styled:
    ax.plot(x, y, color=color, linestyle=linestyle, marker=marker)
```

### Load a palette directly

```python
from plotstyle.color.palettes import load_palette

colors = load_palette("tol_bright")
```

## Exceptions

- {class}`~plotstyle.color.palettes.UnknownJournalError` — raised when a
  journal key is not in `JOURNAL_PALETTE_MAP`.
- {class}`~plotstyle.color.palettes.PaletteNotFoundError` — raised when the
  JSON file for a palette does not exist.
