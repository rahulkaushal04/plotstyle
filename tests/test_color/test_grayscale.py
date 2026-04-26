"""Enhanced test suite for plotstyle.color.grayscale.

Covers: rgb_to_luminance, luminance_delta, is_grayscale_safe,
preview_grayscale, BT.709 coefficients, and all edge/error/boundary cases.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")

from plotstyle.color.grayscale import (
    _LUMA_B,
    _LUMA_G,
    _LUMA_R,
    is_grayscale_safe,
    luminance_delta,
    preview_grayscale,
    rgb_to_luminance,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all figures after each test to prevent resource leaks."""
    yield
    plt.close("all")


@pytest.fixture
def simple_fig() -> plt.Figure:
    """A minimal figure with coloured bars for grayscale preview."""
    fig, ax = plt.subplots(figsize=(2, 2), dpi=72)
    ax.bar([1, 2, 3], [4, 7, 2], color=["#e41a1c", "#377eb8", "#4daf4a"])
    return fig


# ---------------------------------------------------------------------------
# BT.709 luminance coefficients
# ---------------------------------------------------------------------------


class TestLumaCoefficients:
    """Validate the BT.709 luminance weight constants."""

    def test_coefficients_sum_to_one(self) -> None:
        """
        Description: BT.709 weights must sum to 1.0 exactly.
        Scenario: Sum _LUMA_R + _LUMA_G + _LUMA_B.
        Expectation: Sum == 1.0.
        """
        assert pytest.approx(1.0) == _LUMA_R + _LUMA_G + _LUMA_B

    def test_green_has_largest_weight(self) -> None:
        """
        Description: Green must have the largest coefficient (human perception).
        Scenario: Compare coefficients.
        Expectation: _LUMA_G > _LUMA_R > _LUMA_B.
        """
        assert _LUMA_G > _LUMA_R > _LUMA_B

    def test_coefficients_are_positive(self) -> None:
        """
        Description: All coefficients must be positive.
        Scenario: Check each coefficient.
        Expectation: > 0.
        """
        assert _LUMA_R > 0
        assert _LUMA_G > 0
        assert _LUMA_B > 0

    def test_known_bt709_values(self) -> None:
        """
        Description: Coefficients must match the BT.709 standard.
        Scenario: Compare against known values.
        Expectation: R=0.2126, G=0.7152, B=0.0722.
        """
        assert pytest.approx(0.2126) == _LUMA_R
        assert pytest.approx(0.7152) == _LUMA_G
        assert pytest.approx(0.0722) == _LUMA_B


# ---------------------------------------------------------------------------
# rgb_to_luminance
# ---------------------------------------------------------------------------


class TestRgbToLuminance:
    """Validate the per-colour luminance computation."""

    def test_white_luminance_is_one(self) -> None:
        """
        Description: Pure white (1, 1, 1) must have luminance 1.0.
        Scenario: rgb_to_luminance(1.0, 1.0, 1.0).
        Expectation: Result == 1.0.
        """
        assert rgb_to_luminance(1.0, 1.0, 1.0) == pytest.approx(1.0)

    def test_black_luminance_is_zero(self) -> None:
        """
        Description: Pure black (0, 0, 0) must have luminance 0.0.
        Scenario: rgb_to_luminance(0.0, 0.0, 0.0).
        Expectation: Result == 0.0.
        """
        assert rgb_to_luminance(0.0, 0.0, 0.0) == pytest.approx(0.0)

    def test_pure_red_luminance(self) -> None:
        """
        Description: Pure red (1, 0, 0) must have luminance == _LUMA_R.
        Scenario: rgb_to_luminance(1.0, 0.0, 0.0).
        Expectation: Result == 0.2126.
        """
        assert rgb_to_luminance(1.0, 0.0, 0.0) == pytest.approx(_LUMA_R)

    def test_pure_green_luminance(self) -> None:
        """
        Description: Pure green (0, 1, 0) must have luminance == _LUMA_G.
        Scenario: rgb_to_luminance(0.0, 1.0, 0.0).
        Expectation: Result == 0.7152.
        """
        assert rgb_to_luminance(0.0, 1.0, 0.0) == pytest.approx(_LUMA_G)

    def test_pure_blue_luminance(self) -> None:
        """
        Description: Pure blue (0, 0, 1) must have luminance == _LUMA_B.
        Scenario: rgb_to_luminance(0.0, 0.0, 1.0).
        Expectation: Result == 0.0722.
        """
        assert rgb_to_luminance(0.0, 0.0, 1.0) == pytest.approx(_LUMA_B)

    def test_mid_grey_luminance(self) -> None:
        """
        Description: Mid-grey (0.5, 0.5, 0.5) must have luminance 0.5.
        Scenario: Coefficients sum to 1, so 0.5*1.0 = 0.5.
        Expectation: Result == 0.5.
        """
        assert rgb_to_luminance(0.5, 0.5, 0.5) == pytest.approx(0.5)

    @pytest.mark.parametrize(
        "r,g,b,expected",
        [
            (1.0, 1.0, 1.0, 1.0),
            (0.0, 0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0, 0.2126),
            (0.0, 1.0, 0.0, 0.7152),
            (0.0, 0.0, 1.0, 0.0722),
        ],
    )
    def test_parametric_known_values(self, r: float, g: float, b: float, expected: float) -> None:
        """
        Description: Parametric validation of known luminance values.
        Scenario: Multiple input/output pairs.
        Expectation: Result matches expected.
        """
        assert rgb_to_luminance(r, g, b) == pytest.approx(expected)

    def test_result_is_float(self) -> None:
        """
        Description: Return type must be float.
        Scenario: Call with float inputs.
        Expectation: isinstance float.
        """
        result = rgb_to_luminance(0.3, 0.5, 0.7)
        assert isinstance(result, float)

    def test_luminance_in_unit_interval(self) -> None:
        """
        Description: For inputs in [0, 1], output must also be in [0, 1].
        Scenario: Boundary values.
        Expectation: 0 <= result <= 1.
        """
        for r in [0.0, 0.5, 1.0]:
            for g in [0.0, 0.5, 1.0]:
                for b in [0.0, 0.5, 1.0]:
                    result = rgb_to_luminance(r, g, b)
                    assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# luminance_delta
