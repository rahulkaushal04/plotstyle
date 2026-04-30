"""Test suite for ``plotstyle.engine.rcparams``.

Tests cover :func:`build_rcparams`, :func:`_resolve_latex_mode`,
:func:`_compute_figure_size`, :func:`_compute_base_font_size`,
:class:`LatexNotFoundError`, and the :data:`SAFETY_PARAMS` constant.
"""

from __future__ import annotations

import math
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
from plotstyle.engine.rcparams import (
    _DISPLAY_DPI,
    _FONTTYPE_TRUETYPE,
    _GOLDEN_RATIO,
    SAFETY_PARAMS,
    LatexNotFoundError,
    _compute_base_font_size,
    _compute_figure_size,
    _resolve_latex_mode,
    build_rcparams,
)

# ===========================================================================
# Helpers / Fixtures
# ===========================================================================


def _make_spec(
    *,
    single_column_mm: float = 88.9,
    min_font_pt: float = 6.0,
    max_font_pt: float = 10.0,
    min_dpi: int = 300,
    editable_text: bool = True,
    min_weight_pt: float = 0.5,
    target_font_pt: float | None = None,
) -> MagicMock:
    """Return a fully-configured :class:`~unittest.mock.MagicMock` that looks
    like a :class:`~plotstyle.specs.schema.JournalSpec`."""
    spec = MagicMock()
    spec.dimensions.single_column_mm = single_column_mm
    spec.typography.min_font_pt = min_font_pt
    spec.typography.max_font_pt = max_font_pt
    spec.export.min_dpi = min_dpi
    spec.export.editable_text = editable_text
    spec.line.min_weight_pt = min_weight_pt
    spec.typography.target_font_pt = target_font_pt
    return spec


@pytest.fixture()
def default_spec() -> MagicMock:
    """A realistic journal spec close to Nature's single-column width."""
    return _make_spec()


@pytest.fixture()
def wide_spec() -> MagicMock:
    """A journal spec with a wide double-column width."""
    return _make_spec(single_column_mm=183.0)


@pytest.fixture()
def narrow_spec() -> MagicMock:
    """A journal spec with an unusually narrow column (40 mm)."""
    return _make_spec(single_column_mm=40.0)


# Patch targets used throughout
_FONTS_SELECT_BEST = "plotstyle.engine.rcparams.select_best"
_DETECT_LATEX = "plotstyle.engine.rcparams.detect_latex"
_CONFIGURE_LATEX = "plotstyle.engine.rcparams.configure_latex"
_DIMENSION_CLS = "plotstyle.engine.rcparams.Dimension"


def _patch_select_best(font_name: str = "Helvetica") -> Any:
    """Return a ``patch`` context manager for :func:`select_best`."""
    return patch(_FONTS_SELECT_BEST, return_value=(font_name, MagicMock()))


def _patch_dimension(inches: float = 3.5) -> Any:
    """Return a ``patch`` context manager for :class:`Dimension`."""
    dim_instance = MagicMock()
    dim_instance.to_inches.return_value = inches
    return patch(_DIMENSION_CLS, return_value=dim_instance)


# ===========================================================================
# SAFETY_PARAMS
# ===========================================================================


class TestSafetyParams:
    """Tests for the :data:`SAFETY_PARAMS` module-level constant."""

    def test_safety_params_is_frozenset(self) -> None:
        """
        Description: Verify that SAFETY_PARAMS is an immutable frozenset.
        Scenario: Direct type inspection of the constant.
        Expectation: isinstance check passes; no AttributeError on frozenset ops.
        """
        assert isinstance(SAFETY_PARAMS, frozenset)

    def test_safety_params_contains_pdf_fonttype(self) -> None:
        """
        Description: Ensure 'pdf.fonttype' is in SAFETY_PARAMS.
        Scenario: Membership test on the frozenset.
        Expectation: 'pdf.fonttype' is present.
        """
        assert "pdf.fonttype" in SAFETY_PARAMS

    def test_safety_params_contains_ps_fonttype(self) -> None:
        """
        Description: Ensure 'ps.fonttype' is in SAFETY_PARAMS.
        Scenario: Membership test on the frozenset.
        Expectation: 'ps.fonttype' is present.
        """
        assert "ps.fonttype" in SAFETY_PARAMS

    def test_safety_params_is_immutable(self) -> None:
        """
        Description: Verify that SAFETY_PARAMS cannot be mutated.
        Scenario: Attempt to call .add() on a frozenset.
        Expectation: AttributeError is raised, confirming immutability.
        """
        with pytest.raises(AttributeError):
            SAFETY_PARAMS.add("new.key")  # type: ignore[attr-defined]

    def test_safety_params_length(self) -> None:
        """
        Description: Verify SAFETY_PARAMS covers exactly the expected keys.
        Scenario: Count elements in the frozenset.
        Expectation: Exactly 2 keys are present (pdf.fonttype and ps.fonttype).
        """
        assert len(SAFETY_PARAMS) == 2


# ===========================================================================
# LatexNotFoundError
# ===========================================================================


