# Installation

## Requirements

- **Python 3.10** or later
- **Matplotlib 3.9+** (installed automatically)

## Install from PyPI

```bash
pip install plotstyle
```

## Optional extras

PlotStyle ships optional dependency groups for specific features. Install them
with bracket syntax:

### Image processing for export safety

Installs [Pillow](https://pillow.readthedocs.io/) for image-based export
verification and raster manipulation.

```bash
pip install "plotstyle[color]"
```

### Font subsetting & inspection

Requires [fonttools](https://fonttools.readthedocs.io/) for advanced font
analysis.

```bash
pip install "plotstyle[fonttools]"
```

### Seaborn integration

Requires [Seaborn](https://seaborn.pydata.org/) and
[pandas](https://pandas.pydata.org/) for statistical plotting support.

```bash
pip install "plotstyle[seaborn]"
```

### Everything at once

```bash
pip install "plotstyle[all]"
```

## Development install

Clone the repository and install in editable mode with all development tools:

```bash
git clone https://github.com/rahulkaushal04/plotstyle.git
cd plotstyle
pip install -e ".[dev]"
```

This installs pytest, ruff, mypy, pre-commit, and pytest-cov alongside the
library itself.

## Building the documentation locally

```bash
pip install -e ".[docs]"
# Or with Hatch:
hatch run docs:build
hatch run docs:serve   # serves on http://localhost:8000
```

## Verifying the installation

```python
import plotstyle
print(plotstyle.__version__)
```

If this prints a version string (e.g. `0.1.0a1`), the installation is working.
