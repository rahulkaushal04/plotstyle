# Changelog

All notable changes to **plotstyle** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/) versioning.

---

## [Unreleased]

_Nothing yet._

---

## [1.2.2] - 2026-04-27

Patch release: docs improvements, README example quality, and CI action bump.

### Added

- **`LatexNotFoundError` catch pattern in API docs** (`docs/api/style.md`): new "Catching LaTeX errors" section shows how to import and handle `LatexNotFoundError` directly, with a note on catching the base `RuntimeError` as an alternative.

### Changed

- **README overlay examples use realistic data**: notebook and okabe-ito overlay snippets now use `np.linspace` / `np.sin` / `np.cos` plots instead of trivial `[1, 2, 3]` lists; axes labels updated to match.
- **README overlay snippet import cleanup**: removed stray `import matplotlib.pyplot as plt` from the minimal overlay example where it was unused.
- **README validation report output updated**: sample terminal output now reflects a two-column figure width rather than a single-column one.
- **README `diff` output adds `Avoid: none`**: accessibility block in the `plotstyle diff` sample output now shows the `Avoid` field.
- **`download-artifact` action bumped to v8** in `.github/workflows/release.yml` (was v4).
- **Version references bumped to 1.2.2** in `README.md` (citation note) and `docs/installation.md` (version-check snippet).

### Fixed

- **Typo in `06_export_submission.py` docstring**: `"smit_"` author prefix corrected to `"smith_"`.

---

## [1.2.1] - 2026-04-26

Patch release: `simulate_cvd` example, warning quality improvements, and docs/example content fixes.

### Added

- **`simulate_cvd` example in `04_accessibility_checks.py`**: demonstrates low-level CVD simulation by rendering a figure to an RGB array and applying a single `CVDType` matrix directly via `simulate_cvd()`.

### Changed

- **`SpecAssumptionWarning` deduplication**: each spec now emits the assumption warning at most once per session. A `_warned_specs` set on `SpecRegistry` tracks which specs have already warned; `reset()` clears it alongside the spec cache.
- **Clearer `OverlaySizeWarning`**: the message now names the journal, the overlay, the actual width, the limit, and the fix action, replacing the previous vague description.
- **Improved font-fallback warning**: lists font names in a readable comma-separated form and adds a hint to rebuild the Matplotlib font cache after installing a new font.
- **FontTools log suppression during PDF export**: `savefig()` temporarily sets the `fontTools` logger to `ERROR` level during `fig.savefig()` to suppress low-level font subsetting noise.
- **`SpecRegistry.get()` uses `_silent=True` during background style registration**: prevents the assumption warning from firing during the import-time `register_all_styles()` call.
- **Docs and example content fixes**: factual errors corrected across API reference, guides, CLI docs, and Jupyter notebooks; overlay guide expanded with additional coverage.

---

## [1.2.0] - 2026-04-23

Feature release: **overlays**, **units & conversions**, **Seaborn integration**, improved **font/LaTeX controls**, plus major CLI/docs/example expansion.

### Added

- **Style overlays** (`plotstyle.overlays`, `plotstyle.list_overlays()`): additive layers that can be composed with a base journal preset.
  - Categories: `color`, `context`, `rendering`, `plot-type`, `script`.
  - Built-in overlays include `minimal`, `notebook`, `presentation`, `high-vis`, `grid`, `bar`, `scatter`, `no-latex`, `pgf`, `latex-sans`, `okabe-ito`, `safe-grayscale`, and `tol-*` palette overlays, plus CJK/Turkish/Russian script overlays.
- **New CLI commands for overlays**
  - `plotstyle overlays [--category <category>]` to list overlays.
  - `plotstyle overlay-info <overlay>` to inspect overlay metadata and `rcParams`.
- **Font checks for overlays**: `plotstyle fonts --overlay <overlay>` (in addition to `--journal`).
- **Seaborn integration**: helpers to keep PlotStyle `rcParams` consistent when using Seaborn themes (`patch_seaborn()`, `plotstyle_theme()`, `unpatch_seaborn()`).
- **Units & conversions**: new/expanded utilities and docs for consistent size specification across specs and helpers.
- **Matplotlib-native styles compatibility**: support for registering/using PlotStyle presets as Matplotlib styles where applicable.
- **New examples & previews**: additional example scripts including overlays, Seaborn integration, units/conversions, print-size preview, Matplotlib native styles, and LaTeX/fonts.

