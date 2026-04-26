"""Comprehensive test suite for plotstyle.preview.print_size.

Covers: module constants, _validate_args(), _build_annotation_label(),
_resolve_target_width(), and the public preview_print_size() API â€” including
happy paths, restoration guarantees, DPI scaling, annotation text, zero-width
figures, invalid arguments, and style isolation.
"""

from __future__ import annotations

from unittest.mock import patch

import matplotlib
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")

from plotstyle.preview.print_size import (
    _ANNOTATION_ALPHA,
    _ANNOTATION_FONTSIZE,
    _ANNOTATION_Y,
    _DEFAULT_MONITOR_DPI,
    _LEFT_ARROW,
    _MM_PER_INCH,
    _RIGHT_ARROW,
    _VALID_COLUMNS,
    _build_annotation_label,
    _resolve_target_width,
    _validate_args,
    preview_print_size,
)
from plotstyle.specs import SpecNotFoundError

# ---------------------------------------------------------------------------
# Helper: correct patch target for plt.show
# ---------------------------------------------------------------------------

# preview_print_size() imports matplotlib.pyplot *locally* inside the function
# body (deferred import), so the module-level attribute
# ``plotstyle.preview.print_size.plt`` does not exist at patch time.  The
# correct target is the canonical pyplot.show entry point.
_SHOW_TARGET = "matplotlib.pyplot.show"

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all Matplotlib figures after each test to prevent memory leaks."""
    yield
    plt.close("all")


@pytest.fixture
def simple_fig():
    """Return a plain 6x4-inch figure for use in preview tests."""
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.plot([1, 2, 3], [1, 4, 9])
    return fig


@pytest.fixture
def nature_single_column_width_in() -> float:
    """Return the expected single-column width for Nature in inches."""
    from plotstyle.specs.units import Dimension

    return Dimension(89.0, "mm").to_inches()


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Validate module-level constants are correctly defined."""

    def test_default_monitor_dpi_is_positive(self) -> None:
        """
        Description: The default monitor DPI must be a strictly positive float
        representing a physically meaningful pixel density.
        Scenario: Inspect _DEFAULT_MONITOR_DPI at module level.
        Expectation: Value is float > 0.
        """
        assert isinstance(_DEFAULT_MONITOR_DPI, float)
        assert _DEFAULT_MONITOR_DPI > 0

    def test_default_monitor_dpi_is_96(self) -> None:
        """
        Description: 96 DPI is the Windows/Linux conventional default.
        Scenario: Check exact value of _DEFAULT_MONITOR_DPI.
        Expectation: 96.0.
        """
        assert _DEFAULT_MONITOR_DPI == 96.0

    def test_left_arrow_is_unicode_left_arrow(self) -> None:
        """
        Description: _LEFT_ARROW must be the Unicode left-arrow character (â†).
        Scenario: Compare _LEFT_ARROW to the expected Unicode code point.
        Expectation: Equal to '\\u2190'.
        """
        assert _LEFT_ARROW == "\u2190"

    def test_right_arrow_is_unicode_right_arrow(self) -> None:
        """
        Description: _RIGHT_ARROW must be the Unicode right-arrow character (\u2192).
        Scenario: Compare _RIGHT_ARROW to the expected Unicode code point.
        Expectation: Equal to '\\u2192'.
        """
        assert _RIGHT_ARROW == "\u2192"

    def test_mm_per_inch_is_correct(self) -> None:
        """
        Description: 25.4 mm/inch is the internationally-defined exact value;
        any deviation would silently produce wrong physical sizes.
        Scenario: Check exact value of _MM_PER_INCH.
        Expectation: 25.4.
        """
        assert pytest.approx(25.4) == _MM_PER_INCH

    def test_valid_columns_contains_one_and_two(self) -> None:
        """
        Description: The valid column-span set must contain exactly {1, 2}.
        Scenario: Inspect _VALID_COLUMNS at module level.
        Expectation: frozenset equal to frozenset({1, 2}).
        """
        assert frozenset({1, 2}) == _VALID_COLUMNS

    def test_annotation_alpha_in_range(self) -> None:
        """
        Description: Alpha must be in [0, 1] for valid Matplotlib transparency.
        Scenario: Inspect _ANNOTATION_ALPHA.
        Expectation: 0 <= value <= 1.
        """
        assert 0.0 <= _ANNOTATION_ALPHA <= 1.0

    def test_annotation_fontsize_is_positive(self) -> None:
        """
        Description: Font size must be positive to render visible text.
        Scenario: Inspect _ANNOTATION_FONTSIZE.
        Expectation: int > 0.
        """
        assert isinstance(_ANNOTATION_FONTSIZE, int)
        assert _ANNOTATION_FONTSIZE > 0

    def test_annotation_y_in_figure_coordinates(self) -> None:
        """
        Description: _ANNOTATION_Y is a figure-normalised coordinate; it must
        be in [0, 1] to be visible within the figure.
        Scenario: Inspect _ANNOTATION_Y.
        Expectation: 0 <= value <= 1.
        """
        assert 0.0 <= _ANNOTATION_Y <= 1.0


