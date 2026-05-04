# Warnings: `plotstyle._utils.warnings`

All warnings emitted by PlotStyle derive from `PlotStyleWarning`. Import them
from `plotstyle._utils.warnings`.

## Warning hierarchy

```
PlotStyleWarning (base)
├── FontFallbackWarning
├── OverlaySizeWarning
└── PaletteColorblindWarning
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
