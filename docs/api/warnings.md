# Warnings: `plotstyle._utils.warnings`

All warnings emitted by PlotStyle derive from `PlotStyleWarning`. Import them
from `plotstyle._utils.warnings`; `SpecAssumptionWarning` is also available
as `plotstyle.specs.SpecAssumptionWarning`.

## Warning hierarchy

```
PlotStyleWarning (base)
├── FontFallbackWarning
├── OverlaySizeWarning
├── PaletteColorblindWarning
└── SpecAssumptionWarning
```

## Classes

### `PlotStyleWarning`

Base class for all PlotStyle warnings. Filter the entire family with:

```python
import warnings
from plotstyle._utils.warnings import PlotStyleWarning

warnings.filterwarnings("ignore", category=PlotStyleWarning)
```

### `FontFallbackWarning`

Emitted when a journal's preferred font is not installed and PlotStyle falls
back to the next entry in the font list or to the generic family.

```python
import warnings
from plotstyle._utils.warnings import FontFallbackWarning

with warnings.catch_warnings():
    warnings.simplefilter("error", FontFallbackWarning)
    plotstyle.use("nature")  # raises if preferred font is missing
```

### `OverlaySizeWarning`

Emitted when a context overlay's `figure.figsize` width exceeds the active
journal's double-column width. Expected when using `notebook` or
`presentation` with a journal preset.

### `PaletteColorblindWarning`

Emitted when the `safe-grayscale` color overlay is combined with a journal
that requires colorblind-safe colors (e.g. `ieee`, `science`).

### `SpecAssumptionWarning`

Emitted when a journal spec is missing fields (e.g. font sizes, line weights)
and PlotStyle applies conservative library defaults in their place. The
warning message lists the affected fields and links to the journal's official
guidelines.

```python
import warnings
from plotstyle._utils.warnings import SpecAssumptionWarning

# Suppress the warning if you know your chosen values are acceptable
warnings.filterwarnings("ignore", category=SpecAssumptionWarning)
```

You can check which fields were assumed programmatically:

```python
from plotstyle.specs import registry

spec = registry.get("wiley")
print(spec.assumed_fields)
# frozenset({'typography.font_family', 'typography.min_font_pt', ...})

spec.is_official("dimensions.single_column_mm")  # True: from official guidelines
spec.is_official("typography.min_font_pt")        # False: library default
```
