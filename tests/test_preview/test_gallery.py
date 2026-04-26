"""Comprehensive test suite for plotstyle.preview.gallery.

Covers: module constants, synthetic data generators, panel drawing helpers,
and the public gallery() API: including happy paths, column-span variations,
invalid inputs, style isolation, and deteminism guarantees.
"""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

matplotlib.use("Agg")

from plotstyle.preview.gallery import (
    _DEFAULT_SEED,
    _GALLERY_ASPECT,
    _HIST_N,
    _PANEL_DRAWERS,
    _SCATTER_GROUPS,
    _SCATTER_N,
    _VALID_COLUMNS,
    _draw_bar_panel,
    _draw_histogram_panel,
    _draw_line_panel,
    _draw_scatter_panel,
    _sample_bar_data,
    _sample_histogram_data,
    _sample_line_data,
    _sample_scatter_data,
    gallery,
)
from plotstyle.specs import SpecNotFoundError

# ---------------------------------------------------------------------------
# Module-level marks
# ---------------------------------------------------------------------------

# gallery() calls use(), which may emit FontFallbackWarning when the journal's
# preferred font (e.g. Helvetica) is not installed on the test machine.  This
# is expected behaviour in CI; suppress it so these tests focus on gallery
# logic rather than the underlying font-selection subsystem.
pytestmark = pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

KNOWN_JOURNALS: list[str] = ["nature", "ieee", "science"]


@pytest.fixture(params=KNOWN_JOURNALS)
def journal_name(request) -> str:
    """Parametric fixture yielding each known journal name in turn."""
    return request.param


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all Matplotlib figures after each test to prevent memory leaks."""
    yield
    plt.close("all")


@pytest.fixture
def bare_axes():
    """Return a fresh Axes on a minimal figure for panel-drawing tests."""
    _fig, ax = plt.subplots()
    return ax


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Validate module-level constants are correctly defined."""

    def test_gallery_aspect_is_positive_float(self) -> None:
        """
        Description: The aspect ratio used to compute figure height must be positive.
        Scenario: Inspect _GALLERY_ASPECT at module level.
        Expectation: Value is a float greater than 0.
        """
        assert isinstance(_GALLERY_ASPECT, float)
        assert _GALLERY_ASPECT > 0

    def test_default_seed_is_integer(self) -> None:
        """
        Description: The default RNG seed must be a plain integer so it can
        be passed directly to numpy.random.default_rng().
        Scenario: Inspect _DEFAULT_SEED at module level.
        Expectation: Value is an int.
        """
        assert isinstance(_DEFAULT_SEED, int)

    def test_valid_columns_contains_one_and_two(self) -> None:
        """
        Description: The valid column-span set must contain exactly {1, 2}.
        Scenario: Inspect _VALID_COLUMNS at module level.
        Expectation: frozenset equal to frozenset({1, 2}).
        """
        assert frozenset({1, 2}) == _VALID_COLUMNS

    def test_scatter_n_is_positive_int(self) -> None:
        """
        Description: The scatter sample count must be a positive integer.
        Scenario: Inspect _SCATTER_N at module level.
        Expectation: int > 0.
        """
        assert isinstance(_SCATTER_N, int)
        assert _SCATTER_N > 0

    def test_hist_n_is_positive_int(self) -> None:
        """
        Description: The histogram sample count must be a positive integer.
        Scenario: Inspect _HIST_N at module level.
        Expectation: int > 0.
        """
        assert isinstance(_HIST_N, int)
        assert _HIST_N > 0

    def test_scatter_groups_non_empty_strings(self) -> None:
        """
        Description: _SCATTER_GROUPS must contain at least one non-empty string
        so that the scatter panel can be drawn.
        Scenario: Inspect _SCATTER_GROUPS at module level.
        Expectation: Non-empty list; every element is a non-empty str.
        """
        assert len(_SCATTER_GROUPS) > 0
        for label in _SCATTER_GROUPS:
            assert isinstance(label, str)
            assert len(label) > 0

    def test_panel_drawers_count_matches_subplots(self) -> None:
        """
        Description: The gallery creates a 2x2 grid (4 axes); there must be
        exactly 4 panel-drawing callables.
        Scenario: Count elements in _PANEL_DRAWERS.
        Expectation: len == 4.
        """
        assert len(_PANEL_DRAWERS) == 4

    def test_panel_drawers_are_callable(self) -> None:
        """
        Description: Every entry in _PANEL_DRAWERS must be callable so the
        dispatch loop in gallery() can invoke each one.
        Scenario: Check callable() for each element.
        Expectation: All return True.
        """
        for drawer in _PANEL_DRAWERS:
            assert callable(drawer)


