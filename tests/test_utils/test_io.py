"""Comprehensive test suite for plotstyle._utils.io.

Covers: load_toml() — happy paths, nested structures, edge cases, and every
documented error condition.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from plotstyle._utils.io import load_toml

# ---------------------------------------------------------------------------
# Import the correct TOML decoder for TOMLDecodeError reference
# ---------------------------------------------------------------------------

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import,no-redef]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_toml_file(tmp_path: Path) -> Path:
    """Write a minimal valid TOML file and return its path."""
    p = tmp_path / "valid.toml"
    p.write_bytes(
        b'[metadata]\nname = "Test"\nvalue = 42\n',
        # explicit binary write — matches load_toml's open mode
    )
    return p


@pytest.fixture
def nested_toml_file(tmp_path: Path) -> Path:
    """Write a TOML file with nested tables, arrays, and diverse types."""
    content = """\
[section_a]
integer = 1
float_val = 3.14
boolean = true
string = "hello"

[section_a.nested]
key = "deep"

[section_b]
array = [1, 2, 3]
"""
    p = tmp_path / "nested.toml"
    p.write_bytes(content.encode("utf-8"))
    return p


@pytest.fixture
def unicode_toml_file(tmp_path: Path) -> Path:
    """Write a TOML file containing Unicode characters."""
    content = '[labels]\ntitle = "Größe der Daten (Ångström)"\n'
    p = tmp_path / "unicode.toml"
    p.write_bytes(content.encode("utf-8"))
    return p


@pytest.fixture
def empty_toml_file(tmp_path: Path) -> Path:
    """Write an empty (zero-byte) TOML file."""
    p = tmp_path / "empty.toml"
    p.write_bytes(b"")
    return p


@pytest.fixture
def invalid_toml_file(tmp_path: Path) -> Path:
    """Write a TOML file with a syntax error."""
    p = tmp_path / "invalid.toml"
    p.write_bytes(b"[unclosed [[[ bracket\n")
    return p


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


class TestLoadTomlHappyPath:
    """Validate correct parsing of well-formed TOML files."""

    def test_returns_dict_for_valid_file(self, valid_toml_file: Path) -> None:
        """
        Description: load_toml must return a dict for all valid TOML files.
        Scenario: Valid TOML file with one table containing a string and int.
        Expectation: Returns dict; top-level key 'metadata' is present.
        """
        result = load_toml(valid_toml_file)
        assert isinstance(result, dict)
        assert "metadata" in result

    def test_string_values_are_str(self, valid_toml_file: Path) -> None:
        """
        Description: TOML strings must be parsed as Python str objects.
        Scenario: TOML file contains name = "Test".
        Expectation: result['metadata']['name'] == 'Test'.
        """
        result = load_toml(valid_toml_file)
        assert result["metadata"]["name"] == "Test"
        assert isinstance(result["metadata"]["name"], str)

    def test_integer_values_are_int(self, valid_toml_file: Path) -> None:
        """
        Description: TOML integers must be parsed as Python int objects.
        Scenario: TOML file contains value = 42.
        Expectation: result['metadata']['value'] == 42 and is int.
        """
        result = load_toml(valid_toml_file)
        assert result["metadata"]["value"] == 42
        assert isinstance(result["metadata"]["value"], int)

    def test_nested_tables_become_nested_dicts(self, nested_toml_file: Path) -> None:
        """
        Description: Nested TOML tables must map to nested Python dicts.
        Scenario: TOML with [section_a.nested] sub-table.
        Expectation: result['section_a']['nested']['key'] == 'deep'.
        """
        result = load_toml(nested_toml_file)
        assert result["section_a"]["nested"]["key"] == "deep"

    def test_float_values_are_float(self, nested_toml_file: Path) -> None:
        """
        Description: TOML floats must be parsed as Python float.
        Scenario: TOML file contains float_val = 3.14.
        Expectation: result['section_a']['float_val'] ≈ 3.14 and is float.
        """
        result = load_toml(nested_toml_file)
        assert result["section_a"]["float_val"] == pytest.approx(3.14)
        assert isinstance(result["section_a"]["float_val"], float)

    def test_boolean_values_are_bool(self, nested_toml_file: Path) -> None:
        """
        Description: TOML booleans must be parsed as Python bool.
        Scenario: TOML file contains boolean = true.
        Expectation: result['section_a']['boolean'] is True.
        """
        result = load_toml(nested_toml_file)
        assert result["section_a"]["boolean"] is True

    def test_arrays_become_python_lists(self, nested_toml_file: Path) -> None:
        """
        Description: TOML arrays must be parsed as Python list.
        Scenario: TOML file contains array = [1, 2, 3].
        Expectation: result['section_b']['array'] == [1, 2, 3].
        """
        result = load_toml(nested_toml_file)
        assert result["section_b"]["array"] == [1, 2, 3]
        assert isinstance(result["section_b"]["array"], list)

    def test_empty_file_returns_empty_dict(self, empty_toml_file: Path) -> None:
        """
        Description: An empty TOML file contains no key-value pairs; the
        result must be an empty dict, not None or an error.
        Scenario: Zero-byte TOML file on disk.
        Expectation: Returns {}.
        """
        result = load_toml(empty_toml_file)
        assert result == {}

    def test_unicode_strings_are_preserved(self, unicode_toml_file: Path) -> None:
        """
        Description: UTF-8 encoded Unicode characters must survive round-trip
        parsing without corruption — important for journal names and author metadata.
        Scenario: TOML file with German Umlauts and special scientific symbols.
        Expectation: Decoded string matches the original Unicode content.
        """
        result = load_toml(unicode_toml_file)
        assert "Größe" in result["labels"]["title"]
        assert "Ångström" in result["labels"]["title"]

    def test_can_load_real_pyproject_toml(self) -> None:
        """
        Description: The repository's own pyproject.toml must be loadable,
        providing an integration smoke test against a real-world TOML file.
        Scenario: Resolve pyproject.toml relative to this test file's location.
        Expectation: Returns dict with 'project' key whose 'name' is 'plotstyle'.
        """
        repo_root = Path(__file__).parent.parent.parent
        pyproject = repo_root / "pyproject.toml"
        result = load_toml(pyproject)
        assert result["project"]["name"] == "plotstyle"

    def test_multiple_sections_all_present(self, nested_toml_file: Path) -> None:
        """
        Description: All top-level TOML tables must appear in the result dict.
        Scenario: TOML file with two top-level tables.
        Expectation: Both 'section_a' and 'section_b' are keys in the result.
        """
        result = load_toml(nested_toml_file)
        assert "section_a" in result
        assert "section_b" in result


# ---------------------------------------------------------------------------
# Error / failure paths
# ---------------------------------------------------------------------------


class TestLoadTomlErrors:
    """Validate load_toml behaviour for invalid and missing inputs."""

    def test_file_not_found_raises_file_not_found_error(self, tmp_path: Path) -> None:
        """
        Description: Requesting a non-existent file must raise FileNotFoundError
        so that callers can distinguish missing-file from parse errors.
        Scenario: Pass a path that does not exist on disk.
        Expectation: FileNotFoundError raised.
        """
        missing = tmp_path / "does_not_exist.toml"
        with pytest.raises(FileNotFoundError):
            load_toml(missing)

    def test_directory_raises_is_a_directory_error(self, tmp_path: Path) -> None:
        """
        Description: Passing a directory path instead of a file must raise
        IsADirectoryError (or OSError on Windows), reflecting the OS semantics.
        Scenario: Pass a path that points to a directory.
        Expectation: IsADirectoryError (or PermissionError/OSError) raised.
        """
        with pytest.raises((IsADirectoryError, PermissionError, OSError)):
            load_toml(tmp_path)

    def test_invalid_toml_raises_toml_decode_error(self, invalid_toml_file: Path) -> None:
        """
        Description: Syntactically invalid TOML must raise TOMLDecodeError so
        that callers receive a meaningful parse-level error rather than a generic
        exception.
        Scenario: Write a file containing malformed TOML syntax.
        Expectation: tomllib.TOMLDecodeError raised.
        """
        with pytest.raises(tomllib.TOMLDecodeError):
            load_toml(invalid_toml_file)

    @pytest.mark.parametrize(
        "bad_content",
        [
            b"key = {unclosed",  # unclosed inline table
            b"[section\nkey = 1",  # unclosed table header
            b'string = "unterminated',  # unterminated string
            b"[dup]\n[dup]\n",  # duplicate table
        ],
    )
    def test_various_syntax_errors_raise_toml_decode_error(
        self, tmp_path: Path, bad_content: bytes
    ) -> None:
        """
        Description: Multiple categories of TOML syntax errors must all result
        in TOMLDecodeError — not generic Python exceptions.
        Scenario: Write each malformed content variant and attempt to load it.
        Expectation: TOMLDecodeError raised for each variant.
        """
        bad_file = tmp_path / "bad.toml"
        bad_file.write_bytes(bad_content)
        with pytest.raises(tomllib.TOMLDecodeError):
            load_toml(bad_file)

    def test_valid_path_returns_deterministic_result(self, valid_toml_file: Path) -> None:
        """
        Description: Calling load_toml twice on the same file must return equal
        dicts (deterministic; no mutable state between calls).
        Scenario: Load the same valid TOML file twice consecutively.
        Expectation: Both results are equal.
        """
        result1 = load_toml(valid_toml_file)
        result2 = load_toml(valid_toml_file)
        assert result1 == result2


# ---------------------------------------------------------------------------
# Cross-platform / encoding
# ---------------------------------------------------------------------------


class TestLoadTomlCrossPlatform:
    """Validate cross-platform file handling."""

    def test_pathlib_path_accepted(self, valid_toml_file: Path) -> None:
        """
        Description: The function must accept pathlib.Path objects (not just
        str) for cross-platform compatibility.
        Scenario: Pass a pathlib.Path directly.
        Expectation: No TypeError; returns a dict.
        """
        assert isinstance(valid_toml_file, Path)
        result = load_toml(valid_toml_file)
        assert isinstance(result, dict)

    def test_nested_directory_path_works(self, tmp_path: Path) -> None:
        """
        Description: Paths under nested directories must work on all platforms
        without requiring OS-specific separators.
        Scenario: Create a file inside a nested subdirectory via pathlib.
        Expectation: File is found and parsed without error.
        """
        sub = tmp_path / "a" / "b" / "c"
        sub.mkdir(parents=True)
        p = sub / "spec.toml"
        p.write_bytes(b'[data]\nkey = "value"\n')
        result = load_toml(p)
        assert result["data"]["key"] == "value"

    def test_file_with_non_ascii_path_component(self, tmp_path: Path) -> None:
        """
        Description: File paths containing non-ASCII directory names must be
        handled correctly; Unicode file systems are common on macOS and Linux.
        Scenario: Create a file in a directory whose name contains a non-ASCII
        character (using a safe ASCII fallback if the filesystem rejects it).
        Expectation: If the OS allows it, the file loads without error.
        """
        try:
            sub = tmp_path / "données"
            sub.mkdir(exist_ok=True)
            p = sub / "config.toml"
            p.write_bytes(b"[x]\nval = 1\n")
            result = load_toml(p)
            assert result["x"]["val"] == 1
        except (OSError, UnicodeEncodeError):
            # Some CI filesystems reject non-ASCII paths — skip gracefully.
            pytest.skip("Filesystem does not support non-ASCII directory names.")
