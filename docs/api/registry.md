# Registry — `plotstyle.specs`

Lazy-loading journal specification registry.

## `SpecRegistry`

```{eval-rst}
.. autoclass:: plotstyle.specs.SpecRegistry
   :members:
```

## `SpecNotFoundError`

```{eval-rst}
.. autoclass:: plotstyle.specs.SpecNotFoundError
   :members:
```

## `registry`

```{eval-rst}
.. autodata:: plotstyle.specs.registry
```

## `JournalSpec`

```{eval-rst}
.. autoclass:: plotstyle.specs.schema.JournalSpec
   :members:
```

## Sub-spec classes

```{eval-rst}
.. autoclass:: plotstyle.specs.schema.MetadataSpec
   :members:

.. autoclass:: plotstyle.specs.schema.DimensionSpec
   :members:

.. autoclass:: plotstyle.specs.schema.TypographySpec
   :members:

.. autoclass:: plotstyle.specs.schema.ExportSpec
   :members:

.. autoclass:: plotstyle.specs.schema.ColorSpec
   :members:

.. autoclass:: plotstyle.specs.schema.LineSpec
   :members:
```

## Usage

### List available journals

```python
from plotstyle.specs import registry

registry.list_available()
# ['acs', 'cell', 'elsevier', 'ieee', 'nature', 'plos', 'prl', 'science', 'springer', 'wiley']
```

### Get a spec

```python
spec = registry.get("nature")
print(spec.metadata.name)           # "Nature"
print(spec.dimensions.single_column_mm)  # 89.0
print(spec.typography.font_family)  # ["Helvetica", "Arial"]
print(spec.export.min_dpi)          # 300
```

### Handle missing specs

```python
from plotstyle.specs import SpecNotFoundError

try:
    registry.get("unknown_journal")
except SpecNotFoundError as exc:
    print(exc.name)       # "unknown_journal"
    print(exc.available)  # ['acs', 'ieee', 'nature', ...]
```

## Notes

- Journal names are case-insensitive: `"Nature"` and `"nature"` both work.
- TOML files starting with `_` (e.g. `_templates.toml`) are private and
  excluded from `list_available()`.
- Parsed specs are cached after first access; subsequent lookups incur no I/O.
