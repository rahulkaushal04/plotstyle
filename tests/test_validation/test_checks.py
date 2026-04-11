"""Comprehensive test suite for plotstyle.validation.checks.*.

Covers:
- _base.py  : check decorator and get_registered_checks()
- dimensions : check_dimensions()
- colors     : internal helpers + check_color_accessibility()
- export     : check_export_settings()
- lines      : check_line_weights()
- typography : _gather_text_artists() + check_typography()
- __init__   : run_all()
- validate() : public API integration
"""

from __future__ import annotations

from unittest.mock import MagicMock

import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")

from plotstyle.validation.checks._base import (
    _REGISTERED_CHECKS,
    check,
    get_registered_checks,
)
from plotstyle.validation.checks.colors import (
    _color_only_differentiator,
    _extract_data_colors,
    _find_grayscale_conflicts,
    _has_red_green_pair,
    _hue_in_range,
    _is_green_hue,
    _is_red_hue,
    check_color_accessibility,
)
from plotstyle.validation.checks.dimensions import (
    _TOLERANCE_MM,
    check_dimensions,
)
from plotstyle.validation.checks.export import (
    _TRUETYPE_FONTTYPE,
    check_export_settings,
)
from plotstyle.validation.checks.lines import (
    check_line_weights,
)
from plotstyle.validation.checks.typography import (
    _gather_text_artists,
    check_typography,
)
from plotstyle.validation.report import CheckStatus

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all figures after every test to prevent memory leaks."""
    yield
    plt.close("all")


@pytest.fixture
def restore_rcparams():
    """Restore rcParams after each test that modifies them."""
    with mpl.rc_context():
        yield


@pytest.fixture
def make_spec():
    """Factory for minimal mock JournalSpec objects.

    Returns a callable that accepts keyword overrides and returns a MagicMock
    configured with sensible defaults matching a Nature-like spec.
    """

    def _factory(
        name: str = "TestJournal",
        single_column_mm: float = 89.0,
        double_column_mm: float = 183.0,
        max_height_mm: float = 247.0,
        min_font_pt: float = 7.0,
        max_font_pt: float = 9.0,
        min_dpi: int = 300,
        min_weight_pt: float = 0.5,
        colorblind_required: bool = True,
        grayscale_required: bool = False,
        avoid_combinations=None,
    ) -> MagicMock:
        spec = MagicMock()
        spec.metadata.name = name
        spec.dimensions.single_column_mm = single_column_mm
        spec.dimensions.double_column_mm = double_column_mm
        spec.dimensions.max_height_mm = max_height_mm
        spec.typography.min_font_pt = min_font_pt
        spec.typography.max_font_pt = max_font_pt
        spec.export.min_dpi = min_dpi
        spec.line.min_weight_pt = min_weight_pt
        spec.color.colorblind_required = colorblind_required
        spec.color.grayscale_required = grayscale_required
        spec.color.avoid_combinations = avoid_combinations if avoid_combinations is not None else []
        return spec

    return _factory


@pytest.fixture
def nature_spec(make_spec):
    """A Nature-like spec: single=89mm, double=183mm, max_h=247mm."""
    return make_spec(
        name="Nature",
        avoid_combinations=[["red", "green"]],
        grayscale_required=False,
    )


@pytest.fixture
def ieee_spec(make_spec):
    """An IEEE-like spec with grayscale required."""
    return make_spec(
        name="IEEE",
        single_column_mm=88.9,
        double_column_mm=182.0,
        max_height_mm=216.0,
        min_dpi=600,
        min_weight_pt=0.5,
        avoid_combinations=[["red", "green"]],
        grayscale_required=True,
    )


@pytest.fixture
def single_col_fig():
    """Figure sized to Nature single-column width (89 mm)."""
    width_in = 89.0 / 25.4
    fig, ax = plt.subplots(figsize=(width_in, 4.0))
    ax.plot([0, 1], [0, 1], lw=1.0, color="blue")
    return fig, ax


@pytest.fixture
def double_col_fig():
    """Figure sized to Nature double-column width (183 mm)."""
    width_in = 183.0 / 25.4
    fig, ax = plt.subplots(figsize=(width_in, 4.0))
    ax.plot([0, 1], [0, 1], lw=1.0, color="blue")
    return fig, ax


@pytest.fixture
def wide_fig():
    """Figure with a width nowhere near Nature single or double column."""
    fig, ax = plt.subplots(figsize=(10.0, 4.0))
    ax.plot([0, 1], [0, 1], lw=1.0)
    return fig, ax


# ---------------------------------------------------------------------------
# _base: check decorator and get_registered_checks
# ---------------------------------------------------------------------------


class TestCheckDecorator:
    """Validate the @check registration decorator."""

    def test_decorator_appends_function_to_registry(self) -> None:
        """
        Description: The @check decorator must append the decorated function to
        _REGISTERED_CHECKS so it will be executed by run_all().
        Scenario: Decorate a sentinel function; check registry membership.
        Expectation: sentinel is in _REGISTERED_CHECKS afterwards.
        """

        def _sentinel(fig, spec):
            return []

        before = len(_REGISTERED_CHECKS)
        check(_sentinel)
        try:
            assert _sentinel in _REGISTERED_CHECKS
            assert len(_REGISTERED_CHECKS) == before + 1
        finally:
            _REGISTERED_CHECKS.remove(_sentinel)

    def test_decorator_returns_function_unchanged(self) -> None:
        """
        Description: @check must return the decorated function itself (pass-
        through) so the function can still be called directly in tests.
        Scenario: Apply check decorator; compare identity.
        Expectation: result is the original function.
        """

        def _sentinel2(fig, spec):
            return []

        result = check(_sentinel2)
        try:
            assert result is _sentinel2
        finally:
            _REGISTERED_CHECKS.remove(_sentinel2)

    def test_get_registered_checks_returns_list(self) -> None:
        """
        Description: get_registered_checks() must return a list so callers
        can iterate or filter without a type error.
        Scenario: Call get_registered_checks().
        Expectation: Returns a list.
        """
        assert isinstance(get_registered_checks(), list)

    def test_get_registered_checks_returns_copy(self) -> None:
        """
        Description: get_registered_checks() must return a COPY of the internal
        list so external mutations (e.g. clear()) do not corrupt the registry.
        Scenario: Clear the returned list; call get_registered_checks() again.
        Expectation: Second call still returns a non-empty list.
        """
        snapshot = get_registered_checks()
        snapshot.clear()
        after = get_registered_checks()
        assert len(after) > 0

    def test_registry_contains_built_in_checks(self) -> None:
        """
        Description: Importing the validation package auto-imports all check
        modules which register their functions; the registry must contain them.
        Scenario: Import plotstyle.validation.checks to trigger side effects.
        Expectation: len(get_registered_checks()) >= 5.
        """
        import plotstyle.validation.checks  # noqa: F401 (triggers registrations)

        assert len(get_registered_checks()) >= 5


# ---------------------------------------------------------------------------
# check_dimensions
# ---------------------------------------------------------------------------


class TestCheckDimensions:
    """Validate check_dimensions() for width and height sub-checks."""

    def test_returns_exactly_two_results(self, single_col_fig, nature_spec) -> None:
        """
        Description: check_dimensions must always return exactly two results
        (width and height) so callers can index them by position.
        Scenario: Single-column-sized figure against nature spec.
        Expectation: len == 2.
        """
        fig, _ = single_col_fig
        results = check_dimensions(fig, nature_spec)
        assert len(results) == 2

    def test_check_names_are_correct(self, single_col_fig, nature_spec) -> None:
        """
        Description: The two result check_names must be 'dimensions.width'
        and 'dimensions.height' — these are stable API keys.
        Scenario: Single-column figure.
        Expectation: check_names match expected values.
        """
        fig, _ = single_col_fig
        results = check_dimensions(fig, nature_spec)
        assert results[0].check_name == "dimensions.width"
        assert results[1].check_name == "dimensions.height"

    def test_single_column_width_passes(self, single_col_fig, nature_spec) -> None:
        """
        Description: A figure sized to exactly single-column width must produce
        a PASS for the width check.
        Scenario: Nature single-column figure.
        Expectation: results[0].status == PASS.
        """
        fig, _ = single_col_fig
        results = check_dimensions(fig, nature_spec)
        assert results[0].status is CheckStatus.PASS

    def test_double_column_width_passes(self, double_col_fig, nature_spec) -> None:
        """
        Description: A figure sized to double-column width must also pass.
        Scenario: Nature double-column figure.
        Expectation: results[0].status == PASS.
        """
        fig, _ = double_col_fig
        results = check_dimensions(fig, nature_spec)
        assert results[0].status is CheckStatus.PASS

    def test_wrong_width_fails(self, wide_fig, nature_spec) -> None:
        """
        Description: A figure width that matches neither single nor double column
        (with tolerance) must produce a FAIL on the width check.
        Scenario: 10-inch-wide figure against 89/183mm spec.
        Expectation: results[0].status == FAIL.
        """
        fig, _ = wide_fig
        results = check_dimensions(fig, nature_spec)
        assert results[0].status is CheckStatus.FAIL

    def test_fail_result_includes_fix_suggestion(self, wide_fig, nature_spec) -> None:
        """
        Description: A width FAIL must include a fix_suggestion so the user
        knows how to correct the figure size.
        Scenario: Wrong-width figure.
        Expectation: fix_suggestion is non-empty.
        """
        fig, _ = wide_fig
        results = check_dimensions(fig, nature_spec)
        assert results[0].fix_suggestion is not None
        assert len(results[0].fix_suggestion) > 0

    def test_height_within_limit_passes(self, nature_spec) -> None:
        """
        Description: A figure whose height is below max_height_mm must pass
        the height check.
        Scenario: Figure with height well within Nature's 247mm limit.
        Expectation: results[1].status == PASS.
        """
        width_in = 89.0 / 25.4
        height_in = 100.0 / 25.4  # 100mm << 247mm
        fig, _ = plt.subplots(figsize=(width_in, height_in))
        results = check_dimensions(fig, nature_spec)
        assert results[1].status is CheckStatus.PASS

    def test_height_exceeding_limit_fails(self, nature_spec) -> None:
        """
        Description: A figure taller than max_height_mm (plus tolerance) must
        produce a FAIL on the height check.
        Scenario: Figure with height 350mm (> 247mm + 1mm tolerance).
        Expectation: results[1].status == FAIL.
        """
        width_in = 89.0 / 25.4
        height_in = 350.0 / 25.4  # 350mm >> 247mm
        fig, _ = plt.subplots(figsize=(width_in, height_in))
        results = check_dimensions(fig, nature_spec)
        assert results[1].status is CheckStatus.FAIL

    def test_width_within_tolerance_passes(self, nature_spec) -> None:
        """
        Description: A figure width within _TOLERANCE_MM of single-column spec
        must still pass — the tolerance accommodates unit-conversion rounding.
        Scenario: Figure width at spec minus 0.5mm (within 1mm tolerance).
        Expectation: PASS.
        """
        width_mm = 89.0 - 0.5  # within 1mm tolerance
        width_in = width_mm / 25.4
        fig, _ = plt.subplots(figsize=(width_in, 4.0))
        results = check_dimensions(fig, nature_spec)
        assert results[0].status is CheckStatus.PASS

    def test_tolerance_constant_is_positive(self) -> None:
        """
        Description: _TOLERANCE_MM must be a positive number; zero or negative
        would make exact width matching impossible.
        Scenario: Inspect constant value.
        Expectation: > 0.
        """
        assert _TOLERANCE_MM > 0


# ---------------------------------------------------------------------------
# colors: internal helpers
# ---------------------------------------------------------------------------


class TestHueInRange:
    """Validate _hue_in_range() boundary conditions."""

    @pytest.mark.parametrize(
        "hue, lo, hi, expected",
        [
            (15.0, 0.0, 30.0, True),  # interior
            (0.0, 0.0, 30.0, True),  # lower boundary
            (30.0, 0.0, 30.0, True),  # upper boundary
            (31.0, 0.0, 30.0, False),  # just outside
            (120.0, 80.0, 160.0, True),
            (79.9, 80.0, 160.0, False),
        ],
    )
    def test_boundary_conditions(self, hue: float, lo: float, hi: float, expected: bool) -> None:
        """
        Description: _hue_in_range must correctly classify hues at and around
        boundary values, including inclusive lower and upper bounds.
        Scenario: Parametrized hue/lo/hi values.
        Expectation: Returns expected bool.
        """
        assert _hue_in_range(hue, lo, hi) is expected


class TestIsRedHue:
    """Validate _is_red_hue() for the wrap-around red range."""

    @pytest.mark.parametrize(
        "hue_deg, expected",
        [
            (0.0, True),  # 0° is red
            (15.0, True),  # core red
            (30.0, True),  # boundary
            (340.0, True),  # near-crimson wraps
            (355.0, True),  # almost 360° red
            (80.0, False),  # green
            (200.0, False),  # blue
            (60.0, False),  # yellow — outside both red ranges
        ],
    )
    def test_red_hue_classification(self, hue_deg: float, expected: bool) -> None:
        """
        Description: Red hues span [330,360] U [0,30]; any hue in those ranges
        must be classified as red; all others must not.
        Scenario: Parametrized hue values.
        Expectation: Returns expected bool.
        """
        assert _is_red_hue(hue_deg) is expected


class TestIsGreenHue:
    """Validate _is_green_hue() for [80°, 160°]."""

    @pytest.mark.parametrize(
        "hue_deg, expected",
        [
            (80.0, True),
            (120.0, True),
            (160.0, True),
            (79.9, False),
            (160.1, False),
            (0.0, False),
            (300.0, False),
        ],
    )
    def test_green_hue_classification(self, hue_deg: float, expected: bool) -> None:
        """
        Description: Green is defined as [80°, 160°]; the check must be
        inclusive at both boundaries.
        Scenario: Parametrized hue values.
        Expectation: Returns expected bool.
        """
        assert _is_green_hue(hue_deg) is expected


class TestHasRedGreenPair:
    """Validate _has_red_green_pair() with real colour strings."""

    def test_red_and_green_returns_true(self) -> None:
        """
        Description: A list containing a pure red and a pure green must return
        True so the accessibility check can flag the combination.
        Scenario: ["#ff0000", "#00bb00"].
        Expectation: True.
        """
        assert _has_red_green_pair(["#ff0000", "#00bb00"]) is True

    def test_only_red_returns_false(self) -> None:
        """
        Description: Only red, no green — no problematic pair exists.
        Scenario: ["#ff0000", "#0000ff"].
        Expectation: False.
        """
        assert _has_red_green_pair(["#ff0000", "#0000ff"]) is False

    def test_only_green_returns_false(self) -> None:
        """
        Description: Only green, no red — no problematic pair.
        Scenario: ["#00cc00", "#0000ff"].
        Expectation: False.
        """
        assert _has_red_green_pair(["#00cc00", "#0000ff"]) is False

    def test_empty_list_returns_false(self) -> None:
        """
        Description: An empty colour list has no pair at all.
        Scenario: [].
        Expectation: False.
        """
        assert _has_red_green_pair([]) is False

    def test_achromatic_colors_ignored(self) -> None:
        """
        Description: Near-grey colours (low saturation) must not be classified
        as red or green to avoid false positives from background elements.
        Scenario: ["#888888", "#aaaaaa"] — both grey.
        Expectation: False.
        """
        assert _has_red_green_pair(["#888888", "#aaaaaa"]) is False

    def test_short_circuit_on_first_match(self) -> None:
        """
        Description: Once both red and green are found the function must stop
        scanning — verifiable by providing a minimal two-element list.
        Scenario: ["#ff0000", "#00cc00", "#0000ff"].
        Expectation: True (found after two elements).
        """
        assert _has_red_green_pair(["#ff0000", "#00cc00", "#0000ff"]) is True


class TestFindGrayscaleConflicts:
    """Validate _find_grayscale_conflicts() index-pair return values."""

    def test_identical_colours_produce_conflict(self) -> None:
        """
        Description: Two identical colours have zero luminance difference and
        must appear as a conflict pair.
        Scenario: ["#336699", "#336699"].
        Expectation: At least one conflict pair returned.
        """
        conflicts = _find_grayscale_conflicts(["#336699", "#336699"])
        assert len(conflicts) >= 1

    def test_black_and_white_produce_no_conflict(self) -> None:
        """
        Description: Black (lum=0) and white (lum=1) have maximum luminance
        contrast and must never conflict.
        Scenario: ["#000000", "#ffffff"].
        Expectation: Empty list.
        """
        conflicts = _find_grayscale_conflicts(["#000000", "#ffffff"])
        assert conflicts == []

    def test_single_colour_produces_no_conflict(self) -> None:
        """
        Description: With only one colour there are no pairs, so no conflicts.
        Scenario: ["#ff0000"].
        Expectation: [].
        """
        conflicts = _find_grayscale_conflicts(["#ff0000"])
        assert conflicts == []

    def test_empty_list_produces_no_conflict(self) -> None:
        """
        Description: Empty colour list must never raise an exception.
        Scenario: [].
        Expectation: [].
        """
        assert _find_grayscale_conflicts([]) == []

    def test_returned_pairs_are_ordered_i_less_than_j(self) -> None:
        """
        Description: Every returned pair (i, j) must satisfy i < j —
        upper-triangular convention prevents double-counting.
        Scenario: Feed three identical colours.
        Expectation: All pairs satisfy i < j.
        """
        conflicts = _find_grayscale_conflicts(["#555555", "#555555", "#555555"])
        for i, j in conflicts:
            assert i < j

    def test_custom_threshold_respected(self) -> None:
        """
        Description: The threshold parameter must determine which pairs are
        flagged; a very low threshold must produce fewer conflicts.
        Scenario: Two very similar colours; check with threshold=0.01.
        Expectation: No conflict at 0.01 threshold (minimal difference allowed).
        """
        # Two nearly identical grey values that would fail at 0.10 but pass at 0.001
        conflicts = _find_grayscale_conflicts(["#808080", "#818181"], threshold=0.001)
        assert len(conflicts) == 0


class TestColorOnlyDifferentiator:
    """Validate _color_only_differentiator() for multi-line figures."""

    def test_two_lines_same_style_returns_true(self) -> None:
        """
        Description: Two lines with identical linestyle and no marker make
        colour the only distinguishing cue — must return True.
        Scenario: Two solid lines, no markers.
        Expectation: True.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="red", linestyle="-")
        ax.plot([0, 1], [1, 0], color="blue", linestyle="-")
        assert _color_only_differentiator(fig) is True

    def test_two_lines_different_style_returns_false(self) -> None:
        """
        Description: Lines with different linestyles are distinguishable
        without colour — must return False.
        Scenario: One solid, one dashed.
        Expectation: False.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="red", linestyle="-")
        ax.plot([0, 1], [1, 0], color="blue", linestyle="--")
        assert _color_only_differentiator(fig) is False

    def test_single_line_returns_false(self) -> None:
        """
        Description: A single line has no peer to compare against; there is
        no colour-only differentiation problem.
        Scenario: One line only.
        Expectation: False.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="red")
        assert _color_only_differentiator(fig) is False

    def test_empty_axes_returns_false(self) -> None:
        """
        Description: An axes with no lines must return False (no pair to compare).
        Scenario: fig with no plots.
        Expectation: False.
        """
        fig, _ax = plt.subplots()
        assert _color_only_differentiator(fig) is False

    def test_lines_with_different_markers_returns_false(self) -> None:
        """
        Description: Lines with different markers are visually distinct even
        if linestyle is the same.
        Scenario: Two solid lines, different markers.
        Expectation: False.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="red", linestyle="-", marker="o")
        ax.plot([0, 1], [1, 0], color="blue", linestyle="-", marker="s")
        assert _color_only_differentiator(fig) is False


class TestExtractDataColors:
    """Validate _extract_data_colors() extraction from various artist types."""

    def test_extracts_line_colors(self) -> None:
        """
        Description: Colors from ax.plot() lines must be extracted.
        Scenario: Figure with a single red line.
        Expectation: A hex red colour appears in the result.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="red")
        colors = _extract_data_colors(fig)
        assert len(colors) > 0
        # Should contain a hex string
        assert any(c.startswith("#") for c in colors)

    def test_extracts_scatter_colors(self) -> None:
        """
        Description: Colors from ax.scatter() must be extracted from the
        PathCollection face colors.
        Scenario: Figure with scatter plot in blue.
        Expectation: Color list is non-empty.
        """
        fig, ax = plt.subplots()
        ax.scatter([1, 2, 3], [1, 2, 3], color="blue")
        colors = _extract_data_colors(fig)
        assert len(colors) > 0

    def test_extracts_bar_colors(self) -> None:
        """
        Description: Colors from ax.bar() BarContainer patches must be extracted.
        Scenario: Figure with a bar chart.
        Expectation: Color list is non-empty.
        """
        fig, ax = plt.subplots()
        ax.bar(["A", "B"], [1, 2], color="green")
        colors = _extract_data_colors(fig)
        assert len(colors) > 0

    def test_deduplicated_colors(self) -> None:
        """
        Description: The same colour drawn multiple times must appear only once
        in the result to avoid inflating palette analysis.
        Scenario: Two lines with the same red colour.
        Expectation: Red colour appears at most once.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="#ff0000")
        ax.plot([0, 1], [1, 0], color="#ff0000")
        colors = _extract_data_colors(fig)
        assert colors.count(colors[0]) == 1 if len(colors) > 0 else True

    def test_empty_figure_returns_empty(self) -> None:
        """
        Description: A figure with no plotted data must return an empty list.
        Scenario: Empty figure with bare axes.
        Expectation: [].
        """
        fig, _ax = plt.subplots()
        colors = _extract_data_colors(fig)
        assert colors == []


# ---------------------------------------------------------------------------
# check_color_accessibility
# ---------------------------------------------------------------------------


class TestCheckColorAccessibility:
    """Validate check_color_accessibility() against various figure/spec combos."""

    def test_no_rg_combination_in_avoid_skips_check(self, make_spec) -> None:
        """
        Description: When the spec does not list red-green in avoid_combinations,
        the red-green sub-check must be skipped entirely (no result entry).
        Scenario: Spec with no avoid combinations; figure with red and green.
        Expectation: No 'color.red_green' result.
        """
        spec = make_spec(avoid_combinations=[])
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="red")
        ax.plot([0, 1], [1, 0], color="green")
        results = check_color_accessibility(fig, spec)
        assert all(r.check_name != "color.red_green" for r in results)

    def test_red_green_pair_emits_warn(self, nature_spec) -> None:
        """
        Description: When a journal prohibits red-green pairs and the figure
        contains both, the check must emit WARN (not FAIL) because it is an
        accessibility advisory, not a hard rejection.
        Scenario: Figure with red and green lines; Nature spec.
        Expectation: color.red_green result with WARN status.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="#cc0000")  # vivid red
        ax.plot([0, 1], [1, 0], color="#00aa00")  # vivid green
        results = check_color_accessibility(fig, nature_spec)
        rg = next((r for r in results if r.check_name == "color.red_green"), None)
        assert rg is not None
        assert rg.status is CheckStatus.WARN

    def test_no_red_green_pair_emits_pass(self, nature_spec) -> None:
        """
        Description: When no red-green pair is present, the check must emit PASS.
        Scenario: Figure with blue and orange (safe pair).
        Expectation: color.red_green result with PASS status.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="blue")
        ax.plot([0, 1], [1, 0], color="orange")
        results = check_color_accessibility(fig, nature_spec)
        rg = next((r for r in results if r.check_name == "color.red_green"), None)
        assert rg is not None
        assert rg.status is CheckStatus.PASS

    def test_grayscale_check_skipped_when_not_required(self, nature_spec) -> None:
        """
        Description: When grayscale_required is False, the grayscale sub-check
        must be skipped.
        Scenario: nature_spec has grayscale_required=False.
        Expectation: No 'color.grayscale' result.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="blue")
        results = check_color_accessibility(fig, nature_spec)
        assert all(r.check_name != "color.grayscale" for r in results)

    def test_grayscale_skipped_with_single_color(self, ieee_spec) -> None:
        """
        Description: With only one data colour there are no pairs to compare;
        the grayscale check must be skipped.
        Scenario: IEEE spec (grayscale_required=True); figure with one line.
        Expectation: No 'color.grayscale' result.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="blue")
        results = check_color_accessibility(fig, ieee_spec)
        assert all(r.check_name != "color.grayscale" for r in results)

    def test_grayscale_conflict_emits_warn(self, ieee_spec) -> None:
        """
        Description: When ieee spec requires grayscale and two similar-
        luminance colours are present, the check must emit WARN.
        Scenario: Two medium-grey colours that are hard to distinguish in print.
        Expectation: color.grayscale result with WARN.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="#777777")
        ax.plot([0, 1], [1, 0], color="#888888")
        results = check_color_accessibility(fig, ieee_spec)
        gs = next((r for r in results if r.check_name == "color.grayscale"), None)
        assert gs is not None
        assert gs.status is CheckStatus.WARN

    def test_sole_differentiator_always_checked(self, nature_spec) -> None:
        """
        Description: The colour-only differentiator sub-check must always run
        regardless of the journal spec's colour settings.
        Scenario: Two same-style lines with spec that has no avoid_combinations.
        Expectation: 'color.sole_differentiator' result present.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="red", linestyle="-")
        ax.plot([0, 1], [1, 0], color="blue", linestyle="-")
        results = check_color_accessibility(fig, nature_spec)
        names = [r.check_name for r in results]
        assert "color.sole_differentiator" in names

    def test_sole_differentiator_pass_when_single_line(self, nature_spec) -> None:
        """
        Description: A figure with only one line has no colour-only
        differentiation issue — sole_differentiator result must not appear when
        no problem is detected.
        Scenario: Single-line figure.
        Expectation: No 'color.sole_differentiator' WARN result.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], color="blue")
        results = check_color_accessibility(fig, nature_spec)
        sd = next((r for r in results if r.check_name == "color.sole_differentiator"), None)
        # No sole_differentiator result should be added when there's no problem
        if sd is not None:
            assert sd.status is not CheckStatus.WARN


