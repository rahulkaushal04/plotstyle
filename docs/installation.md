# Installation

## Requirements

- **Python 3.10** or later
- **Matplotlib 3.9+** (installed automatically)

## Install from PyPI

```bash
pip install plotstyle
```

## Optional extras

Some features need additional packages. Install them with bracket syntax:

### Color accessibility previews

Installs [Pillow](https://pillow.readthedocs.io/) for raster image processing.

```bash
pip install "plotstyle[color]"
```

### Font inspection

Installs [fonttools](https://fonttools.readthedocs.io/) for advanced font analysis.

```bash
pip install "plotstyle[fonttools]"
```

### Seaborn integration

Installs [Seaborn](https://seaborn.pydata.org/) and [pandas](https://pandas.pydata.org/).

```bash
pip install "plotstyle[seaborn]"
```

### Install everything

```bash
pip install "plotstyle[all]"
```

## Development install

```bash
git clone https://github.com/rahulkaushal04/plotstyle.git
cd plotstyle
pip install -e ".[dev]"
```

## Build docs locally

```bash
pip install -e ".[docs]"
hatch run docs:build
hatch run docs:serve   # serves on http://localhost:8000
```

## Verify the installation

```python
import plotstyle
print(plotstyle.__version__)  # e.g. '1.2.3'
```
