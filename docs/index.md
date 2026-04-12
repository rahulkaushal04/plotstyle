# plotstyle

**Publication-ready scientific figures — one line of code.**

[![PyPI](https://img.shields.io/pypi/v/plotstyle?color=blue)](https://pypi.org/project/plotstyle/)
[![Python](https://img.shields.io/pypi/pyversions/plotstyle)](https://pypi.org/project/plotstyle/)
[![License](https://img.shields.io/github/license/rahulkaushal04/plotstyle)](https://github.com/rahulkaushal04/plotstyle/blob/main/LICENSE)
[![Docs](https://readthedocs.org/projects/plotstyle/badge/?version=latest)](https://plotstyle.readthedocs.io/en/latest/)

---

PlotStyle configures [Matplotlib](https://matplotlib.org/) (and optionally
[Seaborn](https://seaborn.pydata.org/)) so your figures match the typographic,
dimensional, and export requirements of major scientific journals — out of the
box.

```python
import plotstyle

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature", columns=1)
    ax.plot([0, 1, 2], [0.2, 0.8, 0.4])
    plotstyle.savefig(fig, "figure1.pdf", journal="nature")
```

## Key features

- **One-line journal presets** — `plotstyle.use("nature")` configures fonts, sizes, line widths, and export settings.
- **Correctly-sized figures** — `figure()` / `subplots()` create figures at the exact column widths specified by each journal.
- **Auto panel labels** — multi-panel figures get **(a)**, **(b)**, **(c)**, … labels per the journal's style rules.
- **Colorblind-safe palettes** — Okabe–Ito, Tol, and grayscale-safe palettes built in.
- **Accessibility previews** — simulate deuteranopia, protanopia, and tritanopia.
- **Pre-submission validation** — check dimensions, fonts, line weights, and colours against the target spec.
- **Submission-ready export** — batch-export to all formats a journal accepts with font embedding and DPI enforcement.
- **Spec diffing & migration** — compare two specs side-by-side; migrate a figure between journals.
- **Seaborn compatibility** — PlotStyle's `rcParams` survive `sns.set_theme()` calls.
- **CLI** — `plotstyle list`, `plotstyle info`, `plotstyle validate`, and more.

## Supported journals

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

```{toctree}
:maxdepth: 2
:caption: Getting Started

installation
quickstart
concepts
```

```{toctree}
:maxdepth: 2
:caption: User Guide

guides/index
journals/index
```

```{toctree}
:maxdepth: 2
:caption: Reference

api/index
cli
```

```{toctree}
:maxdepth: 2
:caption: Project

changelog
contributing
faq
```