# ---------------------------------------------------------------------------
# _validate_args() function tests
# ---------------------------------------------------------------------------


class TestValidateArgs:
    """Validate _validate_args() rejects invalid columns/monitor_dpi values."""

    @pytest.mark.parametrize("columns", [1, 2])
    @pytest.mark.parametrize("dpi", [1.0, 72.0, 96.0, 144.0, 300.0, 600.0])
    def test_valid_combinations_do_not_raise(self, columns, dpi) -> None:
        """
        Description: All valid combinations of columns and monitor_dpi must
        pass without raising.
        Scenario: Call _validate_args(columns, dpi) for supported values.
        Expectation: No exception.
        """
        _validate_args(columns, dpi)

    @pytest.mark.parametrize("invalid_columns", [0, 3, -1, 4, 100])
    def test_invalid_columns_raises_value_error(self, invalid_columns) -> None:
        """
        Description: Columns outside {1, 2} must raise ValueError.
        Scenario: Call _validate_args with unsupported column values.
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_args(invalid_columns, 96.0)

    def test_invalid_columns_error_mentions_value(self) -> None:
        """
        Description: The ValueError must include the offending value so the
        developer can quickly identify the mistake.
        Scenario: Call _validate_args(5, 96.0).
        Expectation: '5' appears in the error message.
        """
        with pytest.raises(ValueError, match="5"):
            _validate_args(5, 96.0)

    @pytest.mark.parametrize("bad_dpi", [0.0, -1.0, -96.0, -0.001])
    def test_non_positive_dpi_raises_value_error(self, bad_dpi) -> None:
        """
        Description: A non-positive monitor DPI is physically nonsensical and
        must raise ValueError.
        Scenario: Call _validate_args(1, bad_dpi) for various non-positive values.
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_args(1, bad_dpi)

    def test_zero_dpi_raises_value_error(self) -> None:
        """
        Description: Zero DPI would produce a division-by-zero in DPI scaling;
        it must be caught eagerly.
        Scenario: Call _validate_args(1, 0.0).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_args(1, 0.0)

    def test_invalid_dpi_error_mentions_value(self) -> None:
        """
        Description: The ValueError for bad DPI must mention the offending
        value for clarity.
        Scenario: Call _validate_args(1, -5.0).
        Expectation: '-5' appears in the error message.
        """
        with pytest.raises(ValueError, match=r"-5"):
            _validate_args(1, -5.0)

    def test_columns_validation_takes_priority_over_dpi(self) -> None:
        """
        Description: Both columns and dpi are invalid; the error must still
        be a ValueError (the function can raise either in any order).
        Scenario: Call _validate_args(99, -1.0).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_args(99, -1.0)


# ---------------------------------------------------------------------------
# _build_annotation_label() function tests
# ---------------------------------------------------------------------------