class TestLatexNotFoundError:
    """Tests for :class:`LatexNotFoundError`."""

    def test_is_runtime_error_subclass(self) -> None:
        """
        Description: LatexNotFoundError must be a RuntimeError subclass.
        Scenario: Raise LatexNotFoundError and catch as RuntimeError.
        Expectation: except RuntimeError clause is triggered.
        """
        with pytest.raises(RuntimeError):
            raise LatexNotFoundError()

    def test_default_message_contains_hint(self) -> None:
        """
        Description: Default message should mention 'latex' binary and PATH.
        Scenario: Instantiate with no arguments and inspect str().
        Expectation: Message includes 'latex' and 'PATH'.
        """
        exc = LatexNotFoundError()
        msg = str(exc)
        assert "latex" in msg.lower()
        assert "PATH" in msg

    def test_custom_message_is_preserved(self) -> None:
        """
        Description: A custom message passed to __init__ should not be altered.
        Scenario: Instantiate with a bespoke string and read back str().
        Expectation: str(exc) equals the provided message.
        """
        custom = "Custom LaTeX error for test."
        exc = LatexNotFoundError(custom)
        assert str(exc) == custom

    def test_can_be_caught_as_latex_not_found_error(self) -> None:
        """
        Description: LatexNotFoundError should be catchable by its own type.
        Scenario: Raise and catch LatexNotFoundError directly.
        Expectation: except LatexNotFoundError clause is triggered.
        """
        with pytest.raises(LatexNotFoundError):
            raise LatexNotFoundError()

    def test_empty_string_message(self) -> None:
        """
        Description: An explicitly empty string message should not trigger the default.
        Scenario: Pass '' as the message.
        Expectation: str(exc) is ''.
        """
        exc = LatexNotFoundError("")
        assert str(exc) == ""


# ===========================================================================
# _resolve_latex_mode
# ===========================================================================


class TestResolveLatexMode:
    """Tests for :func:`_resolve_latex_mode`."""

    def test_false_returns_false_without_checking_latex(self) -> None:
        """
        Description: latex=False should return False immediately and never
                     call detect_latex.
        Scenario: Call _resolve_latex_mode(False) with detect_latex patched.
        Expectation: Returns False; detect_latex is never invoked.
        """
        with patch(_DETECT_LATEX) as mock_detect:
            result = _resolve_latex_mode(False)
        assert result is False
        mock_detect.assert_not_called()

    def test_true_returns_true_when_latex_available(self) -> None:
        """
        Description: latex=True should return True when detect_latex() is True.
        Scenario: detect_latex patched to return True; call with latex=True.
        Expectation: Returns True without raising.
        """
        with patch(_DETECT_LATEX, return_value=True):
            assert _resolve_latex_mode(True) is True

    def test_true_raises_when_latex_unavailable(self) -> None:
        """
        Description: latex=True must raise LatexNotFoundError when detect_latex
                     returns False.
        Scenario: detect_latex patched to return False; call with latex=True.
        Expectation: LatexNotFoundError is raised.
        """
        with patch(_DETECT_LATEX, return_value=False), pytest.raises(LatexNotFoundError):
            _resolve_latex_mode(True)

    def test_auto_returns_true_when_latex_available(self) -> None:
        """
        Description: latex='auto' should return True when LaTeX is present.
        Scenario: detect_latex patched to True; call with latex='auto'.
        Expectation: Returns True.
        """
        with patch(_DETECT_LATEX, return_value=True):
            assert _resolve_latex_mode("auto") is True

    def test_auto_returns_false_when_latex_unavailable(self) -> None:
        """
        Description: latex='auto' should silently degrade (return False) when
                     LaTeX is absent.
        Scenario: detect_latex patched to False; call with latex='auto'.
        Expectation: Returns False without raising.
        """
        with patch(_DETECT_LATEX, return_value=False):
            assert _resolve_latex_mode("auto") is False

    def test_auto_does_not_raise_when_latex_missing(self) -> None:
        """
        Description: Unlike latex=True, latex='auto' must never raise even if
                     no LaTeX binary is found.
        Scenario: detect_latex returns False; call with latex='auto'.
        Expectation: No exception of any kind is raised.
        """
        with patch(_DETECT_LATEX, return_value=False):
            try:
                _resolve_latex_mode("auto")
            except Exception as exc:
                pytest.fail(f"Unexpected exception: {exc}")


# ===========================================================================
# _compute_figure_size
# ===========================================================================


