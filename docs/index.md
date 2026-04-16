# plotstyle

**Publication-ready scientific figures — one line of code.**

[![PyPI](https://img.shields.io/pypi/v/plotstyle?color=blue)](https://pypi.org/project/plotstyle/)
[![Python](https://img.shields.io/pypi/pyversions/plotstyle)](https://pypi.org/project/plotstyle/)
[![License](https://img.shields.io/github/license/rahulkaushal04/plotstyle)](https://github.com/rahulkaushal04/plotstyle/blob/main/LICENSE)
[![Docs](https://readthedocs.org/projects/plotstyle/badge/?version=stable)](https://plotstyle.readthedocs.io/en/stable/)

---

PlotStyle sets up [Matplotlib](https://matplotlib.org/) (and optionally
[Seaborn](https://seaborn.pydata.org/)) so your figures match what each
scientific journal expects — the right size, font, line weights, DPI, and
export format.

```python
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)
    ax.plot([0, 1, 2], [0.2, 0.8, 0.4])
    style.savefig(fig, "figure1.pdf")
```

## What it does

- **Journal presets** — `plotstyle.use("nature")` sets fonts, sizes, line widths, and DPI for you.
- **Correct figure sizes** — `figure()` / `subplots()` create figures at the exact column width a journal requires.
- **Panel labels** — multi-panel figures automatically get **(a)**, **(b)**, **(c)** labels in the journal's style.
- **Colorblind-safe palettes** — Okabe–Ito, Tol, and grayscale-safe palettes are built in.
- **Accessibility previews** — see how your figure looks under deuteranopia, protanopia, and tritanopia.
- **Pre-submission validation** — check dimensions, fonts, line weights, and colours before you submit.
- **Export for submission** — save in all formats a journal accepts, with correct DPI and embedded fonts.
- **Spec diffing & migration** — compare two journals side-by-side and migrate a figure from one to another.
- **Seaborn support** — PlotStyle's settings survive `sns.set_theme()` calls.
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
