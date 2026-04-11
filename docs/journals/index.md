# Supported Journals

PlotStyle ships specifications for 10 major scientific journal publishers.
Each spec is stored as a validated TOML file and loaded on demand via the
{class}`~plotstyle.specs.SpecRegistry`.

## Overview

| Key | Journal | Publisher | Column (mm) | Min DPI | Formats |
|-----|---------|-----------|-------------|---------|---------|
| `acs` | ACS (JACS) | American Chemical Society | 84.6 / 177.8 | 300 | PDF, EPS, TIFF |
| `cell` | Cell | Cell Press | 85.0 / 174.0 | 300 | TIFF, PDF, EPS |
| `elsevier` | Elsevier | Elsevier | 90.0 / 190.0 | 300 | TIFF, EPS, PDF |
| `ieee` | IEEE Transactions | IEEE | 88.9 / 182.0 | 600 | PDF, EPS, PNG, TIFF |
| `nature` | Nature | Springer Nature | 89.0 / 183.0 | 300 | TIFF, PDF, EPS |
| `plos` | PLOS ONE | PLOS | 132.0 / 190.5 | 300 | TIFF, EPS, PDF |
| `prl` | Physical Review Letters | APS | 86.0 / 178.0 | 600 | PDF, EPS |
| `science` | Science | AAAS | 57.0 / 121.0 | 300 | TIFF, PDF, EPS |
| `springer` | Springer | Springer | 84.0 / 174.0 | 300 | TIFF, EPS, PDF |
| `wiley` | Wiley | Wiley | 85.0 / 178.0 | 300 | TIFF, EPS, PDF |

*Column widths listed as single / double in mm.*

## Typography

| Key | Font family | Size range (pt) | Panel labels |
|-----|------------|-----------------|-------------|
| `acs` | Helvetica, Arial | 4.5 – 8.0 | bold lowercase |
| `cell` | Helvetica, Arial | 6.0 – 8.0 | bold uppercase |
| `elsevier` | Helvetica, Arial, Times New Roman | 6.0 – 8.0 | bold uppercase |
| `ieee` | Times New Roman, Times | 8.0 – 10.0 | normal (a), (b), (c) |
| `nature` | Helvetica, Arial | 5.0 – 7.0 | bold lowercase |
| `plos` | Arial, Helvetica | 8.0 – 12.0 | bold uppercase |
| `prl` | Times, Times New Roman | 6.0 – 10.0 | normal (a), (b), (c) |
| `science` | Helvetica, Myriad Pro, Arial | 5.0 – 9.0 | bold uppercase |
| `springer` | Helvetica, Arial | 6.0 – 9.0 | bold lowercase |
| `wiley` | Helvetica, Arial | 8.0 – 12.0 | normal lowercase |

## Accessibility requirements

| Key | Colorblind safe | Grayscale safe | Min line weight (pt) |
|-----|----------------|----------------|---------------------|
| `acs` | Required | — | 0.50 |
| `cell` | Required | — | 0.50 |
| `elsevier` | Required | — | 0.25 |
| `ieee` | Required | **Required** | 0.50 |
| `nature` | Required | — | 0.25 |
| `plos` | Required | — | 0.50 |
| `prl` | Required | — | 0.50 |
| `science` | Required | — | 0.28 |
| `springer` | Required | — | 0.30 |
| `wiley` | Required | — | 0.50 |

## Using a spec

```python
import plotstyle

# Apply a journal's style
with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature", columns=1)
    ax.plot([1, 2, 3])
    plotstyle.savefig(fig, "figure.pdf", journal="nature")
```

## Inspect a spec programmatically

```python
from plotstyle.specs import registry

spec = registry.get("ieee")
print(spec.dimensions.single_column_mm)   # 88.9
print(spec.typography.font_family)        # ['Times New Roman', 'Times']
print(spec.export.preferred_formats)      # ['pdf', 'eps', 'png', 'tiff']
print(spec.color.grayscale_required)      # True
```

## Inspect via CLI

```bash
plotstyle info nature
plotstyle info ieee
```

## Adding a new journal

See [Contributing](../contributing.md) for instructions on adding a new
journal specification.