class TestComputeFigureSize:
    """Tests for :func:`_compute_figure_size`."""

    def test_width_derived_from_dimension_conversion(self, default_spec: MagicMock) -> None:
        """
        Description: Width in inches must equal the value returned by
                     Dimension.to_inches() for the spec's single_column_mm.
        Scenario: Dimension.to_inches patched to return 3.5; default_spec used.
        Expectation: First element of return tuple equals 3.5.
        """
        with _patch_dimension(3.5):
            width_in, _ = _compute_figure_size(default_spec)
        assert width_in == pytest.approx(3.5)

    def test_height_is_width_over_golden_ratio(self, default_spec: MagicMock) -> None:
        """
        Description: Height must equal width / φ (golden ratio).
        Scenario: Dimension.to_inches patched to 3.5; derive expected height.
        Expectation: height_in ≈ 3.5 / 1.618...
        """
        expected_width = 3.5
        with _patch_dimension(expected_width):
            width_in, height_in = _compute_figure_size(default_spec)
        assert height_in == pytest.approx(width_in / _GOLDEN_RATIO)

    def test_returns_two_floats(self, default_spec: MagicMock) -> None:
        """
        Description: Return type must be a 2-tuple of floats.
        Scenario: Normal call with default_spec and patched Dimension.
        Expectation: tuple of length 2, both elements are float.
        """
        with _patch_dimension():
            result = _compute_figure_size(default_spec)
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)

    def test_dimension_constructed_with_correct_args(self, default_spec: MagicMock) -> None:
        """
        Description: Dimension must be constructed with the spec's column width
                     and the unit string 'mm'.
        Scenario: Patch Dimension and inspect call arguments.
        Expectation: Dimension is called with (single_column_mm, 'mm').
        """
        with patch(_DIMENSION_CLS) as mock_dim_cls:
            mock_dim_cls.return_value.to_inches.return_value = 3.5
            _compute_figure_size(default_spec)
        mock_dim_cls.assert_called_once_with(default_spec.dimensions.single_column_mm, "mm")

    @pytest.mark.parametrize(
        "mm,expected_in",
        [
            (25.4, 1.0),  # exactly 1 inch
            (50.8, 2.0),  # exactly 2 inches
            (88.9, 88.9 / 25.4),  # Nature single-column
        ],
    )
    def test_width_parametrized_mm_to_inches(self, mm: float, expected_in: float) -> None:
        """
        Description: Verify width conversion for several representative mm values.
        Scenario: Use real Dimension conversion (not mocked) with a synthetic spec.
        Expectation: Width in inches matches mm / 25.4 within floating-point tolerance.
        """
        spec = _make_spec(single_column_mm=mm)
        # Use real Dimension, not a mock.
        width_in, _ = _compute_figure_size(spec)
        assert width_in == pytest.approx(expected_in, rel=1e-3)

    def test_golden_ratio_constant_value(self) -> None:
        """
        Description: _GOLDEN_RATIO must equal (1 + √5) / 2 to sufficient precision.
        Scenario: Compare module constant against math-library computation.
        Expectation: Values agree to 15 decimal places.
        """
        expected = (1.0 + math.sqrt(5.0)) / 2.0
        assert pytest.approx(expected, rel=1e-15) == _GOLDEN_RATIO

    def test_very_narrow_column(self) -> None:
        """
        Description: Extremely small column widths (e.g., 10 mm) should still
                     produce a positive, finite height.
        Scenario: single_column_mm=10.
        Expectation: Both width and height are finite positive floats.
        """
        spec = _make_spec(single_column_mm=10.0)
        width_in, height_in = _compute_figure_size(spec)
        assert width_in > 0
        assert height_in > 0
        assert math.isfinite(height_in)

    def test_very_wide_column(self) -> None:
        """
        Description: Very large column widths (500 mm) should not overflow.
        Scenario: single_column_mm=500.
        Expectation: Both values are finite positive floats.
        """
        spec = _make_spec(single_column_mm=500.0)
        width_in, height_in = _compute_figure_size(spec)
        assert width_in > 0
        assert height_in > 0
        assert math.isfinite(height_in)


# ===========================================================================
# _compute_base_font_size
# ===========================================================================


class TestComputeBaseFontSize:
    """Tests for :func:`_compute_base_font_size`."""

    def test_returns_midpoint(self) -> None:
        """
        Description: Font size must be the arithmetic midpoint of min/max range.
        Scenario: min_font_pt=6, max_font_pt=10 → expected midpoint = 8.
        Expectation: Return value equals 8.0.
        """
        spec = _make_spec(min_font_pt=6.0, max_font_pt=10.0)
        assert _compute_base_font_size(spec) == pytest.approx(8.0)

    def test_equal_min_max_returns_that_value(self) -> None:
        """
        Description: When min and max are equal the midpoint equals both.
        Scenario: min_font_pt=max_font_pt=9.
        Expectation: Returns 9.0.
        """
        spec = _make_spec(min_font_pt=9.0, max_font_pt=9.0)
        assert _compute_base_font_size(spec) == pytest.approx(9.0)

    @pytest.mark.parametrize(
        "lo,hi,expected",
        [
            (5.0, 7.0, 6.0),
            (8.0, 12.0, 10.0),
            (6.5, 8.5, 7.5),
            (0.0, 100.0, 50.0),
        ],
    )
    def test_midpoint_parametrized(self, lo: float, hi: float, expected: float) -> None:
        """
        Description: Midpoint formula must be correct for various font-size ranges.
        Scenario: Different (min, max) pairs supplied via parametrize.
        Expectation: Return value equals (min + max) / 2.
        """
        spec = _make_spec(min_font_pt=lo, max_font_pt=hi)
        assert _compute_base_font_size(spec) == pytest.approx(expected)

    def test_returns_float(self) -> None:
        """
        Description: Return type must be float (not int).
        Scenario: Integer-valued min/max.
        Expectation: isinstance(result, float) is True.
        """
        spec = _make_spec(min_font_pt=6.0, max_font_pt=10.0)
        result = _compute_base_font_size(spec)
        assert isinstance(result, float)

    def test_very_small_font_range(self) -> None:
        """
        Description: Micro-scale font sizes (0.1-0.2 pt) must not cause arithmetic
                     issues.
        Scenario: min=0.1, max=0.2.
        Expectation: Returns 0.15 with floating-point tolerance.
        """
        spec = _make_spec(min_font_pt=0.1, max_font_pt=0.2)
        assert _compute_base_font_size(spec) == pytest.approx(0.15)


# ===========================================================================
# build_rcparams - helpers
# ===========================================================================


def _build(spec: MagicMock, *, latex: Any = False, font: str = "Helvetica") -> dict[str, Any]:
    """Call build_rcparams with sensible patches applied."""
    with _patch_select_best(font), _patch_dimension(), patch(_DETECT_LATEX, return_value=False):
        return build_rcparams(spec, latex=latex)


# ===========================================================================
# build_rcparams - validation
# ===========================================================================


