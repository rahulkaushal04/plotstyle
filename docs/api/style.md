# Style: `plotstyle.core.style`

Apply and restore journal style presets.

## `use`

```{eval-rst}
.. autofunction:: plotstyle.core.style.use
```

## `JournalStyle`

```{eval-rst}
.. autoclass:: plotstyle.core.style.JournalStyle
   :members:
   :special-members: __enter__, __exit__
```

## `detect_latex`

```{eval-rst}
.. autofunction:: plotstyle.engine.latex.detect_latex
```

## `detect_distribution`

```{eval-rst}
.. autofunction:: plotstyle.engine.latex.detect_distribution
```

```{note}
`detect_distribution` is available as `plotstyle.engine.latex.detect_distribution`.
Unlike `detect_latex`, it is not exported from the top-level `plotstyle` namespace.
```

## Usage

### Context manager (recommended)

```python
import plotstyle

with plotstyle.use("nature") as style:
    print(style.spec.metadata.name)  # "Nature"
    fig, ax = style.figure()
    ax.plot([1, 2, 3])
# rcParams restored automatically
```

### Manual restore

```python
style = plotstyle.use("nature")
try:
    fig, ax = style.figure()
    ax.plot([1, 2, 3])
finally:
    style.restore()
```

### Journal with overlays

```python
import plotstyle

with plotstyle.use(["nature", "minimal", "grid"]) as style:
    fig, ax = style.figure()
    ax.plot([1, 2, 3])
```

Overlays are applied in list order. If two overlays set the same rcParam, the
last one wins. At most one journal key may appear in the list.

### Overlay-only mode (no journal)

```python
with plotstyle.use(["notebook", "grid"]) as style:
    fig, ax = style.figure()   # falls back to 6.4 in default width
    ax.plot([1, 2, 3])
    # style.palette(), style.validate(), style.export_submission()
    # all raise RuntimeError without a journal spec
```

### LaTeX detection

```python
import plotstyle

if plotstyle.detect_latex():
    style = plotstyle.use("nature", latex=True)
else:
    style = plotstyle.use("nature")          # falls back to MathText
```

### Automatic LaTeX mode

Pass `latex="auto"` to let PlotStyle detect and enable LaTeX automatically.
This is equivalent to the manual detection pattern above, but in one line:

```python
with plotstyle.use("nature", latex="auto") as style:
    fig, ax = style.figure()
    ax.set_xlabel(r"$\alpha$ (rad)")  # LaTeX if available, MathText otherwise
```

The three `latex` modes:

| Value | Behaviour |
|-------|-----------|
| `False` (default) | Use Matplotlib's built-in MathText renderer |
| `True` | Force LaTeX; raises `LatexNotFoundError` (a `RuntimeError`) if no `latex` binary is on PATH |
| `"auto"` | Enable LaTeX when available, silently fall back to MathText otherwise |

### Catching LaTeX errors

`LatexNotFoundError` is not exported from the top-level `plotstyle` namespace.
Import it directly for specific error handling:

```python
from plotstyle.engine.rcparams import LatexNotFoundError

try:
    style = plotstyle.use("nature", latex=True)
except LatexNotFoundError:
    style = plotstyle.use("nature")  # fall back to MathText
```

Alternatively, catch the base `RuntimeError` if you only need to handle the
failure and not distinguish it from other runtime errors.

### Detect TeX distribution

```python
from plotstyle.engine.latex import detect_distribution

dist = detect_distribution()
# Returns "texlive", "miktex", or None
if dist == "texlive":
    print("TeX Live is installed")
elif dist == "miktex":
    print("MiKTeX is installed")
else:
    print("No LaTeX distribution found")
```

### Seaborn-compatible mode

When working with Seaborn, pass `seaborn_compatible=True` so that
`sns.set_theme()` calls don't clobber PlotStyle's settings:

```python
with plotstyle.use("nature", seaborn_compatible=True):
    import seaborn as sns
    sns.set_theme(style="ticks")
    # PlotStyle rcParams are automatically reapplied after set_theme()
```
