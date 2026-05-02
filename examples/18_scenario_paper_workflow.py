"""
Scenario: complete paper submission workflow.

A practical end-to-end workflow for creating and submitting figures for a
journal paper. This example walks through the full lifecycle of a submission:

1. Compare target journals to pick the right one.
2. Create all figures inside a single plotstyle.use() block.
3. Validate each figure before export.
4. Export all figures in the formats the journal requires.
5. Check accessibility (colorblind and grayscale).

This example targets Nature, but the same workflow applies to any supported
journal by changing the journal key in plotstyle.use().

Output:
    output/paper_fig1_nature.pdf
    output/paper_fig2_nature.pdf
    output/paper_submission/   (submission-ready files in journal formats)
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

# Box-drawing characters in validation reports require UTF-8 output.
sys.stdout.reconfigure(encoding="utf-8")

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
SUBMISSION_DIR = OUTPUT_DIR / "paper_submission"

# ==============================================================================
# Step 1: Compare journals to decide where to submit
# ==============================================================================
# plotstyle.diff() shows every spec field that differs between two journals.
# Use this to understand what changes you need to make when switching targets.

result = plotstyle.diff("nature", "science")
print("Nature vs Science: key differences\n")
print(result)
print(f"\n{len(result)} fields differ.\n")

# ==============================================================================
# Step 2: Create all figures inside one style block
# ==============================================================================
# Using a single plotstyle.use() block ensures all figures share the same
# rcParams. The palette is set automatically; no color= kwarg is required.

rng = np.random.default_rng(42)
time = np.linspace(0, 5, 80)

with plotstyle.use("nature") as style:
    colors = style.palette(n=4)

    # Figure 1: single-column line plot with shaded confidence interval
    fig1, ax1 = style.figure(columns=1)
    signal = np.exp(-time / 3) * np.sin(2 * np.pi * time)
    ax1.plot(time, signal, color=colors[0], label="Signal")
    ax1.fill_between(time, signal - 0.10, signal + 0.10, alpha=0.3, color=colors[0], label="95% CI")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude (a.u.)")
    ax1.legend()
    style.savefig(fig1, OUTPUT_DIR / "paper_fig1_nature.pdf")

    # Figure 2: double-column two-panel comparison
    fig2, axes = style.subplots(nrows=1, ncols=2, columns=2)

    # Panel a: bar chart with error bars
    groups = ["Control", "Treatment A", "Treatment B", "Treatment C"]
    means = [1.00, 1.34, 0.87, 1.56]
    errors = [0.05, 0.08, 0.06, 0.09]
    axes[0, 0].bar(groups, means, yerr=errors, color=colors[:4], capsize=3)
    axes[0, 0].set_ylabel("Relative expression")
    axes[0, 0].axhline(1.0, color="black", linewidth=0.5, linestyle="--")

    # Panel b: scatter plot
    xs = rng.normal(0, 1, 50)
    ys = 0.7 * xs + rng.normal(0, 0.3, 50)
    axes[0, 1].scatter(xs, ys, color=colors[1], s=10, alpha=0.8)
    axes[0, 1].set_xlabel("Variable X")
    axes[0, 1].set_ylabel("Variable Y")
    style.savefig(fig2, OUTPUT_DIR / "paper_fig2_nature.pdf")

    # ===========================================================================
    # Step 3: Validate both figures before export
    # ===========================================================================
    # validate() checks dimensions, fonts, DPI, line weights, and typography.
    # Run it before export so problems are caught early.

    print("\nValidation results:")
    print("-" * 40)
    for label, fig in [("fig1 (single-col)", fig1), ("fig2 (double-col)", fig2)]:
        report = style.validate(fig)
        status = "PASS" if report.passed else "FAIL"
        n_checks = len(report.checks)
        n_fail = len(report.failures)
        n_warn = len(report.warnings)
        print(f"  {label}: {status}  ({n_checks} checks, {n_fail} failures, {n_warn} warnings)")
        for failure in report.failures:
            print(f"    FAIL: {failure.message}")
            if failure.fix_suggestion:
                print(f"    Fix:  {failure.fix_suggestion}")

    # ===========================================================================
    # Step 4: Export in all formats required for submission
    # ===========================================================================
    # export_submission() uses the journal's preferred_formats automatically.
    # Pass quiet=True to suppress per-file compliance summaries.

    SUBMISSION_DIR.mkdir(exist_ok=True)
    print("\nExporting submission files:")
    for label, fig in [("fig1", fig1), ("fig2", fig2)]:
        paths = style.export_submission(
            fig,
            label,
            output_dir=SUBMISSION_DIR,
            quiet=True,
        )
        names = [p.name for p in paths]
        print(f"  {label}: {names}")

    # ===========================================================================
    # Step 5: Check accessibility before submission
    # ===========================================================================
    # preview_colorblind() simulates deuteranopia, protanopia, and tritanopia.
    # preview_grayscale() shows how the figure looks in black and white.
    # Save these as supplementary checks; do not include them in the submission.

    cvd_fig = plotstyle.preview_colorblind(fig1)
    cvd_fig.savefig(OUTPUT_DIR / "paper_fig1_cvd_check.png", dpi=100, bbox_inches="tight")
    plt.close(cvd_fig)

    gray_fig = plotstyle.preview_grayscale(fig1)
    gray_fig.savefig(OUTPUT_DIR / "paper_fig1_gray_check.png", dpi=100, bbox_inches="tight")
    plt.close(gray_fig)

    print("\nAccessibility checks saved:")
    print("  paper_fig1_cvd_check.png  (colorblind simulation)")
    print("  paper_fig1_gray_check.png (grayscale simulation)")

    plt.close(fig1)
    plt.close(fig2)

# ==============================================================================
# Summary
# ==============================================================================
print("\nSubmission folder contents:")
for p in sorted(SUBMISSION_DIR.iterdir()):
    size_kb = p.stat().st_size // 1024
    print(f"  {p.name:<30}  {size_kb} KB")
