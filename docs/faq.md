# FAQ & Troubleshooting

## General

### What Python versions are supported?

Python 3.10, 3.11, 3.12, and 3.13.

### Do I need to install LaTeX?

No. PlotStyle uses Matplotlib's built-in text rendering by default. LaTeX
rendering is available as an opt-in feature if you have a LaTeX distribution
installed, but it is not required.

### Does PlotStyle work with Seaborn?

Yes. See the [Seaborn integration guide](guides/seaborn.md) for details on
preventing `sns.set_theme()` from overriding PlotStyle's settings.

## Style & Figures

### Why do my figures look different after exiting the `with` block?

`plotstyle.use()` modifies Matplotlib's `rcParams`. When used as a context
manager, the original values are restored on exit. Figures created inside the
block are not affected — their styling is baked in at creation time. Only
*new* figures created after the block use the restored defaults.

### Can I use `plotstyle.use()` without a context manager?

Yes. Call `style.restore()` manually when you're done:

```python
style = plotstyle.use("nature")
# ... create figures ...
style.restore()
```

### What does `columns=1` vs `columns=2` mean?

- `columns=1` — single-column width (fits in one text column of the journal
  page)
- `columns=2` — double-column / full-text width (spans the entire page width)

The exact widths in mm come from the journal spec.

### Why does `subplots()` always return a 2-D array?

This is intentional. Unlike `plt.subplots()`, PlotStyle's `subplots()` always
returns axes as a `(nrows, ncols)` ndarray so you can consistently use
`axes[i, j]` indexing and `axes.flat` iteration without special-casing the
single-panel case. Access a single axes with `axes[0, 0]`.

## Palettes

### My journal isn't in the palette map. What happens?

`plotstyle.palette()` raises
{class}`~plotstyle.color.palettes.UnknownJournalError` for unrecognised
journal keys. Use `load_palette()` to access palettes directly by name:

```python
from plotstyle.color.palettes import load_palette
colors = load_palette("tol_bright")
```

### How do I check if my palette is grayscale-safe?

```python
from plotstyle.color.grayscale import is_grayscale_safe
safe = is_grayscale_safe(colors, threshold=0.1)
```

## Export

### Why does `savefig()` print to stderr?

The compliance summary (dimensions, DPI, font embedding) is intentionally
printed to stderr to support CI pipelines and interactive workflows. Redirect
stderr to suppress it:

```python
import sys, os
with open(os.devnull, "w") as devnull:
    old_stderr = sys.stderr
    sys.stderr = devnull
    plotstyle.savefig(fig, "fig.pdf", journal="nature")
    sys.stderr = old_stderr
```

### What are Type 3 fonts and why are they bad?

Type 3 fonts are device-dependent bitmap fonts that many journal submission
portals reject. PlotStyle forces Type 42 (TrueType) embedding by setting
`pdf.fonttype=42` and `ps.fonttype=42` during every `savefig()` call.

### My PDF still has Type 3 fonts. Why?

This can happen if:
- You use LaTeX rendering and your LaTeX installation doesn't embed fonts
  properly.
- A third-party Matplotlib backend overrides the fonttype settings.

After saving, `plotstyle.savefig()` automatically prints a warning to stderr
if Type 3 fonts are detected in the saved PDF. Inspect the output to confirm.

## Validation

### What does `WARN` vs `FAIL` mean?

- **FAIL** — the check criterion was not met; the figure is likely to be
  rejected
- **WARN** — the check is advisory or could not be verified conclusively

Only `FAIL` results affect `report.passed`. A report with warnings but no
failures is still considered passing.

### Can I skip specific checks?

Not via the public `validate()` API. All registered checks run in one pass.
For selective validation, use the internal check registry:

```python
from plotstyle.validation.checks._base import get_registered_checks
from plotstyle.validation.checks import run_all
```

## Migration

### Does `migrate()` modify my figure permanently?

Yes. `migrate()` mutates the figure in-place. If you need to preserve the
original, clone it first:

```python
import copy
fig_copy = copy.deepcopy(fig)
plotstyle.migrate(fig_copy, from_journal="nature", to_journal="ieee")
```

## Build errors

### Sphinx build fails with "module not found"

The package must be installed before building docs. On Read the Docs this
happens automatically via `.readthedocs.yaml`. Locally:

```bash
pip install -e ".[docs]"
hatch run docs:build
```