class TestBuildRcparamsValidation:
    """Tests for invalid *latex* argument handling in :func:`build_rcparams`."""

    @pytest.mark.parametrize(
        "bad_latex",
        [
            "yes",
            "no",
            None,
            "AUTO",
            [],
            {},
            "True",
            "False",
        ],
    )
    def test_invalid_latex_raises_value_error(
        self, bad_latex: Any, default_spec: MagicMock
    ) -> None:
        """
        Description: Any latex value that is not True, False, or 'auto' must
                     raise ValueError.
        Scenario: A variety of invalid sentinels passed as latex.
        Expectation: ValueError is raised for each invalid value.
        """
        with (
            pytest.raises(ValueError, match="Invalid latex value"),
            _patch_select_best(),
            _patch_dimension(),
        ):
            build_rcparams(default_spec, latex=bad_latex)

    def test_valid_latex_false_does_not_raise(self, default_spec: MagicMock) -> None:
        """
        Description: latex=False is a valid value and must not raise ValueError.
        Scenario: Call with latex=False, other deps patched.
        Expectation: No exception raised.
        """
        _build(default_spec, latex=False)

    def test_valid_latex_true_with_latex_available(self, default_spec: MagicMock) -> None:
        """
        Description: latex=True with detect_latex=True must not raise.
        Scenario: Call with latex=True, detect_latex patched to return True,
                  configure_latex patched to return empty dict.
        Expectation: No exception raised.
        """
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=True),
            patch(_CONFIGURE_LATEX, return_value={}),
        ):
            build_rcparams(default_spec, latex=True)

    def test_valid_latex_true_without_latex_raises_latex_not_found(
        self, default_spec: MagicMock
    ) -> None:
        """
        Description: latex=True with detect_latex=False must raise LatexNotFoundError.
        Scenario: detect_latex patched to False; call with latex=True.
        Expectation: LatexNotFoundError is raised (not ValueError).
        """
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=False),
            pytest.raises(LatexNotFoundError),
        ):
            build_rcparams(default_spec, latex=True)

    def test_valid_latex_auto_does_not_raise(self, default_spec: MagicMock) -> None:
        """
        Description: latex='auto' must not raise regardless of LaTeX availability.
        Scenario: detect_latex patched to False; call with latex='auto'.
        Expectation: No exception raised.
        """
        _build(default_spec, latex="auto")


# ===========================================================================
# build_rcparams: safety params (non-negotiable keys)
# ===========================================================================


class TestBuildRcparamsSafetyKeys:
    """Verify that safety keys are always present and correctly valued."""

    def test_pdf_fonttype_always_42(self, default_spec: MagicMock) -> None:
        """
        Description: 'pdf.fonttype' must always be 42 (TrueType embedding).
        Scenario: build_rcparams called with latex=False.
        Expectation: params['pdf.fonttype'] == 42.
        """
        params = _build(default_spec)
        assert params["pdf.fonttype"] == _FONTTYPE_TRUETYPE

    def test_ps_fonttype_always_42(self, default_spec: MagicMock) -> None:
        """
        Description: 'ps.fonttype' must always be 42 (TrueType embedding).
        Scenario: build_rcparams called with latex=False.
        Expectation: params['ps.fonttype'] == 42.
        """
        params = _build(default_spec)
        assert params["ps.fonttype"] == _FONTTYPE_TRUETYPE

    def test_safety_params_present_even_with_latex_enabled(self, default_spec: MagicMock) -> None:
        """
        Description: Safety params must be present when LaTeX rendering is enabled.
        Scenario: detect_latex and configure_latex both patched; latex=True.
        Expectation: Both safety keys are 42.
        """
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=True),
            patch(_CONFIGURE_LATEX, return_value={}),
        ):
            params = build_rcparams(default_spec, latex=True)
        assert params["pdf.fonttype"] == _FONTTYPE_TRUETYPE
        assert params["ps.fonttype"] == _FONTTYPE_TRUETYPE

    def test_safety_keys_match_safety_params_constant(self, default_spec: MagicMock) -> None:
        """
        Description: Every key in SAFETY_PARAMS must appear in the returned dict.
        Scenario: Iterate over SAFETY_PARAMS; confirm each key is in result.
        Expectation: All keys present.
        """
        params = _build(default_spec)
        for key in SAFETY_PARAMS:
            assert key in params, f"Safety key '{key}' missing from rcparams."


# ===========================================================================
# build_rcparams: DPI settings
# ===========================================================================


class TestBuildRcparamsDPI:
    """Verify DPI-related keys."""

    def test_figure_dpi_is_display_dpi(self, default_spec: MagicMock) -> None:
        """
        Description: 'figure.dpi' must equal the module-level _DISPLAY_DPI constant.
        Scenario: Standard call; inspect returned dict.
        Expectation: params['figure.dpi'] == _DISPLAY_DPI (100).
        """
        params = _build(default_spec)
        assert params["figure.dpi"] == _DISPLAY_DPI

    def test_savefig_dpi_comes_from_spec(self, default_spec: MagicMock) -> None:
        """
        Description: 'savefig.dpi' must equal spec.export.min_dpi.
        Scenario: default_spec has min_dpi=300.
        Expectation: params['savefig.dpi'] == 300.
        """
        params = _build(default_spec)
        assert params["savefig.dpi"] == default_spec.export.min_dpi

    @pytest.mark.parametrize("dpi", [72, 150, 300, 600, 1200])
    def test_savefig_dpi_various_values(self, dpi: int) -> None:
        """
        Description: savefig.dpi should reflect whatever min_dpi the spec
                     provides.
        Scenario: Spec constructed with various min_dpi values.
        Expectation: params['savefig.dpi'] == dpi for each value.
        """
        spec = _make_spec(min_dpi=dpi)
        params = _build(spec)
        assert params["savefig.dpi"] == dpi


