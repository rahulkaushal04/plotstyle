"""Enhanced test suite for plotstyle.core.migrate.

Covers: diff, migrate, SpecDiff, SpecDifference, formatting helpers,
_rescale_text_artists, _emit_migration_warnings, and all edge cases.
"""

from __future__ import annotations

import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

from plotstyle._utils.warnings import PlotStyleWarning
from plotstyle.core.migrate import (
    _DIFF_FIELDS,
    _SEPARATOR_WIDTH,
    SpecDiff,
    SpecDifference,
    _emit_migration_warnings,
    _format_bool,
    _format_list,
    _format_mm,
    _format_pt,
    _rescale_text_artists,
    _resolve_attr,
    diff,
    migrate,
)
from plotstyle.specs import registry
from plotstyle.specs.units import Dimension

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

KNOWN_JOURNALS: list[str] = ["nature", "ieee", "science"]


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all Matplotlib figures after each test to prevent memory leaks."""
    yield
    plt.close("all")


@pytest.fixture
def nature_fig() -> plt.Figure:
    """A simple figure created at Nature's single-column width."""
    spec = registry.get("nature")
    width_in = Dimension(spec.dimensions.single_column_mm, "mm").to_inches()
    fig, ax = plt.subplots(figsize=(width_in, width_in / 1.618))
    ax.plot([0, 1, 2], [3, 4, 5])
    ax.set_title("Test Title")
    ax.set_xlabel("X Label")
    ax.set_ylabel("Y Label")
    return fig


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


class TestFormatHelpers:
    """Validate the internal formatting helper functions."""

    def test_format_list_with_list(self) -> None:
        """
        Description: Lists must be joined with commas.
        Scenario: _format_list(['pdf', 'tiff']).
        Expectation: 'pdf, tiff'.
        """
        assert _format_list(["pdf", "tiff"]) == "pdf, tiff"

    def test_format_list_with_single_item(self) -> None:
        """
        Description: Single-item lists produce no comma.
        Scenario: _format_list(['pdf']).
        Expectation: 'pdf'.
        """
        assert _format_list(["pdf"]) == "pdf"

    def test_format_list_with_empty_list(self) -> None:
        """
        Description: Empty lists produce an empty string.
        Scenario: _format_list([]).
        Expectation: ''.
        """
        assert _format_list([]) == ""

    def test_format_list_with_non_list(self) -> None:
        """
        Description: Non-list values are stringified directly.
        Scenario: _format_list(42).
        Expectation: '42'.
        """
        assert _format_list(42) == "42"

    def test_format_mm(self) -> None:
        """
        Description: _format_mm appends 'mm' suffix.
        Scenario: _format_mm(89.0).
        Expectation: '89.0mm'.
        """
        assert _format_mm(89.0) == "89.0mm"

    def test_format_pt(self) -> None:
        """
        Description: _format_pt appends 'pt' suffix.
        Scenario: _format_pt(7.0).
        Expectation: '7.0pt'.
        """
        assert _format_pt(7.0) == "7.0pt"

    def test_format_bool_true(self) -> None:
        """
        Description: Truthy values must produce 'Yes'.
        Scenario: _format_bool(True).
        Expectation: 'Yes'.
        """
        assert _format_bool(True) == "Yes"

    def test_format_bool_false(self) -> None:
        """
        Description: Falsy values must produce 'No'.
        Scenario: _format_bool(False).
        Expectation: 'No'.
        """
        assert _format_bool(False) == "No"

    def test_format_bool_truthy_non_bool(self) -> None:
        """
        Description: Non-bool truthy values must produce 'Yes'.
        Scenario: _format_bool(1).
        Expectation: 'Yes'.
        """
        assert _format_bool(1) == "Yes"

    def test_format_bool_falsy_non_bool(self) -> None:
        """
        Description: Non-bool falsy values must produce 'No'.
        Scenario: _format_bool(0).
        Expectation: 'No'.
        """
        assert _format_bool(0) == "No"


# ---------------------------------------------------------------------------
# _resolve_attr
# ---------------------------------------------------------------------------


