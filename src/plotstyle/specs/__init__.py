"""Journal specification registry — lazy-loads and caches TOML specs.

This module provides :class:`SpecRegistry`, a lightweight facade that
discovers ``*.toml`` journal-specification files on disk, deserialises them
into :class:`~plotstyle.specs.schema.JournalSpec` instances on first access,
and caches the result so that subsequent lookups are effectively free.

A module-level :data:`registry` singleton is exposed for convenience and is
the primary entry-point used by the rest of the *plotstyle* library.

Notes
-----
* Spec file names are treated **case-insensitively** — ``"Nature"`` and
  ``"nature"`` both resolve to ``nature.toml``.
* Files whose name starts with an underscore (e.g. ``_base.toml``) are
  considered *private* and excluded from :meth:`SpecRegistry.list_available`.

Example::

    from plotstyle.specs import registry

    spec = registry.get("nature")
    print(spec.metadata.name)  # "Nature"
    print(registry.list_available())  # ['acs', 'ieee', 'nature', 'science']
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from plotstyle._utils.io import load_toml
from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "SpecNotFoundError",
    "SpecRegistry",
    "registry",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default directory that ships the built-in TOML spec files.
_SPECS_DIR: Final[Path] = Path(__file__).parent


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class SpecNotFoundError(KeyError):
    """Raised when a requested journal specification cannot be found.

    Inherits from :class:`KeyError` so that existing ``except KeyError``
    handlers continue to work without modification.

    Attributes
    ----------
    name
        The journal identifier that was requested.
    available
        Journal identifiers that *are* available at the time of the error.

    Example::

        try:
            registry.get("unknown_journal")
        except SpecNotFoundError as exc:
            print(exc.name)  # "unknown_journal"
            print(exc.available)  # ['acs', 'ieee', 'nature', 'science']
    """

    def __init__(self, name: str, available: list[str]) -> None:
        self.name: str = name
        self.available: list[str] = available
        # Build a human-friendly message while remaining a KeyError subclass
        # so that existing ``except KeyError`` handlers still work.
        available_str: str = ", ".join(available) if available else "(none)"
        super().__init__(f"Unknown journal {name!r}. Available journals: {available_str}")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class SpecRegistry:
    """Registry for discovering, loading, and caching journal specifications.

    TOML files are parsed **lazily** on first access via :meth:`get` and
    cached in an internal dictionary so that repeated lookups for the same
    journal incur no I/O or parsing overhead.

    Args:
        specs_dir: Directory that contains the ``*.toml`` spec files.
            When ``None`` (the default), the package's own ``specs/``
            directory is used.

    Notes
    -----
    ``__slots__`` is used to reduce per-instance memory overhead and to
    prevent accidental attribute assignment outside the defined interface.

    Example::

        reg = SpecRegistry()
        reg.list_available()  # ['acs', 'ieee', 'nature', 'science']
        spec = reg.get("nature")
    """

    __slots__ = ("_cache", "_specs_dir")

    def __init__(self, specs_dir: Path | None = None) -> None:
        self._specs_dir: Final[Path] = specs_dir or _SPECS_DIR
        self._cache: dict[str, JournalSpec] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, name: str) -> JournalSpec:
        """Retrieve a journal specification by name.

        The *name* is normalised to lower-case before lookup, so
        ``"Nature"`` and ``"NATURE"`` both resolve to ``nature.toml``.
        Parsed specs are cached after the first access — subsequent calls
        for the same name are free.

        Args:
            name: Journal identifier (e.g. ``"nature"``).

        Returns
        -------
            The fully-parsed :class:`~plotstyle.specs.schema.JournalSpec`
            instance.

        Raises
        ------
            SpecNotFoundError: If no matching TOML file exists in the specs
                directory.
            TypeError: If *name* is not a string.

        Example::

            spec = registry.get("nature")
            print(spec.dimensions.single_column_mm)  # 89.0
        """
        if not isinstance(name, str):
            raise TypeError(f"Journal name must be a string, got {type(name).__name__!r}.")

        key: str = name.lower()

        # Fast path — spec already parsed and cached.
        try:
            return self._cache[key]
        except KeyError:
            pass

        # Slow path — resolve the TOML file, parse, and populate the cache.
        toml_path: Path = self._specs_dir / f"{key}.toml"

        if not toml_path.is_file():
            raise SpecNotFoundError(name, available=self.list_available())

        raw_data: dict[str, object] = load_toml(toml_path)
        spec: JournalSpec = JournalSpec.from_toml(raw_data)

        self._cache[key] = spec
        return spec

    def list_available(self) -> list[str]:
        """List the identifiers of every discoverable journal specification.

        Scans :attr:`_specs_dir` for ``*.toml`` files whose names do **not**
        start with an underscore (private or internal specs are excluded).

        Returns
        -------
            Alphabetically sorted list of spec names (file stems, lower-case).

        Raises
        ------
            FileNotFoundError: If the specs directory is inaccessible.

        Example::

            registry.list_available()
            # ['acs', 'ieee', 'nature', 'science']
        """
        try:
            entries: list[str] = sorted(
                Path(entry.path).stem
                for entry in os.scandir(self._specs_dir)
                if entry.is_file()
                and entry.name.endswith(".toml")
                and not entry.name.startswith("_")
            )
        except OSError as exc:
            raise FileNotFoundError(f"Specs directory is inaccessible: {self._specs_dir}") from exc

        return entries

    def preload(self, names: list[str] | None = None) -> None:
        """Eagerly parse and cache one or more specifications.

        Useful when startup latency matters more than lazy loading — for
        example, in a CLI tool that accesses many specs in a tight loop.

        Args:
            names: Journal identifiers to preload.  When ``None``, **all**
                available specs are loaded.

        Raises
        ------
            SpecNotFoundError: If any requested name does not correspond
                to a TOML file in the specs directory.

        Notes
        -----
        Delegation to :meth:`get` keeps validation and caching logic
        centralised — this method adds no caching logic of its own.
        """
        targets: list[str] = names if names is not None else self.list_available()
        for target in targets:
            # Delegate to get() so validation and caching stay centralised.
            self.get(target)

    def clear_cache(self) -> None:
        """Discard all cached :class:`~plotstyle.specs.schema.JournalSpec` instances.

        Subsequent calls to :meth:`get` will re-read from disk and re-parse.
        Primarily useful during testing or after the specs directory has been
        modified at runtime.
        """
        self._cache.clear()

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __contains__(self, name: str) -> bool:
        """Check whether a journal specification is available.

        Args:
            name: Journal identifier to test.  Case-insensitive.

        Returns
        -------
            ``True`` if a spec with the given name exists in the cache or
            has a corresponding TOML file on disk.

        Example::

            "nature" in registry  # True
            "unknown" in registry  # False
        """
        key: str = name.lower()
        # Check cache first to avoid a filesystem call when already loaded.
        if key in self._cache:
            return True
        return (self._specs_dir / f"{key}.toml").is_file()

    def __len__(self) -> int:
        """Return the total number of discoverable spec files on disk.

        Returns
        -------
            Count of ``*.toml`` files in the specs directory that do not
            start with an underscore.
        """
        return len(self.list_available())

    def __repr__(self) -> str:
        """Return a developer-friendly representation of the registry.

        Returns
        -------
            A string of the form
            ``<SpecRegistry specs_dir='...' cached=N/M>``.
        """
        cached: int = len(self._cache)
        total: int = len(self)
        return f"<{type(self).__name__} specs_dir={str(self._specs_dir)!r} cached={cached}/{total}>"


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Module-level registry singleton used throughout the *plotstyle* library.
#:
#: Import this directly rather than instantiating :class:`SpecRegistry`
#: unless you need a non-default specs directory.
#:
#: Example::
#:
#:     from plotstyle.specs import registry
#:
#:     spec = registry.get("ieee")
registry: Final[SpecRegistry] = SpecRegistry()