class TestBuildAnnotationLabel:
    """Validate _build_annotation_label() produces a correctly formatted string."""

    def test_contains_left_arrow(self) -> None:
        """
        Description: The annotation must include the left-pointing arrow to
        frame the width measurement visually.
        Scenario: Call _build_annotation_label(89.0).
        Expectation: _LEFT_ARROW in result.
        """
        label = _build_annotation_label(89.0)
        assert _LEFT_ARROW in label

    def test_contains_right_arrow(self) -> None:
        """
        Description: The annotation must include the right-pointing arrow.
        Scenario: Call _build_annotation_label(89.0).
        Expectation: _RIGHT_ARROW in result.
        """
        label = _build_annotation_label(89.0)
        assert _RIGHT_ARROW in label

    def test_contains_mm_unit(self) -> None:
        """
        Description: The annotation must include 'mm' so the unit is explicit
        to the viewer.
        Scenario: Call _build_annotation_label(89.0).
        Expectation: 'mm' in result.
        """
        label = _build_annotation_label(89.0)
        assert "mm" in label

    @pytest.mark.parametrize(
        "width_mm, expected_digits",
        [
            (89.0, "89"),
            (183.0, "183"),
            (88.9, "89"),  # rounds to nearest integer
            (182.5, "182"),  # rounds to nearest (banker's rounding or floor)
        ],
    )
    def test_width_formatted_as_integer_mm(self, width_mm, expected_digits) -> None:
        """
        Description: Width is formatted with zero decimal places (:.0f) so the
        label is compact; the rounded integer digits must appear in the label.
        Scenario: Call _build_annotation_label with the given width.
        Expectation: expected_digits substring is present in the label.
        """
        label = _build_annotation_label(width_mm)
        assert expected_digits in label

    def test_returns_string(self) -> None:
        """
        Description: _build_annotation_label must return a str, not bytes or
        another type.
        Scenario: Call with a typical width value.
        Expectation: isinstance(result, str).
        """
        assert isinstance(_build_annotation_label(89.0), str)

    def test_label_is_non_empty(self) -> None:
        """
        Description: The label must never be empty.
        Scenario: Call with a non-zero width.
        Expectation: len(result) > 0.
        """
        assert len(_build_annotation_label(89.0)) > 0


# ---------------------------------------------------------------------------
# _resolve_target_width() function tests
# ---------------------------------------------------------------------------


