"""Journal specification schema — typed dataclasses for TOML spec data.

This module defines the complete schema for journal figure-submission
specifications parsed from TOML configuration files.  Each sub-spec maps
directly to a top-level TOML table (``[metadata]``, ``[dimensions]``, etc.),
and the root :class:`JournalSpec` composes them into a single validated,
immutable object.

Public types
------------
:class:`JournalSpec`
    Root specification object.  Construct via :meth:`JournalSpec.from_toml`.

:class:`MetadataSpec`
    Provenance and verification metadata.

:class:`DimensionSpec`
    Physical column-width and height constraints (all values in mm).

:class:`TypographySpec`
    Font family, size range, and panel-label formatting rules.

:class:`ExportSpec`
    File-format, DPI, colour-space, and font-embedding requirements.

:class:`ColorSpec`
    Colour-combination restrictions and accessibility requirements.

:class:`LineSpec`
    Minimum stroke-weight constraint.

Exceptions
----------
:class:`JournalSpecError`
    Base exception; all parse errors inherit from this class.

:class:`MissingFieldError`, :class:`FieldTypeError`, :class:`FieldValueError`
    Specific parse-error subtypes raised by :meth:`JournalSpec.from_toml`.

Typical usage
-------------
::

    import tomllib
    from plotstyle.specs.schema import JournalSpec

    with open("nature.toml", "rb") as fh:
        raw = tomllib.load(fh)

    spec = JournalSpec.from_toml(raw)
    print(spec.dimensions.single_column_mm)  # 89.0

Design notes
------------
* Every dataclass is **frozen** (immutable) and uses **slots** for reduced
  per-instance memory overhead — important when many specs are loaded at once.
* Validation is centralised in private helper functions so that
  :meth:`JournalSpec.from_toml` stays readable and each sub-spec constructor
  stays simple.
* All public exceptions inherit from :class:`JournalSpecError` so callers
  can catch the entire family with a single ``except`` clause.
* Inline TOML defaults are documented alongside each field so that the
  schema is self-describing without needing to cross-reference external docs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Supported export format identifiers (lowercase, without leading dot).
_KNOWN_FORMATS: Final[frozenset[str]] = frozenset(
    {"pdf", "eps", "svg", "tiff", "tif", "png", "emf", "jpg", "jpeg", "ps"}
)

#: Supported colour-space identifiers.
_KNOWN_COLOR_SPACES: Final[frozenset[str]] = frozenset({"rgb", "cmyk", "grayscale"})

#: Accepted CSS-style font-weight keywords.
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

#: Accepted text-transformation keywords for panel labels.
_KNOWN_LABEL_CASES: Final[frozenset[str]] = frozenset(
    {"lower", "upper", "title", "sentence", "parens_lower", "parens_upper"}
)

#: Minimum physically meaningful resolution in DPI.
_MIN_DPI_FLOOR: Final[int] = 72

#: ISO 8601 date pattern (YYYY-MM-DD) for validating ``last_verified``.
_ISO_DATE_RE: Final[re.Pattern[str]] = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class JournalSpecError(ValueError):
    """Base exception for all errors raised by this module.

    Inherits from :class:`ValueError` so that existing code catching the
    built-in exception continues to work without modification.

    All more specific parse errors (:class:`MissingFieldError`,
    :class:`FieldTypeError`, :class:`FieldValueError`) are subclasses of
    this class, so callers can catch the entire family with a single
    ``except JournalSpecError`` clause.
    """


class MissingFieldError(JournalSpecError):
    """Raised when a required TOML field is absent.

    Args:
        table:      Top-level TOML table name (e.g. ``"metadata"``).
        field_name: Missing key within *table*.

    Attributes
    ----------
    table
        The TOML table in which the field was expected.
    field_name
        The missing key name.

    Example::

        raise MissingFieldError("metadata", "publisher")
        # MissingFieldError: [metadata] Missing required field 'publisher'.
    """

    def __init__(self, table: str, field_name: str) -> None:
        super().__init__(f"[{table}] Missing required field {field_name!r}.")
        self.table: str = table
        self.field_name: str = field_name


class FieldTypeError(JournalSpecError):
    """Raised when a TOML field value cannot be cast to the expected type.

    Args:
        table:    Top-level TOML table name.
        field_name: Key within *table*.
        expected: Human-readable name of the expected type.
        got:      The actual value that failed conversion.

    Attributes
    ----------
    table
        The TOML table containing the offending field.
    field_name
        The key whose value has the wrong type.
    expected
        Human-readable expected type (e.g. ``"float"``).
    got
        The actual value received.

    Example::

        raise FieldTypeError("dimensions", "single_column_mm", "float", "wide")
        # FieldTypeError: [dimensions.single_column_mm] Expected float, got 'wide'.
    """

    def __init__(
        self,
        table: str,
        field_name: str,
        expected: str,
        got: object,
    ) -> None:
        super().__init__(f"[{table}.{field_name}] Expected {expected}, got {got!r}.")
        self.table: str = table
        self.field_name: str = field_name
        self.expected: str = expected
        self.got: object = got


class FieldValueError(JournalSpecError):
    """Raised when a field has the right type but fails a domain constraint.

    Args:
        table:      Top-level TOML table name.
        field_name: Key within *table*.
        reason:     Human-readable explanation of why the value is invalid.

    Attributes
    ----------
    table
        The TOML table containing the offending field.
    field_name
        The key whose value violated a constraint.
    reason
        Human-readable description of the violated constraint.

    Example::

        raise FieldValueError("export", "min_dpi", "must be ≥ 72, got 0")
        # FieldValueError: [export.min_dpi] must be ≥ 72, got 0
    """

    def __init__(self, table: str, field_name: str, reason: str) -> None:
        super().__init__(f"[{table}.{field_name}] {reason}")
        self.table: str = table
        self.field_name: str = field_name
        self.reason: str = reason


# ---------------------------------------------------------------------------
# Private parsing helpers
# ---------------------------------------------------------------------------


def _require(table: dict[str, Any], table_name: str, key: str) -> Any:  # noqa: ANN401
    """Return ``table[key]``, raising :class:`MissingFieldError` if absent.

    Args:
        table:      The TOML sub-table dict to look up.
        table_name: Human-readable name used in error messages.
        key:        The key to retrieve.

    Returns
    -------
        The raw value stored at ``table[key]``.

    Raises
    ------
        MissingFieldError: If *key* is not present in *table*.
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

    Args:
        table:      Source dict (one TOML table).
        table_name: Name used in error messages.
        key:        Key to retrieve from *table*.
        default:    Fallback when *key* is absent; if ``None`` the key is
                    treated as required.
        min_val:    Inclusive lower bound; ``None`` means no lower bound.
        max_val:    Inclusive upper bound; ``None`` means no upper bound.

    Returns
    -------
        The validated ``float`` value.

    Raises
    ------
        MissingFieldError: If *key* is absent and *default* is ``None``.
        FieldTypeError:    If the value cannot be converted to ``float``.
        FieldValueError:   If the value falls outside [*min_val*, *max_val*].
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

    Args:
        table:      Source dict.
        table_name: Name used in error messages.
        key:        Key to retrieve.
        default:    Fallback when *key* is absent; ``None`` means required.
        min_val:    Inclusive lower bound; ``None`` means no lower bound.

    Returns
    -------
        The validated ``int`` value.

    Raises
    ------
        MissingFieldError: If *key* is absent and *default* is ``None``.
        FieldTypeError:    If the value cannot be converted to ``int``.
        FieldValueError:   If the value is below *min_val*.
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

    Args:
        table:      Source dict.
        table_name: Name used in error messages.
        key:        Key to retrieve.
        default:    Fallback when *key* is absent; ``None`` means required.
        allowed:    If provided, the value must be a member (case-insensitive
                    comparison is performed and the lower-cased value is
                    returned).
        non_empty:  If ``True``, the empty string is rejected.

    Returns
    -------
        The validated string, lower-cased when *allowed* is set.

    Raises
    ------
        MissingFieldError: If *key* is absent and *default* is ``None``.
        FieldTypeError:    If the stored value is not string-like.
        FieldValueError:   If the value is empty (when *non_empty* is ``True``)
                           or not in *allowed*.
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

    Args:
        table:      Source dict.
        table_name: Name used in error messages.
        key:        Key to retrieve.
        default:    Fallback when *key* is absent.

    Returns
    -------
        The boolean value.

    Raises
    ------
        FieldTypeError: If the stored value is not a Python ``bool``.

    Notes
    -----
    TOML natively distinguishes booleans from strings, so ``"true"``
    (a TOML string) would raise :class:`FieldTypeError` here.  Use proper
    TOML boolean literals (``true`` / ``false``) in spec files.
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

    Args:
        table:      Source dict.
        table_name: Name used in error messages.
        key:        Key to retrieve.
        default:    Fallback when *key* is absent; ``None`` means required.
        non_empty:  If ``True``, the list itself must contain ≥ 1 element.
        allowed:    If provided, every element must be a member (comparison
                    is case-insensitive; lower-cased elements are returned).

    Returns
    -------
        A ``list[str]``, lower-cased when *allowed* is set.

    Raises
    ------
        MissingFieldError: If *key* is absent and *default* is ``None``.
        FieldTypeError:    If the value is not a list, or any item is not a
                           string.
        FieldValueError:   If the list is empty (when *non_empty*) or an
                           element is not in *allowed*.
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


