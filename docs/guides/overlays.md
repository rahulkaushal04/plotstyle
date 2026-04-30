# Overlays

How to combine journal presets with overlays to fine-tune your figures.

See the working example: [`examples/12_overlays.py`](../../examples/12_overlays.py)

## What overlays are

Overlays are additive rcParam patches that layer on top of a journal preset
(or on their own, without any journal). They let you adjust one aspect of the
figure (the color palette, the scale, the plot type) without touching the
base journal settings.

Pass overlay names in the same list as the journal key:

```python
import plotstyle

with plotstyle.use(["nature", "minimal"]) as style:
    fig, ax = style.figure(columns=1)
    ax.plot([1, 2, 3])
    style.savefig(fig, "figure.pdf")
```

Overlays are applied in list order. If two overlays set the same rcParam, the
last one wins.

## Overlay categories

| Category | Purpose | Examples |
|----------|---------|---------|
| `color` | Change the default color cycle | `okabe-ito`, `tol-bright`, `tol-vibrant`, `tol-muted`, `tol-light`, `tol-high-contrast`, `tol-rainbow-4/6/8/10/12`, `safe-grayscale` |
| `context` | Adjust scale for a different medium | `notebook`, `presentation`, `minimal`, `high-vis` |
| `rendering` | Control text rendering and grids | `no-latex`, `grid`, `latex-sans`, `pgf` |
| `plot-type` | Optimise for a chart type | `bar`, `scatter` |
| `script` | Font support for non-Latin text | `cjk-japanese`, `russian`, `turkish` |

## Context overlays

### `minimal`: clean editorial look

Removes the top and right spines and hides the grid. Useful for blog posts,
editorial figures, or any context where heavy axis boxes look out of place.

```python
with plotstyle.use(["nature", "minimal"]) as style:
    fig, ax = style.figure(columns=1)
    ax.plot(x, y)
    style.savefig(fig, "figure.pdf")
```

### `notebook`: Jupyter scale

Sets `figure.figsize` to 8 x 5.5 in and increases font sizes to 14 pt for
on-screen readability in Jupyter notebooks.

Because `style.figure()` always uses journal column dimensions, use
`plt.subplots()` to let the overlay's figsize apply:

```python
import matplotlib.pyplot as plt

with plotstyle.use(["nature", "notebook"]) as style:
    fig, ax = plt.subplots()   # uses notebook's 8x5.5 in figsize
    ax.plot(x, y)
    fig.savefig("notebook_figure.png", dpi=150)
```

> **Note:** An `OverlaySizeWarning` is raised when using `notebook` with a
> journal preset because 8 in exceeds most journal double-column widths. This
> is expected; the notebook overlay is for interactive exploration, not
> submission.

### `presentation`: slides and posters

Similar to `notebook` but scaled for projected displays: 10 x 7 in,
20 pt font, thick lines.

### `high-vis`: projectors

Maximum contrast, bold lines, and oversized ticks for projected figures where
fine detail is lost.

## Rendering overlays

### `no-latex`

Forces Matplotlib's built-in MathText renderer, disabling LaTeX even when
the journal preset would enable it:

```python
with plotstyle.use(["nature", "no-latex"]) as style:
    fig, ax = style.figure()
    ax.plot(x, y)
```

### `grid`

Enables subtle dashed major grid lines (`alpha=0.3`):

```python
with plotstyle.use(["nature", "grid"]) as style:
    fig, ax = style.figure()
    ax.plot(x, y)
```

### `latex-sans`

Enables LaTeX rendering with a sans-serif font family
(`\usepackage{helvet}`). Emits a warning when used with a journal that
specifies a serif font:

```python
with plotstyle.use(["science", "latex-sans"]) as style:
    fig, ax = style.figure()
    ax.plot(x, y)
```

### `pgf`

Activates the PGF LaTeX backend for publication-quality vector output.
PlotStyle calls `plt.switch_backend("pgf")` automatically. Must be applied
before any figures are drawn:

```python
with plotstyle.use(["nature", "pgf"]) as style:
    fig, ax = style.figure()
    ax.plot(x, y)
    fig.savefig("figure.pgf")
```

> **Note:** Only one rendering overlay takes effect; if you pass multiple
> rendering overlays in a single list, the last one wins and a
> `PlotStyleWarning` is emitted.

## Plot-type overlays

### `bar`

Removes markers and sets a 0.5 pt patch border, standard for bar charts in
most journals:

```python
with plotstyle.use(["nature", "bar"]) as style:
    fig, ax = style.figure(columns=1)
    ax.bar(categories, values, color=style.palette(n=len(categories)))
    style.savefig(fig, "bar_figure.pdf")
```

### `scatter`

Enables markers, removes connecting lines, and turns on the grid, a good
starting point for scatter plots:

```python
with plotstyle.use(["nature", "scatter"]) as style:
    fig, ax = style.figure(columns=1)
    ax.scatter(x, y)
    style.savefig(fig, "scatter_figure.pdf")
```

