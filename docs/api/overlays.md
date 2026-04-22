# Overlays — `plotstyle.overlays`

Style overlay registry and data types.

## `OverlayRegistry`

```{eval-rst}
.. autoclass:: plotstyle.overlays.OverlayRegistry
   :members:
```

## `OverlayNotFoundError`

```{eval-rst}
.. autoexception:: plotstyle.overlays.OverlayNotFoundError
   :members:
```

## `StyleOverlay`

```{eval-rst}
.. autoclass:: plotstyle.overlays.StyleOverlay
   :members:
```

## `overlay_registry`

```{eval-rst}
.. autodata:: plotstyle.overlays.overlay_registry
```

## `list_overlays`

```{eval-rst}
.. autofunction:: plotstyle.list_overlays
```

## Usage

### List all overlays

```python
import plotstyle

plotstyle.list_overlays()
# ['bar', 'cjk-japanese', 'cjk-korean', 'cjk-simplified', ...]

plotstyle.list_overlays(category="context")
# ['high-vis', 'minimal', 'notebook', 'presentation']
```

### Inspect an overlay

```python
ov = plotstyle.overlay_registry.get("notebook")
print(ov.key)          # "notebook"
print(ov.name)         # "Notebook"
print(ov.category)     # "context"
print(ov.description)  # "Enlarged figures and larger fonts for ..."
print(ov.rcparams)     # {'figure.figsize': [8.0, 5.5], 'font.size': 14.0, ...}
```

### Check if an overlay exists

```python
"minimal" in plotstyle.overlay_registry   # True
"unknown" in plotstyle.overlay_registry   # False
```

### Handle a missing overlay

```python
from plotstyle.overlays import OverlayNotFoundError

try:
    plotstyle.overlay_registry.get("unknown")
except OverlayNotFoundError as exc:
    print(exc.name)       # "unknown"
    print(exc.available)  # ['bar', 'grid', 'minimal', ...]
```

## Notes

- Overlay keys are **case-insensitive**: `"Notebook"` and `"notebook"` both
  resolve to `notebook.toml`.
- TOML files starting with `_` are private and excluded from
  `list_available()`.
- Overlays are loaded lazily on first access and cached for subsequent lookups.
- `overlay_registry.clear_cache()` discards all cached overlays and forces
  re-reads from disk on the next access.