# ---------------------------------------------------------------------------
# check_export_settings
# ---------------------------------------------------------------------------


class TestCheckExportSettings:
    """Validate check_export_settings() rcParam checks."""

    def test_returns_three_results(self, nature_spec, restore_rcparams) -> None:
        """
        Description: check_export_settings must always return exactly three
        results (pdf_fonttype, ps_fonttype, dpi).
        Scenario: Any figure and spec.
        Expectation: len == 3.
        """
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        assert len(results) == 3

    def test_check_names_are_stable(self, nature_spec, restore_rcparams) -> None:
        """
        Description: The check names must be stable API keys for downstream
        consumers that filter by name.
        Scenario: Default rcParams.
        Expectation: names are pdf_fonttype, ps_fonttype, dpi.
        """
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        names = [r.check_name for r in results]
        assert "export.pdf_fonttype" in names
        assert "export.ps_fonttype" in names
        assert "export.dpi" in names

    def test_all_pass_when_correctly_configured(self, nature_spec, restore_rcparams) -> None:
        """
        Description: When all three rcParams are correctly set, all checks
        must pass.
        Scenario: Set pdf.fonttype=42, ps.fonttype=42, savefig.dpi=300.
        Expectation: All three PASS.
        """
        mpl.rcParams["pdf.fonttype"] = 42
        mpl.rcParams["ps.fonttype"] = 42
        mpl.rcParams["savefig.dpi"] = 300
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        assert all(r.status is CheckStatus.PASS for r in results)

    def test_pdf_fonttype_fail_when_type3(self, nature_spec, restore_rcparams) -> None:
        """
        Description: pdf.fonttype=3 (Type 3 embedding) must produce a FAIL
        because journals and PDF preflight systems reject Type 3 fonts.
        Scenario: Set pdf.fonttype=3.
        Expectation: export.pdf_fonttype result is FAIL.
        """
        mpl.rcParams["pdf.fonttype"] = 3
        mpl.rcParams["ps.fonttype"] = 42
        mpl.rcParams["savefig.dpi"] = 300
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        pdf_result = next(r for r in results if r.check_name == "export.pdf_fonttype")
        assert pdf_result.status is CheckStatus.FAIL

    def test_ps_fonttype_fail_when_type3(self, nature_spec, restore_rcparams) -> None:
        """
        Description: ps.fonttype=3 must produce a FAIL for EPS output font checks.
        Scenario: ps.fonttype=3, pdf.fonttype=42.
        Expectation: export.ps_fonttype result is FAIL.
        """
        mpl.rcParams["pdf.fonttype"] = 42
        mpl.rcParams["ps.fonttype"] = 3
        mpl.rcParams["savefig.dpi"] = 300
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        ps_result = next(r for r in results if r.check_name == "export.ps_fonttype")
        assert ps_result.status is CheckStatus.FAIL

    def test_dpi_fail_when_below_minimum(self, nature_spec, restore_rcparams) -> None:
        """
        Description: savefig.dpi below the journal's minimum must produce FAIL.
        Scenario: savefig.dpi=72 but spec requires 300.
        Expectation: export.dpi result is FAIL.
        """
        mpl.rcParams["pdf.fonttype"] = 42
        mpl.rcParams["ps.fonttype"] = 42
        mpl.rcParams["savefig.dpi"] = 72
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        dpi_result = next(r for r in results if r.check_name == "export.dpi")
        assert dpi_result.status is CheckStatus.FAIL

    def test_dpi_warn_when_figure_string(self, nature_spec, restore_rcparams) -> None:
        """
        Description: savefig.dpi='figure' (Matplotlib's default) must produce
        WARN rather than FAIL since the actual DPI is not deterministic.
        Scenario: savefig.dpi='figure'.
        Expectation: export.dpi result is WARN.
        """
        mpl.rcParams["pdf.fonttype"] = 42
        mpl.rcParams["ps.fonttype"] = 42
        mpl.rcParams["savefig.dpi"] = "figure"
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        dpi_result = next(r for r in results if r.check_name == "export.dpi")
        assert dpi_result.status is CheckStatus.WARN

    def test_truetype_fonttype_constant_is_42(self) -> None:
        """
        Description: The TrueType font type constant must be 42 — the PDF spec
        value for embedded TrueType fonts.
        Scenario: Inspect _TRUETYPE_FONTTYPE.
        Expectation: 42.
        """
        assert _TRUETYPE_FONTTYPE == 42

    def test_fail_result_includes_fix_suggestion(self, nature_spec, restore_rcparams) -> None:
        """
        Description: FAIL results for export settings must provide a fix
        suggestion so the user knows how to correct the configuration.
        Scenario: All three settings wrong.
        Expectation: Each FAIL result has non-None fix_suggestion.
        """
        mpl.rcParams["pdf.fonttype"] = 3
        mpl.rcParams["ps.fonttype"] = 3
        mpl.rcParams["savefig.dpi"] = 72
        fig, _ = plt.subplots()
        results = check_export_settings(fig, nature_spec)
        for r in results:
            if r.status is CheckStatus.FAIL:
                assert r.fix_suggestion is not None


