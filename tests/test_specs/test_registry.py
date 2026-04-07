"""Enhanced test suite for plotstyle.specs.

Covers: SpecRegistry, SpecNotFoundError, and the module-level singleton.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from plotstyle.specs import SpecNotFoundError, SpecRegistry
from plotstyle.specs.schema import JournalSpec

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Minimal valid TOML content for synthetic test specs
# ---------------------------------------------------------------------------

_MINIMAL_TOML = """\
[metadata]
name = "Synthetic Journal"
publisher = "Test Publisher"
source_url = "https://example.com"
last_verified = "2024-01-15"
verified_by = "tester"

[dimensions]
single_column_mm = 89.0
double_column_mm = 183.0
max_height_mm = 247.0

[typography]
font_family = ["Helvetica"]
min_font_pt = 7.0
max_font_pt = 9.0

[export]
preferred_formats = ["pdf"]
min_dpi = 300
color_space = "rgb"
font_embedding = true
editable_text = false
"""

_ALTERNATE_TOML = """\
[metadata]
name = "Alternate Journal"
publisher = "Alt Publisher"
source_url = "https://alt.example.com"
last_verified = "2024-06-01"
verified_by = "tester2"

[dimensions]
single_column_mm = 90.0
double_column_mm = 190.0
max_height_mm = 260.0

[typography]
font_family = ["Arial"]
min_font_pt = 6.0
max_font_pt = 10.0