### Changed

- **CLI UX improvements**
  - `plotstyle fonts` now supports `--journal` *or* `--overlay` (mutually exclusive, required).
  - More robust argument parsing (e.g. ignores empty entries in `--formats`).
  - Friendlier output for empty registries (journals/overlays) and clearer reporting for overlay font availability.
- **Docs & README expansion**: new/expanded guides and API reference for overlays, units, warnings, Seaborn, preview tooling, and updated patterns/examples.

### Fixed

- **CLI stability**: avoid noisy/unclear behavior in edge cases (empty registry listings, malformed format lists) and improve error messaging around missing overlay keys.

---

## [1.1.0] - 2026-04-16

Minor feature release : ergonomics improvements, hardened error handling, and spec updates.

### Added

- **`quiet` parameter on `JournalStyle.export()`** : suppresses compliance summaries and manifest output for scripting workflows.
- **Pre-computed Type 3 font checks** : compliance summary now accepts a pre-computed result for Type 3 font detection, improving performance when the check has already been run by the caller.
- **`JournalSpec` key access** : `JournalSpec` now supports key-style access, and the dimension check message has been updated for clarity.

### Fixed

- **`SpecNotFoundError` base classes** : now inherits from both `ValueError` and `KeyError` so existing `except ValueError` and `except KeyError` handlers catch it correctly; a custom `__str__` produces clearer diagnostic messages.

### Changed

- **IEEE Transactions spec updated** : column widths, max height, font family, panel-label properties, and preferred output formats revised to match current IEEE author guidelines.
- **CI documentation build** : Sphinx `docs` job (`sphinx-build -W -n`) added to the CI workflow; rendered HTML is uploaded as an artifact on every push.
- **Module docstrings** : expanded and standardised across `__init__.py`, `_utils/`, `color/`, `core/`, and `validation/` for consistent Sphinx rendering.
- **Context-manager examples** : all `plotstyle.use()` call sites in docs and examples updated to the `with plotstyle.use(...) as style:` form to ensure correct `rcParams` restoration.

---

## [1.0.0] - 2026-04-12

First stable release: production-ready for scientific publication workflows.

### Changed

- **Stable release**: promoted from alpha (`0.1.0a2`) to stable (`1.0.0`); all public APIs are now considered stable and subject to semantic versioning guarantees.
- **PyPI classifiers** updated to `Development Status :: 5 - Production/Stable`.
- **Enhanced project metadata**: expanded keywords, classifiers, and project URLs in `pyproject.toml` for better PyPI discoverability.
- **README improvements**: added more badges (downloads, docs status, code style), expanded feature descriptions, and added star-history / citation section.

---

## [0.1.0a2] - 2026-04-12

Second alpha: full documentation suite, comprehensive test coverage, and hardened validation.

### Added

- **Full documentation suite**: Sphinx/MyST docs covering installation, quickstart, concepts, CLI reference, complete API reference for every public symbol, how-to guides (accessibility, export, migration, multi-panel, palettes, seaborn), FAQ, and a journal comparison index.
- **ReadTheDocs integration**: `.readthedocs.yaml` added; docs build automatically on every push; Furo theme configured with custom CSS.
- **Comprehensive test suite**: new test modules added: `test_style`, `test_palettes`, `test_accessibility`, `test_grayscale`, `test_rendering`, `test_gallery`, `test_print_size`, `test_cli`, `test_io`, `test_warnings`, `test_checks`, `test_report`; existing modules `test_figure`, `test_export`, `test_migrate`, `test_fonts`, and `test_registry` substantially expanded.
- **Export DPI validation**: `validation/checks/export.py` now emits a hard `FAIL` (instead of a `WARN`) when `savefig.dpi` is a numeric value that is provably below the journal's minimum DPI requirement.
- **Dependabot**: `.github/dependabot.yml` added for automated dependency-update pull requests.
- **`_format_panel_label()` range guard**: raises `ValueError` for panel indices ≥ 702 (beyond the two-character `"zz"` label); valid range is now explicitly documented as 0–701.

