# Grayscale: `plotstyle.color.grayscale`

Grayscale simulation and luminance analysis for print safety checks.

## `preview_grayscale`

```{eval-rst}
.. autofunction:: plotstyle.color.grayscale.preview_grayscale
```

## `is_grayscale_safe`

```{eval-rst}
.. autofunction:: plotstyle.color.grayscale.is_grayscale_safe
```

## `luminance_delta`

```{eval-rst}
.. autofunction:: plotstyle.color.grayscale.luminance_delta
```

## `rgb_to_luminance`

```{eval-rst}
.. autofunction:: plotstyle.color.grayscale.rgb_to_luminance
```

## Usage

### Check if a palette is print-safe

```python
from plotstyle.color.grayscale import is_grayscale_safe

colors = ["#e41a1c", "#377eb8", "#4daf4a"]
print(is_grayscale_safe(colors, threshold=0.1))  # True or False
```

The default `threshold=0.1` requires every pair of colours to differ by at
least 10% of the full luminance range. Use `0.15` for stricter workflows.

### Inspect pairwise luminance differences

```python
from plotstyle.color.grayscale import luminance_delta

pairs = luminance_delta(["#ffffff", "#000000", "#888888"])
for idx_a, idx_b, delta in pairs:
    print(f"Pair ({idx_a}, {idx_b}): delta = {delta:.3f}")
```

Results are sorted ascending; the most problematic pair comes first.

### Visual grayscale preview

```python
import matplotlib.pyplot as plt
from plotstyle.color.grayscale import preview_grayscale

fig, ax = plt.subplots()
ax.bar([1, 2, 3], [4, 7, 2], color=["#e41a1c", "#377eb8", "#4daf4a"])

comp = preview_grayscale(fig)
comp.savefig("grayscale_preview.png", dpi=150)
```

Creates a side-by-side `[Original | Grayscale]` comparison.

**Output:**

![Grayscale preview: original vs grayscale](../images/accessibility_grayscale.png)

## Notes

- Luminance uses ITU-R BT.709 coefficients:
  $L = 0.2126 R + 0.7152 G + 0.0722 B$
- The source figure is never modified. `preview_grayscale()` returns a new
  figure.