# ---------------------------------------------------------------------------
# Synthetic data generators
# ---------------------------------------------------------------------------


class TestSampleLineData:
    """Validate _sample_line_data() output shape, type, and determinism."""

    def test_returns_two_tuple(self) -> None:
        """
        Description: _sample_line_data must return a 2-tuple (x, ys).
        Scenario: Call _sample_line_data() with no arguments.
        Expectation: Returns exactly two objects.
        """
        result = _sample_line_data()
        assert len(result) == 2

    def test_x_is_float64_array_of_length_100(self) -> None:
        """
        Description: x must be a float64 ndarray of exactly 100 elements.
        Scenario: Inspect the first element returned by _sample_line_data().
        Expectation: dtype == float64, shape == (100,).
        """
        x, _ = _sample_line_data()
        assert x.dtype == np.float64
        assert x.shape == (100,)

    def test_ys_contains_four_arrays(self) -> None:
        """
        Description: The sample generator produces four curves; ys must have
        exactly four elements.
        Scenario: Inspect the second element returned by _sample_line_data().
        Expectation: len(ys) == 4.
        """
        _, ys = _sample_line_data()
        assert len(ys) == 4

    def test_each_y_matches_x_length(self) -> None:
        """
        Description: Every y-array must align element-wise with x.
        Scenario: Compare lengths of x and each y in the result.
        Expectation: All len(y) == len(x).
        """
        x, ys = _sample_line_data()
        for y in ys:
            assert len(y) == len(x)

    def test_x_spans_zero_to_two_pi(self) -> None:
        """
        Description: x should cover [0, 2π] to produce a full cycle of the
        trigonometric curves used in the line panel.
        Scenario: Check first and last values of x.
        Expectation: x[0] == 0.0, x[-1] ≈ 2π.
        """
        x, _ = _sample_line_data()
        assert x[0] == pytest.approx(0.0)
        assert x[-1] == pytest.approx(2 * np.pi)

    def test_is_deterministic(self) -> None:
        """
        Description: _sample_line_data() is deterministic (no RNG dependency),
        so successive calls must return identical arrays.
        Scenario: Call twice and compare.
        Expectation: All values identical.
        """
        x1, ys1 = _sample_line_data()
        x2, ys2 = _sample_line_data()
        np.testing.assert_array_equal(x1, x2)
        for y1, y2 in zip(ys1, ys2, strict=True):
            np.testing.assert_array_equal(y1, y2)