# ---------------------------------------------------------------------------


class TestLuminanceDelta:
    """Validate pairwise luminance difference computation."""

    def test_two_colors_returns_one_pair(self) -> None:
        """
        Description: Two colours must produce exactly one pair.
        Scenario: luminance_delta(['#000000', '#ffffff']).
        Expectation: len == 1.
        """
        pairs = luminance_delta(["#000000", "#ffffff"])
        assert len(pairs) == 1

    def test_three_colors_returns_three_pairs(self) -> None:
        """
        Description: Three colours must produce C(3,2)=3 pairs.
        Scenario: luminance_delta(['#000000', '#ffffff', '#888888']).
        Expectation: len == 3.
        """
        pairs = luminance_delta(["#000000", "#ffffff", "#888888"])
        assert len(pairs) == 3

    def test_pair_tuple_structure(self) -> None:
        """
        Description: Each pair must be a (idx_a, idx_b, delta) triple.
        Scenario: Inspect first pair.
        Expectation: 3-tuple with int, int, float.
        """
        pairs = luminance_delta(["#000000", "#ffffff"])
        idx_a, idx_b, delta = pairs[0]
        assert isinstance(idx_a, int)
        assert isinstance(idx_b, int)
        assert isinstance(delta, float)

    def test_indices_are_valid(self) -> None:
        """
        Description: Indices must be valid indices into the input list with i < j.
        Scenario: Three-colour palette.
        Expectation: 0 <= idx_a < idx_b <= 2.
        """
        pairs = luminance_delta(["#ff0000", "#00ff00", "#0000ff"])
        for idx_a, idx_b, _ in pairs:
            assert 0 <= idx_a < idx_b <= 2

    def test_sorted_ascending_by_delta(self) -> None:
        """
        Description: Pairs must be sorted by ascending delta.
        Scenario: Three colours with different luminances.
        Expectation: delta[i] <= delta[i+1] for all consecutive pairs.
        """
        pairs = luminance_delta(["#000000", "#888888", "#ffffff"])
        deltas = [d for _, _, d in pairs]
        assert deltas == sorted(deltas)

    def test_black_and_white_maximum_delta(self) -> None:
        """
        Description: Black and white must have the maximum delta ≈ 1.0.
        Scenario: luminance_delta(['#000000', '#ffffff']).
        Expectation: delta close to 1.0.
        """
        pairs = luminance_delta(["#000000", "#ffffff"])
        assert pairs[0][2] == pytest.approx(1.0, abs=0.01)

    def test_identical_colors_zero_delta(self) -> None:
        """
        Description: Identical colours must have delta 0.0.
        Scenario: luminance_delta(['#ff0000', '#ff0000']).
        Expectation: delta == 0.0.
        """
        pairs = luminance_delta(["#ff0000", "#ff0000"])
        assert pairs[0][2] == pytest.approx(0.0)

    def test_empty_list_returns_empty(self) -> None:
        """
        Description: Empty input must return an empty list.
        Scenario: luminance_delta([]).
        Expectation: [].
        """
        assert luminance_delta([]) == []

    def test_single_color_returns_empty(self) -> None:
        """
        Description: Single colour has no pairs.
        Scenario: luminance_delta(['#ff0000']).
        Expectation: [].
        """
        assert luminance_delta(["#ff0000"]) == []

    def test_deltas_are_non_negative(self) -> None:
        """
        Description: All deltas must be non-negative (absolute difference).
        Scenario: Various colour inputs.
        Expectation: delta >= 0.0 for all pairs.
        """
        pairs = luminance_delta(["#e41a1c", "#377eb8", "#4daf4a", "#984ea3"])
        for _, _, delta in pairs:
            assert delta >= 0.0

    def test_named_colors_accepted(self) -> None:
        """
        Description: Named matplotlib colours must be accepted.
        Scenario: luminance_delta(['red', 'blue', 'green']).
        Expectation: No error; valid pairs returned.
        """
        pairs = luminance_delta(["red", "blue", "green"])
        assert len(pairs) == 3

    def test_invalid_color_raises(self) -> None:
        """
        Description: Invalid colour strings must propagate ValueError.
        Scenario: luminance_delta(['not_a_color']).
        Expectation: ValueError (from matplotlib.colors.to_rgb).
        """
        with pytest.raises(ValueError):
            luminance_delta(["#000000", "not_a_valid_color_xyz"])

    def test_four_colors_six_pairs(self) -> None:
        """
        Description: Four colours must produce C(4,2)=6 pairs.
        Scenario: Four hex colours.
        Expectation: len == 6.
        """
        pairs = luminance_delta(["#000000", "#333333", "#666666", "#999999"])
        assert len(pairs) == 6

    def test_symmetric_delta(self) -> None:
        """
        Description: Delta must be symmetric: |L_a - L_b| == |L_b - L_a|.
        Scenario: Two colours in either order produce same delta.
        Expectation: Delta identical regardless of order.
        """
        pairs_ab = luminance_delta(["#ff0000", "#0000ff"])
        pairs_ba = luminance_delta(["#0000ff", "#ff0000"])
        assert pairs_ab[0][2] == pytest.approx(pairs_ba[0][2])


