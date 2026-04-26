"""
Spec comparison and figure migration between journals.

Steps:
1. Compare two journal specs with plotstyle.diff() to see what changes.
2. Create a figure styled for the source journal (Nature).
3. Migrate it to a new journal with plotstyle.migrate(). Resizes the figure,
   rescales text, and applies the target journal's rcParams in-place.

Output:
    output/before_migration_nature.pdf
    output/after_migration_science.pdf
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

# Arrow characters in the diff table require UTF-8 output.
sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 1. Compare two journal specs
# ==============================================================================
result = plotstyle.diff("nature", "science")

if result:
    print("Differences between Nature and Science:")
    print(result)
    print(f"\nTotal differing fields: {len(result)}")
else:
    print("Nature and Science specs are identical.")

# Each SpecDifference has .label, .value_a, .value_b for programmatic access
print("\nDetailed differences:")
for d in result.differences:
    print(f"  {d.label}: {d.value_a} -> {d.value_b}")

# ==============================================================================
# 2. Create a figure styled for Nature
# ==============================================================================
with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)
    x = np.linspace(0, 10, 100)
    ax.plot(x, np.sin(x), label="Data")
    ax.fill_between(x, np.sin(x) - 0.2, np.sin(x) + 0.2, alpha=0.3)
    ax.set_xlabel("Wavelength (nm)")
    ax.set_ylabel("Intensity (a.u.)")
    ax.legend()

    # Save the pre-migration version for comparison
    style.savefig(fig, OUTPUT_DIR / "before_migration_nature.pdf")

# ==============================================================================
# 3. Migrate the figure from Nature to Science
# ==============================================================================

# migrate() mutates the figure in-place: resizes canvas, rescales text, applies rcParams.
# Any significant changes (font family switch, DPI increase, etc.) are printed as warnings.
plotstyle.migrate(fig, from_journal="nature", to_journal="science")

# Save the post-migration figure with Science-compliant settings
plotstyle.savefig(fig, OUTPUT_DIR / "after_migration_science.pdf", journal="science")
plt.close(fig)
