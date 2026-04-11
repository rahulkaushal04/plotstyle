# Pre-Submission Validation

This guide shows how to validate your figures against a journal's
requirements before submitting.

## Run validation

```python
import plotstyle

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
    ax.plot([1, 2, 3], [4, 5, 6])

    report = plotstyle.validate(fig, journal="nature")
```

## Interpret results

### Quick pass/fail

```python
if report.passed:
    print("Ready to submit!")
else:
    print("Issues found — see below.")
```

### Print the full report

```python
print(report)
```

Output looks like:

```
┌──────────────────────────────────────────────────────┐
│      PlotStyle Validation Report — Nature            │
├──────────┬───────────────────────────────────────────┤
│ ✓ PASS   │ Figure width: 89.0mm (single column)      │
│ ✓ PASS   │ Height within max allowed (247.0mm)        │
│ ✗ FAIL   │ Font size 4pt below minimum 5pt            │
│ ✓ PASS   │ Line weights OK                            │
└──────────┴───────────────────────────────────────────┘
3/4 checks passed, 0 warning(s), 1 failure(s)
```

### Iterate over failures

```python
for failure in report.failures:
    print(f"Check:  {failure.check_name}")
    print(f"Issue:  {failure.message}")
    print(f"Fix:    {failure.fix_suggestion}")
    print()
```

Each `CheckResult` has:

- `status` — `PASS`, `FAIL`, or `WARN`
- `check_name` — dot-namespaced identifier (e.g. `dimensions.width`)
- `message` — human-readable description
- `fix_suggestion` — actionable fix (for FAIL/WARN)

### Warnings vs failures

`WARN` results are advisory — they don't affect `report.passed`:

```python
print(report.passed)     # True even if warnings exist
print(report.warnings)   # list of WARN results
print(report.failures)   # list of FAIL results only
```

## Serialize to dict

For programmatic pipelines or CI integration:

```python
data = report.to_dict()
# {
#     "journal": "Nature",
#     "passed": True,
#     "checks": [
#         {"status": "PASS", "check_name": "dimensions.width", ...},
#         ...
#     ]
# }
```

## Validate in CI

A minimal CI check:

```python
import sys
import plotstyle

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
    # ... compose figure ...

    report = plotstyle.validate(fig, journal="nature")
    if not report.passed:
        print(report, file=sys.stderr)
        sys.exit(1)
```

## What gets validated

| Category | Checks |
|----------|--------|
| Dimensions | Figure width/height vs journal column widths and max height |
| Typography | All text elements within min/max font size range |
| Lines | Stroke weights above journal minimum |
| Colours | Avoided combinations (e.g. red-green), colorblind and grayscale compliance |
| Export | DPI, format, and font embedding requirements |

All checks run in a single pass. There is no way to skip individual checks
via the public `validate()` API.
