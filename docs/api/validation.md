# Validation: `plotstyle.validation`

Pre-submission figure validation against journal specifications.

## `validate`

```{eval-rst}
.. autofunction:: plotstyle.validation.validate
```

## `ValidationReport`

```{eval-rst}
.. autoclass:: plotstyle.validation.report.ValidationReport
   :members:
```

## `CheckResult`

```{eval-rst}
.. autoclass:: plotstyle.validation.report.CheckResult
   :members:
```

## `CheckStatus`

```{eval-rst}
.. autoclass:: plotstyle.validation.report.CheckStatus
   :members:
   :undoc-members:
```

## Usage

### Basic validation

```python
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    ax.plot([1, 2, 3])

    report = style.validate(fig)
    print(report.passed)  # True
```

### Inspect failures

```python
report = plotstyle.validate(fig, journal="nature")

if not report.passed:
    for failure in report.failures:
        print(f"{failure.check_name}: {failure.message}")
        print(f"  Fix: {failure.fix_suggestion}")
```

### Print a formatted report

```python
print(report)
```

This prints a box-drawing table showing each check with a status icon
(`✓ PASS`, `✗ FAIL`, `⚠ WARN`).

### Serialize to dict

```python
data = report.to_dict()
```

### Check warnings separately

```python
for warning in report.warnings:
    print(f"⚠ {warning.check_name}: {warning.message}")
```

## What gets checked

| Check | Description |
|-------|-------------|
| `dimensions.width` | Figure width matches journal column width |
| `dimensions.height` | Figure height within journal maximum |
| `typography.*` | Font sizes within min/max bounds |
| `lines.*` | Stroke weights above journal minimum |
| `colors.*` | Avoided color combinations, colorblind safety |
| `export.*` | DPI and format compliance |

## Notes

- The `journal` parameter is keyword-only to prevent accidental positional
  argument confusion.
- Validation does **not** modify the figure or any global Matplotlib state.
- `WARN` results do not affect `report.passed`; a report with warnings but
  no failures is still considered passing.
