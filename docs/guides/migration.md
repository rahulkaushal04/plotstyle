# Spec Diffing & Migration

How to compare journal specs and re-style a figure for a different journal.

## Compare two journals

`plotstyle.diff()` shows exactly what differs between two journals:

```python
import plotstyle

result = plotstyle.diff("nature", "ieee")
print(result)
```

Output:

```
Nature → IEEE Transactions
──────────────────────────────────────────────────
Column Width (single):  89.0mm → 88.9mm
Column Width (double):  183.0mm → 182.0mm
Max Height:             247.0mm → 216.0mm
Font Family:            Helvetica, Arial → Times New Roman, Helvetica, Arial
Min Font Size:          5.0pt → 9.0pt
Max Font Size:          7.0pt → 10.0pt
Panel Label Size:       5.0pt → 9.0pt
Preferred Formats:      ai, eps, pdf → tiff, eps, pdf, png
Colorblind Required:    No → Yes
```

### Check programmatically

```python
result = plotstyle.diff("nature", "science")

if result:
    print(f"{len(result)} fields differ")
else:
    print("Specs are identical")
```

### Serialize to JSON

```python
import json

data = result.to_dict()
print(json.dumps(data, indent=2))
```

## Migrate a figure

`plotstyle.migrate()` re-styles an existing figure for a different journal:

```python
import numpy as np
import plotstyle

# Create a Nature figure
with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.legend()

# Migrate to IEEE
plotstyle.migrate(fig, from_journal="nature", to_journal="ieee")
plotstyle.savefig(fig, "figure_ieee.pdf", journal="ieee")
```

### What migration does

1. Applies the target journal's rcParams (fonts, sizes, line widths)
2. Resizes the figure to the target's single-column width, keeping aspect ratio
3. Rescales all text proportionally, clamped to the target's font-size range

### Migration warnings

When notable changes are detected, PlotStyle emits `PlotStyleWarning` instances to guide you:

- **Font family change** (e.g. Helvetica → Times New Roman): update any
  hardcoded font references.
- **Grayscale now required**: verify all colours are distinguishable in print.
- **Increased DPI floor**: re-export at the higher resolution.

## Full workflow

```python
# 1. See what changes
diff = plotstyle.diff("nature", "science")
print(diff)

# 2. Migrate if needed
if diff:
    plotstyle.migrate(fig, from_journal="nature", to_journal="science")

    # 3. Validate the result
    report = plotstyle.validate(fig, journal="science")
    if not report.passed:
        for f in report.failures:
            print(f.fix_suggestion)
```

## Notes

- `migrate()` modifies the figure **in-place** and returns the same `Figure`
  instance. Clone it first if you need to keep the original:

  ```python
  import copy
  fig_copy = copy.deepcopy(fig)
  plotstyle.migrate(fig_copy, from_journal="nature", to_journal="ieee")
  ```

- `migrate()` applies the target journal's rcParams temporarily and restores
  global state when it returns.
