"""
Unit conversions: type-safe physical measurements for figure dimensions.

PlotStyle's specs/units module provides Dimension and FontSize classes for
working with physical measurements across different unit systems (mm, cm, in,
pt, pica).

Steps:
1. Create Dimension and FontSize objects from raw values.
2. Convert between units using to_mm(), to_inches(), to_pt(), etc.
3. Perform arithmetic (add, subtract, multiply, divide) across units.
4. Compare measurements across different unit systems.
5. Use with journal specs for unit-safe dimension calculations.

Output: (console only)
"""

from plotstyle.specs import registry
from plotstyle.specs.units import Dimension, FontSize, IncompatibleUnitsError

# ==============================================================================
# 1. Create and convert measurements
# ==============================================================================

width = Dimension(89.0, "mm")
print(f"Width: {width}")
print(f"  → inches: {width.to_inches():.4f}")
print(f"  → cm:     {width.to_cm():.2f}")
print(f"  → pt:     {width.to_pt():.2f}")

font = FontSize(7.0, "pt")
print(f"\nFont size: {font}")
print(f"  → mm:   {font.to_mm():.3f}")
print(f"  → pica: {font.to_pica():.3f}")

# ==============================================================================
# 2. Arithmetic: works across units
# ==============================================================================

a = Dimension(89.0, "mm")
b = Dimension(1.0, "in")

total = a + b
print(f"\n89 mm + 1 in = {total}")

half = a / 2
print(f"89 mm / 2    = {half}")

doubled = a * 2
print(f"89 mm x 2    = {doubled}")

diff = a - b
print(f"89 mm - 1 in = {diff}")

# ==============================================================================
# 3. Cross-unit comparison
# ==============================================================================

one_inch_mm = Dimension(25.4, "mm")
one_inch_in = Dimension(1.0, "in")

print(f"\n25.4 mm == 1 in: {one_inch_mm == one_inch_in}")
print(f"Float-tolerant:  {one_inch_mm.is_close(one_inch_in)}")

# ==============================================================================
# 4. as_unit: returns a new measurement object (not a float)
# ==============================================================================

width_in = width.as_unit("in")
print(f"\n89 mm as inches: {width_in}")
print(f"  type: {type(width_in).__name__}")

# ==============================================================================
# 5. Type safety: Dimension and FontSize cannot be mixed
# ==============================================================================

try:
    _ = width + font  # type: ignore[operator]
except (IncompatibleUnitsError, TypeError) as exc:
    print(f"\nMixing Dimension + FontSize raises: {type(exc).__name__}: {exc}")

# ==============================================================================
# 6. Working with journal specs
# ==============================================================================

print("\nJournal column widths:")
print(f"{'Journal':<12} {'mm':>8} {'inches':>8}")
print("-" * 30)

for name in registry.list_available():
    spec = registry.get(name)
    mm = spec.dimensions.single_column_mm
    if mm is not None:
        dim = Dimension(mm, "mm")
        print(f"{name:<12} {mm:>8.1f} {dim.to_inches():>8.2f}")
    else:
        print(f"{name:<12} {'—':>8} {'—':>8}")

print("\nFont size ranges (in mm):")
for name in ["nature", "science", "ieee"]:
    spec = registry.get(name)
    min_fs = FontSize(spec.typography.min_font_pt, "pt")
    max_fs = FontSize(spec.typography.max_font_pt, "pt")
    print(f"  {name:<10} {min_fs.to_mm():.2f} - {max_fs.to_mm():.2f} mm")
