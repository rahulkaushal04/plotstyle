"""Enhanced test suite for plotstyle.core.figure.

Covers: figure, subplots, _validate_columns, _resolve_width,
_format_panel_label, _compute_figsize, _add_panel_labels, and module constants.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pytest

from plotstyle.core.figure import (
    _GOLDEN_RATIO,
    _LABEL_X,
    _LABEL_Y,
    _VALID_COLUMNS,
    _compute_figsize,
    _format_panel_label,
    _resolve_width,
    _validate_columns,
    figure,
    subplots,
)
from plotstyle.specs import registry
from plotstyle.specs.units import Dimension

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


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Validate module-level constants are correctly defined."""

    def test_golden_ratio_value(self) -> None:
        """
        Description: The golden ratio constant must be approximately 1.618.
        Scenario: Compare _GOLDEN_RATIO to (1 + sqrt(5)) / 2.
        Expectation: Values match within float tolerance.
        """
        assert pytest.approx((1 + 5**0.5) / 2) == _GOLDEN_RATIO

    def test_valid_columns_contains_1_and_2(self) -> None:
        """
        Description: Only column spans 1 and 2 are supported.
        Scenario: Check _VALID_COLUMNS membership.
        Expectation: Contains exactly {1, 2}.
        """
        assert frozenset({1, 2}) == _VALID_COLUMNS

    def test_valid_columns_is_frozenset(self) -> None:
        """
        Description: Column set must be immutable.
        Scenario: Check type.
        Expectation: isinstance(frozenset) is True.
        """
        assert isinstance(_VALID_COLUMNS, frozenset)

    def test_label_x_is_negative(self) -> None:
        """
        Description: Panel labels are placed to the left of axes (negative x).
        Scenario: Check _LABEL_X sign.
        Expectation: _LABEL_X < 0.
        """
        assert _LABEL_X < 0

    def test_label_y_is_above_axes(self) -> None:
        """
        Description: Panel labels are placed above axes (y > 1 in axes coords).
        Scenario: Check _LABEL_Y value.
        Expectation: _LABEL_Y > 1.0.
        """
        assert _LABEL_Y > 1.0


# ---------------------------------------------------------------------------
# _validate_columns
# ---------------------------------------------------------------------------


class TestValidateColumns:
    """Validate the column-span validation helper."""

    @pytest.mark.parametrize("columns", [1, 2])
    def test_valid_columns_accepted(self, columns: int) -> None:
        """
        Description: Valid column values (1 and 2) must not raise.
        Scenario: Call _validate_columns with valid values.
        Expectation: No exception.
        """
        _validate_columns(columns)

    @pytest.mark.parametrize("columns", [0, -1, 3, 4, 10, 100])
    def test_invalid_columns_raises_value_error(self, columns: int) -> None:
        """
        Description: Invalid column values must raise ValueError.
        Scenario: Call _validate_columns with out-of-range values.
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_columns(columns)

    def test_error_message_contains_bad_value(self) -> None:
        """
        Description: The error message must include the invalid value.
        Scenario: Call _validate_columns(5).
        Expectation: '5' appears in the error message.
        """
        with pytest.raises(ValueError, match="5"):
            _validate_columns(5)


# ---------------------------------------------------------------------------
# _resolve_width
# ---------------------------------------------------------------------------


class TestResolveWidth:
    """Validate width resolution from journal specs."""

    def test_single_column_width_for_nature(self) -> None:
        """
        Description: Nature single-column width is 89mm; must convert to inches.
        Scenario: _resolve_width('nature', 1).
        Expectation: Matches Dimension(89, 'mm').to_inches().
        """
        expected = Dimension(89.0, "mm").to_inches()
        assert _resolve_width("nature", 1) == pytest.approx(expected)

    def test_double_column_width_for_nature(self) -> None:
        """
        Description: Nature double-column width is 183mm.
        Scenario: _resolve_width('nature', 2).
        Expectation: Matches Dimension(183, 'mm').to_inches().
        """
        expected = Dimension(183.0, "mm").to_inches()
        assert _resolve_width("nature", 2) == pytest.approx(expected)

    def test_unknown_journal_raises(self) -> None:
        """
        Description: Unknown journal names must raise SpecNotFoundError.
        Scenario: _resolve_width('nonexistent_xyz', 1).
        Expectation: KeyError (SpecNotFoundError) raised.
        """
        with pytest.raises(KeyError):
            _resolve_width("nonexistent_xyz", 1)

    def test_invalid_columns_raises(self) -> None:
        """
        Description: Invalid column value must raise ValueError.
        Scenario: _resolve_width('nature', 3).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _resolve_width("nature", 3)

    def test_returns_float(self) -> None:
        """
        Description: Width must be returned as a float (in inches).
        Scenario: _resolve_width('nature', 1).
        Expectation: isinstance(float) is True.
        """
        assert isinstance(_resolve_width("nature", 1), float)

    def test_width_is_positive(self, journal_name: str) -> None:
        """
        Description: Resolved width must always be positive.
        Scenario: Parametric check for each known journal.
        Expectation: Width > 0.
        """
        assert _resolve_width(journal_name, 1) > 0

    def test_double_column_wider_than_single(self, journal_name: str) -> None:
        """
        Description: Double-column width must exceed single-column width.
        Scenario: Compare widths for each journal.
        Expectation: double > single.
        """
        single = _resolve_width(journal_name, 1)
        double = _resolve_width(journal_name, 2)
        assert double > single


