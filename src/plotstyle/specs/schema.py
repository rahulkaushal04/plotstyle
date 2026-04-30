"""Journal specification schema: typed dataclasses for TOML spec data.

Defines frozen dataclasses representing a parsed journal specification,
exception types raised during validation, and private parsing helpers
that populate each dataclass from a raw TOML dictionary.

Classes
-------
JournalSpec
    Top-level specification combining all sub-specifications.
MetadataSpec, DimensionSpec, TypographySpec, ExportSpec, ColorSpec, LineSpec
    Sub-specifications covering each aspect of the journal requirements.

Exceptions
----------
JournalSpecError
    Base exception for all schema parse errors.
MissingFieldError
    Raised when a required TOML field is absent.
FieldTypeError
    Raised when a field value cannot be cast to the expected type.
FieldValueError
    Raised when a field value fails a domain constraint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from dataclasses import replace as _dc_replace
from typing import Any, Final

__all__: list[str] = [
    "ColorSpec",
    "DimensionSpec",
    "ExportSpec",
    "FieldTypeError",
    "FieldValueError",
    "JournalSpec",
    "JournalSpecError",
    "LineSpec",
    "MetadataSpec",
    "MissingFieldError",
    "TypographySpec",
]

_KNOWN_FORMATS: Final[frozenset[str]] = frozenset(
    {"ai", "pdf", "eps", "svg", "tiff", "tif", "png", "emf", "jpg", "jpeg", "ps"}
)

_KNOWN_COLOR_SPACES: Final[frozenset[str]] = frozenset({"rgb", "cmyk", "grayscale"})

_KNOWN_FONT_WEIGHTS: Final[frozenset[str]] = frozenset(
    {
        "thin",
        "light",
        "normal",
        "regular",
        "medium",
        "semibold",
        "bold",
        "extrabold",
        "black",
    }
)

_KNOWN_LABEL_CASES: Final[frozenset[str]] = frozenset(
    {"lower", "upper", "title", "sentence", "parens_lower", "parens_upper"}
)

_MIN_DPI_FLOOR: Final[int] = 72

_ISO_DATE_RE: Final[re.Pattern[str]] = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Conservative, research-grade defaults for fields journals may not specify.
# These are NOT journal-official values; they are library assumptions used only
# when a journal's guidelines are silent on a particular requirement.
_LIBRARY_DEFAULTS: Final[dict[str, Any]] = {
    "typography.font_family": ["Helvetica", "Arial"],
    "typography.font_fallback": "sans-serif",
    "typography.min_font_pt": 6.0,
    "typography.max_font_pt": 10.0,
    "typography.panel_label_weight": "bold",
    "typography.panel_label_case": "lower",
    "line.min_weight_pt": 0.5,
}


class JournalSpecError(ValueError):
    """Base exception for all schema parse errors."""


class MissingFieldError(JournalSpecError):
    """Raised when a required TOML field is absent.

    Parameters
    ----------
    table : str
        TOML section name (e.g. ``"metadata"``, ``"dimensions"``).
    field_name : str
        Key that was expected but not found in *table*.

    Attributes
    ----------
    table : str
        TOML section name where the field was missing.
    field_name : str
        The key that was required but absent.
    """

    def __init__(self, table: str, field_name: str) -> None:
        super().__init__(f"[{table}] Missing required field {field_name!r}.")
        self.table: str = table
        self.field_name: str = field_name


class FieldTypeError(JournalSpecError):
    """Raised when a TOML field value cannot be cast to the expected type.

    Parameters
    ----------
    table : str
        TOML section name (e.g. ``"typography"``).
    field_name : str
        Key whose value had the wrong type.
    expected : str
        Human-readable description of the expected type (e.g. ``"float"``).
    got : object
        The actual raw value that failed the cast.

    Attributes
    ----------
    table : str
        TOML section name containing the offending field.
    field_name : str
        The key whose value had the wrong type.
    expected : str
        Human-readable expected type string.
    got : object
        The raw value that could not be cast.
    """

    def __init__(self, table: str, field_name: str, expected: str, got: object) -> None:
        super().__init__(f"[{table}.{field_name}] Expected {expected}, got {got!r}.")
        self.table: str = table
        self.field_name: str = field_name
        self.expected: str = expected
        self.got: object = got


class FieldValueError(JournalSpecError):
    """Raised when a field has the right type but fails a domain constraint.

    Parameters
    ----------
    table : str
        TOML section name.
    field_name : str
        Key whose value violated the constraint.
    reason : str
        Human-readable explanation of the violation.

    Attributes
    ----------
    table : str
        TOML section name containing the offending field.
    field_name : str
        The key whose value violated the domain constraint.
    reason : str
        Human-readable explanation of why the value was rejected.
    """

    def __init__(self, table: str, field_name: str, reason: str) -> None:
        super().__init__(f"[{table}.{field_name}] {reason}")
        self.table: str = table
        self.field_name: str = field_name
        self.reason: str = reason


def _require(table: dict[str, Any], table_name: str, key: str) -> Any:  # noqa: ANN401
    """Return ``table[key]``, raising `MissingFieldError` if absent.

    Parameters
    ----------
    table : dict[str, Any]
        Raw TOML sub-table to look up.
    table_name : str
        Section name used in error messages (e.g. ``"metadata"``).
    key : str
        Dict key to retrieve.

    Returns
    -------
    Any
        The raw value at ``table[key]``.

    Raises
    ------
    MissingFieldError
        If *key* is absent from *table*.
    """
    try:
        return table[key]
    except KeyError:
        raise MissingFieldError(table_name, key) from None


def _cast_float(
    table: dict[str, Any],
    table_name: str,
    key: str,
    *,
    default: float | None = None,
    min_val: float | None = None,
    max_val: float | None = None,
) -> float:
    """Extract and validate a float field from a TOML sub-table.

    Parameters
    ----------
    table : dict[str, Any]
        Raw TOML sub-table.
    table_name : str
        Section name for error messages.
    key : str
        Field key to extract.
    default : float | None, optional
        Fallback when *key* is absent. When ``None``, *key* is required.
    min_val : float | None, optional
        Inclusive lower bound.
    max_val : float | None, optional
        Inclusive upper bound.

    Returns
    -------
    float
        The extracted and validated float.

    Raises
    ------
    MissingFieldError
        If *key* is absent and *default* is ``None``.
    FieldTypeError
        If the raw value cannot be cast to ``float``.
    FieldValueError
        If the value falls outside ``[min_val, max_val]``.
    """
    raw = table.get(key, default) if default is not None else _require(table, table_name, key)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise FieldTypeError(table_name, key, "float", raw) from None

    if min_val is not None and value < min_val:
        raise FieldValueError(table_name, key, f"must be ≥ {min_val}, got {value}")
    if max_val is not None and value > max_val:
        raise FieldValueError(table_name, key, f"must be ≤ {max_val}, got {value}")

    return value


def _cast_int(
    table: dict[str, Any],
    table_name: str,
    key: str,
    *,
    default: int | None = None,
    min_val: int | None = None,
) -> int:
    """Extract and validate an integer field from a TOML sub-table.

    Parameters
    ----------
    table : dict[str, Any]
        Raw TOML sub-table.
    table_name : str
        Section name for error messages.
    key : str
        Field key to extract.
    default : int | None, optional
        Fallback when *key* is absent. When ``None``, *key* is required.
    min_val : int | None, optional
        Inclusive lower bound.

    Returns
    -------
    int
        The extracted and validated integer.

    Raises
    ------
    MissingFieldError
        If *key* is absent and *default* is ``None``.
    FieldTypeError
        If the raw value cannot be cast to ``int``.
    FieldValueError
        If the value is below *min_val*.
    """
    raw = table.get(key, default) if default is not None else _require(table, table_name, key)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise FieldTypeError(table_name, key, "int", raw) from None

    if min_val is not None and value < min_val:
        raise FieldValueError(table_name, key, f"must be ≥ {min_val}, got {value}")

    return value


def _cast_str(
    table: dict[str, Any],
    table_name: str,
    key: str,
    *,
    default: str | None = None,
    allowed: frozenset[str] | None = None,
    non_empty: bool = False,
) -> str:
    """Extract and validate a string field from a TOML sub-table.

    Parameters
    ----------
    table : dict[str, Any]
        Raw TOML sub-table.
    table_name : str
        Section name for error messages.
    key : str
        Field key to extract.
    default : str | None, optional
        Fallback when *key* is absent. When ``None``, *key* is required.
    allowed : frozenset[str] | None, optional
        Permitted values; the raw string is stripped and lower-cased before
        comparison.
    non_empty : bool, optional
        When ``True``, reject empty or whitespace-only strings.

    Returns
    -------
    str
        The raw string, or normalised (stripped, lower-cased) when *allowed*
        is given.

    Raises
    ------
    MissingFieldError
        If *key* is absent and *default* is ``None``.
    FieldTypeError
        If the raw value is not a ``str``.
    FieldValueError
        If empty (with *non_empty=True*) or not in *allowed*.
    """
    raw = table.get(key, default) if default is not None else _require(table, table_name, key)
    if not isinstance(raw, str):
        raise FieldTypeError(table_name, key, "str", raw)
    if non_empty and not raw.strip():
        raise FieldValueError(table_name, key, "must not be empty")
    if allowed is not None:
        normalised = raw.strip().lower()
        if normalised not in allowed:
            raise FieldValueError(
                table_name,
                key,
                f"must be one of {sorted(allowed)!r}, got {raw!r}",
            )
        return normalised
    return raw


def _cast_bool(
    table: dict[str, Any],
    table_name: str,
    key: str,
    *,
    default: bool,
) -> bool:
    """Extract a boolean field from a TOML sub-table.

    Parameters
    ----------
    table : dict[str, Any]
        Raw TOML sub-table.
    table_name : str
        Section name for error messages.
    key : str
        Field key to extract.
    default : bool
        Fallback value when *key* is absent.

    Returns
    -------
    bool
        The extracted boolean value.

    Raises
    ------
    FieldTypeError
        If the raw value is not a ``bool``.
    """
    raw = table.get(key, default)
    if not isinstance(raw, bool):
        raise FieldTypeError(table_name, key, "bool", raw)
    return raw


def _cast_str_list(
    table: dict[str, Any],
    table_name: str,
    key: str,
    *,
    default: list[str] | None = None,
    non_empty: bool = False,
    allowed: frozenset[str] | None = None,
) -> list[str]:
    """Extract and validate a list-of-strings field from a TOML sub-table.

    Parameters
    ----------
    table : dict[str, Any]
        Raw TOML sub-table.
    table_name : str
        Section name for error messages.
    key : str
        Field key to extract.
    default : list[str] | None, optional
        Fallback list when *key* is absent. When ``None``, *key* is required.
    non_empty : bool, optional
        When ``True``, reject empty lists.
    allowed : frozenset[str] | None, optional
        Constraint set; each item is validated after stripping and lower-casing.

    Returns
    -------
    list[str]
        List of strings. Each item is normalised (stripped, lower-cased) when
        *allowed* is given.

    Raises
    ------
    MissingFieldError
        If *key* is absent and *default* is ``None``.
    FieldTypeError
        If the raw value is not a list, or any element is not a ``str``.
    FieldValueError
        If the list is empty (with *non_empty=True*) or contains a value not
        in *allowed*.
    """
    raw = table.get(key, default) if default is not None else _require(table, table_name, key)
    if not isinstance(raw, list):
        raise FieldTypeError(table_name, key, "list[str]", raw)
    if non_empty and not raw:
        raise FieldValueError(table_name, key, "list must contain at least one entry")

    result: list[str] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, str):
            raise FieldTypeError(table_name, f"{key}[{idx}]", "str", item)
        normalised = item.strip().lower() if allowed else item
        if allowed and normalised not in allowed:
            raise FieldValueError(
                table_name,
                f"{key}[{idx}]",
                f"must be one of {sorted(allowed)!r}, got {item!r}",
            )
        result.append(normalised if allowed else item)
    return result


@dataclass(frozen=True, slots=True)
class MetadataSpec:
    """Metadata describing the journal source and specification provenance.

    Attributes
    ----------
    name : str
        Display name of the journal (e.g. ``"Nature"``).
    publisher : str
        Publisher name (e.g. ``"Springer Nature"``).
    source_url : str
        URL of the author guidelines used as the specification source.
    last_verified : str
        ISO 8601 date (``YYYY-MM-DD``) when the guidelines were last reviewed.
    verified_by : str
        Name or identifier of the person who last verified the spec.
    """

    name: str
    publisher: str
    source_url: str
    last_verified: str
    verified_by: str


@dataclass(frozen=True, slots=True)
class DimensionSpec:
    """Physical column-width and height constraints (all values in mm).

    Fields are ``None`` when the journal's official guidelines do not specify
    a value. Check ``JournalSpec.assumed_fields`` or call
    ``JournalSpec.is_official()`` before relying on any dimension value.

    Attributes
    ----------
    single_column_mm : float | None
        Width in millimetres for a single-column figure, or ``None`` if
        the journal does not publish this value.
    double_column_mm : float | None
        Width in millimetres for a double-column (full-page) figure, or
        ``None`` if the journal does not publish this value.
    max_height_mm : float | None
        Maximum permitted figure height in millimetres, or ``None`` if
        the journal does not publish this value.
    """

    single_column_mm: float | None
    double_column_mm: float | None
    max_height_mm: float | None


@dataclass(frozen=True, slots=True)
class TypographySpec:
    """Typography constraints and preferences for figure text elements.

    Attributes
    ----------
    font_family : list[str]
        Ordered list of preferred font family names.
    font_fallback : str
        Generic CSS-style family name used when none of the preferred fonts
        are installed (e.g. ``"sans-serif"``).
    min_font_pt : float
        Minimum permitted font size in points.
    max_font_pt : float
        Maximum permitted font size in points.
    panel_label_pt : float
        Font size in points for panel labels (e.g. ``"a"``, ``"b"``).
    panel_label_weight : str
        Font weight for panel labels (e.g. ``"bold"``).
    panel_label_case : str
        Case transformation for panel labels (e.g. ``"lower"``, ``"upper"``).
    target_font_pt : float | None
        Recommended rendering font size in points, when the journal's
        guidelines state a preferred target distinct from the midpoint of
        ``[min_font_pt, max_font_pt]``.  ``None`` when absent from the TOML,
        in which case ``build_rcparams`` falls back to the midpoint heuristic.
        Must be within ``[min_font_pt, max_font_pt]`` when set.
    """

    font_family: list[str]
    font_fallback: str
    min_font_pt: float
    max_font_pt: float
    panel_label_pt: float
    panel_label_weight: str
    panel_label_case: str
    target_font_pt: float | None = None


@dataclass(frozen=True, slots=True)
class ExportSpec:
    """Export and rendering requirements for figure files.

    Attributes
    ----------
    preferred_formats : list[str]
        Recommended output formats in preference order
        (e.g. ``["pdf", "tiff"]``).
    min_dpi : int
        Minimum acceptable raster resolution in dots per inch.
    color_space : str
        Required colour space for submission (e.g. ``"rgb"``, ``"cmyk"``).
    font_embedding : bool
        Whether the journal requires embedded fonts in vector exports.
    editable_text : bool
        Whether the journal requires vector/editable text in EPS/PDF files.
    """

    preferred_formats: list[str]
    min_dpi: int
    color_space: str
    font_embedding: bool
    editable_text: bool


@dataclass(frozen=True, slots=True)
class ColorSpec:
    """Colour usage and accessibility requirements.

    Attributes
    ----------
    avoid_combinations : list[list[str]]
        Colour pairs that should not be used together due to accessibility
        constraints (e.g. ``[["red", "green"]]``).
    colorblind_required : bool
        Whether figures must pass all common colour-blindness simulations.
    grayscale_required : bool
        Whether figures must be interpretable in grayscale.
    """

    avoid_combinations: list[list[str]]
    colorblind_required: bool
    grayscale_required: bool


@dataclass(frozen=True, slots=True)
class LineSpec:
    """Line rendering constraints for figures.

    Attributes
    ----------
    min_weight_pt : float
        Minimum permitted line weight in points.
    """

    min_weight_pt: float


@dataclass(frozen=True, slots=True)
class JournalSpec:
    """Complete, validated journal figure-submission specification.

    Attributes
    ----------
    metadata : MetadataSpec
        Journal provenance and source information.
    dimensions : DimensionSpec
        Physical column-width and height limits.
    typography : TypographySpec
        Font, size, and panel-label constraints.
    export : ExportSpec
        File format, DPI, and embedding requirements.
    color : ColorSpec
        Colour usage and accessibility constraints.
    line : LineSpec
        Line rendering constraints.
    notes : str
        Free-form notes from the specification source; may be empty.
    key : str
        Lower-case registry identifier assigned by ``_with_key``
        (e.g. ``"nature"``). Empty until the spec is registered.
    """

    metadata: MetadataSpec
    dimensions: DimensionSpec
    typography: TypographySpec
    export: ExportSpec
    color: ColorSpec
    line: LineSpec
    notes: str = field(default="")
    assumed_fields: frozenset[str] = field(default_factory=frozenset)
    key: str = field(default="")

    def is_official(self, field_path: str) -> bool:
        """Return ``True`` if *field_path* came from the journal's official guidelines.

        Parameters
        ----------
        field_path : str
            Dot-notation field path, e.g. ``"typography.min_font_pt"`` or
            ``"line.min_weight_pt"``.

        Returns
        -------
        bool
            ``False`` when the field was absent from the TOML and a library
            default was used instead.
        """
        return field_path not in self.assumed_fields

    def _with_key(self, key: str) -> JournalSpec:
        """Return a copy of this spec with *key* set to the registry identifier.

        Parameters
        ----------
        key : str
            Lower-case spec file stem (e.g. ``"nature"``, ``"ieee"``).

        Returns
        -------
        JournalSpec
            A new instance identical to *self* except that ``key`` is set.
        """
        return _dc_replace(self, key=key)

    @classmethod
    def from_toml(cls, data: dict[str, Any]) -> JournalSpec:
        """Construct a validated ``JournalSpec`` from raw TOML data.

        Parameters
        ----------
        data : dict[str, Any]
            Raw dictionary from parsing a ``.toml`` spec file
            (e.g. via ``plotstyle._utils.io.load_toml``).

        Returns
        -------
        JournalSpec
            A fully validated, frozen ``JournalSpec`` instance.

        Raises
        ------
        MissingFieldError
            If a required TOML field is absent.
        FieldTypeError
            If a field value cannot be cast to the expected Python type.
        FieldValueError
            If a field value violates a domain constraint.
        """
        assumed: set[str] = set()
        return cls(
            metadata=cls._parse_metadata(_require(data, "root", "metadata")),
            dimensions=cls._parse_dimensions(data.get("dimensions", {}), assumed),
            typography=cls._parse_typography(_require(data, "root", "typography"), assumed),
            export=cls._parse_export(_require(data, "root", "export")),
            color=cls._parse_color(data.get("color", {})),
            line=cls._parse_line(data.get("line", {}), assumed),
            notes=str(data.get("notes", "")),
            assumed_fields=frozenset(assumed),
        )

    @staticmethod
    def _parse_metadata(raw: dict[str, Any]) -> MetadataSpec:
        """Parse and validate the ``[metadata]`` TOML sub-table.

        Parameters
        ----------
        raw : dict[str, Any]
            Raw ``[metadata]`` dict.

        Returns
        -------
        MetadataSpec
            A validated ``MetadataSpec`` instance.

        Raises
        ------
        MissingFieldError
            If a required field is absent.
        FieldValueError
            If ``last_verified`` is not in ``YYYY-MM-DD`` format.
        """
        t = "metadata"
        last_verified = _cast_str(raw, t, "last_verified", non_empty=True)
        if not _ISO_DATE_RE.match(last_verified):
            raise FieldValueError(
                t,
                "last_verified",
                f"must be in YYYY-MM-DD format, got {last_verified!r}",
            )

        return MetadataSpec(
            name=_cast_str(raw, t, "name", non_empty=True),
            publisher=_cast_str(raw, t, "publisher", non_empty=True),
            source_url=_cast_str(raw, t, "source_url", non_empty=True),
            last_verified=last_verified,
            verified_by=_cast_str(raw, t, "verified_by", default=""),
        )

    @staticmethod
    def _parse_dimensions(raw: dict[str, Any], assumed: set[str]) -> DimensionSpec:
        """Parse and validate the ``[dimensions]`` TOML sub-table.

        All three fields are optional. Missing fields receive ``None`` and their
        dot-notation paths are added to *assumed*. When both column widths are
        present, cross-validation (``double > single``) is applied.

        Parameters
        ----------
        raw : dict[str, Any]
            Raw ``[dimensions]`` dict (may be empty when the journal does not
            publish physical dimension constraints).
        assumed : set[str]
            Mutable set updated with the dot-notation path of each field that
            was absent from the TOML (e.g. ``"dimensions.single_column_mm"``).

        Returns
        -------
        DimensionSpec
            A validated ``DimensionSpec`` instance. Any field absent from
            *raw* is set to ``None``.

        Raises
        ------
        FieldTypeError
            If a present field cannot be cast to ``float``.
        FieldValueError
            If a present dimension is not strictly positive, or if both column
            widths are present but ``double_column_mm`` ≤ ``single_column_mm``.
        """
        t = "dimensions"

        def _optional_mm(key: str) -> float | None:
            if key not in raw:
                assumed.add(f"dimensions.{key}")
                return None
            val = raw[key]
            try:
                v = float(val)
            except (TypeError, ValueError):
                raise FieldTypeError(t, key, "float", val) from None
            if v <= 0:
                raise FieldValueError(t, key, f"must be > 0, got {v}")
            return v

        single = _optional_mm("single_column_mm")
        double = _optional_mm("double_column_mm")
        height = _optional_mm("max_height_mm")

        if single is not None and double is not None and double <= single:
            raise FieldValueError(
                t,
                "double_column_mm",
                f"must be > single_column_mm ({single}), got {double}",
            )

        return DimensionSpec(
            single_column_mm=single,
            double_column_mm=double,
            max_height_mm=height,
        )

    @staticmethod
    def _parse_typography(raw: dict[str, Any], assumed: set[str]) -> TypographySpec:
        """Parse and validate the ``[typography]`` TOML sub-table.

        Fields not present in the TOML fall back to :data:`_LIBRARY_DEFAULTS`
        and their dot-notation paths are recorded in *assumed* so callers can
        distinguish official values from library assumptions.

        Parameters
        ----------
        raw : dict[str, Any]
            Raw ``[typography]`` dict (may be empty when the journal does not
            define typography constraints).
        assumed : set[str]
            Mutable set that receives the dot-notation paths of every field
            that used a library default rather than an official journal value
            (e.g. ``"typography.min_font_pt"``).

        Returns
        -------
        TypographySpec
            A validated ``TypographySpec`` instance.

        Raises
        ------
        FieldValueError
            If ``max_font_pt`` < ``min_font_pt``, or if
            ``panel_label_weight`` or ``panel_label_case`` is unrecognised.
        """
        t = "typography"

        if "min_font_pt" not in raw:
            assumed.add("typography.min_font_pt")
        if "max_font_pt" not in raw:
            assumed.add("typography.max_font_pt")
        if "font_family" not in raw:
            assumed.add("typography.font_family")

        min_pt = _cast_float(
            raw,
            t,
            "min_font_pt",
            default=_LIBRARY_DEFAULTS["typography.min_font_pt"],
            min_val=0.0,
        )
        max_pt = _cast_float(
            raw,
            t,
            "max_font_pt",
            default=_LIBRARY_DEFAULTS["typography.max_font_pt"],
            min_val=0.0,
        )

        if max_pt < min_pt:
            raise FieldValueError(
                t,
                "max_font_pt",
                f"must be ≥ min_font_pt ({min_pt}), got {max_pt}",
            )

        # target_font_pt is optional. When present it must be a non-negative
        # float within the journal's compliance range [min_pt, max_pt].
        target_pt: float | None = None
        if "target_font_pt" in raw:
            raw_target = raw["target_font_pt"]
            try:
                target_pt = float(raw_target)
            except (TypeError, ValueError):
                raise FieldTypeError(t, "target_font_pt", "float", raw_target) from None
            if target_pt < 0.0:
                raise FieldValueError(t, "target_font_pt", f"must be ≥ 0, got {target_pt}")
            if not (min_pt <= target_pt <= max_pt):
                raise FieldValueError(
                    t,
                    "target_font_pt",
                    f"must be within [min_font_pt={min_pt}, max_font_pt={max_pt}], got {target_pt}",
                )

        return TypographySpec(
            font_family=_cast_str_list(
                raw,
                t,
                "font_family",
                default=_LIBRARY_DEFAULTS["typography.font_family"],
                non_empty=True,
            ),
            font_fallback=_cast_str(raw, t, "font_fallback", default="sans-serif"),
            min_font_pt=min_pt,
            max_font_pt=max_pt,
            panel_label_pt=_cast_float(raw, t, "panel_label_pt", default=min_pt, min_val=0.0),
            panel_label_weight=_cast_str(
                raw, t, "panel_label_weight", default="bold", allowed=_KNOWN_FONT_WEIGHTS
            ),
            panel_label_case=_cast_str(
                raw, t, "panel_label_case", default="lower", allowed=_KNOWN_LABEL_CASES
            ),
            target_font_pt=target_pt,
        )

    @staticmethod
    def _parse_export(raw: dict[str, Any]) -> ExportSpec:
        """Parse and validate the ``[export]`` TOML sub-table.

        Parameters
        ----------
        raw : dict[str, Any]
            Raw ``[export]`` dict.

        Returns
        -------
        ExportSpec
            A validated ``ExportSpec`` instance. Defaults: ``min_dpi=300``,
            ``color_space="rgb"``, ``font_embedding=True``,
            ``editable_text=False``.
        """
        t = "export"
        return ExportSpec(
            preferred_formats=_cast_str_list(
                raw,
                t,
                "preferred_formats",
                default=["pdf"],
                non_empty=True,
                allowed=_KNOWN_FORMATS,
            ),
            min_dpi=_cast_int(raw, t, "min_dpi", default=300, min_val=_MIN_DPI_FLOOR),
            color_space=_cast_str(
                raw, t, "color_space", default="rgb", allowed=_KNOWN_COLOR_SPACES
            ),
            font_embedding=_cast_bool(raw, t, "font_embedding", default=True),
            editable_text=_cast_bool(raw, t, "editable_text", default=False),
        )

    @staticmethod
    def _parse_color(raw: dict[str, Any]) -> ColorSpec:
        """Parse and validate the ``[color]`` TOML sub-table.

        All fields default to safe values; an empty dict is acceptable.

        Parameters
        ----------
        raw : dict[str, Any]
            Raw ``[color]`` dict (may be empty).

        Returns
        -------
        ColorSpec
            A validated ``ColorSpec`` instance.

        Raises
        ------
        FieldTypeError
            If ``avoid_combinations`` is not a list of string lists.
        FieldValueError
            If any combination entry has fewer than two colour names.
        """
        t = "color"
        raw_combos: list[Any] = raw.get("avoid_combinations", [])
        if not isinstance(raw_combos, list):
            raise FieldTypeError(t, "avoid_combinations", "list[list[str]]", raw_combos)

        avoid: list[list[str]] = []
        for combo_idx, combo in enumerate(raw_combos):
            field_path = f"avoid_combinations[{combo_idx}]"
            if not isinstance(combo, list):
                raise FieldTypeError(t, field_path, "list[str]", combo)
            if len(combo) < 2:
                raise FieldValueError(
                    t,
                    field_path,
                    "each combination must list at least two colours",
                )
            validated_combo: list[str] = []
            for item_idx, item in enumerate(combo):
                if not isinstance(item, str):
                    raise FieldTypeError(t, f"{field_path}[{item_idx}]", "str", item)
                validated_combo.append(item)
            avoid.append(validated_combo)

        return ColorSpec(
            avoid_combinations=avoid,
            colorblind_required=_cast_bool(raw, t, "colorblind_required", default=False),
            grayscale_required=_cast_bool(raw, t, "grayscale_required", default=False),
        )

    @staticmethod
    def _parse_line(raw: dict[str, Any], assumed: set[str]) -> LineSpec:
        """Parse and validate the ``[line]`` TOML sub-table.

        An empty dict is acceptable. When ``min_weight_pt`` is absent the
        library default (``0.5 pt``) is used and ``"line.min_weight_pt"`` is
        added to *assumed*.

        Parameters
        ----------
        raw : dict[str, Any]
            Raw ``[line]`` dict (may be empty).
        assumed : set[str]
            Mutable set updated when ``min_weight_pt`` falls back to the
            library default.

        Returns
        -------
        LineSpec
            A validated ``LineSpec`` instance.
        """
        if "min_weight_pt" not in raw:
            assumed.add("line.min_weight_pt")
        return LineSpec(
            min_weight_pt=_cast_float(
                raw,
                "line",
                "min_weight_pt",
                default=_LIBRARY_DEFAULTS["line.min_weight_pt"],
                min_val=0.0,
            ),
        )