> **Warning:** Combining `scatter` with the `ieee` journal emits a `PlotStyleWarning`
> because it sets `lines.linestyle='none'`, removing the line style differentiation
> that IEEE figures rely on for print accessibility. Use `style.palette(n=..., with_markers=True)`
> to restore per-series distinction via marker shapes. The same warning applies when
> combining `scatter` with the `safe-grayscale` overlay.

## Script overlays

Script overlays configure fonts for non-Latin text. They set `font.family`
to a prioritised list of installed fonts and, when LaTeX is active, append
the appropriate `\usepackage` lines to `text.latex.preamble`.

If none of the required fonts are installed, PlotStyle emits a
`FontFallbackWarning` and non-Latin characters may render as boxes.

Available script overlays:

| Key | Language | Primary fonts |
|-----|---------|---------------|
| `cjk-simplified` | Simplified Chinese | SimHei, Microsoft YaHei, Noto Sans CJK SC |
| `cjk-traditional` | Traditional Chinese | PMingLiU, MingLiU, Noto Sans CJK TC |
| `cjk-japanese` | Japanese | IPAPGothic, TakaoGothic, Noto Sans CJK JP |
| `cjk-korean` | Korean | NanumGothic, Noto Sans CJK KR |
| `russian` | Russian / Cyrillic | DejaVu Sans, Liberation Sans |
| `turkish` | Turkish | DejaVu Sans, Liberation Sans |

Check whether the required fonts are installed before using a script overlay:

```bash
plotstyle fonts --overlay cjk-simplified
```

```python
with plotstyle.use(["nature", "cjk-simplified"]) as style:
    fig, ax = style.figure()
    ax.set_xlabel("时间 (s)")
    style.savefig(fig, "cjk_figure.pdf")
```

## Color overlays

Each journal already has a recommended palette applied automatically as the default
color cycle when you call `plotstyle.use()` (see [Color Palettes](palettes.md)).
Color overlays let you replace that default with a specific palette:

```python
with plotstyle.use(["ieee", "okabe-ito"]) as style:
    fig, ax = style.figure(columns=1)
    ax.plot(x, y)  # uses Okabe-Ito instead of IEEE's default safe-grayscale
```

> **Note:** Using `safe-grayscale` with a colorblind-required journal (e.g.
> `ieee`, `science`) raises a `PaletteColorblindWarning`.

All available color overlays:

| Key | Colors | Description |
|-----|--------|-------------|
| `okabe-ito` | 8 | Colorblind-safe qualitative palette by Okabe & Ito (2008) |
| `tol-bright` | 7 | Paul Tol's bright qualitative palette, colorblind-safe |
| `tol-vibrant` | 7 | Paul Tol's vibrant qualitative palette, colorblind-safe |
| `tol-muted` | 10 | Paul Tol's muted qualitative palette, colorblind-safe |
| `tol-light` | 9 | Paul Tol's light qualitative palette, for light backgrounds |
| `tol-high-contrast` | 3 | Paul Tol's high-contrast palette, optimised for black/white print |
| `tol-rainbow-4` | 4 | Paul Tol's discrete rainbow palette, 4 stops |
| `tol-rainbow-6` | 6 | Paul Tol's discrete rainbow palette, 6 stops |
| `tol-rainbow-8` | 8 | Paul Tol's discrete rainbow palette, 8 stops |
| `tol-rainbow-10` | 10 | Paul Tol's discrete rainbow palette, 10 stops |
| `tol-rainbow-12` | 12 | Paul Tol's discrete rainbow palette, 12 stops |
| `safe-grayscale` | 6 | Grayscale steps distinguishable in black-and-white print |

## List and inspect overlays

### Via Python

```python
import plotstyle

# All overlays
print(plotstyle.list_overlays())

# Filter by category
print(plotstyle.list_overlays(category="context"))

# Inspect one overlay
ov = plotstyle.overlay_registry.get("minimal")
print(ov.key, ov.category, ov.description)
print(ov.rcparams)
```

### Via CLI

```bash
$ plotstyle overlays --category context
  high-vis        [context]  Maximum contrast, bold lines, and oversized ticks ...
  minimal         [context]  Stripped-down axes with no top/right spines ...
  notebook        [context]  Enlarged figures and larger fonts for Jupyter ...
  presentation    [context]  Large text and thick lines for slide decks ...

$ plotstyle overlay-info notebook
Overlay: Notebook
Key:     notebook
...
```

## Overlay-only mode (no journal)

You can use overlays without a journal preset. This is useful for quickly
styling plots in a notebook or script without worrying about column widths:

```python
with plotstyle.use("notebook") as style:
    # No spec attached; style.figure() falls back to default 6.4in width
    fig, ax = style.figure()   # OK: uses default figsize
    ax.plot(x, y)
    # style.validate(fig)  # raises RuntimeError: needs a journal spec
    # style.palette()      # raises RuntimeError: needs a journal spec
```

When no journal is given, `style.palette()`, `style.validate()`, and
`style.export_submission()` raise `RuntimeError`. `style.figure()` and
`style.subplots()` still work but fall back to Matplotlib's default figure
width (6.4 in) instead of a journal column width.
