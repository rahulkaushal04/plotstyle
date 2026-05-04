# Supported Journals

PlotStyle ships specifications for 10 major scientific journal publishers.
Each spec is stored as a validated TOML file and loaded on demand via the
{class}`~plotstyle.specs.SpecRegistry`.

## Overview

| Key | Journal | Publisher | Column (mm) | Min DPI | Formats |
|-----|---------|-----------|-------------|---------|---------|
| `acs` | ACS (JACS) | American Chemical Society | 82.6 / 177.8 | 300 | TIFF, EPS, PDF |
| `cell` | Cell | Cell Press | 85.0 / 174.0 | 300 | TIFF, PDF, JPEG |
| `elsevier` | Elsevier | Elsevier | 90.0 / 190.0 | 300 | TIFF, EPS, PDF |
| `ieee` | IEEE Transactions | IEEE | 88.9 / 182.0 | 300 | TIFF, EPS, PDF, PNG |
| `nature` | Nature | Springer Nature | 89.0 / 183.0 | 300 | AI †, EPS, PDF |
| `plos` | PLOS ONE | PLOS | 132.0 / 190.5 | 300 | TIFF, EPS |
| `prl` | Physical Review Letters | APS | 86.0 / 178.0 | 300 | EPS, PDF, PNG, JPG |
| `science` | Science | AAAS | 86.4 / 177.8 | 300 | AI †, EPS, PDF, TIFF |
| `springer` | Springer | Springer | - ‡ | 300 | TIFF, EPS, PDF |
| `wiley` | Wiley | Wiley | 80.0 / 180.0 | 300 | TIFF, EPS |

*Column widths listed as single / double in mm.*

## Typography

| Key | Font family | Size range (pt) | Target (pt) | Panel labels |
|-----|------------|-----------------|-------------|-------------|
| `acs` | Helvetica, Arial | 5.0 – 10.0 | - | bold lowercase |
| `cell` | Helvetica, Arial | 6.0 – 8.0 | - | bold lowercase |
| `elsevier` | Arial, Times New Roman | 8.0 – 12.0 | - | bold lowercase |
| `ieee` | Times New Roman, Helvetica, Arial | 9.0 – 10.0 | - | bold lowercase |
| `nature` | Helvetica, Arial | 5.0 – 7.0 | **7.0** | bold lowercase |
| `plos` | Arial, Times | 8.0 – 12.0 | - | bold lowercase |
| `prl` | Times New Roman, Times | 6.0 – 10.0 | - | bold lowercase |
| `science` | Minion Pro, Benton Sans Condensed | 7.5 – 10.0 | - | bold lowercase |
| `springer` | Helvetica, Arial ‡ | 6.0 – 10.0 ‡ | - | bold lowercase ‡ |
| `wiley` | Helvetica, Arial ‡ | 6.0 – 10.0 ‡ | - | bold lowercase ‡ |

The **Target** column shows the `target_font_pt` value from the spec. When set,
`plotstyle.use()` uses this as the default font size instead of the midpoint of
the range. Nature's guidelines explicitly state 7pt as the standard text size.

## Accessibility requirements

| Key | Colorblind safe | Grayscale safe | Min line weight (pt) |
|-----|----------------|----------------|---------------------|
| `acs` | - | - | 0.50 |
| `cell` | - | - | 0.50 |
| `elsevier` | - | - | 0.50 ‡ |
| `ieee` | Required | - | 0.50 ‡ |
| `nature` | - | - | 0.50 ‡ |
| `plos` | - | - | 0.57 |
| `prl` | - | - | 0.50 |
| `science` | Required | - | 0.50 ‡ |
| `springer` | - | - | 0.50 ‡ |
| `wiley` | - | - | 0.50 ‡ |

‡ Library default or not defined: the journal's public guidelines do not specify
this value. For dimension fields marked `-`, `style.figure()` will raise a
`RuntimeError` directing you to set the size manually. For typography and line
fields, PlotStyle applies conservative defaults silently. Use
`spec.is_official(field)` to check any field programmatically, or inspect
`spec.assumed_fields` for the full list.

AI (Adobe Illustrator) format is listed in the spec for journals that accept it,
but Matplotlib cannot produce `.ai` files. `export_submission()` skips AI
automatically and notes it in the output. Use a vector editor to convert from
PDF or EPS if your journal requires AI.

## Using a spec

```python
import plotstyle

# Apply a journal's style
with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)
    ax.plot([1, 2, 3])
    style.savefig(fig, "figure.pdf")
```

## Inspect a spec programmatically

```python
from plotstyle.specs import registry

spec = registry.get("ieee")
print(spec.dimensions.single_column_mm)   # 88.9
print(spec.typography.font_family)        # ['Times New Roman', 'Helvetica', 'Arial']
print(spec.export.preferred_formats)      # ['tiff', 'eps', 'pdf', 'png']
print(spec.color.grayscale_required)      # False
```

## Inspect via CLI

```bash
plotstyle info nature
plotstyle info ieee
```

## Adding a new journal

See [Contributing](../contributing.md) for instructions on adding a new
journal specification.
