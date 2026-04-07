"""
Batch export — write a figure in multiple formats for journal submission.

Steps:
1. Create a figure with plotstyle.use() and plotstyle.figure().
2. Call plotstyle.export_submission() to write the figure in journal-preferred formats.
   Pass author_surname for journals (e.g. IEEE) that require author-prefix filenames.

Output:
    output/submission_nature/   — Nature preferred formats
    output/submission_ieee/     — IEEE with "smit_" author prefix
    output/submission_science/  — Science with explicit format override
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 1. Nature — uses the journal's preferred formats automatically
# ==============================================================================

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature", columns=1)
    x = np.linspace(0, 4 * np.pi, 200)
    ax.plot(x, np.exp(-x / 10) * np.sin(x))
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")

    # When formats= is omitted, preferred_formats from the Nature spec are used.
    paths = plotstyle.export_submission(
        fig,
        "fig1",
        journal="nature",
        output_dir=OUTPUT_DIR / "submission_nature",
    )
    print("Nature submission files:")
    for p in paths:
        print(f"  {p}")

plt.close(fig)

# ==============================================================================
# 2. IEEE — author-surname prefix for filename compliance
# ==============================================================================

with plotstyle.use("ieee"):
    fig, ax = plotstyle.figure("ieee", columns=1)
    categories = ["Method A", "Method B", "Method C"]
    accuracy = [92.3, 95.1, 88.7]
    ax.bar(categories, accuracy)
    ax.set_ylabel("Accuracy (%)")

    # author_surname triggers IEEE naming: "smith_fig2.pdf" (first 5 chars of surname)
    paths = plotstyle.export_submission(
        fig,
        "fig2",
        journal="ieee",
        author_surname="Smith",
        output_dir=OUTPUT_DIR / "submission_ieee",
    )
    print("\nIEEE submission files:")
    for p in paths:
        print(f"  {p}")

plt.close(fig)

# ==============================================================================
# 3. Science — explicit format list overrides the spec
# ==============================================================================

with plotstyle.use("science"):
    fig, ax = plotstyle.figure("science", columns=1)
    ax.plot([0, 1, 2], [1, 3, 2])
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    # formats= takes priority over the spec's preferred_formats
    paths = plotstyle.export_submission(
        fig,
        "supplementary_fig",
        formats=["pdf", "png"],
        journal="science",
        output_dir=OUTPUT_DIR / "submission_science",
    )
    print("\nScience submission files (custom formats):")
    for p in paths:
        print(f"  {p}")

plt.close(fig)