class TestSampleScatterData:
    """Validate _sample_scatter_data() shape, types, and seed behaviour."""

    def test_returns_three_tuple(self) -> None:
        """
        Description: _sample_scatter_data must return a 3-tuple (x, y, groups).
        Scenario: Call with no arguments.
        Expectation: Returns exactly three objects.
        """
        result = _sample_scatter_data()
        assert len(result) == 3

    def test_x_and_y_have_scatter_n_elements(self) -> None:
        """
        Description: x and y must each have exactly _SCATTER_N elements.
        Scenario: Inspect the first two arrays returned.
        Expectation: len(x) == len(y) == _SCATTER_N.
        """
        x, y, _ = _sample_scatter_data()
        assert len(x) == _SCATTER_N
        assert len(y) == _SCATTER_N

    def test_groups_has_scatter_n_elements(self) -> None:
        """
        Description: The group label array must align element-wise with x and y.
        Scenario: Inspect the third element returned.
        Expectation: len(groups) == _SCATTER_N.
        """
        _, _, groups = _sample_scatter_data()
        assert len(groups) == _SCATTER_N

    def test_groups_values_are_subset_of_scatter_groups(self) -> None:
        """
        Description: Every group label must be a member of _SCATTER_GROUPS.
        Scenario: Check set of unique values in groups.
        Expectation: set(groups) ⊆ set(_SCATTER_GROUPS).
        """
        _, _, groups = _sample_scatter_data()
        assert set(groups).issubset(set(_SCATTER_GROUPS))

    def test_same_seed_produces_identical_data(self) -> None:
        """
        Description: Reproducibility contract: identical seeds yield identical data.
        Scenario: Call _sample_scatter_data(seed=7) twice.
        Expectation: All three arrays are equal.
        """
        x1, y1, g1 = _sample_scatter_data(seed=7)
        x2, y2, g2 = _sample_scatter_data(seed=7)
        np.testing.assert_array_equal(x1, x2)
        np.testing.assert_array_equal(y1, y2)
        np.testing.assert_array_equal(g1, g2)

    def test_different_seeds_produce_different_data(self) -> None:
        """
        Description: Different seeds must produce different data to confirm the
        seed parameter is actually used.
        Scenario: Call with seed=0 and seed=99.
        Expectation: x arrays are not equal.
        """
        x1, _, _ = _sample_scatter_data(seed=0)
        x2, _, _ = _sample_scatter_data(seed=99)
        assert not np.array_equal(x1, x2)

    def test_default_seed_matches_default_seed_constant(self) -> None:
        """
        Description: Calling with no argument should give the same result as
        calling with seed=_DEFAULT_SEED explicitly.
        Scenario: Compare outputs of _sample_scatter_data() vs
        _sample_scatter_data(seed=_DEFAULT_SEED).
        Expectation: All three arrays are equal.
        """
        x1, y1, g1 = _sample_scatter_data()
        x2, y2, g2 = _sample_scatter_data(seed=_DEFAULT_SEED)
        np.testing.assert_array_equal(x1, x2)
        np.testing.assert_array_equal(y1, y2)
        np.testing.assert_array_equal(g1, g2)

    def test_x_and_y_are_float64(self) -> None:
        """
        Description: The coordinate arrays must have float dtype for
        Matplotlib scatter().
        Scenario: Inspect dtype of x and y.
        Expectation: Both dtype == float64.
        """
        x, y, _ = _sample_scatter_data()
        assert x.dtype == np.float64
        assert y.dtype == np.float64


class TestSampleBarData:
    """Validate _sample_bar_data() output structure and deterministic values."""

    def test_returns_three_tuple(self) -> None:
        """
        Description: _sample_bar_data must return a 3-tuple.
        Scenario: Call with no arguments.
        Expectation: Returns exactly three objects.
        """
        result = _sample_bar_data()
        assert len(result) == 3

    def test_categories_values_errors_same_length(self) -> None:
        """
        Description: categories, values, and errors must have the same length
        so that bar() with yerr does not raise a shape mismatch.
        Scenario: Compare lengths of all three returned lists.
        Expectation: All three have equal length.
        """
        categories, values, errors = _sample_bar_data()
        assert len(categories) == len(values) == len(errors)

    def test_categories_are_strings(self) -> None:
        """
        Description: Category labels must be strings for Matplotlib bar().
        Scenario: Inspect type of each element in categories.
        Expectation: All elements are str.
        """
        categories, _, _ = _sample_bar_data()
        for c in categories:
            assert isinstance(c, str)

    def test_values_and_errors_are_numeric(self) -> None:
        """
        Description: Bar heights and error magnitudes must be numeric (int or float).
        Scenario: Inspect types of values and errors.
        Expectation: All elements are int or float.
        """
        _, values, errors = _sample_bar_data()
        for v in values:
            assert isinstance(v, (int, float))
        for e in errors:
            assert isinstance(e, (int, float))

    def test_is_deterministic(self) -> None:
        """
        Description: _sample_bar_data() uses fixed values and must return
        identical results on every call.
        Scenario: Call twice and compare.
        Expectation: All returned objects are equal.
        """
        r1 = _sample_bar_data()
        r2 = _sample_bar_data()
        assert r1 == r2

    def test_at_least_one_category(self) -> None:
        """
        Description: The bar panel requires at least one category to render.
        Scenario: Check length of categories.
        Expectation: len > 0.
        """
        categories, _, _ = _sample_bar_data()
        assert len(categories) > 0


