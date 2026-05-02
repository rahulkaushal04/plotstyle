"""
Grayscale safety: programmatic luminance analysis for print-safe color choices.

PlotStyle provides utility functions to check whether a set of colors will be
distinguishable when printed in grayscale. These work with any Matplotlib
color strings and do not require a journal preset.

Functions covered:
- rgb_to_luminance(): BT.709 luminance for a single RGB color.
- luminance_delta(): pairwise luminance differences for a list of colors.
- is_grayscale_safe(): pass/fail check against a minimum delta threshold.

Use cases:
- Verify a custom palette before using it in a figure.
- Identify which color pairs are hardest to tell apart in grayscale.
- Automate accessibility checks in a CI pipeline.

Output: (console only)
"""

import plotstyle
from plotstyle.color.grayscale import is_grayscale_safe, luminance_delta, rgb_to_luminance

# ==============================================================================
# 1. Luminance of individual colors
# ==============================================================================
# rgb_to_luminance() applies BT.709 coefficients to sRGB values in [0, 1]:
#   L = 0.2126 * R + 0.7152 * G + 0.0722 * B  # noqa: ERA001
# Result is in [0, 1]: 0.0 is black, 1.0 is white.

print("BT.709 luminance for primary colors:")
print(f"  Red   (1, 0, 0): {rgb_to_luminance(1.0, 0.0, 0.0):.4f}")
print(f"  Green (0, 1, 0): {rgb_to_luminance(0.0, 1.0, 0.0):.4f}")
print(f"  Blue  (0, 0, 1): {rgb_to_luminance(0.0, 0.0, 1.0):.4f}")
print(f"  White (1, 1, 1): {rgb_to_luminance(1.0, 1.0, 1.0):.4f}")
print(f"  Black (0, 0, 0): {rgb_to_luminance(0.0, 0.0, 0.0):.4f}")

# ==============================================================================
# 2. Pairwise luminance deltas for a list of colors
# ==============================================================================
# luminance_delta() returns (idx_a, idx_b, delta) triples sorted ascending.
# The first entry is always the weakest (most similar in grayscale) pair.

custom_palette = ["#E69F00", "#56B4E9", "#009E73", "#F0E442"]

print("\nPairwise luminance deltas for a custom palette (ascending):")
deltas = luminance_delta(custom_palette)
for i, j, delta in deltas:
    status = "pass" if delta >= 0.10 else "fail"
    print(
        f"  [{status}]  Color {i} ({custom_palette[i]}) vs Color {j} ({custom_palette[j]})"
        f":  delta = {delta:.4f}"
    )

# ==============================================================================
# 3. Pass/fail grayscale safety check
# ==============================================================================
# is_grayscale_safe() returns True only when every pair has delta >= threshold.
# A common threshold is 0.10 (10% of the full luminance range).

threshold = 0.10
safe = is_grayscale_safe(custom_palette, threshold=threshold)
print(f"\nis_grayscale_safe(threshold={threshold}): {safe}")

# The weakest pair determines the outcome
weakest_i, weakest_j, weakest_delta = deltas[0]
print(f"Weakest pair: Color {weakest_i} vs Color {weakest_j} (delta = {weakest_delta:.4f})")

# ==============================================================================
# 4. Compare grayscale safety across journal palettes
# ==============================================================================
# IEEE uses safe_grayscale by design; most colorblind-safe palettes are not
# automatically safe in grayscale because they rely on hue differences.

print(f"\nJournal palette grayscale safety (threshold = {threshold}, n = 6 colors):")
print(f"  {'Journal':<12}  {'Safe':>6}  {'Min delta':>10}")
for journal in ["nature", "science", "ieee", "acs", "cell", "plos"]:
    colors = plotstyle.palette(journal, n=6)
    pair_deltas = luminance_delta(colors)
    min_delta = pair_deltas[0][2] if pair_deltas else 1.0
    safe = is_grayscale_safe(colors, threshold=threshold)
    mark = "yes" if safe else "no"
    print(f"  {journal:<12}  {mark:>6}  {min_delta:>10.4f}")

# ==============================================================================
# 5. Diagnosing problematic pairs
# ==============================================================================
# Find which pairs fall below a threshold in a specific palette.

print("\nProblematic pairs in the Nature palette (delta < 0.15, n = 4):")
nature_colors = plotstyle.palette("nature", n=4)
nature_deltas = luminance_delta(nature_colors)
found = False
for i, j, delta in nature_deltas:
    if delta < 0.15:
        print(
            f"  Color {i} ({nature_colors[i]}) vs Color {j} ({nature_colors[j]})"
            f":  delta = {delta:.4f}"
        )
        found = True
if not found:
    print("  None (all pairs above threshold)")

# ==============================================================================
# 6. Checking a fully custom color set
# ==============================================================================
# Any Matplotlib color string is accepted: hex codes, CSS names, or RGB strings.

brand_colors = ["steelblue", "coral", "mediumseagreen", "gold"]
brand_deltas = luminance_delta(brand_colors)
brand_safe = is_grayscale_safe(brand_colors, threshold=0.10)

print(f"\nCustom brand colors: {brand_colors}")
print(f"Grayscale safe (threshold=0.10): {brand_safe}")
print("Pairs sorted by luminance delta (ascending):")
for i, j, delta in brand_deltas:
    print(f"  {brand_colors[i]:>18} vs {brand_colors[j]:<18}  delta = {delta:.4f}")
