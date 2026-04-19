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

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Examples](#examples)
  - [Multi-panel figures](#multi-panel-figures)
  - [Color palettes](#color-palettes)
  - [Colorblind and grayscale previews](#colorblind-and-grayscale-previews)
  - [Validation and submission export](#validation-and-submission-export)
- [Supported Journals](#supported-journals)
- [CLI](#cli)
- [Documentation](#documentation)
- [Contributing](#contributing)
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

`style.subplots()` works like `plt.subplots()` but sizes the figure to the journal spec and adds panel labels automatically, styled to each journal's convention (**A**, **B**, **C** for Science; **a**, **b**, **c** for Nature; **(a)**, **(b)**, **(c)** for IEEE).

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
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/multi_panel_science.png" width="70%" alt="2x2 multi-panel Science figure with automatic panel labels A B C D">
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

for ax, journal in zip(axes, journals):
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
styled = plotstyle.palette("ieee", n=4, with_markers=True)
for color, ls, marker in styled:
    ax.plot(x, y, color=color, linestyle=ls, marker=marker)
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

    cvd_fig = plotstyle.preview_colorblind(fig)
    cvd_fig.savefig("accessibility_colorblind.png", dpi=150, bbox_inches="tight")
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/accessibility_colorblind.png" width="90%" alt="Colorblind simulation: original, deuteranopia, protanopia, tritanopia">
</p>

```python
    gray_fig = plotstyle.preview_grayscale(fig)
    gray_fig.savefig("accessibility_grayscale.png", dpi=150, bbox_inches="tight")
```

<p align="center">
  <img src="https://raw.githubusercontent.com/rahulkaushal04/plotstyle/main/examples/output/accessibility_grayscale.png" width="60%" alt="Grayscale simulation: original vs grayscale rendering">
</p>

---

### Validation and submission export

Validate a figure against the journal's requirements, then export in all required formats at once.

```python
report = plotstyle.validate(fig, journal="nature")
print(report)          # formatted compliance table
print(report.passed)   # True if everything is OK

for failure in report.failures:
    print(failure.message)         # what failed
    print(failure.fix_suggestion)  # how to fix it
```

```python
paths = plotstyle.export_submission(
    fig,
    "figure1",
    journal="ieee",
    author_surname="Smith",     # IEEE prepends the surname prefix to filenames
    output_dir="submission/",
)
# Produces: submission/smith_figure1.pdf (and any other IEEE-required formats)
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
plotstyle validate <file> --journal <journal>  # validate a saved figure
plotstyle export <file> --journal <journal>    # print snippet for re-exporting
```

---

## Documentation

Full documentation at **[plotstyle.readthedocs.io](https://plotstyle.readthedocs.io)**:

- [Installation guide](https://plotstyle.readthedocs.io/en/stable/installation.html)
- [Quick start tutorial](https://plotstyle.readthedocs.io/en/stable/quickstart.html)
- [API reference](https://plotstyle.readthedocs.io/en/stable/api/index.html)
- [CLI reference](https://plotstyle.readthedocs.io/en/stable/cli.html)
- [FAQ](https://plotstyle.readthedocs.io/en/stable/faq.html)

Working examples are in the [`examples/`](examples/) directory.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, adding journal specs, and pull request guidelines.

---

## Citation

If PlotStyle helps your research, a citation or star is appreciated:

```bibtex
@misc{plotstyle,
  author  = {Kaushal, Rahul},
  title   = {PlotStyle: Publication-ready scientific figure presets for Matplotlib},
  year    = {2026},
  url     = {https://github.com/rahulkaushal04/plotstyle},
  note    = {Version 1.1.0},
}
```

---

## License

[MIT](LICENSE) © 2026 Rahul Kaushal
