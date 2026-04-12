"""Enhanced test suite for plotstyle.color._rendering.

Covers: _fig_to_rgb_array rasterisation, output shape, dtype, writability,
alpha stripping, and edge/error cases.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

matplotlib.use("Agg")

from plotstyle.color._rendering import _fig_to_rgb_array

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
    """A minimal figure with a single line plot."""
    fig, ax = plt.subplots(figsize=(2, 2), dpi=72)
    ax.plot([0, 1], [0, 1], color="red")
    return fig


@pytest.fixture
def empty_fig() -> plt.Figure:
    """An empty figure with no artists."""
    return plt.figure(figsize=(2, 2), dpi=72)


# ---------------------------------------------------------------------------
# _fig_to_rgb_array
# ---------------------------------------------------------------------------


class TestFigToRgbArray:
    """Validate the internal rasterisation helper."""

    def test_returns_numpy_array(self, simple_fig: plt.Figure) -> None:
        """
        Description: Return type must be a NumPy ndarray.
        Scenario: Call with a simple figure.
        Expectation: isinstance(np.ndarray).
        """
        result = _fig_to_rgb_array(simple_fig)
        assert isinstance(result, np.ndarray)

    def test_output_dtype_is_uint8(self, simple_fig: plt.Figure) -> None:
        """
        Description: Output must be uint8 (standard pixel format).
        Scenario: Check dtype.
        Expectation: np.uint8.
        """
        result = _fig_to_rgb_array(simple_fig)
        assert result.dtype == np.uint8

    def test_output_is_3d_rgb(self, simple_fig: plt.Figure) -> None:
        """
        Description: Output must have exactly 3 dimensions (H, W, 3).
        Scenario: Check ndim and last dimension.
        Expectation: ndim == 3, shape[2] == 3.
        """
        result = _fig_to_rgb_array(simple_fig)
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_alpha_channel_stripped(self, simple_fig: plt.Figure) -> None:
        """
        Description: Output must have 3 channels (RGB), not 4 (RGBA).
        Scenario: Last dimension of shape.
        Expectation: shape[2] == 3 (not 4).
        """
        result = _fig_to_rgb_array(simple_fig)
        assert result.shape[2] == 3

    def test_output_shape_matches_figure_size(self, simple_fig: plt.Figure) -> None:
        """
        Description: Output pixel dimensions must match fig size x DPI.
        Scenario: 2x2 inch figure at 72 DPI -> 144x144.
        Expectation: Height and width are approximately 144.
        """
        result = _fig_to_rgb_array(simple_fig)
        expected_w = int(simple_fig.get_size_inches()[0] * simple_fig.dpi)
        expected_h = int(simple_fig.get_size_inches()[1] * simple_fig.dpi)
        assert result.shape[0] == expected_h
        assert result.shape[1] == expected_w

    def test_output_is_writeable(self, simple_fig: plt.Figure) -> None:
        """
        Description: Returned array must be writeable (a copy, not a view).
        Scenario: Check flags.writeable.
        Expectation: True.
        """
        result = _fig_to_rgb_array(simple_fig)
        assert result.flags.writeable

    def test_mutation_does_not_affect_canvas(self, simple_fig: plt.Figure) -> None:
        """
        Description: Mutating the returned array must not affect the figure canvas.
        Scenario: Get array, modify pixel, get array again.
        Expectation: Second array unaffected.
        """
        first = _fig_to_rgb_array(simple_fig)
        original_pixel = first[0, 0].copy()
        first[0, 0] = [255, 0, 0]
        second = _fig_to_rgb_array(simple_fig)
        np.testing.assert_array_equal(second[0, 0], original_pixel)

    def test_empty_figure_works(self, empty_fig: plt.Figure) -> None:
        """
        Description: An empty figure must still rasterise without error.
        Scenario: Figure with no artists.
        Expectation: Valid (H, W, 3) array.
        """
        result = _fig_to_rgb_array(empty_fig)
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_values_in_uint8_range(self, simple_fig: plt.Figure) -> None:
        """
        Description: All pixel values must be in [0, 255].
        Scenario: Check min and max.
        Expectation: 0 <= min and max <= 255.
        """
        result = _fig_to_rgb_array(simple_fig)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_non_trivial_pixels(self, simple_fig: plt.Figure) -> None:
        """
        Description: A figure with a coloured line should not produce all-white pixels.
        Scenario: Check for non-255 pixel values.
        Expectation: Not all pixels are white.
        """
        result = _fig_to_rgb_array(simple_fig)
        assert not np.all(result == 255)

    def test_different_dpi_changes_resolution(self) -> None:
        """
        Description: Higher DPI must produce a larger pixel array.
        Scenario: Same figure size at 72 vs 144 DPI.
        Expectation: 144 DPI produces ~4x pixels.
        """
        fig_lo, _ = plt.subplots(figsize=(2, 2), dpi=72)
        fig_hi, _ = plt.subplots(figsize=(2, 2), dpi=144)
        lo = _fig_to_rgb_array(fig_lo)
        hi = _fig_to_rgb_array(fig_hi)
        # Higher DPI should have more pixels in each dimension
        assert hi.shape[0] > lo.shape[0]
        assert hi.shape[1] > lo.shape[1]
        # Approximately 2x in each dimension
        assert hi.shape[0] == pytest.approx(lo.shape[0] * 2, abs=2)
        assert hi.shape[1] == pytest.approx(lo.shape[1] * 2, abs=2)

    def test_different_figure_sizes(self) -> None:
        """
        Description: Wider figure must produce a wider pixel array.
        Scenario: 4x2 vs 2x2 figures at same DPI.
        Expectation: Wide figure has ~2x width.
        """
        fig_wide, _ = plt.subplots(figsize=(4, 2), dpi=72)
        fig_sqr, _ = plt.subplots(figsize=(2, 2), dpi=72)
        wide = _fig_to_rgb_array(fig_wide)
        sqr = _fig_to_rgb_array(fig_sqr)
        assert wide.shape[1] == pytest.approx(sqr.shape[1] * 2, abs=2)
        assert wide.shape[0] == pytest.approx(sqr.shape[0], abs=2)

    def test_figure_with_text_renders(self) -> None:
        """
        Description: Figures with text artists must rasterise without error.
        Scenario: Figure with title and axis labels.
        Expectation: Valid array returned.
        """
        fig, ax = plt.subplots(figsize=(3, 3), dpi=72)
        ax.set_title("Test Title")
        ax.set_xlabel("X Label")
        ax.set_ylabel("Y Label")
        result = _fig_to_rgb_array(fig)
        assert result.ndim == 3

    def test_figure_with_multiple_subplots(self) -> None:
        """
        Description: Multi-subplot figures must rasterise correctly.
        Scenario: 2x2 subplots.
        Expectation: Valid array with expected dimensions.
        """
        fig, axes = plt.subplots(2, 2, figsize=(4, 4), dpi=72)
        for ax in axes.flat:
            ax.plot([0, 1], [0, 1])
        result = _fig_to_rgb_array(fig)
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_idempotent_calls(self, simple_fig: plt.Figure) -> None:
        """
        Description: Multiple calls on the same figure must return identical arrays.
        Scenario: Call twice.
        Expectation: Arrays are equal.
        """
        first = _fig_to_rgb_array(simple_fig)
        second = _fig_to_rgb_array(simple_fig)
        np.testing.assert_array_equal(first, second)
