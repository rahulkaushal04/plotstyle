# Export & Submission

This guide covers exporting figures for journal submission — from single-file
saves to full multi-format submission packages.

## Single-file export

`plotstyle.savefig()` is a drop-in replacement for `fig.savefig()` with two
safety features baked in:

```python
import plotstyle

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
    ax.plot([1, 2, 3])
    plotstyle.savefig(fig, "figure1.pdf", journal="nature")
```

### What `savefig()` does differently

1. **Forces TrueType font embedding** — sets `pdf.fonttype=42` and
   `ps.fonttype=42`, preventing Type 3 fonts that journal portals reject.
2. **Enforces journal DPI** — when `journal` is specified, the spec's
   `min_dpi` is applied automatically.
3. **Prints compliance summary** to stderr:

```
✓ TrueType fonts embedded (pdf.fonttype=42)
✓ Resolution: 300 DPI
✓ Dimensions: 3.50in × 2.16in
✓ Saved: figure1.pdf
```

Both overrides are scoped to the single save call — your rcParams are restored
afterwards.

### Without a journal

You can still use `savefig()` without specifying a journal to get TrueType
embedding without DPI enforcement:

```python
plotstyle.savefig(fig, "figure.pdf")
```

## Batch submission export

`plotstyle.export_submission()` exports a figure in every format the journal
accepts:

```python
paths = plotstyle.export_submission(
    fig, "figure1",
    journal="nature",
    output_dir="submission_nature",
)
# paths = [Path('submission_nature/figure1.tiff'),
#          Path('submission_nature/figure1.pdf'),
#          Path('submission_nature/figure1.eps')]
```

### IEEE filename convention

IEEE requires filenames prefixed with the first 5 characters of the author's
surname:

```python
plotstyle.export_submission(
    fig, "figure1",
    journal="ieee",
    author_surname="Kaushal",
    output_dir="submission_ieee",
)
# Creates: kaush_figure1.pdf, kaush_figure1.eps, etc.
```

### Custom format list

Override the journal defaults:

```python
plotstyle.export_submission(
    fig, "figure1",
    formats=["pdf", "svg"],
    output_dir="output",
)
```

### Format priority

1. Explicit `formats` argument (highest priority)
2. Journal spec's `preferred_formats` list
3. `["pdf"]` fallback

## Supported formats

| Format | Extension | Notes |
|--------|-----------|-------|
| `pdf` | `.pdf` | Vector; most journals accept this |
| `eps` | `.eps` | Vector; required by some physics journals |
| `tiff` | `.tiff` | Raster; common in biology journals |
| `png` | `.png` | Raster; screen/web use |
| `svg` | `.svg` | Vector; web/interactive |
| `jpg` | `.jpg` | Raster; rarely required |
| `ps` | `.ps` | PostScript; legacy format |

## Complete workflow

```python
import numpy as np
import plotstyle

with plotstyle.use("ieee"):
    fig, ax = plotstyle.figure("ieee")
    x = np.linspace(0, 10, 100)
    styled = plotstyle.palette("ieee", n=3, with_markers=True)

    for i, (c, ls, m) in enumerate(styled):
        ax.plot(x, np.sin(x + i), color=c, linestyle=ls,
                marker=m, markevery=15, label=f"Series {i+1}")
    ax.legend()
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal (a.u.)")

    # Validate first
    report = plotstyle.validate(fig, journal="ieee")
    assert report.passed, report.failures

    # Export for submission
    plotstyle.export_submission(
        fig, "signal_plot",
        journal="ieee",
        author_surname="Kaushal",
        output_dir="submission_ieee",
    )
```
