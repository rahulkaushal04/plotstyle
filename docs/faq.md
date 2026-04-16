# FAQ & Troubleshooting

## General

### What Python versions are supported?

Python 3.10, 3.11, 3.12, and 3.13.

### Do I need to install LaTeX?

No. PlotStyle uses Matplotlib's built-in text rendering by default. LaTeX
is available as an opt-in if you have a LaTeX distribution installed, but it
is not required.

### Does PlotStyle work with Seaborn?

Yes. See the [Seaborn integration guide](guides/seaborn.md).

---

## Style & Figures

### Why do my figures look different after the `with` block ends?

`plotstyle.use()` modifies Matplotlib's `rcParams`. When the `with` block
ends, those changes are reversed. Figures created *inside* the block are not
affected — their styling is baked in at creation time. Only new figures
created *after* the block use the restored defaults.

### Can I use `plotstyle.use()` without a context manager?

Yes. Call `style.restore()` manually when you're done:

```python
style = plotstyle.use("nature")
# ... create figures ...
style.restore()
```

### What does `columns=1` vs `columns=2` mean?

- `columns=1` — single-column width (fits in one text column of the journal)
- `columns=2` — double-column / full-page width

The exact sizes in mm come from the journal spec.

### Why does `subplots()` always return a 2-D array?

Unlike `plt.subplots()`, PlotStyle's `subplots()` always returns a 2-D array
so you can use `axes[i, j]` indexing and `axes.flat` iteration for any grid
shape without special-casing single-panel or single-row layouts.

Pass `squeeze=True` to get Matplotlib-compatible behaviour — size-1 dimensions
are dropped:

```python
fig, axes = style.subplots(nrows=1, ncols=3, squeeze=True)
for ax in axes:   # 1-D array
    ax.plot([1, 2, 3])
```

---

## Palettes

### My journal isn't in the palette map. What happens?

`plotstyle.palette()` raises `SpecNotFoundError` for unrecognised journal
keys. Use `load_palette()` to access a palette directly by name:

```python
from plotstyle.color.palettes import load_palette
colors = load_palette("tol_bright")
```

### How do I check if my palette is grayscale-safe?

```python
from plotstyle.color.grayscale import is_grayscale_safe
safe = is_grayscale_safe(colors, threshold=0.1)
```

---

## Export

### Why does `savefig()` print to stderr?

The compliance summary (dimensions, DPI, font embedding) is printed to stderr
so it stays out of your script's stdout. Pass `quiet=True` to suppress it:

```python
style.savefig(fig, "fig.pdf", quiet=True)
```

### What are Type 3 fonts and why are they bad?

Type 3 fonts are bitmap fonts that many journal submission portals reject.
PlotStyle forces Type 42 (TrueType) embedding by setting `pdf.fonttype=42`
during every `savefig()` call.

### My PDF still has Type 3 fonts. Why?

This can happen if:
- You use LaTeX rendering and your LaTeX installation doesn't embed fonts.
- A third-party Matplotlib backend overrides the fonttype settings.

`plotstyle.savefig()` prints a warning if Type 3 fonts are detected in the
saved PDF.

---

## Validation

### What does `WARN` vs `FAIL` mean?

- **FAIL** — the criterion was not met; the figure is likely to be rejected.
- **WARN** — advisory; could not be verified conclusively.

Only `FAIL` results affect `report.passed`.

### Can I skip specific checks?

Not via the public `validate()` API. All registered checks run in one pass.

---

## Migration

### Does `migrate()` modify my figure permanently?

Yes. `migrate()` mutates the figure in-place. Clone it first if you need to
keep the original:

```python
import copy
fig_copy = copy.deepcopy(fig)
plotstyle.migrate(fig_copy, from_journal="nature", to_journal="ieee")
```

---

## Build errors

### Sphinx build fails with "module not found"

The package must be installed before building docs:

```bash
pip install -e ".[docs]"
hatch run docs:build
```