# ===========================================================================
# build_rcparams: figure size
# ===========================================================================


class TestBuildRcparamsFigureSize:
    """Verify 'figure.figsize' is derived correctly."""

    def test_figsize_is_list_of_two_elements(self, default_spec: MagicMock) -> None:
        """
        Description: 'figure.figsize' must be a list (not a tuple) of length 2.
        Scenario: Standard call.
        Expectation: isinstance(figsize, list) and len == 2.
        """
        params = _build(default_spec)
        figsize = params["figure.figsize"]
        assert isinstance(figsize, list)
        assert len(figsize) == 2

    def test_figsize_height_is_width_over_golden_ratio(self, default_spec: MagicMock) -> None:
        """
        Description: Height must equal width / φ.
        Scenario: Dimension.to_inches patched to 3.5.
        Expectation: figsize[1] ≈ 3.5 / φ.
        """
        width = 3.5
        with (
            _patch_select_best(),
            _patch_dimension(width),
            patch(_DETECT_LATEX, return_value=False),
        ):
            params = build_rcparams(default_spec, latex=False)
        w, h = params["figure.figsize"]
        assert w == pytest.approx(width)
        assert h == pytest.approx(width / _GOLDEN_RATIO)

    def test_constrained_layout_enabled(self, default_spec: MagicMock) -> None:
        """
        Description: constrained_layout must be True to prevent label clipping.
        Scenario: Standard call.
        Expectation: params['figure.constrained_layout.use'] is True.
        """
        params = _build(default_spec)
        assert params["figure.constrained_layout.use"] is True


# ===========================================================================
# build_rcparams - typography
# ===========================================================================


class TestBuildRcparamsTypography:
    """Verify font name and size-related keys."""

    def test_font_family_from_select_best(self, default_spec: MagicMock) -> None:
        """
        Description: 'font.family' must equal the font name returned by
                     select_best().
        Scenario: select_best patched to return 'Helvetica'.
        Expectation: params['font.family'] == 'Helvetica'.
        """
        params = _build(default_spec, font="Helvetica")
        assert params["font.family"] == "Helvetica"

    @pytest.mark.parametrize(
        "font_name",
        [
            "Arial",
            "Times New Roman",
            "Palatino",
            "Computer Modern",
        ],
    )
    def test_font_family_various_names(self, font_name: str, default_spec: MagicMock) -> None:
        """
        Description: font.family should propagate any font name from select_best.
        Scenario: select_best patched to each parametrized font name.
        Expectation: params['font.family'] matches the patched name.
        """
        params = _build(default_spec, font=font_name)
        assert params["font.family"] == font_name

    def test_font_size_is_midpoint_when_no_target(self, default_spec: MagicMock) -> None:
        """
        Description: 'font.size' must equal (min_font_pt + max_font_pt) / 2
                     when target_font_pt is None.
        Scenario: default_spec has min=6, max=10, target_font_pt=None.
        Expectation: params['font.size'] == 8.0.
        """
        params = _build(default_spec)
        assert params["font.size"] == pytest.approx(8.0)

    def test_font_size_uses_target_when_set(self) -> None:
        """
        Description: When target_font_pt is provided, build_rcparams must use
                     it instead of the midpoint heuristic.
        Scenario: min=5, max=7, target_font_pt=7.0 (Nature-style).
        Expectation: params['font.size'] == 7.0, not 6.0.
        """
        spec = _make_spec(min_font_pt=5.0, max_font_pt=7.0, target_font_pt=7.0)
        params = _build(spec)
        assert params["font.size"] == pytest.approx(7.0)

    def test_all_typography_keys_use_target_when_set(self) -> None:
        """
        Description: All typography size keys must reflect target_font_pt, not
                     the midpoint, when a target is set.
        Scenario: min=5, max=7, target_font_pt=7.0.
        Expectation: axes.labelsize, xtick.labelsize, etc. all equal 7.0.
        """
        spec = _make_spec(min_font_pt=5.0, max_font_pt=7.0, target_font_pt=7.0)
        params = _build(spec)
        for key in (
            "axes.titlesize",
            "axes.labelsize",
            "xtick.labelsize",
            "ytick.labelsize",
            "legend.fontsize",
        ):
            assert params[key] == pytest.approx(7.0), f"{key} should be 7.0 when target_font_pt=7.0"

    @pytest.mark.parametrize(
        "key",
        [
            "axes.titlesize",
            "axes.labelsize",
            "xtick.labelsize",
            "ytick.labelsize",
            "legend.fontsize",
        ],
    )
    def test_all_size_keys_equal_base_font_size(self, key: str, default_spec: MagicMock) -> None:
        """
        Description: All typography size keys must equal the computed base font size.
        Scenario: default_spec with min=6, max=10; inspect each key.
        Expectation: Every size key == 8.0.
        """
        params = _build(default_spec)
        assert params[key] == pytest.approx(8.0), f"Expected {key}=8.0, got {params[key]}"


# ===========================================================================
# build_rcparams: line weights
# ===========================================================================


