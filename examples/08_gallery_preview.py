"""
Journal discovery: see what each journal preset looks like before you commit.

gallery() renders a 2x2 sample figure (line, scatter, bar, histogram) with the
chosen journal's fonts, colors, and dimensions. Use it to quickly compare how
journals style a figure before picking one.

Steps:
1. List all available journals with their key column widths.
2. Render a gallery preview for a few common journals.
3. Use plotstyle.diff() to see what changes between any two journals.

Output:
    output/gallery_nature.png
    output/gallery_science.png
    output/gallery_ieee.png
"""

from pathlib import Path

import matplotlib.pyplot as plt

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Print column widths for all journals so you can choose the right one
print(f"{'Journal':<12} {'Single col (mm)':<18} {'Double col (mm)'}")
print("-" * 46)
for name in plotstyle.registry.list_available():
    spec = plotstyle.registry.get(name)
    single = spec.dimensions.single_column_mm
    double = spec.dimensions.double_column_mm
    single_str = f"{single} mm" if single is not None else "-"
    double_str = f"{double} mm" if double is not None else "-"
    print(f"{name:<12} {single_str:<18} {double_str}")

print()

# Render a gallery preview for three common journals
for journal in ["nature", "science", "ieee"]:
    fig = plotstyle.gallery(journal, columns=1)
    out = OUTPUT_DIR / f"gallery_{journal}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")

print()

# Show what changes when you move from one journal to another
result = plotstyle.diff("nature", "science")
print(f"Nature vs Science: {len(result)} differences")
for d in result.differences:
    print(f"  {d.label}: {d.value_a} -> {d.value_b}")