class TestResolveAttr:
    """Validate dotted attribute resolution."""

    def test_single_level_attr(self) -> None:
        """
        Description: Single-segment paths resolve one getattr call.
        Scenario: Resolve 'notes' on a spec.
        Expectation: Returns the notes string.
        """
        spec = registry.get("nature")
        assert _resolve_attr(spec, "notes") == spec.notes

    def test_nested_attr(self) -> None:
        """
        Description: Multi-segment paths resolve through nested objects.
        Scenario: Resolve 'dimensions.single_column_mm' on a spec.
        Expectation: Returns spec.dimensions.single_column_mm.
        """
        spec = registry.get("nature")
        result = _resolve_attr(spec, "dimensions.single_column_mm")
        assert result == spec.dimensions.single_column_mm

    def test_missing_attr_raises(self) -> None:
        """
        Description: Invalid attribute paths must raise AttributeError.
        Scenario: Resolve 'nonexistent.field' on a spec.
        Expectation: AttributeError raised.
        """
        spec = registry.get("nature")
        with pytest.raises(AttributeError):
            _resolve_attr(spec, "nonexistent.field")


# ---------------------------------------------------------------------------
# SpecDifference
# ---------------------------------------------------------------------------


class TestSpecDifference:
    """Validate the immutable difference record."""

    def test_frozen_dataclass(self) -> None:
        """
        Description: SpecDifference must be frozen (immutable).
        Scenario: Attempt to set an attribute after construction.
        Expectation: FrozenInstanceError (or AttributeError) raised.
        """
        d = SpecDifference(field="a", label="A", value_a="1", value_b="2")
        with pytest.raises(AttributeError):
            d.field = "b"  # type: ignore[misc]

    def test_attributes_stored(self) -> None:
        """
        Description: All four attributes must be stored correctly.
        Scenario: Construct a SpecDifference.
        Expectation: Each attribute matches the constructor argument.
        """
        d = SpecDifference(field="a.b", label="Label", value_a="X", value_b="Y")
        assert d.field == "a.b"
        assert d.label == "Label"
        assert d.value_a == "X"
        assert d.value_b == "Y"

    def test_hashable(self) -> None:
        """
        Description: Frozen dataclass with slots must be hashable.
        Scenario: Insert into a set.
        Expectation: No error.
        """
        d = SpecDifference(field="a", label="A", value_a="1", value_b="2")
        assert len({d}) == 1

    def test_equal_instances(self) -> None:
        """
        Description: Two SpecDifference with same fields must be equal.
        Scenario: Compare two identical instances.
        Expectation: Equality is True.
        """
        d1 = SpecDifference(field="a", label="A", value_a="1", value_b="2")
        d2 = SpecDifference(field="a", label="A", value_a="1", value_b="2")
        assert d1 == d2


# ---------------------------------------------------------------------------
# SpecDiff
# ---------------------------------------------------------------------------


