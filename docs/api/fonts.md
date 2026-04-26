# Font Engine: `plotstyle.engine.fonts`

Font detection, selection, and PDF font-embedding verification.

## `detect_available`

```{eval-rst}
.. autofunction:: plotstyle.engine.fonts.detect_available
```

## `select_best`

```{eval-rst}
.. autofunction:: plotstyle.engine.fonts.select_best
```

## `check_overlay_fonts`

```{eval-rst}
.. autofunction:: plotstyle.engine.fonts.check_overlay_fonts
```

## `verify_embedded`

```{eval-rst}
.. autofunction:: plotstyle.engine.fonts.verify_embedded
```

## Usage

### Check which journal fonts are installed

```python
from plotstyle.engine.fonts import detect_available

installed = detect_available(["Helvetica", "Arial", "DejaVu Sans"])
print(installed)  # e.g. ['Arial', 'DejaVu Sans']
```

### Select the best font for a journal

`select_best()` walks the journal's font preference list and returns the
first installed match, or falls back to the generic family:

```python
from plotstyle.specs import registry
from plotstyle.engine.fonts import select_best

spec = registry.get("nature")
font_name, is_exact = select_best(spec)
print(f"Selected: {font_name}, exact match: {is_exact}")
# e.g. Selected: Arial, exact match: True
```

When the preferred font is not found, a
`FontFallbackWarning` is emitted.

### Check fonts for a script overlay

Script overlays (CJK, Russian, Turkish) require specific fonts. Use
`check_overlay_fonts()` to verify installation:

```python
from plotstyle.overlays import overlay_registry
from plotstyle.engine.fonts import check_overlay_fonts

ov = overlay_registry.get("cjk-japanese")
status = check_overlay_fonts(ov)
for font, installed in status.items():
    print(f"  {font}: {'installed' if installed else 'MISSING'}")
```

This is the same check the CLI runs with `plotstyle fonts --overlay cjk-japanese`.

### Verify PDF font embedding

After saving a figure, check that no Type 3 (bitmap) fonts slipped through:

```python
from pathlib import Path
from plotstyle.engine.fonts import verify_embedded

issues = verify_embedded(Path("figure.pdf"))
if issues:
    print("Type 3 fonts detected: journal portal may reject this file.")
else:
    print("No Type 3 fonts found: TrueType embedding OK.")
```

## Notes

- Font detection uses Matplotlib's `FontManager`. Results depend on which
  fonts are installed on the current system.
- `verify_embedded()` uses a heuristic byte-level scan of the PDF file. It
  detects the most common Type 3 patterns but is not a full PDF parser.
- The CLI commands `plotstyle fonts --journal <journal>` and
  `plotstyle fonts --overlay <overlay>` wrap these functions.
