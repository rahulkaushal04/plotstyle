# Changelog

All notable changes to **plotstyle** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/) versioning.

---

## [Unreleased]

_Nothing yet._

---

## [1.0.0] - 2026-04-12

First stable release — production-ready for scientific publication workflows.

### Changed

- **Stable release** — promoted from alpha (`0.1.0a2`) to stable (`1.0.0`); all public APIs are now considered stable and subject to semantic versioning guarantees.
- **PyPI classifiers** updated to `Development Status :: 5 - Production/Stable`.
- **Enhanced project metadata** — expanded keywords, classifiers, and project URLs in `pyproject.toml` for better PyPI discoverability.
- **README improvements** — added more badges (downloads, docs status, code style), expanded feature descriptions, and added star-history / citation section.

---

## [0.1.0a2] - 2026-04-12

Second alpha — full documentation suite, comprehensive test coverage, and hardened validation.

### Added

- **Full documentation suite** — Sphinx/MyST docs covering installation, quickstart, concepts, CLI reference, complete API reference for every public symbol, how-to guides (accessibility, export, migration, multi-panel, palettes, seaborn), FAQ, and a journal comparison index.
- **ReadTheDocs integration** — `.readthedocs.yaml` added; docs build automatically on every push; Furo theme configured with custom CSS.
- **Comprehensive test suite** — new test modules added: `test_style`, `test_palettes`, `test_accessibility`, `test_grayscale`, `test_rendering`, `test_gallery`, `test_print_size`, `test_cli`, `test_io`, `test_warnings`, `test_checks`, `test_report`; existing modules `test_figure`, `test_export`, `test_migrate`, `test_fonts`, and `test_registry` substantially expanded.
- **Export DPI validation** — `validation/checks/export.py` now emits a hard `FAIL` (instead of a `WARN`) when `savefig.dpi` is a numeric value that is provably below the journal's minimum DPI requirement.
- **Dependabot** — `.github/dependabot.yml` added for automated dependency-update pull requests.
- **`_format_panel_label()` range guard** — raises `ValueError` for panel indices ≥ 702 (beyond the two-character `"zz"` label); valid range is now explicitly documented as 0–701.

### Changed

- CI workflow extended: a `docs` build job added to `.github/workflows/ci.yml` — runs `sphinx-build -W -n` on every push and uploads the rendered HTML as an artifact.
- Module docstring quick-start example in `__init__.py` updated to use the context-manager form (`with plotstyle.use(...) as style:`) and `plotstyle.figure()` instead of `plotstyle.subplots()`.
- Docstrings across `migrate.py`, `report.py`, `style.py`, `figure.py`, `export.py`, and `accessibility.py` converted to NumPy-style attribute sections for consistent Sphinx rendering.
- `FORMAT_EXTENSIONS` constant in `export.py` annotated as a module-level Sphinx data comment (`#:`) so it appears correctly in the API docs.
- `pyproject.toml` documentation extras updated: `furo` pinned to `>=2025.12.19` and `myst-parser` bumped to `>=5.0,<6`.

---

## [0.1.0a1] - 2026-04-07

First public alpha release.

### Added

- **Core style engine** — `plotstyle.use()` applies journal presets to Matplotlib's `rcParams`; works as a context manager with automatic restoration on exit.
- **Figure helpers** — `plotstyle.figure()` and `plotstyle.subplots()` create correctly-sized figures at the exact column width and max height specified by each journal.
- **Auto panel labels** — multi-panel figures receive **(a)**, **(b)**, **(c)**, … labels placed according to the journal's style rules.
- **Colorblind-safe palettes** — built-in Okabe–Ito, Tol Bright, Tol Vibrant, Tol Muted, and Safe Grayscale palettes (`plotstyle.palette()`).
- **Accessibility previews** — `plotstyle.preview_colorblind()` simulates deuteranopia, protanopia, and tritanopia; `plotstyle.preview_grayscale()` previews grayscale rendering.
- **Pre-submission validation** — `plotstyle.validate()` checks dimensions, typography, line weights, color accessibility, and export settings against a target journal spec.
- **Submission-ready export** — `plotstyle.savefig()` saves with font embedding and DPI enforcement; `plotstyle.export_submission()` batch-exports to all formats a journal accepts.
- **Spec diffing & migration** — `plotstyle.diff()` compares two journal specs; `plotstyle.migrate()` re-targets a figure from one journal to another.
- **Seaborn integration** — `patch_seaborn()` / `plotstyle_theme()` ensure PlotStyle `rcParams` survive `sns.set_theme()` calls.
- **Gallery & print-size preview** — `plotstyle.gallery()` generates sample figures; `plotstyle.preview_print_size()` opens an interactive scaled preview window.
- **Journal spec registry** — programmatic access via `plotstyle.registry`; specs are TOML files validated by immutable, typed dataclasses.
- **CLI** — `plotstyle list`, `plotstyle info`, `plotstyle diff`, `plotstyle fonts`, `plotstyle validate`, and `plotstyle export` sub-commands.
- **10 journal presets** — ACS, Cell, Elsevier, IEEE, Nature, PLOS, PRL, Science, Springer, Wiley.
- **10 working examples** — quick start, multi-panel, palettes, accessibility, validation, export, diff/migrate, gallery, registry, context manager patterns.
- **Dynamic versioning** — version derived from git tags via `hatch-vcs` and `importlib.metadata`.
- **CI/CD pipeline** — GitHub Actions workflows for lint, type-check, test matrix, and automated PyPI release via OIDC Trusted Publishing.

[Unreleased]: https://github.com/rahulkaushal04/plotstyle/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/rahulkaushal04/plotstyle/compare/v0.1.0a2...v1.0.0
[0.1.0a2]: https://github.com/rahulkaushal04/plotstyle/compare/v0.1.0a1...v0.1.0a2
[0.1.0a1]: https://github.com/rahulkaushal04/plotstyle/releases/tag/v0.1.0a1