### Changed

- CI workflow extended: a `docs` build job added to `.github/workflows/ci.yml` - runs `sphinx-build -W -n` on every push and uploads the rendered HTML as an artifact.
- Module docstring quick-start example in `__init__.py` updated to use the context-manager form (`with plotstyle.use(...) as style:`) and `plotstyle.figure()` instead of `plotstyle.subplots()`.
- Docstrings across `migrate.py`, `report.py`, `style.py`, `figure.py`, `export.py`, and `accessibility.py` converted to NumPy-style attribute sections for consistent Sphinx rendering.
- `FORMAT_EXTENSIONS` constant in `export.py` annotated as a module-level Sphinx data comment (`#:`) so it appears correctly in the API docs.
- `pyproject.toml` documentation extras updated: `furo` pinned to `>=2025.12.19` and `myst-parser` bumped to `>=5.0,<6`.

---

## [0.1.0a1] - 2026-04-07

First public alpha release.

### Added

- **Core style engine**: `plotstyle.use()` applies journal presets to Matplotlib's `rcParams`; works as a context manager with automatic restoration on exit.
- **Figure helpers**: `plotstyle.figure()` and `plotstyle.subplots()` create correctly-sized figures at the exact column width and max height specified by each journal.
- **Auto panel labels**: multi-panel figures receive **(a)**, **(b)**, **(c)**, … labels placed according to the journal's style rules.
- **Colorblind-safe palettes**: built-in Okabe–Ito, Tol Bright, Tol Vibrant, Tol Muted, and Safe Grayscale palettes (`plotstyle.palette()`).
- **Accessibility previews**: `plotstyle.preview_colorblind()` simulates deuteranopia, protanopia, and tritanopia; `plotstyle.preview_grayscale()` previews grayscale rendering.
- **Pre-submission validation**: `plotstyle.validate()` checks dimensions, typography, line weights, color accessibility, and export settings against a target journal spec.
- **Submission-ready export**: `plotstyle.savefig()` saves with font embedding and DPI enforcement; `plotstyle.export_submission()` batch-exports to all formats a journal accepts.
- **Spec diffing & migration**: `plotstyle.diff()` compares two journal specs; `plotstyle.migrate()` re-targets a figure from one journal to another.
- **Seaborn integration**: `patch_seaborn()` / `plotstyle_theme()` ensure PlotStyle `rcParams` survive `sns.set_theme()` calls.
- **Gallery & print-size preview**: `plotstyle.gallery()` generates sample figures; `plotstyle.preview_print_size()` opens an interactive scaled preview window.
- **Journal spec registry**: programmatic access via `plotstyle.registry`; specs are TOML files validated by immutable, typed dataclasses.
- **CLI**: `plotstyle list`, `plotstyle info`, `plotstyle diff`, `plotstyle fonts`, `plotstyle validate`, and `plotstyle export` sub-commands.
- **10 journal presets**: ACS, Cell, Elsevier, IEEE, Nature, PLOS, PRL, Science, Springer, Wiley.
- **10 working examples**: quick start, multi-panel, palettes, accessibility, validation, export, diff/migrate, gallery, registry, context manager patterns.
- **Dynamic versioning**: version derived from git tags via `hatch-vcs` and `importlib.metadata`.
- **CI/CD pipeline**: GitHub Actions workflows for lint, type-check, test matrix, and automated PyPI release via OIDC Trusted Publishing.

[Unreleased]: https://github.com/rahulkaushal04/plotstyle/compare/v1.2.2...HEAD
[1.2.2]: https://github.com/rahulkaushal04/plotstyle/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/rahulkaushal04/plotstyle/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/rahulkaushal04/plotstyle/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/rahulkaushal04/plotstyle/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/rahulkaushal04/plotstyle/compare/v0.1.0a2...v1.0.0
[0.1.0a2]: https://github.com/rahulkaushal04/plotstyle/compare/v0.1.0a1...v0.1.0a2
[0.1.0a1]: https://github.com/rahulkaushal04/plotstyle/releases/tag/v0.1.0a1
