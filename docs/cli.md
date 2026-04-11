# CLI Reference

PlotStyle includes a command-line interface for quick access to common
workflows without writing Python scripts.

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
  springer        Springer
  wiley           Wiley
```

### `plotstyle info <journal>`

Show detailed specification for a journal:

```bash
$ plotstyle info nature
Journal: Nature
Publisher: Springer Nature
Source: https://www.nature.com/nature/for-authors/final-submission
Last Verified: 2026-04-02
──────────────────────────
Dimensions:
  Single column: 89.0mm (3.50in)
  Double column: 183.0mm (7.20in)
  Max height:    247.0mm
Typography:
  Font:          Helvetica, Arial (fallback: sans-serif)
  Size range:    5.0-7.0pt
  Panel labels:  8.0pt bold lower (a, b, c)
Export:
  Formats:  tiff, pdf, eps
  Min DPI:  300
  Color:    rgb
Accessibility:
  Colorblind safe: Required
  Grayscale safe:  Not required
  Avoid:           red-green
```

### `plotstyle diff <journal_a> <journal_b>`

Compare two journal specifications side-by-side:

```bash
$ plotstyle diff nature ieee
Nature → IEEE Transactions
──────────────────────────────────────────────────
Column Width (single):  89.0mm → 88.9mm
Font Family:            Helvetica, Arial → Times New Roman, Times
Min Font Size:          5.0pt → 8.0pt
...
```

### `plotstyle fonts --journal <journal>`

Check whether the required fonts are available on your system:

```bash
$ plotstyle fonts --journal nature
```

### `plotstyle validate <file> --journal <journal>`

Validate a saved figure file against a journal's specification:

```bash
$ plotstyle validate figure1.pdf --journal nature
```

### `plotstyle export <file> --journal <journal>`

Re-export a figure in the journal's required formats:

```bash
$ plotstyle export figure1.png --journal ieee --formats pdf,eps
```

## Exit codes

All commands return `0` on success and `1` on error, following POSIX
conventions for use in shell scripts and CI pipelines.
