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

You usually don't interact with specs directly; `plotstyle.use("nature")`
handles everything automatically. But you can inspect them:

```python
from plotstyle.specs import registry

spec = registry.get("nature")
print(spec.dimensions.single_column_mm)  # 89.0
print(spec.typography.font_family)       # ['Helvetica', 'Arial']
print(spec.export.min_dpi)               # 300
```

### Incomplete specs and library defaults

Some journals do not publish complete figure guidelines; for example, they may
specify column widths and export formats but leave font sizes and line weights
undefined.

When a spec is missing these fields, PlotStyle applies conservative
**library defaults** and emits a `SpecAssumptionWarning`
listing the affected fields:

```
SpecAssumptionWarning: "Wiley" has no official values for dimensions.max_height_mm,
line.min_weight_pt, typography.font_family, typography.max_font_pt,
typography.min_font_pt; plotstyle defaults will be used.
```

You can inspect which fields are library-assumed at any time:

```python
import warnings
from plotstyle._utils.warnings import SpecAssumptionWarning
from plotstyle.specs import registry

spec = registry.get("wiley")

# Set of dot-notation paths that used library defaults
print(spec.assumed_fields)
# frozenset({'dimensions.max_height_mm', 'line.min_weight_pt', 'typography.font_family', 'typography.min_font_pt', 'typography.max_font_pt'})

# Check a specific field
spec.is_official("typography.min_font_pt")  # False: Wiley doesn't define this
spec.is_official("dimensions.single_column_mm")  # True: from the official guidelines

# Suppress the warning if you know what you're doing
warnings.filterwarnings("ignore", category=SpecAssumptionWarning)
```

**Dimensions** are treated differently from typography and line fields. When a
journal does not publish column widths (e.g. Springer), the dimension fields are
set to ``None`` and calling ``style.figure(columns=1)`` raises a ``RuntimeError``
with a clear message. All other style settings (fonts, DPI, export formats) still
work normally. Use ``spec.is_official("dimensions.single_column_mm")`` to check
before calling ``figure()``, or pass an explicit ``figsize`` to ``plt.subplots``.

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

`plotstyle.use()` accepts either a single journal key (`"nature"`) or a list
that may include one journal key and any number of overlay keys
(`["nature", "minimal", "tol-bright"]`).  It then:

1. Looks up the journal spec from the registry (if a journal key is present)
2. Saves the current Matplotlib rcParams values it's about to change
3. Applies the journal's base rcParams
4. Applies each overlay's rcParams in list order, with later overlays winning
   on any key conflict

The {class}`~plotstyle.core.style.JournalStyle` handle stores the saved values
and can restore them, either when you call `style.restore()` or automatically
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

- **Dimensions**: width and height vs. journal limits
- **Typography**: font sizes within allowed range
- **Lines**: stroke weights above journal minimum
- **Colours**: avoided combinations, colorblind/grayscale compliance
- **Export**: DPI and font embedding

Each failed check includes a `fix_suggestion` so you know exactly what to fix.

## Export safety

`plotstyle.savefig()` wraps `Figure.savefig()` with two guarantees:

1. **TrueType font embedding**: `pdf.fonttype` and `ps.fonttype` are set to
   `42`, preventing Type 3 fonts that most journal portals reject.
2. **Journal DPI enforcement**: when a journal is specified, its minimum DPI
   is applied automatically.

Both settings are scoped to the single save call and restored afterwards.

## Overlays

Overlays are additive rcParam patches that layer on top of a journal preset.
They let you adjust one aspect of a figure without changing the base journal
settings.

```python
# Apply Nature's journal settings, then layer the "minimal" overlay on top
with plotstyle.use(["nature", "minimal"]) as style:
    fig, ax = style.figure(columns=1)
```

Overlay categories:

| Category | Purpose | Examples |
|----------|---------|---------|
| `color` | Swap the default colour cycle | `okabe-ito`, `tol-bright`, `tol-vibrant`, `tol-muted`, `tol-light`, `tol-high-contrast`, `tol-rainbow-4/6/8/10/12`, `safe-grayscale` |
| `context` | Adjust scale for the medium | `notebook`, `presentation`, `minimal`, `high-vis` |
| `rendering` | Control LaTeX and grid rendering | `no-latex`, `grid`, `latex-sans`, `pgf` |
| `plot-type` | Optimise for a specific chart type | `bar`, `scatter` |
| `script` | Font support for non-Latin text | `cjk-simplified`, `russian`, `turkish` |

List all available overlays:

```python
plotstyle.list_overlays()                    # all overlays
plotstyle.list_overlays(category="context")  # filter by category
```

---

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

## Matplotlib native style integration

At import time, PlotStyle registers all journal presets and overlays as native
Matplotlib styles under a `"plotstyle."` prefix.  This lets you use them with
Matplotlib's built-in style API:

```python
import matplotlib.pyplot as plt

plt.style.use("plotstyle.nature")
plt.style.use(["plotstyle.nature", "plotstyle.notebook"])

with plt.style.context("plotstyle.ieee"):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])

# Discover all registered styles
[s for s in plt.style.available if s.startswith("plotstyle.")]
```

Registered styles are rcParam-only snapshots built without LaTeX (`latex=False`).
For validation, export, and journal-aware figure sizing, use `plotstyle.use()`
instead; the native style integration is for quick exploration only.
