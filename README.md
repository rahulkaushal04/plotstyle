<p align="center">
  <strong>plotstyle</strong>
</p>

<p align="center">
  <em>Publication-ready scientific figures — one line of code.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/plotstyle/"><img alt="PyPI" src="https://img.shields.io/pypi/v/plotstyle?color=blue"></a>
  <a href="https://pypi.org/project/plotstyle/"><img alt="Python" src="https://img.shields.io/pypi/pyversions/plotstyle"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/rahulkaushal04/plotstyle"></a>
  <a href="https://github.com/rahulkaushal04/plotstyle/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/rahulkaushal04/plotstyle/ci.yml?label=CI"></a>
</p>

---

**PlotStyle** configures [Matplotlib](https://matplotlib.org/) (and optionally [Seaborn](https://seaborn.pydata.org/)) so your figures match the typographic, dimensional, and export requirements of major scientific journals — out of the box.

> **Current release:** `v0.1.0a1` (alpha)

---

## Table of Contents

- [Features](#features)
- [Supported Journals](#supported-journals)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [CLI](#cli)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **One-line journal presets** — `plotstyle.use("nature")` sets fonts, sizes, line widths, and export parameters via Matplotlib's `rcParams`.
- **Correctly-sized figures** — `plotstyle.figure()` / `plotstyle.subplots()` create figures at the exact column width and max height specified by each journal.
- **Auto panel labels** — multi-panel figures get **(a)**, **(b)**, **(c)**, … labels placed according to the journal's style rules.
- **Colorblind-safe palettes** — built-in Okabe–Ito, Tol Bright/Vibrant/Muted, and grayscale-safe palettes with optional markers and linestyles.
- **Accessibility previews** — simulate deuteranopia, protanopia, and tritanopia; preview grayscale rendering.
- **Pre-submission validation** — check figure dimensions, font sizes, line weights, color accessibility, and export settings against the target journal's spec.
- **Submission-ready export** — batch-export to all formats a journal accepts (PDF, EPS, TIFF, …) with font embedding and DPI enforcement.
- **Spec diffing & migration** — compare two journal specs side-by-side; migrate a figure from one journal to another.
- **Seaborn compatibility** — a monkey-patch layer ensures PlotStyle's `rcParams` survive `sns.set_theme()` calls.
- **Typed, schema-validated specs** — journal requirements are stored as TOML files validated by immutable dataclasses.
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

Requires **Python 3.10+**.

```bash
pip install plotstyle
```

### Extras

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

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature", columns=1)

    x = np.linspace(0, 2 * np.pi, 200)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()

    plotstyle.savefig(fig, "quickstart_nature.pdf", journal="nature")
```

`plotstyle.use()` also works as a context manager — `rcParams` are automatically restored on exit:

```python
with plotstyle.use("ieee"):
    fig, ax = plotstyle.figure("ieee", columns=1)
    ax.plot([1, 2, 3])
    plotstyle.savefig(fig, "fig_ieee.eps", journal="ieee")
# rcParams are back to normal here
```

---

## Usage

**Multi-panel figures** with auto labels:

```python
fig, axes = plotstyle.subplots("science", nrows=2, ncols=2, columns=2)
# Axes get (a), (b), (c), (d) labels per journal style
```

**Colorblind-safe palettes** (Okabe–Ito, Tol Bright/Vibrant/Muted, Safe Grayscale):

```python
colors = plotstyle.palette("nature", n=4)
styled = plotstyle.palette("ieee", n=3, with_markers=True)  # [(color, linestyle, marker), ...]
```

**Validation** — check dimensions, fonts, line weights, colors, and export settings:

```python
report = plotstyle.validate(fig, journal="nature")
print(report.passed)    # True / False
print(report.failures)  # with fix suggestions
```

**Submission export** — batch-export to all formats a journal accepts:

```python
plotstyle.export_submission(fig, "figure1", journal="ieee",
                            author_surname="Kaushal",
                            output_dir="submission_ieee")
```

**Accessibility previews**, **spec diffing & migration**, and **Seaborn integration** are also available — see the [`examples/`](examples/) directory for full usage.

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, adding journal specs, code style, and pull request guidelines.

---

## License

[MIT](LICENSE) © 2026 Rahul Kaushal
