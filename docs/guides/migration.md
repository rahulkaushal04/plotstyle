# Spec Diffing & Migration

This guide demonstrates how to compare journal specs and migrate existing
figures from one journal to another.

## Compare two journals

Use `plotstyle.diff()` to see exactly what differs between two journals:

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
Font Family:            Helvetica, Arial → Times New Roman, Times
Min Font Size:          5.0pt → 8.0pt
Max Font Size:          7.0pt → 10.0pt
Min DPI:                300 → 600
Grayscale Required:     No → Yes
Min Line Weight:        0.25pt → 0.5pt
```

### Check programmatically

```python
result = plotstyle.diff("nature", "science")

if result:
    print(f"{len(result)} fields differ")
else:
    print("Specs are identical across all tracked fields")
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
with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
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

1. **Applies target rcParams** — fonts, sizes, line widths
2. **Resizes the figure** — to the target journal's single-column width,
   preserving the current aspect ratio
3. **Rescales text** — all text artists are proportionally rescaled and clamped
   to the target journal's allowed font-size range

### Migration warnings

PlotStyle warns you about notable changes that may require manual attention:

- **Font family change**: e.g. Helvetica → Times New Roman. Update any
  hardcoded font references.
- **Grayscale now required**: verify all colours remain distinguishable when
  printed in grayscale.
- **Increased DPI floor**: re-export at the higher resolution.

```python
import warnings
from plotstyle._utils.warnings import PlotStyleWarning

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    plotstyle.migrate(fig, from_journal="nature", to_journal="ieee")

for w in caught:
    if issubclass(w.category, PlotStyleWarning):
        print(w.message)
```

## Workflow: diff, decide, migrate

```python
# 1. See what changes
diff = plotstyle.diff("nature", "science")
print(diff)

# 2. Decide if migration is appropriate
if diff:
    # 3. Migrate
    plotstyle.migrate(fig, from_journal="nature", to_journal="science")

    # 4. Validate the result
    report = plotstyle.validate(fig, journal="science")
    if not report.passed:
        for f in report.failures:
            print(f.fix_suggestion)
```

## Notes

- `migrate()` mutates the figure **in-place** and returns it (for call
  chaining). Clone the figure first if you need to preserve the original.
- `migrate()` calls `mpl.rcParams.update()` with the target journal's
  rcParams. Wrap it in `plotstyle.use()` if you need the original state
  restored afterwards.
