"""Physical dimension and font-size types with unit conversion.

Provides immutable value objects for physical measurements (`Dimension`)
and typographic sizes (`FontSize`). Both share a common base (`_Measurement`)
that implements conversion, arithmetic, and comparison.

Supported units: ``mm``, ``cm``, ``in``, ``pt``, ``pica``.

Classes
-------
Dimension
    Spatial measurement (widths, heights, margins).
FontSize
    Typographic measurement (font sizes).

Exceptions
----------
DimensionError
    Base exception; all unit-related errors inherit from this.
UnsupportedUnitError
    Raised when an unrecognised unit string is encountered.
IncompatibleUnitsError
    Raised when two measurements of different concrete types are combined.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Literal, TypeVar

__all__: list[str] = [
    "Dimension",
    "DimensionError",
    "FontSize",
    "IncompatibleUnitsError",
    "Unit",
    "UnsupportedUnitError",
]

#: Literal type enumerating every supported measurement unit.
Unit = Literal["mm", "cm", "in", "pt", "pica"]

# Conversion factors: from the named unit to millimetres.
# Using mm as the canonical pivot keeps the table O(n); adding a new unit
# requires only one entry instead of N.
_TO_MM: Final[dict[str, float]] = {
    "mm": 1.0,
    "cm": 10.0,
    "in": 25.4,
    "pt": 25.4 / 72.0,  # 1 pt   = 1/72 inch (PostScript point)
    "pica": 25.4 / 72.0 * 12.0,  # 1 pica = 12 pt
}

# Self-type for arithmetic/conversion methods defined on the base class.
_T = TypeVar("_T", bound="_Measurement")


class DimensionError(ValueError):
    """Base exception for errors raised by this module."""


class UnsupportedUnitError(DimensionError):
    """Raised when an unrecognised or unsupported unit string is encountered.

    Parameters
    ----------
    unit : str
        The offending unit string.

    Attributes
    ----------
    unit : str
        The unit string that was rejected.
    """

    def __init__(self, unit: str) -> None:
        supported = ", ".join(sorted(_TO_MM))
        super().__init__(f"Unknown unit {unit!r}. Supported units: {supported}")
        self.unit: str = unit


class IncompatibleUnitsError(DimensionError):
    """Raised when two measurements with incompatible types are combined.

    Guards against accidentally adding a `Dimension` to a `FontSize` —
    they are semantically distinct even though both store a (value, unit) pair.

    Parameters
    ----------
    left : str
        The left-hand operand type name.
    right : str
        The right-hand operand type name.

    Attributes
    ----------
    left : str
        Type name of the left-hand operand.
    right : str
        Type name of the right-hand operand.
    """

    def __init__(self, left: str, right: str) -> None:
        super().__init__(
            f"Cannot combine {left!r} with {right!r}: operands must be the same measurement type."
        )
        self.left: str = left
        self.right: str = right


def _validate_unit(unit: str) -> Unit:
    """Return *unit* unchanged if supported, otherwise raise.

    Parameters
    ----------
    unit : str
        Arbitrary string to validate.

    Returns
    -------
    Unit
        The same string, narrowed to the `Unit` literal type.

    Raises
    ------
    UnsupportedUnitError
        If *unit* is not a key in ``_TO_MM``.
    """
    if unit not in _TO_MM:
        raise UnsupportedUnitError(unit)
    return unit  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class _Measurement:
    """Immutable base for physical measurements.

    Stores a (value, unit) pair and provides the conversion engine shared
    by `Dimension` and `FontSize`. Not intended for direct instantiation.

    Attributes
    ----------
    value : float
        Numeric magnitude of the measurement.
    unit : Unit
        Unit in which *value* is expressed.
    """

    value: float
    unit: Unit

    def __post_init__(self) -> None:
        """Validate *unit* and coerce *value* to ``float``.

        Raises
        ------
        UnsupportedUnitError
            If *unit* is not a recognised unit string.
        TypeError
            If *value* cannot be converted to ``float``.
        """
        object.__setattr__(self, "unit", _validate_unit(self.unit))
        object.__setattr__(self, "value", float(self.value))

    def _to_mm_raw(self) -> float:
        """Return the value converted to millimetres.

        Single conversion point; all other methods delegate here to keep
        rounding consistent across the unit system.

        Returns
        -------
        float
            Magnitude in millimetres.
        """
        return self.value * _TO_MM[self.unit]

    def to(self, target_unit: str) -> float:
        """Convert to any supported unit.

        Parameters
        ----------
        target_unit : str
            Destination unit (e.g. ``"in"``, ``"pt"``).

        Returns
        -------
        float
            Magnitude expressed in *target_unit*.

        Raises
        ------
        UnsupportedUnitError
            If *target_unit* is not recognised.
        """
        validated: Unit = _validate_unit(target_unit)
        return self._to_mm_raw() / _TO_MM[validated]

    def _check_compatible(self, other: object) -> _Measurement:
        """Assert *other* is the same concrete type as *self*.

        Parameters
        ----------
        other : object
            The right-hand operand to inspect.

        Returns
        -------
        _Measurement
            *other* cast to ``_Measurement``.

        Raises
        ------
        IncompatibleUnitsError
            If *other* is a different ``_Measurement`` subclass.
        TypeError
            If *other* is not a ``_Measurement`` instance at all.
        """
        if not isinstance(other, _Measurement):
            return NotImplemented  # type: ignore[return-value]
        if type(self) is not type(other):
            raise IncompatibleUnitsError(type(self).__name__, type(other).__name__)
        return other

    def __add__(self: _T, other: object) -> _T:
        """Return ``self + other`` as a new measurement in *self*'s unit.

        Raises
        ------
        IncompatibleUnitsError
            If *other* is a different measurement type.
        """
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return type(self)(self.value + rhs.to(self.unit), self.unit)  # type: ignore[return-value]

    def __sub__(self: _T, other: object) -> _T:
        """Return ``self - other`` as a new measurement in *self*'s unit.

        Raises
        ------
        IncompatibleUnitsError
            If *other* is a different measurement type.
        """
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return type(self)(self.value - rhs.to(self.unit), self.unit)  # type: ignore[return-value]

    def __mul__(self: _T, scalar: float) -> _T:
        """Scale the measurement by a dimensionless scalar."""
        if not isinstance(scalar, (int, float)):
            return NotImplemented  # type: ignore[return-value]
        return type(self)(self.value * scalar, self.unit)  # type: ignore[return-value]

    __rmul__ = __mul__

    def __truediv__(self: _T, scalar: float) -> _T:
        """Divide the measurement by a dimensionless scalar.

        Raises
        ------
        ZeroDivisionError
            If *scalar* is zero.
        """
        if not isinstance(scalar, (int, float)):
            return NotImplemented  # type: ignore[return-value]
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide a measurement by zero.")
        return type(self)(self.value / scalar, self.unit)  # type: ignore[return-value]

    def __lt__(self, other: object) -> bool:
        """Return ``True`` if *self* < *other* (cross-unit aware)."""
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._to_mm_raw() < rhs._to_mm_raw()

    def __le__(self, other: object) -> bool:
        """Return ``True`` if *self* <= *other* (cross-unit aware)."""
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._to_mm_raw() <= rhs._to_mm_raw()

    def __gt__(self, other: object) -> bool:
        """Return ``True`` if *self* > *other* (cross-unit aware)."""
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._to_mm_raw() > rhs._to_mm_raw()

    def __ge__(self, other: object) -> bool:
        """Return ``True`` if *self* >= *other* (cross-unit aware)."""
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._to_mm_raw() >= rhs._to_mm_raw()

    def __eq__(self, other: object) -> bool:
        """Return ``True`` if *self* == *other* (cross-unit, float-tolerant)."""
        if not isinstance(other, _Measurement) or type(self) is not type(other):
            return NotImplemented
        return math.isclose(self._to_mm_raw(), other._to_mm_raw(), rel_tol=1e-9)

    def __hash__(self) -> int:
        """Return a hash consistent with cross-unit equality."""
        return hash(round(self._to_mm_raw(), 6))

    def is_close(self, other: _Measurement, rel_tol: float = 1e-9) -> bool:
        """Return whether two measurements are approximately equal.

        Compares millimetre representations via `math.isclose` to handle
        floating-point rounding differences across unit conversions.

        Parameters
        ----------
        other : _Measurement
            Measurement to compare against *self*.
        rel_tol : float, optional
            Maximum allowed relative difference (default ``1e-9``).

        Returns
        -------
        bool
            ``True`` if the two values are within *rel_tol* of each other.

        Raises
        ------
        TypeError
            If *other* is not a ``_Measurement`` instance.
        IncompatibleUnitsError
            If *other* is a different measurement type.
        """
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            raise TypeError(
                f"is_close() requires a {type(self).__name__!r}, got {type(other).__name__!r}."
            )
        return math.isclose(self._to_mm_raw(), rhs._to_mm_raw(), rel_tol=rel_tol)

    def as_unit(self: _T, target_unit: str) -> _T:
        """Return a new measurement expressed in *target_unit*.

        Unlike `to`, which returns a plain ``float``, this returns a typed
        measurement object — useful for normalising a collection to one unit.

        Parameters
        ----------
        target_unit : str
            The unit for the returned object.

        Returns
        -------
        _T
            A new instance of the same type with the converted value.

        Raises
        ------
        UnsupportedUnitError
            If *target_unit* is unrecognised.
        """
        return type(self)(self.to(target_unit), target_unit)  # type: ignore[return-value]

    def __repr__(self) -> str:
        """Return an unambiguous string representation.

        Returns
        -------
        str
            A string of the form ``ClassName(value=…, unit='…')``.
        """
        return f"{type(self).__name__}(value={self.value!r}, unit={self.unit!r})"


@dataclass(frozen=True, slots=True, eq=False)
class Dimension(_Measurement):
    """A physical spatial measurement (width, height, margin, etc.).

    Intended for layout measurements such as page widths, margins, and
    gutter sizes. Inherits full unit-conversion and arithmetic support
    from `_Measurement`.

    Attributes
    ----------
    value : float
        Numeric magnitude of the dimension.
    unit : Unit
        Unit of measurement: ``"mm"``, ``"cm"``, ``"in"``, ``"pt"``,
        or ``"pica"``.
    """

    def to_mm(self) -> float:
        """Return the value in millimetres."""
        return self._to_mm_raw()

    def to_cm(self) -> float:
        """Return the value in centimetres."""
        return self.to("cm")

    def to_inches(self) -> float:
        """Return the value in inches."""
        return self.to("in")

    def to_pt(self) -> float:
        """Return the value in PostScript points (1 pt = 1/72 in)."""
        return self.to("pt")

    def to_pica(self) -> float:
        """Return the value in picas (1 pica = 12 pt)."""
        return self.to("pica")


@dataclass(frozen=True, slots=True, eq=False)
class FontSize(_Measurement):
    """A typographic font-size measurement.

    Semantically distinct from `Dimension` to prevent accidental mixing
    (e.g. adding a font size to a page margin). ``"pt"`` and ``"pica"``
    are the most common units for this class.

    Attributes
    ----------
    value : float
        Numeric magnitude of the font size.
    unit : Unit
        Unit of measurement: ``"mm"``, ``"cm"``, ``"in"``, ``"pt"``,
        or ``"pica"``.
    """

    def to_mm(self) -> float:
        """Return the value in millimetres."""
        return self._to_mm_raw()

    def to_pt(self) -> float:
        """Return the value in PostScript points (1 pt = 1/72 in)."""
        return self.to("pt")

    def to_pica(self) -> float:
        """Return the value in picas (1 pica = 12 pt)."""
        return self.to("pica")

    def to_inches(self) -> float:
        """Return the value in inches."""
        return self.to("in")

    def to_cm(self) -> float:
        """Return the value in centimetres."""
        return self.to("cm")
