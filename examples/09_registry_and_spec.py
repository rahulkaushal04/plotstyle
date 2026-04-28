"""
Registry inspection: list and inspect journal specifications.

Steps:
1. List all available journal presets.
2. Inspect a full journal spec: dimensions, typography, export, and accessibility.
3. Compare column widths across all journals.

Output: (console only)
"""

import plotstyle

# List every available journal preset
available = plotstyle.registry.list_available()
print(f"Available journals ({len(available)}):")
for name in available:
    print(f"  {name}")

# Deep-inspect a single journal spec
spec = plotstyle.registry.get("nature")

print(f"\n{'=' * 40}")
print(f"Journal: {spec.metadata.name}")
print(f"Publisher: {spec.metadata.publisher}")
print(f"{'=' * 40}")

print("\nDimensions:")
print(f"  Single column: {spec.dimensions.single_column_mm} mm")
print(f"  Double column: {spec.dimensions.double_column_mm} mm")
print(f"  Max height:    {spec.dimensions.max_height_mm} mm")

print("\nTypography:")
print(f"  Font family:   {spec.typography.font_family}")
print(f"  Font size:     {spec.typography.min_font_pt}-{spec.typography.max_font_pt} pt")
print(f"  Panel labels:  {spec.typography.panel_label_pt} pt, {spec.typography.panel_label_weight}")
print(f"  Label case:    {spec.typography.panel_label_case}")

print("\nExport:")
print(f"  Formats:       {spec.export.preferred_formats}")
print(f"  Min DPI:       {spec.export.min_dpi}")
print(f"  Color space:   {spec.export.color_space}")

print("\nAccessibility:")
print(f"  Colorblind required: {spec.color.colorblind_required}")
print(f"  Grayscale required:  {spec.color.grayscale_required}")

# Cross-journal column width comparison
print(f"\n{'Journal':<12} {'Single (mm)':<14} {'Double (mm)':<14}")
print("-" * 40)
for name in available:
    s = plotstyle.registry.get(name)
    single = (
        f"{s.dimensions.single_column_mm}" if s.dimensions.single_column_mm is not None else "-"
    )
    double = (
        f"{s.dimensions.double_column_mm}" if s.dimensions.double_column_mm is not None else "-"
    )
    print(f"{name:<12} {single:<14} {double:<14}")
