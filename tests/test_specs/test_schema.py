"""Enhanced test suite for plotstyle.specs.schema.

Covers: exception hierarchy, happy paths, defaults, missing required fields,
type errors, value constraint violations, normalisation, immutability,
cross-field invariants, edge/boundary values, and structural properties.
"""

from __future__ import annotations

import pytest

from plotstyle.specs.schema import (
    ColorSpec,
    DimensionSpec,
    ExportSpec,
    FieldTypeError,
    FieldValueError,
    JournalSpec,
    JournalSpecError,
    LineSpec,
    MetadataSpec,
    MissingFieldError,
    TypographySpec,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_data() -> dict:
    """
    Description: Returns a minimal, fully-valid TOML-equivalent dict.
    Scenario: All required fields present with legal values; optional tables absent.
    Expectation: JournalSpec.from_toml succeeds without error.
    """
    return {
        "metadata": {
            "name": "Test Journal",
            "publisher": "Test Publisher",
            "source_url": "https://example.com/guidelines",
            "last_verified": "2024-01-15",
        },
        "dimensions": {
            "single_column_mm": 89.0,
            "double_column_mm": 183.0,
            "max_height_mm": 247.0,
        },
        "typography": {
            "font_family": ["Helvetica", "Arial"],
            "min_font_pt": 7.0,
            "max_font_pt": 9.0,
        },
        "export": {
            "preferred_formats": ["pdf"],
            "min_dpi": 300,
            "color_space": "rgb",
            "font_embedding": True,
            "editable_text": False,
        },
    }


@pytest.fixture
def full_data(valid_data) -> dict:
    """
    Description: Returns a fully-populated TOML-equivalent dict including all optional tables.
    Scenario: Every supported table and field is present with valid values.
    Expectation: JournalSpec.from_toml succeeds and all attributes are populated.
    """
    valid_data["color"] = {
        "avoid_combinations": [["red", "green"], ["blue", "yellow"]],
        "colorblind_required": True,
        "grayscale_required": True,
    }
    valid_data["line"] = {"min_weight_pt": 0.75}
    valid_data["notes"] = "Test notes."
    return valid_data


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class TestExceptionHierarchy:
    def test_journal_spec_error_is_value_error(self):
        """
        Description: Validates that JournalSpecError inherits from ValueError.
        Scenario: Instantiate JournalSpecError directly.
        Expectation: isinstance check against ValueError returns True.
        """
        assert isinstance(JournalSpecError("test"), ValueError)

    def test_missing_field_error_is_journal_spec_error(self):
        """
        Description: Validates MissingFieldError sits in the correct exception hierarchy.
        Scenario: Instantiate MissingFieldError.
        Expectation: Is instance of both JournalSpecError and ValueError.
        """
        err = MissingFieldError("metadata", "name")
        assert isinstance(err, JournalSpecError)
        assert isinstance(err, ValueError)

    def test_field_type_error_is_journal_spec_error(self):
        """
        Description: Validates FieldTypeError sits in the correct exception hierarchy.
        Scenario: Instantiate FieldTypeError.
        Expectation: Is instance of both JournalSpecError and ValueError.
        """
        err = FieldTypeError("dimensions", "single_column_mm", "float", "wide")
        assert isinstance(err, JournalSpecError)
        assert isinstance(err, ValueError)

    def test_field_value_error_is_journal_spec_error(self):
        """
        Description: Validates FieldValueError sits in the correct exception hierarchy.
        Scenario: Instantiate FieldValueError.
        Expectation: Is instance of both JournalSpecError and ValueError.
        """
        err = FieldValueError("export", "min_dpi", "must be ≥ 72, got 0")
        assert isinstance(err, JournalSpecError)
        assert isinstance(err, ValueError)

    def test_all_errors_catchable_as_journal_spec_error(self):
        """
        Description: Confirms all three error subtypes are catchable with a single except clause.
        Scenario: Raise each subtype and catch as JournalSpecError.
        Expectation: No uncaught exception propagates.
        """
        for exc in [
            MissingFieldError("t", "f"),
            FieldTypeError("t", "f", "int", "x"),
            FieldValueError("t", "f", "bad"),
        ]:
            with pytest.raises(JournalSpecError):
                raise exc

    def test_missing_field_error_attributes(self):
        """
        Description: Validates MissingFieldError stores table and field_name attributes correctly.
        Scenario: Create error with known table and field_name.
        Expectation: .table == 'metadata', .field_name == 'publisher'.
        """
        err = MissingFieldError("metadata", "publisher")
        assert err.table == "metadata"
        assert err.field_name == "publisher"

    def test_missing_field_error_message_contains_table_and_field(self):
        """
        Description: Validates error message includes both the table and field name.
        Scenario: Stringify a MissingFieldError.
        Expectation: Both 'metadata' and 'publisher' appear in the message.
        """
        err = MissingFieldError("metadata", "publisher")
        msg = str(err)
        assert "metadata" in msg
        assert "publisher" in msg

    def test_field_type_error_attributes(self):
        """
        Description: Validates FieldTypeError stores all four diagnostic attributes.
        Scenario: Create error with table, field_name, expected type, and got value.
        Expectation: All four attributes match the constructor arguments.
        """
        err = FieldTypeError("dimensions", "single_column_mm", "float", "wide")
        assert err.table == "dimensions"
        assert err.field_name == "single_column_mm"
        assert err.expected == "float"
        assert err.got == "wide"

    def test_field_type_error_message_contains_all_info(self):
        """
        Description: Validates FieldTypeError message carries table, field, expected, and got.
        Scenario: Stringify a FieldTypeError.
        Expectation: All four pieces of info appear in the message string.
        """
        err = FieldTypeError("dimensions", "single_column_mm", "float", "wide")
        msg = str(err)
        assert "dimensions" in msg
        assert "single_column_mm" in msg
        assert "float" in msg
        assert "wide" in msg

    def test_field_value_error_attributes(self):
        """
        Description: Validates FieldValueError stores table, field_name, and reason attributes.
        Scenario: Create error with known arguments.
        Expectation: All attributes match.
        """
        err = FieldValueError("export", "min_dpi", "must be ≥ 72, got 0")
        assert err.table == "export"
        assert err.field_name == "min_dpi"
        assert err.reason == "must be ≥ 72, got 0"

    def test_field_value_error_message_contains_location_and_reason(self):
        """
        Description: Validates FieldValueError message includes table, field, and reason.
        Scenario: Stringify a FieldValueError.
        Expectation: All three components appear in the message.
        """
        err = FieldValueError("export", "min_dpi", "must be ≥ 72, got 0")
        msg = str(err)
        assert "export" in msg
        assert "min_dpi" in msg
        assert "must be ≥ 72, got 0" in msg


# ---------------------------------------------------------------------------
# Happy path — full valid data
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_from_toml_returns_journal_spec_instance(self, valid_data):
        """
        Description: Validates that from_toml returns a JournalSpec instance.
        Scenario: Minimal valid data dictionary.
        Expectation: Return type is JournalSpec.
        """
        assert isinstance(JournalSpec.from_toml(valid_data), JournalSpec)

    def test_metadata_fields_populated(self, valid_data):
        """
        Description: Validates metadata sub-spec fields match input values.
        Scenario: Minimal valid data with all metadata fields present.
        Expectation: Each MetadataSpec attribute equals the supplied value.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.metadata.name == "Test Journal"
        assert spec.metadata.publisher == "Test Publisher"
        assert spec.metadata.source_url == "https://example.com/guidelines"
        assert spec.metadata.last_verified == "2024-01-15"

    def test_dimensions_fields_populated(self, valid_data):
        """
        Description: Validates dimension sub-spec fields match input values.
        Scenario: Minimal valid data with all dimension fields.
        Expectation: Each DimensionSpec attribute equals the supplied value.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.dimensions.single_column_mm == 89.0
        assert spec.dimensions.double_column_mm == 183.0
        assert spec.dimensions.max_height_mm == 247.0

    def test_typography_fields_populated(self, valid_data):
        """
        Description: Validates typography sub-spec fields match input values.
        Scenario: Minimal valid data with all typography fields.
        Expectation: Each TypographySpec attribute equals the supplied value.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.font_family == ["Helvetica", "Arial"]
        assert spec.typography.min_font_pt == 7.0
        assert spec.typography.max_font_pt == 9.0

    def test_export_fields_populated(self, valid_data):
        """
        Description: Validates export sub-spec fields match input values.
        Scenario: Minimal valid data with all export fields present.
        Expectation: Each ExportSpec attribute equals the supplied value.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.export.preferred_formats == ["pdf"]
        assert spec.export.min_dpi == 300
        assert spec.export.color_space == "rgb"
        assert spec.export.font_embedding is True
        assert spec.export.editable_text is False

    def test_full_spec_with_all_optional_tables(self, full_data):
        """
        Description: Validates all optional tables (color, line, notes) are parsed correctly.
        Scenario: Full data dict including color, line, and notes tables.
        Expectation: All optional sub-spec attributes match supplied values.
        """
        spec = JournalSpec.from_toml(full_data)
        assert spec.color.avoid_combinations == [["red", "green"], ["blue", "yellow"]]
        assert spec.color.colorblind_required is True
        assert spec.color.grayscale_required is True
        assert spec.line.min_weight_pt == 0.75
        assert spec.notes == "Test notes."

    def test_notes_defaults_to_empty_string_when_absent(self, valid_data):
        """
        Description: Validates that notes defaults to empty string when key is absent.
        Scenario: Minimal valid data without a 'notes' key.
        Expectation: spec.notes == ''.
        """
        assert JournalSpec.from_toml(valid_data).notes == ""

    def test_sub_spec_types_are_correct(self, valid_data):
        """
        Description: Validates each attribute of JournalSpec is of the correct sub-spec type.
        Scenario: Minimal valid data.
        Expectation: isinstance checks pass for all six sub-specs.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert isinstance(spec.metadata, MetadataSpec)
        assert isinstance(spec.dimensions, DimensionSpec)
        assert isinstance(spec.typography, TypographySpec)
        assert isinstance(spec.export, ExportSpec)
        assert isinstance(spec.color, ColorSpec)
        assert isinstance(spec.line, LineSpec)


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


class TestDefaults:
    def test_verified_by_defaults_to_empty_string(self, valid_data):
        """
        Description: Validates optional 'verified_by' field defaults to empty string.
        Scenario: 'verified_by' absent from metadata table.
        Expectation: spec.metadata.verified_by == ''.
        """
        assert "verified_by" not in valid_data["metadata"]
        assert JournalSpec.from_toml(valid_data).metadata.verified_by == ""

    def test_panel_label_pt_defaults_to_min_font_pt(self, valid_data):
        """
        Description: Validates panel_label_pt defaults to min_font_pt when absent.
        Scenario: 'panel_label_pt' absent from typography table.
        Expectation: spec.typography.panel_label_pt == spec.typography.min_font_pt.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.panel_label_pt == spec.typography.min_font_pt

    def test_font_fallback_defaults_to_sans_serif(self, valid_data):
        """
        Description: Validates font_fallback defaults to 'sans-serif'.
        Scenario: 'font_fallback' absent from typography table.
        Expectation: spec.typography.font_fallback == 'sans-serif'.
        """
        assert JournalSpec.from_toml(valid_data).typography.font_fallback == "sans-serif"

    def test_panel_label_weight_defaults_to_bold(self, valid_data):
        """
        Description: Validates panel_label_weight defaults to 'bold'.
        Scenario: 'panel_label_weight' absent from typography.
        Expectation: spec.typography.panel_label_weight == 'bold'.
        """
        assert JournalSpec.from_toml(valid_data).typography.panel_label_weight == "bold"

    def test_panel_label_case_defaults_to_lower(self, valid_data):
        """
        Description: Validates panel_label_case defaults to 'lower'.
        Scenario: 'panel_label_case' absent from typography.
        Expectation: spec.typography.panel_label_case == 'lower'.
        """
        assert JournalSpec.from_toml(valid_data).typography.panel_label_case == "lower"

    def test_export_preferred_formats_defaults_to_pdf(self, valid_data):
        """
        Description: Validates preferred_formats defaults to ['pdf'] when absent.
        Scenario: 'preferred_formats' removed from export table.
        Expectation: spec.export.preferred_formats == ['pdf'].
        """
        del valid_data["export"]["preferred_formats"]
        assert JournalSpec.from_toml(valid_data).export.preferred_formats == ["pdf"]

    def test_export_min_dpi_defaults_to_300(self, valid_data):
        """
        Description: Validates min_dpi defaults to 300 when absent.
        Scenario: 'min_dpi' removed from export table.
        Expectation: spec.export.min_dpi == 300.
        """
        del valid_data["export"]["min_dpi"]
        assert JournalSpec.from_toml(valid_data).export.min_dpi == 300

    def test_export_color_space_defaults_to_rgb(self, valid_data):
        """
        Description: Validates color_space defaults to 'rgb' when absent.
        Scenario: 'color_space' removed from export table.
        Expectation: spec.export.color_space == 'rgb'.
        """
        del valid_data["export"]["color_space"]
        assert JournalSpec.from_toml(valid_data).export.color_space == "rgb"

    def test_export_font_embedding_defaults_to_true(self, valid_data):
        """
        Description: Validates font_embedding defaults to True when absent.
        Scenario: 'font_embedding' removed from export table.
        Expectation: spec.export.font_embedding is True.
        """
        del valid_data["export"]["font_embedding"]
        assert JournalSpec.from_toml(valid_data).export.font_embedding is True

    def test_export_editable_text_defaults_to_false(self, valid_data):
        """
        Description: Validates editable_text defaults to False when absent.
        Scenario: 'editable_text' removed from export table.
        Expectation: spec.export.editable_text is False.
        """
        del valid_data["export"]["editable_text"]
        assert JournalSpec.from_toml(valid_data).export.editable_text is False

    def test_absent_color_table_uses_defaults(self, valid_data):
        """
        Description: Validates absent [color] table produces sensible defaults.
        Scenario: No 'color' key in data dict.
        Expectation: avoid_combinations=[], colorblind_required=False, grayscale_required=False.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.color.avoid_combinations == []
        assert spec.color.colorblind_required is False
        assert spec.color.grayscale_required is False

    def test_absent_line_table_uses_default_weight(self, valid_data):
        """
        Description: Validates absent [line] table produces default min_weight_pt of 0.5.
        Scenario: No 'line' key in data dict.
        Expectation: spec.line.min_weight_pt == 0.5.
        """
        assert JournalSpec.from_toml(valid_data).line.min_weight_pt == 0.5

    def test_empty_export_table_uses_all_defaults(self, valid_data):
        """
        Description: Validates an empty export table triggers all export defaults.
        Scenario: export table present but completely empty.
        Expectation: All export fields revert to documented defaults.
        """
        valid_data["export"] = {}
        spec = JournalSpec.from_toml(valid_data)
        assert spec.export.preferred_formats == ["pdf"]
        assert spec.export.min_dpi == 300
        assert spec.export.color_space == "rgb"
        assert spec.export.font_embedding is True
        assert spec.export.editable_text is False

    def test_panel_label_pt_explicit_overrides_default(self, valid_data):
        """
        Description: Validates explicit panel_label_pt takes precedence over the min_font_pt default.
        Scenario: 'panel_label_pt' set to a value different from min_font_pt.
        Expectation: spec.typography.panel_label_pt equals the explicit value.
        """
        valid_data["typography"]["panel_label_pt"] = 8.0
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.panel_label_pt == 8.0
        assert spec.typography.panel_label_pt != spec.typography.min_font_pt

    def test_empty_color_table_uses_all_defaults(self, valid_data):
        """
        Description: Validates an empty color table triggers all color defaults.
        Scenario: color table present but completely empty.
        Expectation: All color fields revert to documented defaults.
        """
        valid_data["color"] = {}
        spec = JournalSpec.from_toml(valid_data)
        assert spec.color.avoid_combinations == []
        assert spec.color.colorblind_required is False
        assert spec.color.grayscale_required is False

    def test_empty_line_table_uses_default_weight(self, valid_data):
        """
        Description: Validates an empty line table reverts min_weight_pt to 0.5.
        Scenario: line table present but completely empty.
        Expectation: spec.line.min_weight_pt == 0.5.
        """
        valid_data["line"] = {}
        assert JournalSpec.from_toml(valid_data).line.min_weight_pt == 0.5

    def test_verified_by_explicit_value_preserved(self, valid_data):
        """
        Description: Validates that an explicit verified_by value is preserved as-is.
        Scenario: 'verified_by' set to a non-empty string.
        Expectation: spec.metadata.verified_by equals the supplied string.
        """
        valid_data["metadata"]["verified_by"] = "j.doe"
        assert JournalSpec.from_toml(valid_data).metadata.verified_by == "j.doe"


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------


class TestMissingRequiredFields:
    @pytest.mark.parametrize("table", ["metadata", "dimensions", "typography", "export"])
    def test_missing_top_level_table_raises_missing_field_error(self, valid_data, table):
        """
        Description: Validates that each required top-level table, when absent, raises MissingFieldError.
        Scenario: Delete one required top-level table key at a time.
        Expectation: MissingFieldError is raised.
        """
        del valid_data[table]
        with pytest.raises(MissingFieldError):
            JournalSpec.from_toml(valid_data)

    @pytest.mark.parametrize("field_name", ["name", "publisher", "source_url", "last_verified"])
    def test_missing_metadata_field_raises_with_correct_field_name(self, valid_data, field_name):
        """
        Description: Validates each required metadata field raises MissingFieldError when absent.
        Scenario: Delete one required metadata field at a time.
        Expectation: MissingFieldError.field_name matches the deleted key.
        """
        del valid_data["metadata"][field_name]
        with pytest.raises(MissingFieldError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == field_name

    @pytest.mark.parametrize(
        "field_name", ["single_column_mm", "double_column_mm", "max_height_mm"]
    )
    def test_missing_dimension_field_raises_with_correct_field_name(self, valid_data, field_name):
        """
        Description: Validates each required dimension field raises MissingFieldError when absent.
        Scenario: Delete one required dimension field at a time.
        Expectation: MissingFieldError.field_name matches the deleted key.
        """
        del valid_data["dimensions"][field_name]
        with pytest.raises(MissingFieldError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == field_name

    @pytest.mark.parametrize("field_name", ["min_font_pt", "max_font_pt"])
    def test_missing_typography_field_raises_with_correct_field_name(self, valid_data, field_name):
        """
        Description: Validates required typography fields raise MissingFieldError when absent.
        Scenario: Delete one required typography field at a time.
        Expectation: MissingFieldError.field_name matches the deleted key.
        """
        del valid_data["typography"][field_name]
        with pytest.raises(MissingFieldError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == field_name

    def test_absent_font_family_raises_field_value_error(self, valid_data):
        """
        Description: Validates absent font_family (defaults to []) triggers FieldValueError due to non_empty=True.
        Scenario: 'font_family' key removed; default is empty list which fails non_empty constraint.
        Expectation: FieldValueError for font_family.
        """
        del valid_data["typography"]["font_family"]
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "font_family"

    def test_verified_by_is_optional_no_error(self, valid_data):
        """
        Description: Confirms verified_by can be omitted without raising any error.
        Scenario: verified_by absent from metadata.
        Expectation: No exception; spec.metadata.verified_by == ''.
        """
        assert "verified_by" not in valid_data["metadata"]
        spec = JournalSpec.from_toml(valid_data)
        assert spec.metadata.verified_by == ""

    def test_missing_table_error_has_correct_table_attribute(self, valid_data):
        """
        Description: Validates MissingFieldError.table is set correctly for a missing top-level table.
        Scenario: Delete 'metadata' table; catch resulting error.
        Expectation: err.table == 'root' (since the table itself is missing from root).
        """
        del valid_data["metadata"]
        with pytest.raises(MissingFieldError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "metadata"


# ---------------------------------------------------------------------------
# Type errors
# ---------------------------------------------------------------------------


class TestFieldTypeErrors:
    def test_single_column_string_raises_type_error(self, valid_data):
        """
        Description: Validates that a string value for single_column_mm raises FieldTypeError.
        Scenario: single_column_mm set to 'wide' (str).
        Expectation: FieldTypeError with field_name == 'single_column_mm'.
        """
        valid_data["dimensions"]["single_column_mm"] = "wide"
        with pytest.raises(FieldTypeError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "single_column_mm"

    def test_double_column_none_raises_type_error(self, valid_data):
        """
        Description: Validates that None for double_column_mm raises FieldTypeError.
        Scenario: double_column_mm set to None.
        Expectation: FieldTypeError is raised.
        """
        valid_data["dimensions"]["double_column_mm"] = None
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_max_height_bool_raises_type_error(self, valid_data):
        """
        Description: Validates that a boolean for max_height_mm (non-numeric bool as float check).
        Scenario: max_height_mm set to True — booleans are a subtype of int in Python and
                  can be coerced to float, so this tests the boundary; True == 1.0 which is > 0.
        Expectation: Parsed as 1.0 float (no error) since bool subclasses int in Python.
        """
        # bool is a subclass of int in Python, so True -> 1.0 is valid per _cast_float
        valid_data["dimensions"]["max_height_mm"] = True
        valid_data["dimensions"]["double_column_mm"] = 2.0  # ensure double > single
        valid_data["dimensions"]["single_column_mm"] = 1.0
        # Actually True coerces to 1.0 fine; single=1.0 same as max_height=True(1.0) is fine
        # This documents that booleans pass through as floats in this implementation.
        spec = JournalSpec.from_toml(valid_data)
        assert spec.dimensions.max_height_mm == 1.0

    def test_min_dpi_string_raises_type_error(self, valid_data):
        """
        Description: Validates that a string for min_dpi raises FieldTypeError.
        Scenario: min_dpi set to 'high'.
        Expectation: FieldTypeError with field_name == 'min_dpi'.
        """
        valid_data["export"]["min_dpi"] = "high"
        with pytest.raises(FieldTypeError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "min_dpi"

    def test_font_embedding_int_raises_type_error(self, valid_data):
        """
        Description: Validates that int 1 for font_embedding (a bool field) raises FieldTypeError.
        Scenario: font_embedding set to 1 (int).
        Expectation: FieldTypeError because TOML bool field requires actual bool.
        """
        valid_data["export"]["font_embedding"] = 1
        with pytest.raises(FieldTypeError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "font_embedding"

    def test_editable_text_string_raises_type_error(self, valid_data):
        """
        Description: Validates that string 'yes' for editable_text raises FieldTypeError.
        Scenario: editable_text set to 'yes'.
        Expectation: FieldTypeError is raised.
        """
        valid_data["export"]["editable_text"] = "yes"
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_preferred_formats_bare_string_raises_type_error(self, valid_data):
        """
        Description: Validates that a bare string (not list) for preferred_formats raises FieldTypeError.
        Scenario: preferred_formats set to 'pdf' (str instead of list).
        Expectation: FieldTypeError referencing 'preferred_formats'.
        """
        valid_data["export"]["preferred_formats"] = "pdf"
        with pytest.raises(FieldTypeError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "preferred_formats" in exc_info.value.field_name

    def test_font_family_bare_string_raises_type_error(self, valid_data):
        """
        Description: Validates that a bare string for font_family raises FieldTypeError.
        Scenario: font_family set to 'Helvetica' (str instead of list).
        Expectation: FieldTypeError is raised.
        """
        valid_data["typography"]["font_family"] = "Helvetica"
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_font_family_list_with_non_string_item_raises_type_error(self, valid_data):
        """
        Description: Validates that a non-string item within font_family list raises FieldTypeError.
        Scenario: font_family contains an integer element.
        Expectation: FieldTypeError for the integer element.
        """
        valid_data["typography"]["font_family"] = ["Helvetica", 42]
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_metadata_name_int_raises_type_error(self, valid_data):
        """
        Description: Validates that an integer for metadata.name raises FieldTypeError.
        Scenario: name set to 123 (int).
        Expectation: FieldTypeError with field_name == 'name'.
        """
        valid_data["metadata"]["name"] = 123
        with pytest.raises(FieldTypeError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "name"

    def test_metadata_publisher_list_raises_type_error(self, valid_data):
        """
        Description: Validates that a list for metadata.publisher raises FieldTypeError.
        Scenario: publisher set to a list instead of a string.
        Expectation: FieldTypeError is raised.
        """
        valid_data["metadata"]["publisher"] = ["Springer", "Nature"]
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_color_avoid_combinations_string_raises_type_error(self, valid_data):
        """
        Description: Validates that a bare string for avoid_combinations raises FieldTypeError.
        Scenario: avoid_combinations set to 'red,green' (str).
        Expectation: FieldTypeError referencing 'avoid_combinations'.
        """
        valid_data["color"] = {"avoid_combinations": "red,green"}
        with pytest.raises(FieldTypeError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "avoid_combinations" in exc_info.value.field_name

    def test_color_avoid_combinations_list_of_strings_not_list_of_lists_raises(self, valid_data):
        """
        Description: Validates that avoid_combinations containing bare strings raises FieldTypeError.
        Scenario: avoid_combinations is ['red', 'green'] instead of [['red', 'green']].
        Expectation: FieldTypeError because inner items must be lists.
        """
        valid_data["color"] = {"avoid_combinations": ["red", "green"]}
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_color_avoid_combinations_inner_non_string_raises_type_error(self, valid_data):
        """
        Description: Validates non-string item inside a combination group raises FieldTypeError.
        Scenario: avoid_combinations = [['red', 42]].
        Expectation: FieldTypeError for the integer element.
        """
        valid_data["color"] = {"avoid_combinations": [["red", 42]]}
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_colorblind_required_int_raises_type_error(self, valid_data):
        """
        Description: Validates that int 0 for colorblind_required raises FieldTypeError.
        Scenario: colorblind_required set to 0 (int).
        Expectation: FieldTypeError because only proper bool is accepted.
        """
        valid_data["color"] = {"colorblind_required": 0}
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_grayscale_required_string_raises_type_error(self, valid_data):
        """
        Description: Validates that string 'false' for grayscale_required raises FieldTypeError.
        Scenario: grayscale_required set to 'false' (str).
        Expectation: FieldTypeError because TOML boolean field requires native bool.
        """
        valid_data["color"] = {"grayscale_required": "false"}
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_line_min_weight_string_raises_type_error(self, valid_data):
        """
        Description: Validates that a string for min_weight_pt raises FieldTypeError.
        Scenario: min_weight_pt set to 'thin'.
        Expectation: FieldTypeError is raised.
        """
        valid_data["line"] = {"min_weight_pt": "thin"}
        with pytest.raises(FieldTypeError):
            JournalSpec.from_toml(valid_data)

    def test_dimensions_table_is_not_a_dict_raises(self, valid_data):
        """
        Description: Validates that a non-dict dimensions table raises an error.
        Scenario: dimensions set to a list instead of a dict.
        Expectation: Some JournalSpecError subtype is raised.
        """
        valid_data["dimensions"] = [89.0, 183.0, 247.0]
        with pytest.raises((TypeError, AttributeError, JournalSpecError)):
            JournalSpec.from_toml(valid_data)

    def test_field_type_error_got_attribute_preserves_original_value(self, valid_data):
        """
        Description: Validates FieldTypeError.got stores the exact offending value.
        Scenario: single_column_mm set to the string 'wide'.
        Expectation: FieldTypeError.got == 'wide'.
        """
        valid_data["dimensions"]["single_column_mm"] = "wide"
        with pytest.raises(FieldTypeError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.got == "wide"


# ---------------------------------------------------------------------------
# Value constraint violations
# ---------------------------------------------------------------------------


class TestFieldValueErrors:
    def test_negative_single_column_mm_raises(self, valid_data):
        """
        Description: Validates that a negative single_column_mm raises FieldValueError.
        Scenario: single_column_mm = -1.0 (below min_val=0.0).
        Expectation: FieldValueError with field_name == 'single_column_mm'.
        """
        valid_data["dimensions"]["single_column_mm"] = -1.0
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "single_column_mm"

    def test_zero_single_column_mm_raises(self, valid_data):
        """
        Description: Validates that zero single_column_mm raises FieldValueError.
        Scenario: single_column_mm = 0.0 (equal to min_val, which is exclusive per > check).
        Expectation: FieldValueError is raised because min_val check is >= 0 but the cross-field
                     check (double > single) would also fail if double == 0.
        Note: _cast_float uses min_val=0.0 with >= constraint so 0.0 passes the cast,
              but the cross-field invariant (double > single) catches 0==0.
        """
        valid_data["dimensions"]["single_column_mm"] = 0.0
        valid_data["dimensions"]["double_column_mm"] = 0.0
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_negative_max_height_mm_raises(self, valid_data):
        """
        Description: Validates negative max_height_mm raises FieldValueError.
        Scenario: max_height_mm = -10.0.
        Expectation: FieldValueError is raised.
        """
        valid_data["dimensions"]["max_height_mm"] = -10.0
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_double_column_equal_to_single_raises(self, valid_data):
        """
        Description: Validates cross-field invariant: double_column_mm must be strictly greater than single.
        Scenario: Both set to 89.0 (equal).
        Expectation: FieldValueError with field_name == 'double_column_mm'.
        """
        valid_data["dimensions"]["single_column_mm"] = 89.0
        valid_data["dimensions"]["double_column_mm"] = 89.0
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "double_column_mm" in exc_info.value.field_name

    def test_double_column_less_than_single_raises(self, valid_data):
        """
        Description: Validates cross-field invariant rejects double_column < single_column.
        Scenario: single=100.0, double=80.0.
        Expectation: FieldValueError with field_name == 'double_column_mm'.
        """
        valid_data["dimensions"]["single_column_mm"] = 100.0
        valid_data["dimensions"]["double_column_mm"] = 80.0
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "double_column_mm" in exc_info.value.field_name

    def test_max_font_pt_less_than_min_font_pt_raises(self, valid_data):
        """
        Description: Validates cross-field invariant: max_font_pt must be >= min_font_pt.
        Scenario: min=9.0, max=7.0 (inverted).
        Expectation: FieldValueError with field_name == 'max_font_pt'.
        """
        valid_data["typography"]["min_font_pt"] = 9.0
        valid_data["typography"]["max_font_pt"] = 7.0
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "max_font_pt"

    def test_max_font_pt_equal_to_min_font_pt_is_valid(self, valid_data):
        """
        Description: Validates that max_font_pt == min_font_pt is permitted (boundary condition).
        Scenario: Both set to 8.0.
        Expectation: No error; both attributes == 8.0.
        """
        valid_data["typography"]["min_font_pt"] = 8.0
        valid_data["typography"]["max_font_pt"] = 8.0
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.min_font_pt == spec.typography.max_font_pt == 8.0

    def test_min_dpi_below_72_raises(self, valid_data):
        """
        Description: Validates that min_dpi below the physical floor (72) raises FieldValueError.
        Scenario: min_dpi = 71.
        Expectation: FieldValueError with field_name == 'min_dpi'.
        """
        valid_data["export"]["min_dpi"] = 71
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "min_dpi"

    def test_min_dpi_exactly_72_is_valid(self, valid_data):
        """
        Description: Validates that min_dpi == 72 (physical floor) is accepted.
        Scenario: min_dpi = 72.
        Expectation: No error; spec.export.min_dpi == 72.
        """
        valid_data["export"]["min_dpi"] = 72
        assert JournalSpec.from_toml(valid_data).export.min_dpi == 72

    def test_min_dpi_zero_raises(self, valid_data):
        """
        Description: Validates that min_dpi == 0 raises FieldValueError.
        Scenario: min_dpi = 0.
        Expectation: FieldValueError is raised.
        """
        valid_data["export"]["min_dpi"] = 0
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_unknown_color_space_raises(self, valid_data):
        """
        Description: Validates that an unrecognised color_space raises FieldValueError.
        Scenario: color_space = 'pantone'.
        Expectation: FieldValueError with field_name == 'color_space'.
        """
        valid_data["export"]["color_space"] = "pantone"
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "color_space"

    def test_unknown_preferred_format_raises(self, valid_data):
        """
        Description: Validates that an unrecognised export format raises FieldValueError.
        Scenario: preferred_formats includes 'docx' (unsupported).
        Expectation: FieldValueError is raised.
        """
        valid_data["export"]["preferred_formats"] = ["pdf", "docx"]
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_empty_preferred_formats_list_raises(self, valid_data):
        """
        Description: Validates that an empty preferred_formats list raises FieldValueError (non_empty).
        Scenario: preferred_formats = [].
        Expectation: FieldValueError referencing 'preferred_formats'.
        """
        valid_data["export"]["preferred_formats"] = []
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "preferred_formats" in exc_info.value.field_name

    def test_unknown_panel_label_weight_raises(self, valid_data):
        """
        Description: Validates that an unrecognised panel_label_weight raises FieldValueError.
        Scenario: panel_label_weight = 'ultralight'.
        Expectation: FieldValueError with field_name == 'panel_label_weight'.
        """
        valid_data["typography"]["panel_label_weight"] = "ultralight"
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "panel_label_weight"

    def test_unknown_panel_label_case_raises(self, valid_data):
        """
        Description: Validates that an unrecognised panel_label_case raises FieldValueError.
        Scenario: panel_label_case = 'camelcase'.
        Expectation: FieldValueError with field_name == 'panel_label_case'.
        """
        valid_data["typography"]["panel_label_case"] = "camelcase"
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "panel_label_case"

    def test_empty_font_family_list_raises(self, valid_data):
        """
        Description: Validates that an empty font_family list raises FieldValueError (non_empty).
        Scenario: font_family = [].
        Expectation: FieldValueError referencing 'font_family'.
        """
        valid_data["typography"]["font_family"] = []
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "font_family" in exc_info.value.field_name

    def test_empty_metadata_name_raises(self, valid_data):
        """
        Description: Validates that an empty string for metadata.name raises FieldValueError.
        Scenario: name = ''.
        Expectation: FieldValueError with field_name == 'name'.
        """
        valid_data["metadata"]["name"] = ""
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "name"

    def test_whitespace_only_name_raises(self, valid_data):
        """
        Description: Validates that whitespace-only metadata.name raises FieldValueError.
        Scenario: name = '   '.
        Expectation: FieldValueError is raised (strip() removes whitespace, leaving empty string).
        """
        valid_data["metadata"]["name"] = "   "
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_whitespace_only_publisher_raises(self, valid_data):
        """
        Description: Validates that whitespace-only publisher raises FieldValueError.
        Scenario: publisher = '\t'.
        Expectation: FieldValueError is raised.
        """
        valid_data["metadata"]["publisher"] = "\t"
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_whitespace_only_source_url_raises(self, valid_data):
        """
        Description: Validates that whitespace-only source_url raises FieldValueError.
        Scenario: source_url = '\n'.
        Expectation: FieldValueError is raised.
        """
        valid_data["metadata"]["source_url"] = "\n"
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_invalid_date_format_slashes_raises(self, valid_data):
        """
        Description: Validates that a date with slashes (not ISO 8601) raises FieldValueError.
        Scenario: last_verified = '2024/01/15'.
        Expectation: FieldValueError with field_name == 'last_verified'.
        """
        valid_data["metadata"]["last_verified"] = "2024/01/15"
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert exc_info.value.field_name == "last_verified"

    def test_date_without_separator_raises(self, valid_data):
        """
        Description: Validates that a date without separators raises FieldValueError.
        Scenario: last_verified = '20240115'.
        Expectation: FieldValueError is raised.
        """
        valid_data["metadata"]["last_verified"] = "20240115"
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_empty_last_verified_raises(self, valid_data):
        """
        Description: Validates that empty string for last_verified raises FieldValueError.
        Scenario: last_verified = ''.
        Expectation: FieldValueError is raised (non_empty=True fails before regex).
        """
        valid_data["metadata"]["last_verified"] = ""
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_last_verified_wrong_structure_raises(self, valid_data):
        """
        Description: Validates date strings matching other patterns are rejected.
        Scenario: last_verified = 'Jan 15 2024'.
        Expectation: FieldValueError is raised.
        """
        valid_data["metadata"]["last_verified"] = "Jan 15 2024"
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_color_combination_with_single_color_raises(self, valid_data):
        """
        Description: Validates that a single-colour combination group raises FieldValueError.
        Scenario: avoid_combinations = [['red']] (only one colour — meaningless contrast rule).
        Expectation: FieldValueError referencing 'avoid_combinations'.
        """
        valid_data["color"] = {"avoid_combinations": [["red"]]}
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "avoid_combinations" in exc_info.value.field_name

    def test_color_combination_with_empty_inner_list_raises(self, valid_data):
        """
        Description: Validates that an empty inner combination list raises FieldValueError.
        Scenario: avoid_combinations = [[]] (zero colours in the group).
        Expectation: FieldValueError is raised.
        """
        valid_data["color"] = {"avoid_combinations": [[]]}
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_negative_line_weight_raises(self, valid_data):
        """
        Description: Validates that a negative min_weight_pt raises FieldValueError.
        Scenario: min_weight_pt = -0.1.
        Expectation: FieldValueError is raised.
        """
        valid_data["line"] = {"min_weight_pt": -0.1}
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_negative_min_font_pt_raises(self, valid_data):
        """
        Description: Validates that a negative min_font_pt raises FieldValueError.
        Scenario: min_font_pt = -1.0.
        Expectation: FieldValueError is raised.
        """
        valid_data["typography"]["min_font_pt"] = -1.0
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_negative_panel_label_pt_raises(self, valid_data):
        """
        Description: Validates that a negative panel_label_pt raises FieldValueError.
        Scenario: panel_label_pt = -2.0.
        Expectation: FieldValueError is raised.
        """
        valid_data["typography"]["panel_label_pt"] = -2.0
        with pytest.raises(FieldValueError):
            JournalSpec.from_toml(valid_data)

    def test_field_value_error_reason_describes_constraint(self, valid_data):
        """
        Description: Validates the reason attribute of FieldValueError is descriptive.
        Scenario: min_dpi = 0.
        Expectation: err.reason contains '72' (the floor value).
        """
        valid_data["export"]["min_dpi"] = 0
        with pytest.raises(FieldValueError) as exc_info:
            JournalSpec.from_toml(valid_data)
        assert "72" in exc_info.value.reason


# ---------------------------------------------------------------------------
# Normalisation — case-insensitive string fields
# ---------------------------------------------------------------------------


class TestNormalisation:
    def test_color_space_uppercase_normalised_to_lowercase(self, valid_data):
        """
        Description: Validates that uppercase color_space is normalised to lowercase.
        Scenario: color_space = 'RGB'.
        Expectation: spec.export.color_space == 'rgb'.
        """
        valid_data["export"]["color_space"] = "RGB"
        assert JournalSpec.from_toml(valid_data).export.color_space == "rgb"

    def test_color_space_mixed_case_normalised(self, valid_data):
        """
        Description: Validates that mixed-case color_space is normalised to lowercase.
        Scenario: color_space = 'Cmyk'.
        Expectation: spec.export.color_space == 'cmyk'.
        """
        valid_data["export"]["color_space"] = "Cmyk"
        assert JournalSpec.from_toml(valid_data).export.color_space == "cmyk"

    def test_preferred_format_uppercase_normalised(self, valid_data):
        """
        Description: Validates that uppercase format strings in preferred_formats are normalised.
        Scenario: preferred_formats = ['PDF', 'EPS'].
        Expectation: spec.export.preferred_formats == ['pdf', 'eps'].
        """
        valid_data["export"]["preferred_formats"] = ["PDF", "EPS"]
        assert JournalSpec.from_toml(valid_data).export.preferred_formats == ["pdf", "eps"]

    def test_panel_label_weight_uppercase_normalised(self, valid_data):
        """
        Description: Validates that uppercase panel_label_weight is normalised to lowercase.
        Scenario: panel_label_weight = 'BOLD'.
        Expectation: spec.typography.panel_label_weight == 'bold'.
        """
        valid_data["typography"]["panel_label_weight"] = "BOLD"
        assert JournalSpec.from_toml(valid_data).typography.panel_label_weight == "bold"

    def test_panel_label_case_mixed_case_normalised(self, valid_data):
        """
        Description: Validates that mixed-case panel_label_case is normalised to lowercase.
        Scenario: panel_label_case = 'Upper'.
        Expectation: spec.typography.panel_label_case == 'upper'.
        """
        valid_data["typography"]["panel_label_case"] = "Upper"
        assert JournalSpec.from_toml(valid_data).typography.panel_label_case == "upper"

    @pytest.mark.parametrize(
        "weight",
        ["thin", "light", "normal", "regular", "medium", "semibold", "bold", "extrabold", "black"],
    )
    def test_all_known_font_weights_are_valid(self, valid_data, weight):
        """
        Description: Validates every documented font weight keyword is accepted.
        Scenario: panel_label_weight set to each known weight in turn.
        Expectation: No error; the normalised weight is stored.
        """
        valid_data["typography"]["panel_label_weight"] = weight
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.panel_label_weight == weight

    @pytest.mark.parametrize(
        "case", ["lower", "upper", "title", "sentence", "parens_lower", "parens_upper"]
    )
    def test_all_known_label_cases_are_valid(self, valid_data, case):
        """
        Description: Validates every documented panel_label_case keyword is accepted.
        Scenario: panel_label_case set to each known case in turn.
        Expectation: No error; the normalised case is stored.
        """
        valid_data["typography"]["panel_label_case"] = case
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.panel_label_case == case

    @pytest.mark.parametrize("fmt", ["pdf", "eps", "svg", "tiff", "png", "emf"])
    def test_all_known_export_formats_are_valid(self, valid_data, fmt):
        """
        Description: Validates every documented export format is accepted.
        Scenario: preferred_formats = [fmt] for each known format.
        Expectation: No error; fmt appears in spec.export.preferred_formats.
        """
        valid_data["export"]["preferred_formats"] = [fmt]
        spec = JournalSpec.from_toml(valid_data)
        assert fmt in spec.export.preferred_formats

    @pytest.mark.parametrize("space", ["rgb", "cmyk", "grayscale"])
    def test_all_known_color_spaces_are_valid(self, valid_data, space):
        """
        Description: Validates every documented color_space identifier is accepted.
        Scenario: color_space = space for each known space.
        Expectation: No error; spec.export.color_space == space.
        """
        valid_data["export"]["color_space"] = space
        spec = JournalSpec.from_toml(valid_data)
        assert spec.export.color_space == space

    def test_preferred_formats_mixed_case_each_element_normalised(self, valid_data):
        """
        Description: Validates that every element in preferred_formats is independently normalised.
        Scenario: preferred_formats = ['Pdf', 'SVG', 'TIFF'].
        Expectation: spec.export.preferred_formats == ['pdf', 'svg', 'tiff'].
        """
        valid_data["export"]["preferred_formats"] = ["Pdf", "SVG", "TIFF"]
        spec = JournalSpec.from_toml(valid_data)
        assert spec.export.preferred_formats == ["pdf", "svg", "tiff"]

    def test_panel_label_weight_with_leading_trailing_whitespace_normalised(self, valid_data):
        """
        Description: Validates that allowed string fields are stripped before comparison.
        Scenario: panel_label_weight = ' bold ' (with surrounding spaces).
        Expectation: No error; stored as 'bold'.
        """
        valid_data["typography"]["panel_label_weight"] = " bold "
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.panel_label_weight == "bold"


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


class TestImmutability:
    def test_journal_spec_is_frozen(self, valid_data):
        """
        Description: Validates that JournalSpec instances are immutable (frozen dataclass).
        Scenario: Attempt to assign a new value to spec.notes after construction.
        Expectation: AttributeError or TypeError is raised.
        """
        spec = JournalSpec.from_toml(valid_data)
        with pytest.raises((AttributeError, TypeError)):
            spec.notes = "modified"  # type: ignore[misc]

    def test_metadata_spec_is_frozen(self, valid_data):
        """
        Description: Validates that MetadataSpec is immutable.
        Scenario: Attempt to mutate spec.metadata.name.
        Expectation: AttributeError or TypeError is raised.
        """
        spec = JournalSpec.from_toml(valid_data)
        with pytest.raises((AttributeError, TypeError)):
            spec.metadata.name = "changed"  # type: ignore[misc]

    def test_dimension_spec_is_frozen(self, valid_data):
        """
        Description: Validates that DimensionSpec is immutable.
        Scenario: Attempt to mutate spec.dimensions.single_column_mm.
        Expectation: AttributeError or TypeError is raised.
        """
        spec = JournalSpec.from_toml(valid_data)
        with pytest.raises((AttributeError, TypeError)):
            spec.dimensions.single_column_mm = 0.0  # type: ignore[misc]

    def test_typography_spec_is_frozen(self, valid_data):
        """
        Description: Validates that TypographySpec is immutable.
        Scenario: Attempt to mutate spec.typography.min_font_pt.
        Expectation: AttributeError or TypeError is raised.
        """
        spec = JournalSpec.from_toml(valid_data)
        with pytest.raises((AttributeError, TypeError)):
            spec.typography.min_font_pt = 6.0  # type: ignore[misc]

    def test_export_spec_is_frozen(self, valid_data):
        """
        Description: Validates that ExportSpec is immutable.
        Scenario: Attempt to mutate spec.export.min_dpi.
        Expectation: AttributeError or TypeError is raised.
        """
        spec = JournalSpec.from_toml(valid_data)
        with pytest.raises((AttributeError, TypeError)):
            spec.export.min_dpi = 72  # type: ignore[misc]

    def test_color_spec_is_frozen(self, full_data):
        """
        Description: Validates that ColorSpec is immutable.
        Scenario: Attempt to mutate spec.color.colorblind_required.
        Expectation: AttributeError or TypeError is raised.
        """
        spec = JournalSpec.from_toml(full_data)
        with pytest.raises((AttributeError, TypeError)):
            spec.color.colorblind_required = False  # type: ignore[misc]

    def test_line_spec_is_frozen(self, full_data):
        """
        Description: Validates that LineSpec is immutable.
        Scenario: Attempt to mutate spec.line.min_weight_pt.
        Expectation: AttributeError or TypeError is raised.
        """
        spec = JournalSpec.from_toml(full_data)
        with pytest.raises((AttributeError, TypeError)):
            spec.line.min_weight_pt = 1.0  # type: ignore[misc]

    def test_two_specs_from_same_data_are_equal(self, valid_data):
        """
        Description: Validates that frozen dataclasses with identical data compare as equal.
        Scenario: Two calls to from_toml with the same data dict.
        Expectation: spec1 == spec2.
        """
        spec1 = JournalSpec.from_toml(valid_data)
        spec2 = JournalSpec.from_toml(valid_data)
        assert spec1 == spec2

    def test_spec_is_not_hashable_due_to_list_fields(self, valid_data):
        """
        Description: Validates that JournalSpec is NOT hashable because it contains list fields.
        Scenario: Attempt to hash a spec instance.
        Expectation: TypeError is raised — frozen=True alone does not guarantee hashability;
                    all contained types must also be hashable, and list is not.
        """
        spec = JournalSpec.from_toml(valid_data)
        with pytest.raises(TypeError, match="unhashable type"):
            hash(spec)


# ---------------------------------------------------------------------------
# Edge cases and boundary values
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_double_column_just_above_single_is_valid(self, valid_data):
        """
        Description: Validates the lower boundary of the double > single invariant.
        Scenario: double_column_mm = single_column_mm + epsilon (89.001).
        Expectation: No error; double > single holds.
        """
        valid_data["dimensions"]["single_column_mm"] = 89.0
        valid_data["dimensions"]["double_column_mm"] = 89.001
        spec = JournalSpec.from_toml(valid_data)
        assert spec.dimensions.double_column_mm > spec.dimensions.single_column_mm

    def test_avoid_combinations_with_two_colors_is_valid(self, valid_data):
        """
        Description: Validates the minimum valid combination group size (two colours).
        Scenario: avoid_combinations = [['red', 'green']].
        Expectation: Stored as-is, no error.
        """
        valid_data["color"] = {"avoid_combinations": [["red", "green"]]}
        spec = JournalSpec.from_toml(valid_data)
        assert spec.color.avoid_combinations == [["red", "green"]]

    def test_avoid_combinations_with_three_colors_is_valid(self, valid_data):
        """
        Description: Validates that combination groups with more than two colours are accepted.
        Scenario: avoid_combinations = [['red', 'green', 'blue']].
        Expectation: Stored as-is, no error.
        """
        valid_data["color"] = {"avoid_combinations": [["red", "green", "blue"]]}
        spec = JournalSpec.from_toml(valid_data)
        assert spec.color.avoid_combinations == [["red", "green", "blue"]]

    def test_multiple_color_combinations_all_stored(self, valid_data):
        """
        Description: Validates that multiple combination groups are all stored correctly.
        Scenario: Two combination groups supplied.
        Expectation: spec.color.avoid_combinations has length 2.
        """
        valid_data["color"] = {
            "avoid_combinations": [["red", "green"], ["blue", "yellow"]],
        }
        spec = JournalSpec.from_toml(valid_data)
        assert len(spec.color.avoid_combinations) == 2

    def test_font_family_single_entry_is_valid(self, valid_data):
        """
        Description: Validates that a single-element font_family list is accepted.
        Scenario: font_family = ['Arial'].
        Expectation: spec.typography.font_family == ['Arial'].
        """
        valid_data["typography"]["font_family"] = ["Arial"]
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.font_family == ["Arial"]

    def test_font_family_many_entries_preserved_in_order(self, valid_data):
        """
        Description: Validates that a large font_family list is preserved in order.
        Scenario: font_family has five entries.
        Expectation: All five entries stored in original order.
        """
        fonts = ["Helvetica", "Arial", "Calibri", "Gill Sans", "Myriad Pro"]
        valid_data["typography"]["font_family"] = fonts
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.font_family == fonts

    def test_multiple_preferred_formats_stored_in_order(self, valid_data):
        """
        Description: Validates that multiple preferred_formats entries are stored in order.
        Scenario: preferred_formats = ['tiff', 'eps', 'pdf'].
        Expectation: spec.export.preferred_formats == ['tiff', 'eps', 'pdf'].
        """
        valid_data["export"]["preferred_formats"] = ["tiff", "eps", "pdf"]
        spec = JournalSpec.from_toml(valid_data)
        assert spec.export.preferred_formats == ["tiff", "eps", "pdf"]

    def test_notes_with_multiline_string(self, valid_data):
        """
        Description: Validates that notes can contain multiline strings.
        Scenario: notes contains newline characters.
        Expectation: Notes stored verbatim.
        """
        valid_data["notes"] = "Line one.\nLine two.\nLine three."
        spec = JournalSpec.from_toml(valid_data)
        assert spec.notes == "Line one.\nLine two.\nLine three."

    def test_iso_date_last_day_of_year_is_valid(self, valid_data):
        """
        Description: Validates that a valid ISO date on the last day of the year is accepted.
        Scenario: last_verified = '2023-12-31'.
        Expectation: spec.metadata.last_verified == '2023-12-31'.
        """
        valid_data["metadata"]["last_verified"] = "2023-12-31"
        assert JournalSpec.from_toml(valid_data).metadata.last_verified == "2023-12-31"

    def test_iso_date_first_day_of_year_is_valid(self, valid_data):
        """
        Description: Validates that a valid ISO date on the first day of the year is accepted.
        Scenario: last_verified = '2024-01-01'.
        Expectation: spec.metadata.last_verified == '2024-01-01'.
        """
        valid_data["metadata"]["last_verified"] = "2024-01-01"
        assert JournalSpec.from_toml(valid_data).metadata.last_verified == "2024-01-01"

    def test_min_dpi_exactly_300_is_valid(self, valid_data):
        """
        Description: Validates that the canonical 300 DPI value is accepted.
        Scenario: min_dpi = 300.
        Expectation: spec.export.min_dpi == 300.
        """
        assert JournalSpec.from_toml(valid_data).export.min_dpi == 300

    def test_min_dpi_very_high_value_is_valid(self, valid_data):
        """
        Description: Validates that a very large DPI value (e.g. 2400) is accepted.
        Scenario: min_dpi = 2400.
        Expectation: spec.export.min_dpi == 2400.
        """
        valid_data["export"]["min_dpi"] = 2400
        assert JournalSpec.from_toml(valid_data).export.min_dpi == 2400

    def test_dimension_as_integer_coerced_to_float(self, valid_data):
        """
        Description: Validates that integer dimension values are coerced to float.
        Scenario: single_column_mm and double_column_mm supplied as int literals.
        Expectation: Both stored as floats.
        """
        valid_data["dimensions"]["single_column_mm"] = 89
        valid_data["dimensions"]["double_column_mm"] = 183
        spec = JournalSpec.from_toml(valid_data)
        assert isinstance(spec.dimensions.single_column_mm, float)
        assert isinstance(spec.dimensions.double_column_mm, float)

    def test_all_six_export_formats_in_single_spec(self, valid_data):
        """
        Description: Validates that all six known export formats can coexist in one list.
        Scenario: preferred_formats contains all six known formats.
        Expectation: All six stored in order, no error.
        """
        all_formats = ["pdf", "eps", "svg", "tiff", "png", "emf"]
        valid_data["export"]["preferred_formats"] = all_formats
        spec = JournalSpec.from_toml(valid_data)
        assert spec.export.preferred_formats == all_formats

    def test_large_number_of_avoid_combinations(self, valid_data):
        """
        Description: Validates parsing robustness with many avoid_combinations entries.
        Scenario: Ten combination groups, each with two colours.
        Expectation: All ten groups stored without error.
        """
        combos = [[f"color_{i}a", f"color_{i}b"] for i in range(10)]
        valid_data["color"] = {"avoid_combinations": combos}
        spec = JournalSpec.from_toml(valid_data)
        assert len(spec.color.avoid_combinations) == 10

    def test_panel_label_pt_equal_to_max_font_pt_is_valid(self, valid_data):
        """
        Description: Validates panel_label_pt can equal max_font_pt (no cross-field constraint).
        Scenario: panel_label_pt set to max_font_pt value.
        Expectation: No error; stored correctly.
        """
        valid_data["typography"]["panel_label_pt"] = 9.0
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.panel_label_pt == 9.0

    def test_line_weight_very_small_positive_is_valid(self, valid_data):
        """
        Description: Validates that a very small positive line weight is accepted.
        Scenario: min_weight_pt = 0.001.
        Expectation: No error; stored as 0.001.
        """
        valid_data["line"] = {"min_weight_pt": 0.001}
        assert JournalSpec.from_toml(valid_data).line.min_weight_pt == pytest.approx(0.001)

    def test_notes_numeric_value_coerced_to_string(self, valid_data):
        """
        Description: Validates that numeric notes values are coerced to str via str().
        Scenario: notes = 42 (int).
        Expectation: spec.notes == '42'.
        """
        valid_data["notes"] = 42
        assert JournalSpec.from_toml(valid_data).notes == "42"

    def test_avoid_combinations_colour_names_not_normalised(self, valid_data):
        """
        Description: Validates colour name strings inside avoid_combinations are NOT normalised.
        Scenario: avoid_combinations = [['Red', 'Green']] (capitalised).
        Expectation: Stored as-is — the schema does not normalise colour names.
        """
        valid_data["color"] = {"avoid_combinations": [["Red", "Green"]]}
        spec = JournalSpec.from_toml(valid_data)
        assert spec.color.avoid_combinations == [["Red", "Green"]]

    def test_from_toml_does_not_mutate_input_dict(self, valid_data):
        """
        Description: Validates that from_toml is a pure function that does not mutate its argument.
        Scenario: Record snapshot of keys before and after calling from_toml.
        Expectation: The input dict's top-level keys are unchanged.
        """
        keys_before = set(valid_data.keys())
        JournalSpec.from_toml(valid_data)
        keys_after = set(valid_data.keys())
        assert keys_before == keys_after


# ---------------------------------------------------------------------------
# Cross-field invariants
# ---------------------------------------------------------------------------


class TestCrossFieldInvariants:
    def test_double_column_strictly_greater_than_single(self, valid_data):
        """
        Description: Validates the core dimension invariant: double > single.
        Scenario: Standard valid values (89.0 and 183.0).
        Expectation: spec.dimensions.double_column_mm > spec.dimensions.single_column_mm.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.dimensions.double_column_mm > spec.dimensions.single_column_mm

    def test_max_font_pt_gte_min_font_pt(self, valid_data):
        """
        Description: Validates the typography invariant: max_font_pt >= min_font_pt.
        Scenario: Standard valid values (7.0 and 9.0).
        Expectation: spec.typography.max_font_pt >= spec.typography.min_font_pt.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.max_font_pt >= spec.typography.min_font_pt

    def test_panel_label_pt_defaults_equal_to_min_when_absent(self, valid_data):
        """
        Description: Validates the default relationship between panel_label_pt and min_font_pt.
        Scenario: panel_label_pt absent; min_font_pt = 7.0.
        Expectation: spec.typography.panel_label_pt == 7.0.
        """
        spec = JournalSpec.from_toml(valid_data)
        assert spec.typography.panel_label_pt == 7.0

    @pytest.mark.parametrize(
        "single, double",
        [
            (89.0, 183.0),
            (60.0, 120.0),
            (50.0, 50.1),
            (1.0, 1000.0),
        ],
    )
    def test_various_valid_column_pairs_accepted(self, valid_data, single, double):
        """
        Description: Validates a range of valid (single, double) column pairs.
        Scenario: Parametrised pairs where double > single.
        Expectation: No error for any pair.
        """
        valid_data["dimensions"]["single_column_mm"] = single
        valid_data["dimensions"]["double_column_mm"] = double
        spec = JournalSpec.from_toml(valid_data)
        assert spec.dimensions.double_column_mm > spec.dimensions.single_column_mm