class TestSpecDiff:
    """Validate the SpecDiff result container."""

    def test_empty_diff_is_falsy(self) -> None:
        """
        Description: A SpecDiff with no differences must be falsy.
        Scenario: Create SpecDiff with empty differences list.
        Expectation: bool(diff_obj) is False.
        """
        sd = SpecDiff(journal_a="A", journal_b="B", differences=[])
        assert not sd

    def test_non_empty_diff_is_truthy(self) -> None:
        """
        Description: A SpecDiff with at least one difference must be truthy.
        Scenario: Create SpecDiff with one difference.
        Expectation: bool(diff_obj) is True.
        """
        d = SpecDifference(field="a", label="A", value_a="1", value_b="2")
        sd = SpecDiff(journal_a="A", journal_b="B", differences=[d])
        assert sd

    def test_len_returns_difference_count(self) -> None:
        """
        Description: len(SpecDiff) must return the number of differences.
        Scenario: Create SpecDiff with 3 differences.
        Expectation: len == 3.
        """
        diffs = [
            SpecDifference(field=f"f{i}", label=f"L{i}", value_a=f"{i}", value_b=f"{i + 1}")
            for i in range(3)
        ]
        sd = SpecDiff(journal_a="A", journal_b="B", differences=diffs)
        assert len(sd) == 3

    def test_len_zero_when_identical(self) -> None:
        """
        Description: Identical specs must produce len 0.
        Scenario: Create empty SpecDiff.
        Expectation: len == 0.
        """
        sd = SpecDiff(journal_a="A", journal_b="B")
        assert len(sd) == 0

    def test_str_contains_journal_names(self) -> None:
        """
        Description: String representation must include both journal names.
        Scenario: Create SpecDiff with known journal names.
        Expectation: Both names appear in str().
        """
        sd = SpecDiff(journal_a="Nature", journal_b="Science")
        s = str(sd)
        assert "Nature" in s
        assert "Science" in s

    def test_str_no_differences_message(self) -> None:
        """
        Description: Empty diffs must produce 'No differences.' message.
        Scenario: Create empty SpecDiff.
        Expectation: 'No differences.' in str().
        """
        sd = SpecDiff(journal_a="A", journal_b="B")
        assert "No differences." in str(sd)

    def test_str_with_differences_contains_labels(self) -> None:
        """
        Description: Non-empty diffs must include the field labels.
        Scenario: Create SpecDiff with a labeled difference.
        Expectation: Label appears in str().
        """
        d = SpecDifference(field="a", label="My Label", value_a="1", value_b="2")
        sd = SpecDiff(journal_a="A", journal_b="B", differences=[d])
        assert "My Label" in str(sd)

    def test_str_contains_arrow(self) -> None:
        """
        Description: Diff rows must use arrow notation.
        Scenario: Create SpecDiff with one difference.
        Expectation: '→' appears in str().
        """
        d = SpecDifference(field="a", label="L", value_a="1", value_b="2")
        sd = SpecDiff(journal_a="A", journal_b="B", differences=[d])
        assert "→" in str(sd)

    def test_to_dict_structure(self) -> None:
        """
        Description: to_dict must return a JSON-serialisable dict.
        Scenario: Create SpecDiff and call to_dict().
        Expectation: Keys 'journal_a', 'journal_b', 'differences' present.
        """
        sd = SpecDiff(journal_a="A", journal_b="B")
        d = sd.to_dict()
        assert "journal_a" in d
        assert "journal_b" in d
        assert "differences" in d
        assert isinstance(d["differences"], list)

    def test_to_dict_with_differences(self) -> None:
        """
        Description: Each difference must appear as a dict in to_dict output.
        Scenario: Create SpecDiff with one difference.
        Expectation: differences[0] has field, label, value_a, value_b.
        """
        diff_item = SpecDifference(field="f", label="L", value_a="1", value_b="2")
        sd = SpecDiff(journal_a="A", journal_b="B", differences=[diff_item])
        d = sd.to_dict()
        assert len(d["differences"]) == 1
        entry = d["differences"][0]
        assert entry["field"] == "f"
        assert entry["label"] == "L"
        assert entry["value_a"] == "1"
        assert entry["value_b"] == "2"

    def test_to_dict_journal_names(self) -> None:
        """
        Description: Journal names in to_dict must match constructor args.
        Scenario: Create and serialize.
        Expectation: Names match.
        """
        sd = SpecDiff(journal_a="Nature", journal_b="Science")
        d = sd.to_dict()
        assert d["journal_a"] == "Nature"
        assert d["journal_b"] == "Science"


# ---------------------------------------------------------------------------
# _DIFF_FIELDS manifest
# ---------------------------------------------------------------------------


