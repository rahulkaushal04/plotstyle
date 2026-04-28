---
name: Bug Report
about: Report a bug in PlotStyle
labels: bug
assignees: ''
---

**Security vulnerability?** Do not open a bug report. Use [GitHub's private vulnerability reporting](https://github.com/rahulkaushal04/plotstyle/security/advisories/new) instead. See [SECURITY.md](../../SECURITY.md).

## Before You File

- [ ] I searched existing issues and this hasn't been reported yet
- [ ] I can reproduce this on the latest version of PlotStyle

## What happened?

A short description of the bug. What went wrong?

## How to reproduce it

Steps to trigger the bug:

1. Run the following code:

```python
import plotstyle

# Paste the smallest example that shows the problem
```

2. See the error or unexpected result

## What did you expect?

What should have happened instead?

## What actually happened?

What you saw instead. Paste the full error message or traceback if there is one:

```
Paste error output here
```

## Screenshots or figures

If the bug is visual (wrong styling, bad export, broken layout), attach a screenshot or the exported figure.

## Severity

- [ ] Crash / exception
- [ ] Wrong output (incorrect styling or data)
- [ ] Visual glitch (layout, spacing, colors)
- [ ] Performance issue
- [ ] Other

## Environment

- PlotStyle version: (run `python -c "import plotstyle; print(plotstyle.__version__)"`)
- matplotlib version: (run `python -c "import matplotlib; print(matplotlib.__version__)"`)
- Python version: (run `python --version`)
- OS: (e.g. Windows 11, Ubuntu 22.04, macOS 14)

**Optional dependencies (if related to the bug):**

- Pillow version:
- seaborn version:
- fonttools version:

## Which part of PlotStyle is affected?

Check any that apply:

- [ ] Applying a journal style (`plotstyle.use()`)
- [ ] Figure creation (`plotstyle.figure()` / `plotstyle.subplots()`)
- [ ] Exporting or saving (`plotstyle.savefig()` / `plotstyle.export_submission()`)
- [ ] Validation (`plotstyle.validate()`)
- [ ] Color or accessibility tools
- [ ] CLI (`plotstyle` command)
- [ ] A specific journal spec (which one?)
- [ ] Something else

## Additional context

Add any other context here. For example: does this only happen with a certain journal, file format, or backend?
