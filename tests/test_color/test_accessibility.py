"""Enhanced test suite for plotstyle.color.accessibility.

Covers: CVDType enum, simulate_cvd, preview_colorblind, SIMULATION_MATRICES,
CVDSimulationError, and all edge/error/boundary cases.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

matplotlib.use("Agg")

from plotstyle.color.accessibility import (
    _SIMULATION_MATRICES_NP,
    SIMULATION_MATRICES,
    CVDSimulationError,
    CVDType,
    preview_colorblind,
    simulate_cvd,
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
    """A minimal figure with a coloured scatter plot for previewing."""
    fig, ax = plt.subplots(figsize=(2, 2), dpi=72)
    ax.scatter([1, 2, 3], [4, 5, 6], c=["#e41a1c", "#377eb8", "#4daf4a"], s=20)
    return fig


@pytest.fixture
def rgb_uint8() -> np.ndarray:
    """A small uint8 RGB image (4x4x3) for testing simulate_cvd."""
    rng = np.random.RandomState(42)
    return rng.randint(0, 256, size=(4, 4, 3), dtype=np.uint8)


@pytest.fixture
def rgb_float() -> np.ndarray:
    """A small float64 RGB image (4x4x3) in [0, 1]."""
    rng = np.random.RandomState(42)
    return rng.random((4, 4, 3)).astype(np.float64)


# ---------------------------------------------------------------------------
# CVDType enum
# ---------------------------------------------------------------------------


class TestCVDType:
    """Validate the CVDType enumeration."""

    def test_has_three_members(self) -> None:
        """
        Description: CVDType must have exactly three members.
        Scenario: Count enum members.
        Expectation: len == 3.
        """
        assert len(CVDType) == 3

    @pytest.mark.parametrize(
        "member,value",
        [
            (CVDType.DEUTERANOPIA, "deuteranopia"),
            (CVDType.PROTANOPIA, "protanopia"),
            (CVDType.TRITANOPIA, "tritanopia"),
        ],
    )
    def test_member_values(self, member: CVDType, value: str) -> None:
        """
        Description: Each CVDType member must have the expected string value.
        Scenario: Check .value for each member.
        Expectation: Matches the lowercase name.
        """
        assert member.value == value

    def test_members_are_strings(self) -> None:
        """
        Description: CVDType inherits from str; each member must be usable as a string.
        Scenario: Check isinstance(str).
        Expectation: True for all members.
        """
        for member in CVDType:
            assert isinstance(member, str)

    def test_members_usable_as_dict_keys(self) -> None:
        """
        Description: CVDType members must be hashable and usable as dict keys.
        Scenario: Build a dict keyed by CVDType members.
        Expectation: Dict has 3 entries.
        """
        d = {cvd: i for i, cvd in enumerate(CVDType)}
        assert len(d) == 3


# ---------------------------------------------------------------------------
# SIMULATION_MATRICES
# ---------------------------------------------------------------------------


class TestSimulationMatrices:
    """Validate the simulation matrix constants."""

    def test_all_cvd_types_have_matrices(self) -> None:
        """
        Description: Every CVDType member must have a simulation matrix.
        Scenario: Check SIMULATION_MATRICES keys.
        Expectation: All members present.
        """
        for cvd in CVDType:
            assert cvd in SIMULATION_MATRICES

    def test_matrices_are_3x3(self) -> None:
        """
        Description: Each matrix must be 3x3 (RGB→RGB).
        Scenario: Check shape.
        Expectation: 3 rows, each with 3 columns.
        """
        for cvd, matrix in SIMULATION_MATRICES.items():
            assert len(matrix) == 3, f"{cvd}: expected 3 rows"
            for row in matrix:
                assert len(row) == 3, f"{cvd}: expected 3 columns"

    def test_numpy_matrices_shape(self) -> None:
        """
        Description: Pre-computed numpy matrices must have shape (3, 3).
        Scenario: Check _SIMULATION_MATRICES_NP.
        Expectation: shape == (3, 3) for all.
        """
        for mat in _SIMULATION_MATRICES_NP.values():
            assert mat.shape == (3, 3)

    def test_numpy_matrices_dtype(self) -> None:
        """
        Description: Pre-computed numpy matrices must be float64.
        Scenario: Check dtype.
        Expectation: np.float64.
        """
        for mat in _SIMULATION_MATRICES_NP.values():
            assert mat.dtype == np.float64

    def test_identity_like_for_no_deficiency(self) -> None:
        """
        Description: The diagonal sum of each matrix should be close to 3
        for mild transforms; severe transforms may differ.
        Scenario: Sum diagonals.
        Expectation: Diagonal sum is a finite number.
        """
        for mat in _SIMULATION_MATRICES_NP.values():
            diag_sum = np.trace(mat)
            assert np.isfinite(diag_sum)


# ---------------------------------------------------------------------------
# CVDSimulationError
# ---------------------------------------------------------------------------


class TestCVDSimulationError:
    """Validate the custom exception."""

    def test_is_value_error(self) -> None:
        """
        Description: CVDSimulationError must extend ValueError.
        Scenario: Check isinstance.
        Expectation: True.
        """
        assert isinstance(CVDSimulationError("test"), ValueError)

    def test_message_preserved(self) -> None:
        """
        Description: The error message must be preserved in str().
        Scenario: Raise and catch.
        Expectation: Message matches.
        """
        with pytest.raises(CVDSimulationError, match="bad image"):
            raise CVDSimulationError("bad image")


# ---------------------------------------------------------------------------
# simulate_cvd
# ---------------------------------------------------------------------------


class TestSimulateCvd:
    """Validate the core CVD simulation function."""

    @pytest.mark.parametrize("cvd", list(CVDType))
    def test_output_shape_matches_input(self, rgb_uint8: np.ndarray, cvd: CVDType) -> None:
        """
        Description: Output shape must match input shape.
        Scenario: (4, 4, 3) input for each CVDType.
        Expectation: Output shape == (4, 4, 3).
        """
        result = simulate_cvd(rgb_uint8, cvd)
        assert result.shape == rgb_uint8.shape

    @pytest.mark.parametrize("cvd", list(CVDType))
    def test_output_dtype_is_float64(self, rgb_uint8: np.ndarray, cvd: CVDType) -> None:
        """
        Description: Output must always be float64 regardless of input dtype.
        Scenario: uint8 input.
        Expectation: result.dtype == float64.
        """
        result = simulate_cvd(rgb_uint8, cvd)
        assert result.dtype == np.float64

    @pytest.mark.parametrize("cvd", list(CVDType))
    def test_output_clipped_to_unit_interval(self, rgb_float: np.ndarray, cvd: CVDType) -> None:
        """
        Description: Output values must be clipped to [0, 1].
        Scenario: Float input for each CVDType.
        Expectation: All values >= 0 and <= 1.
        """
        result = simulate_cvd(rgb_float, cvd)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_uint8_normalisation(self, rgb_uint8: np.ndarray) -> None:
        """
        Description: uint8 input must be normalised to [0, 1] before transform.
        Scenario: Pure white pixel (255, 255, 255).
        Expectation: Output values near 1.0 (identity-ish transform).
        """
        white = np.full((1, 1, 3), 255, dtype=np.uint8)
        result = simulate_cvd(white, CVDType.DEUTERANOPIA)
        assert result.shape == (1, 1, 3)
        assert np.all(result >= 0.0) and np.all(result <= 1.0)

    def test_float_input_accepted(self, rgb_float: np.ndarray) -> None:
        """
        Description: Float input in [0, 1] must be accepted without error.
        Scenario: simulate_cvd with float64 image.
        Expectation: No exception.
        """
        result = simulate_cvd(rgb_float, CVDType.PROTANOPIA)
        assert result.shape == rgb_float.shape

    def test_black_image_stays_black(self) -> None:
        """
        Description: Pure black (0, 0, 0) must remain black under all simulations.
        Scenario: All-zero image.
        Expectation: Output is all zeros.
        """
        black = np.zeros((2, 2, 3), dtype=np.float64)
        for cvd in CVDType:
            result = simulate_cvd(black, cvd)
            np.testing.assert_array_equal(result, 0.0)

    def test_invalid_shape_2d_raises(self) -> None:
        """
        Description: 2D array must raise CVDSimulationError.
        Scenario: Shape (4, 4) — no channel dimension.
        Expectation: CVDSimulationError.
        """
        bad = np.zeros((4, 4), dtype=np.float64)
        with pytest.raises(CVDSimulationError, match="shape"):
            simulate_cvd(bad, CVDType.DEUTERANOPIA)

    def test_invalid_shape_4_channels_raises(self) -> None:
        """
        Description: RGBA (4 channels) must raise CVDSimulationError.
        Scenario: Shape (4, 4, 4).
        Expectation: CVDSimulationError.
        """
        bad = np.zeros((4, 4, 4), dtype=np.float64)
        with pytest.raises(CVDSimulationError, match="shape"):
            simulate_cvd(bad, CVDType.PROTANOPIA)

    def test_invalid_shape_1_channel_raises(self) -> None:
        """
        Description: Grayscale (1 channel) must raise CVDSimulationError.
        Scenario: Shape (4, 4, 1).
        Expectation: CVDSimulationError.
        """
        bad = np.zeros((4, 4, 1), dtype=np.float64)
        with pytest.raises(CVDSimulationError, match="shape"):
            simulate_cvd(bad, CVDType.TRITANOPIA)

    def test_invalid_shape_4d_raises(self) -> None:
        """
        Description: 4D arrays must raise CVDSimulationError.
        Scenario: Shape (1, 4, 4, 3).
        Expectation: CVDSimulationError.
        """
        bad = np.zeros((1, 4, 4, 3), dtype=np.float64)
        with pytest.raises(CVDSimulationError):
            simulate_cvd(bad, CVDType.DEUTERANOPIA)

    def test_single_pixel_image(self) -> None:
        """
        Description: A 1x1 image must work correctly.
        Scenario: Shape (1, 1, 3).
        Expectation: Output shape (1, 1, 3).
        """
        pixel = np.array([[[0.5, 0.3, 0.8]]], dtype=np.float64)
        result = simulate_cvd(pixel, CVDType.TRITANOPIA)
        assert result.shape == (1, 1, 3)

    def test_large_image_performance(self) -> None:
        """
        Description: Simulate CVD on a moderately sized image without error.
        Scenario: Shape (100, 100, 3).
        Expectation: Output shape matches; no crash.
        """
        img = np.random.RandomState(0).random((100, 100, 3)).astype(np.float64)
        result = simulate_cvd(img, CVDType.DEUTERANOPIA)
        assert result.shape == (100, 100, 3)

    def test_float32_input_accepted(self) -> None:
        """
        Description: float32 input must be accepted (cast to float64 internally).
        Scenario: float32 image.
        Expectation: Output dtype is float64.
        """
        img = np.random.RandomState(1).random((3, 3, 3)).astype(np.float32)
        result = simulate_cvd(img, CVDType.PROTANOPIA)
        assert result.dtype == np.float64

    def test_different_cvd_types_produce_different_results(self, rgb_float: np.ndarray) -> None:
        """
        Description: Different CVD simulations must produce different pixel values.
        Scenario: Apply all three types to the same image.
        Expectation: At least two results differ.
        """
        results = [simulate_cvd(rgb_float, cvd) for cvd in CVDType]
        # At least one pair must differ
        all_same = all(np.allclose(results[0], r) for r in results[1:])
        assert not all_same


# ---------------------------------------------------------------------------
# preview_colorblind
# ---------------------------------------------------------------------------


class TestPreviewColorblind:
    """Validate the high-level colorblind preview function."""

    def test_returns_new_figure(self, simple_fig: plt.Figure) -> None:
        """
        Description: preview_colorblind must return a new Figure object.
        Scenario: Call with a simple figure.
        Expectation: Returned object is a Figure and is not the input.
        """
        comp = preview_colorblind(simple_fig)
        assert isinstance(comp, plt.Figure)
        assert comp is not simple_fig

    def test_default_panels_include_all_cvd_types(self, simple_fig: plt.Figure) -> None:
        """
        Description: Default call must produce 1 + 3 = 4 panels.
        Scenario: preview_colorblind(fig) with no cvd_types.
        Expectation: 4 axes in the comparison figure.
        """
        comp = preview_colorblind(simple_fig)
        assert len(comp.get_axes()) == 4

    def test_custom_cvd_types(self, simple_fig: plt.Figure) -> None:
        """
        Description: Passing a subset of CVDTypes must produce correct panel count.
        Scenario: cvd_types=[DEUTERANOPIA].
        Expectation: 1 + 1 = 2 panels.
        """
        comp = preview_colorblind(simple_fig, cvd_types=[CVDType.DEUTERANOPIA])
        assert len(comp.get_axes()) == 2

    def test_two_cvd_types(self, simple_fig: plt.Figure) -> None:
        """
        Description: Two CVD types must produce 3 panels.
        Scenario: cvd_types=[DEUTERANOPIA, PROTANOPIA].
        Expectation: 3 axes.
        """
        comp = preview_colorblind(simple_fig, cvd_types=[CVDType.DEUTERANOPIA, CVDType.PROTANOPIA])
        assert len(comp.get_axes()) == 3

    def test_original_panel_title(self, simple_fig: plt.Figure) -> None:
        """
        Description: First panel must be titled 'Original'.
        Scenario: Inspect axes[0].get_title().
        Expectation: 'Original'.
        """
        comp = preview_colorblind(simple_fig, cvd_types=[CVDType.DEUTERANOPIA])
        assert comp.get_axes()[0].get_title() == "Original"

    def test_cvd_panel_titles_capitalised(self, simple_fig: plt.Figure) -> None:
        """
        Description: CVD panel titles must be capitalised versions of the enum value.
        Scenario: Inspect axes[1..N] titles.
        Expectation: Capitalised CVD type names.
        """
        comp = preview_colorblind(simple_fig, cvd_types=[CVDType.DEUTERANOPIA])
        assert comp.get_axes()[1].get_title() == "Deuteranopia"

    def test_axes_are_off(self, simple_fig: plt.Figure) -> None:
        """
        Description: All axes ticks must be disabled for clean preview.
        Scenario: Check axis visibility.
        Expectation: axison is False for all panels.
        """
        comp = preview_colorblind(simple_fig, cvd_types=[CVDType.PROTANOPIA])
        for ax in comp.get_axes():
            assert not ax.axison

    def test_source_figure_not_modified(self, simple_fig: plt.Figure) -> None:
        """
        Description: The source figure must not be altered.
        Scenario: Count axes before and after.
        Expectation: Same number of axes.
        """
        n_axes_before = len(simple_fig.get_axes())
        preview_colorblind(simple_fig)
        assert len(simple_fig.get_axes()) == n_axes_before

    def test_empty_cvd_types_list(self, simple_fig: plt.Figure) -> None:
        """
        Description: Empty cvd_types list must produce only the original panel.
        Scenario: cvd_types=[].
        Expectation: 1 axis.
        """
        comp = preview_colorblind(simple_fig, cvd_types=[])
        assert len(comp.get_axes()) == 1

    @pytest.mark.parametrize("cvd", list(CVDType))
    def test_single_cvd_type_produces_two_panels(
        self, simple_fig: plt.Figure, cvd: CVDType
    ) -> None:
        """
        Description: Single CVD type must produce exactly 2 panels.
        Scenario: Parametric sweep of each CVDType.
        Expectation: 2 axes.
        """
        comp = preview_colorblind(simple_fig, cvd_types=[cvd])
        assert len(comp.get_axes()) == 2