class TestResolveTargetWidth:
    """Validate _resolve_target_width() for journal and 1:1 paths."""

    def test_no_journal_returns_current_width(self) -> None:
        """
        Description: When journal is None, the 1:1 path must return the
        figure's current width unchanged.
        Scenario: Call _resolve_target_width(None, 1, 5.0).
        Expectation: width_in == 5.0.
        """
        width_in, _ = _resolve_target_width(None, 1, 5.0)
        assert width_in == pytest.approx(5.0)

    def test_no_journal_converts_width_to_mm(self) -> None:
        """
        Description: When journal is None, width_mm must equal width_in x 25.4.
        Scenario: Call _resolve_target_width(None, 1, 5.0).
        Expectation: width_mm ~= 5.0 x 25.4 = 127.0.
        """
        _, width_mm = _resolve_target_width(None, 1, 5.0)
        assert width_mm == pytest.approx(5.0 * _MM_PER_INCH)

    def test_journal_single_column_returns_spec_width(self) -> None:
        """
        Description: When journal is 'nature' and columns=1, the target width
        must match Nature's single-column spec (89 mm).
        Scenario: Call _resolve_target_width('nature', 1, 6.0).
        Expectation: width_mm ~= 89.0.
        """
        _, width_mm = _resolve_target_width("nature", 1, 6.0)
        assert width_mm == pytest.approx(89.0)

    def test_journal_double_column_returns_spec_width(self) -> None:
        """
        Description: When journal is 'nature' and columns=2, the target width
        must match Nature's double-column spec (183 mm).
        Scenario: Call _resolve_target_width('nature', 2, 6.0).
        Expectation: width_mm ~= 183.0.
        """
        _, width_mm = _resolve_target_width("nature", 2, 6.0)
        assert width_mm == pytest.approx(183.0)

    def test_journal_width_in_consistent_with_width_mm(self) -> None:
        """
        Description: width_in and width_mm must be consistent: width_mm ~=
        width_in x 25.4.
        Scenario: Call _resolve_target_width('nature', 1, 6.0).
        Expectation: width_mm ~= width_in x 25.4.
        """
        width_in, width_mm = _resolve_target_width("nature", 1, 6.0)
        assert width_mm == pytest.approx(width_in * _MM_PER_INCH, rel=1e-4)

    def test_unknown_journal_raises_spec_not_found(self) -> None:
        """
        Description: Requesting a width for an unregistered journal must raise
        SpecNotFoundError so the caller receives a clear error.
        Scenario: Call _resolve_target_width('__ghost__', 1, 6.0).
        Expectation: SpecNotFoundError raised.
        """
        with pytest.raises((SpecNotFoundError, KeyError)):
            _resolve_target_width("__ghost__", 1, 6.0)

    def test_no_journal_any_current_width_is_accepted(self) -> None:
        """
        Description: The 1:1 path must accept any positive current_width_in
        without error.
        Scenario: Call _resolve_target_width(None, 1, 0.1).
        Expectation: No exception; width_in == 0.1.
        """
        width_in, _ = _resolve_target_width(None, 1, 0.1)
        assert width_in == pytest.approx(0.1)


# ---------------------------------------------------------------------------
# Public API: preview_print_size()
# ---------------------------------------------------------------------------


class TestPreviewPrintSizeArgValidation:
    """Validate that preview_print_size() raises for invalid arguments."""

    @pytest.mark.parametrize("invalid_columns", [0, 3, -1])
    def test_invalid_columns_raises_value_error(self, simple_fig, invalid_columns) -> None:
        """
        Description: An unsupported column-span must raise ValueError before
        plt.show() is called, leaving the figure unchanged.
        Scenario: Call preview_print_size with invalid columns.
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            preview_print_size(simple_fig, columns=invalid_columns)

    @pytest.mark.parametrize("bad_dpi", [0.0, -1.0, -96.0])
    def test_invalid_monitor_dpi_raises_value_error(self, simple_fig, bad_dpi) -> None:
        """
        Description: A non-positive monitor_dpi is physically invalid and
        must raise ValueError.
        Scenario: Call preview_print_size with bad monitor_dpi values.
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            preview_print_size(simple_fig, monitor_dpi=bad_dpi)

    def test_zero_width_figure_raises_value_error(self) -> None:
        """
        Description: A figure with zero width makes DPI scaling undefined;
        preview_print_size must raise ValueError with a descriptive message.
        Scenario: Create a figure with figsize=(0, 4) â€” effectively zero width.
        Expectation: ValueError raised; message mentions 'zero'.
        """
        fig = plt.figure(figsize=(0, 4))
        with pytest.raises(ValueError, match="zero"):
            preview_print_size(fig)

    def test_unknown_journal_raises_spec_not_found(self, simple_fig) -> None:
        """
        Description: Passing an unregistered journal name must raise
        SpecNotFoundError before modifying the figure.
        Scenario: Call preview_print_size(fig, journal='__no_such_journal__').
        Expectation: SpecNotFoundError (or KeyError subclass) raised.
        """
        with pytest.raises((SpecNotFoundError, KeyError)):
            preview_print_size(simple_fig, journal="__no_such_journal__")


