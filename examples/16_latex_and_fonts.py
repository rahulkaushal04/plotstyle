"""
LaTeX modes and font inspection: control text rendering and verify fonts.

Steps:
1. Use latex="auto" for automatic LaTeX detection and fallback.
2. Use detect_latex() and detect_distribution() to inspect the LaTeX environment.
3. Use detect_available() to check which journal fonts are installed.
4. Use select_best() to find the best available font for a journal spec.
5. Use check_overlay_fonts() to verify font requirements for script overlays.

Output: (console only)
"""

import plotstyle
from plotstyle.engine.fonts import check_overlay_fonts, detect_available, select_best
from plotstyle.engine.latex import detect_distribution, detect_latex
from plotstyle.overlays import overlay_registry
from plotstyle.specs import registry

# ==============================================================================
# 1. LaTeX detection
# ==============================================================================

has_latex = detect_latex()
print(f"LaTeX available: {has_latex}")

dist = detect_distribution()
if dist:
    print(f"TeX distribution: {dist}")
else:
    print("No TeX distribution detected")

# ==============================================================================
# 2. latex="auto": one-line LaTeX with graceful fallback
# ==============================================================================
# "auto" enables LaTeX when available and silently falls back to MathText
# otherwise. This replaces the manual detect + conditional pattern.

with plotstyle.use("nature", latex="auto") as style:
    print(f"\nLaTeX mode 'auto', journal: {style.spec.metadata.name}")
    fig, ax = style.figure()
    ax.set_xlabel(r"$\alpha$ (rad)")
    ax.set_ylabel(r"$\beta$ (a.u.)")
    import matplotlib.pyplot as plt

    plt.close(fig)

# ==============================================================================
# 3. Font availability check
# ==============================================================================

# Check which common scientific fonts are installed
test_fonts = ["Helvetica", "Arial", "Times New Roman", "DejaVu Sans", "Myriad Pro"]
installed = detect_available(test_fonts)
print(f"\nInstalled fonts (from test list): {installed}")

# ==============================================================================
# 4. Best font selection per journal
# ==============================================================================

print(f"\n{'Journal':<12} {'Selected font':<20} {'Exact match'}")
print("-" * 44)
for name in registry.list_available():
    spec = registry.get(name)
    font_name, is_exact = select_best(spec)
    marker = "✓" if is_exact else "✗ (fallback)"
    print(f"{name:<12} {font_name:<20} {marker}")

# ==============================================================================
# 5. Script overlay font checks
# ==============================================================================

script_overlays = [key for key in overlay_registry.list_available(category="script")]
if script_overlays:
    print("\nScript overlay font status:")
    for key in script_overlays:
        ov = overlay_registry.get(key)
        status = check_overlay_fonts(ov)
        if status:
            any_ok = any(status.values())
            summary = "OK" if any_ok else "MISSING"
            print(f"  {key:<20} {summary}")
            for font, found in status.items():
                print(f"    {'✓' if found else '✗'} {font}")
        else:
            print(f"  {key:<20} (no font requirements)")
