"""
Validation — check a figure against journal requirements before submission.

Steps:
1. Create a figure using plotstyle.use() and plotstyle.figure().
2. Run plotstyle.validate() to check dimensions, fonts, DPI, and colors.
3. Read the report: report.passed, report.failures, and report.to_dict().

Output: (console only)
"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import plotstyle

# Box-drawing characters in the report table require UTF-8 output.
sys.stdout.reconfigure(encoding="utf-8")

with plotstyle.use("nature"):
    fig, ax = plotstyle.figure("nature", columns=1)
    ax.plot(np.arange(10), np.random.default_rng(0).normal(0, 1, 10))
    ax.set_xlabel("Sample")
    ax.set_ylabel("Measurement")

    report = plotstyle.validate(fig, journal="nature")

    # Human-readable table (uses box-drawing characters)
    print(report)
    print()

    # Programmatic access
    print(f"Overall passed: {report.passed}")
    print(f"Total checks:   {len(report.checks)}")

    if not report.passed:
        print("\nFailures:")
        for result in report.failures:
            print(f"  [{result.check_name}] {result.message}")
            if result.fix_suggestion:
                print(f"    Fix: {result.fix_suggestion}")

    # JSON-serializable dict — useful for CI quality gates
    report_dict = report.to_dict()
    print(f"\nReport keys: {list(report_dict.keys())}")

plt.close(fig)