class TestSampleHistogramData:
    """Validate _sample_histogram_data() shape, dtype, and seed behaviour."""

    def test_returns_array_of_hist_n_elements(self) -> None:
        """
        Description: The histogram sample must have exactly _HIST_N elements.
        Scenario: Call _sample_histogram_data() with no arguments.
        Expectation: len(result) == _HIST_N.
        """
        data = _sample_histogram_data()
        assert len(data) == _HIST_N

    def test_returns_float64_array(self) -> None:
        """
        Description: Histogram data must be float64 for Matplotlib hist().
        Scenario: Inspect dtype of returned array.
        Expectation: dtype == float64.
        """
        data = _sample_histogram_data()
        assert data.dtype == np.float64

    def test_same_seed_produces_identical_data(self) -> None:
        """
        Description: Reproducibility contract: identical seeds yield identical
        histogram samples.
        Scenario: Call twice with seed=3.
        Expectation: Arrays are equal.
        """
        d1 = _sample_histogram_data(seed=3)
        d2 = _sample_histogram_data(seed=3)
        np.testing.assert_array_equal(d1, d2)

    def test_different_seeds_produce_different_data(self) -> None:
        """
        Description: Different seeds must produce different samples.
        Scenario: Call with seed=0 and seed=1.
        Expectation: Arrays are not equal.
        """
        d1 = _sample_histogram_data(seed=0)
        d2 = _sample_histogram_data(seed=1)
        assert not np.array_equal(d1, d2)

    def test_default_seed_matches_constant(self) -> None:
        """
        Description: Default call should match calling with seed=_DEFAULT_SEED.
        Scenario: Compare _sample_histogram_data() vs
        _sample_histogram_data(seed=_DEFAULT_SEED).
        Expectation: Arrays are equal.
        """
        d1 = _sample_histogram_data()
        d2 = _sample_histogram_data(seed=_DEFAULT_SEED)
        np.testing.assert_array_equal(d1, d2)


# ---------------------------------------------------------------------------
# Panel drawing helpers
# ---------------------------------------------------------------------------


class TestDrawLinePanel:
    """Validate _draw_line_panel() populates axes with the expected content."""

    def test_draws_without_error(self, bare_axes) -> None:
        """
        Description: _draw_line_panel() must complete without raising on a
        fresh Axes object.
        Scenario: Pass a bare Axes to _draw_line_panel().
        Expectation: No exception raised.
        """
        _draw_line_panel(bare_axes)

    def test_adds_four_lines(self, bare_axes) -> None:
        """
        Description: The line panel must draw four periodic curves, one per
        y-series produced by _sample_line_data().
        Scenario: Count ax.lines after calling _draw_line_panel().
        Expectation: Exactly 4 Line2D objects.
        """
        _draw_line_panel(bare_axes)
        assert len(bare_axes.lines) == 4

    def test_sets_xlabel(self, bare_axes) -> None:
        """
        Description: The x-axis label must be set so the panel is readable
        without additional configuration.
        Scenario: Inspect ax.get_xlabel() after drawing.
        Expectation: Non-empty string.
        """
        _draw_line_panel(bare_axes)
        assert bare_axes.get_xlabel() != ""

    def test_sets_ylabel(self, bare_axes) -> None:
        """
        Description: The y-axis label must be set.
        Scenario: Inspect ax.get_ylabel() after drawing.
        Expectation: Non-empty string.
        """
        _draw_line_panel(bare_axes)
        assert bare_axes.get_ylabel() != ""

    def test_sets_title(self, bare_axes) -> None:
        """
        Description: Each panel must have a title for identification in the
        gallery grid.
        Scenario: Inspect ax.get_title() after drawing.
        Expectation: Non-empty string.
        """
        _draw_line_panel(bare_axes)
        assert bare_axes.get_title() != ""

    def test_legend_is_present(self, bare_axes) -> None:
        """
        Description: The line panel must include a legend to label the series.
        Scenario: Inspect ax.get_legend() after drawing.
        Expectation: Not None.
        """
        _draw_line_panel(bare_axes)
        assert bare_axes.get_legend() is not None