# ---------------------------------------------------------------------------
# _compute_figsize
# ---------------------------------------------------------------------------


class TestComputeFigsize:
    """Validate figure size computation from width and aspect ratio."""

    def test_golden_ratio_default(self) -> None:
        """
        Description: When aspect is None, the golden ratio should be used.
        Scenario: _compute_figsize(6.0, None).
        Expectation: height = 6.0 / _GOLDEN_RATIO.
        """
        w, h = _compute_figsize(6.0, None)
        assert w == pytest.approx(6.0)
        assert h == pytest.approx(6.0 / _GOLDEN_RATIO)

    def test_explicit_aspect_ratio(self) -> None:
        """
        Description: An explicit aspect ratio must override the golden ratio.
        Scenario: _compute_figsize(6.0, 2.0).
        Expectation: height = 6.0 / 2.0 = 3.0.
        """
        w, h = _compute_figsize(6.0, 2.0)
        assert w == pytest.approx(6.0)
        assert h == pytest.approx(3.0)

    def test_square_aspect(self) -> None:
        """
        Description: Aspect ratio of 1.0 produces a square figure.
        Scenario: _compute_figsize(5.0, 1.0).
        Expectation: width == height == 5.0.
        """
        w, h = _compute_figsize(5.0, 1.0)
        assert w == pytest.approx(h)

    def test_returns_tuple(self) -> None:
        """
        Description: Return type must be a tuple of two floats.
        Scenario: Call _compute_figsize.
        Expectation: Tuple of length 2.
        """
        result = _compute_figsize(6.0, None)
        assert isinstance(result, tuple)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# _format_panel_label
# ---------------------------------------------------------------------------