# ---------------------------------------------------------------------------
# Sub-spec dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MetadataSpec:
    """Metadata describing the journal source and specification provenance.

    Attributes
    ----------
    name
        Human-readable journal name.
    publisher
        Publisher or society that owns the journal.
    source_url
        Canonical URL for the author guidelines being modelled.
    last_verified
        ISO 8601 date (``YYYY-MM-DD``) the spec was last checked against
        the live guidelines.
    verified_by
        Name or identifier of the person who performed the last verification
        (may be empty for legacy entries).

    Example::

        MetadataSpec(
            name="Nature",
            publisher="Springer Nature",
            source_url="https://www.nature.com/nature/for-authors/formatting-guide",
            last_verified="2024-05-01",
            verified_by="j.doe",
        )
    """

    name: str
    publisher: str
    source_url: str
    last_verified: str
    verified_by: str


@dataclass(frozen=True, slots=True)
class DimensionSpec:
    """Physical column-width and height constraints for submitted figures.

    All values are in **millimetres**.  Layout code should use these widths
    as the maximum printable extent of a figure; exceeding them typically
    results in automated rejection at submission.

    Attributes
    ----------
    single_column_mm
        Maximum width for a single-column figure (> 0).
    double_column_mm
        Maximum width for a double-column figure
        (must be > *single_column_mm*).
    max_height_mm
        Maximum figure height for any column format (> 0).

    Example::

        DimensionSpec(single_column_mm=89.0, double_column_mm=183.0, max_height_mm=247.0)
    """

    single_column_mm: float
    double_column_mm: float
    max_height_mm: float


