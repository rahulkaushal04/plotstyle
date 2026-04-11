# Migration — `plotstyle.core.migrate`

Compare journal specs and migrate figures between journals.

## `diff`

```{eval-rst}
.. autofunction:: plotstyle.core.migrate.diff
```

## `migrate`

```{eval-rst}
.. autofunction:: plotstyle.core.migrate.migrate
```

## `SpecDiff`

```{eval-rst}
.. autoclass:: plotstyle.core.migrate.SpecDiff
   :members:
```

## `SpecDifference`

```{eval-rst}
.. autoclass:: plotstyle.core.migrate.SpecDifference
   :members:
```

## Usage

### Compare two journal specs

```python
import plotstyle

result = plotstyle.diff("nature", "ieee")
print(result)
```

Output:

```
Nature → IEEE Transactions
──────────────────────────────────────────────────
Column Width (single):  89.0mm → 88.9mm
Font Family:            Helvetica, Arial → Times New Roman, Times
Min Font Size:          5.0pt → 8.0pt
Max Font Size:          7.0pt → 10.0pt
Min DPI:                300 → 600
Grayscale Required:     No → Yes
Min Line Weight:        0.25pt → 0.5pt
```

### Check if specs differ

```python
result = plotstyle.diff("nature", "science")
if result:
    print(f"{len(result)} fields differ")
else:
    print("Specs are identical")
```

### Serialize to dict

```python
data = result.to_dict()
# Ready for JSON serialization
```

### Migrate a figure

```python
with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
    ax.plot([1, 2, 3])

# Re-style for IEEE
plotstyle.migrate(fig, from_journal="nature", to_journal="ieee")
plotstyle.savefig(fig, "figure_ieee.pdf", journal="ieee")
```

`migrate()` mutates the figure in-place. It:

1. Applies target journal's rcParams globally
2. Resizes the figure to the target's column width (preserving aspect ratio)
3. Rescales all text artists, clamping to the target's font size range

## Notes

- `migrate()` modifies `mpl.rcParams` globally. Wrap it in a `plotstyle.use()`
  context manager if you need the original state restored afterwards.
- Warnings are emitted when the migration involves a font family change, newly
  required grayscale safety, or an increased DPI floor.
