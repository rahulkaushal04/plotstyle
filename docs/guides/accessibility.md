# Accessibility Checks

This guide shows how to verify that your figures are perceptible by readers
with colour vision deficiencies and readable in greyscale print.

## Colorblind preview

`preview_colorblind()` simulates how your figure looks under three types of
colour vision deficiency:

```python
import matplotlib.pyplot as plt
import plotstyle
from plotstyle.color.accessibility import preview_colorblind

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
    colors = plotstyle.palette("nature", n=3)

    ax.bar([1, 2, 3], [4, 7, 2], color=colors)
    ax.set_ylabel("Value")

    comp = preview_colorblind(fig)
    comp.savefig("cvd_comparison.png", dpi=150)
```

This produces a 4-panel figure:

```
[ Original | Deuteranopia | Protanopia | Tritanopia ]
```

If the colour-coded elements are indistinguishable in any panel, consider
switching palettes or adding redundant encoding (markers, patterns, labels).

### Preview specific deficiency types

```python
from plotstyle.color.accessibility import preview_colorblind, CVDType

comp = preview_colorblind(fig, cvd_types=[CVDType.DEUTERANOPIA, CVDType.PROTANOPIA])
```

## Grayscale preview

For journals like IEEE that require grayscale-safe figures:

```python
from plotstyle.color.grayscale import preview_grayscale

comp = preview_grayscale(fig)
comp.savefig("grayscale_comparison.png", dpi=150)
```

Produces a 2-panel figure: `[Original | Grayscale]`.

## Programmatic grayscale check

Instead of visual inspection, check numerically:

```python
from plotstyle.color.grayscale import is_grayscale_safe, luminance_delta

colors = plotstyle.palette("nature", n=4)

# Quick boolean check
safe = is_grayscale_safe(colors, threshold=0.1)
print(f"Grayscale safe: {safe}")

# Detailed pairwise analysis
pairs = luminance_delta(colors)
for idx_a, idx_b, delta in pairs:
    status = "✓" if delta >= 0.1 else "✗"
    print(f"  {status} Colors {idx_a} vs {idx_b}: Δ = {delta:.3f}")
```

The `threshold` parameter controls the minimum required luminance difference
between every pair. Common values:

| Threshold | Use case |
|-----------|----------|
| `0.10` | Practical minimum for most print media |
| `0.15` | Recommended for high-quality print |
| `0.20` | Conservative; good for low-quality printers |

## Best practices

1. **Always check** if the target journal requires colorblind- or
   grayscale-safe figures (see the journal spec's `color.colorblind_required`
   and `color.grayscale_required` fields).
2. **Use the journal's recommended palette** via `plotstyle.palette()` — these
   are already optimised for the journal's requirements.
3. **Add redundant encoding** — markers, linestyles, or direct labels — so
   that information is not conveyed by colour alone.
4. **Run `plotstyle.validate()`** as a final check; it flags colour
   accessibility issues automatically.
