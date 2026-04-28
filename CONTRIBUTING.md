# Contributing to PlotStyle

Thanks for your interest in contributing! This guide covers the basics: reporting bugs, proposing changes, adding journal specs, and submitting pull requests.

All contributors are expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md). For security vulnerabilities, see [SECURITY.md](SECURITY.md); do not open a public issue.

## Reporting Issues

Before opening an issue, search existing issues to avoid duplicates.

- **Bug reports:** use the [Bug Report](https://github.com/rahulkaushal04/plotstyle/issues/new?template=bug_report.md) template. Include a minimal reproducing example, the full traceback, and your environment details (PlotStyle version, matplotlib version, Python version, OS).
- **Spec inaccuracies:** use the [Spec Inaccuracy](https://github.com/rahulkaushal04/plotstyle/issues/new?template=spec_inaccuracy.md) template. Include a link to the journal's official guidelines and a table of what's wrong vs. what it should be.
- **New journal specs:** use the [New Journal Spec](https://github.com/rahulkaushal04/plotstyle/issues/new?template=new_journal_spec.md) template. Fill in as many fields as you can from the journal's author guidelines.

## Development Setup

PlotStyle uses [Hatch](https://hatch.pypa.io/) as its build and environment manager.

```bash
# Clone the repo
git clone https://github.com/rahulkaushal04/plotstyle.git
cd plotstyle

# Create a virtual environment and install with dev dependencies
pip install -e ".[dev]"
```

If you also need seaborn or fonttools extras:

```bash
pip install -e ".[all,dev]"
```

### Running Tests

```bash
pytest
```

### Linting and Formatting

PlotStyle uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

To auto-fix lint issues and reformat:

```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

### Pre-commit

If you have [pre-commit](https://pre-commit.com/) installed:

```bash
pre-commit install
```

This will run linting and formatting checks automatically before each commit.

## Adding a New Journal

Journal specs live in `src/plotstyle/specs/` as `.toml` files. Each file describes a single journal's figure requirements (dimensions, fonts, export settings, etc.).

### Step-by-step

1. **Copy the template:** start from `src/plotstyle/specs/_templates.toml`:

   ```bash
   cp src/plotstyle/specs/_templates.toml src/plotstyle/specs/<journal>.toml
   ```

   Use a short, lowercase name (e.g. `nature.toml`, `ieee.toml`, `plos.toml`).

2. **Fill in the spec:** open the journal's official author/figure guidelines and fill in every field you can. Look at an existing spec like `nature.toml` for reference. Key sections:

   - `[metadata]`: journal name, publisher, guidelines URL, date verified, your GitHub username
   - `[dimensions]`: single-column width, double-column width, max height (all in mm)
   - `[typography]`: required fonts, font size range, panel label style
   - `[export]`: accepted formats, minimum DPI, color space, font embedding
   - `[color]`: accessibility requirements (colorblind, grayscale)
   - `[line]`: minimum line weight in points

3. **Validate:** run the validation script to check your spec against the schema:

   ```bash
   python scripts/validate_all_specs.py
   ```

   All fields listed in the template are expected. If the journal's guidelines don't specify a value, use a sensible default and note it in the PR.

4. **Test:** run the full test suite to make sure nothing is broken:

   ```bash
   pytest
   ```

5. **Submit a PR:** include a link to the journal's official figure preparation guidelines in your PR description.

### Updating an Existing Spec

Follow the same process but edit the existing `.toml` file instead of copying the template. Update `last_verified` and `verified_by` in the `[metadata]` section.

## Contributing Changes

1. Fork the repository and create a branch from `main`.
2. Make your changes. Keep commits focused; one logical change per commit.
3. Add or update tests if your change affects behavior.
4. Make sure these all pass before pushing:
   - `pytest`
   - `ruff check src/ tests/`
5. Open a pull request.

## Pull Request Guidelines

Fill out the [PR template](https://github.com/rahulkaushal04/plotstyle/blob/main/.github/PULL_REQUEST_TEMPLATE.md) when you open your PR. In particular:

- Describe what the PR does and why.
- Link to any related issues (`Closes #...`).
- Describe how you tested the change.
- Check off the items in the checklist:
  - [ ] `pytest` passes
  - [ ] `ruff check src/ tests/` passes
  - [ ] Tests added or updated (if applicable)
  - [ ] Docs updated (if the public API changed)

**If adding or updating a journal spec:**

- [ ] Ran `python scripts/validate_all_specs.py`
- [ ] Included a link to the journal's official figure preparation guidelines

## Code Style

- Python 3.10+ syntax (use `X | Y` unions, `match` statements where appropriate).
- Ruff handles formatting (double quotes, 4-space indent, 100-char line length).
- NumPy-style docstrings for public API.
- Type annotations on all public functions.

## Questions?

Open a [discussion](https://github.com/rahulkaushal04/plotstyle/issues) or ask in your PR. Happy to help.