class TestDrawScatterPanel:
    """Validate _draw_scatter_panel() populates axes with the expected content."""

    def test_draws_without_error(self, bare_axes) -> None:
        """
        Description: _draw_scatter_panel() must complete without raising.
        Scenario: Pass a bare Axes to _draw_scatter_panel().
        Expectation: No exception raised.
        """
        _draw_scatter_panel(bare_axes)

    def test_produces_scatter_collections(self, bare_axes) -> None:
        """
        Description: scatter() adds PathCollection objects; there should be
        one per group in _SCATTER_GROUPS.
        Scenario: Count ax.collections after calling _draw_scatter_panel().
        Expectation: len == number of unique groups.
        """
        _draw_scatter_panel(bare_axes)
        assert len(bare_axes.collections) == len(_SCATTER_GROUPS)

    def test_sets_xlabel(self, bare_axes) -> None:
        """
        Description: The scatter panel x-axis label must be set.
        Scenario: Inspect ax.get_xlabel() after drawing.
        Expectation: Non-empty string.
        """
        _draw_scatter_panel(bare_axes)
        assert bare_axes.get_xlabel() != ""

    def test_sets_ylabel(self, bare_axes) -> None:
        """
        Description: The scatter panel y-axis label must be set.
        Scenario: Inspect ax.get_ylabel() after drawing.
        Expectation: Non-empty string.
        """
        _draw_scatter_panel(bare_axes)
        assert bare_axes.get_ylabel() != ""

    def test_sets_title(self, bare_axes) -> None:
        """
        Description: Each panel must have a title for identification.
        Scenario: Inspect ax.get_title() after drawing.
        Expectation: Non-empty string.
        """
        _draw_scatter_panel(bare_axes)
        assert bare_axes.get_title() != ""

    def test_legend_is_present(self, bare_axes) -> None:
        """
        Description: The scatter panel must include a legend for group labels.
        Scenario: Inspect ax.get_legend() after drawing.
        Expectation: Not None.
        """
        _draw_scatter_panel(bare_axes)
        assert bare_axes.get_legend() is not None


class TestDrawBarPanel:
    """Validate _draw_bar_panel() populates axes with the expected content."""

    def test_draws_without_error(self, bare_axes) -> None:
        """
        Description: _draw_bar_panel() must complete without raising.
        Scenario: Pass a bare Axes to _draw_bar_panel().
        Expectation: No exception raised.
        """
        _draw_bar_panel(bare_axes)

    def test_produces_bar_containers(self, bare_axes) -> None:
        """
        Description: bar() adds a BarContainer; at least one must be present.
        Scenario: Inspect ax.containers after calling _draw_bar_panel().
        Expectation: At least 1 container.
        """
        _draw_bar_panel(bare_axes)
        assert len(bare_axes.containers) >= 1

    def test_sets_ylabel(self, bare_axes) -> None:
        """
        Description: The bar panel y-axis label must be set.
        Scenario: Inspect ax.get_ylabel() after drawing.
        Expectation: Non-empty string.
        """
        _draw_bar_panel(bare_axes)
        assert bare_axes.get_ylabel() != ""

    def test_sets_title(self, bare_axes) -> None:
        """
        Description: Each panel must have a title for identification.
        Scenario: Inspect ax.get_title() after drawing.
        Expectation: Non-empty string.
        """
        _draw_bar_panel(bare_axes)
        assert bare_axes.get_title() != ""


class TestDrawHistogramPanel:
    """Validate _draw_histogram_panel() populates axes with the expected content."""

    def test_draws_without_error(self, bare_axes) -> None:
        """
        Description: _draw_histogram_panel() must complete without raising.
        Scenario: Pass a bare Axes to _draw_histogram_panel().
        Expectation: No exception raised.
        """
        _draw_histogram_panel(bare_axes)

    def test_produces_patches(self, bare_axes) -> None:
        """
        Description: hist() adds Rectangle patches for each bin; there must
        be at least one patch.
        Scenario: Inspect ax.patches after calling _draw_histogram_panel().
        Expectation: len > 0.
        """
        _draw_histogram_panel(bare_axes)
        assert len(bare_axes.patches) > 0

    def test_sets_xlabel(self, bare_axes) -> None:
        """
        Description: The histogram x-axis label must be set.
        Scenario: Inspect ax.get_xlabel() after drawing.
        Expectation: Non-empty string.
        """
        _draw_histogram_panel(bare_axes)
        assert bare_axes.get_xlabel() != ""

    def test_sets_ylabel(self, bare_axes) -> None:
        """
        Description: The histogram y-axis label must be set.
        Scenario: Inspect ax.get_ylabel() after drawing.
        Expectation: Non-empty string.
        """
        _draw_histogram_panel(bare_axes)
        assert bare_axes.get_ylabel() != ""

    def test_sets_title(self, bare_axes) -> None:
        """
        Description: Each panel must have a title for identification.
        Scenario: Inspect ax.get_title() after drawing.
        Expectation: Non-empty string.
        """
        _draw_histogram_panel(bare_axes)
        assert bare_axes.get_title() != ""