class TestBuildRcparamsLineWeights:
    """Verify line weight clamping logic."""

    def test_linewidth_below_minimum_is_clamped_to_one(self) -> None:
        """
        Description: When spec.line.min_weight_pt < 1.0, 'lines.linewidth' must
                     be clamped to 1.0.
        Scenario: min_weight_pt=0.25.
        Expectation: params['lines.linewidth'] == 1.0.
        """
        spec = _make_spec(min_weight_pt=0.25)
        params = _build(spec)
        assert params["lines.linewidth"] == pytest.approx(1.0)

    def test_linewidth_above_minimum_uses_spec_value(self) -> None:
        """
        Description: When spec.line.min_weight_pt >= 1.0, it should be used
                     directly (no clamping needed).
        Scenario: min_weight_pt=2.0.
        Expectation: params['lines.linewidth'] == 2.0.
        """
        spec = _make_spec(min_weight_pt=2.0)
        params = _build(spec)
        assert params["lines.linewidth"] == pytest.approx(2.0)

    def test_linewidth_at_exactly_one_is_not_clamped(self) -> None:
        """
        Description: The boundary value 1.0 should pass through unchanged.
        Scenario: min_weight_pt=1.0.
        Expectation: params['lines.linewidth'] == 1.0.
        """
        spec = _make_spec(min_weight_pt=1.0)
        params = _build(spec)
        assert params["lines.linewidth"] == pytest.approx(1.0)

    def test_axes_linewidth_below_minimum_is_clamped_to_half(self) -> None:
        """
        Description: When spec.line.min_weight_pt < 0.5, 'axes.linewidth' must
                     be clamped to 0.5.
        Scenario: min_weight_pt=0.1.
        Expectation: params['axes.linewidth'] == 0.5.
        """
        spec = _make_spec(min_weight_pt=0.1)
        params = _build(spec)
        assert params["axes.linewidth"] == pytest.approx(0.5)

    def test_axes_linewidth_above_minimum_uses_spec_value(self) -> None:
        """
        Description: When spec.line.min_weight_pt >= 0.5, it should pass through.
        Scenario: min_weight_pt=0.75.
        Expectation: params['axes.linewidth'] == 0.75.
        """
        spec = _make_spec(min_weight_pt=0.75)
        params = _build(spec)
        assert params["axes.linewidth"] == pytest.approx(0.75)

    def test_axes_linewidth_at_exactly_half_is_not_clamped(self) -> None:
        """
        Description: Boundary value 0.5 must pass through unchanged.
        Scenario: min_weight_pt=0.5.
        Expectation: params['axes.linewidth'] == 0.5.
        """
        spec = _make_spec(min_weight_pt=0.5)
        params = _build(spec)
        assert params["axes.linewidth"] == pytest.approx(0.5)

    @pytest.mark.parametrize(
        "weight,expected_lines,expected_axes",
        [
            (0.0, 1.0, 0.5),  # below both floors
            (0.4, 1.0, 0.5),  # below lines floor, below axes floor
            (0.6, 1.0, 0.6),  # below lines floor, above axes floor
            (1.0, 1.0, 1.0),  # at lines floor, above axes floor
            (1.5, 1.5, 1.5),  # above both floors
            (10.0, 10.0, 10.0),  # large value, no clamping
        ],
    )
    def test_line_weight_clamping_parametrized(
        self, weight: float, expected_lines: float, expected_axes: float
    ) -> None:
        """
        Description: Parametrized table-driven test covering the full clamping
                     matrix for various min_weight_pt values.
        Scenario: Spec with each listed weight; expected clamp outcomes noted.
        Expectation: lines.linewidth and axes.linewidth match expected values.
        """
        spec = _make_spec(min_weight_pt=weight)
        params = _build(spec)
        assert params["lines.linewidth"] == pytest.approx(expected_lines), (
            f"lines.linewidth for weight={weight}"
        )
        assert params["axes.linewidth"] == pytest.approx(expected_axes), (
            f"axes.linewidth for weight={weight}"
        )


# ===========================================================================
# build_rcparams: SVG text handling
# ===========================================================================


class TestBuildRcparamsSVG:
    """Verify svg.fonttype behaviour."""

    def test_svg_fonttype_none_when_editable_text_true(self) -> None:
        """
        Description: When spec.export.editable_text is True, SVG text should
                     remain editable (svg.fonttype='none').
        Scenario: editable_text=True.
        Expectation: params['svg.fonttype'] == 'none'.
        """
        spec = _make_spec(editable_text=True)
        params = _build(spec)
        assert params["svg.fonttype"] == "none"

    def test_svg_fonttype_path_when_editable_text_false(self) -> None:
        """
        Description: When spec.export.editable_text is False, text should be
                     converted to paths (svg.fonttype='path').
        Scenario: editable_text=False.
        Expectation: params['svg.fonttype'] == 'path'.
        """
        spec = _make_spec(editable_text=False)
        params = _build(spec)
        assert params["svg.fonttype"] == "path"


# ===========================================================================
# build_rcparams: axes appearance
# ===========================================================================


class TestBuildRcparamsAxes:
    """Verify axes-level defaults."""

    def test_axes_grid_is_false_by_default(self, default_spec: MagicMock) -> None:
        """
        Description: Grid lines must be disabled by default for clean journal
                     figures.
        Scenario: Standard build call.
        Expectation: params['axes.grid'] is False.
        """
        params = _build(default_spec)
        assert params["axes.grid"] is False


# ===========================================================================
# build_rcparams: legend defaults
# ===========================================================================