# ---------------------------------------------------------------------------
# is_grayscale_safe
# ---------------------------------------------------------------------------


class TestIsGrayscaleSafe:
    """Validate the grayscale safety check."""

    def test_well_separated_palette_is_safe(self) -> None:
        """
        Description: Black and white are maximally separated and must pass.
        Scenario: is_grayscale_safe(['#000000', '#ffffff']).
        Expectation: True.
        """
        assert is_grayscale_safe(["#000000", "#ffffff"]) is True

    def test_identical_colors_are_not_safe(self) -> None:
        """
        Description: Identical colours have zero delta and must fail.
        Scenario: is_grayscale_safe(['#ff0000', '#ff0000']).
        Expectation: False.
        """
        assert is_grayscale_safe(["#ff0000", "#ff0000"]) is False

    def test_threshold_boundary_exact_match(self) -> None:
        """
        Description: Delta exactly equal to threshold must pass (>=).
        Scenario: Colours with known delta; threshold set to that delta.
        Expectation: True.
        """
        pairs = luminance_delta(["#000000", "#333333"])
        delta = pairs[0][2]
        assert is_grayscale_safe(["#000000", "#333333"], threshold=delta) is True

    def test_threshold_boundary_just_below(self) -> None:
        """
        Description: Delta just below threshold must fail.
        Scenario: Threshold slightly above actual delta.
        Expectation: False.
        """
        pairs = luminance_delta(["#000000", "#333333"])
        delta = pairs[0][2]
        assert is_grayscale_safe(["#000000", "#333333"], threshold=delta + 0.01) is False

    def test_empty_list_is_safe(self) -> None:
        """
        Description: Empty palette is trivially safe.
        Scenario: is_grayscale_safe([]).
        Expectation: True.
        """
        assert is_grayscale_safe([]) is True

    def test_single_color_is_safe(self) -> None:
        """
        Description: Single colour is trivially safe.
        Scenario: is_grayscale_safe(['#ff0000']).
        Expectation: True.
        """
        assert is_grayscale_safe(["#ff0000"]) is True

    def test_threshold_zero_always_safe(self) -> None:
        """
        Description: Threshold 0.0 means any delta passes (except identical).
        Scenario: Similar colours with threshold=0.0.
        Expectation: True (delta >= 0.0 for any pair with nonzero difference).
        """
        assert is_grayscale_safe(["#000000", "#010101"], threshold=0.0) is True

    def test_threshold_one_requires_black_and_white(self) -> None:
        """
        Description: Threshold 1.0 requires maximum contrast.
        Scenario: Non-extreme colours.
        Expectation: False for typical palettes.
        """
        assert is_grayscale_safe(["#ff0000", "#0000ff"], threshold=1.0) is False

    def test_threshold_negative_raises_value_error(self) -> None:
        """
        Description: Negative threshold must raise ValueError.
        Scenario: threshold=-0.1.
        Expectation: ValueError.
        """
        with pytest.raises(ValueError, match="threshold"):
            is_grayscale_safe(["#000000", "#ffffff"], threshold=-0.1)

    def test_threshold_above_one_raises_value_error(self) -> None:
        """
        Description: Threshold > 1.0 must raise ValueError.
        Scenario: threshold=1.5.
        Expectation: ValueError.
        """
        with pytest.raises(ValueError, match="threshold"):
            is_grayscale_safe(["#000000", "#ffffff"], threshold=1.5)

    def test_default_threshold_is_0_1(self) -> None:
        """
        Description: Default threshold must be 0.1.
        Scenario: Similar colours that differ by less than 0.1 luminance.
        Expectation: is_grayscale_safe returns False.
        """
        # Two very similar greys; difference < 0.1
        assert is_grayscale_safe(["#808080", "#858585"]) is False

    def test_safe_grayscale_palette_is_safe(self) -> None:
        """
        Description: The built-in safe_grayscale palette must pass the default check.
        Scenario: Load safe_grayscale colours and check.
        Expectation: True.
        """
        from plotstyle.color.palettes import load_palette

        colors = load_palette("safe_grayscale")
        assert is_grayscale_safe(colors) is True

    @pytest.mark.parametrize("threshold", [0.0, 0.05, 0.1, 0.5, 1.0])
    def test_threshold_boundary_values_accepted(self, threshold: float) -> None:
        """
        Description: All valid threshold boundary values must be accepted.
        Scenario: is_grayscale_safe with boundary threshold values.
        Expectation: No ValueError.
        """
        # Should not raise
        is_grayscale_safe(["#000000", "#ffffff"], threshold=threshold)