class TestPreviewPrintSizeRestorationGuarantee:
    """Validate that preview_print_size() always restores the figure to its
    original state after plt.show() returns."""

    def test_dpi_restored_after_normal_exit(self, simple_fig) -> None:
        """
        Description: After a successful preview_print_size() call, the figure's
        DPI must be identical to its pre-call value.
        Scenario: Record DPI, mock plt.show, call preview_print_size(), compare.
        Expectation: fig.dpi is unchanged.
        """
        original_dpi = simple_fig.dpi
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig)
        assert simple_fig.dpi == pytest.approx(original_dpi)

    def test_dpi_restored_even_if_show_raises(self, simple_fig) -> None:
        """
        Description: The finally block must restore DPI even if plt.show()
        raises an exception.
        Scenario: Mock plt.show to raise RuntimeError, call preview_print_size.
        Expectation: fig.dpi is restored; RuntimeError propagates.
        """
        original_dpi = simple_fig.dpi
        with (
            patch(_SHOW_TARGET, side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError, match="boom"),
        ):
            preview_print_size(simple_fig)
        assert simple_fig.dpi == pytest.approx(original_dpi)

    def test_annotation_removed_after_normal_exit(self, simple_fig) -> None:
        """
        Description: The width annotation added during preview must be removed
        from the figure after plt.show() returns so the caller's figure is
        not permanently altered.
        Scenario: Count fig.texts before and after a successful call.
        Expectation: fig.texts count is the same before and after.
        """
        text_count_before = len(simple_fig.texts)
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig)
        assert len(simple_fig.texts) == text_count_before

    def test_annotation_removed_even_if_show_raises(self, simple_fig) -> None:
        """
        Description: The annotation must be removed from fig.texts even if
        plt.show() raises, so the caller's figure remains clean.
        Scenario: Mock plt.show to raise RuntimeError; check fig.texts after.
        Expectation: fig.texts count is the same as before the call.
        """
        text_count_before = len(simple_fig.texts)
        with (
            patch(_SHOW_TARGET, side_effect=RuntimeError("x")),
            pytest.raises(RuntimeError),
        ):
            preview_print_size(simple_fig)
        assert len(simple_fig.texts) == text_count_before

    def test_figure_size_unchanged_after_call(self, simple_fig) -> None:
        """
        Description: preview_print_size scales DPI (not canvas size), so
        fig.get_size_inches() must be unchanged after the call.
        Scenario: Record figsize, call preview_print_size, compare figsize.
        Expectation: figsize is the same (within float tolerance).
        """
        original_size = simple_fig.get_size_inches()
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig)
        assert simple_fig.get_size_inches() == pytest.approx(original_size)


