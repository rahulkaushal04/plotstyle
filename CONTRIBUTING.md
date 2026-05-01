# Contributing to PlotStyle

Thanks for your interest in contributing. This guide covers reporting bugs, proposing changes, adding journal specs, and submitting pull requests.

All contributors are expected to follow the [Code of Conduct](https://github.com/rahulkaushal04/plotstyle/blob/main/CODE_OF_CONDUCT.md). For security vulnerabilities, see [SECURITY.md](https://github.com/rahulkaushal04/plotstyle/blob/main/SECURITY.md); do not open a public issue.

## Reporting Issues

Before opening an issue, search existing issues to avoid duplicates.

- **Bug reports:** [open a new issue](https://github.com/rahulkaushal04/plotstyle/issues/new) and include:
  - A minimal reproducing example
  - The full traceback
  - Your environment details: PlotStyle version, Matplotlib version, Python version, OS

- **Spec inaccuracies:** [open a new issue](https://github.com/rahulkaushal04/plotstyle/issues/new) and include:
  - A link to the journal's official figure guidelines
  - A table showing what is currently wrong and what it should be

- **New journal specs:** [open a new issue](https://github.com/rahulkaushal04/plotstyle/issues/new) with as much information as you can find from the journal's author guidelines. You can also skip the issue and go straight to a PR using the steps in "Adding a New Journal" below.

## Development Setup

**Prerequisites:** Git, Python 3.10 or later.

```bash
# Clone the repo
git clone https://github.com/rahulkaushal04/plotstyle.git
cd plotstyle

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

If you also need the fonttools or seaborn extras (for example, when working on font or export code):

```bash
pip install -e ".[fonttools,dev]"   # font subsetting only
pip install -e ".[all,dev]"         # all optional extras
```

**Using Hatch (optional):** PlotStyle also supports [Hatch](https://hatch.pypa.io/) for environment management. If you have Hatch installed, run `hatch shell` to create and enter the dev environment. You can then use `hatch run test`, `hatch run lint`, `hatch run fmt`, and `hatch run typecheck` instead of the commands below.

### Running Tests

```bash
pytest
```

### Linting and Formatting

PlotStyle uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff check src tests
ruff format --check src tests
```

To auto-fix lint issues and reformat:

```bash
ruff check --fix src tests
ruff format src tests
```

### Type Checking

```bash
mypy src
```

### Pre-commit

If you have [pre-commit](https://pre-commit.com/) installed:

```bash
pre-commit install
```

This runs linting, formatting, and other checks automatically before each commit.

## Adding a New Journal

Journal specs live in `src/plotstyle/specs/` as `.toml` files. Each file describes a single journal's figure requirements: dimensions, fonts, export settings, and more.

### Step-by-step

1. **Copy the template:** start from `src/plotstyle/specs/_templates.toml`:

   ```bash
   cp src/plotstyle/specs/_templates.toml src/plotstyle/specs/<journal>.toml
   ```

   Use a short, lowercase name (e.g. `nature.toml`, `ieee.toml`, `plos.toml`).

2. **Fill in the spec:** open the journal's official author/figure guidelines and fill in every field you can. Look at an existing spec like `nature.toml` for reference. Key sections:

   - `[metadata]`: journal name, publisher, guidelines URL, date verified (`last_verified`)
   - `[dimensions]`: single-column width, double-column width, max height (all in mm)
   - `[typography]`: required fonts, font size range, panel label style
   - `[export]`: accepted formats, minimum DPI, color space, font embedding
   - `[color]`: accessibility requirements (colorblind, grayscale)
   - `[line]`: minimum line weight in points

3. **Validate:** run the validation script to check your spec against the schema:

   ```bash
   python scripts/validate_all_specs.py
   ```

   All fields listed in the template are expected. If the journal's guidelines do not specify a value, use a sensible default and note it in the PR.

4. **Test:** run the full test suite to make sure nothing is broken:

   ```bash
   pytest
   ```

5. **Submit a PR:** include a link to the journal's official figure preparation guidelines in your PR description.

### Updating an Existing Spec

Follow the same process but edit the existing `.toml` file instead of copying the template. Update `last_verified` in the `[metadata]` section to today's date.

## Contributing Changes

1. Fork the repository and create a branch from `main`.
2. Make your changes. Keep commits focused; one logical change per commit.
3. Add or update tests if your change affects behavior.
4. Make sure these all pass before pushing:
   - `pytest`
   - `ruff check src tests`
   - `ruff format --check src tests`
   - `mypy src`
5. Open a pull request.

## Pull Request Guidelines

In your PR:

- Describe what the PR does and why.
- Link to any related issues (`Closes #...`).
- Describe how you tested the change.
- Confirm these are all passing:
  - [ ] `pytest` passes
  - [ ] `ruff check src tests` passes
  - [ ] `ruff format --check src tests` passes
  - [ ] `mypy src` passes
  - [ ] Tests added or updated (if applicable)
  - [ ] Docs updated (if the public API changed)

**If adding or updating a journal spec:**

  - [ ] Ran `python scripts/validate_all_specs.py`
  - [ ] Included a link to the journal's official figure preparation guidelines

## Code Style

- Python 3.10+ syntax (use `X | Y` unions, `match` statements where appropriate).
- Ruff handles formatting: double quotes, 4-space indent, 100-character line length.
- NumPy-style docstrings for public API.
- Type annotations on all public functions.

## Questions?

Open an [issue](https://github.com/rahulkaushal04/plotstyle/issues) or ask directly in your PR. Happy to help.
