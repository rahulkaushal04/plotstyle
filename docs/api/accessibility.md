# Accessibility — `plotstyle.color.accessibility`

Colorblind simulation engine using Machado et al. (2009) matrices.

## `preview_colorblind`

```{eval-rst}
.. autofunction:: plotstyle.color.accessibility.preview_colorblind
```

## `simulate_cvd`

```{eval-rst}
.. autofunction:: plotstyle.color.accessibility.simulate_cvd
```

## `CVDType`

```{eval-rst}
.. autoclass:: plotstyle.color.accessibility.CVDType
   :members:
   :undoc-members:
```

## Supported deficiency types

| Type | Affects | Prevalence |
|------|---------|------------|
| `CVDType.DEUTERANOPIA` | Green (M-cone) | ~6 % of males |
| `CVDType.PROTANOPIA` | Red (L-cone) | ~2 % of males |
| `CVDType.TRITANOPIA` | Blue (S-cone) | < 0.01 % of population |

## Usage

### Preview all CVD types

```python
import matplotlib.pyplot as plt
from plotstyle.color.accessibility import preview_colorblind

fig, ax = plt.subplots()
ax.scatter([1, 2, 3], [4, 5, 6], c=["#e41a1c", "#377eb8", "#4daf4a"])

comp = preview_colorblind(fig)
comp.savefig("cvd_preview.png", dpi=150)
```

This creates a figure with four panels: Original, Deuteranopia, Protanopia,
Tritanopia.

### Preview specific types only

```python
from plotstyle.color.accessibility import preview_colorblind, CVDType

comp = preview_colorblind(fig, cvd_types=[CVDType.DEUTERANOPIA])
```

### Low-level simulation

```python
import numpy as np
from plotstyle.color.accessibility import simulate_cvd, CVDType

img = np.random.rand(100, 100, 3).astype(np.float32)
result = simulate_cvd(img, CVDType.PROTANOPIA)
# result.shape == (100, 100, 3), dtype float64, values in [0, 1]
```

## Notes

- The simulation matrices assume linear sRGB input. Matplotlib's Agg renderer
  outputs gamma-encoded sRGB, so results are an approximation rather than a
  physically exact model.
- The source figure is never modified. `preview_colorblind()` returns a new
  figure.
