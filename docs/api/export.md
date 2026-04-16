# Export — `plotstyle.core.export`

Export-safe figure saving and batch submission packaging.

## `savefig`

```{eval-rst}
.. autofunction:: plotstyle.core.export.savefig
```

## `export_submission`

```{eval-rst}
.. autofunction:: plotstyle.core.export.export_submission
```

## `FORMAT_EXTENSIONS`

```{eval-rst}
.. autodata:: plotstyle.core.export.FORMAT_EXTENSIONS
```

## Usage

### Save with journal DPI and font embedding

```python
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    ax.plot([1, 2, 3])
    style.savefig(fig, "figure.pdf")
```

`savefig()` forces TrueType font embedding (`pdf.fonttype=42`,
`ps.fonttype=42`) and applies the journal's minimum DPI. A compliance summary
is printed to stderr after each save:

```
✓ TrueType fonts embedded (pdf.fonttype=42)
✓ Resolution: 300 DPI
✓ Dimensions: 3.50in x 2.16in
✓ Saved: figure.pdf
```

### Batch export for submission

```python
plotstyle.export_submission(
    fig, "figure1",
    journal="ieee",
    author_surname="Kaushal",
    output_dir="submission_ieee",
)
```

This creates files in every format the journal accepts. For IEEE, the
author's surname is prefixed to filenames:

```
submission_ieee/
├── kaush_figure1.pdf
├── kaush_figure1.eps
├── kaush_figure1.png
└── kaush_figure1.tiff
```

### Explicit format list

Override the journal's defaults by passing `formats`:

```python
plotstyle.export_submission(
    fig, "fig2",
    formats=["pdf", "svg"],
    output_dir="output",
)
```

## Notes

- Both functions temporarily override `pdf.fonttype` and `ps.fonttype` and
  restore the originals in a `finally` block. The caller's rcParams are never
  mutated.
- If `journal` is not provided, `savefig()` still forces TrueType embedding
  but skips DPI enforcement.
- The default format when neither `journal` nor `formats` is specified is
  `["pdf"]`.
