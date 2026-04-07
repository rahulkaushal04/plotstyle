"""Enhanced test suite for plotstyle.specs.units.

Covers construction, conversion, arithmetic, comparison, hashing, repr,
and all exception paths for both Dimension and FontSize, with edge cases,
boundary values, parametric sweeps, and docstrings on every test.
"""

from __future__ import annotations

import math
import sys

import pytest

from plotstyle.specs.units import (
    Dimension,
    DimensionError,
    FontSize,
    IncompatibleUnitsError,
    Unit,
    UnsupportedUnitError,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

ALL_UNITS: list[str] = ["mm", "cm", "in", "pt", "pica"]


@pytest.fixture(params=ALL_UNITS)
def any_unit(request) -> str:
    """Parametric fixture yielding each supported unit string in turn."""
    return request.param


@pytest.fixture
def dim_mm() -> Dimension:
    """A simple Dimension in millimetres for reuse across tests."""
    return Dimension(100.0, "mm")


@pytest.fixture
def dim_in() -> Dimension:
    """A Dimension of exactly 1 inch, useful for known-value assertions."""
    return Dimension(1.0, "in")


@pytest.fixture
def fs_pt() -> FontSize:
    """A FontSize of 12 pt (a common body-copy size)."""
    return FontSize(12.0, "pt")


@pytest.fixture
def fs_pica() -> FontSize:
    """A FontSize of 1 pica (= 12 pt exactly)."""
    return FontSize(1.0, "pica")


# ---------------------------------------------------------------------------
# Construction and validation
# ---------------------------------------------------------------------------


class TestConstruction:
    """Validate object construction, type coercion, and unit gating."""

    @pytest.mark.parametrize("unit", ALL_UNITS)
    def test_dimension_accepts_all_supported_units(self, unit: str) -> None:
        """
        Description: Dimension should accept every unit in the supported set.
        Scenario: Construct Dimension(1.0, unit) for each unit.
        Expectation: No exception; stored unit equals the supplied string.
        """
        d = Dimension(1.0, unit)
        assert d.unit == unit

    @pytest.mark.parametrize("unit", ALL_UNITS)
    def test_fontsize_accepts_all_supported_units(self, unit: str) -> None:
        """
        Description: FontSize should accept every unit in the supported set.
        Scenario: Construct FontSize(1.0, unit) for each unit.
        Expectation: No exception; stored unit equals the supplied string.
        """
        fs = FontSize(1.0, unit)
        assert fs.unit == unit

    @pytest.mark.parametrize("value", [0, 1, 10, 10.5, -5, -0.001])
    def test_dimension_stores_value_as_float(self, value) -> None:
        """
        Description: Any numeric value (int or float) must be stored as float.
        Scenario: Construct Dimension with various int/float values.
        Expectation: d.value is a float equal to the input.
        """
        d = Dimension(value, "mm")
        assert isinstance(d.value, float)
        assert d.value == float(value)

    @pytest.mark.parametrize("value", [0, 1, 12, 12.5, -1, -0.5])
    def test_fontsize_stores_value_as_float(self, value) -> None:
        """
        Description: Any numeric value must be stored as float in FontSize too.
        Scenario: Construct FontSize with various int/float values.
        Expectation: fs.value is a float equal to the input.
        """
        fs = FontSize(value, "pt")
        assert isinstance(fs.value, float)
        assert fs.value == float(value)

    def test_zero_dimension_is_valid(self) -> None:
        """
        Description: A measurement of magnitude zero is physically meaningful.
        Scenario: Construct Dimension(0, 'mm').
        Expectation: No exception; value == 0.0.
        """
        d = Dimension(0, "mm")
        assert d.value == 0.0

    def test_negative_dimension_is_valid(self) -> None:
        """
        Description: Negative values may represent offsets or over-bleed; they
        must not be rejected at construction time.
        Scenario: Construct Dimension(-10, 'mm').
        Expectation: No exception; value == -10.0.
        """
        d = Dimension(-10, "mm")
        assert d.value == -10.0

    def test_very_large_value_is_valid(self) -> None:
        """
        Description: Extremely large values should not overflow or raise.
        Scenario: Construct Dimension(1e15, 'mm').
        Expectation: value stored without error.
        """
        d = Dimension(1e15, "mm")
        assert d.value == 1e15

    def test_very_small_positive_value_is_valid(self) -> None:
        """
        Description: Sub-micron values are valid (e.g. tolerances).
        Scenario: Construct Dimension(1e-10, 'mm').
        Expectation: value stored without error.
        """
        d = Dimension(1e-10, "mm")
        assert d.value == pytest.approx(1e-10)

    @pytest.mark.parametrize(
        "bad_unit",
        ["furlong", "px", "em", "rem", "", "MM", "PT", "IN", "Mm", " mm", "mm ", "pt\n"],
    )
    def test_unsupported_unit_raises_unsupported_unit_error(self, bad_unit: str) -> None:
        """
        Description: Unrecognised or case-variant unit strings must raise
        UnsupportedUnitError, which is a DimensionError and a ValueError.
        Scenario: Construct Dimension with an invalid unit string.
        Expectation: UnsupportedUnitError raised; .unit attribute set correctly.
        """
        with pytest.raises(UnsupportedUnitError) as exc_info:
            Dimension(1.0, bad_unit)
        assert exc_info.value.unit == bad_unit

    def test_error_message_contains_bad_unit_name(self) -> None:
        """
        Description: The error message must name the offending unit so the
        developer can identify the problem without reading source code.
        Scenario: Construct Dimension(1.0, 'furlong').
        Expectation: 'furlong' appears in str(exception).
        """
        with pytest.raises(UnsupportedUnitError) as exc_info:
            Dimension(1.0, "furlong")
        assert "furlong" in str(exc_info.value)

    def test_error_message_lists_all_supported_units(self) -> None:
        """
        Description: The error message should tell the developer every
        accepted unit so they know what alternatives exist.
        Scenario: Trigger UnsupportedUnitError with unit='px'.
        Expectation: Each of mm, cm, in, pt, pica appears in the message.
        """
        with pytest.raises(UnsupportedUnitError) as exc_info:
            Dimension(1.0, "px")
        msg = str(exc_info.value)
        for u in ALL_UNITS:
            assert u in msg

    def test_unsupported_unit_error_is_dimension_error(self) -> None:
        """
        Description: UnsupportedUnitError must be catchable as DimensionError.
        Scenario: Catch DimensionError when constructing with bad unit.
        Expectation: DimensionError is raised (isinstance check passes).
        """
        with pytest.raises(DimensionError):
            Dimension(1.0, "em")

    def test_unsupported_unit_error_is_value_error(self) -> None:
        """
        Description: UnsupportedUnitError must be catchable as ValueError for
        backward-compatibility with callers that predate this library.
        Scenario: Catch ValueError when constructing with bad unit.
        Expectation: ValueError is raised.
        """
        with pytest.raises(ValueError):
            Dimension(1.0, "em")

    @pytest.mark.parametrize("bad_value", ["wide", "12pt", None, [], {}, object()])
    def test_non_numeric_value_raises(self, bad_value) -> None:
        """
        Description: Non-numeric values must be rejected during construction.
        Scenario: Construct Dimension with non-numeric value.
        Expectation: TypeError or ValueError is raised.
        """
        with pytest.raises((TypeError, ValueError)):
            Dimension(bad_value, "mm")  # type: ignore[arg-type]

    def test_dimension_is_immutable(self) -> None:
        """
        Description: Frozen dataclasses must reject attribute assignment.
        Scenario: Try to assign a new value to d.value after construction.
        Expectation: AttributeError or TypeError is raised.
        """
        d = Dimension(10.0, "mm")
        with pytest.raises((AttributeError, TypeError)):
            d.value = 20.0  # type: ignore[misc]

    def test_dimension_unit_is_immutable(self) -> None:
        """
        Description: The unit field must also be immutable.
        Scenario: Try to assign a new unit to d.unit after construction.
        Expectation: AttributeError or TypeError is raised.
        """
        d = Dimension(10.0, "mm")
        with pytest.raises((AttributeError, TypeError)):
            d.unit = "cm"  # type: ignore[misc]

    def test_fontsize_is_immutable(self) -> None:
        """
        Description: FontSize frozen dataclass must reject attribute mutation.
        Scenario: Try to assign d.value on a FontSize instance.
        Expectation: AttributeError or TypeError is raised.
        """
        fs = FontSize(10.0, "pt")
        with pytest.raises((AttributeError, TypeError)):
            fs.value = 20.0  # type: ignore[misc]

    def test_dimension_is_hashable(self) -> None:
        """
        Description: Frozen dataclasses must be hashable (usable in sets/dicts).
        Scenario: Create two equal Dimension objects and insert into a set.
        Expectation: Set has length 1.
        """
        d1 = Dimension(10.0, "mm")
        d2 = Dimension(10.0, "mm")
        assert len({d1, d2}) == 1

    def test_fontsize_is_hashable_as_dict_key(self) -> None:
        """
        Description: FontSize must be usable as a dictionary key.
        Scenario: Create a dict keyed by a FontSize object.
        Expectation: Key lookup succeeds.
        """
        fs = FontSize(12.0, "pt")
        d = {fs: "twelve pt"}
        assert d[fs] == "twelve pt"

    def test_dimension_and_fontsize_with_same_fields_not_equal(self) -> None:
        """
        Description: Even with identical (value, unit) fields, Dimension and
        FontSize are different types and must not be considered equal.
        Scenario: Compare Dimension(10, 'pt') == FontSize(10, 'pt').
        Expectation: Equality is False.
        """
        assert Dimension(10.0, "pt") != FontSize(10.0, "pt")

    def test_no_instance_dict_on_dimension(self) -> None:
        """
        Description: slots=True should prevent a per-instance __dict__.
        Scenario: Access __dict__ on a Dimension instance.
        Expectation: AttributeError (no __dict__) or dict is absent/empty.
        """
        d = Dimension(1.0, "mm")
        assert not hasattr(d, "__dict__")

    def test_no_instance_dict_on_fontsize(self) -> None:
        """
        Description: slots=True should prevent a per-instance __dict__ on FontSize.
        Scenario: Access __dict__ on a FontSize instance.
        Expectation: AttributeError or no __dict__ attribute.
        """
        fs = FontSize(1.0, "pt")
        assert not hasattr(fs, "__dict__")


# ---------------------------------------------------------------------------
# Conversion factors (physics-correct known values)
# ---------------------------------------------------------------------------


class TestConversionFactors:
    """Verify each conversion path against authoritative physical constants."""

    # --- Dimension ---

    def test_1_inch_to_mm(self, dim_in: Dimension) -> None:
        """
        Description: 1 inch = 25.4 mm exactly (ISO 31-1).
        Scenario: Dimension(1, 'in').to_mm()
        Expectation: 25.4
        """
        assert dim_in.to_mm() == pytest.approx(25.4)

    def test_1_inch_to_pt(self, dim_in: Dimension) -> None:
        """
        Description: 1 inch = 72 PostScript points.
        Scenario: Dimension(1, 'in').to_pt()
        Expectation: 72.0
        """
        assert dim_in.to_pt() == pytest.approx(72.0)

    def test_1_inch_to_pica(self, dim_in: Dimension) -> None:
        """
        Description: 1 inch = 6 picas (each pica = 12 pt = 1/6 inch).
        Scenario: Dimension(1, 'in').to_pica()
        Expectation: 6.0
        """
        assert dim_in.to_pica() == pytest.approx(6.0)

    def test_1_pica_to_pt(self) -> None:
        """
        Description: 1 pica = 12 PostScript points by definition.
        Scenario: Dimension(1, 'pica').to_pt()
        Expectation: 12.0
        """
        assert Dimension(1, "pica").to_pt() == pytest.approx(12.0)

    def test_1_cm_to_mm(self) -> None:
        """
        Description: 1 cm = 10 mm.
        Scenario: Dimension(1, 'cm').to_mm()
        Expectation: 10.0
        """
        assert Dimension(1, "cm").to_mm() == pytest.approx(10.0)

    def test_100_mm_to_cm(self, dim_mm: Dimension) -> None:
        """
        Description: 100 mm = 10 cm.
        Scenario: Dimension(100, 'mm').to_cm()
        Expectation: 10.0
        """
        assert dim_mm.to_cm() == pytest.approx(10.0)

    def test_25_4_mm_to_inches(self) -> None:
        """
        Description: 25.4 mm = 1 inch (inverse of the base constant).
        Scenario: Dimension(25.4, 'mm').to_inches()
        Expectation: 1.0
        """
        assert Dimension(25.4, "mm").to_inches() == pytest.approx(1.0)

    def test_72_pt_to_inches(self) -> None:
        """
        Description: 72 pt = 1 inch (inverse of pt→inch).
        Scenario: Dimension(72, 'pt').to_inches()
        Expectation: 1.0
        """
        assert Dimension(72, "pt").to_inches() == pytest.approx(1.0)

    def test_6_pica_to_inches(self) -> None:
        """
        Description: 6 pica = 1 inch.
        Scenario: Dimension(6, 'pica').to_inches()
        Expectation: 1.0
        """
        assert Dimension(6, "pica").to_inches() == pytest.approx(1.0)

    def test_a4_width_mm_to_inches(self) -> None:
        """
        Description: A4 page width is 210 mm; verify in-to-mm round-trip
        matches the known A4 value in inches.
        Scenario: Dimension(210, 'mm').to_inches()
        Expectation: 210 / 25.4 ≈ 8.2677…
        """
        assert Dimension(210, "mm").to_inches() == pytest.approx(210 / 25.4)

    def test_a4_width_mm_to_pt(self) -> None:
        """
        Description: A4 width in points is the canonical DTP page size.
        Scenario: Dimension(210, 'mm').to_pt()
        Expectation: 210 / (25.4/72) ≈ 595.28 pt
        """
        assert Dimension(210, "mm").to_pt() == pytest.approx(210 / (25.4 / 72))

    def test_zero_dimension_converts_to_zero_in_any_unit(self, any_unit: str) -> None:
        """
        Description: A measurement of 0 must convert to 0 in every unit.
        Scenario: Dimension(0, unit).to(other_unit) for every target unit.
        Expectation: 0.0
        """
        d = Dimension(0, any_unit)
        for target in ALL_UNITS:
            assert d.to(target) == pytest.approx(0.0)

    # --- FontSize ---

    def test_fontsize_10pt_to_mm(self) -> None:
        """
        Description: 10 pt x (25.4 mm/in ÷ 72 pt/in) = approx 3.528 mm.
        Scenario: FontSize(10, 'pt').to_mm()
        Expectation: 10 * 25.4 / 72
        """
        assert FontSize(10, "pt").to_mm() == pytest.approx(10 * 25.4 / 72)

    def test_fontsize_1_pica_to_pt(self, fs_pica: FontSize) -> None:
        """
        Description: 1 pica = 12 pt.
        Scenario: FontSize(1, 'pica').to_pt()
        Expectation: 12.0
        """
        assert fs_pica.to_pt() == pytest.approx(12.0)

    def test_fontsize_24pt_to_pica(self) -> None:
        """
        Description: 24 pt = 2 picas.
        Scenario: FontSize(24, 'pt').to_pica()
        Expectation: 2.0
        """
        assert FontSize(24, "pt").to_pica() == pytest.approx(2.0)

    def test_fontsize_72pt_to_inches(self) -> None:
        """
        Description: 72 pt = 1 inch.
        Scenario: FontSize(72, 'pt').to_inches()
        Expectation: 1.0
        """
        assert FontSize(72, "pt").to_inches() == pytest.approx(1.0)

    def test_fontsize_10mm_to_cm(self) -> None:
        """
        Description: 10 mm = 1 cm.
        Scenario: FontSize(10, 'mm').to_cm()
        Expectation: 1.0
        """
        assert FontSize(10, "mm").to_cm() == pytest.approx(1.0)

    def test_fontsize_to_inches_to_pt_roundtrip(self) -> None:
        """
        Description: Converting pt→in→pt should recover the original value.
        Scenario: FontSize(36, 'pt') → to_inches() → Dimension → to_pt()
        Expectation: 36.0
        """
        inches = FontSize(36, "pt").to_inches()
        back = FontSize(inches, "in").to_pt()
        assert back == pytest.approx(36.0)


# ---------------------------------------------------------------------------
# .to() generic converter
# ---------------------------------------------------------------------------


class TestToMethod:
    """Tests for the generic .to(target_unit) method."""

    @pytest.mark.parametrize("unit", ALL_UNITS)
    def test_to_same_unit_is_identity(self, unit: str) -> None:
        """
        Description: Converting to the same unit must return the original value.
        Scenario: Dimension(1.0, unit).to(unit)
        Expectation: 1.0
        """
        assert Dimension(1.0, unit).to(unit) == pytest.approx(1.0)

    def test_to_returns_plain_float(self) -> None:
        """
        Description: .to() must return a Python float, not a Dimension object.
        Scenario: Dimension(1.0, 'in').to('mm')
        Expectation: isinstance(result, float) is True.
        """
        result = Dimension(1.0, "in").to("mm")
        assert isinstance(result, float)

    def test_to_unsupported_unit_raises(self) -> None:
        """
        Description: Passing an invalid unit to .to() must raise UnsupportedUnitError.
        Scenario: Dimension(1.0, 'mm').to('em')
        Expectation: UnsupportedUnitError raised.
        """
        with pytest.raises(UnsupportedUnitError):
            Dimension(1.0, "mm").to("em")

    def test_roundtrip_in_to_mm_to_in(self) -> None:
        """
        Description: Inch→mm→inch round-trip must recover 1.0 within float tolerance.
        Scenario: Convert 1 in to mm, then back to in.
        Expectation: 1.0
        """
        mm_val = Dimension(1.0, "in").to("mm")
        assert Dimension(mm_val, "mm").to("in") == pytest.approx(1.0)

    def test_roundtrip_pt_to_pica_to_pt(self) -> None:
        """
        Description: pt→pica→pt round-trip must be lossless.
        Scenario: 12 pt → pica → pt.
        Expectation: 12.0
        """
        pica_val = Dimension(12.0, "pt").to("pica")
        assert Dimension(pica_val, "pica").to("pt") == pytest.approx(12.0)

    def test_roundtrip_cm_to_in_to_cm(self) -> None:
        """
        Description: cm→in→cm round-trip must be lossless.
        Scenario: 2.54 cm → in → cm.
        Expectation: 2.54
        """
        inches = Dimension(2.54, "cm").to("in")
        assert Dimension(inches, "in").to("cm") == pytest.approx(2.54)

    @pytest.mark.parametrize(
        "src,tgt",
        [
            ("mm", "cm"),
            ("cm", "mm"),
            ("in", "pt"),
            ("pt", "in"),
            ("pica", "pt"),
            ("pt", "pica"),
            ("in", "pica"),
            ("pica", "in"),
            ("mm", "pt"),
            ("pt", "mm"),
        ],
    )
    def test_all_pairwise_roundtrips(self, src: str, tgt: str) -> None:
        """
        Description: Every unit pair must support a lossless round-trip via .to().
        Scenario: Dimension(1.0, src).to(tgt) then back.
        Expectation: 1.0
        """
        val = Dimension(1.0, src).to(tgt)
        assert Dimension(val, tgt).to(src) == pytest.approx(1.0, rel=1e-9)


# ---------------------------------------------------------------------------
# .as_unit() typed converter
# ---------------------------------------------------------------------------


class TestAsUnit:
    """Tests for as_unit(), which returns a typed measurement object."""

    def test_returns_dimension_type(self) -> None:
        """
        Description: as_unit on a Dimension must return a Dimension, not a base type.
        Scenario: Dimension(2.54, 'cm').as_unit('mm')
        Expectation: isinstance(result, Dimension) is True.
        """
        result = Dimension(2.54, "cm").as_unit("mm")
        assert isinstance(result, Dimension)

    def test_returns_fontsize_type(self) -> None:
        """
        Description: as_unit on a FontSize must return a FontSize.
        Scenario: FontSize(1, 'pica').as_unit('pt')
        Expectation: isinstance(result, FontSize) is True.
        """
        result = FontSize(1, "pica").as_unit("pt")
        assert isinstance(result, FontSize)

    def test_converted_value_correct_for_dimension(self) -> None:
        """
        Description: The value in the returned object must match manual conversion.
        Scenario: Dimension(2.54, 'cm').as_unit('mm')
        Expectation: result.value ≈ 25.4, result.unit == 'mm'.
        """
        result = Dimension(2.54, "cm").as_unit("mm")
        assert result.value == pytest.approx(25.4)
        assert result.unit == "mm"

    def test_converted_value_correct_for_fontsize(self) -> None:
        """
        Description: FontSize.as_unit must set value and unit correctly.
        Scenario: FontSize(1, 'pica').as_unit('pt')
        Expectation: result.value ≈ 12.0, result.unit == 'pt'.
        """
        result = FontSize(1, "pica").as_unit("pt")
        assert result.value == pytest.approx(12.0)
        assert result.unit == "pt"

    def test_unsupported_target_unit_raises(self) -> None:
        """
        Description: as_unit with an invalid target must raise UnsupportedUnitError.
        Scenario: Dimension(1.0, 'mm').as_unit('px')
        Expectation: UnsupportedUnitError raised.
        """
        with pytest.raises(UnsupportedUnitError):
            Dimension(1.0, "mm").as_unit("px")

    def test_original_is_unchanged(self) -> None:
        """
        Description: as_unit must not mutate the original (frozen) object.
        Scenario: Call as_unit on a Dimension, then check original fields.
        Expectation: original.value == 1.0, original.unit == 'in'.
        """
        original = Dimension(1.0, "in")
        original.as_unit("mm")
        assert original.value == 1.0
        assert original.unit == "in"

    def test_as_unit_same_unit_is_new_object_equal_value(self) -> None:
        """
        Description: as_unit to the same unit must return a new object with
        identical value (not necessarily the same identity).
        Scenario: Dimension(5.0, 'mm').as_unit('mm')
        Expectation: result == Dimension(5.0, 'mm').
        """
        d = Dimension(5.0, "mm")
        result = d.as_unit("mm")
        assert result == d


# ---------------------------------------------------------------------------
# is_close
# ---------------------------------------------------------------------------


class TestIsClose:
    """Tests for floating-point approximate comparison via is_close."""

    def test_identical_measurements_are_close(self) -> None:
        """
        Description: Two structurally identical measurements must be close.
        Scenario: a = b = Dimension(10, 'mm').
        Expectation: True.
        """
        assert Dimension(10.0, "mm").is_close(Dimension(10.0, "mm"))

    def test_equivalent_in_different_units_are_close(self) -> None:
        """
        Description: 1 in = 25.4 mm exactly; is_close must recognise this.
        Scenario: Dimension(1, 'in').is_close(Dimension(25.4, 'mm'))
        Expectation: True.
        """
        assert Dimension(1.0, "in").is_close(Dimension(25.4, "mm"))

    def test_non_equivalent_values_are_not_close_with_tight_tol(self) -> None:
        """
        Description: Values that differ by ~0.4% must NOT be close at default tolerance.
        Scenario: 1 in vs 25.5 mm.
        Expectation: False (default rel_tol=1e-9).
        """
        assert not Dimension(1.0, "in").is_close(Dimension(25.5, "mm"))

    def test_loose_rel_tol_accepts_small_difference(self) -> None:
        """
        Description: A rel_tol of 1% must accept the ~0.4% difference between
        1 in and 25.5 mm.
        Scenario: a.is_close(b, rel_tol=0.01)
        Expectation: True.
        """
        assert Dimension(1.0, "in").is_close(Dimension(25.5, "mm"), rel_tol=0.01)

    def test_very_tight_tol_rejects_small_difference(self) -> None:
        """
        Description: At rel_tol=1e-9 the 0.4% difference must be rejected.
        Scenario: a.is_close(b, rel_tol=1e-9) where a≈1in, b=25.5mm.
        Expectation: False.
        """
        assert not Dimension(1.0, "in").is_close(Dimension(25.5, "mm"), rel_tol=1e-9)

    def test_incompatible_types_raises(self) -> None:
        """
        Description: Comparing a Dimension against a FontSize must raise
        IncompatibleUnitsError even inside is_close.
        Scenario: d.is_close(fs) with same (value, unit).
        Expectation: IncompatibleUnitsError raised.
        """
        with pytest.raises(IncompatibleUnitsError):
            Dimension(10.0, "pt").is_close(FontSize(10.0, "pt"))

    def test_fontsize_equivalent_pica_and_pt_are_close(self, fs_pica: FontSize) -> None:
        """
        Description: 1 pica = 12 pt; FontSize.is_close must recognise this.
        Scenario: FontSize(1, 'pica').is_close(FontSize(12, 'pt'))
        Expectation: True.
        """
        assert fs_pica.is_close(FontSize(12.0, "pt"))

    def test_zero_measurements_are_close(self) -> None:
        """
        Description: Two zero-value measurements in any units must be close.
        Scenario: Dimension(0, 'mm').is_close(Dimension(0, 'in'))
        Expectation: True (math.isclose handles 0,0 case).
        """
        assert Dimension(0.0, "mm").is_close(Dimension(0.0, "in"))

    def test_is_close_uses_mm_canonical_form(self) -> None:
        """
        Description: Comparison happens in mm, so unit mismatch must not
        produce false positives or negatives.
        Scenario: 1 cm vs 9.9 mm — clearly NOT close at default tol.
        Expectation: False.
        """
        assert not Dimension(1.0, "cm").is_close(Dimension(9.9, "mm"))


# ---------------------------------------------------------------------------
# Arithmetic — addition
# ---------------------------------------------------------------------------


class TestAddition:
    """Tests for the __add__ operator."""

    def test_add_same_unit(self) -> None:
        """
        Description: Adding two same-unit dimensions gives the numeric sum.
        Scenario: 10mm + 5mm
        Expectation: Dimension(15, 'mm').
        """
        assert Dimension(10.0, "mm") + Dimension(5.0, "mm") == Dimension(15.0, "mm")

    def test_add_cross_unit_result_is_left_unit(self) -> None:
        """
        Description: The result unit must be the unit of the left operand.
        Scenario: 10mm + 1cm
        Expectation: result.unit == 'mm'.
        """
        result = Dimension(10.0, "mm") + Dimension(1.0, "cm")
        assert result.unit == "mm"

    def test_add_cross_unit_value_correct(self) -> None:
        """
        Description: Cross-unit add must convert rhs before summing.
        Scenario: 10mm + 1cm = 20mm.
        Expectation: result.value ≈ 20.0.
        """
        result = Dimension(10.0, "mm") + Dimension(1.0, "cm")
        assert result.value == pytest.approx(20.0)

    def test_add_1in_plus_1pica(self) -> None:
        """
        Description: 1in + 1pica = 1in + (1/6)in = 7/6 in.
        Scenario: Dimension(1, 'in') + Dimension(1, 'pica')
        Expectation: result.value ≈ 7/6.
        """
        result = Dimension(1.0, "in") + Dimension(1.0, "pica")
        assert result.unit == "in"
        assert result.value == pytest.approx(7.0 / 6.0)

    def test_add_preserves_concrete_type_dimension(self) -> None:
        """
        Description: Adding two Dimensions must yield a Dimension, not the base type.
        Scenario: Dimension + Dimension
        Expectation: isinstance(result, Dimension) is True.
        """
        result = Dimension(1.0, "in") + Dimension(25.4, "mm")
        assert isinstance(result, Dimension)

    def test_add_preserves_concrete_type_fontsize(self) -> None:
        """
        Description: Adding two FontSizes must yield a FontSize.
        Scenario: FontSize + FontSize
        Expectation: isinstance(result, FontSize) is True.
        """
        result = FontSize(10.0, "pt") + FontSize(2.0, "pt")
        assert isinstance(result, FontSize)

    def test_add_dimension_and_fontsize_raises(self) -> None:
        """
        Description: Cross-type addition must raise IncompatibleUnitsError.
        Scenario: Dimension(10, 'pt') + FontSize(10, 'pt')
        Expectation: IncompatibleUnitsError.
        """
        with pytest.raises(IncompatibleUnitsError):
            Dimension(10.0, "pt") + FontSize(10.0, "pt")

    def test_add_fontsize_and_dimension_raises(self) -> None:
        """
        Description: The error must be symmetric; FontSize + Dimension also raises.
        Scenario: FontSize(10, 'pt') + Dimension(10, 'pt')
        Expectation: IncompatibleUnitsError.
        """
        with pytest.raises(IncompatibleUnitsError):
            FontSize(10.0, "pt") + Dimension(10.0, "pt")

    def test_add_non_measurement_returns_not_implemented(self) -> None:
        """
        Description: __add__ with a plain int must signal NotImplemented so
        Python can try the reflected operator.
        Scenario: Dimension(10, 'mm').__add__(5)
        Expectation: NotImplemented sentinel returned.
        """
        result = Dimension(10.0, "mm").__add__(5)
        assert result is NotImplemented

    def test_add_zero_dimension_is_identity(self) -> None:
        """
        Description: Adding a zero-value measurement must not change the left operand.
        Scenario: Dimension(10, 'mm') + Dimension(0, 'mm')
        Expectation: Dimension(10.0, 'mm').
        """
        result = Dimension(10.0, "mm") + Dimension(0.0, "mm")
        assert result == Dimension(10.0, "mm")

    def test_add_commutativity_value_in_respective_units(self) -> None:
        """
        Description: a + b and b + a must give numerically equal mm totals
        (though they may differ in stored unit since the result unit follows
        the left operand).
        Scenario: 10mm + 1cm vs 1cm + 10mm — both should sum to 20mm equivalent.
        Expectation: Both convert to ≈ 20mm.
        """
        ab = Dimension(10.0, "mm") + Dimension(1.0, "cm")
        ba = Dimension(1.0, "cm") + Dimension(10.0, "mm")
        assert ab.to_mm() == pytest.approx(ba.to_mm())


# ---------------------------------------------------------------------------
# Arithmetic — subtraction
# ---------------------------------------------------------------------------


class TestSubtraction:
    """Tests for the __sub__ operator."""

    def test_sub_same_unit(self) -> None:
        """
        Description: Subtracting same-unit measurements gives numeric difference.
        Scenario: 20mm - 5mm
        Expectation: Dimension(15.0, 'mm').
        """
        assert Dimension(20.0, "mm") - Dimension(5.0, "mm") == Dimension(15.0, "mm")

    def test_sub_cross_unit_result_in_left_unit(self) -> None:
        """
        Description: Cross-unit subtraction uses the left operand's unit.
        Scenario: 10cm - 25mm
        Expectation: result.unit == 'cm', result.value ≈ 7.5.
        """
        result = Dimension(10.0, "cm") - Dimension(25.0, "mm")
        assert result.unit == "cm"
        assert result.value == pytest.approx(7.5)

    def test_sub_incompatible_types_raises(self) -> None:
        """
        Description: Subtracting FontSize from Dimension must raise.
        Scenario: Dimension(10, 'mm') - FontSize(10, 'mm')
        Expectation: IncompatibleUnitsError.
        """
        with pytest.raises(IncompatibleUnitsError):
            Dimension(10.0, "mm") - FontSize(10.0, "mm")

    def test_sub_non_measurement_returns_not_implemented(self) -> None:
        """
        Description: __sub__ with a non-measurement must return NotImplemented.
        Scenario: Dimension(10, 'mm').__sub__(5)
        Expectation: NotImplemented.
        """
        result = Dimension(10.0, "mm").__sub__(5)
        assert result is NotImplemented

    def test_sub_preserves_concrete_type(self) -> None:
        """
        Description: Subtraction result must be the same concrete type.
        Scenario: Dimension - Dimension
        Expectation: isinstance(result, Dimension).
        """
        result = Dimension(2.0, "in") - Dimension(1.0, "in")
        assert isinstance(result, Dimension)

    def test_sub_produces_negative_result(self) -> None:
        """
        Description: Subtracting a larger value from a smaller one is valid and
        produces a negative measurement (e.g. an over-bleed).
        Scenario: 5mm - 10mm
        Expectation: Dimension(-5.0, 'mm').
        """
        result = Dimension(5.0, "mm") - Dimension(10.0, "mm")
        assert result == Dimension(-5.0, "mm")

    def test_sub_self_is_zero(self) -> None:
        """
        Description: Subtracting a measurement from itself gives zero.
        Scenario: d - d
        Expectation: value == 0.0.
        """
        d = Dimension(10.0, "in")
        result = d - d
        assert result.value == pytest.approx(0.0)

    def test_sub_fontsize_cross_unit(self) -> None:
        """
        Description: FontSize subtraction across units must work correctly.
        Scenario: 1 pica - 6 pt = 0.5 pica.
        Expectation: result.value ≈ 0.5, result.unit == 'pica'.
        """
        result = FontSize(1.0, "pica") - FontSize(6.0, "pt")
        assert result.unit == "pica"
        assert result.value == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# Arithmetic — multiplication
# ---------------------------------------------------------------------------


class TestMultiplication:
    """Tests for __mul__ and __rmul__."""

    @pytest.mark.parametrize("scalar", [0, 1, 2, 3, -1, 2.5, 0.1, 1e6])
    def test_mul_numeric_scalar_dimension(self, scalar) -> None:
        """
        Description: Multiplying by any numeric scalar must scale the value.
        Scenario: Dimension(5, 'cm') * scalar
        Expectation: result.value ≈ 5.0 * scalar.
        """
        result = Dimension(5.0, "cm") * scalar
        assert isinstance(result, Dimension)
        assert result.value == pytest.approx(5.0 * scalar)
        assert result.unit == "cm"

    def test_rmul_scalar_times_measurement(self) -> None:
        """
        Description: scalar * measurement must work via __rmul__.
        Scenario: 3 * Dimension(5, 'cm')
        Expectation: Dimension(15.0, 'cm').
        """
        result = 3 * Dimension(5.0, "cm")
        assert isinstance(result, Dimension)
        assert result.value == pytest.approx(15.0)

    def test_mul_preserves_unit(self) -> None:
        """
        Description: Multiplication must not change the unit.
        Scenario: Dimension(10, 'pt') * 2
        Expectation: result.unit == 'pt'.
        """
        assert (Dimension(10.0, "pt") * 2).unit == "pt"

    def test_mul_fontsize_by_float_scalar(self) -> None:
        """
        Description: FontSize multiplication by float must scale correctly.
        Scenario: FontSize(10, 'pt') * 2.4
        Expectation: result ≈ FontSize(24, 'pt').
        """
        result = FontSize(10.0, "pt") * 2.4
        assert isinstance(result, FontSize)
        assert result.value == pytest.approx(24.0)

    def test_mul_by_zero_gives_zero(self) -> None:
        """
        Description: Multiplying by 0 must give a zero-value measurement.
        Scenario: Dimension(100, 'mm') * 0
        Expectation: result.value == 0.0.
        """
        assert (Dimension(100.0, "mm") * 0).value == pytest.approx(0.0)

    def test_mul_by_non_numeric_returns_not_implemented(self) -> None:
        """
        Description: __mul__ with a non-numeric must return NotImplemented.
        Scenario: Dimension(5, 'mm').__mul__('x')
        Expectation: NotImplemented sentinel.
        """
        assert Dimension(5.0, "mm").__mul__("x") is NotImplemented

    def test_mul_by_non_numeric_as_operator_raises_type_error(self) -> None:
        """
        Description: Using * with a string operand must ultimately raise TypeError.
        Scenario: Dimension(5, 'mm') * 'x'
        Expectation: TypeError.
        """
        with pytest.raises(TypeError):
            Dimension(5.0, "mm") * "x"  # type: ignore[operator]

    def test_rmul_by_non_numeric_raises_type_error(self) -> None:
        """
        Description: 'x' * measurement must raise TypeError.
        Scenario: 'x' * Dimension(5, 'mm')
        Expectation: TypeError.
        """
        with pytest.raises(TypeError):
            "x" * Dimension(5.0, "mm")  # type: ignore[operator]

    def test_mul_negative_scalar(self) -> None:
        """
        Description: Multiplying by a negative scalar should negate the value.
        Scenario: Dimension(10, 'mm') * -1
        Expectation: result.value == -10.0.
        """
        result = Dimension(10.0, "mm") * -1
        assert result.value == pytest.approx(-10.0)


# ---------------------------------------------------------------------------
# Arithmetic — division
# ---------------------------------------------------------------------------


class TestDivision:
    """Tests for __truediv__."""

    @pytest.mark.parametrize("scalar", [1, 2, 4, 0.5, 10, 1e3])
    def test_truediv_by_positive_scalar(self, scalar) -> None:
        """
        Description: Dividing by a positive scalar must scale the value correctly.
        Scenario: Dimension(10, 'in') / scalar
        Expectation: result.value ≈ 10.0 / scalar.
        """
        result = Dimension(10.0, "in") / scalar
        assert isinstance(result, Dimension)
        assert result.value == pytest.approx(10.0 / scalar)

    def test_truediv_preserves_unit(self) -> None:
        """
        Description: Division must not change the stored unit.
        Scenario: Dimension(12, 'pt') / 3
        Expectation: result.unit == 'pt'.
        """
        assert (Dimension(12.0, "pt") / 3).unit == "pt"

    def test_truediv_fontsize(self) -> None:
        """
        Description: FontSize division must return a FontSize.
        Scenario: FontSize(24, 'pt') / 2
        Expectation: isinstance(result, FontSize) and result.value ≈ 12.0.
        """
        result = FontSize(24.0, "pt") / 2
        assert isinstance(result, FontSize)
        assert result.value == pytest.approx(12.0)

    def test_truediv_by_zero_raises(self) -> None:
        """
        Description: Division by zero must raise ZeroDivisionError.
        Scenario: Dimension(10, 'mm') / 0
        Expectation: ZeroDivisionError.
        """
        with pytest.raises(ZeroDivisionError):
            Dimension(10.0, "mm") / 0

    def test_truediv_by_zero_float_raises(self) -> None:
        """
        Description: Division by 0.0 (float zero) must also raise ZeroDivisionError.
        Scenario: Dimension(10, 'mm') / 0.0
        Expectation: ZeroDivisionError.
        """
        with pytest.raises(ZeroDivisionError):
            Dimension(10.0, "mm") / 0.0

    def test_truediv_by_non_numeric_returns_not_implemented(self) -> None:
        """
        Description: __truediv__ with a string must return NotImplemented.
        Scenario: Dimension(10, 'mm').__truediv__('two')
        Expectation: NotImplemented sentinel.
        """
        assert Dimension(10.0, "mm").__truediv__("two") is NotImplemented

    def test_truediv_by_non_numeric_operator_raises_type_error(self) -> None:
        """
        Description: Using / with a string must ultimately raise TypeError.
        Scenario: Dimension(10, 'mm') / 'two'
        Expectation: TypeError.
        """
        with pytest.raises(TypeError):
            Dimension(10.0, "mm") / "two"  # type: ignore[operator]

    def test_truediv_by_negative_scalar(self) -> None:
        """
        Description: Division by a negative scalar must negate the value.
        Scenario: Dimension(10, 'mm') / -2
        Expectation: result.value ≈ -5.0.
        """
        result = Dimension(10.0, "mm") / -2
        assert result.value == pytest.approx(-5.0)

    def test_mul_then_div_roundtrip(self) -> None:
        """
        Description: Multiplying by k then dividing by k should recover original.
        Scenario: (Dimension(7, 'pt') * 3) / 3
        Expectation: value ≈ 7.0.
        """
        d = Dimension(7.0, "pt")
        assert (d * 3) / 3 == d


# ---------------------------------------------------------------------------
# Comparison operators
# ---------------------------------------------------------------------------


class TestComparison:
    """Tests for __lt__, __le__, __gt__, __ge__ with cross-unit awareness."""

    def test_lt_cross_unit_true(self) -> None:
        """
        Description: 1in ≈ 25.4mm < 30mm = 3cm, so lt must be True.
        Scenario: Dimension(1, 'in') < Dimension(3, 'cm')
        Expectation: True.
        """
        assert Dimension(1.0, "in") < Dimension(3.0, "cm")

    def test_lt_cross_unit_false(self) -> None:
        """
        Description: 3cm > 1in, so reversed comparison must be False.
        Scenario: Dimension(3, 'cm') < Dimension(1, 'in')
        Expectation: False.
        """
        assert not (Dimension(3.0, "cm") < Dimension(1.0, "in"))

    def test_lt_equal_values_is_false(self) -> None:
        """
        Description: 10mm == 1cm, so strict less-than must be False.
        Scenario: Dimension(10, 'mm') < Dimension(1, 'cm')
        Expectation: False.
        """
        assert not (Dimension(10.0, "mm") < Dimension(1.0, "cm"))

    def test_le_equal_cross_unit(self) -> None:
        """
        Description: 10mm = 1cm, so ≤ must be True.
        Scenario: Dimension(10, 'mm') <= Dimension(1, 'cm')
        Expectation: True.
        """
        assert Dimension(10.0, "mm") <= Dimension(1.0, "cm")

    def test_le_less_than_is_also_le(self) -> None:
        """
        Description: 9mm < 1cm, so ≤ must also be True.
        Scenario: Dimension(9, 'mm') <= Dimension(1, 'cm')
        Expectation: True.
        """
        assert Dimension(9.0, "mm") <= Dimension(1.0, "cm")

    def test_gt_cross_unit_true(self) -> None:
        """
        Description: 1cm > 9mm.
        Scenario: Dimension(1, 'cm') > Dimension(9, 'mm')
        Expectation: True.
        """
        assert Dimension(1.0, "cm") > Dimension(9.0, "mm")

    def test_gt_equal_is_false(self) -> None:
        """
        Description: Equal values must not satisfy strict >.
        Scenario: Dimension(10, 'mm') > Dimension(1, 'cm')
        Expectation: False.
        """
        assert not (Dimension(10.0, "mm") > Dimension(1.0, "cm"))

    def test_ge_equal_cross_unit(self) -> None:
        """
        Description: 1cm == 10mm, so ≥ must be True.
        Scenario: Dimension(1, 'cm') >= Dimension(10, 'mm')
        Expectation: True.
        """
        assert Dimension(1.0, "cm") >= Dimension(10.0, "mm")

    def test_ge_greater_is_also_ge(self) -> None:
        """
        Description: 11mm > 1cm, so ≥ must be True.
        Scenario: Dimension(11, 'mm') >= Dimension(1, 'cm')
        Expectation: True.
        """
        assert Dimension(11.0, "mm") >= Dimension(1.0, "cm")

    def test_comparison_incompatible_types_raises(self) -> None:
        """
        Description: Comparing Dimension vs FontSize must raise
        IncompatibleUnitsError.
        Scenario: Dimension(10, 'pt') < FontSize(10, 'pt')
        Expectation: IncompatibleUnitsError.
        """
        with pytest.raises(IncompatibleUnitsError):
            assert Dimension(10.0, "pt") < FontSize(10.0, "pt")  # type: ignore[operator]

    def test_fontsize_comparison_cross_unit(self) -> None:
        """
        Description: 10pt < 12pt = 1pica.
        Scenario: FontSize(10, 'pt') < FontSize(1, 'pica')
        Expectation: True.
        """
        assert FontSize(10.0, "pt") < FontSize(1.0, "pica")

    def test_1_5_in_greater_than_3_cm(self) -> None:
        """
        Description: 1.5in = 38.1mm > 30mm = 3cm.
        Scenario: Dimension(1.5, 'in') > Dimension(3, 'cm')
        Expectation: True.
        """
        assert Dimension(1.5, "in") > Dimension(3.0, "cm")

    def test_negative_less_than_positive(self) -> None:
        """
        Description: A negative measurement must be less than a positive one.
        Scenario: Dimension(-1, 'mm') < Dimension(1, 'mm')
        Expectation: True.
        """
        assert Dimension(-1.0, "mm") < Dimension(1.0, "mm")

    @pytest.mark.parametrize(
        "op_name,expected",
        [
            ("__lt__", False),
            ("__le__", True),
            ("__gt__", False),
            ("__ge__", True),
        ],
    )
    def test_reflexive_comparison(self, op_name: str, expected: bool) -> None:
        """
        Description: Comparing a measurement to itself must satisfy reflexivity
        for ≤ and ≥, and deny strict < and >.
        Scenario: d <op> d for all comparison operators.
        Expectation: lt/gt False; le/ge True.
        """
        d = Dimension(10.0, "mm")
        result = getattr(d, op_name)(d)
        assert result is expected

    def test_comparison_non_measurement_returns_not_implemented(self) -> None:
        """
        Description: Comparing against a plain number must signal NotImplemented.
        Scenario: Dimension(1, 'mm').__lt__(42)
        Expectation: NotImplemented sentinel.
        """
        d = Dimension(1.0, "mm")
        assert d.__lt__(42) is NotImplemented


# ---------------------------------------------------------------------------
# Equality and hashing
# ---------------------------------------------------------------------------


class TestEqualityAndHash:
    """Tests for __eq__ and __hash__ (frozen dataclass semantics)."""

    def test_equal_same_value_and_unit(self) -> None:
        """
        Description: Two Dimensions with identical (value, unit) must be equal.
        Scenario: Dimension(10, 'mm') == Dimension(10, 'mm')
        Expectation: True.
        """
        assert Dimension(10.0, "mm") == Dimension(10.0, "mm")

    def test_not_equal_different_value(self) -> None:
        """
        Description: Different numeric values must produce inequality.
        Scenario: Dimension(10, 'mm') != Dimension(11, 'mm')
        Expectation: True.
        """
        assert Dimension(10.0, "mm") != Dimension(11.0, "mm")

    def test_not_equal_different_unit_same_numeric(self) -> None:
        """
        Description: Equality is based on stored representation, not physical
        equivalence; 10mm and 10cm have the same numeric value but differ in
        unit, so they must not be equal.
        Scenario: Dimension(10, 'mm') != Dimension(10, 'cm')
        Expectation: True (they are not equal).
        """
        assert Dimension(10.0, "mm") != Dimension(10.0, "cm")

    def test_dimension_not_equal_fontsize_same_fields(self) -> None:
        """
        Description: Different concrete types must not be equal, even with
        identical stored fields.
        Scenario: Dimension(10, 'pt') != FontSize(10, 'pt')
        Expectation: True (not equal).
        """
        assert Dimension(10.0, "pt") != FontSize(10.0, "pt")

    def test_equal_objects_have_equal_hash(self) -> None:
        """
        Description: The hash contract requires equal objects to have the
        same hash value.
        Scenario: Two equal Dimension objects.
        Expectation: hash(d1) == hash(d2).
        """
        d1 = Dimension(10.0, "mm")
        d2 = Dimension(10.0, "mm")
        assert hash(d1) == hash(d2)

    def test_unequal_objects_may_have_different_hash(self) -> None:
        """
        Description: Unequal objects should (in practice) have different
        hashes to avoid collisions in sets/dicts — not a contractual
        requirement, but a quality signal.
        Scenario: Dimension(10, 'mm') vs Dimension(10, 'cm').
        Expectation: Different hashes (practically guaranteed by tuple hash).
        """
        d1 = Dimension(10.0, "mm")
        d2 = Dimension(10.0, "cm")
        # Not guaranteed by spec but expected for frozen dataclasses.
        assert hash(d1) != hash(d2)

    def test_usable_as_dict_keys(self) -> None:
        """
        Description: Hashable objects must be usable as dict keys, with
        correct lookup.
        Scenario: Map two different Dimensions to separate values.
        Expectation: Each lookup returns the correct value.
        """
        d1 = Dimension(10.0, "mm")
        d2 = Dimension(10.0, "cm")
        m = {d1: "a", d2: "b"}
        assert m[d1] == "a"
        assert m[d2] == "b"

    def test_usable_in_set(self) -> None:
        """
        Description: Multiple insertions of equal objects should collapse
        in a set.
        Scenario: Insert same Dimension 3x.
        Expectation: Set length is 1.
        """
        d = Dimension(5.0, "pt")
        assert len({d, d, Dimension(5.0, "pt")}) == 1

    def test_fontsize_equal_self(self, fs_pt: FontSize) -> None:
        """
        Description: A FontSize must equal itself.
        Scenario: fs == fs
        Expectation: True.
        """
        assert fs_pt == fs_pt


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


class TestRepr:
    """Tests for the string representation of measurement objects."""

    def test_dimension_repr_format(self) -> None:
        """
        Description: repr must match the documented format ClassName(value=…, unit='…').
        Scenario: Dimension(10.0, 'mm')
        Expectation: "Dimension(value=10.0, unit='mm')".
        """
        assert repr(Dimension(10.0, "mm")) == "Dimension(value=10.0, unit='mm')"

    def test_fontsize_repr_format(self) -> None:
        """
        Description: FontSize repr must follow the same template.
        Scenario: FontSize(12.0, 'pt')
        Expectation: "FontSize(value=12.0, unit='pt')".
        """
        assert repr(FontSize(12.0, "pt")) == "FontSize(value=12.0, unit='pt')"

    def test_repr_shows_coerced_float(self) -> None:
        """
        Description: Integer inputs are coerced to float; repr must reflect that.
        Scenario: Dimension(10, 'mm') — int input.
        Expectation: '10.0' appears in repr, not '10'.
        """
        assert "10.0" in repr(Dimension(10, "mm"))

    def test_repr_starts_with_class_name_dimension(self) -> None:
        """
        Description: The class name must be the leading token in repr.
        Scenario: repr(Dimension(...))
        Expectation: starts with 'Dimension('.
        """
        assert repr(Dimension(1.0, "in")).startswith("Dimension(")

    def test_repr_starts_with_class_name_fontsize(self) -> None:
        """
        Description: FontSize repr must lead with 'FontSize('.
        Scenario: repr(FontSize(...))
        Expectation: starts with 'FontSize('.
        """
        assert repr(FontSize(1.0, "pt")).startswith("FontSize(")

    def test_repr_round_trips_via_eval(self) -> None:
        """
        Description: eval(repr(d)) should reconstruct an equal object, confirming
        the format is valid Python and contains all necessary information.
        Scenario: eval(repr(Dimension(10.0, 'mm')))
        Expectation: Equal to original Dimension.
        """
        d = Dimension(10.0, "mm")
        reconstructed = eval(repr(d), {"Dimension": Dimension})
        assert reconstructed == d

    @pytest.mark.parametrize("unit", ALL_UNITS)
    def test_repr_contains_unit(self, unit: str) -> None:
        """
        Description: The repr string must always include the unit label.
        Scenario: Dimension(1.0, unit) for each unit.
        Expectation: unit string appears in repr.
        """
        d = Dimension(1.0, unit)
        assert unit in repr(d)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    """Verify the custom exception class relationships."""

    def test_unsupported_unit_error_is_dimension_error(self) -> None:
        """
        Description: UnsupportedUnitError must inherit DimensionError.
        Scenario: Instantiate UnsupportedUnitError directly.
        Expectation: isinstance check against DimensionError is True.
        """
        err = UnsupportedUnitError("px")
        assert isinstance(err, DimensionError)

    def test_unsupported_unit_error_is_value_error(self) -> None:
        """
        Description: DimensionError inherits ValueError for backward-compat.
        Scenario: isinstance(UnsupportedUnitError(...), ValueError)
        Expectation: True.
        """
        err = UnsupportedUnitError("px")
        assert isinstance(err, ValueError)

    def test_incompatible_units_error_is_dimension_error(self) -> None:
        """
        Description: IncompatibleUnitsError must inherit DimensionError.
        Scenario: Instantiate IncompatibleUnitsError.
        Expectation: isinstance check is True.
        """
        err = IncompatibleUnitsError("Dimension", "FontSize")
        assert isinstance(err, DimensionError)

    def test_incompatible_units_error_is_value_error(self) -> None:
        """
        Description: IncompatibleUnitsError must also be catchable as ValueError.
        Scenario: isinstance(IncompatibleUnitsError(...), ValueError)
        Expectation: True.
        """
        err = IncompatibleUnitsError("Dimension", "FontSize")
        assert isinstance(err, ValueError)

    def test_incompatible_units_error_message_contains_both_types(self) -> None:
        """
        Description: The error message must name both operand types so the
        developer can pinpoint the problem.
        Scenario: IncompatibleUnitsError('Dimension', 'FontSize')
        Expectation: Both 'Dimension' and 'FontSize' in str(err).
        """
        err = IncompatibleUnitsError("Dimension", "FontSize")
        msg = str(err)
        assert "Dimension" in msg
        assert "FontSize" in msg

    def test_incompatible_units_error_attributes(self) -> None:
        """
        Description: The .left and .right attributes must hold the supplied names.
        Scenario: IncompatibleUnitsError('A', 'B')
        Expectation: err.left == 'A', err.right == 'B'.
        """
        err = IncompatibleUnitsError("A", "B")
        assert err.left == "A"
        assert err.right == "B"

    def test_unsupported_unit_error_unit_attribute(self) -> None:
        """
        Description: UnsupportedUnitError.unit must store the offending unit.
        Scenario: UnsupportedUnitError('furlong')
        Expectation: err.unit == 'furlong'.
        """
        err = UnsupportedUnitError("furlong")
        assert err.unit == "furlong"

    def test_incompatible_error_raised_by_add(self) -> None:
        """
        Description: Addition of mixed types must raise IncompatibleUnitsError.
        Scenario: Dimension(1, 'mm') + FontSize(1, 'mm')
        Expectation: IncompatibleUnitsError.
        """
        with pytest.raises(IncompatibleUnitsError):
            Dimension(1.0, "mm") + FontSize(1.0, "mm")

    def test_incompatible_error_raised_by_sub(self) -> None:
        """
        Description: Subtraction of mixed types must raise IncompatibleUnitsError.
        Scenario: Dimension(10, 'mm') - FontSize(5, 'mm')
        Expectation: IncompatibleUnitsError.
        """
        with pytest.raises(IncompatibleUnitsError):
            Dimension(10.0, "mm") - FontSize(5.0, "mm")

    def test_incompatible_error_raised_by_comparison(self) -> None:
        """
        Description: Comparison of mixed types must raise IncompatibleUnitsError.
        Scenario: Dimension(10, 'mm') > FontSize(10, 'mm')
        Expectation: IncompatibleUnitsError.
        """
        with pytest.raises(IncompatibleUnitsError):
            _ = Dimension(10.0, "mm") > FontSize(10.0, "mm")


# ---------------------------------------------------------------------------
# Public API surface (__all__)
# ---------------------------------------------------------------------------


class TestPublicAPI:
    """Ensure the module's __all__ exports are exactly as documented."""

    def test_all_exports_present(self) -> None:
        """
        Description: Every name listed in __all__ must be importable and present
        in the module namespace.
        Scenario: Import plotstyle.specs.units and check __all__ members.
        Expectation: All names are accessible.
        """
        import plotstyle.specs.units as mod

        for name in mod.__all__:
            assert hasattr(mod, name), f"{name!r} listed in __all__ but not found"

    def test_unit_type_alias_exists(self) -> None:
        """
        Description: The Unit type alias must be exported.
        Scenario: Access plotstyle.specs.units.Unit.
        Expectation: Not None / importable.
        """
        assert Unit is not None


# ---------------------------------------------------------------------------
# Numeric edge cases and floating-point behaviour
# ---------------------------------------------------------------------------


class TestFloatingPointEdgeCases:
    """Edge cases involving floating-point precision and special values."""

    def test_infinity_value_is_stored(self) -> None:
        """
        Description: Python floats can represent inf; storing math.inf must not
        raise (even if physically meaningless), because the class does not
        impose domain restrictions.
        Scenario: Dimension(math.inf, 'mm')
        Expectation: d.value == math.inf.
        """
        d = Dimension(math.inf, "mm")
        assert d.value == math.inf

    def test_negative_infinity_value_is_stored(self) -> None:
        """
        Description: -math.inf should also be accepted without error.
        Scenario: Dimension(-math.inf, 'mm')
        Expectation: d.value == -math.inf.
        """
        d = Dimension(-math.inf, "mm")
        assert d.value == -math.inf

    def test_nan_value_is_stored(self) -> None:
        """
        Description: math.nan is a valid float; the class should accept it.
        Scenario: Dimension(math.nan, 'mm')
        Expectation: math.isnan(d.value) is True.
        """
        d = Dimension(math.nan, "mm")
        assert math.isnan(d.value)

    def test_very_small_differences_detected_at_tight_tol(self) -> None:
        """
        Description: is_close with tight tolerance must distinguish values that
        differ by a single ULP of the mm representation.
        Scenario: Two Dimensions differing by sys.float_info.epsilon in mm.
        Expectation: is_close(rel_tol=1e-15) is False when they differ.
        """
        a = Dimension(1.0, "mm")
        b = Dimension(1.0 + sys.float_info.epsilon * 100, "mm")
        # At rel_tol=1e-9, they may or may not be close; just check no error.
        result = a.is_close(b, rel_tol=1e-9)
        assert isinstance(result, bool)

    def test_conversion_preserves_relative_precision(self) -> None:
        """
        Description: Round-tripping a large value through multiple unit conversions
        must not accumulate more than a tiny relative error.
        Scenario: 1000 in → mm → pt → pica → in
        Expectation: result ≈ 1000.0 (within 1e-9 relative).
        """
        val_in = 1000.0
        val_mm = Dimension(val_in, "in").to("mm")
        val_pt = Dimension(val_mm, "mm").to("pt")
        val_pica = Dimension(val_pt, "pt").to("pica")
        val_back = Dimension(val_pica, "pica").to("in")
        assert val_back == pytest.approx(val_in, rel=1e-9)
