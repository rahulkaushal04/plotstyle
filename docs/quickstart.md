# Quick Start

This page walks through the essential PlotStyle workflow: apply a journal
style, create a figure, validate it, and export for submission.

## 1. Apply a journal style

`plotstyle.use()` configures Matplotlib's `rcParams` to match a journal's
typographic requirements. Use it as a context manager so the original settings
are restored automatically when the block exits:

```python
import plotstyle

with plotstyle.use("nature"):
    # Everything inside this block uses Nature's fonts, sizes, and line widths.
    ...
# rcParams are back to normal here.
```

`use()` returns a {class}`~plotstyle.core.style.JournalStyle` handle. You can
also restore manually:

```python
style = plotstyle.use("nature")
# ... do work ...
style.restore()
```

## 2. Create a correctly-sized figure

`plotstyle.figure()` creates a single-axis figure at the journal's exact
column width. `plotstyle.subplots()` does the same for multi-panel layouts:

```python
import plotstyle
import numpy as np

with plotstyle.use("nature"):
    # Single-column figure
    fig, ax = plotstyle.figure("nature", columns=1)

    x = np.linspace(0, 2 * np.pi, 200)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.plot(x, np.cos(x), label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()
```

For a multi-panel figure with automatic **(a)**, **(b)**, **(c)**, … labels:

```python
with plotstyle.use("science"):
    fig, axes = plotstyle.subplots("science", nrows=2, ncols=2, columns=2)
    for ax in axes.flat:
        ax.plot([1, 2, 3])
```

## 3. Pick colorblind-safe colours

`plotstyle.palette()` returns colours from the journal's recommended palette:

```python
colors = plotstyle.palette("nature", n=4)
# ['#E69F00', '#56B4E9', '#009E73', '#F0E442']
```

Add markers and linestyles for print-safe differentiation:

```python
styled = plotstyle.palette("ieee", n=3, with_markers=True)
for color, linestyle, marker in styled:
    ax.plot(x, y, color=color, linestyle=linestyle, marker=marker)
```

## 4. Validate before submission

`plotstyle.validate()` checks a figure against the target journal's spec —
dimensions, font sizes, line weights, colours, and export settings:

```python
report = plotstyle.validate(fig, journal="nature")
print(report.passed)    # True / False
print(report.failures)  # list of CheckResult objects with fix suggestions
print(report)           # formatted table
```

## 5. Export for submission

`plotstyle.savefig()` saves with TrueType font embedding and journal DPI
enforcement:

```python
plotstyle.savefig(fig, "figure1.pdf", journal="nature")
```

`plotstyle.export_submission()` batch-exports in every format the journal
accepts:

```python
plotstyle.export_submission(
    fig, "figure1",
    journal="ieee",
    author_surname="Kaushal",
    output_dir="submission_ieee",
)
# Creates: submission_ieee/kaush_figure1.pdf, kaush_figure1.eps, etc.
```

## Complete example

Putting it all together:

```python
import numpy as np
import plotstyle

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature", columns=1)

    x = np.linspace(0, 2 * np.pi, 200)
    colors = plotstyle.palette("nature", n=2)
    ax.plot(x, np.sin(x), color=colors[0], label="sin(x)")
    ax.plot(x, np.cos(x), color=colors[1], label="cos(x)")
    ax.set_xlabel("Phase (rad)")
    ax.set_ylabel("Amplitude (a.u.)")
    ax.legend()

    report = plotstyle.validate(fig, journal="nature")
    assert report.passed, report.failures

    plotstyle.savefig(fig, "quickstart_nature.pdf", journal="nature")
```