@dataclass(frozen=True, slots=True)
class TypographySpec:
    """Typography constraints and preferences for figure text elements.

    Attributes
    ----------
    font_family
        Ordered list of preferred font-family names.  The first available
        font on the target system should be used.
    font_fallback
        Generic fallback family (e.g. ``"sans-serif"``) when none of
        *font_family* is available.
    min_font_pt
        Smallest permissible font size in points (> 0).
    max_font_pt
        Largest permissible font size in points (≥ *min_font_pt*).
    panel_label_pt
        Font size in points for panel labels (A, B, …).  Defaults to
        *min_font_pt* when omitted in TOML.
    panel_label_weight
        CSS-style font weight for panel labels (e.g. ``"bold"``).
    panel_label_case
        Text transformation for panel labels — one of ``"lower"``,
        ``"upper"``, ``"title"``, ``"sentence"``, ``"parens_lower"``,
        ``"parens_upper"``.

    Example::

        TypographySpec(
            font_family=["Helvetica", "Arial"],
            font_fallback="sans-serif",
            min_font_pt=7.0,
            max_font_pt=9.0,
            panel_label_pt=7.0,
            panel_label_weight="bold",
            panel_label_case="lower",
        )
    """

    font_family: list[str]
    font_fallback: str
    min_font_pt: float
    max_font_pt: float
    panel_label_pt: float
    panel_label_weight: str
    panel_label_case: str


