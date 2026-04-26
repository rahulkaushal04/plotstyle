# Export & Submission

How to save figures for journal submission: from a single file to a full
multi-format submission package.

## Single-file export

`plotstyle.savefig()` is a drop-in replacement for `fig.savefig()`:

```python
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    ax.plot([1, 2, 3])
    style.savefig(fig, "figure1.pdf")
```

It automatically:

1. **Embeds TrueType fonts**: sets `pdf.fonttype=42` and `ps.fonttype=42`,
   preventing Type 3 fonts that journal portals often reject.
2. **Enforces DPI**: uses the journal's minimum DPI when `journal` is set.
3. **Prints a compliance summary** to stderr:

```
✓ TrueType fonts embedded (pdf.fonttype=42)
✓ Resolution: 300 DPI
✓ Dimensions: 3.50in x 2.16in
✓ Saved: figure1.pdf
```

Pass `quiet=True` to suppress this output in scripts or batch loops.

### Save without a journal

You can use `savefig()` without a journal to get TrueType embedding only:

```python
plotstyle.savefig(fig, "figure.pdf")
```

## Batch submission export

`plotstyle.export_submission()` saves a figure in every format the journal
accepts:

```python
paths = plotstyle.export_submission(
    fig, "figure1",
    journal="nature",
    output_dir="submission_nature",
)
# paths = [Path('submission_nature/figure1.eps'),
#          Path('submission_nature/figure1.pdf')]
# Note: Nature also accepts AI (Adobe Illustrator) files, but Matplotlib
# cannot produce them. The AI format is skipped with a note in the output.
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
# Creates: submission_ieee/kaush_figure1.pdf, kaush_figure1.eps, etc.
```

### Override the format list

```python
plotstyle.export_submission(
    fig, "figure1",
    formats=["pdf", "svg"],
    output_dir="output",
)
```

### Format priority

1. Explicit `formats` argument (highest)
2. Journal spec's `preferred_formats`
3. `["pdf"]` fallback

## Supported formats

| Format | Extension | Notes |
|--------|-----------|-------|
| `pdf` | `.pdf` | Vector; accepted by most journals |
| `eps` | `.eps` | Vector; required by some physics journals |
| `tiff` | `.tiff` | Raster; common in biology journals |
| `tif` | `.tif` | Alias for `tiff` |
| `png` | `.png` | Raster; web/screen use |
| `svg` | `.svg` | Vector; web/interactive |
| `jpg` | `.jpg` | Raster; rarely required |
| `jpeg` | `.jpeg` | Alias for `jpg` |
| `ps` | `.ps` | PostScript; legacy |
| `ai` | `.ai` | Adobe Illustrator; accepted by Nature and Science but skipped during export (requires external tool) |

## Complete workflow

```python
import numpy as np
import plotstyle

with plotstyle.use("ieee") as style:
    fig, ax = style.figure()
    x = np.linspace(0, 10, 100)
    styled = style.palette(n=3, with_markers=True)

    for i, (c, ls, m) in enumerate(styled):
        ax.plot(x, np.sin(x + i), color=c, linestyle=ls,
                marker=m, markevery=15, label=f"Series {i+1}")
    ax.legend()
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal (a.u.)")

    # Validate first
    report = style.validate(fig)
    assert report.passed, report.failures

    # Export for submission
    style.export_submission(
        fig, "signal_plot",
        author_surname="Kaushal",
        output_dir="submission_ieee",
    )
```
