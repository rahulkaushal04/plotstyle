# Core Concepts

This page explains the key ideas behind PlotStyle so you understand *why*
things work the way they do, not just *how* to call the functions.

## Journal specifications (specs)

Every journal has specific rules for figure submissions: column widths in mm,
allowed fonts and size ranges, minimum DPI, preferred export formats, and
accessibility requirements.

PlotStyle stores these rules as **TOML files** inside the `plotstyle/specs/`
directory. Each file is parsed into a frozen, immutable
{class}`~plotstyle.specs.schema.JournalSpec` dataclass with typed sub-specs:

| Sub-spec | What it describes |
|----------|-------------------|
| `metadata` | Journal name, publisher, source URL, last verified date |
| `dimensions` | Single/double column widths (mm), max height (mm) |
| `typography` | Font family, size range (pt), panel label style |
| `export` | Preferred formats, min DPI, colour space, font embedding |
| `color` | Colour avoidance rules, colorblind/grayscale requirements |
| `line` | Minimum stroke weight (pt) |

You rarely interact with specs directly — calling `plotstyle.use("nature")`
triggers the chain automatically. But you can inspect them:

```python
from plotstyle.specs import registry

spec = registry.get("nature")
print(spec.dimensions.single_column_mm)  # 89.0
print(spec.typography.font_family)       # ['Helvetica', 'Arial']
print(spec.export.min_dpi)               # 300
```

## The spec registry

The {class}`~plotstyle.specs.SpecRegistry` lazily loads and caches specs from
disk. The module-level `registry` singleton is used by the entire library:

```python
from plotstyle.specs import registry

registry.list_available()
# ['acs', 'cell', 'elsevier', 'ieee', 'nature', 'plos', 'prl', 'science', 'springer', 'wiley']
```

Journal names are **case-insensitive**: `"Nature"`, `"NATURE"`, and `"nature"`
all resolve to the same spec.

## Style application and restoration

`plotstyle.use()` takes a snapshot of the Matplotlib `rcParams` keys it
modifies, then applies the journal's rcParams. The returned
{class}`~plotstyle.core.style.JournalStyle` handle stores this snapshot and
can restore it:

```
                    ┌──────────┐
mpl.rcParams ──────│ snapshot  │
                    └──────────┘
                         │
                    ┌──────────┐
                    │  apply   │── journal rcParams active
                    └──────────┘
                         │
                    ┌──────────┐
                    │ restore  │── original rcParams restored
                    └──────────┘
```

The snapshot is **surgical** — only the keys that PlotStyle touches are saved
and restored. Any unrelated rcParam changes you make before or during the block
are preserved.

## Figure sizing

`plotstyle.figure()` and `plotstyle.subplots()` resolve the journal's
column width from the spec, convert from millimetres to inches, and pass
the result as `figsize` to Matplotlib.

- `columns=1` → single-column width (e.g. 89 mm for Nature)
- `columns=2` → double-column / full-text width (e.g. 183 mm for Nature)
- The default aspect ratio is the **golden ratio** (φ ≈ 1.618). Override it
  with the `aspect` parameter.

## Palettes

`plotstyle.palette()` maps each journal to a curated, colorblind-safe palette:

| Journal | Default palette |
|---------|----------------|
| nature, plos, cell | Okabe–Ito |
| acs, elsevier, springer | Tol Bright |
| prl, wiley | Tol Muted |
| science | Tol Vibrant |
| ieee | Safe Grayscale |

Palettes **cycle** automatically if you request more colours than the palette
contains.

## Validation

`plotstyle.validate()` runs every registered check function against a figure
and returns a {class}`~plotstyle.validation.report.ValidationReport`. Checks
cover:

- **Dimensions** — width and height against the journal's allowed ranges
- **Typography** — font sizes within min/max bounds
- **Lines** — stroke weights above journal minimum
- **Colours** — avoided combinations, colorblind safety, grayscale compliance
- **Export** — DPI and format requirements

Each failed check includes a `fix_suggestion` string telling you exactly how
to fix the problem.

## Export safety

`plotstyle.savefig()` wraps `Figure.savefig()` with two guarantees:

1. **TrueType font embedding** — `pdf.fonttype` and `ps.fonttype` are set to
   `42` for the duration of the save, preventing Type 3 fonts that most
   submission portals reject.
2. **Journal DPI enforcement** — when a journal is specified, its `min_dpi` is
   applied automatically.

Both overrides are scoped to the single save call and restored afterwards.

## Migration

`plotstyle.migrate()` re-styles an existing figure for a different journal. It:

1. Applies the target journal's rcParams
2. Resizes the figure to the target's single-column width (preserving aspect
   ratio)
3. Rescales all text artists proportionally, clamping to the target's allowed
   font-size range

Use `plotstyle.diff()` first to see exactly what changes between two journals:

```python
result = plotstyle.diff("nature", "ieee")
print(result)
```
