"""
Gallery preview — render a journal's style as a 2x2 sample figure.

Steps:
1. Call plotstyle.gallery(journal, columns=) to get a ready-made sample figure
   with line, scatter, bar, and histogram panels styled for that journal.
2. Save or display the result.

Tip: plotstyle.preview_print_size(fig, journal=..., columns=...) opens an
interactive window scaled to the figure's true physical print size.

Output:
    output/gallery_nature.png
    output/gallery_ieee.png
"""

from pathlib import Path

import matplotlib.pyplot as plt

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Single-column gallery for Nature (Okabe-Ito palette, 89 mm width)
gallery_fig = plotstyle.gallery("nature", columns=1)
gallery_fig.savefig(OUTPUT_DIR / "gallery_nature.png", dpi=150, bbox_inches="tight")
plt.close(gallery_fig)
print(f"Saved: {OUTPUT_DIR / 'gallery_nature.png'}")

# Double-column gallery for IEEE (grayscale palette, full text width)
gallery_fig = plotstyle.gallery("ieee", columns=2)
gallery_fig.savefig(OUTPUT_DIR / "gallery_ieee.png", dpi=150, bbox_inches="tight")
plt.close(gallery_fig)
print(f"Saved: {OUTPUT_DIR / 'gallery_ieee.png'}")
