"""Physical dimension and font-size types with unit conversion.

This module provides strongly-typed, immutable value objects for representing
physical measurements (:class:`Dimension`) and typographic sizes
(:class:`FontSize`).  Both types share a common base (:class:`_Measurement`)
to eliminate duplication while exposing domain-specific convenience methods
on each subclass.

Supported units
---------------
``mm``, ``cm``, ``in``, ``pt``, ``pica``

Public types
------------
:data:`Unit`
    Literal type enumerating every supported unit string.

:class:`Dimension`
    Spatial measurement (widths, heights, margins).

:class:`FontSize`
    Typographic measurement (font sizes).

Exceptions
----------
:class:`DimensionError`
    Base exception; all unit-related errors inherit from this.

:class:`UnsupportedUnitError`
    Raised when an unrecognised unit string is encountered.

:class:`IncompatibleUnitsError`
    Raised when two measurements of different concrete types are combined.

Typical usage
-------------
::

    from plotstyle.specs.units import Dimension, FontSize

    width = Dimension(210, "mm")  # A4 width
    body = FontSize(10, "pt")

    print(width.to_inches())  # 8.267716535433071
    print(body.to_mm())  # 3.527777777777778

Design notes
------------
* All values are stored internally as plain Python ``float`` — no external
  numeric library is required.
* Conversion is performed via a single canonical intermediate unit
  (millimetres) to keep the conversion table O(n) rather than O(n²).
* Both public classes are *frozen* dataclasses, making them hashable and
  safe to use as dictionary keys or in sets.
* ``slots=True`` avoids the per-instance ``__dict__`` overhead, which
  matters when thousands of measurement objects are created at once.
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

# ---------------------------------------------------------------------------
# Public type alias
# ---------------------------------------------------------------------------

#: Literal type enumerating every supported measurement unit.
Unit = Literal["mm", "cm", "in", "pt", "pica"]

# ---------------------------------------------------------------------------
# Conversion table
# ---------------------------------------------------------------------------

# All factors convert *from* the named unit *to* millimetres.
# Using millimetres as the canonical pivot keeps the table compact: adding a
# new unit requires only one new entry rather than N new entries.
_TO_MM: Final[dict[str, float]] = {
    "mm": 1.0,
    "cm": 10.0,
    "in": 25.4,
    "pt": 25.4 / 72.0,  # 1 pt   = 1/72 inch (PostScript point)
    "pica": 25.4 / 72.0 * 12.0,  # 1 pica = 12 pt
}

# Self-type for arithmetic operators defined on the base class.
_T = TypeVar("_T", bound="_Measurement")


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class DimensionError(ValueError):
    """Base exception for errors raised by this module.

    Inherits from :class:`ValueError` so callers that catch the built-in
    exception continue to work without modification.
    """


class UnsupportedUnitError(DimensionError):
    """Raised when an unrecognised or unsupported unit string is encountered.

    Args:
        unit: The offending unit string.

    Attributes
    ----------
    unit
        The unit string that was rejected.

    Example::

        raise UnsupportedUnitError("furlong")
        # UnsupportedUnitError: Unknown unit 'furlong'. Supported units: cm, in, mm, pica, pt
    """

    def __init__(self, unit: str) -> None:
        supported = ", ".join(sorted(_TO_MM))
        super().__init__(f"Unknown unit {unit!r}. Supported units: {supported}")
        self.unit: str = unit


class IncompatibleUnitsError(DimensionError):
    """Raised when two measurements with incompatible types are combined.

    Guards against accidentally adding a :class:`Dimension` to a
    :class:`FontSize` — they are semantically distinct even though both
    store a numeric value and a unit.

    Args:
        left:  The left-hand operand type name.
        right: The right-hand operand type name.

    Attributes
    ----------
    left
        Type name of the left-hand operand.
    right
        Type name of the right-hand operand.

    Example::

        Dimension(10, "mm") + FontSize(5, "pt")
        # IncompatibleUnitsError: Cannot combine 'Dimension' with 'FontSize': …
    """

    def __init__(self, left: str, right: str) -> None:
        super().__init__(
            f"Cannot combine {left!r} with {right!r}: operands must be the same measurement type."
        )
        self.left: str = left
        self.right: str = right


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_unit(unit: str) -> Unit:
    """Return *unit* unchanged if it is supported, otherwise raise.

    Args:
        unit: Arbitrary string to validate against the supported-unit table.

    Returns
    -------
        The same string, narrowed to the :data:`Unit` literal type.

    Raises
    ------
        UnsupportedUnitError: If *unit* is not a key in :data:`_TO_MM`.

    Example::

        >>> _validate_unit("mm")
        'mm'
        >>> _validate_unit("furlong")
        UnsupportedUnitError: Unknown unit 'furlong'. Supported units: …
    """
    if unit not in _TO_MM:
        raise UnsupportedUnitError(unit)
    return unit  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Base class — not part of the public API
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Measurement:
    """Immutable base for physical measurements.

    Stores a (value, unit) pair and provides the unit-conversion engine
    shared by :class:`Dimension` and :class:`FontSize`.  End users should
    not instantiate this class directly.

    Attributes
    ----------
    value
        The numeric magnitude of the measurement.
    unit
        The unit in which *value* is expressed.

    Notes
    -----
    ``slots=True`` is used for memory efficiency: slot-based dataclasses
    avoid the per-instance ``__dict__`` overhead, which is meaningful when
    thousands of measurement objects are created (e.g. in a layout engine).

    The class is ``frozen`` (immutable) so instances are hashable and can
    be used as dictionary keys or cached safely.
    """

    value: float
    unit: Unit

    def __post_init__(self) -> None:
        """Validate *unit* and coerce *value* to ``float`` after construction.

        Raises
        ------
            UnsupportedUnitError: If *unit* is not a recognised unit string.
            TypeError:            If *value* cannot be converted to ``float``.
        """
        # Validate and normalise the unit first so the error is descriptive.
        object.__setattr__(self, "unit", _validate_unit(self.unit))
        # Coerce value to float; this catches non-numeric inputs early.
        object.__setattr__(self, "value", float(self.value))

    # ------------------------------------------------------------------
    # Core conversion
    # ------------------------------------------------------------------

    def _to_mm_raw(self) -> float:
        """Return the measurement's value expressed in millimetres.

        This is the single point where unit→mm conversion happens; all
        other conversion methods delegate here to keep rounding errors
        consistent across the unit system.

        Returns
        -------
            The magnitude in millimetres as a ``float``.
        """
        return self.value * _TO_MM[self.unit]

    def to(self, target_unit: str) -> float:
        """Convert to any supported target unit.

        Args:
            target_unit: Destination unit string (e.g. ``"in"``, ``"pt"``).

        Returns
        -------
            The measurement's magnitude expressed in *target_unit*.

        Raises
        ------
            UnsupportedUnitError: If *target_unit* is not a recognised unit.

        Example::

            >>> Dimension(2.54, "cm").to("in")
            1.0
            >>> Dimension(72, "pt").to("in")
            1.0
        """
        validated: Unit = _validate_unit(target_unit)
        return self._to_mm_raw() / _TO_MM[validated]

    # ------------------------------------------------------------------
    # Arithmetic operators
    # ------------------------------------------------------------------

    def _check_compatible(self, other: object) -> _Measurement:
        """Assert that *other* is the same concrete type as *self*.

        Args:
            other: The right-hand operand to inspect.

        Returns
        -------
            *other* cast to :class:`_Measurement` (for further use).

        Raises
        ------
            IncompatibleUnitsError: If *other* is a different measurement
                subclass (e.g. mixing :class:`Dimension` with
                :class:`FontSize`).
            TypeError: If *other* is not a :class:`_Measurement` subclass
                at all.
        """
        if not isinstance(other, _Measurement):
            return NotImplemented  # type: ignore[return-value]
        if type(self) is not type(other):
            raise IncompatibleUnitsError(type(self).__name__, type(other).__name__)
        return other

    def __add__(self: _T, other: object) -> _T:
        """Return a new measurement equal to ``self + other``.

        The result is expressed in *self*'s unit.

        Args:
            other: A measurement of the same concrete type.

        Returns
        -------
            A new instance of the same type with the summed value, in
            *self*'s unit.

        Raises
        ------
            IncompatibleUnitsError: If *other* is a different measurement type.
            TypeError:              If *other* is not a measurement object.

        Example::

            >>> Dimension(10, "mm") + Dimension(1, "cm")
            Dimension(value=20.0, unit='mm')
        """
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        # Convert rhs to self's unit before adding to preserve self's unit.
        return type(self)(self.value + rhs.to(self.unit), self.unit)  # type: ignore[return-value]

    def __sub__(self: _T, other: object) -> _T:
        """Return a new measurement equal to ``self - other``.

        The result is expressed in *self*'s unit.

        Args:
            other: A measurement of the same concrete type.

        Returns
        -------
            A new instance of the same type with the difference, in
            *self*'s unit.

        Raises
        ------
            IncompatibleUnitsError: If *other* is a different measurement type.
            TypeError:              If *other* is not a measurement object.

        Example::

            >>> Dimension(10, "cm") - Dimension(25, "mm")
            Dimension(value=7.5, unit='cm')
        """
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return type(self)(self.value - rhs.to(self.unit), self.unit)  # type: ignore[return-value]

    def __mul__(self: _T, scalar: float) -> _T:
        """Scale a measurement by a dimensionless scalar.

        Args:
            scalar: A real-valued multiplier.

        Returns
        -------
            A new instance with ``value * scalar``, in the same unit.

        Raises
        ------
            TypeError: If *scalar* is not numeric.

        Example::

            >>> Dimension(5, "cm") * 3
            Dimension(value=15.0, unit='cm')
        """
        if not isinstance(scalar, (int, float)):
            return NotImplemented  # type: ignore[return-value]
        return type(self)(self.value * scalar, self.unit)  # type: ignore[return-value]

    #: Support ``scalar * measurement`` as well as ``measurement * scalar``.
    __rmul__ = __mul__

    def __truediv__(self: _T, scalar: float) -> _T:
        """Divide a measurement by a dimensionless scalar.

        Args:
            scalar: A non-zero real-valued divisor.

        Returns
        -------
            A new instance with ``value / scalar``, in the same unit.

        Raises
        ------
            TypeError:         If *scalar* is not numeric.
            ZeroDivisionError: If *scalar* is zero.

        Example::

            >>> Dimension(30, "mm") / 2
            Dimension(value=15.0, unit='mm')
        """
        if not isinstance(scalar, (int, float)):
            return NotImplemented  # type: ignore[return-value]
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide a measurement by zero.")
        return type(self)(self.value / scalar, self.unit)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def __lt__(self, other: object) -> bool:
        """Return ``True`` if *self* is strictly less than *other*.

        Comparison is performed in the canonical unit (mm) so that
        ``Dimension(1, "in") < Dimension(3, "cm")`` evaluates correctly.

        Args:
            other: A measurement of the same concrete type.

        Raises
        ------
            IncompatibleUnitsError: If *other* is a different measurement type.
        """
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._to_mm_raw() < rhs._to_mm_raw()

    def __le__(self, other: object) -> bool:
        """Return ``True`` if *self* ≤ *other* (cross-unit aware)."""
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
        """Return ``True`` if *self* ≥ *other* (cross-unit aware)."""
        rhs = self._check_compatible(other)
        if rhs is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._to_mm_raw() >= rhs._to_mm_raw()

    # ``__eq__`` and ``__hash__`` are defined explicitly to compare by canonical
    # mm value, keeping equality consistent with the comparison operators above.

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Measurement) or type(self) is not type(other):
            return NotImplemented
        return math.isclose(self._to_mm_raw(), other._to_mm_raw(), rel_tol=1e-9)

    def __hash__(self) -> int:
        return hash(round(self._to_mm_raw(), 6))

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def is_close(self, other: _Measurement, rel_tol: float = 1e-9) -> bool:
        """Return whether two measurements are approximately equal.

        Uses :func:`math.isclose` on the millimetre representations so
        that floating-point rounding differences across unit conversions
        are handled gracefully.

        Args:
            other:   A measurement to compare against *self*.
            rel_tol: Maximum allowed relative difference (default ``1e-9``).

        Returns
        -------
            ``True`` if the two values are within *rel_tol* of each other.

        Raises
        ------
            IncompatibleUnitsError: If *other* is a different measurement
                type.

        Example::

            >>> a = Dimension(1, "in")
            >>> b = Dimension(25.4, "mm")
            >>> a.is_close(b)
            True
        """
        self._check_compatible(other)
        return math.isclose(self._to_mm_raw(), other._to_mm_raw(), rel_tol=rel_tol)

    def as_unit(self: _T, target_unit: str) -> _T:
        """Return a new measurement expressed in *target_unit*.

        Unlike :meth:`to`, which returns a plain ``float``, this method
        returns a fully typed measurement object — useful when normalising
        a collection to a single unit.

        Args:
            target_unit: The unit for the returned object.

        Returns
        -------
            A new instance of the same type with the converted value.

        Raises
        ------
            UnsupportedUnitError: If *target_unit* is unrecognised.

        Example::

            >>> Dimension(2.54, "cm").as_unit("mm")
            Dimension(value=25.4, unit='mm')
        """
        return type(self)(self.to(target_unit), target_unit)  # type: ignore[return-value]

    def __repr__(self) -> str:
        """Return an unambiguous string representation.

        Returns
        -------
            A string of the form ``ClassName(value=…, unit='…')``.
        """
        return f"{type(self).__name__}(value={self.value!r}, unit={self.unit!r})"


# ---------------------------------------------------------------------------
# Public measurement classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True, eq=False)
class Dimension(_Measurement):
    """A physical spatial measurement (width, height, margin, etc.).

    :class:`Dimension` is intended for layout measurements such as page
    widths, margins, and gutter sizes.  It inherits full unit-conversion
    and arithmetic support from :class:`_Measurement`.

    Attributes
    ----------
    value
        Numeric magnitude of the dimension.
    unit
        Unit of measurement: ``"mm"``, ``"cm"``, ``"in"``, ``"pt"``,
        or ``"pica"``.

    Example::

        >>> page_width = Dimension(210, "mm")   # A4 width
        >>> page_width.to_inches()
        8.267716535433071
        >>> page_width.to_pt()
        595.2755905511812

        >>> margin = Dimension(0.5, "in")
        >>> live_width = page_width - margin.as_unit("mm") * 2
        >>> round(live_width.to_inches(), 4)
        7.2677
    """

    # ------------------------------------------------------------------
    # Named convenience converters
    # ------------------------------------------------------------------

    def to_mm(self) -> float:
        """Return the dimension expressed in millimetres.

        Returns
        -------
            Value in millimetres.

        Example::

            >>> Dimension(1, "in").to_mm()
            25.4
        """
        return self._to_mm_raw()

    def to_cm(self) -> float:
        """Return the dimension expressed in centimetres.

        Returns
        -------
            Value in centimetres.

        Example::

            >>> Dimension(100, "mm").to_cm()
            10.0
        """
        return self.to("cm")

    def to_inches(self) -> float:
        """Return the dimension expressed in inches.

        Returns
        -------
            Value in inches.

        Example::

            >>> Dimension(25.4, "mm").to_inches()
            1.0
        """
        return self.to("in")

    def to_pt(self) -> float:
        """Return the dimension expressed in PostScript points (1 pt = 1/72 in).

        Returns
        -------
            Value in points.

        Example::

            >>> Dimension(1, "in").to_pt()
            72.0
        """
        return self.to("pt")

    def to_pica(self) -> float:
        """Return the dimension expressed in picas (1 pica = 12 pt).

        Returns
        -------
            Value in picas.

        Example::

            >>> Dimension(1, "in").to_pica()
            6.0
        """
        return self.to("pica")


@dataclass(frozen=True, slots=True, eq=False)
class FontSize(_Measurement):
    """A typographic font size measurement.

    :class:`FontSize` is semantically distinct from :class:`Dimension`
    even though both wrap a (value, unit) pair.  Keeping them separate
    prevents accidental mixing (e.g. adding a font size to a page margin)
    and allows each type to expose domain-appropriate helper methods.

    Attributes
    ----------
    value
        Numeric magnitude of the font size.
    unit
        Unit of measurement: ``"mm"``, ``"cm"``, ``"in"``, ``"pt"``,
        or ``"pica"``.

    Notes
    -----
    In typography, ``"pt"`` (PostScript point) and ``"pica"`` are by far
    the most common units.  The :meth:`to_pt` and :meth:`to_pica` helpers
    are therefore the primary API surface for this class.

    Example::

        >>> body = FontSize(10, "pt")
        >>> body.to_mm()
        3.527777777777778
        >>> heading = body * 2.4
        >>> round(heading.to_pt(), 1)
        24.0
    """

    # ------------------------------------------------------------------
    # Named convenience converters
    # ------------------------------------------------------------------

    def to_mm(self) -> float:
        """Return the font size expressed in millimetres.

        Returns
        -------
            Value in millimetres.

        Example::

            >>> FontSize(7, "pt").to_mm()
            2.469444444444444
        """
        return self._to_mm_raw()

    def to_pt(self) -> float:
        """Return the font size expressed in PostScript points (1 pt = 1/72 in).

        Returns
        -------
            Value in points.

        Example::

            >>> FontSize(1, "pica").to_pt()
            12.0
        """
        return self.to("pt")

    def to_pica(self) -> float:
        """Return the font size expressed in picas (1 pica = 12 pt).

        Returns
        -------
            Value in picas.

        Example::

            >>> FontSize(24, "pt").to_pica()
            2.0
        """
        return self.to("pica")

    def to_inches(self) -> float:
        """Return the font size expressed in inches.

        Returns
        -------
            Value in inches.

        Example::

            >>> FontSize(72, "pt").to_inches()
            1.0
        """
        return self.to("in")

    def to_cm(self) -> float:
        """Return the font size expressed in centimetres.

        Returns
        -------
            Value in centimetres.

        Example::

            >>> FontSize(10, "mm").to_cm()
            1.0
        """
        return self.to("cm")
