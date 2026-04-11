# Preview — `plotstyle.preview`

Gallery and print-size preview utilities.

## `gallery`

```{eval-rst}
.. autofunction:: plotstyle.preview.gallery.gallery
```

## `preview_print_size`

```{eval-rst}
.. autofunction:: plotstyle.preview.print_size.preview_print_size
```

## Usage

### Generate a gallery preview

`gallery()` creates a 2×2 grid of representative plots (line, scatter, bar,
histogram) styled to match a journal's settings:

```python
import plotstyle

fig = plotstyle.gallery("nature", columns=1)
fig.savefig("nature_gallery.png", dpi=150)
```

For a double-column gallery:

```python
fig = plotstyle.gallery("ieee", columns=2)
```

The gallery uses deterministic synthetic data, so output is identical across
repeated calls.

### Preview at physical print size

`preview_print_size()` temporarily scales a figure's DPI so it appears at its
actual physical column width on screen:

```python
import plotstyle

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature")
    ax.plot([1, 2, 3])

    plotstyle.preview_print_size(fig, journal="nature", columns=1)
```

An annotation showing the target width in millimetres is added temporarily
during the preview window.

#### Monitor DPI

Accuracy depends on the `monitor_dpi` parameter matching your display:

| Display | Typical `monitor_dpi` |
|---------|----------------------|
| Windows / most Linux | `96` (default) |
| macOS 1× logical | `144` |
| macOS 2× Retina | `192` |

```python
plotstyle.preview_print_size(fig, journal="nature", monitor_dpi=144)
```

## Notes

- `gallery()` applies the journal style via `plotstyle.use()` internally and
  restores rcParams in a `finally` block. It never permanently alters global
  state.
- `preview_print_size()` removes the transient annotation and restores the
  original DPI after `plt.show()` returns.