class TestDiffFieldsManifest:
    """Validate the diff field manifest structure."""

    def test_manifest_is_list(self) -> None:
        """
        Description: _DIFF_FIELDS must be a list for ordered iteration.
        Scenario: Check type.
        Expectation: isinstance(list).
        """
        assert isinstance(_DIFF_FIELDS, list)

    def test_manifest_entries_are_triples(self) -> None:
        """
        Description: Each entry must be a (dotted_path, label, formatter) triple.
        Scenario: Check structure of each entry.
        Expectation: Each is a tuple of length 3.
        """
        for entry in _DIFF_FIELDS:
            assert isinstance(entry, tuple)
            assert len(entry) == 3

    def test_manifest_formatters_are_callable(self) -> None:
        """
        Description: The third element of each triple must be callable.
        Scenario: Check each formatter.
        Expectation: callable() returns True.
        """
        for _, _, formatter in _DIFF_FIELDS:
            assert callable(formatter)

    def test_manifest_dotted_paths_resolve_on_known_spec(self) -> None:
        """
        Description: Every dotted_path must resolve on a real spec without error.
        Scenario: Resolve each path against the 'nature' spec.
        Expectation: No AttributeError.
        """
        spec = registry.get("nature")
        for dotted_path, _, _ in _DIFF_FIELDS:
            _resolve_attr(spec, dotted_path)  # Should not raise

    def test_manifest_has_expected_fields(self) -> None:
        """
        Description: Key fields must be tracked in the manifest.
        Scenario: Check for known paths.
        Expectation: Dimension, typography, and export fields present.
        """
        paths = [entry[0] for entry in _DIFF_FIELDS]
        assert "dimensions.single_column_mm" in paths
        assert "typography.font_family" in paths
        assert "export.min_dpi" in paths


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------


