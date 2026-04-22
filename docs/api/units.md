# Units — `plotstyle.specs.units`

Type-safe physical measurements with automatic unit conversion.

## `Dimension`

```{eval-rst}
.. autoclass:: plotstyle.specs.units.Dimension
   :members:
   :special-members: __add__, __sub__, __mul__, __truediv__
```

## `FontSize`

```{eval-rst}
.. autoclass:: plotstyle.specs.units.FontSize
   :members:
   :special-members: __add__, __sub__, __mul__, __truediv__
```

## `Unit`

```{eval-rst}
.. autodata:: plotstyle.specs.units.Unit
```

Supported unit strings: `"mm"`, `"cm"`, `"in"`, `"pt"`, `"pica"`.

## Exceptions

```{eval-rst}
.. autoexception:: plotstyle.specs.units.DimensionError

.. autoexception:: plotstyle.specs.units.UnsupportedUnitError

.. autoexception:: plotstyle.specs.units.IncompatibleUnitsError
```

## Usage

### Create and convert measurements

```python
from plotstyle.specs.units import Dimension, FontSize

# Create a dimension in millimetres and convert
width = Dimension(89.0, "mm")
print(width.to_inches())  # 3.503937...
print(width.to_cm())      # 8.9
print(width.to_pt())      # 252.28...

# Create a font size in points and convert
font = FontSize(7.0, "pt")
print(font.to_mm())    # 2.469...
print(font.to_pica())  # 0.583...
```

### Arithmetic

Measurements of the same type support addition, subtraction, multiplication
by a scalar, and division by a scalar. Results are returned in the left
operand's unit:

```python
from plotstyle.specs.units import Dimension

a = Dimension(89.0, "mm")
b = Dimension(1.0, "in")

total = a + b       # Dimension(value=114.4, unit='mm')
half = a / 2        # Dimension(value=44.5, unit='mm')
doubled = a * 2     # Dimension(value=178.0, unit='mm')
diff = a - b        # Dimension(value=63.6, unit='mm')
```

### Cross-unit comparison

Comparisons work across units — values are converted automatically:

```python
from plotstyle.specs.units import Dimension

a = Dimension(25.4, "mm")
b = Dimension(1.0, "in")

print(a == b)   # True  (25.4 mm == 1 inch)
print(a < b)    # False
```

For floating-point-tolerant equality, use `is_close()`:

```python
a.is_close(b)  # True
```

### Convert to a new measurement object

`as_unit()` returns a new measurement in the target unit (unlike `to()`,
which returns a plain float):

```python
width = Dimension(89.0, "mm")
width_in = width.as_unit("in")   # Dimension(value=3.5039..., unit='in')
```

### Type safety

`Dimension` and `FontSize` cannot be mixed in arithmetic, preventing
accidental errors:

```python
from plotstyle.specs.units import Dimension, FontSize

width = Dimension(89.0, "mm")
font = FontSize(7.0, "pt")

# width + font  → raises IncompatibleUnitsError
```

### Working with journal specs

Journal specs expose raw float values, but you can wrap them in `Dimension`
or `FontSize` for unit-safe manipulation:

```python
from plotstyle.specs import registry
from plotstyle.specs.units import Dimension, FontSize

spec = registry.get("nature")

width = Dimension(spec.dimensions.single_column_mm, "mm")
print(f"Nature single-column: {width.to_inches():.2f} in")

min_font = FontSize(spec.typography.min_font_pt, "pt")
print(f"Nature min font: {min_font.to_mm():.2f} mm")
```

## Notes

- All measurements are immutable (frozen dataclasses).
- Arithmetic always returns a new object; the originals are never modified.
- `UnsupportedUnitError` is raised when an unrecognised unit string is used.
- `IncompatibleUnitsError` is raised when adding or subtracting measurements
  of different types (e.g. `Dimension + FontSize`).