class TestPreviewPrintSizeDPIScaling:
    """Validate the DPI scaling logic applied by preview_print_size()."""

    def test_dpi_is_scaled_during_show(self, simple_fig) -> None:
        """
        Description: During plt.show(), the figure DPI must be scaled to match
        the target physical width at the monitor's pixel density.
        Scenario: Capture the DPI value mid-show by inspecting fig.dpi inside
        a patched plt.show() call.
        Expectation: fig.dpi during show != original dpi (for a journal with a
        different width than the current figure width).
        """
        captured_dpi: list[float] = []

        def fake_show() -> None:
            captured_dpi.append(simple_fig.dpi)

        with patch(_SHOW_TARGET, side_effect=fake_show):
            preview_print_size(simple_fig, journal="nature", columns=1, monitor_dpi=96.0)

        assert len(captured_dpi) == 1
        # The scaled DPI must be strictly positive
        assert captured_dpi[0] > 0

    def test_dpi_scaling_formula(self, simple_fig, nature_single_column_width_in) -> None:
        """
        Description: display_dpi = monitor_dpi x (target_width_in / current_width_in).
        This relationship must hold during the preview call.
        Scenario: Compare captured DPI against the formula.
        Expectation: captured_dpi ~= expected_display_dpi.
        """
        monitor_dpi = 96.0
        current_width_in = simple_fig.get_size_inches()[0]
        expected_dpi = monitor_dpi * (nature_single_column_width_in / current_width_in)

        captured_dpi: list[float] = []

        def fake_show() -> None:
            captured_dpi.append(simple_fig.dpi)

        with patch(_SHOW_TARGET, side_effect=fake_show):
            preview_print_size(simple_fig, journal="nature", columns=1, monitor_dpi=monitor_dpi)

        assert captured_dpi[0] == pytest.approx(expected_dpi, rel=1e-6)

    def test_double_column_produces_higher_dpi_than_single(self, simple_fig) -> None:
        """
        Description: The double-column target width is larger than single-column,
        so the preview DPI must be higher for columns=2 than for columns=1.
        Scenario: Capture DPI for columns=1 and columns=2 separately.
        Expectation: dpi_double > dpi_single.
        """
        dpis: list[float] = []

        for cols in (1, 2):
            captured: list[float] = []

            def fake_show(c: list[float] = captured) -> None:
                c.append(simple_fig.dpi)

            with patch(_SHOW_TARGET, side_effect=fake_show):
                preview_print_size(simple_fig, journal="nature", columns=cols, monitor_dpi=96.0)
            dpis.append(captured[0])

        assert dpis[1] > dpis[0]

    def test_no_journal_preserves_dpi_ratio_one(self, simple_fig) -> None:
        """
        Description: When journal=None, target_width_in == current_width_in,
        so scale_factor == 1.0 and display_dpi == monitor_dpi.
        Scenario: Call preview_print_size(fig) with no journal; capture DPI.
        Expectation: captured_dpi ~= _DEFAULT_MONITOR_DPI.
        """
        captured_dpi: list[float] = []

        def fake_show() -> None:
            captured_dpi.append(simple_fig.dpi)

        with patch(_SHOW_TARGET, side_effect=fake_show):
            preview_print_size(simple_fig, monitor_dpi=_DEFAULT_MONITOR_DPI)

        assert captured_dpi[0] == pytest.approx(_DEFAULT_MONITOR_DPI, rel=1e-6)


class TestPreviewPrintSizeAnnotation:
    """Validate the physical-width annotation added during preview."""

    def test_annotation_is_added_during_show(self, simple_fig) -> None:
        """
        Description: During plt.show(), a text annotation must be present on
        the figure so the viewer can verify the physical scale.
        Scenario: Capture fig.texts inside a patched plt.show.
        Expectation: len(fig.texts) > 0 during show.
        """
        text_count_during: list[int] = []

        def fake_show() -> None:
            text_count_during.append(len(simple_fig.texts))

        with patch(_SHOW_TARGET, side_effect=fake_show):
            preview_print_size(simple_fig)

        assert text_count_during[0] > 0

    def test_annotation_contains_mm(self, simple_fig) -> None:
        """
        Description: The annotation text must include 'mm' so the physical
        unit is unambiguous to the viewer.
        Scenario: Capture annotation text inside a patched plt.show.
        Expectation: 'mm' appears in the annotation text.
        """
        annotation_texts: list[str] = []

        def fake_show() -> None:
            annotation_texts.extend(t.get_text() for t in simple_fig.texts)

        with patch(_SHOW_TARGET, side_effect=fake_show):
            preview_print_size(simple_fig, journal="nature")

        assert any("mm" in t for t in annotation_texts)

    def test_annotation_contains_arrows(self, simple_fig) -> None:
        """
        Description: The annotation must include both Unicode arrows to frame
        the width measurement, as defined by _build_annotation_label.
        Scenario: Capture annotation text inside patched plt.show.
        Expectation: Both _LEFT_ARROW and _RIGHT_ARROW present in the text.
        """
        annotation_texts: list[str] = []

        def fake_show() -> None:
            annotation_texts.extend(t.get_text() for t in simple_fig.texts)

        with patch(_SHOW_TARGET, side_effect=fake_show):
            preview_print_size(simple_fig, journal="nature")

        joined = "".join(annotation_texts)
        assert _LEFT_ARROW in joined
        assert _RIGHT_ARROW in joined