class TestFormatPanelLabel:
    """Validate panel label formatting across all supported case styles."""

    @pytest.fixture
    def _make_spec(self):
        """Factory returning a mock spec with the given panel_label_case."""
        from unittest.mock import MagicMock

        def _factory(case: str) -> MagicMock:
            spec = MagicMock()
            spec.typography.panel_label_case = case
            return spec

        return _factory

    def test_lower_case_index_0(self, _make_spec) -> None:
        """
        Description: 'lower' case at index 0 must produce 'a'.
        Scenario: _format_panel_label(0, spec) with case='lower'.
        Expectation: 'a'.
        """
        assert _format_panel_label(0, _make_spec("lower")) == "a"

    def test_lower_case_index_2(self, _make_spec) -> None:
        """
        Description: 'lower' case at index 2 must produce 'c'.
        Scenario: _format_panel_label(2, spec) with case='lower'.
        Expectation: 'c'.
        """
        assert _format_panel_label(2, _make_spec("lower")) == "c"

    def test_upper_case_index_0(self, _make_spec) -> None:
        """
        Description: 'upper' case at index 0 must produce 'A'.
        Scenario: _format_panel_label(0, spec) with case='upper'.
        Expectation: 'A'.
        """
        assert _format_panel_label(0, _make_spec("upper")) == "A"

    def test_title_case_is_alias_for_upper(self, _make_spec) -> None:
        """
        Description: 'title' is an alias for 'upper'.
        Scenario: _format_panel_label(1, spec) with case='title'.
        Expectation: 'B'.
        """
        assert _format_panel_label(1, _make_spec("title")) == "B"

    def test_parens_lower_index_0(self, _make_spec) -> None:
        """
        Description: 'parens_lower' at index 0 must produce '(a)'.
        Scenario: _format_panel_label(0, spec) with case='parens_lower'.
        Expectation: '(a)'.
        """
        assert _format_panel_label(0, _make_spec("parens_lower")) == "(a)"

    def test_parens_upper_index_0(self, _make_spec) -> None:
        """
        Description: 'parens_upper' at index 0 must produce '(A)'.
        Scenario: _format_panel_label(0, spec) with case='parens_upper'.
        Expectation: '(A)'.
        """
        assert _format_panel_label(0, _make_spec("parens_upper")) == "(A)"

    def test_sentence_case_first_panel_capitalized(self, _make_spec) -> None:
        """
        Description: 'sentence' case capitalises only the first panel.
        Scenario: _format_panel_label(0, spec) with case='sentence'.
        Expectation: 'A'.
        """
        assert _format_panel_label(0, _make_spec("sentence")) == "A"

    def test_sentence_case_second_panel_lowercase(self, _make_spec) -> None:
        """
        Description: 'sentence' case keeps subsequent panels lowercase.
        Scenario: _format_panel_label(1, spec) with case='sentence'.
        Expectation: 'b'.
        """
        assert _format_panel_label(1, _make_spec("sentence")) == "b"

    def test_unknown_case_falls_back_to_lower(self, _make_spec) -> None:
        """
        Description: Unrecognised case values must fall back to lowercase.
        Scenario: _format_panel_label(0, spec) with case='unknown'.
        Expectation: 'a'.
        """
        assert _format_panel_label(0, _make_spec("unknown")) == "a"

    def test_index_25_is_z(self, _make_spec) -> None:
        """
        Description: Index 25 maps to the last single letter 'z'.
        Scenario: _format_panel_label(25, spec) with case='lower'.
        Expectation: 'z'.
        """
        assert _format_panel_label(25, _make_spec("lower")) == "z"

    def test_index_26_is_two_char_label(self, _make_spec) -> None:
        """
        Description: Index 26 exceeds a-z; must produce a two-character label.
        Scenario: _format_panel_label(26, spec) with case='lower'.
        Expectation: 'aa'.
        """
        assert _format_panel_label(26, _make_spec("lower")) == "aa"

    def test_index_27_is_ab(self, _make_spec) -> None:
        """
        Description: Index 27 must produce 'ab'.
        Scenario: _format_panel_label(27, spec) with case='lower'.
        Expectation: 'ab'.
        """
        assert _format_panel_label(27, _make_spec("lower")) == "ab"

    @pytest.mark.parametrize(
        "case,idx,expected",
        [
            ("lower", 0, "a"),
            ("upper", 0, "A"),
            ("parens_lower", 2, "(c)"),
            ("parens_upper", 2, "(C)"),
            ("sentence", 0, "A"),
            ("sentence", 3, "d"),
        ],
    )
    def test_parametric_cases(self, _make_spec, case: str, idx: int, expected: str) -> None:
        """
        Description: Parametric sweep of case/index combinations.
        Scenario: Various case and index pairs.
        Expectation: Each produces the listed expected label.
        """
        assert _format_panel_label(idx, _make_spec(case)) == expected


# ---------------------------------------------------------------------------
# figure
# ---------------------------------------------------------------------------


