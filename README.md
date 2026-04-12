<p align="center">
  <strong>plotstyle</strong>
</p>

<p align="center">
  <em>Publication-ready scientific figures — one line of code.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/plotstyle/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/plotstyle?color=blue"></a>
  <a href="https://pypi.org/project/plotstyle/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/plotstyle"></a>
  <a href="https://pypi.org/project/plotstyle/"><img alt="Downloads" src="https://img.shields.io/pypi/dm/plotstyle?color=green"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/rahulkaushal04/plotstyle"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/rahulkaushal04/plotstyle/ci.yml?label=CI"></a>
  <a href="https://plotstyle.readthedocs.io"><img alt="Docs" src="https://img.shields.io/readthedocs/plotstyle?label=docs"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle"><img alt="Code style: Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle"><img alt="Typed: mypy" src="https://img.shields.io/badge/typed-mypy-blue"></a>
</p>

---

**PlotStyle** configures [Matplotlib](https://matplotlib.org/) (and optionally [Seaborn](https://seaborn.pydata.org/)) so your figures match the exact typographic, dimensional, and export requirements of major academic journals — out of the box.

Getting a figure accepted often means matching a journal's precise column width, font size range, line weight, DPI, and export format. PlotStyle encodes those requirements as TOML specs and applies them automatically, so you spend time on your science rather than your figure settings.

> **Current release:** `v1.0.0` (stable)

---

## Table of Contents

- [Why PlotStyle?](#why-plotstyle)
- [Features](#features)
- [Supported Journals](#supported-journals)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [CLI](#cli)
- [Examples](#examples)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)

---

## Why PlotStyle?

Most journals reject figures that don't meet their formatting requirements — wrong column width, incorrect font sizes, missing font embedding, insufficient DPI, or incompatible file formats. Fixing these manually is tedious and error-prone, especially when targeting multiple journals.

PlotStyle solves this by encoding each journal's exact requirements into machine-readable specs and applying them automatically. You focus on your data; PlotStyle handles the formatting.

---

## Features

- **One-line journal presets** — `plotstyle.use("nature")` sets fonts, sizes, line widths, and export parameters in Matplotlib's `rcParams`. Wrap it in a `with` block and everything is restored automatically when the block exits.
- **Correctly-sized figures** — `plotstyle.figure()` and `plotstyle.subplots()` create figures at the exact column width and maximum height specified by each journal.
- **Auto panel labels** — multi-panel figures get **(a)**, **(b)**, **(c)**, … labels placed and styled according to each journal's conventions.
- **Colorblind-safe palettes** — built-in Okabe–Ito, Tol Bright/Vibrant/Muted, and grayscale-safe palettes via `plotstyle.palette()`.
- **Accessibility previews** — simulate deuteranopia, protanopia, and tritanopia; preview grayscale rendering.
- **Pre-submission validation** — check figure dimensions, font sizes, line weights, color accessibility, and export settings against the target journal's spec before you submit.
- **Submission-ready export** — `plotstyle.savefig()` enforces TrueType font embedding and minimum DPI; `plotstyle.export_submission()` batch-exports to every format the journal requires.
- **Spec diffing & migration** — compare two journal specs side-by-side; re-target a figure from one journal to another with `plotstyle.migrate()`.
- **Seaborn compatibility** — a patch layer ensures PlotStyle's `rcParams` survive `sns.set_theme()` calls.
- **Typed, schema-validated specs** — journal requirements are stored as TOML files validated by immutable typed dataclasses.
- **CLI** — `plotstyle list`, `plotstyle info`, `plotstyle validate`, and more — no Python script needed.

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

> Need another journal? See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add one.

---

## Installation

Requires **Python 3.10+** and **Matplotlib ≥ 3.9**.

```bash
pip install plotstyle
```

### Optional extras

```bash
# Colorblind / grayscale preview (needs Pillow)
pip install "plotstyle[color]"

# Font subsetting / inspection
pip install "plotstyle[fonttools]"

# Seaborn integration
pip install "plotstyle[seaborn]"

# Everything
pip install "plotstyle[all]"
```

### Development install

```bash
git clone https://github.com/rahulkaushal04/plotstyle.git
cd plotstyle
pip install -e ".[dev]"
```

---

## Quick Start

```python
import numpy as np
import plotstyle

# plotstyle.use() applies the journal's rcParams (fonts, sizes, line widths).
# The `with` block ensures they are restored automatically when plotting is done.
with plotstyle.use("nature"):
    # Creates a figure at Nature's exact single-column width (89 mm).
    # Use columns=2 for double-column (full text width).
    fig, ax = plotstyle.figure("nature", columns=1)

    x = np.linspace(0, 2 * np.pi, 200)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()

    # Enforces Nature's minimum DPI (300) and embeds TrueType fonts.
    plotstyle.savefig(fig, "quickstart_nature.pdf", journal="nature")
```

The `with` block is the recommended pattern — `rcParams` are always restored on exit, even if an exception occurs inside the block.

If you need to manage the style manually:

```python
style = plotstyle.use("ieee")
try:
    fig, ax = plotstyle.figure("ieee", columns=1)
    ax.plot([1, 2, 3])
    plotstyle.savefig(fig, "fig_ieee.eps", journal="ieee")
finally:
    style.restore()  # always restore, even on error
```

---

## Usage

### Multi-panel figures

`plotstyle.subplots()` works like `plt.subplots()` but sizes the figure to the journal spec and adds panel labels automatically.

> **Note:** Unlike `plt.subplots()`, `plotstyle.subplots()` **always** returns a 2-D NumPy array of axes — even for a single panel. Use `axes[0, 0]` to access a single axes, or `axes.flat` to iterate over all panels.

```python
import plotstyle

with plotstyle.use("science"):
    fig, axes = plotstyle.subplots("science", nrows=2, ncols=2, columns=2)
    # axes has shape (2, 2); each panel is labelled (a), (b), (c), (d)
    for ax in axes.flat:
        ax.plot([1, 2, 3])
    plotstyle.savefig(fig, "multipanel.pdf", journal="science")
```

Pass `panels=False` to suppress the automatic labels.

### Color palettes

```python
# A list of 4 hex color strings from Nature's recommended palette
colors = plotstyle.palette("nature", n=4)

# With linestyles and markers — useful for accessible line plots
styled = plotstyle.palette("ieee", n=3, with_markers=True)
# styled is a list of (color, linestyle, marker) tuples
for color, ls, marker in styled:
    ax.plot(x, y, color=color, linestyle=ls, marker=marker)
```

### Validation

```python
report = plotstyle.validate(fig, journal="nature")
print(report)           # formatted table of all checks
print(report.passed)    # True if no checks failed

for failure in report.failures:
    print(failure.message)          # what failed
    print(failure.fix_suggestion)   # how to fix it
```

### Submission export

`export_submission()` writes the figure in every format the journal requires (PDF, TIFF, EPS, etc.) and applies journal-specific naming conventions.

```python
paths = plotstyle.export_submission(
    fig,
    "figure1",
    journal="ieee",
    author_surname="Kaushal",   # IEEE prepends the first 5 chars of the surname
    output_dir="submission_ieee",
)
# Produces: submission_ieee/kaush_figure1.pdf (and any other IEEE-required formats)
```

### Spec diffing and migration

```python
# Compare two journals — useful when retargeting a figure
result = plotstyle.diff("nature", "science")
print(result)           # aligned two-column table of differences

# Re-target a figure to a different journal in place
plotstyle.migrate(fig, from_journal="nature", to_journal="science")
plotstyle.savefig(fig, "figure_science.pdf", journal="science")
```

### Accessibility previews

```python
# Simulate how a figure looks under three types of color blindness
comp = plotstyle.preview_colorblind(fig)
comp.savefig("colorblind_check.png", dpi=150)

# Preview grayscale rendering
gs = plotstyle.preview_grayscale(fig)
gs.savefig("grayscale_check.png", dpi=150)
```

### Seaborn integration

`sns.set_theme()` normally overwrites the rcParams that PlotStyle set. Pass `seaborn_compatible=True` to prevent that:

```python
import seaborn as sns
import plotstyle

with plotstyle.use("nature", seaborn_compatible=True):
    fig, ax = plotstyle.figure("nature", columns=1)
    sns.lineplot(x=[1, 2, 3], y=[4, 5, 6], ax=ax)
    plotstyle.savefig(fig, "seaborn_figure.pdf", journal="nature")
```

---

## CLI

```
plotstyle list                                 # List all journal presets
plotstyle info <journal>                       # Show spec details
plotstyle diff <journal_a> <journal_b>         # Compare two journals
plotstyle fonts --journal <journal>            # Check font availability
plotstyle validate <file> --journal <journal>  # Validate a saved figure
plotstyle export <file> --journal <journal>    # Re-export in required formats
```

---

## Examples

Working examples are in the [`examples/`](examples/) directory:

| # | File | Topic |
|---|------|-------|
| 01 | [01_quickstart.py](examples/01_quickstart.py) | Basic publication-ready figure |
| 02 | [02_multi_panel_figure.py](examples/02_multi_panel_figure.py) | 2×2 subplot grid with auto panel labels |
| 03 | [03_color_palettes.py](examples/03_color_palettes.py) | Journal-specific and universal palettes |
| 04 | [04_accessibility_checks.py](examples/04_accessibility_checks.py) | Colorblind and grayscale previews |
| 05 | [05_validation.py](examples/05_validation.py) | Pre-submission validation |
| 06 | [06_export_submission.py](examples/06_export_submission.py) | Batch submission export |
| 07 | [07_spec_diff_and_migrate.py](examples/07_spec_diff_and_migrate.py) | Spec comparison and figure migration |
| 08 | [08_gallery_preview.py](examples/08_gallery_preview.py) | Gallery preview generation |
| 09 | [09_registry_and_spec.py](examples/09_registry_and_spec.py) | Registry and spec access |
| 10 | [10_context_manager_patterns.py](examples/10_context_manager_patterns.py) | Context manager usage patterns |

---

## Documentation

Full documentation is available at **[plotstyle.readthedocs.io](https://plotstyle.readthedocs.io)**:

- [Installation guide](https://plotstyle.readthedocs.io/en/latest/installation.html)
- [Quick start tutorial](https://plotstyle.readthedocs.io/en/latest/quickstart.html)
- [API reference](https://plotstyle.readthedocs.io/en/latest/api/index.html)
- [How-to guides](https://plotstyle.readthedocs.io/en/latest/guides/index.html)
- [CLI reference](https://plotstyle.readthedocs.io/en/latest/cli.html)
- [FAQ](https://plotstyle.readthedocs.io/en/latest/faq.html)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, adding journal specs, code style, and pull request guidelines.

---

## Citation

If PlotStyle helps your research, a citation or star is appreciated:

```bibtex
@software{plotstyle,
  author  = {Kaushal, Rahul},
  title   = {PlotStyle: Publication-ready scientific figure presets for Matplotlib},
  year    = {2026},
  url     = {https://github.com/rahulkaushal04/plotstyle},
  license = {MIT},
}
```

---

## License

[MIT](LICENSE) © 2026 Rahul Kaushal