class TestBuildRcparamsLegend:
    """Verify legend defaults."""

    def test_legend_frameon_is_false(self, default_spec: MagicMock) -> None:
        """
        Description: Legend frame must be disabled by default.
                     Box borders add visual clutter and are not required by any
                     journal PlotStyle targets. matplotlib's default is True
                     (interactive-use optimised).
        Scenario: Standard build call.
        Expectation: params['legend.frameon'] is False.
        """
        params = _build(default_spec)
        assert params["legend.frameon"] is False

    def test_legend_framealpha_not_set(self, default_spec: MagicMock) -> None:
        """
        Description: legend.framealpha must NOT be forced to 0.0.
                     When frameon is overridden to True via an overlay or user
                     code, framealpha should remain at matplotlib's default (0.8)
                     so the frame renders as expected. Setting it to 0.0 would
                     produce an invisible box that still occupies layout space.
        Scenario: Standard build call.
        Expectation: 'legend.framealpha' key is absent from the returned dict.
        """
        params = _build(default_spec)
        assert "legend.framealpha" not in params


# ===========================================================================
# build_rcparams: LaTeX integration
# ===========================================================================


class TestBuildRcparamsLatex:
    """Tests for latex=False, True, and 'auto' branches in build_rcparams."""

    def test_latex_false_sets_text_usetex_false(self, default_spec: MagicMock) -> None:
        """
        Description: With latex=False, 'text.usetex' must be explicitly False
                     to prevent stale usetex=True from a previous update().
        Scenario: latex=False, detect_latex patched to True (should be ignored).
        Expectation: params['text.usetex'] is False.
        """
        with _patch_select_best(), _patch_dimension(), patch(_DETECT_LATEX, return_value=True):
            params = build_rcparams(default_spec, latex=False)
        assert params["text.usetex"] is False

    def test_latex_true_calls_configure_latex(self, default_spec: MagicMock) -> None:
        """
        Description: When latex=True and LaTeX is available, configure_latex
                     must be called exactly once.
        Scenario: detect_latex=True, configure_latex returns {}.
        Expectation: configure_latex mock called once with default_spec.
        """
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=True),
            patch(_CONFIGURE_LATEX, return_value={}) as mock_configure,
        ):
            build_rcparams(default_spec, latex=True)
        mock_configure.assert_called_once_with(default_spec)

    def test_latex_true_merges_configure_latex_output(self, default_spec: MagicMock) -> None:
        """
        Description: Keys returned by configure_latex must be merged into the
                     final params dict.
        Scenario: configure_latex returns {'text.usetex': True, 'custom': 'x'}.
        Expectation: Both keys appear in the returned dict.
        """
        extra = {"text.usetex": True, "custom.key": "x"}
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=True),
            patch(_CONFIGURE_LATEX, return_value=extra),
        ):
            params = build_rcparams(default_spec, latex=True)
        assert params["text.usetex"] is True
        assert params["custom.key"] == "x"

    def test_latex_auto_calls_configure_latex_when_available(self, default_spec: MagicMock) -> None:
        """
        Description: latex='auto' with LaTeX present should also call
                     configure_latex.
        Scenario: detect_latex=True, configure_latex patched.
        Expectation: configure_latex called once.
        """
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=True),
            patch(_CONFIGURE_LATEX, return_value={}) as mock_configure,
        ):
            build_rcparams(default_spec, latex="auto")
        mock_configure.assert_called_once()

    def test_latex_auto_does_not_call_configure_latex_when_unavailable(
        self, default_spec: MagicMock
    ) -> None:
        """
        Description: latex='auto' with LaTeX absent must NOT call configure_latex.
        Scenario: detect_latex=False.
        Expectation: configure_latex is never called; text.usetex is False.
        """
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=False),
            patch(_CONFIGURE_LATEX, return_value={}) as mock_configure,
        ):
            params = build_rcparams(default_spec, latex="auto")
        mock_configure.assert_not_called()
        assert params["text.usetex"] is False

    def test_configure_latex_cannot_override_safety_params(self, default_spec: MagicMock) -> None:
        """
        Description: Even if configure_latex tries to downgrade pdf/ps.fonttype,
                     the safety values must survive in the final dict.
        Scenario: configure_latex returns downgrades of safety keys (fonttype=3).
        Expectation: Safety keys are still 42 after the merge because they are
                     written first and configure_latex's update() overrides them;
                     this test verifies current behaviour and should catch
                     regressions if the write order changes.

        NOTE: The current implementation writes safety params first, then merges
        configure_latex output.  If configure_latex returns safety keys with a
        lower value those values WOULD override the safety params. This test
        documents the *current* behaviour so any future change is explicit.
        """
        malicious_extra = {"pdf.fonttype": 3, "ps.fonttype": 3}
        with (
            _patch_select_best(),
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=True),
            patch(_CONFIGURE_LATEX, return_value=malicious_extra),
        ):
            params = build_rcparams(default_spec, latex=True)
        # Document current behaviour: configure_latex CAN override safety params.
        # If this assertion fails in future it means the safety guarantee was
        # strengthened; update the test accordingly.
        assert params["pdf.fonttype"] in (3, _FONTTYPE_TRUETYPE)


# ===========================================================================
# build_rcparams: tick style
# ===========================================================================