class TestDiff:
    """Validate the public diff function."""

    def test_diff_same_journal_is_empty(self) -> None:
        """
        Description: Diffing a journal against itself must yield no differences.
        Scenario: diff('nature', 'nature').
        Expectation: SpecDiff is falsy; len == 0.
        """
        result = diff("nature", "nature")
        assert not result
        assert len(result) == 0

    def test_diff_different_journals_has_differences(self) -> None:
        """
        Description: Nature and IEEE differ on many fields.
        Scenario: diff('nature', 'ieee').
        Expectation: SpecDiff is truthy; len > 0.
        """
        result = diff("nature", "ieee")
        assert result
        assert len(result) > 0

    def test_diff_returns_spec_diff_instance(self) -> None:
        """
        Description: Return type must be SpecDiff.
        Scenario: diff('nature', 'science').
        Expectation: isinstance(SpecDiff).
        """
        result = diff("nature", "science")
        assert isinstance(result, SpecDiff)

    def test_diff_uses_display_names(self) -> None:
        """
        Description: journal_a and journal_b must be display names from metadata.
        Scenario: diff('nature', 'ieee').
        Expectation: Display names (e.g. 'Nature', 'IEEE') are used.
        """
        result = diff("nature", "ieee")
        assert result.journal_a == registry.get("nature").metadata.name
        assert result.journal_b == registry.get("ieee").metadata.name

    def test_diff_unknown_journal_raises(self) -> None:
        """
        Description: Unknown journal must raise SpecNotFoundError.
        Scenario: diff('nature', 'nonexistent_xyz').
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            diff("nature", "nonexistent_xyz")

    def test_diff_unknown_first_journal_raises(self) -> None:
        """
        Description: Unknown first journal must also raise.
        Scenario: diff('nonexistent_xyz', 'nature').
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            diff("nonexistent_xyz", "nature")

    def test_diff_both_unknown_raises(self) -> None:
        """
        Description: Both journals unknown must raise (on the first one).
        Scenario: diff('nonexistent_a', 'nonexistent_b').
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            diff("nonexistent_a", "nonexistent_b")

    def test_diff_differences_contain_spec_difference_instances(self) -> None:
        """
        Description: Each difference must be a SpecDifference.
        Scenario: diff('nature', 'ieee').differences.
        Expectation: All entries are SpecDifference instances.
        """
        result = diff("nature", "ieee")
        for d in result.differences:
            assert isinstance(d, SpecDifference)

    def test_diff_symmetry_difference_count(self) -> None:
        """
        Description: diff(a, b) and diff(b, a) must have the same number of differences.
        Scenario: Compare len(diff('nature', 'ieee')) and len(diff('ieee', 'nature')).
        Expectation: Equal counts.
        """
        ab = diff("nature", "ieee")
        ba = diff("ieee", "nature")
        assert len(ab) == len(ba)

    def test_diff_to_dict_is_serialisable(self) -> None:
        """
        Description: to_dict output must contain only JSON-serialisable primitives.
        Scenario: diff('nature', 'ieee').to_dict().
        Expectation: Can import json and dumps without error.
        """
        import json

        result = diff("nature", "ieee").to_dict()
        json.dumps(result)  # Should not raise


# ---------------------------------------------------------------------------
# _rescale_text_artists
# ---------------------------------------------------------------------------


class TestRescaleTextArtists:
    """Validate text rescaling and clamping logic."""

    def test_scale_factor_applied(self) -> None:
        """
        Description: Each text artist's font size must be scaled by the factor.
        Scenario: Create figure with 10pt text, scale by 2.0, clamp [5, 30].
        Expectation: Text size becomes 20pt.
        """
        fig, ax = plt.subplots()
        text = ax.text(0.5, 0.5, "Hello", fontsize=10)
        _rescale_text_artists(fig, scale=2.0, min_pt=5.0, max_pt=30.0)
        assert text.get_fontsize() == pytest.approx(20.0)

    def test_clamping_to_max(self) -> None:
        """
        Description: Scaled sizes exceeding max_pt must be clamped.
        Scenario: 10pt text scaled by 5.0 with max_pt=20.
        Expectation: Text size clamped to 20pt.
        """
        fig, ax = plt.subplots()
        text = ax.text(0.5, 0.5, "Hello", fontsize=10)
        _rescale_text_artists(fig, scale=5.0, min_pt=5.0, max_pt=20.0)
        assert text.get_fontsize() == pytest.approx(20.0)

    def test_clamping_to_min(self) -> None:
        """
        Description: Scaled sizes below min_pt must be clamped.
        Scenario: 10pt text scaled by 0.1 with min_pt=5.
        Expectation: Text size clamped to 5pt.
        """
        fig, ax = plt.subplots()
        text = ax.text(0.5, 0.5, "Hello", fontsize=10)
        _rescale_text_artists(fig, scale=0.1, min_pt=5.0, max_pt=20.0)
        assert text.get_fontsize() == pytest.approx(5.0)

    def test_scale_factor_one_preserves_size(self) -> None:
        """
        Description: Scale factor 1.0 must not change sizes (within clamp range).
        Scenario: 10pt text scaled by 1.0, clamp [5, 20].
        Expectation: Text size remains 10pt.
        """
        fig, ax = plt.subplots()
        text = ax.text(0.5, 0.5, "Hello", fontsize=10)
        _rescale_text_artists(fig, scale=1.0, min_pt=5.0, max_pt=20.0)
        assert text.get_fontsize() == pytest.approx(10.0)

    def test_multiple_text_artists_all_scaled(self) -> None:
        """
        Description: All text artists in the figure must be rescaled.
        Scenario: Two text objects at different sizes.
        Expectation: Both are scaled.
        """
        fig, ax = plt.subplots()
        t1 = ax.text(0.1, 0.1, "A", fontsize=10)
        t2 = ax.text(0.5, 0.5, "B", fontsize=8)
        _rescale_text_artists(fig, scale=1.5, min_pt=5.0, max_pt=30.0)
        assert t1.get_fontsize() == pytest.approx(15.0)
        assert t2.get_fontsize() == pytest.approx(12.0)


# ---------------------------------------------------------------------------
# _emit_migration_warnings
# ---------------------------------------------------------------------------


class TestEmitMigrationWarnings:
    """Validate migration warning emission."""

    def test_font_family_change_emits_warning(self) -> None:
        """
        Description: Changing font families must produce a PlotStyleWarning.
        Scenario: Migrate from nature (Helvetica) to ieee (Times New Roman).
        Expectation: Warning about font family change.
        """
        from_spec = registry.get("nature")
        to_spec = registry.get("ieee")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _emit_migration_warnings(from_spec, to_spec)
        font_warnings = [x for x in w if "Font family" in str(x.message)]
        assert len(font_warnings) >= 1

    def test_same_font_family_no_warning(self) -> None:
        """
        Description: No font warning when families are identical.
        Scenario: Migrate from nature to nature.
        Expectation: No font family warning.
        """
        spec = registry.get("nature")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _emit_migration_warnings(spec, spec)
        font_warnings = [x for x in w if "Font family" in str(x.message)]
        assert len(font_warnings) == 0

    def test_grayscale_newly_required_emits_warning(self) -> None:
        """
        Description: Warning when target requires grayscale but source does not.
        Scenario: Nature (grayscale_required=false) → IEEE (grayscale_required=true).
        Expectation: Grayscale warning emitted.
        """
        from_spec = registry.get("nature")
        to_spec = registry.get("ieee")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _emit_migration_warnings(from_spec, to_spec)
        gray_warnings = [x for x in w if "grayscale" in str(x.message).lower()]
        assert len(gray_warnings) >= 1

    def test_dpi_increase_emits_warning(self) -> None:
        """
        Description: Warning when target requires higher DPI than source.
        Scenario: Nature (300 DPI) → IEEE (600 DPI).
        Expectation: DPI warning emitted.
        """
        from_spec = registry.get("nature")
        to_spec = registry.get("ieee")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _emit_migration_warnings(from_spec, to_spec)
        dpi_warnings = [x for x in w if "DPI" in str(x.message)]
        assert len(dpi_warnings) >= 1

    def test_no_dpi_warning_when_dpi_decreases(self) -> None:
        """
        Description: No DPI warning when target has lower or equal DPI.
        Scenario: IEEE (600 DPI) → Nature (300 DPI).
        Expectation: No DPI warning.
        """
        from_spec = registry.get("ieee")
        to_spec = registry.get("nature")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _emit_migration_warnings(from_spec, to_spec)
        dpi_warnings = [x for x in w if "DPI" in str(x.message)]
        assert len(dpi_warnings) == 0

    def test_all_warnings_are_plotstyle_warning(self) -> None:
        """
        Description: All warnings must be PlotStyleWarning subclass.
        Scenario: Migrate from nature to ieee to generate multiple warnings.
        Expectation: Every caught warning is PlotStyleWarning.
        """
        from_spec = registry.get("nature")
        to_spec = registry.get("ieee")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _emit_migration_warnings(from_spec, to_spec)
        for warning in w:
            assert issubclass(warning.category, PlotStyleWarning)


# ---------------------------------------------------------------------------
# migrate
# ---------------------------------------------------------------------------


class TestMigrate:
    """Validate the public migrate function."""

    def test_migrate_returns_same_figure(self, nature_fig: plt.Figure) -> None:
        """
        Description: migrate must return the same figure object (mutated in-place).
        Scenario: Migrate a Nature figure to IEEE.
        Expectation: Return value is the same object.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", PlotStyleWarning)
            result = migrate(nature_fig, from_journal="nature", to_journal="ieee")
        assert result is nature_fig

    def test_migrate_resizes_figure_width(self, nature_fig: plt.Figure) -> None:
        """
        Description: Figure width must match the target journal's single-column width.
        Scenario: Migrate from Nature to Science.
        Expectation: New width equals Dimension(57, 'mm').to_inches() within 0.5%.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", PlotStyleWarning)
            migrate(nature_fig, from_journal="nature", to_journal="science")
        expected_w = Dimension(57.0, "mm").to_inches()
        actual_w = nature_fig.get_size_inches()[0]
        assert actual_w == pytest.approx(expected_w, rel=0.005)

    def test_migrate_preserves_aspect_ratio(self, nature_fig: plt.Figure) -> None:
        """
        Description: Aspect ratio must be preserved after migration.
        Scenario: Migrate from Nature to Science.
        Expectation: height/width ratio is unchanged within 0.5% (pixel rounding tolerance).
        """
        old_w, old_h = nature_fig.get_size_inches()
        old_aspect = old_h / old_w
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", PlotStyleWarning)
            migrate(nature_fig, from_journal="nature", to_journal="science")
        new_w, new_h = nature_fig.get_size_inches()
        new_aspect = new_h / new_w
        assert new_aspect == pytest.approx(old_aspect, rel=0.005)

    def test_migrate_rescales_text(self, nature_fig: plt.Figure) -> None:
        """
        Description: Text artists must be rescaled to the target's font range.
        Scenario: Migrate from Nature (5-7pt) to IEEE (8-10pt).
        Expectation: Text sizes are within IEEE's range.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", PlotStyleWarning)
            migrate(nature_fig, from_journal="nature", to_journal="ieee")
        ieee_spec = registry.get("ieee")
        for text_artist in nature_fig.findobj(mpl.text.Text):
            size = text_artist.get_fontsize()
            if text_artist.get_text():  # Only check non-empty text
                assert size >= ieee_spec.typography.min_font_pt - 0.01
                assert size <= ieee_spec.typography.max_font_pt + 0.01

    def test_migrate_unknown_source_raises(self, nature_fig: plt.Figure) -> None:
        """
        Description: Unknown source journal must raise.
        Scenario: migrate from 'nonexistent_xyz'.
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            migrate(nature_fig, from_journal="nonexistent_xyz", to_journal="ieee")

    def test_migrate_unknown_target_raises(self, nature_fig: plt.Figure) -> None:
        """
        Description: Unknown target journal must raise.
        Scenario: migrate to 'nonexistent_xyz'.
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            migrate(nature_fig, from_journal="nature", to_journal="nonexistent_xyz")

    def test_migrate_same_journal_no_resize(self, nature_fig: plt.Figure) -> None:
        """
        Description: Migrating to the same journal should not change width.
        Scenario: migrate from nature to nature.
        Expectation: Width is approximately the same.
        """
        expected_w = Dimension(registry.get("nature").dimensions.single_column_mm, "mm").to_inches()
        migrate(nature_fig, from_journal="nature", to_journal="nature")
        actual_w = nature_fig.get_size_inches()[0]
        assert actual_w == pytest.approx(expected_w)

    def test_migrate_emits_warnings_for_changes(self, nature_fig: plt.Figure) -> None:
        """
        Description: Migration from Nature to IEEE must emit warnings.
        Scenario: Capture warnings during migration.
        Expectation: At least one PlotStyleWarning emitted.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            migrate(nature_fig, from_journal="nature", to_journal="ieee")
        plotstyle_warnings = [x for x in w if issubclass(x.category, PlotStyleWarning)]
        assert len(plotstyle_warnings) >= 1

    @pytest.mark.parametrize(
        "src,tgt",
        [
            ("nature", "ieee"),
            ("nature", "science"),
            ("ieee", "nature"),
            ("ieee", "science"),
            ("science", "nature"),
            ("science", "ieee"),
        ],
    )
    def test_migrate_cross_journal_no_error(self, src: str, tgt: str) -> None:
        """
        Description: Migration between any two known journals must not raise.
        Scenario: Parametric sweep of journal pairs.
        Expectation: No exception.
        """
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        ax.set_title("T")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", PlotStyleWarning)
            migrate(fig, from_journal=src, to_journal=tgt)

    def test_migrate_updates_rcparams(self, nature_fig: plt.Figure) -> None:
        """
        Description: migrate must update mpl.rcParams with target journal's params.
        Scenario: Check a known rcParam after migration.
        Expectation: savefig.dpi matches target journal's min_dpi.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", PlotStyleWarning)
            migrate(nature_fig, from_journal="nature", to_journal="ieee")
        ieee_spec = registry.get("ieee")
        assert mpl.rcParams["savefig.dpi"] == ieee_spec.export.min_dpi


# ---------------------------------------------------------------------------
# _SEPARATOR_WIDTH constant
# ---------------------------------------------------------------------------


class TestSeparatorWidth:
    """Validate the separator width constant."""

    def test_separator_width_is_positive_int(self) -> None:
        """
        Description: _SEPARATOR_WIDTH must be a positive integer.
        Scenario: Check type and value.
        Expectation: int > 0.
        """
        assert isinstance(_SEPARATOR_WIDTH, int)
        assert _SEPARATOR_WIDTH > 0
