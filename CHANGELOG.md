# Changelog

All notable changes to **plotstyle** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/) versioning.

---

## [Unreleased]

_Nothing yet._

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

---

[Unreleased]: https://github.com/rahulkaushal04/plotstyle/compare/v0.1.0a1...HEAD
[0.1.0a1]: https://github.com/rahulkaushal04/plotstyle/releases/tag/v0.1.0a1