class TestFigure:
    """Validate the single-axis figure creation function."""

    def test_figure_returns_tuple(self) -> None:
        """
        Description: figure() must return a (Figure, Axes) tuple.
        Scenario: Call figure('nature').
        Expectation: Tuple of length 2.
        """
        result = figure("nature")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_figure_returns_matplotlib_figure(self) -> None:
        """
        Description: First element must be a Matplotlib Figure.
        Scenario: figure('nature')[0].
        Expectation: isinstance(Figure) is True.
        """
        fig, _ = figure("nature")
        assert isinstance(fig, plt.Figure)

    def test_figure_width_matches_spec_single_column(self) -> None:
        """
        Description: Figure width must match the journal's single-column width.
        Scenario: figure('nature', columns=1).
        Expectation: Width matches Dimension(89, 'mm').to_inches() within 0.01in
        (accounts for Matplotlib's DPI-based integer pixel rounding).
        """
        fig, _ = figure("nature", columns=1)
        expected = Dimension(89.0, "mm").to_inches()
        actual_w = fig.get_size_inches()[0]
        assert actual_w == pytest.approx(expected, abs=0.01)

    def test_figure_width_matches_spec_double_column(self) -> None:
        """
        Description: Double-column figure width must match the spec.
        Scenario: figure('nature', columns=2).
        Expectation: Width matches Dimension(183, 'mm').to_inches() within 0.01in.
        """
        fig, _ = figure("nature", columns=2)
        expected = Dimension(183.0, "mm").to_inches()
        actual_w = fig.get_size_inches()[0]
        assert actual_w == pytest.approx(expected, abs=0.01)

    def test_figure_default_aspect_is_golden_ratio(self) -> None:
        """
        Description: Default aspect ratio must be the golden ratio.
        Scenario: figure('nature') without explicit aspect.
        Expectation: width / height ≈ _GOLDEN_RATIO within 0.5%
        (accounts for DPI-based pixel rounding on both dimensions).
        """
        fig, _ = figure("nature")
        w, h = fig.get_size_inches()
        assert w / h == pytest.approx(_GOLDEN_RATIO, rel=0.005)

    def test_figure_explicit_aspect(self) -> None:
        """
        Description: Explicit aspect must override the golden ratio.
        Scenario: figure('nature', aspect=2.0).
        Expectation: width / height ≈ 2.0.
        """
        fig, _ = figure("nature", aspect=2.0)
        w, h = fig.get_size_inches()
        assert w / h == pytest.approx(2.0)

    def test_figure_square_aspect(self) -> None:
        """
        Description: Aspect=1.0 must produce a square figure.
        Scenario: figure('nature', aspect=1.0).
        Expectation: width == height.
        """
        fig, _ = figure("nature", aspect=1.0)
        w, h = fig.get_size_inches()
        assert w == pytest.approx(h)

    def test_figure_invalid_columns_raises(self) -> None:
        """
        Description: Invalid columns must raise ValueError.
        Scenario: figure('nature', columns=3).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            figure("nature", columns=3)

    def test_figure_unknown_journal_raises(self) -> None:
        """
        Description: Unknown journal must raise SpecNotFoundError.
        Scenario: figure('nonexistent_xyz').
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            figure("nonexistent_xyz")

    @pytest.mark.parametrize("journal", KNOWN_JOURNALS)
    def test_figure_creates_for_all_known_journals(self, journal: str) -> None:
        """
        Description: figure() must work for all known journals.
        Scenario: Parametric sweep over known journals.
        Expectation: No exception; returns a valid (fig, ax) tuple.
        """
        fig, ax = figure(journal)
        assert fig is not None
        assert ax is not None


# ---------------------------------------------------------------------------
# subplots
# ---------------------------------------------------------------------------