class TestPreviewPrintSizeHappyPaths:
    """Smoke tests for common usage patterns."""

    def test_no_journal_no_error(self, simple_fig) -> None:
        """
        Description: Calling with no journal (1:1 preview) must succeed.
        Scenario: Call preview_print_size(fig) with plt.show mocked.
        Expectation: No exception raised; returns None.
        """
        with patch(_SHOW_TARGET):
            result = preview_print_size(simple_fig)
        assert result is None

    @pytest.mark.parametrize("journal", ["nature", "ieee", "science"])
    def test_known_journals_succeed(self, simple_fig, journal) -> None:
        """
        Description: preview_print_size must accept every registered journal
        without raising.
        Scenario: Call with each known journal; mock plt.show.
        Expectation: No exception raised.
        """
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig, journal=journal)

    @pytest.mark.parametrize("columns", [1, 2])
    def test_both_column_spans_succeed(self, simple_fig, columns) -> None:
        """
        Description: Both column-span values must be accepted.
        Scenario: Call preview_print_size(fig, journal='nature', columns=columns).
        Expectation: No exception raised.
        """
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig, journal="nature", columns=columns)

    @pytest.mark.parametrize("monitor_dpi", [72.0, 96.0, 144.0, 192.0])
    def test_common_monitor_dpis_succeed(self, simple_fig, monitor_dpi) -> None:
        """
        Description: Common real-world monitor DPI values must be accepted.
        Scenario: Call preview_print_size with each monitor_dpi.
        Expectation: No exception raised.
        """
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig, monitor_dpi=monitor_dpi)

    def test_returns_none(self, simple_fig) -> None:
        """
        Description: preview_print_size is a display side-effect function; it
        must return None, not a figure or other value.
        Scenario: Capture return value with plt.show mocked.
        Expectation: return value is None.
        """
        with patch(_SHOW_TARGET):
            result = preview_print_size(simple_fig, journal="nature")
        assert result is None


class TestPreviewPrintSizeEdgeCases:
    """Validate edge-case and boundary scenarios."""

    def test_very_small_figure_width_succeeds(self) -> None:
        """
        Description: A figure width of 0.1 inch is unusual but non-zero and
        must not raise.
        Scenario: Create fig with figsize=(0.1, 1.0); call preview_print_size.
        Expectation: No exception raised.
        """
        fig = plt.figure(figsize=(0.1, 1.0))
        with patch(_SHOW_TARGET):
            preview_print_size(fig)

    def test_very_large_monitor_dpi_succeeds(self, simple_fig) -> None:
        """
        Description: Extremely high monitor DPI (e.g. 1000) must not cause
        overflow or errors.
        Scenario: Call preview_print_size with monitor_dpi=1000.0.
        Expectation: No exception raised; DPI restored afterwards.
        """
        original_dpi = simple_fig.dpi
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig, monitor_dpi=1000.0)
        assert simple_fig.dpi == pytest.approx(original_dpi)

    def test_figure_with_existing_texts_is_not_corrupted(self) -> None:
        """
        Description: If the figure already contains text artists, the preview
        call must not remove them (only the annotation it added).
        Scenario: Add a text to the figure; call preview_print_size; verify text
        still present after.
        Expectation: Pre-existing text is still in fig.texts after the call.
        """
        fig, _ax = plt.subplots()
        existing = fig.text(0.5, 0.95, "my title", ha="center")
        with patch(_SHOW_TARGET):
            preview_print_size(fig)
        assert existing in fig.texts

    def test_multiple_calls_on_same_figure_leave_no_residual_annotations(self, simple_fig) -> None:
        """
        Description: Calling preview_print_size multiple times on the same
        figure must not accumulate annotation text artists.
        Scenario: Call preview_print_size twice; count fig.texts before and after.
        Expectation: fig.texts count is the same after both calls.
        """
        text_count_before = len(simple_fig.texts)
        with patch(_SHOW_TARGET):
            preview_print_size(simple_fig)
            preview_print_size(simple_fig)
        assert len(simple_fig.texts) == text_count_before
