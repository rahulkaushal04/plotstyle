<p align="center">
  <strong>plotstyle</strong>
</p>

<p align="center">
  <em>Matplotlib figures formatted for journal submission, automatically.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/plotstyle/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/plotstyle?color=blue"></a>
  <a href="https://pypi.org/project/plotstyle/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/plotstyle"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/rahulkaushal04/plotstyle"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/rahulkaushal04/plotstyle/ci.yml?label=CI"></a>
  <a href="https://plotstyle.readthedocs.io/en/stable/"><img alt="Docs" src="https://img.shields.io/readthedocs/plotstyle/stable?label=docs"></a>
</p>

---

**PlotStyle** makes it easy to produce Matplotlib figures that meet the exact typographic, dimensional, and export requirements of major academic journals. It also integrates with Seaborn, with more integrations planned. Pick a journal, create your figure, save it. PlotStyle handles the rest.

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/before_after.png" width="90%" alt="Left: default Matplotlib output. Right: the same figure styled with plotstyle.use('nature').">
</p>

<p align="center">
  <em>Left: default Matplotlib. Right: <code>plotstyle.use("nature")</code>. Same data, same code.</em>
</p>

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Examples](#examples)
  - [Multi-panel figures](#multi-panel-figures)
  - [Color palettes](#color-palettes)
  - [Overlays](#overlays)
  - [Colorblind and grayscale previews](#colorblind-and-grayscale-previews)
  - [Validation and submission export](#validation-and-submission-export)
- [Supported Journals](#supported-journals)
- [CLI](#cli)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Code of Conduct](#code-of-conduct)
- [Security](#security)
- [Citation](#citation)
- [License](#license)

---

## Installation

Requires **Python 3.10+** and **Matplotlib >= 3.9**.

```bash
pip install plotstyle
```

Optional extras:

```bash
pip install "plotstyle[color]"     # colorblind / grayscale previews
pip install "plotstyle[seaborn]"   # seaborn integration
pip install "plotstyle[all]"       # everything
```

---

## Quick Start

```python
import numpy as np
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)   # sized to Nature's single-column width (89 mm)

    x = np.linspace(0, 2 * np.pi, 200)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()

    style.savefig(fig, "figure.pdf")    # 300 DPI minimum, TrueType fonts embedded
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/quickstart_nature.png" width="55%" alt="Quickstart output: sin and cos figure styled for Nature">
</p>

The `with` block is the recommended pattern. Matplotlib's `rcParams` are restored automatically when it exits, even if an exception occurs.

---

## Examples

### Multi-panel figures

`style.subplots()` works like `plt.subplots()` but sizes the figure to the journal spec and adds panel labels automatically. All built-in journal specs use bold lowercase labels (**a**, **b**, **c**, …). The label style is driven by each spec's `panel_label_case` field and can be `lower`, `upper`, `parens_lower`, `parens_upper`, `sentence`, or `title`.

```python
import numpy as np
import plotstyle

rng = np.random.default_rng(42)

with plotstyle.use("science") as style:
    fig, axes = style.subplots(nrows=2, ncols=2, columns=2)

    x = np.linspace(0, 10, 100)
    axes[0, 0].plot(x, np.sin(x), label="sin")
    axes[0, 0].plot(x, np.cos(x), label="cos")
    axes[0, 0].set_xlabel("x")
    axes[0, 0].set_ylabel("f(x)")
    axes[0, 0].legend()

    xs = rng.normal(0, 1, 60)
    ys = 0.7 * xs + rng.normal(0, 0.3, 60)
    axes[0, 1].scatter(xs, ys, s=12, alpha=0.7)
    axes[0, 1].set_xlabel("Variable X")
    axes[0, 1].set_ylabel("Variable Y")

    axes[1, 0].bar(["A", "B", "C", "D"], [3.2, 5.8, 4.1, 6.5])
    axes[1, 0].set_xlabel("Category")
    axes[1, 0].set_ylabel("Count")

    axes[1, 1].hist(rng.normal(0, 1, 500), bins=25, edgecolor="white", linewidth=0.5)
    axes[1, 1].set_xlabel("Value")
    axes[1, 1].set_ylabel("Frequency")

    style.savefig(fig, "multi_panel.pdf")
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/multi_panel_science.png" width="70%" alt="2x2 multi-panel Science figure with automatic panel labels a b c d">
</p>

> `axes` is always a 2-D NumPy array. Use `axes[0, 0]` to access a single panel or `axes.flat` to iterate. Pass `panels=False` to suppress the automatic labels.

---

### Color palettes

Each journal has a recommended colorblind-safe palette. `plotstyle.palette()` returns hex color strings, cycling if you need more than the palette length.

```python
import matplotlib.pyplot as plt
import plotstyle

journals = ["nature", "science", "ieee", "acs"]
fig, axes = plt.subplots(len(journals), 1, figsize=(6, 0.6 * len(journals)))

for ax, journal in zip(axes, journals, strict=False):
    pal = plotstyle.palette(journal, n=8)
    for i, color in enumerate(pal):
        ax.barh(0, 1, left=i, color=color, edgecolor="none", height=0.8)
    ax.set_xlim(0, 8)
    ax.set_yticks([])
    ax.set_ylabel(journal, rotation=0, ha="right", va="center")
    ax.set_xticks([])

fig.suptitle("Journal Color Palettes")
fig.tight_layout()
fig.savefig("palette_comparison.png", dpi=150)
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/palette_comparison.png" width="70%" alt="Color swatch comparison for Nature, Science, IEEE, and ACS palettes">
</p>

Pass `with_markers=True` to get `(color, linestyle, marker)` tuples, useful for journals like IEEE that print in grayscale:

```python
import numpy as np
import plotstyle

x = np.linspace(0, 2 * np.pi, 100)
curves = [np.sin(x + i * 0.5) for i in range(4)]

with plotstyle.use("ieee") as style:
    fig, ax = style.figure(columns=1)
    styled = plotstyle.palette("ieee", n=4, with_markers=True)
    for i, (color, ls, marker) in enumerate(styled):
        ax.plot(x, curves[i], color=color, linestyle=ls, marker=marker,
                markevery=20, label=f"Series {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    style.savefig(fig, "ieee_markers.pdf")
```

```text
# styled: one (color, linestyle, marker) tuple per series:
[('#000000', '-', 'o'), ('#333333', '--', 's'), ('#666666', '-.', '^'), ('#999999', ':', 'D')]
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/palette_styled_ieee.png" width="55%" alt="IEEE figure with per-series color, linestyle, and marker combinations">
</p>

---

### Overlays

Overlays are additive patches that layer on top of a journal preset. They let you adjust one aspect of a figure (the colour palette, the context, the chart type) without changing the base journal settings.

Pass overlay names in the same list as the journal key:

```python
import plotstyle

# Strip top/right spines for a clean editorial look
with plotstyle.use(["nature", "minimal"]) as style:
    fig, ax = style.figure(columns=1)
    ax.plot([1, 2, 3], label="data")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    style.savefig(fig, "minimal_figure.pdf")
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/overlay_minimal.png" width="45%" alt="Nature figure with minimal overlay: no top/right spines">
</p>

```python
import numpy as np
import matplotlib.pyplot as plt
import plotstyle

x = np.linspace(0, 2 * np.pi, 100)

# Larger figure and fonts for Jupyter notebooks
with plotstyle.use(["nature", "notebook"]) as style:
    fig, ax = plt.subplots()   # plt.subplots() picks up the notebook figsize
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()
    style.savefig(fig, "notebook_figure.pdf")
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/overlay_notebook.png" width="60%" alt="Nature figure with notebook overlay: larger fonts and figure size">
</p>

```python
import numpy as np
import plotstyle

x = np.linspace(0, 2 * np.pi, 100)

# Swap the colour cycle to a specific palette
with plotstyle.use(["ieee", "okabe-ito"]) as style:
    fig, ax = style.figure(columns=1)
    for i in range(4):
        ax.plot(x, np.sin(x + i * 0.5), label=f"Series {i + 1}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    style.savefig(fig, "okabe_ito_figure.pdf")
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/overlay_okabe_ito.png" width="55%" alt="IEEE figure with okabe-ito colorblind-safe palette">
</p>

| Category | Purpose | Examples |
|----------|---------|---------|
| `color` | Swap the colour cycle | `okabe-ito`, `tol-bright`, `safe-grayscale` |
| `context` | Adjust scale for the medium | `notebook`, `presentation`, `minimal`, `high-vis` |
| `rendering` | Control LaTeX and grid rendering | `no-latex`, `grid`, `latex-sans`, `pgf` |
| `plot-type` | Optimise for a chart type | `bar`, `scatter` |
| `script` | Non-Latin font support | `cjk-simplified`, `cjk-traditional`, `cjk-japanese`, `cjk-korean`, `russian`, `turkish` |

```python
# List all available overlays
plotstyle.list_overlays()
plotstyle.list_overlays(category="context")
```

```text
# plotstyle.list_overlays()
['bar', 'cjk-japanese', 'cjk-korean', 'cjk-simplified', 'cjk-traditional', 'grid',
 'high-vis', 'latex-sans', 'minimal', 'no-latex', 'notebook', 'okabe-ito', 'pgf',
 'presentation', 'russian', 'safe-grayscale', 'scatter', 'tol-bright',
 'tol-high-contrast', 'tol-light', 'tol-muted', 'tol-rainbow-10', 'tol-rainbow-12',
 'tol-rainbow-4', 'tol-rainbow-6', 'tol-rainbow-8', 'tol-vibrant', 'turkish']

# plotstyle.list_overlays(category="context")
['high-vis', 'minimal', 'notebook', 'presentation']
```

---

### Colorblind and grayscale previews

Build a figure, then simulate how it looks under color vision deficiency or grayscale printing before you submit.

```python
import numpy as np
import plotstyle

with plotstyle.use("nature") as style:
    colors = style.palette(n=4)
    fig, ax = style.figure(columns=1)
    x = np.linspace(0, 5, 80)
    for i, c in enumerate(colors):
        ax.plot(x, np.sin(x + i), color=c, linewidth=1.5, label=f"Series {i + 1}")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal")
    ax.legend()

    # Simulate colour vision deficiency (deuteranopia, protanopia, tritanopia)
    cvd_fig = plotstyle.preview_colorblind(fig)
    cvd_fig.savefig("accessibility_colorblind.png", dpi=150, bbox_inches="tight")

    # Simulate grayscale print
    gray_fig = plotstyle.preview_grayscale(fig)
    gray_fig.savefig("accessibility_grayscale.png", dpi=150, bbox_inches="tight")
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/accessibility_colorblind.png" width="90%" alt="Colorblind simulation: original, deuteranopia, protanopia, tritanopia">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/accessibility_grayscale.png" width="60%" alt="Grayscale simulation: original vs grayscale rendering">
</p>

---

### Validation and submission export

Validate a figure against the journal's requirements, then export in all required formats at once.

```python
import numpy as np
import matplotlib.pyplot as plt
import plotstyle

x = np.linspace(0, 2 * np.pi, 100)

# Outside plotstyle.use(): some checks will fail
fig, ax = plt.subplots()
ax.plot(x, np.sin(x), label="sin(x)")
ax.set_xlabel("Phase (rad)")
ax.set_ylabel("Amplitude")
ax.legend()

report = plotstyle.validate(fig, journal="nature")
print(report)          # formatted compliance table
print(report.passed)   # False, rcParams not configured

for failure in report.failures:
    print(failure.message)         # what failed
    print(failure.fix_suggestion)  # how to fix it
plt.close(fig)

# Inside plotstyle.use(): all checks pass
with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()

    report = plotstyle.validate(fig, journal="nature")
    print(report)
    print(report.passed)   # True
```

```text
┌──────────────────────────────────────────────────────┐
│         PlotStyle Validation Report: Nature          │
├──────────┬───────────────────────────────────────────┤
│ ✗ FAIL   │ Figure width 162.6mm does not match Nat...│
│ ✓ PASS   │ Figure height 121.9mm is within the Nat...│
│ ✗ FAIL   │ pdf.fonttype = 3; must be 42 for TrueTy...│
│ ✗ FAIL   │ ps.fonttype = 3; must be 42 for TrueTyp...│
│ ⚠ WARN   │ savefig.dpi = 'figure'; Nature requires...│
│ ✓ PASS   │ All plotted lines and spines meet the N...│
│ ✗ FAIL   │ 23 text element(s) outside the Nature r...│
└──────────┴───────────────────────────────────────────┘
2/7 checks passed, 1 warning(s), 4 failure(s)

passed: False

failure.message:       pdf.fonttype = 3; must be 42 for TrueType font embedding.
failure.fix_suggestion: Call plotstyle.use() to apply all required rcParams, or set
                        mpl.rcParams['pdf.fonttype'] = 42 manually.
```

When called inside `plotstyle.use()`, all checks pass:

```text
┌──────────────────────────────────────────────────────┐
│         PlotStyle Validation Report: Nature          │
├──────────┬───────────────────────────────────────────┤
│ ✓ PASS   │ Figure width 89.0mm matches single colu...│
│ ✓ PASS   │ Figure height 55.0mm is within the Natu...│
│ ✓ PASS   │ pdf.fonttype = 42 (TrueType fonts will ...│
│ ✓ PASS   │ ps.fonttype = 42 (TrueType fonts will b...│
│ ✓ PASS   │ savefig.dpi = 300.0 meets the Nature mi...│
│ ✓ PASS   │ All plotted lines and spines meet the N...│
│ ✓ PASS   │ All text elements are within the Nature...│
└──────────┴───────────────────────────────────────────┘
7/7 checks passed, 0 warning(s), 0 failure(s)

passed: True
```

```python
import numpy as np
import os
import plotstyle

os.makedirs("submission", exist_ok=True)

with plotstyle.use("ieee") as style:
    fig, ax = style.figure(columns=1)
    x = np.linspace(0, 2 * np.pi, 100)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude")
    ax.legend()

    paths = plotstyle.export_submission(
        fig,
        "figure1",
        journal="ieee",
        author_surname="Smith",     # IEEE prepends the surname prefix to filenames
        output_dir="submission/",
    )
    print(paths)
```

```text
[PosixPath('submission/smith_figure1.tiff'),
 PosixPath('submission/smith_figure1.eps'),
 PosixPath('submission/smith_figure1.pdf'),
 PosixPath('submission/smith_figure1.png')]
```

---

## Supported Journals

| Key | Journal | Publisher |
|-----|---------|-----------|
| `acs` | ACS (JACS) | American Chemical Society |
| `cell` | Cell | Cell Press |
| `elsevier` | Elsevier | Elsevier |
| `ieee` | IEEE Transactions | IEEE |
| `nature` | Nature | Springer Nature |
| `plos` | PLOS ONE | Public Library of Science |
| `prl` | Physical Review Letters | American Physical Society |
| `science` | Science | AAAS |
| `springer` | Springer | Springer |
| `wiley` | Wiley | Wiley |

> Need another journal? See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## CLI

```
plotstyle list                                 # list all journal presets
plotstyle info <journal>                       # show spec details
plotstyle diff <journal_a> <journal_b>         # compare two journals
plotstyle fonts --journal <journal>            # check font availability
plotstyle overlays [--category <category>]    # list available overlays
plotstyle overlay-info <overlay>               # show overlay details
plotstyle validate <file> --journal <journal>  # validate a saved figure
plotstyle export <file> --journal <journal>    # print snippet for re-exporting
```

**`plotstyle list`**
```text
  acs             American Chemical Society
  cell            Cell Press
  elsevier        Elsevier
  ieee            IEEE
  nature          Springer Nature
  plos            Public Library of Science
  prl             American Physical Society
  science         AAAS
  springer        Springer Nature
  wiley           Wiley
```

**`plotstyle info nature`**
```text
Journal: Nature
Publisher: Springer Nature
Source: https://www.nature.com/documents/nature-final-artwork.pdf
Last Verified: 2026-04-22
──────────────────────────
Dimensions:
  Single column: 89.0mm (3.50in)
  Double column: 183.0mm (7.20in)
  Max height:    247.0mm
Typography:
  Font:          Helvetica, Arial (fallback: sans-serif)
  Size range:    5.0-7.0pt
  Panel labels:  5.0pt bold lower (a, b, c)
Export:
  Formats:  ai, eps, pdf
  Min DPI:  300
  Color:    rgb
Accessibility:
  Colorblind safe: Not required
  Grayscale safe:  Not required
  Avoid:           none
```

**`plotstyle diff nature science`**
```text
Nature → Science
──────────────────────────────────────────────────
Column Width (single):  89.0mm → 86.4mm
Column Width (double):  183.0mm → 177.8mm
Max Height:             247.0mm → -
Font Family:            Helvetica, Arial → Minion Pro, Benton Sans Condensed
Min Font Size:          5.0pt → 7.5pt
Max Font Size:          7.0pt → 10.0pt
Panel Label Size:       5.0pt → 7.5pt
Preferred Formats:      ai, eps, pdf → ai, eps, pdf, tiff
Colorblind Required:    No → Yes
```

**`plotstyle fonts --journal nature`**
```text
Font check for: Nature
Required:        Helvetica, Arial
Available:       Helvetica, Arial
Selected:        Helvetica
Exact match:     Yes
```

**`plotstyle overlays`**
```text
  bar             [plot-type]  Optimised rcParams for bar charts.
  cjk-simplified  [script]     Font configuration for Simplified Chinese labels.
  grid            [rendering]  Enable major grid lines with a subtle dashed style.
  high-vis        [context]    Maximum contrast, bold lines, and oversized ticks.
  latex-sans      [rendering]  Enable LaTeX rendering with a sans-serif font family.
  minimal         [context]    Stripped-down axes with no top/right spines.
  no-latex        [rendering]  Disable LaTeX text rendering; use Matplotlib MathText.
  notebook        [context]    Enlarged figures and larger fonts for Jupyter.
  okabe-ito       [color]      Colorblind-safe 8-color qualitative palette.
  pgf             [rendering]  Use the PGF LaTeX backend for vector output.
  presentation    [context]    Large text and thick lines for slide decks.
  safe-grayscale  [color]      6-step grayscale palette for black-and-white print.
  scatter         [plot-type]  Optimised rcParams for scatter plots.
  tol-bright      [color]      Paul Tol's bright 7-color qualitative palette.
  ...
```

**`plotstyle overlay-info minimal`**
```text
Overlay: Minimal
Key:     minimal
Category: context
Description: Stripped-down axes with no top/right spines for editorial and blog use.
──────────────────────────
rcParams:
  axes.spines.top = False
  axes.spines.right = False
  xtick.top = False
  ytick.right = False
  axes.grid = False
  axes.linewidth = 0.8
```

---

## Documentation

Full documentation at **[plotstyle.readthedocs.io](https://plotstyle.readthedocs.io)**:

- [Installation guide](https://plotstyle.readthedocs.io/en/stable/installation.html)
- [Quick start tutorial](https://plotstyle.readthedocs.io/en/stable/quickstart.html)
- [API reference](https://plotstyle.readthedocs.io/en/stable/api/index.html)
- [CLI reference](https://plotstyle.readthedocs.io/en/stable/cli.html)
- [FAQ](https://plotstyle.readthedocs.io/en/stable/faq.html)

Working examples are in the [`examples/`](https://github.com/rahulkaushal04/plotstyle/tree/main/examples/) directory:

| Example | What it covers |
|---------|----------------|
| [`01_quickstart.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/01_quickstart.py) | Apply a journal preset, create a figure, and save |
| [`02_multi_panel_figure.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/02_multi_panel_figure.py) | Multi-panel layouts with automatic panel labels |
| [`03_color_palettes.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/03_color_palettes.py) | Journal palettes, grayscale-safe markers, `apply_palette` |
| [`04_accessibility_checks.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/04_accessibility_checks.py) | Colorblind simulation and grayscale print-safety |
| [`05_validation.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/05_validation.py) | Validate a figure against journal requirements |
| [`06_export_submission.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/06_export_submission.py) | Export in all required formats for submission |
| [`07_spec_diff_and_migrate.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/07_spec_diff_and_migrate.py) | Compare journals and migrate a figure between them |
| [`08_gallery_preview.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/08_gallery_preview.py) | Discover journals and preview their styles |
| [`09_registry_and_spec.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/09_registry_and_spec.py) | Inspect journal specs from the registry |
| [`10_context_manager_patterns.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/10_context_manager_patterns.py) | Patterns for managing rcParam lifetime |
| [`11_seaborn_integration.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/11_seaborn_integration.py) | Keep PlotStyle settings intact with Seaborn |
| [`12_overlays.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/12_overlays.py) | Overlays: context, color, and plot-type |
| [`14_print_size_preview.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/14_print_size_preview.py) | Preview a figure at its true physical print size |
| [`15_matplotlib_native_styles.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/15_matplotlib_native_styles.py) | Use PlotStyle presets with `plt.style` |
| [`16_latex_and_fonts.py`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/16_latex_and_fonts.py) | LaTeX modes and font availability checks |

Interactive Jupyter notebooks are in [`examples/notebooks/`](https://github.com/rahulkaushal04/plotstyle/tree/main/examples/notebooks/):

| Notebook | What it covers |
|----------|----------------|
| [`01_quickstart.ipynb`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/notebooks/01_quickstart.ipynb) | Full quickstart: style, figure, palette, validate, save, overlays |
| [`02_accessibility_and_validation.ipynb`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/notebooks/02_accessibility_and_validation.ipynb) | Colorblind and grayscale previews, validation reports |
| [`03_journal_comparison_and_migration.ipynb`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/notebooks/03_journal_comparison_and_migration.ipynb) | Diff journals and migrate figures between them |
| [`04_overlays.ipynb`](https://github.com/rahulkaushal04/plotstyle/blob/main/examples/notebooks/04_overlays.ipynb) | Overlays in depth: context, color, plot-type, combining |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, adding journal specs, and pull request guidelines.

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this standard.

---

## Security

To report a security vulnerability, use [GitHub's private vulnerability reporting](https://github.com/rahulkaushal04/plotstyle/security/advisories/new) rather than opening a public issue. See [SECURITY.md](SECURITY.md) for scope, timeline, and disclosure guidelines.

---

## Citation

If PlotStyle helps your research, a citation or star is appreciated.

Use the **"Cite this repository"** button on the GitHub sidebar to get a ready-to-use APA or BibTeX entry. It reads from [`CITATION.cff`](CITATION.cff) and is always up to date.

---

## License

[MIT](LICENSE) © 2026 Rahul Kaushal