@dataclass(frozen=True, slots=True)
class ExportSpec:
    """Export and rendering requirements for figure files.

    Attributes
    ----------
    preferred_formats
        Ordered list of accepted file formats (e.g. ``["pdf", "tiff"]``).
        Formats are stored in lowercase without a leading dot.
    min_dpi
        Minimum resolution in dots per inch for raster output (≥ 72).
    color_space
        Required colour space — one of ``"rgb"``, ``"cmyk"``, or
        ``"grayscale"``.
    font_embedding
        Whether fonts must be embedded in vector outputs.
    editable_text
        Whether text layers must remain editable in vector outputs
        (e.g. for EPS/PDF).

    Example::

        ExportSpec(
            preferred_formats=["pdf", "eps"],
            min_dpi=300,
            color_space="rgb",
            font_embedding=True,
            editable_text=False,
        )
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
    avoid_combinations
        List of colour-pair groups that must not appear together in the
        same figure (e.g. ``[["red", "green"], ["blue", "yellow"]]``).
        Each inner list contains two or more colour identifiers.
    colorblind_required
        ``True`` if the palette must be perceptually distinguishable for
        the most common types of colour-vision deficiency.
    grayscale_required
        ``True`` if the figure must remain interpretable when printed in
        greyscale.

    Example::

        ColorSpec(
            avoid_combinations=[["red", "green"]],
            colorblind_required=True,
            grayscale_required=False,
        )
    """

    avoid_combinations: list[list[str]]
    colorblind_required: bool
    grayscale_required: bool


@dataclass(frozen=True, slots=True)
class LineSpec:
    """Line rendering constraints for figures.

    Attributes
    ----------
    min_weight_pt
        Minimum stroke/line weight in points (> 0).  Lines thinner than
        this threshold may not reproduce reliably in print.

    Example::

        LineSpec(min_weight_pt=0.5)
    """

    min_weight_pt: float