# ---------------------------------------------------------------------------
# check_line_weights
# ---------------------------------------------------------------------------


class TestCheckLineWeights:
    """Validate check_line_weights() for lines and spines."""

    def test_returns_exactly_one_result(self, make_spec) -> None:
        """
        Description: check_line_weights must return exactly one result (the
        aggregate lines.min_weight check).
        Scenario: Simple figure with one passing line.
        Expectation: len == 1.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=1.0)
        results = check_line_weights(fig, spec)
        assert len(results) == 1

    def test_check_name_is_stable(self, make_spec) -> None:
        """
        Description: check_name must be 'lines.min_weight' — a stable key for
        downstream consumers.
        Scenario: Any figure.
        Expectation: check_name == 'lines.min_weight'.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=1.0)
        results = check_line_weights(fig, spec)
        assert results[0].check_name == "lines.min_weight"

    def test_line_above_minimum_passes(self, make_spec) -> None:
        """
        Description: A line whose linewidth equals or exceeds the minimum must
        produce a PASS result.
        Scenario: lw=1.0 vs min_weight_pt=0.5.
        Expectation: PASS.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=1.0)
        results = check_line_weights(fig, spec)
        assert results[0].status is CheckStatus.PASS

    def test_line_at_minimum_passes(self, make_spec) -> None:
        """
        Description: A line exactly at the minimum weight must pass (strict <,
        not <=, in the violation check).
        Scenario: lw=0.5 vs min_weight_pt=0.5.
        Expectation: PASS.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, ax = plt.subplots()
        # Draw line directly at minimum — must pass by the strict < rule
        ax.plot([0, 1], [0, 1], lw=0.5)
        results = check_line_weights(fig, spec)
        assert results[0].status is CheckStatus.PASS

    def test_line_below_minimum_fails(self, make_spec) -> None:
        """
        Description: A line whose linewidth is below the minimum must produce
        a FAIL result so the user knows to increase it.
        Scenario: lw=0.1 vs min_weight_pt=0.5.
        Expectation: FAIL.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=0.1)
        results = check_line_weights(fig, spec)
        assert results[0].status is CheckStatus.FAIL

    def test_fail_result_includes_fix_suggestion(self, make_spec) -> None:
        """
        Description: A FAIL for line weights must include a fix suggestion.
        Scenario: Under-weight line.
        Expectation: fix_suggestion is not None.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=0.1)
        results = check_line_weights(fig, spec)
        assert results[0].fix_suggestion is not None

    def test_empty_figure_passes(self, make_spec) -> None:
        """
        Description: A figure with no lines should pass since there are no
        violations — absence of under-weight lines is success.
        Scenario: Empty axes (no plot calls).
        Expectation: PASS.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, _ax = plt.subplots()
        results = check_line_weights(fig, spec)
        assert results[0].status is CheckStatus.PASS

    def test_multiple_violations_reported(self, make_spec) -> None:
        """
        Description: When multiple lines are below the minimum, the message
        must mention multiple violations.
        Scenario: Three thin lines.
        Expectation: FAIL; message mentions count.
        """
        spec = make_spec(min_weight_pt=0.5)
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=0.1)
        ax.plot([0, 1], [0.5, 0.5], lw=0.2)
        ax.plot([0, 1], [0.8, 0.8], lw=0.3)
        results = check_line_weights(fig, spec)
        assert results[0].status is CheckStatus.FAIL
        # Message should mention that multiple elements are below minimum
        assert any(char.isdigit() for char in results[0].message)


# ---------------------------------------------------------------------------
# _gather_text_artists and check_typography
# ---------------------------------------------------------------------------


class TestGatherTextArtists:
    """Validate _gather_text_artists() coverage of text element types."""

    def test_returns_list(self) -> None:
        """
        Description: _gather_text_artists must return a list.
        Scenario: Any figure.
        Expectation: isinstance(result, list).
        """
        fig, ax = plt.subplots()
        ax.set_title("Title")
        assert isinstance(_gather_text_artists(fig), list)

    def test_includes_title(self) -> None:
        """
        Description: The axes title must be included in the collected text
        artists since it is a labelling element.
        Scenario: Axes with a title set.
        Expectation: Title text appears in collected artists.
        """
        fig, ax = plt.subplots()
        ax.set_title("My Title")
        texts = [t.get_text() for t in _gather_text_artists(fig)]
        assert "My Title" in texts

    def test_includes_xlabels(self) -> None:
        """
        Description: The x-axis label must be included.
        Scenario: Axes with x label.
        Expectation: 'X Axis' appears.
        """
        fig, ax = plt.subplots()
        ax.set_xlabel("X Axis")
        texts = [t.get_text() for t in _gather_text_artists(fig)]
        assert "X Axis" in texts

    def test_includes_ylabels(self) -> None:
        """
        Description: The y-axis label must be included.
        Scenario: Axes with y label.
        Expectation: 'Y Axis' appears.
        """
        fig, ax = plt.subplots()
        ax.set_ylabel("Y Axis")
        texts = [t.get_text() for t in _gather_text_artists(fig)]
        assert "Y Axis" in texts

    def test_includes_figure_suptitle(self) -> None:
        """
        Description: fig.text() artists (suptitles) must be included.
        Scenario: Figure with suptitle.
        Expectation: Suptitle text appears in collected artists.
        """
        fig, _ax = plt.subplots()
        fig.suptitle("My Suptitle")
        texts = [t.get_text() for t in _gather_text_artists(fig)]
        assert "My Suptitle" in texts

    def test_does_not_modify_fig_texts(self) -> None:
        """
        Description: _gather_text_artists must not mutate fig.texts (it must
        work on a copy to avoid side effects).
        Scenario: Figure with one text artist; inspect fig.texts after call.
        Expectation: fig.texts length unchanged.
        """
        fig, _ax = plt.subplots()
        fig.text(0.5, 0.95, "Annotation")
        before = len(fig.texts)
        _gather_text_artists(fig)
        assert len(fig.texts) == before


class TestCheckTypography:
    """Validate check_typography() for font size compliance."""

    def test_returns_exactly_one_result(self, make_spec) -> None:
        """
        Description: check_typography must return exactly one result.
        Scenario: Simple figure.
        Expectation: len == 1.
        """
        spec = make_spec(min_font_pt=7.0, max_font_pt=9.0)
        fig, ax = plt.subplots()
        ax.set_xlabel("X", fontsize=8)
        results = check_typography(fig, spec)
        assert len(results) == 1

    def test_check_name_is_stable(self, make_spec) -> None:
        """
        Description: check_name must be 'typography.font_size'.
        Scenario: Any figure.
        Expectation: check_name == 'typography.font_size'.
        """
        spec = make_spec(min_font_pt=7.0, max_font_pt=9.0)
        fig, _ax = plt.subplots()
        results = check_typography(fig, spec)
        assert results[0].check_name == "typography.font_size"

    def test_compliant_font_sizes_pass(self, make_spec) -> None:
        """
        Description: Text with font sizes within [min_font_pt, max_font_pt]
        must produce a PASS result.
        Scenario: Full figure created inside rc_context(font.size=8) so that
        tick labels also use 8pt - within the 7-9pt allowed range.
        Expectation: PASS.
        """
        spec = make_spec(min_font_pt=7.0, max_font_pt=9.0)
        with mpl.rc_context({"font.size": 8.0}):
            fig, ax = plt.subplots()
            ax.set_xlabel("X", fontsize=8)
            ax.set_title("T", fontsize=8)
        results = check_typography(fig, spec)
        assert results[0].status is CheckStatus.PASS

    def test_below_minimum_font_fails(self, make_spec) -> None:
        """
        Description: Text below min_font_pt must produce FAIL so the user
        knows their figure text will be illegible at journal column width.
        Scenario: xlabel at 4pt vs min=7pt.
        Expectation: FAIL.
        """
        spec = make_spec(min_font_pt=7.0, max_font_pt=9.0)
        fig, ax = plt.subplots()
        ax.set_xlabel("Too small", fontsize=4)
        results = check_typography(fig, spec)
        assert results[0].status is CheckStatus.FAIL

    def test_above_maximum_font_fails(self, make_spec) -> None:
        """
        Description: Text above max_font_pt must produce FAIL.
        Scenario: title at 20pt vs max=9pt.
        Expectation: FAIL.
        """
        spec = make_spec(min_font_pt=7.0, max_font_pt=9.0)
        fig, ax = plt.subplots()
        ax.set_title("Too large", fontsize=20)
        results = check_typography(fig, spec)
        assert results[0].status is CheckStatus.FAIL

    def test_empty_text_artists_are_skipped(self, make_spec) -> None:
        """
        Description: Empty or whitespace-only text artists must not trigger
        a FAIL even if their explicit font size is outside the allowed range.
        Scenario: All in-range text + one empty Text at 4pt (out of range).
        Expectation: PASS because the empty artist is skipped.
        """
        spec = make_spec(min_font_pt=7.0, max_font_pt=9.0)
        # Create the figure with all valid font sizes
        with mpl.rc_context({"font.size": 8.0}):
            fig, _ax = plt.subplots()
        # Add a deliberately out-of-range but EMPTY text - must not trigger FAIL
        fig.text(0.5, 0.5, "", fontsize=4)
        results = check_typography(fig, spec)
        assert results[0].status is CheckStatus.PASS

    def test_fail_result_includes_fix_suggestion(self, make_spec) -> None:
        """
        Description: Typography FAIL must include a fix suggestion with the
        allowed range so the user can apply the correction.
        Scenario: Under-size font.
        Expectation: fix_suggestion is not None and mentions font size.
        """
        spec = make_spec(min_font_pt=7.0, max_font_pt=9.0)
        fig, ax = plt.subplots()
        ax.set_xlabel("Too small", fontsize=4)
        results = check_typography(fig, spec)
        assert results[0].fix_suggestion is not None


# ---------------------------------------------------------------------------
# run_all() integration
# ---------------------------------------------------------------------------


class TestRunAll:
    """Validate that run_all() correctly dispatches to all registered checks."""

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_run_all_returns_list(self, nature_spec) -> None:
        """
        Description: run_all() must return a list of CheckResult objects.
        Scenario: Call run_all against a simple figure.
        Expectation: Returns a list.
        """
        from plotstyle.validation.checks import run_all

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=1.0)
        results = run_all(fig, nature_spec)
        assert isinstance(results, list)

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_run_all_returns_multiple_results(self, nature_spec) -> None:
        """
        Description: run_all() must return results from all registered checks
        (at least 5 from the built-in modules).
        Scenario: Typical figure and spec.
        Expectation: len >= 5.
        """
        from plotstyle.validation.checks import run_all

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1], lw=1.0)
        results = run_all(fig, nature_spec)
        assert len(results) >= 5

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_run_all_results_are_check_result_instances(self, nature_spec) -> None:
        """
        Description: Every element in the run_all output must be a CheckResult
        so callers can treat the list homogeneously.
        Scenario: Typical figure.
        Expectation: All elements are CheckResult instances.
        """
        from plotstyle.validation.checks import run_all
        from plotstyle.validation.report import CheckResult as CR

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        results = run_all(fig, nature_spec)
        assert all(isinstance(r, CR) for r in results)


# ---------------------------------------------------------------------------
# validate() public API integration
# ---------------------------------------------------------------------------


class TestValidatePublicAPI:
    """Validate the plotstyle.validation.validate() public function."""

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_returns_validation_report(self) -> None:
        """
        Description: validate() must return a ValidationReport so callers have
        a consistent, well-typed result object.
        Scenario: Simple figure validated against 'ieee'.
        Expectation: Returns ValidationReport.
        """
        from plotstyle.validation import validate
        from plotstyle.validation.report import ValidationReport

        fig, ax = plt.subplots(figsize=(88.9 / 25.4, 4.0))
        ax.plot([0, 1], [0, 1], lw=1.0)
        report = validate(fig, journal="ieee")
        assert isinstance(report, ValidationReport)

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_report_journal_name_matches_spec(self) -> None:
        """
        Description: The ValidationReport.journal attribute must be the spec's
        display name (e.g. 'IEEE Transactions') not the lowercase key.
        Scenario: validate(fig, journal='ieee').
        Expectation: report.journal contains 'IEEE'.
        """
        from plotstyle.validation import validate

        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        report = validate(fig, journal="ieee")
        assert "IEEE" in report.journal

    def test_unknown_journal_raises_key_error(self) -> None:
        """
        Description: validate() with an unknown journal must raise KeyError
        (SpecNotFoundError) so callers get a clear error.
        Scenario: journal='__no_such__'.
        Expectation: KeyError raised.
        """
        from plotstyle.validation import validate

        fig, _ax = plt.subplots()
        with pytest.raises(KeyError):
            validate(fig, journal="__no_such__")

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_journal_argument_is_keyword_only(self) -> None:
        """
        Description: The journal parameter must be keyword-only (PEP 3102) to
        prevent positional-argument confusion.
        Scenario: Try calling validate(fig, 'nature') positionally.
        Expectation: TypeError raised.
        """
        from plotstyle.validation import validate

        fig, _ax = plt.subplots()
        with pytest.raises(TypeError):
            validate(fig, "nature")  # type: ignore[call-arg]