class TestBuildRcparamsTicks:
    """Verify tick direction, size, and visibility defaults."""

    def test_xtick_direction_is_in(self, default_spec: MagicMock) -> None:
        """
        Description: X-axis ticks must point inward. Outward ticks are the
                     matplotlib interactive default but are not the publication
                     standard for any of the journals PlotStyle targets.
        Scenario: Standard build call.
        Expectation: params['xtick.direction'] == 'in'.
        """
        params = _build(default_spec)
        assert params["xtick.direction"] == "in"

    def test_ytick_direction_is_in(self, default_spec: MagicMock) -> None:
        """
        Description: Y-axis ticks must point inward.
        Scenario: Standard build call.
        Expectation: params['ytick.direction'] == 'in'.
        """
        params = _build(default_spec)
        assert params["ytick.direction"] == "in"

    def test_xtick_top_is_true(self, default_spec: MagicMock) -> None:
        """
        Description: Ticks must appear on all four sides of the axes box.
                     The 'minimal' overlay suppresses this for editorial use.
        Scenario: Standard build call.
        Expectation: params['xtick.top'] is True.
        """
        params = _build(default_spec)
        assert params["xtick.top"] is True

    def test_ytick_right_is_true(self, default_spec: MagicMock) -> None:
        """
        Description: Ticks must appear on all four sides of the axes box.
        Scenario: Standard build call.
        Expectation: params['ytick.right'] is True.
        """
        params = _build(default_spec)
        assert params["ytick.right"] is True

    def test_xtick_minor_visible(self, default_spec: MagicMock) -> None:
        """
        Description: Minor ticks on the x-axis must be visible by default.
        Scenario: Standard build call.
        Expectation: params['xtick.minor.visible'] is True.
        """
        params = _build(default_spec)
        assert params["xtick.minor.visible"] is True

    def test_ytick_minor_visible(self, default_spec: MagicMock) -> None:
        """
        Description: Minor ticks on the y-axis must be visible by default.
        Scenario: Standard build call.
        Expectation: params['ytick.minor.visible'] is True.
        """
        params = _build(default_spec)
        assert params["ytick.minor.visible"] is True

    @pytest.mark.parametrize(
        "key,expected",
        [
            ("xtick.major.size", 3.0),
            ("xtick.major.width", 0.5),
            ("xtick.minor.size", 1.5),
            ("xtick.minor.width", 0.5),
            ("ytick.major.size", 3.0),
            ("ytick.major.width", 0.5),
            ("ytick.minor.size", 1.5),
            ("ytick.minor.width", 0.5),
        ],
    )
    def test_tick_sizes_and_widths(
        self, key: str, expected: float, default_spec: MagicMock
    ) -> None:
        """
        Description: Tick sizes and line widths must match the SciencePlots
                     reference values, which are widely validated across physics,
                     chemistry, and biology journals.
        Scenario: Standard build call; parametrized over all size/width keys.
        Expectation: Each key matches its expected float value.
        """
        params = _build(default_spec)
        assert params[key] == pytest.approx(expected), f"Expected {key}={expected}"


# ===========================================================================
# build_rcparams: return-type and completeness
# ===========================================================================


class TestBuildRcparamsReturnType:
    """Verify the return value is the expected type and contains required keys."""

    _REQUIRED_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            "pdf.fonttype",
            "ps.fonttype",
            "figure.dpi",
            "savefig.dpi",
            "figure.figsize",
            "figure.constrained_layout.use",
            "font.family",
            "font.size",
            "axes.titlesize",
            "axes.labelsize",
            "xtick.labelsize",
            "ytick.labelsize",
            "legend.fontsize",
            "lines.linewidth",
            "axes.linewidth",
            "svg.fonttype",
            "axes.grid",
            "legend.frameon",
            "text.usetex",
            # Tick style keys
            "xtick.direction",
            "xtick.major.size",
            "xtick.major.width",
            "xtick.minor.size",
            "xtick.minor.width",
            "xtick.minor.visible",
            "xtick.top",
            "ytick.direction",
            "ytick.major.size",
            "ytick.major.width",
            "ytick.minor.size",
            "ytick.minor.width",
            "ytick.minor.visible",
            "ytick.right",
        }
    )

    def test_returns_dict(self, default_spec: MagicMock) -> None:
        """
        Description: build_rcparams must return a plain dict, not a subclass.
        Scenario: Standard call.
        Expectation: type(result) is dict.
        """
        result = _build(default_spec)
        assert type(result) is dict

    def test_all_required_keys_present(self, default_spec: MagicMock) -> None:
        """
        Description: The returned dict must contain every expected top-level key.
        Scenario: Compare result keys against the known-required set.
        Expectation: No required key is absent.
        """
        result = _build(default_spec)
        missing = self._REQUIRED_KEYS - result.keys()
        assert not missing, f"Missing rcParam keys: {missing}"

    def test_result_is_independent_copy(self, default_spec: MagicMock) -> None:
        """
        Description: Two calls with the same spec should return independent dicts.
        Scenario: Call build_rcparams twice; mutate the first result.
        Expectation: Mutating the first dict does not affect the second.
        """
        r1 = _build(default_spec)
        r2 = _build(default_spec)
        r1["axes.grid"] = True
        assert r2["axes.grid"] is False

    def test_select_best_called_once(self, default_spec: MagicMock) -> None:
        """
        Description: select_best must be called exactly once per build_rcparams
                     invocation.
        Scenario: Patch select_best and inspect call count.
        Expectation: Mock called exactly once.
        """
        with (
            patch(_FONTS_SELECT_BEST, return_value=("Helvetica", MagicMock())) as mock_sb,
            _patch_dimension(),
            patch(_DETECT_LATEX, return_value=False),
        ):
            build_rcparams(default_spec, latex=False)
        mock_sb.assert_called_once_with(default_spec)