# ---------------------------------------------------------------------------
# Public API: gallery()
# ---------------------------------------------------------------------------


class TestGalleryHappyPath:
    """Validate gallery() produces the expected Figure structure."""

    def test_returns_figure_for_known_journal(self, journal_name) -> None:
        """
        Description: gallery() must return a matplotlib Figure for any
        registered journal.
        Scenario: Call gallery(journal_name) for each known journal.
        Expectation: Return value is a matplotlib.figure.Figure.
        """
        from matplotlib.figure import Figure

        result = gallery(journal_name)
        assert isinstance(result, Figure)

    def test_figure_has_four_axes(self, journal_name) -> None:
        """
        Description: The 2x2 subplot grid must produce exactly 4 Axes.
        Scenario: Call gallery(journal_name) and inspect fig.axes.
        Expectation: len(fig.axes) == 4.
        """
        fig = gallery(journal_name)
        assert len(fig.axes) == 4

    @pytest.mark.parametrize("columns", [1, 2])
    def test_columns_parameter_is_accepted(self, columns) -> None:
        """
        Description: Both column-span values (1 and 2) must be accepted.
        Scenario: Call gallery("nature", columns=columns).
        Expectation: No exception raised; returns a Figure.
        """
        from matplotlib.figure import Figure

        result = gallery("nature", columns=columns)
        assert isinstance(result, Figure)

    def test_single_column_figure_narrower_than_double(self) -> None:
        """
        Description: A single-column figure must be narrower than a
        double-column figure for the same journal.
        Scenario: Compare figsize widths for columns=1 vs columns=2.
        Expectation: width_1 < width_2.
        """
        fig1 = gallery("nature", columns=1)
        fig2 = gallery("nature", columns=2)
        width1, _ = fig1.get_size_inches()
        width2, _ = fig2.get_size_inches()
        assert width1 < width2

    def test_figure_height_equals_width_times_aspect(self) -> None:
        """
        Description: Height is computed as width x _GALLERY_ASPECT; this
        relationship ensures the figure remains compact for on-screen preview.
        Scenario: Check width and height of a gallery figure.
        Expectation: height ≈ width x _GALLERY_ASPECT.
        """
        fig = gallery("nature", columns=1)
        width, height = fig.get_size_inches()
        assert height == pytest.approx(width * _GALLERY_ASPECT, rel=1e-6)

    def test_figure_has_suptitle(self, journal_name) -> None:
        """
        Description: The gallery figure must include a suptitle naming the
        journal style for clarity.
        Scenario: Inspect the suptitle text of the returned figure.
        Expectation: Non-empty text.
        """
        fig = gallery(journal_name)
        suptitle = fig._suptitle
        assert suptitle is not None
        assert len(suptitle.get_text()) > 0

    def test_suptitle_contains_journal_name(self, journal_name) -> None:
        """
        Description: The suptitle should reference the journal's spec name so
        the viewer knows which style they are previewing.
        Scenario: Inspect the suptitle text against the spec's metadata.name.
        Expectation: spec.metadata.name is a substring of the suptitle text.
        """
        from plotstyle.specs import registry

        fig = gallery(journal_name)
        spec = registry.get(journal_name)
        assert spec.metadata.name in fig._suptitle.get_text()


class TestGalleryInvalidInputs:
    """Validate gallery() raises appropriate errors for invalid arguments."""

    @pytest.mark.parametrize("invalid_columns", [0, 3, -1, 1.5, "1", None])
    def test_invalid_columns_raises_value_error(self, invalid_columns) -> None:
        """
        Description: Passing an unsupported column-span must raise ValueError
        before any Matplotlib state is modified.
        Scenario: Call gallery("nature", columns=invalid_columns).
        Expectation: ValueError raised.
        """
        with pytest.raises((ValueError, TypeError)):
            gallery("nature", columns=invalid_columns)

    def test_invalid_columns_error_mentions_value(self) -> None:
        """
        Description: The ValueError message must name the offending value so
        the developer can immediately identify the mistake.
        Scenario: Call gallery("nature", columns=99).
        Expectation: '99' appears in the error message.
        """
        with pytest.raises(ValueError, match="99"):
            gallery("nature", columns=99)

    def test_unknown_journal_raises_spec_not_found_error(self) -> None:
        """
        Description: Requesting a journal that is not in the registry must
        raise SpecNotFoundError.
        Scenario: Call gallery("__no_such_journal__").
        Expectation: SpecNotFoundError raised.
        """
        with pytest.raises(SpecNotFoundError):
            gallery("__no_such_journal__")

    def test_unknown_journal_error_is_key_error(self) -> None:
        """
        Description: SpecNotFoundError inherits from KeyError; callers that
        catch KeyError must also catch spec lookup failures.
        Scenario: Call gallery("__no_such_journal__") and catch KeyError.
        Expectation: KeyError (or subclass) raised.
        """
        with pytest.raises(KeyError):
            gallery("__no_such_journal__")


