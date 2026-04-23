"""Enhanced test suite for plotstyle.color.palettes.

Covers: load_palette, palette, JOURNAL_PALETTE_MAP, exception hierarchy,
caching, cycling behaviour, with_markers mode, and all edge/error cases.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from plotstyle.color.palettes import (
    _DATA_DIR,
    _LINESTYLES,
    _MARKERS,
    JOURNAL_PALETTE_MAP,
    PaletteNotFoundError,
    _palette_cache,
    load_palette,
    palette,
)
from plotstyle.specs import SpecNotFoundError

# ---------------------------------------------------------------------------
# Shared constants and fixtures
# ---------------------------------------------------------------------------

ALL_JOURNALS: list[str] = sorted(JOURNAL_PALETTE_MAP.keys())
ALL_PALETTE_NAMES: list[str] = sorted(set(JOURNAL_PALETTE_MAP.values()))


@pytest.fixture(params=ALL_JOURNALS)
def journal(request) -> str:
    """Parametric fixture yielding each known journal identifier."""
    return request.param


@pytest.fixture(params=ALL_PALETTE_NAMES)
def palette_name(request) -> str:
    """Parametric fixture yielding each unique palette name."""
    return request.param


@pytest.fixture(autouse=True)
def _clear_palette_cache():
    """Clear the module-level palette cache before and after each test."""
    saved = dict(_palette_cache)
    _palette_cache.clear()
    yield
    _palette_cache.clear()
    _palette_cache.update(saved)


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    """Validate custom exception inheritance and attributes."""

    def test_palette_not_found_error_is_file_not_found(self) -> None:
        """
        Description: PaletteNotFoundError must extend FileNotFoundError.
        Scenario: Instantiate PaletteNotFoundError.
        Expectation: isinstance(FileNotFoundError) is True.
        """
        err = PaletteNotFoundError("test")
        assert isinstance(err, FileNotFoundError)

    def test_unknown_journal_error_is_key_error(self) -> None:
        """
        Description: SpecNotFoundError must extend KeyError.
        Scenario: Instantiate SpecNotFoundError.
        Expectation: isinstance(KeyError) is True.
        """
        err = SpecNotFoundError("test", available=[])
        assert isinstance(err, KeyError)

    def test_palette_not_found_catchable_as_os_error(self) -> None:
        """
        Description: FileNotFoundError is an OSError; PaletteNotFoundError must be too.
        Scenario: Catch as OSError.
        Expectation: No uncaught exception.
        """
        with pytest.raises(OSError):
            raise PaletteNotFoundError("missing")

    def test_unknown_journal_catchable_as_lookup_error(self) -> None:
        """
        Description: KeyError is a LookupError; SpecNotFoundError must be too.
        Scenario: Catch as LookupError.
        Expectation: No uncaught exception.
        """
        with pytest.raises(LookupError):
            raise SpecNotFoundError("bad", available=[])


# ---------------------------------------------------------------------------
# JOURNAL_PALETTE_MAP
# ---------------------------------------------------------------------------


class TestJournalPaletteMap:
    """Validate the journal-to-palette mapping constant."""

    def test_map_is_non_empty(self) -> None:
        """
        Description: The mapping must contain at least one entry.
        Scenario: Check length.
        Expectation: len > 0.
        """
        assert len(JOURNAL_PALETTE_MAP) > 0

    def test_all_keys_are_lowercase(self) -> None:
        """
        Description: Journal identifiers must be lowercase for case-insensitive lookup.
        Scenario: Check each key.
        Expectation: key == key.lower() for all keys.
        """
        for key in JOURNAL_PALETTE_MAP:
            assert key == key.lower(), f"Key {key!r} is not lowercase"

    def test_all_values_are_strings(self) -> None:
        """
        Description: Each mapped palette name must be a non-empty string.
        Scenario: Check type and content of each value.
        Expectation: isinstance str and len > 0.
        """
        for value in JOURNAL_PALETTE_MAP.values():
            assert isinstance(value, str) and len(value) > 0

    @pytest.mark.parametrize("journal", ALL_JOURNALS)
    def test_each_mapped_palette_file_exists(self, journal: str) -> None:
        """
        Description: Every palette name in the map must have a corresponding JSON file.
        Scenario: Resolve the file path for each journal's mapped palette.
        Expectation: JSON file exists on disk.
        """
        palette_name = JOURNAL_PALETTE_MAP[journal]
        json_path = _DATA_DIR / f"{palette_name}.json"
        assert json_path.is_file(), f"Missing {json_path}"

    @pytest.mark.parametrize(
        "journal",
        [
            "acs",
            "cell",
            "elsevier",
            "ieee",
            "nature",
            "plos",
            "prl",
            "science",
            "springer",
            "wiley",
        ],
    )
    def test_expected_journals_present(self, journal: str) -> None:
        """
        Description: All documented journals must appear in the map.
        Scenario: Check each expected journal.
        Expectation: Key exists.
        """
        assert journal in JOURNAL_PALETTE_MAP


# ---------------------------------------------------------------------------
# _DATA_DIR
# ---------------------------------------------------------------------------


class TestDataDir:
    """Validate the data directory location and contents."""

    def test_data_dir_exists(self) -> None:
        """
        Description: The bundled data directory must exist.
        Scenario: Check _DATA_DIR path.
        Expectation: Path exists and is a directory.
        """
        assert _DATA_DIR.is_dir()

    def test_data_dir_contains_json_files(self) -> None:
        """
        Description: The data directory must contain at least one JSON file.
        Scenario: Glob for *.json.
        Expectation: At least one file found.
        """
        json_files = list(_DATA_DIR.glob("*.json"))
        assert len(json_files) > 0

    @pytest.mark.parametrize("name", ALL_PALETTE_NAMES)
    def test_each_palette_json_has_colors_key(self, name: str) -> None:
        """
        Description: Each palette JSON must contain a top-level 'colors' key.
        Scenario: Load and inspect the JSON file.
        Expectation: 'colors' key exists and is a list.
        """
        json_path = _DATA_DIR / f"{name}.json"
        with json_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        assert "colors" in data
        assert isinstance(data["colors"], list)

    @pytest.mark.parametrize("name", ALL_PALETTE_NAMES)
    def test_each_palette_colors_are_hex_strings(self, name: str) -> None:
        """
        Description: All colour entries must be hex string format.
        Scenario: Check each colour in each palette.
        Expectation: Each starts with '#' and has length 7.
        """
        json_path = _DATA_DIR / f"{name}.json"
        with json_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        for c in data["colors"]:
            assert isinstance(c, str)
            assert c.startswith("#"), f"Colour {c!r} is not hex"
            assert len(c) == 7, f"Colour {c!r} is not 7-char hex"


# ---------------------------------------------------------------------------
# load_palette
# ---------------------------------------------------------------------------


class TestLoadPalette:
    """Validate palette loading, caching, and error handling."""

    @pytest.mark.parametrize("name", ALL_PALETTE_NAMES)
    def test_load_all_built_in_palettes(self, name: str) -> None:
        """
        Description: Every built-in palette must load without error.
        Scenario: Call load_palette for each palette name.
        Expectation: Non-empty list of strings returned.
        """
        colors = load_palette(name)
        assert isinstance(colors, list)
        assert len(colors) > 0
        assert all(isinstance(c, str) for c in colors)

    def test_load_palette_returns_hex_strings(self) -> None:
        """
        Description: Loaded colours must be hex strings.
        Scenario: Load okabe_ito.
        Expectation: Each colour starts with '#'.
        """
        colors = load_palette("okabe_ito")
        for c in colors:
            assert c.startswith("#")

    def test_load_palette_caches_result(self) -> None:
        """
        Description: Second call must return the cached object identity.
        Scenario: Load twice.
        Expectation: Same list object (is check).
        """
        first = load_palette("okabe_ito")
        second = load_palette("okabe_ito")
        assert first is second

    def test_load_palette_cache_populated(self) -> None:
        """
        Description: After loading, the name must appear in the cache.
        Scenario: Load and check _palette_cache.
        Expectation: Key present.
        """
        load_palette("tol_bright")
        assert "tol_bright" in _palette_cache

    def test_load_palette_unknown_name_raises(self) -> None:
        """
        Description: Non-existent palette must raise PaletteNotFoundError.
        Scenario: load_palette('nonexistent_palette_xyz').
        Expectation: PaletteNotFoundError raised.
        """
        with pytest.raises(PaletteNotFoundError):
            load_palette("nonexistent_palette_xyz")

    def test_load_palette_error_message_lists_available(self) -> None:
        """
        Description: Error message must list available palettes for guidance.
        Scenario: Trigger PaletteNotFoundError and inspect message.
        Expectation: At least one known palette name appears.
        """
        with pytest.raises(PaletteNotFoundError, match="okabe-ito"):
            load_palette("no_such_palette")

    def test_load_palette_error_message_contains_palette_name(self) -> None:
        """
        Description: Error message must include the requested palette name.
        Scenario: load_palette('bad_name').
        Expectation: 'bad_name' in str(error).
        """
        with pytest.raises(PaletteNotFoundError, match="bad_name"):
            load_palette("bad_name")

    def test_load_palette_error_is_file_not_found(self) -> None:
        """
        Description: PaletteNotFoundError must be catchable as FileNotFoundError.
        Scenario: Catch as FileNotFoundError.
        Expectation: No uncaught exception.
        """
        with pytest.raises(FileNotFoundError):
            load_palette("no_such")

    def test_load_palette_missing_colors_key_raises(self, tmp_path: Path) -> None:
        """
        Description: A JSON file without 'colors' key must raise KeyError.
        Scenario: Provide a JSON file lacking the key.
        Expectation: KeyError raised.
        """
        bad_json = tmp_path / "bad_palette.json"
        bad_json.write_text('{"name": "bad"}', encoding="utf-8")
        with patch("plotstyle.color.palettes._DATA_DIR", tmp_path):
            _palette_cache.clear()
            with pytest.raises(KeyError):
                load_palette("bad_palette")

    def test_load_palette_malformed_json_raises(self, tmp_path: Path) -> None:
        """
        Description: A malformed JSON file must raise JSONDecodeError.
        Scenario: Provide a file with invalid JSON.
        Expectation: json.JSONDecodeError raised.
        """
        bad_json = tmp_path / "broken.json"
        bad_json.write_text("{not valid json", encoding="utf-8")
        with patch("plotstyle.color.palettes._DATA_DIR", tmp_path):
            _palette_cache.clear()
            with pytest.raises(json.JSONDecodeError):
                load_palette("broken")

    def test_load_palette_coerces_values_to_strings(self, tmp_path: Path) -> None:
        """
        Description: Non-string color values in JSON must be coerced to str.
        Scenario: JSON with integer colour values.
        Expectation: Returned list contains strings.
        """
        test_json = tmp_path / "int_colors.json"
        test_json.write_text('{"colors": [16711680, 65280]}', encoding="utf-8")
        with patch("plotstyle.color.palettes._DATA_DIR", tmp_path):
            _palette_cache.clear()
            colors = load_palette("int_colors")
            assert all(isinstance(c, str) for c in colors)


# ---------------------------------------------------------------------------
# palette() function tests
# ---------------------------------------------------------------------------


class TestPalette:
    """Validate the high-level palette retrieval function."""

    @pytest.mark.parametrize("journal", ALL_JOURNALS)
    def test_palette_returns_colors_for_all_journals(self, journal: str) -> None:
        """
        Description: palette() must work for every known journal.
        Scenario: Call palette(journal) with default n.
        Expectation: Non-empty list returned.
        """
        result = palette(journal)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_palette_returns_n_colors(self) -> None:
        """
        Description: The returned list must have exactly n elements.
        Scenario: palette('nature', n=4).
        Expectation: len == 4.
        """
        colors = palette("nature", n=4)
        assert len(colors) == 4

    def test_palette_default_n_returns_full_palette(self) -> None:
        """
        Description: Default n must return all colours in the underlying palette.
        Scenario: palette('nature') without explicit n.
        Expectation: len equals the full palette size.
        """
        colors = palette("nature")
        base = load_palette(JOURNAL_PALETTE_MAP["nature"])
        assert len(colors) == len(base)

    @pytest.mark.parametrize("n", [1, 2, 3, 5, 8, 10])
    def test_palette_various_n_values(self, n: int) -> None:
        """
        Description: palette() must return exactly n colours for various counts.
        Scenario: Parametric sweep of n values.
        Expectation: len == n.
        """
        colors = palette("nature", n=n)
        assert len(colors) == n

    def test_palette_cycles_when_n_exceeds_length(self) -> None:
        """
        Description: When n > palette length, colours must cycle.
        Scenario: palette('nature', n=20) for an 8-colour palette.
        Expectation: len == 20; colors cycle correctly.
        """
        colors = palette("nature", n=20)
        assert len(colors) == 20
        base = load_palette(JOURNAL_PALETTE_MAP["nature"])
        for i, c in enumerate(colors):
            assert c == base[i % len(base)]

    def test_palette_n_equals_one_returns_first_color(self) -> None:
        """
        Description: n=1 must return the first colour in the palette.
        Scenario: palette('nature', n=1).
        Expectation: Single element matching first colour.
        """
        colors = palette("nature", n=1)
        base = load_palette(JOURNAL_PALETTE_MAP["nature"])
        assert colors == [base[0]]

    def test_palette_case_insensitive_journal(self) -> None:
        """
        Description: Journal identifiers must be case-insensitive.
        Scenario: 'Nature', 'NATURE', 'nature' all produce the same result.
        Expectation: Identical output.
        """
        lower = palette("nature", n=4)
        upper = palette("NATURE", n=4)
        title = palette("Nature", n=4)
        assert lower == upper == title

    def test_palette_n_zero_raises_value_error(self) -> None:
        """
        Description: n=0 is not a positive integer and must raise ValueError.
        Scenario: palette('nature', n=0).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError, match="positive"):
            palette("nature", n=0)

    def test_palette_negative_n_raises_value_error(self) -> None:
        """
        Description: Negative n must raise ValueError.
        Scenario: palette('nature', n=-3).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            palette("nature", n=-3)

    def test_palette_unknown_journal_raises(self) -> None:
        """
        Description: Unknown journal must raise SpecNotFoundError.
        Scenario: palette('nonexistent').
        Expectation: SpecNotFoundError raised.
        """
        with pytest.raises(SpecNotFoundError):
            palette("nonexistent")

    def test_palette_unknown_journal_error_lists_known(self) -> None:
        """
        Description: Error message must list known journal identifiers.
        Scenario: Trigger SpecNotFoundError and inspect message.
        Expectation: At least one known journal in the message.
        """
        with pytest.raises(SpecNotFoundError, match="nature"):
            palette("fake_journal")

    def test_palette_unknown_journal_error_contains_input(self) -> None:
        """
        Description: Error message must include the invalid journal name.
        Scenario: palette('FakeJournal').
        Expectation: 'FakeJournal' in str(error).
        """
        with pytest.raises(SpecNotFoundError, match="FakeJournal"):
            palette("FakeJournal")

    def test_palette_unknown_journal_catchable_as_key_error(self) -> None:
        """
        Description: SpecNotFoundError must be catchable as KeyError.
        Scenario: Catch as KeyError.
        Expectation: No uncaught exception.
        """
        with pytest.raises(KeyError):
            palette("nope")


# ---------------------------------------------------------------------------
# palette() with_markers mode
# ---------------------------------------------------------------------------


class TestPaletteWithMarkers:
    """Validate the with_markers=True return format."""

    def test_with_markers_returns_tuples(self) -> None:
        """
        Description: with_markers=True must return a list of 3-tuples.
        Scenario: palette('nature', n=3, with_markers=True).
        Expectation: Each element is a tuple of length 3.
        """
        result = palette("nature", n=3, with_markers=True)
        assert len(result) == 3
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 3

    def test_with_markers_tuple_structure(self) -> None:
        """
        Description: Each tuple must contain (colour, linestyle, marker).
        Scenario: Inspect first element.
        Expectation: colour is hex, linestyle in _LINESTYLES, marker in _MARKERS.
        """
        result = palette("nature", n=1, with_markers=True)
        color, ls, marker = result[0]
        assert isinstance(color, str) and color.startswith("#")
        assert ls in _LINESTYLES
        assert marker in _MARKERS

    def test_with_markers_linestyles_cycle(self) -> None:
        """
        Description: Line styles must cycle through _LINESTYLES.
        Scenario: Request more items than linestyles.
        Expectation: Styles repeat modularly.
        """
        n = len(_LINESTYLES) + 2
        result = palette("nature", n=n, with_markers=True)
        for i, (_, ls, _) in enumerate(result):
            assert ls == _LINESTYLES[i % len(_LINESTYLES)]

    def test_with_markers_markers_cycle(self) -> None:
        """
        Description: Markers must cycle through _MARKERS.
        Scenario: Request more items than markers.
        Expectation: Markers repeat modularly.
        """
        n = len(_MARKERS) + 2
        result = palette("nature", n=n, with_markers=True)
        for i, (_, _, marker) in enumerate(result):
            assert marker == _MARKERS[i % len(_MARKERS)]

    def test_with_markers_false_returns_flat_list(self) -> None:
        """
        Description: with_markers=False must return plain hex strings.
        Scenario: palette('nature', n=3, with_markers=False).
        Expectation: Each element is a string.
        """
        result = palette("nature", n=3, with_markers=False)
        for item in result:
            assert isinstance(item, str)

    def test_with_markers_n_one(self) -> None:
        """
        Description: with_markers=True and n=1 must return a single tuple.
        Scenario: palette('ieee', n=1, with_markers=True).
        Expectation: One-element list with a 3-tuple.
        """
        result = palette("ieee", n=1, with_markers=True)
        assert len(result) == 1
        assert isinstance(result[0], tuple)

    def test_with_markers_large_n_cycles_all_three(self) -> None:
        """
        Description: Large n must cycle colours, linestyles, and markers independently.
        Scenario: palette('nature', n=30, with_markers=True).
        Expectation: 30 tuples; each component cycles independently.
        """
        result = palette("nature", n=30, with_markers=True)
        assert len(result) == 30
        base = load_palette(JOURNAL_PALETTE_MAP["nature"])
        for i, (color, ls, marker) in enumerate(result):
            assert color == base[i % len(base)]
            assert ls == _LINESTYLES[i % len(_LINESTYLES)]
            assert marker == _MARKERS[i % len(_MARKERS)]


# ---------------------------------------------------------------------------
# _build_not_found_message (via load_palette error path)
# ---------------------------------------------------------------------------


class TestBuildNotFoundMessage:
    """Validate the error message generation for missing palettes."""

    def test_message_lists_available_palettes(self) -> None:
        """
        Description: Error message must enumerate available palette files.
        Scenario: Trigger PaletteNotFoundError.
        Expectation: Known palette stems appear in message.
        """
        with pytest.raises(PaletteNotFoundError) as exc_info:
            load_palette("totally_missing")
        msg = str(exc_info.value)
        for name in ALL_PALETTE_NAMES:
            # Error message uses kebab-case (okabe-ito), not underscore (okabe_ito)
            assert name.replace("_", "-") in msg

    def test_message_when_no_palettes_exist(self, tmp_path: Path) -> None:
        """
        Description: When no JSON files exist, message should say '(none)'.
        Scenario: Point _DATA_DIR to an empty directory.
        Expectation: '(none)' in the error message.
        """
        with patch("plotstyle.color.palettes._DATA_DIR", tmp_path):
            _palette_cache.clear()
            with pytest.raises(PaletteNotFoundError, match=r"\(none\)"):
                load_palette("anything")


# ---------------------------------------------------------------------------
# Linestyle and marker constants
# ---------------------------------------------------------------------------


class TestStyleConstants:
    """Validate the linestyle and marker sequences."""

    def test_linestyles_are_non_empty(self) -> None:
        """
        Description: _LINESTYLES must contain at least one element.
        Scenario: Check length.
        Expectation: len > 0.
        """
        assert len(_LINESTYLES) > 0

    def test_markers_are_non_empty(self) -> None:
        """
        Description: _MARKERS must contain at least one element.
        Scenario: Check length.
        Expectation: len > 0.
        """
        assert len(_MARKERS) > 0

    def test_linestyles_are_strings(self) -> None:
        """
        Description: Each linestyle must be a string.
        Scenario: Type-check each element.
        Expectation: isinstance str.
        """
        for ls in _LINESTYLES:
            assert isinstance(ls, str)

    def test_markers_are_strings(self) -> None:
        """
        Description: Each marker must be a string.
        Scenario: Type-check each element.
        Expectation: isinstance str.
        """
        for m in _MARKERS:
            assert isinstance(m, str)

    def test_linestyles_are_tuples(self) -> None:
        """
        Description: Constant sequences must be immutable tuples.
        Scenario: Type-check the container.
        Expectation: isinstance tuple.
        """
        assert isinstance(_LINESTYLES, tuple)
        assert isinstance(_MARKERS, tuple)
