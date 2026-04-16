# Core Concepts

A short explanation of how PlotStyle works and why it's designed this way.

## Journal specs

Every journal has rules for figures: column widths, allowed fonts, minimum
DPI, export formats, and accessibility requirements.

PlotStyle stores these rules as TOML files inside the package. Each file is
parsed into a {class}`~plotstyle.specs.schema.JournalSpec` dataclass with
typed sub-specs:

| Sub-spec | What it covers |
|----------|----------------|
| `metadata` | Journal name, publisher, source URL |
| `dimensions` | Column widths (mm), max height (mm) |
| `typography` | Font family, size range (pt), panel label style |
| `export` | Preferred formats, min DPI, colour space |
| `color` | Colorblind/grayscale requirements, avoided combinations |
| `line` | Minimum stroke weight (pt) |

You usually don't interact with specs directly — `plotstyle.use("nature")`
handles everything automatically. But you can inspect them:

```python
from plotstyle.specs import registry

spec = registry.get("nature")
print(spec.dimensions.single_column_mm)  # 89.0
print(spec.typography.font_family)       # ['Helvetica', 'Arial']
print(spec.export.min_dpi)               # 300
```

## The spec registry

The {class}`~plotstyle.specs.SpecRegistry` loads and caches specs on demand.
The `registry` singleton is used by the whole library:

```python
from plotstyle.specs import registry

registry.list_available()
# ['acs', 'cell', 'elsevier', 'ieee', 'nature', 'plos', 'prl', 'science', 'springer', 'wiley']
```

Journal names are **case-insensitive**: `"Nature"`, `"NATURE"`, and `"nature"`
all work.

## How style application works

`plotstyle.use()` does three things:

1. Looks up the journal spec from the registry
2. Saves the current Matplotlib rcParams values it's about to change
3. Applies the journal's rcParams

The {class}`~plotstyle.core.style.JournalStyle` handle stores the saved values
and can restore them — either when you call `style.restore()` or automatically
when the `with` block ends.

Only the keys PlotStyle actually changes are saved. Any other rcParam changes
you make are untouched.

## Figure sizing

`plotstyle.figure()` and `plotstyle.subplots()` look up the journal's column
width, convert from millimetres to inches, and create a Matplotlib figure at
that exact size.

- `columns=1` → single-column width (e.g. 89 mm for Nature)
- `columns=2` → double-column / full-text width (e.g. 183 mm for Nature)

The default aspect ratio is the **golden ratio** (≈ 1.618). Override it with
the `aspect` parameter.

## Palettes

`plotstyle.palette()` maps each journal to a colorblind-safe palette:

| Journal | Palette |
|---------|---------|
| Nature, PLOS, Cell | Okabe–Ito |
| ACS, Elsevier, Springer | Tol Bright |
| PRL, Wiley | Tol Muted |
| Science | Tol Vibrant |
| IEEE | Safe Grayscale |

Palettes cycle automatically if you request more colours than the palette
contains.

## Validation

`plotstyle.validate()` runs a set of checks against your figure and returns a
{class}`~plotstyle.validation.report.ValidationReport`. Checks cover:

- **Dimensions** — width and height vs. journal limits
- **Typography** — font sizes within allowed range
- **Lines** — stroke weights above journal minimum
- **Colours** — avoided combinations, colorblind/grayscale compliance
- **Export** — DPI and font embedding

Each failed check includes a `fix_suggestion` so you know exactly what to fix.

## Export safety

`plotstyle.savefig()` wraps `Figure.savefig()` with two guarantees:

1. **TrueType font embedding** — `pdf.fonttype` and `ps.fonttype` are set to
   `42`, preventing Type 3 fonts that most journal portals reject.
2. **Journal DPI enforcement** — when a journal is specified, its minimum DPI
   is applied automatically.

Both settings are scoped to the single save call and restored afterwards.

## Migration

`plotstyle.migrate()` re-styles an existing figure for a different journal:

1. Applies the target journal's rcParams
2. Resizes the figure to the target journal's column width (keeping aspect ratio)
3. Rescales all text proportionally, clamping to the target's font-size range

Use `plotstyle.diff()` first to see what changes between two journals:

```python
result = plotstyle.diff("nature", "ieee")
print(result)
```