[export]
preferred_formats = ["eps", "tiff"]
min_dpi = 600
color_space = "cmyk"
font_embedding = true
editable_text = true
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_specs_dir(tmp_path: Path) -> Path:
    """
    A temporary specs directory with two public and one private TOML files.
    Provides an isolated environment for registry tests.
    """
    (tmp_path / "alpha.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
    (tmp_path / "beta.toml").write_text(_ALTERNATE_TOML, encoding="utf-8")
    (tmp_path / "_private.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
    return tmp_path


@pytest.fixture
def reg(tmp_specs_dir: Path) -> SpecRegistry:
    """Fresh SpecRegistry pointing at the temporary specs directory."""
    return SpecRegistry(specs_dir=tmp_specs_dir)


@pytest.fixture
def empty_specs_dir(tmp_path: Path) -> Path:
    """An empty temporary specs directory with no TOML files."""
    return tmp_path


@pytest.fixture
def single_spec_dir(tmp_path: Path) -> Path:
    """A temporary specs directory containing exactly one public TOML file."""
    (tmp_path / "solo.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
    return tmp_path


@pytest.fixture
def only_private_specs_dir(tmp_path: Path) -> Path:
    """A temporary specs directory with only underscore-prefixed (private) TOMLs."""
    (tmp_path / "_internal.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
    (tmp_path / "_base.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
    return tmp_path


@pytest.fixture
def mixed_files_dir(tmp_path: Path) -> Path:
    """
    A specs directory containing TOML files alongside non-TOML files.
    Tests that list_available() ignores irrelevant file types.
    """
    (tmp_path / "gamma.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
    (tmp_path / "README.md").write_text("# Specs", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("some notes", encoding="utf-8")
    (tmp_path / "schema.json").write_text("{}", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# TestSpecNotFoundError
# ---------------------------------------------------------------------------


class TestSpecNotFoundError:
    def test_is_subclass_of_key_error(self):
        """
        Description: Validates the inheritance chain of SpecNotFoundError.
        Scenario: Instantiate SpecNotFoundError with a name and available list.
        Expectation: The exception is an instance of KeyError.
        """
        err = SpecNotFoundError("foo", ["acs", "nature"])
        assert isinstance(err, KeyError)

    def test_is_subclass_of_exception(self):
        """
        Description: Ensures SpecNotFoundError is a proper Exception subtype.
        Scenario: Instantiate SpecNotFoundError and check MRO.
        Expectation: isinstance check against Exception returns True.
        """
        err = SpecNotFoundError("foo", [])
        assert isinstance(err, Exception)

    def test_name_attribute_stored_correctly(self):
        """
        Description: Validates the .name attribute is stored as provided.
        Scenario: Create error with name='foo'.
        Expectation: err.name == 'foo'.
        """
        err = SpecNotFoundError("foo", ["acs"])
        assert err.name == "foo"

    def test_available_attribute_stored_correctly(self):
        """
        Description: Validates the .available attribute is stored as provided.
        Scenario: Create error with available=['acs', 'nature'].
        Expectation: err.available equals the provided list.
        """
        err = SpecNotFoundError("foo", ["acs", "nature"])
        assert err.available == ["acs", "nature"]

    def test_empty_available_list_stored(self):
        """
        Description: Validates that an empty available list is stored faithfully.
        Scenario: Pass an empty list for available.
        Expectation: err.available == [].
        """
        err = SpecNotFoundError("foo", [])
        assert err.available == []

    def test_str_contains_requested_name(self):
        """
        Description: Ensures the human-readable message includes the unknown name.
        Scenario: Create SpecNotFoundError with name='missing'.
        Expectation: 'missing' appears in str(err).
        """
        err = SpecNotFoundError("missing", ["acs"])
        assert "missing" in str(err)

    def test_str_contains_available_journals(self):
        """
        Description: Ensures the error message lists available journals.
        Scenario: Create error with available=['acs', 'nature'].
        Expectation: Both names appear in the string representation.
        """
        err = SpecNotFoundError("missing", ["acs", "nature"])
        msg = str(err)
        assert "acs" in msg
        assert "nature" in msg

    def test_str_contains_none_when_available_empty(self):
        """
        Description: Validates fallback text when no journals are available.
        Scenario: Create error with an empty available list.
        Expectation: The message contains '(none)' as the fallback.
        """
        err = SpecNotFoundError("missing", [])
        assert "(none)" in str(err)

    def test_catchable_as_key_error(self, reg):
        """
        Description: Verifies backward compatibility — handlers catching KeyError
                     still work when SpecNotFoundError is raised.
        Scenario: Call reg.get() with a nonexistent journal inside an
                  'except KeyError' block.
        Expectation: The exception is caught without modification.
        """
        with pytest.raises(KeyError):
            reg.get("nonexistent")

    def test_catchable_as_spec_not_found_error(self, reg):
        """
        Description: Verifies that SpecNotFoundError can be caught by its own type.
        Scenario: Call reg.get() with a nonexistent journal.
        Expectation: SpecNotFoundError is raised and caught correctly.
        """
        with pytest.raises(SpecNotFoundError):
            reg.get("nonexistent")

    @pytest.mark.parametrize("name", ["", "  ", "123", "journal-with-dashes"])
    def test_arbitrary_names_stored_verbatim(self, name: str):
        """
        Description: Validates that SpecNotFoundError stores any string name as-is.
        Scenario: Create error with various unusual name strings.
        Expectation: err.name equals the exact string passed.
        """
        err = SpecNotFoundError(name, [])
        assert err.name == name


# ---------------------------------------------------------------------------
# TestListAvailable
# ---------------------------------------------------------------------------


class TestListAvailable:
    def test_returns_sorted_list(self, reg):
        """
        Description: Validates that list_available() returns alphabetically sorted names.
        Scenario: Registry with 'alpha' and 'beta' files.
        Expectation: Result equals its own sorted version.
        """
        names = reg.list_available()
        assert names == sorted(names)

    def test_returns_only_toml_stems(self, reg):
        """
        Description: Validates that only .toml file stems are returned.
        Scenario: Directory contains alpha.toml, beta.toml, _private.toml.
        Expectation: Result is exactly ['alpha', 'beta'].
        """
        names = reg.list_available()
        assert names == ["alpha", "beta"]

    def test_excludes_underscore_prefixed_files(self, reg):
        """
        Description: Validates that private (_-prefixed) specs are excluded.
        Scenario: Directory contains _private.toml alongside public specs.
        Expectation: '_private' is not in the returned list.
        """
        assert "_private" not in reg.list_available()

    def test_empty_directory_returns_empty_list(self, empty_specs_dir):
        """
        Description: Validates behavior when no TOML files exist.
        Scenario: Empty specs directory.
        Expectation: list_available() returns an empty list (not an error).
        """
        reg = SpecRegistry(specs_dir=empty_specs_dir)
        assert reg.list_available() == []

    def test_only_private_files_returns_empty_list(self, only_private_specs_dir):
        """
        Description: Validates that a directory with only private TOMLs is
                     treated as effectively empty.
        Scenario: Directory with only _internal.toml and _base.toml.
        Expectation: list_available() returns [].
        """
        reg = SpecRegistry(specs_dir=only_private_specs_dir)
        assert reg.list_available() == []

    def test_ignores_non_toml_files(self, mixed_files_dir):
        """
        Description: Validates that non-.toml files (README.md, notes.txt, etc.)
                     are not included in available specs.
        Scenario: Directory with a mix of .toml and other file types.
        Expectation: Only 'gamma' (the .toml stem) is returned.
        """
        reg = SpecRegistry(specs_dir=mixed_files_dir)
        assert reg.list_available() == ["gamma"]

    def test_inaccessible_directory_raises_file_not_found_error(self, tmp_path):
        """
        Description: Validates that an inaccessible specs directory raises
                     FileNotFoundError rather than OSError or a silent failure.
        Scenario: Registry pointed at a nonexistent subdirectory.
        Expectation: FileNotFoundError is raised on list_available().
        """
        missing = tmp_path / "nonexistent_dir"
        reg = SpecRegistry(specs_dir=missing)
        with pytest.raises(FileNotFoundError):
            reg.list_available()

    def test_single_spec_directory(self, single_spec_dir):
        """
        Description: Validates behavior with exactly one public spec file.
        Scenario: Directory contains only solo.toml.
        Expectation: list_available() returns ['solo'].
        """
        reg = SpecRegistry(specs_dir=single_spec_dir)
        assert reg.list_available() == ["solo"]

    def test_returns_list_type(self, reg):
        """
        Description: Validates that the return type is a list, not a generator
                     or other iterable.
        Scenario: Normal registry with specs.
        Expectation: isinstance(..., list) is True.
        """
        result = reg.list_available()
        assert isinstance(result, list)

    def test_returns_lowercase_stems(self, tmp_path):
        """
        Description: Validates that file stems are returned in lower-case.
        Scenario: TOML file named 'gamma.toml' (already lowercase).
        Expectation: The stem 'gamma' is returned (not uppercase variant).
        """
        (tmp_path / "gamma.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
        reg = SpecRegistry(specs_dir=tmp_path)
        assert "gamma" in reg.list_available()

    def test_multiple_calls_are_consistent(self, reg):
        """
        Description: Validates that repeated calls to list_available() return
                     the same result (no side-effects or state mutation).
        Scenario: Call list_available() twice in succession.
        Expectation: Both calls return identical results.
        """
        first = reg.list_available()
        second = reg.list_available()
        assert first == second

    def test_default_registry_includes_known_journals(self):
        """
        Description: Integration smoke-test that the built-in specs directory
                     is readable and contains expected journals.
        Scenario: Use the module-level default registry.
        Expectation: 'acs', 'ieee', 'nature' are all available.
        """
        from plotstyle.specs import registry as default_reg

        available = default_reg.list_available()
        for expected in ("acs", "ieee", "nature"):
            assert expected in available

    def test_default_registry_excludes_templates(self):
        """
        Description: Validates that internal template files starting with
                     underscores are not exposed via the default registry.
        Scenario: Use the module-level default registry.
        Expectation: '_templates' (or similar) is not in list_available().
        """
        from plotstyle.specs import registry as default_reg

        assert "_templates" not in default_reg.list_available()

    def test_default_registry_all_stems_are_strings(self):
        """
        Description: Validates all entries returned by the default registry
                     are proper strings (not Path objects or other types).
        Scenario: Call list_available() on the default registry.
        Expectation: Every element is a str instance.
        """
        from plotstyle.specs import registry as default_reg

        for name in default_reg.list_available():
            assert isinstance(name, str)


# ---------------------------------------------------------------------------
# TestGet
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_returns_journal_spec_instance(self, reg):
        """
        Description: Validates the return type of get().
        Scenario: Request a known journal by name.
        Expectation: Returns a JournalSpec instance.
        """
        spec = reg.get("alpha")
        assert isinstance(spec, JournalSpec)

    def test_get_case_insensitive_uppercase(self, reg):
        """
        Description: Validates that get() is case-insensitive for uppercase input.
        Scenario: Call get('ALPHA') where alpha.toml exists.
        Expectation: Returns a JournalSpec without error.
        """
        spec = reg.get("ALPHA")
        assert isinstance(spec, JournalSpec)

    def test_get_case_insensitive_mixed(self, reg):
        """
        Description: Validates that get() is case-insensitive for mixed-case input.
        Scenario: Call get('Alpha').
        Expectation: Returns a JournalSpec without error.
        """
        spec = reg.get("Alpha")
        assert isinstance(spec, JournalSpec)

    def test_get_lowercase_and_uppercase_return_same_object(self, reg):
        """
        Description: Validates that case-insensitive normalisation results in
                     the exact same cached object being returned.
        Scenario: Call get('alpha') and get('ALPHA') in sequence.
        Expectation: Both return the identical (is) Python object.
        """
        spec_lower = reg.get("alpha")
        spec_upper = reg.get("ALPHA")
        assert spec_lower is spec_upper

    def test_get_mixed_case_returns_same_cached_object(self, reg):
        """
        Description: Validates cache identity across arbitrary case variants.
        Scenario: Call get() with 'alpha', 'ALPHA', and 'Alpha'.
        Expectation: All three return the exact same object.
        """
        a = reg.get("alpha")
        b = reg.get("ALPHA")
        c = reg.get("Alpha")
        assert a is b is c

    def test_get_unknown_name_raises_spec_not_found_error(self, reg):
        """
        Description: Validates the exception raised for an unknown journal name.
        Scenario: Call get('nonexistent') on a registry that doesn't have it.
        Expectation: SpecNotFoundError is raised.
        """
        with pytest.raises(SpecNotFoundError):
            reg.get("nonexistent")

    def test_get_unknown_name_error_has_correct_name_attr(self, reg):
        """
        Description: Validates that SpecNotFoundError carries the requested name.
        Scenario: Call get('nonexistent'), catch the error.
        Expectation: err.name == 'nonexistent'.
        """
        with pytest.raises(SpecNotFoundError) as exc_info:
            reg.get("nonexistent")
        assert exc_info.value.name == "nonexistent"

    def test_get_unknown_name_error_has_available_attr(self, reg):
        """
        Description: Validates that SpecNotFoundError carries available specs.
        Scenario: Call get('nonexistent'), catch the error.
        Expectation: err.available equals the list from list_available().
        """
        with pytest.raises(SpecNotFoundError) as exc_info:
            reg.get("nonexistent")
        assert exc_info.value.available == reg.list_available()

    @pytest.mark.parametrize("invalid_input", [42, 3.14, None, [], {}, object()])
    def test_get_non_string_raises_type_error(self, reg, invalid_input):
        """
        Description: Validates type-checking guard on get().
        Scenario: Pass a non-string value as the journal name.
        Expectation: TypeError is raised for each non-string type.
        """
        with pytest.raises(TypeError):
            reg.get(invalid_input)  # type: ignore[arg-type]

    def test_get_type_error_message_is_informative(self, reg):
        """
        Description: Validates that the TypeError message mentions the type received.
        Scenario: Call get(42).
        Expectation: TypeError message contains 'int'.
        """
        with pytest.raises(TypeError, match="int"):
            reg.get(42)  # type: ignore[arg-type]

    def test_get_parses_metadata_name_correctly(self, reg):
        """
        Description: Validates that metadata.name is correctly deserialized.
        Scenario: Load 'alpha' which maps to _MINIMAL_TOML.
        Expectation: spec.metadata.name == 'Synthetic Journal'.
        """
        spec = reg.get("alpha")
        assert spec.metadata.name == "Synthetic Journal"

    def test_get_parses_metadata_publisher_correctly(self, reg):
        """
        Description: Validates that metadata.publisher is correctly deserialized.
        Scenario: Load 'alpha'.
        Expectation: spec.metadata.publisher == 'Test Publisher'.
        """
        spec = reg.get("alpha")
        assert spec.metadata.publisher == "Test Publisher"

    def test_get_parses_dimensions_single_column(self, reg):
        """
        Description: Validates that dimensions.single_column_mm is parsed correctly.
        Scenario: Load 'alpha'.
        Expectation: Value equals 89.0.
        """
        spec = reg.get("alpha")
        assert spec.dimensions.single_column_mm == pytest.approx(89.0)

    def test_get_parses_dimensions_double_column(self, reg):
        """
        Description: Validates that dimensions.double_column_mm is parsed correctly.
        Scenario: Load 'alpha'.
        Expectation: Value equals 183.0.
        """
        spec = reg.get("alpha")
        assert spec.dimensions.double_column_mm == pytest.approx(183.0)

    def test_get_parses_dimensions_max_height(self, reg):
        """
        Description: Validates that dimensions.max_height_mm is parsed correctly.
        Scenario: Load 'alpha'.
        Expectation: Value equals 247.0.
        """
        spec = reg.get("alpha")
        assert spec.dimensions.max_height_mm == pytest.approx(247.0)

    def test_get_different_specs_have_different_data(self, reg):
        """
        Description: Validates that two different specs load distinct data.
        Scenario: Load 'alpha' and 'beta', each backed by different TOML.
        Expectation: Their metadata.name values differ.
        """
        alpha = reg.get("alpha")
        beta = reg.get("beta")
        assert alpha.metadata.name != beta.metadata.name

    def test_get_private_spec_by_name_with_underscore(self, tmp_specs_dir):
        """
        Description: Validates that _private.toml IS directly loadable by name
                     (since get() does a raw file lookup, not a filtered one).
                     Documents the intentional distinction from list_available().
        Scenario: Call get('_private') where _private.toml exists.
        Expectation: Returns a JournalSpec (private specs are not forbidden
                     from direct access, only excluded from listing).
        """
        reg = SpecRegistry(specs_dir=tmp_specs_dir)
        spec = reg.get("_private")
        assert isinstance(spec, JournalSpec)

    def test_get_real_nature_spec(self):
        """
        Description: Integration test validating the built-in Nature spec loads
                     and has correct key fields.
        Scenario: Use default SpecRegistry, load 'nature'.
        Expectation: metadata.name == 'Nature', single_column_mm ≈ 89.0.
        """
        reg = SpecRegistry()
        spec = reg.get("nature")
        assert spec.metadata.name == "Nature"
        assert spec.dimensions.single_column_mm == pytest.approx(89.0)

    def test_get_real_nature_spec_case_insensitive(self):
        """
        Description: Integration test validating case-insensitive lookup on
                     real built-in specs.
        Scenario: Call get('Nature') (mixed case) on the default registry.
        Expectation: Returns spec with metadata.name == 'Nature'.
        """
        reg = SpecRegistry()
        spec = reg.get("Nature")
        assert spec.metadata.name == "Nature"


# ---------------------------------------------------------------------------
# TestCaching
# ---------------------------------------------------------------------------


class TestCaching:
    def test_second_get_returns_same_object(self, reg):
        """
        Description: Validates that get() caches results and returns the same
                     Python object on subsequent calls (identity, not equality).
        Scenario: Call get('alpha') twice.
        Expectation: Both calls return the exact same object (is check).
        """
        first = reg.get("alpha")
        second = reg.get("alpha")
        assert first is second

    def test_cache_is_empty_before_any_get(self, tmp_specs_dir):
        """
        Description: Validates lazy-loading — nothing is cached at construction.
        Scenario: Create a fresh SpecRegistry without calling get().
        Expectation: Internal cache is empty.
        """
        reg = SpecRegistry(specs_dir=tmp_specs_dir)
        assert len(reg._cache) == 0

    def test_cache_grows_after_get(self, reg):
        """
        Description: Validates that get() populates the internal cache.
        Scenario: Call get('alpha') on a fresh registry.
        Expectation: 'alpha' is present in reg._cache after the call.
        """
        reg.get("alpha")
        assert "alpha" in reg._cache

    def test_cache_uses_lowercase_key(self, reg):
        """
        Description: Validates that the cache key is always lowercase regardless
                     of how the name was requested.
        Scenario: Call get('ALPHA').
        Expectation: The cache contains the key 'alpha', not 'ALPHA'.
        """
        reg.get("ALPHA")
        assert "alpha" in reg._cache
        assert "ALPHA" not in reg._cache

    def test_cache_does_not_grow_on_repeated_get(self, reg):
        """
        Description: Validates that repeated get() calls for the same spec do
                     not cause duplicate cache entries.
        Scenario: Call get('alpha') three times.
        Expectation: Cache size remains 1.
        """
        reg.get("alpha")
        reg.get("alpha")
        reg.get("alpha")
        assert len(reg._cache) == 1

    def test_cache_grows_independently_per_spec(self, reg):
        """
        Description: Validates that each distinct spec gets its own cache entry.
        Scenario: Call get('alpha') and get('beta').
        Expectation: Cache size is 2.
        """
        reg.get("alpha")
        reg.get("beta")
        assert len(reg._cache) == 2

    def test_clear_cache_empties_internal_dict(self, reg):
        """
        Description: Validates that clear_cache() wipes all cached entries.
        Scenario: Load 'alpha', then clear_cache().
        Expectation: reg._cache is empty afterward.
        """
        reg.get("alpha")
        reg.clear_cache()
        assert len(reg._cache) == 0

    def test_get_after_clear_cache_returns_new_object(self, reg):
        """
        Description: Validates that after clearing the cache, get() re-reads
                     from disk and returns a fresh object.
        Scenario: Load 'alpha', clear cache, load 'alpha' again.
        Expectation: The second object is NOT the same Python object (is not).
        """
        first = reg.get("alpha")
        reg.clear_cache()
        second = reg.get("alpha")
        assert first is not second

    def test_get_after_clear_cache_returns_equal_spec(self, reg):
        """
        Description: Validates that after cache clearing, the freshly loaded spec
                     has the same data as the original.
        Scenario: Load 'alpha', clear cache, load 'alpha' again.
        Expectation: Both specs have identical metadata.name.
        """
        first = reg.get("alpha")
        reg.clear_cache()
        second = reg.get("alpha")
        assert first.metadata.name == second.metadata.name

    def test_clear_cache_is_idempotent(self, reg):
        """
        Description: Validates that calling clear_cache() multiple times in a row
                     does not raise any errors.
        Scenario: Call clear_cache() three times consecutively.
        Expectation: No exception is raised.
        """
        reg.clear_cache()
        reg.clear_cache()
        reg.clear_cache()

    def test_clear_cache_on_empty_cache_does_not_raise(self, reg):
        """
        Description: Validates that clear_cache() is safe to call on a registry
                     that has never loaded any specs.
        Scenario: Fresh registry with no get() calls; call clear_cache().
        Expectation: No exception is raised.
        """
        reg.clear_cache()  # should not raise

    def test_io_happens_only_once_per_spec(self, reg):
        """
        Description: Validates that I/O (load_toml) is only invoked on the first
                     get() call, not on subsequent hits.
        Scenario: Patch load_toml and call get('alpha') twice.
        Expectation: load_toml is called exactly once.
        """
        with patch(
            "plotstyle.specs.load_toml",
            wraps=__import__("plotstyle._utils.io", fromlist=["load_toml"]).load_toml,
        ) as mock_load:
            reg.get("alpha")
            reg.get("alpha")
            assert mock_load.call_count == 1


# ---------------------------------------------------------------------------
# TestPreload
# ---------------------------------------------------------------------------


class TestPreload:
    def test_preload_none_loads_all_specs(self, reg):
        """
        Description: Validates that preload(None) eagerly loads every available spec.
        Scenario: Call preload() with default argument on a two-spec registry.
        Expectation: Both 'alpha' and 'beta' are present in the cache.
        """
        reg.preload()
        available = reg.list_available()
        for name in available:
            assert name in reg._cache

    def test_preload_none_cache_size_equals_available(self, reg):
        """
        Description: Validates that preload() (no args) caches exactly as many
                     specs as list_available() returns.
        Scenario: Call preload() then compare cache size to list_available().
        Expectation: len(reg._cache) == len(reg.list_available()).
        """
        reg.preload()
        assert len(reg._cache) == len(reg.list_available())

    def test_preload_specific_single_name(self, reg):
        """
        Description: Validates targeted preload of a single named spec.
        Scenario: Call preload(['alpha']).
        Expectation: 'alpha' is in cache; 'beta' is not.
        """
        reg.preload(["alpha"])
        assert "alpha" in reg._cache
        assert "beta" not in reg._cache

    def test_preload_multiple_specific_names(self, reg):
        """
        Description: Validates targeted preload of multiple named specs.
        Scenario: Call preload(['alpha', 'beta']).
        Expectation: Both 'alpha' and 'beta' are in cache.
        """
        reg.preload(["alpha", "beta"])
        assert "alpha" in reg._cache
        assert "beta" in reg._cache

    def test_preload_empty_list_does_nothing(self, reg):
        """
        Description: Validates that preload([]) is a no-op.
        Scenario: Call preload with an explicit empty list.
        Expectation: Cache remains empty.
        """
        reg.preload([])
        assert len(reg._cache) == 0

    def test_preload_unknown_name_raises_spec_not_found_error(self, reg):
        """
        Description: Validates that preload propagates SpecNotFoundError for
                     names that don't correspond to any TOML file.
        Scenario: Call preload(['nonexistent']).
        Expectation: SpecNotFoundError is raised.
        """
        with pytest.raises(SpecNotFoundError):
            reg.preload(["nonexistent"])

    def test_preload_returns_none(self, reg):
        """
        Description: Validates that preload() has no return value (None).
        Scenario: Call preload().
        Expectation: Return value is None.
        """
        result = reg.preload()
        assert result is None

    def test_preload_is_idempotent(self, reg):
        """
        Description: Validates that calling preload() multiple times does not
                     cause errors or duplicate entries.
        Scenario: Call preload() twice.
        Expectation: No exception; cache size remains equal to list_available().
        """
        reg.preload()
        reg.preload()
        assert len(reg._cache) == len(reg.list_available())

    def test_preload_specs_are_same_objects_as_get(self, reg):
        """
        Description: Validates that preloaded specs are the same cached objects
                     returned by subsequent get() calls.
        Scenario: Call preload(), then get('alpha').
        Expectation: The returned object is the same as what preload cached.
        """
        reg.preload(["alpha"])
        cached = reg._cache["alpha"]
        fetched = reg.get("alpha")
        assert cached is fetched

    def test_preload_with_none_after_partial_load(self, reg):
        """
        Description: Validates that preload(None) after a partial load
                     loads only the remaining specs without errors.
        Scenario: get('alpha') first, then preload().
        Expectation: Both specs are in cache and cache size equals available.
        """
        reg.get("alpha")
        reg.preload()  # Should load 'beta' too
        assert len(reg._cache) == len(reg.list_available())


# ---------------------------------------------------------------------------
# TestContains
# ---------------------------------------------------------------------------


class TestContains:
    def test_existing_name_is_contained(self, reg):
        """
        Description: Validates __contains__ for a name with a matching TOML file.
        Scenario: 'alpha' exists on disk.
        Expectation: 'alpha' in reg is True.
        """
        assert "alpha" in reg

    def test_existing_name_case_insensitive(self, reg):
        """
        Description: Validates that __contains__ normalises the name to lowercase.
        Scenario: Check 'ALPHA' when alpha.toml exists.
        Expectation: True.
        """
        assert "ALPHA" in reg

    def test_existing_name_mixed_case(self, reg):
        """
        Description: Validates __contains__ for mixed-case input.
        Scenario: Check 'Alpha' when alpha.toml exists.
        Expectation: True.
        """
        assert "Alpha" in reg

    def test_nonexistent_name_not_in_registry(self, reg):
        """
        Description: Validates __contains__ for a name with no matching file.
        Scenario: Check 'nonexistent'.
        Expectation: False.
        """
        assert "nonexistent" not in reg

    def test_cached_name_is_contained_without_file(self, reg):
        """
        Description: Validates that cached specs remain 'contained' even if
                     the underlying file is deleted after loading.
        Scenario: Load 'alpha', delete alpha.toml, check __contains__.
        Expectation: 'alpha' in reg is True (found in cache).
        """
        reg.get("alpha")
        (reg._specs_dir / "alpha.toml").unlink()
        assert "alpha" in reg

    def test_not_contained_after_file_deleted_and_cache_cleared(self, reg):
        """
        Description: Validates that once the cache is cleared and the file is
                     gone, __contains__ returns False.
        Scenario: Load 'alpha', delete alpha.toml, clear cache, check __contains__.
        Expectation: 'alpha' in reg is False.
        """
        reg.get("alpha")
        (reg._specs_dir / "alpha.toml").unlink()
        reg.clear_cache()
        assert "alpha" not in reg

    def test_contains_does_not_load_into_cache(self, reg):
        """
        Description: Validates that __contains__ is a lightweight check and
                     does not cause the spec to be loaded into the cache.
        Scenario: Use 'in' operator on a fresh registry.
        Expectation: Cache remains empty after the check.
        """
        _ = "alpha" in reg
        assert len(reg._cache) == 0

    def test_empty_string_not_in_registry(self, reg):
        """
        Description: Validates that an empty string is treated as a missing spec.
        Scenario: Check '' (empty string).
        Expectation: False (no file named '.toml' should match).
        """
        assert "" not in reg


# ---------------------------------------------------------------------------
# TestLen
# ---------------------------------------------------------------------------


class TestLen:
    def test_len_equals_list_available_count(self, reg):
        """
        Description: Validates that __len__ is consistent with list_available().
        Scenario: Normal registry with 2 public specs.
        Expectation: len(reg) == len(reg.list_available()).
        """
        assert len(reg) == len(reg.list_available())

    def test_len_is_2_for_two_non_private_files(self, reg):
        """
        Description: Validates the concrete count for the standard fixture.
        Scenario: Registry with alpha.toml and beta.toml (plus _private.toml).
        Expectation: len(reg) == 2.
        """
        assert len(reg) == 2

    def test_len_empty_directory(self, empty_specs_dir):
        """
        Description: Validates __len__ for an empty specs directory.
        Scenario: No TOML files at all.
        Expectation: len(reg) == 0.
        """
        reg = SpecRegistry(specs_dir=empty_specs_dir)
        assert len(reg) == 0

    def test_len_only_private_files(self, only_private_specs_dir):
        """
        Description: Validates that private-only directories have effective length 0.
        Scenario: Directory with only _internal.toml and _base.toml.
        Expectation: len(reg) == 0.
        """
        reg = SpecRegistry(specs_dir=only_private_specs_dir)
        assert len(reg) == 0

    def test_len_single_spec(self, single_spec_dir):
        """
        Description: Validates __len__ when exactly one public spec exists.
        Scenario: Directory with solo.toml only.
        Expectation: len(reg) == 1.
        """
        reg = SpecRegistry(specs_dir=single_spec_dir)
        assert len(reg) == 1

    def test_len_does_not_depend_on_cache(self, reg):
        """
        Description: Validates that __len__ reflects disk contents, not cache state.
        Scenario: Call len() before and after loading specs.
        Expectation: Both calls return the same value (2).
        """
        before = len(reg)
        reg.preload()
        after = len(reg)
        assert before == after == 2

    def test_len_inaccessible_directory_raises(self, tmp_path):
        """
        Description: Validates that __len__ propagates FileNotFoundError from
                     list_available() when the specs dir is missing.
        Scenario: Registry pointed at a nonexistent directory.
        Expectation: FileNotFoundError is raised on len().
        """
        missing = tmp_path / "ghost_dir"
        reg = SpecRegistry(specs_dir=missing)
        with pytest.raises(FileNotFoundError):
            len(reg)


# ---------------------------------------------------------------------------
# TestRepr
# ---------------------------------------------------------------------------


class TestRepr:
    def test_repr_contains_class_name(self, reg):
        """
        Description: Validates that repr includes the class name for debuggability.
        Scenario: Call repr() on a registry.
        Expectation: 'SpecRegistry' appears in the output.
        """
        assert "SpecRegistry" in repr(reg)

    def test_repr_contains_specs_dir(self, reg):
        """
        Description: Validates that repr includes the path to the specs directory.
        Scenario: Call repr() on a registry.
        Expectation: The specs_dir path string appears in repr.
        """
        assert str(reg._specs_dir) in repr(reg)

    def test_repr_contains_cached_key(self, reg):
        """
        Description: Validates that repr includes the 'cached=' key.
        Scenario: Load one spec, then call repr().
        Expectation: 'cached=' is in the repr string.
        """
        reg.get("alpha")
        assert "cached=" in repr(reg)

    def test_repr_format_before_any_load(self, reg):
        """
        Description: Validates the cached=0/N format before any specs are loaded.
        Scenario: Fresh registry, no get() calls.
        Expectation: repr contains 'cached=0/'.
        """
        assert "cached=0/" in repr(reg)

    def test_repr_format_after_preload_all(self, reg):
        """
        Description: Validates the cached=N/N format after preloading all specs.
        Scenario: Call preload() then repr().
        Expectation: repr contains 'cached=2/2'.
        """
        reg.preload()
        assert "cached=2/2" in repr(reg)

    def test_repr_format_after_partial_load(self, reg):
        """
        Description: Validates repr shows correct partial cache counts.
        Scenario: Load only 'alpha' from a two-spec registry.
        Expectation: repr contains 'cached=1/2'.
        """
        reg.get("alpha")
        assert "cached=1/2" in repr(reg)

    def test_repr_is_string(self, reg):
        """
        Description: Validates that repr() returns a str (not bytes or None).
        Scenario: Call repr() on a registry.
        Expectation: isinstance(repr(reg), str) is True.
        """
        assert isinstance(repr(reg), str)

    def test_repr_updates_after_clear_cache(self, reg):
        """
        Description: Validates that repr reflects cache state after clearing.
        Scenario: Load 'alpha', clear cache, check repr.
        Expectation: repr contains 'cached=0/' after clearing.
        """
        reg.get("alpha")
        reg.clear_cache()
        assert "cached=0/" in repr(reg)


# ---------------------------------------------------------------------------
# TestSpecRegistryInit
# ---------------------------------------------------------------------------


class TestSpecRegistryInit:
    def test_default_specs_dir_is_package_directory(self):
        """
        Description: Validates that SpecRegistry without arguments uses the
                     package's own specs directory.
        Scenario: Instantiate SpecRegistry() with no arguments.
        Expectation: _specs_dir is a valid directory Path that exists.
        """
        reg = SpecRegistry()
        assert reg._specs_dir.is_dir()

    def test_custom_specs_dir_is_stored(self, tmp_specs_dir):
        """
        Description: Validates that a custom specs_dir is stored correctly.
        Scenario: Pass tmp_specs_dir to SpecRegistry constructor.
        Expectation: reg._specs_dir == tmp_specs_dir.
        """
        reg = SpecRegistry(specs_dir=tmp_specs_dir)
        assert reg._specs_dir == tmp_specs_dir

    def test_none_specs_dir_uses_default(self):
        """
        Description: Validates that explicitly passing None uses the default dir.
        Scenario: SpecRegistry(specs_dir=None).
        Expectation: _specs_dir equals the module default (_SPECS_DIR).
        """
        from plotstyle.specs import _SPECS_DIR

        reg = SpecRegistry(specs_dir=None)
        assert reg._specs_dir == _SPECS_DIR

    def test_cache_initialised_as_empty_dict(self, tmp_specs_dir):
        """
        Description: Validates that the cache starts as an empty dict on init.
        Scenario: Fresh SpecRegistry.
        Expectation: reg._cache == {}.
        """
        reg = SpecRegistry(specs_dir=tmp_specs_dir)
        assert reg._cache == {}

    def test_slots_prevent_arbitrary_attribute_assignment(self, reg):
        """
        Description: Validates that __slots__ is enforced — arbitrary attribute
                     assignment should raise AttributeError.
        Scenario: Try to assign reg.unexpected_attr = 42.
        Expectation: AttributeError is raised.
        """
        with pytest.raises(AttributeError):
            reg.unexpected_attr = 42  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# TestModuleLevelSingleton
# ---------------------------------------------------------------------------


class TestModuleLevelSingleton:
    def test_singleton_is_spec_registry_instance(self):
        """
        Description: Validates that the module-level registry is a SpecRegistry.
        Scenario: Import registry from plotstyle.specs.
        Expectation: isinstance(registry, SpecRegistry) is True.
        """
        from plotstyle.specs import registry

        assert isinstance(registry, SpecRegistry)

    def test_singleton_is_accessible_from_module(self):
        """
        Description: Validates the importability of the module-level singleton.
        Scenario: Direct import of registry from plotstyle.specs.
        Expectation: No ImportError; object is not None.
        """
        from plotstyle.specs import registry

        assert registry is not None

    def test_singleton_identity_across_imports(self):
        """
        Description: Validates that repeated imports return the same singleton.
        Scenario: Import registry twice via different import statements.
        Expectation: Both references point to the exact same object.
        """
        from plotstyle.specs import registry as reg1
        from plotstyle.specs import registry as reg2

        assert reg1 is reg2

    def test_singleton_can_get_known_journal(self):
        """
        Description: Integration test that the singleton can load a known journal.
        Scenario: Use module-level registry to get 'nature'.
        Expectation: Returns a JournalSpec with name 'Nature'.
        """
        from plotstyle.specs import registry

        spec = registry.get("nature")
        assert spec.metadata.name == "Nature"


# ---------------------------------------------------------------------------
# TestEdgeCases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_get_after_file_added_at_runtime(self, tmp_specs_dir):
        """
        Description: Validates that the registry discovers files added to the
                     specs directory after construction.
        Scenario: Create registry, then add a new .toml file, then get().
        Expectation: The new spec is loadable without reinitialising the registry.
        """
        reg = SpecRegistry(specs_dir=tmp_specs_dir)
        (tmp_specs_dir / "gamma.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
        spec = reg.get("gamma")
        assert isinstance(spec, JournalSpec)

    def test_list_available_reflects_file_added_at_runtime(self, tmp_specs_dir):
        """
        Description: Validates that list_available() always scans disk, so new
                     files are reflected without cache busting.
        Scenario: Add 'gamma.toml' after registry construction, call list_available().
        Expectation: 'gamma' appears in the results.
        """
        reg = SpecRegistry(specs_dir=tmp_specs_dir)
        initial = reg.list_available()
        (tmp_specs_dir / "gamma.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
        updated = reg.list_available()
        assert "gamma" in updated
        assert len(updated) == len(initial) + 1

    def test_get_file_removed_after_caching_still_returns_spec(self, reg):
        """
        Description: Validates resilience: once a spec is cached, deleting its
                     source file does not break subsequent get() calls.
        Scenario: Load 'alpha', delete alpha.toml, call get('alpha') again.
        Expectation: Returns the cached JournalSpec without FileNotFoundError.
        """
        reg.get("alpha")
        (reg._specs_dir / "alpha.toml").unlink()
        spec = reg.get("alpha")
        assert isinstance(spec, JournalSpec)

    def test_get_file_removed_after_cache_cleared_raises(self, reg):
        """
        Description: Validates that deleting a file then clearing the cache causes
                     SpecNotFoundError on subsequent get().
        Scenario: Load 'alpha', delete alpha.toml, clear cache, get('alpha').
        Expectation: SpecNotFoundError is raised.
        """
        reg.get("alpha")
        (reg._specs_dir / "alpha.toml").unlink()
        reg.clear_cache()
        with pytest.raises(SpecNotFoundError):
            reg.get("alpha")

    def test_multiple_registries_are_independent(self, tmp_specs_dir, tmp_path):
        """
        Description: Validates that two SpecRegistry instances do not share state.
        Scenario: Create two registries pointing at different directories.
        Expectation: Caching in one does not affect the other.
        """
        (tmp_path / "delta.toml").write_text(_ALTERNATE_TOML, encoding="utf-8")
        reg_a = SpecRegistry(specs_dir=tmp_specs_dir)
        reg_b = SpecRegistry(specs_dir=tmp_path)

        reg_a.get("alpha")
        assert "alpha" not in reg_b._cache
        assert "delta" not in reg_a._cache

    def test_large_number_of_specs_in_directory(self, tmp_path):
        """
        Description: Validates stability when the specs directory contains many files.
        Scenario: Write 50 TOML spec files and call list_available().
        Expectation: All 50 are returned in sorted order.
        """
        names = [f"journal_{i:03d}" for i in range(50)]
        for name in names:
            (tmp_path / f"{name}.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
        reg = SpecRegistry(specs_dir=tmp_path)
        available = reg.list_available()
        assert available == sorted(names)
        assert len(available) == 50

    def test_spec_name_with_digits(self, tmp_path):
        """
        Description: Validates that spec names containing digits are handled correctly.
        Scenario: File named 'journal2024.toml'.
        Expectation: 'journal2024' appears in list_available() and is loadable.
        """
        (tmp_path / "journal2024.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
        reg = SpecRegistry(specs_dir=tmp_path)
        assert "journal2024" in reg.list_available()
        spec = reg.get("journal2024")
        assert isinstance(spec, JournalSpec)

    def test_spec_name_with_hyphens(self, tmp_path):
        """
        Description: Validates that spec names containing hyphens are handled correctly.
        Scenario: File named 'acs-nano.toml'.
        Expectation: 'acs-nano' appears in list_available() and is loadable.
        """
        (tmp_path / "acs-nano.toml").write_text(_MINIMAL_TOML, encoding="utf-8")
        reg = SpecRegistry(specs_dir=tmp_path)
        assert "acs-nano" in reg.list_available()
        spec = reg.get("acs-nano")
        assert isinstance(spec, JournalSpec)