# ---------------------------------------------------------------------------
# preview_grayscale
# ---------------------------------------------------------------------------


class TestPreviewGrayscale:
    """Validate the grayscale preview figure generation."""

    def test_returns_new_figure(self, simple_fig: plt.Figure) -> None:
        """
        Description: preview_grayscale must return a new Figure.
        Scenario: Call with simple figure.
        Expectation: Different object returned.
        """
        comp = preview_grayscale(simple_fig)
        assert isinstance(comp, plt.Figure)
        assert comp is not simple_fig

    def test_has_two_panels(self, simple_fig: plt.Figure) -> None:
        """
        Description: Comparison figure must have exactly 2 axes.
        Scenario: preview_grayscale(fig).
        Expectation: 2 axes.
        """
        comp = preview_grayscale(simple_fig)
        assert len(comp.get_axes()) == 2

    def test_first_panel_titled_original(self, simple_fig: plt.Figure) -> None:
        """
        Description: First panel must be titled 'Original'.
        Scenario: Inspect axes[0] title.
        Expectation: 'Original'.
        """
        comp = preview_grayscale(simple_fig)
        assert comp.get_axes()[0].get_title() == "Original"

    def test_second_panel_titled_grayscale(self, simple_fig: plt.Figure) -> None:
        """
        Description: Second panel must be titled 'Grayscale'.
        Scenario: Inspect axes[1] title.
        Expectation: 'Grayscale'.
        """
        comp = preview_grayscale(simple_fig)
        assert comp.get_axes()[1].get_title() == "Grayscale"

    def test_source_figure_not_modified(self, simple_fig: plt.Figure) -> None:
        """
        Description: Source figure must not be altered.
        Scenario: Count axes before and after.
        Expectation: Same count.
        """
        n_axes = len(simple_fig.get_axes())
        preview_grayscale(simple_fig)
        assert len(simple_fig.get_axes()) == n_axes

    def test_axes_turned_off(self, simple_fig: plt.Figure) -> None:
        """
        Description: Both axes must have ticks disabled for clean preview.
        Scenario: Check axis visibility.
        Expectation: axison is False for both panels.
        """
        comp = preview_grayscale(simple_fig)
        for ax in comp.get_axes():
            assert not ax.axison

    def test_empty_figure(self) -> None:
        """
        Description: An empty figure (no artists) must still produce a valid preview.
        Scenario: plt.figure() with no content.
        Expectation: No exception; 2 panels returned.
        """
        fig = plt.figure(figsize=(2, 2), dpi=72)
        comp = preview_grayscale(fig)
        assert len(comp.get_axes()) == 2

    def test_figure_with_multiple_axes(self) -> None:
        """
        Description: A figure with multiple subplots must still preview correctly.
        Scenario: 2x2 subplots figure.
        Expectation: Preview has 2 panels.
        """
        fig, axes = plt.subplots(2, 2, figsize=(4, 4), dpi=72)
        for ax in axes.flat:
            ax.plot([0, 1], [0, 1])
        comp = preview_grayscale(fig)
        assert len(comp.get_axes()) == 2
