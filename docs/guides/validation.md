# Pre-Submission Validation

How to check your figures against a journal's requirements before submitting.

## Run validation

```python
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    ax.plot([1, 2, 3], [4, 5, 6])

    report = style.validate(fig)
```

## Check results

### Quick pass/fail

```python
if report.passed:
    print("Ready to submit!")
else:
    print("Issues found: see below.")
```

### Print the full report

```python
print(report)
```

Example output:

```
┌──────────────────────────────────────────────────────┐
│      PlotStyle Validation Report: Nature             │
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
```

Each `CheckResult` has:

- `status`: `PASS`, `FAIL`, or `WARN`
- `check_name`: dot-namespaced id (e.g. `dimensions.width`)
- `message`: what the check found
- `fix_suggestion`: how to fix it (for FAIL/WARN)
- `is_failure`: `True` when `status` is `FAIL` (convenience property)
- `is_warning`: `True` when `status` is `WARN` (convenience property)

### Warnings vs failures

`WARN` results are advisory and don't affect `report.passed`:

```python
print(report.passed)     # True even if warnings exist
print(report.warnings)   # advisory issues
print(report.failures)   # blocking issues only
```

## Serialize to dict

For use in pipelines or CI:

```python
data = report.to_dict()
# {
#     "journal": "Nature",
#     "passed": True,
#     "checks": [{"status": "PASS", "check_name": "dimensions.width", ...}, ...]
# }
```

## Use in CI

```python
import sys
import plotstyle

with plotstyle.use("nature") as style:
    fig, ax = style.figure()
    # ... compose figure ...

    report = style.validate(fig)
    if not report.passed:
        print(report, file=sys.stderr)
        sys.exit(1)
```

## What gets checked

| Category | What's checked |
|----------|----------------|
| Dimensions | Figure width/height vs. journal column widths and max height |
| Typography | All text elements within the journal's font size range |
| Lines | Stroke weights above journal minimum |
| Colours | Avoided combinations, colorblind and grayscale compliance |
| Export | DPI and font embedding requirements |

All checks run in a single pass. There is no way to skip individual checks
via the public `validate()` API.

## Checks against library defaults

Some journals do not publish complete guidelines. When a field like
`min_font_pt` or `min_weight_pt` was not defined by the journal and a
**library default** was used instead, the corresponding check is demoted from
`FAIL` to `WARN`.

This is intentional: you cannot fail a requirement the journal never set.
The warning message identifies which limit is library-assumed and links to the
official guidelines so you can verify the real constraint:

```
⚠ WARN  typography.font_size: 2 text element(s) outside the library-default
         range of 6.0–10.0pt (Wiley does not define official font size limits).
         Use this as a guideline only.
```

To check programmatically whether a field is journal-official:

```python
from plotstyle.specs import registry

spec = registry.get("wiley")
spec.is_official("typography.min_font_pt")  # False
spec.is_official("dimensions.single_column_mm")  # True
```
