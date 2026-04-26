# CLI Reference

PlotStyle includes a command-line tool for inspecting journal specs, checking
fonts, and validating saved files, without writing any Python.

## Commands

### `plotstyle list`

List all available journal presets:

```bash
$ plotstyle list
  acs             American Chemical Society
  cell            Cell Press
  elsevier        Elsevier
  ieee            IEEE
  nature          Springer Nature
  plos            Public Library of Science
  prl             American Physical Society
  science         AAAS
  springer        Springer Nature
  wiley           Wiley
```

---

### `plotstyle info <journal>`

Show the full specification for a journal:

```bash
$ plotstyle info nature
Journal: Nature
Publisher: Springer Nature
Source: https://www.nature.com/documents/nature-final-artwork.pdf
Last Verified: 2026-04-22
──────────────────────────
Dimensions:
  Single column: 89.0mm (3.50in)
  Double column: 183.0mm (7.20in)
  Max height:    247.0mm
Typography:
  Font:          Helvetica, Arial (fallback: sans-serif)
  Size range:    5.0-7.0pt
  Panel labels:  5.0pt bold lower (a, b, c)
Export:
  Formats:  ai, eps, pdf
  Min DPI:  300
  Color:    rgb
Accessibility:
  Colorblind safe: Not required
  Grayscale safe:  Not required
  Avoid:           none
```

---

### `plotstyle diff <journal_a> <journal_b>`

Compare two journal specs field by field:

```bash
$ plotstyle diff nature ieee
Nature → IEEE Transactions
──────────────────────────────────────────────────
Column Width (single):  89.0mm → 88.9mm
Column Width (double):  183.0mm → 182.0mm
Max Height:             247.0mm → 216.0mm
Font Family:            Helvetica, Arial → Times New Roman, Helvetica, Arial
Min Font Size:          5.0pt → 9.0pt
Max Font Size:          7.0pt → 10.0pt
Panel Label Size:       5.0pt → 9.0pt
Preferred Formats:      ai, eps, pdf → tiff, eps, pdf, png
Colorblind Required:    No → Yes
```

If two journals have identical specs the command prints `No differences.` (preceded by the `A → B` header line).

---

### `plotstyle fonts --journal <journal>`

Check which preferred fonts are installed on your system:

```bash
$ plotstyle fonts --journal nature
Font check for: Nature
Required:        Helvetica, Arial
Available:       Helvetica, Arial
Selected:        Helvetica
Exact match:     Yes
```

If the preferred font is missing, PlotStyle falls back to the next entry in
the font list and prints a warning.

You can also check the fonts required by a script overlay:

```bash
$ plotstyle fonts --overlay cjk-japanese
```

---

### `plotstyle overlays [--category <category>]`

List all available overlays. Optionally filter by category:

```bash
$ plotstyle overlays --category context
  high-vis        [context]  Maximum contrast, bold lines, and oversized ticks for projected displays.
  minimal         [context]  Stripped-down axes with no top/right spines for editorial and blog use.
  notebook        [context]  Enlarged figures and larger fonts for Jupyter and interactive sessions.
  presentation    [context]  Large text and thick lines for slide decks and posters.
```

Valid categories: `color`, `context`, `rendering`, `script`, `plot-type`.

---

### `plotstyle overlay-info <overlay>`

Show the full rcParams for a single overlay:

```bash
$ plotstyle overlay-info notebook
Overlay: Notebook
Key:     notebook
Category: context
Description: Enlarged figures and larger fonts for Jupyter and interactive sessions.
──────────────────────────
rcParams:
  figure.figsize = [8.0, 5.5]
  font.size = 14.0
  axes.labelsize = 14.0
  xtick.labelsize = 12.0
  ytick.labelsize = 12.0
  legend.fontsize = 12.0
  lines.linewidth = 2.0
  axes.linewidth = 1.5
  xtick.major.width = 1.5
  ytick.major.width = 1.5
```

---

### `plotstyle validate <file.pdf> --journal <journal>`

Check a saved PDF for Type 3 fonts (a common journal portal rejection reason):

```bash
$ plotstyle validate figure1.pdf --journal nature
Validation against: Nature

✓ PASS  No Type 3 fonts detected (TrueType embedding OK).

Note: Full validation requires a live Matplotlib Figure object.
      Use plotstyle.validate(fig, journal='nature') in Python
      for complete checks (dimensions, typography, colour, line weights).
```

This command checks only the PDF file for font embedding. For a full
validation covering dimensions, font sizes, line weights, and colours, use
`plotstyle.validate(fig, journal=...)` in Python; this requires the live
Matplotlib `Figure` object.

---

### `plotstyle export <file> --journal <journal>`

Print a Python code snippet for re-exporting a figure in all journal-required
formats. No files are created; re-exporting requires the original Matplotlib
`Figure` object, which cannot be recovered from a saved file.

```bash
$ plotstyle export figure1.pdf --journal nature
Re-export requires the original Matplotlib Figure object.
Use plotstyle.export_submission(fig, ...) in Python.

Example:
  import plotstyle
  plotstyle.export_submission(fig, 'figure1', journal='nature')
```

Add `--formats` to override the format list, or `--author` for journals like
IEEE that prefix filenames with the author's surname:

```bash
$ plotstyle export figure1.pdf --journal ieee --formats pdf,eps --author Smith
```

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (bad arguments, unknown journal, file not found, etc.) |

Standard POSIX convention, suitable for use in shell scripts and CI pipelines.