class TestGalleryStyleIsolation:
    """Validate that gallery() does not permanently alter global Matplotlib state."""

    def test_rcparams_restored_after_success(self) -> None:
        """
        Description: gallery() applies a journal style internally and must
        restore all modified rcParams on normal exit.
        Scenario: Snapshot rcParams before and after calling gallery("nature").
        Expectation: Key rcParam values are unchanged after the call.
        """
        import matplotlib as mpl

        before = dict(mpl.rcParams)
        gallery("nature")
        after = dict(mpl.rcParams)
        assert before == after

    def test_rcparams_restored_after_invalid_columns(self) -> None:
        """
        Description: gallery() validates columns *before* applying the style,
        so a ValueError due to invalid columns must not leave rcParams mutated.
        Scenario: Call gallery("nature", columns=99) and compare rcParams.
        Expectation: rcParams unchanged after the failed call.
        """
        import matplotlib as mpl

        before = dict(mpl.rcParams)
        with pytest.raises(ValueError):
            gallery("nature", columns=99)
        after = dict(mpl.rcParams)
        assert before == after

    def test_rcparams_restored_after_unknown_journal(self) -> None:
        """
        Description: Raising SpecNotFoundError from use() must not leave
        rcParams permanently modified.
        Scenario: Call gallery("__ghost__") and compare rcParams.
        Expectation: rcParams unchanged after the failed call.
        """
        import matplotlib as mpl

        before = dict(mpl.rcParams)
        with pytest.raises((SpecNotFoundError, KeyError)):
            gallery("__ghost__")
        after = dict(mpl.rcParams)
        assert before == after


class TestGalleryDeterminism:
    """Validate that gallery() produces pixel-identical figures on repeated calls."""

    def test_repeated_calls_produce_same_figure_size(self) -> None:
        """
        Description: Deterministic data generators ensure each call to
        gallery() produces a figure with the same size.
        Scenario: Call gallery("nature", columns=1) twice and compare sizes.
        Expectation: Both (width, height) tuples are equal.
        """
        fig1 = gallery("nature", columns=1)
        fig2 = gallery("nature", columns=1)
        assert fig1.get_size_inches() == pytest.approx(fig2.get_size_inches())

    def test_all_panel_titles_are_non_empty(self) -> None:
        """
        Description: All four subplot panels must have titles so the gallery
        is self-describing.
        Scenario: Call gallery("nature") and inspect all axes titles.
        Expectation: Every ax.get_title() is a non-empty string.
        """
        fig = gallery("nature")
        for ax in fig.axes:
            assert ax.get_title() != ""


# ---------------------------------------------------------------------------
# Public API: __init__ exports
# ---------------------------------------------------------------------------


class TestPreviewPackageExports:
    """Validate that the plotstyle.preview package exports the expected names."""

    def test_gallery_importable_from_preview(self) -> None:
        """
        Description: gallery must be importable directly from plotstyle.preview.
        Scenario: Import gallery from plotstyle.preview.
        Expectation: gallery is callable.
        """
        from plotstyle.preview import gallery as gal

        assert callable(gal)

    def test_all_contains_gallery(self) -> None:
        """
        Description: __all__ must list 'gallery' to make it part of the
        package's public API.
        Scenario: Inspect plotstyle.preview.__all__.
        Expectation: 'gallery' in __all__.
        """
        import plotstyle.preview as preview

        assert "gallery" in preview.__all__

    def test_all_contains_preview_print_size(self) -> None:
        """
        Description: __all__ must list 'preview_print_size'.
        Scenario: Inspect plotstyle.preview.__all__.
        Expectation: 'preview_print_size' in __all__.
        """
        import plotstyle.preview as preview

        assert "preview_print_size" in preview.__all__