# ---------------------------------------------------------------------------
# Root dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class JournalSpec:
    """Complete, validated journal figure-submission specification.

    :class:`JournalSpec` is the single object a caller works with after
    loading a TOML configuration file.  It composes all domain-specific
    sub-specs into one immutable, hashable value object.

    Attributes
    ----------
    metadata
        Provenance and verification metadata for this spec.
    dimensions
        Physical size constraints for figure files.
    typography
        Font and text-element constraints.
    export
        File-format and rendering requirements.
    color
        Colour usage and accessibility requirements.
    line
        Stroke-weight constraints.
    notes
        Free-form human-readable notes (may be empty).

    Notes
    -----
    All sub-specs and the root :class:`JournalSpec` itself are
    ``frozen=True`` dataclasses, making instances immutable and hashable.
    ``slots=True`` avoids per-instance ``__dict__`` overhead.

    Example::

        import tomllib
        from plotstyle.specs.schema import JournalSpec

        with open("nature.toml", "rb") as fh:
            spec = JournalSpec.from_toml(tomllib.load(fh))

        assert spec.dimensions.single_column_mm == 89.0
        assert "pdf" in spec.export.preferred_formats
    """

    metadata: MetadataSpec
    dimensions: DimensionSpec
    typography: TypographySpec
    export: ExportSpec
    color: ColorSpec
    line: LineSpec
    notes: str = field(default="")

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_toml(cls, data: dict[str, Any]) -> JournalSpec:
        """Construct a validated :class:`JournalSpec` from raw TOML data.

        Each top-level TOML table maps to one sub-spec.  Required fields
        are validated for presence and type; optional fields fall back to
        safe defaults.  All validation errors carry the TOML path of the
        offending field to simplify debugging.

        Args:
            data: Parsed TOML content as returned by ``tomllib.load`` or
                ``tomli.load``.  The expected top-level keys are:
                ``metadata``, ``dimensions``, ``typography``, ``export``,
                and optionally ``color``, ``line``, and ``notes``.

        Returns
        -------
            A fully populated and validated :class:`JournalSpec` instance.

        Raises
        ------
            MissingFieldError: If a required TOML field is absent.
            FieldTypeError:    If a field value cannot be cast to the
                               expected Python type.
            FieldValueError:   If a field value violates a domain constraint
                               (e.g. ``min_dpi < 72`` or an unrecognised
                               ``color_space``).

        Notes
        -----
        * ``[color]`` and ``[line]`` tables are optional; sensible defaults
          are applied when they are absent.
        * ``color_space``, ``preferred_formats``, ``panel_label_weight``,
          and ``panel_label_case`` are normalised to lowercase.
        * Cross-field invariants (e.g. ``max_font_pt ≥ min_font_pt``) are
          checked after individual fields are validated.

        Example::

            import tomllib
            from plotstyle.specs.schema import JournalSpec

            raw = tomllib.loads('''
                [metadata]
                name          = "Nature"
                publisher     = "Springer Nature"
                source_url    = "https://nature.com/guidelines"
                last_verified = "2024-05-01"
                verified_by   = "j.doe"

                [dimensions]
                single_column_mm = 89.0
                double_column_mm = 183.0
                max_height_mm    = 247.0

                [typography]
                font_family   = ["Helvetica", "Arial"]
                font_fallback = "sans-serif"
                min_font_pt   = 7.0
                max_font_pt   = 9.0

                [export]
                preferred_formats = ["pdf", "eps"]
                min_dpi           = 300
                color_space       = "RGB"
            ''')
            spec = JournalSpec.from_toml(raw)
        """
        # Extract raw sub-tables; raise clearly if a required one is absent.
        meta_raw: dict[str, Any] = _require(data, "root", "metadata")
        dims_raw: dict[str, Any] = _require(data, "root", "dimensions")
        typo_raw: dict[str, Any] = _require(data, "root", "typography")
        exp_raw: dict[str, Any] = _require(data, "root", "export")
        # Optional tables default to empty dicts so all .get() calls inside
        # the helpers return their declared defaults without special-casing.
        col_raw: dict[str, Any] = data.get("color", {})
        ln_raw: dict[str, Any] = data.get("line", {})

        # Parse and validate each sub-spec independently.
        metadata = cls._parse_metadata(meta_raw)
        dimensions = cls._parse_dimensions(dims_raw)
        typography = cls._parse_typography(typo_raw)
        export = cls._parse_export(exp_raw)
        color = cls._parse_color(col_raw)
        line = cls._parse_line(ln_raw)

        return cls(
            metadata=metadata,
            dimensions=dimensions,
            typography=typography,
            export=export,
            color=color,
            line=line,
            notes=str(data.get("notes", "")),
        )

    # ------------------------------------------------------------------
    # Private sub-spec parsers — each maps to one TOML table
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_metadata(raw: dict[str, Any]) -> MetadataSpec:
        """Parse and validate the ``[metadata]`` table.

        Args:
            raw: The raw dict for the ``[metadata]`` TOML table.

        Returns
        -------
            A validated :class:`MetadataSpec`.

        Raises
        ------
            MissingFieldError: If a required field is absent.
            FieldTypeError:    If a field value is not a string.
            FieldValueError:   If ``last_verified`` is not ISO 8601.
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
            # ``verified_by`` is optional; legacy specs may omit it.
            verified_by=_cast_str(raw, t, "verified_by", default=""),
        )

    @staticmethod
    def _parse_dimensions(raw: dict[str, Any]) -> DimensionSpec:
        """Parse and validate the ``[dimensions]`` table.

        Args:
            raw: The raw dict for the ``[dimensions]`` TOML table.

        Returns
        -------
            A validated :class:`DimensionSpec`.

        Raises
        ------
            MissingFieldError: If a required field is absent.
            FieldTypeError:    If a field value cannot be cast to float.
            FieldValueError:   If any dimension is ≤ 0, or if
                               ``double_column_mm ≤ single_column_mm``.
        """
        t = "dimensions"
        single = _cast_float(raw, t, "single_column_mm", min_val=0.0)
        if single <= 0:
            raise FieldValueError(t, "single_column_mm", f"must be > 0, got {single}")
        double = _cast_float(raw, t, "double_column_mm", min_val=0.0)
        if double <= 0:
            raise FieldValueError(t, "double_column_mm", f"must be > 0, got {double}")
        height = _cast_float(raw, t, "max_height_mm", min_val=0.0)
        if height <= 0:
            raise FieldValueError(t, "max_height_mm", f"must be > 0, got {height}")

        # Cross-field invariant: double column must be wider than single.
        if double <= single:
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
    def _parse_typography(raw: dict[str, Any]) -> TypographySpec:
        """Parse and validate the ``[typography]`` table.

        Args:
            raw: The raw dict for the ``[typography]`` TOML table.

        Returns
        -------
            A validated :class:`TypographySpec`.

        Raises
        ------
            MissingFieldError: If a required field is absent.
            FieldTypeError:    If a field value has the wrong type.
            FieldValueError:   If ``max_font_pt < min_font_pt``,
                               ``panel_label_weight`` is unrecognised, or
                               ``panel_label_case`` is unrecognised.
        """
        t = "typography"
        min_pt = _cast_float(raw, t, "min_font_pt", min_val=0.0)
        max_pt = _cast_float(raw, t, "max_font_pt", min_val=0.0)

        if max_pt < min_pt:
            raise FieldValueError(
                t,
                "max_font_pt",
                f"must be ≥ min_font_pt ({min_pt}), got {max_pt}",
            )

        # ``panel_label_pt`` defaults to ``min_font_pt`` when omitted so that
        # the smallest body text and panel labels share the same size — a safe
        # default for most journal styles.
        panel_pt = _cast_float(raw, t, "panel_label_pt", default=min_pt, min_val=0.0)

        return TypographySpec(
            font_family=_cast_str_list(raw, t, "font_family", default=[], non_empty=True),
            font_fallback=_cast_str(raw, t, "font_fallback", default="sans-serif"),
            min_font_pt=min_pt,
            max_font_pt=max_pt,
            panel_label_pt=panel_pt,
            panel_label_weight=_cast_str(
                raw,
                t,
                "panel_label_weight",
                default="bold",
                allowed=_KNOWN_FONT_WEIGHTS,
            ),
            panel_label_case=_cast_str(
                raw,
                t,
                "panel_label_case",
                default="lower",
                allowed=_KNOWN_LABEL_CASES,
            ),
        )

    @staticmethod
    def _parse_export(raw: dict[str, Any]) -> ExportSpec:
        """Parse and validate the ``[export]`` table.

        Args:
            raw: The raw dict for the ``[export]`` TOML table.

        Returns
        -------
            A validated :class:`ExportSpec`.

        Raises
        ------
            MissingFieldError: If a required field is absent.
            FieldTypeError:    If a field value has the wrong type.
            FieldValueError:   If ``min_dpi`` is below the physical floor
                               (72 DPI), ``color_space`` is unrecognised,
                               or a format in ``preferred_formats`` is
                               unknown.
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
                raw,
                t,
                "color_space",
                default="rgb",
                allowed=_KNOWN_COLOR_SPACES,
            ),
            font_embedding=_cast_bool(raw, t, "font_embedding", default=True),
            editable_text=_cast_bool(raw, t, "editable_text", default=False),
        )

    @staticmethod
    def _parse_color(raw: dict[str, Any]) -> ColorSpec:
        """Parse and validate the optional ``[color]`` table.

        Args:
            raw: The raw dict for the ``[color]`` TOML table, or ``{}`` if
                 the table was absent.

        Returns
        -------
            A validated :class:`ColorSpec`.

        Raises
        ------
            FieldTypeError:  If ``avoid_combinations`` is not a list of
                             lists, or any element is not a string.
            FieldValueError: If an inner combination list has fewer than
                             two colour entries.
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
            # Enforce that each group contains at least two colours; a
            # single-colour "combination" is meaningless as a contrast rule.
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
    def _parse_line(raw: dict[str, Any]) -> LineSpec:
        """Parse and validate the optional ``[line]`` table.

        Args:
            raw: The raw dict for the ``[line]`` TOML table, or ``{}`` if
                 the table was absent.

        Returns
        -------
            A validated :class:`LineSpec`.

        Raises
        ------
            FieldTypeError:  If ``min_weight_pt`` cannot be cast to float.
            FieldValueError: If ``min_weight_pt`` is ≤ 0.
        """
        return LineSpec(
            min_weight_pt=_cast_float(raw, "line", "min_weight_pt", default=0.5, min_val=0.0),
        )