class TestSubplots:
    """Validate the multi-panel figure creation function."""

    def test_subplots_returns_tuple(self) -> None:
        """
        Description: subplots() must return a (Figure, ndarray) tuple.
        Scenario: Call subplots('nature').
        Expectation: Tuple of length 2.
        """
        result = subplots("nature")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_subplots_axes_always_2d(self) -> None:
        """
        Description: Axes are always a 2-D ndarray regardless of nrows/ncols.
        Scenario: subplots('nature', 1, 1).
        Expectation: axes.ndim == 2 and shape == (1, 1).
        """
        _, axes = subplots("nature", 1, 1)
        assert isinstance(axes, np.ndarray)
        assert axes.ndim == 2
        assert axes.shape == (1, 1)

    @pytest.mark.parametrize(
        "nrows,ncols",
        [(1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 2)],
    )
    def test_subplots_shape_matches_nrows_ncols(self, nrows: int, ncols: int) -> None:
        """
        Description: axes shape must match (nrows, ncols).
        Scenario: Parametric sweep over grid sizes.
        Expectation: axes.shape == (nrows, ncols).
        """
        _, axes = subplots("nature", nrows, ncols)
        assert axes.shape == (nrows, ncols)

    def test_subplots_width_matches_spec(self) -> None:
        """
        Description: Figure width must match the journal column width.
        Scenario: subplots('nature', columns=1).
        Expectation: Width matches Dimension(89, 'mm').to_inches() within 0.01in.
        """
        fig, _ = subplots("nature", columns=1)
        expected = Dimension(89.0, "mm").to_inches()
        assert fig.get_size_inches()[0] == pytest.approx(expected, abs=0.01)

    def test_subplots_double_column(self) -> None:
        """
        Description: Double-column subplots must use double-column width.
        Scenario: subplots('nature', columns=2).
        Expectation: Width matches Dimension(183, 'mm').to_inches() within 0.01in.
        """
        fig, _ = subplots("nature", columns=2)
        expected = Dimension(183.0, "mm").to_inches()
        assert fig.get_size_inches()[0] == pytest.approx(expected, abs=0.01)

    def test_subplots_panels_true_adds_labels(self) -> None:
        """
        Description: When panels=True, each axes should have a text label.
        Scenario: subplots('nature', 2, 2, panels=True).
        Expectation: Each axes has at least one Text child containing a label letter.
        """
        _, axes = subplots("nature", 2, 2, panels=True)
        for idx, ax in enumerate(axes.flat):
            texts = [t.get_text() for t in ax.texts]
            assert len(texts) > 0, f"Panel {idx} has no text label"

    def test_subplots_panels_false_no_labels(self) -> None:
        """
        Description: When panels=False, no panel labels should be added.
        Scenario: subplots('nature', 2, 2, panels=False).
        Expectation: No axes have plotstyle-added text.
        """
        _, axes = subplots("nature", 2, 2, panels=False)
        for ax in axes.flat:
            assert len(ax.texts) == 0

    def test_subplots_panel_label_order(self) -> None:
        """
        Description: Panel labels must follow alphabetical order (a, b, c, d).
        Scenario: subplots('nature', 2, 2, panels=True).
        Expectation: Labels in .flat iteration order are 'a', 'b', 'c', 'd'.
        """
        spec = registry.get("nature")
        _, axes = subplots("nature", 2, 2, panels=True)
        labels = [ax.texts[0].get_text() for ax in axes.flat]
        case = spec.typography.panel_label_case
        if case in ("lower", ""):
            assert labels == ["a", "b", "c", "d"]
        elif case == "upper":
            assert labels == ["A", "B", "C", "D"]

    def test_subplots_invalid_columns_raises(self) -> None:
        """
        Description: Invalid columns must raise ValueError.
        Scenario: subplots('nature', columns=0).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            subplots("nature", columns=0)

    def test_subplots_unknown_journal_raises(self) -> None:
        """
        Description: Unknown journal must raise SpecNotFoundError.
        Scenario: subplots('nonexistent_xyz').
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            subplots("nonexistent_xyz")

    def test_subplots_explicit_aspect(self) -> None:
        """
        Description: Explicit aspect must be applied.
        Scenario: subplots('nature', aspect=2.0).
        Expectation: width / height ≈ 2.0.
        """
        fig, _ = subplots("nature", aspect=2.0)
        w, h = fig.get_size_inches()
        assert w / h == pytest.approx(2.0)

    def test_subplots_flat_iteration_works(self) -> None:
        """
        Description: .flat iteration must yield all axes in row-major order.
        Scenario: subplots('nature', 2, 3).
        Expectation: .flat yields exactly 6 axes.
        """
        _, axes = subplots("nature", 2, 3, panels=False)
        assert len(list(axes.flat)) == 6

    def test_subplots_single_panel_supports_indexing(self) -> None:
        """
        Description: Even 1x1 subplots must support [0, 0] indexing.
        Scenario: subplots('nature', 1, 1).
        Expectation: axes[0, 0] returns an Axes object.
        """
        _, axes = subplots("nature", 1, 1, panels=False)
        ax = axes[0, 0]
        assert ax is not None

    @pytest.mark.parametrize("journal", KNOWN_JOURNALS)
    def test_subplots_for_all_known_journals(self, journal: str) -> None:
        """
        Description: subplots() must work for all known journals.
        Scenario: Parametric sweep over known journals.
        Expectation: No exception.
        """
        fig, axes = subplots(journal, 1, 2, panels=True)
        assert fig is not None
        assert axes.shape == (1, 2)
