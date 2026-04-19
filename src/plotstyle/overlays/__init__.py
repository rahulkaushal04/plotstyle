"""Style overlay registry — discovers, loads, and caches :class:`.StyleOverlay` instances.

A module-level :data:`overlay_registry` singleton is exposed for convenience and
is the primary entry-point used by :func:`~plotstyle.core.style.use` when
resolving overlay keys.

Notes
-----
* Overlay file names are treated **case-insensitively** — ``"Notebook"`` and
  ``"notebook"`` both resolve to ``notebook.toml``.
* Files whose name starts with an underscore are considered *private* and
  excluded from :meth:`OverlayRegistry.list_available`.

Examples
--------
::

    from plotstyle.overlays import overlay_registry

    overlay = overlay_registry.get("notebook")
    print(overlay.name)  # "Notebook"
    print(overlay.category)  # "context"
    print(overlay_registry.list_available())  # ['grid', 'no-latex', 'notebook']
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from plotstyle._utils.io import load_toml
from plotstyle.overlays.schema import StyleOverlay

__all__: list[str] = [
    "OverlayNotFoundError",
    "OverlayRegistry",
    "overlay_registry",
]

#: Default directory that ships the built-in overlay TOML files.
_OVERLAYS_DIR: Final[Path] = Path(__file__).parent


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class OverlayNotFoundError(ValueError):
    """Raised when a requested style overlay cannot be found.

    Attributes
    ----------
    name
        The overlay identifier that was requested.
    available
        Overlay identifiers that *are* available at the time of the error.
    journals
        Journal identifiers available at the time of the error, or ``None``
        when the error was not raised from a combined journal+overlay lookup.

    Examples
    --------
    ::

        try:
            overlay_registry.get("unknown")
        except OverlayNotFoundError as exc:
            print(exc.name)  # "unknown"
            print(exc.available)  # ['grid', 'no-latex', 'notebook']
    """

    def __init__(
        self,
        name: str,
        available: list[str],
        *,
        journals: list[str] | None = None,
    ) -> None:
        self.name: str = name
        self.available: list[str] = available
        self.journals: list[str] | None = journals
        if journals is not None:
            journals_str = ", ".join(journals) if journals else "(none)"
            available_str = ", ".join(available) if available else "(none)"
            message = (
                f"{name!r} not found in journal specs or overlay registry.\n"
                f"  Journals: {journals_str}\n"
                f"  Overlays: {available_str}"
            )
        else:
            available_str = ", ".join(available) if available else "(none)"
            message = f"Unknown overlay {name!r}. Available overlays: {available_str}"
        super().__init__(message)

    def __str__(self) -> str:
        """Return the plain message."""
        return self.args[0]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class OverlayRegistry:
    """Registry for discovering, loading, and caching style overlays.

    TOML files are parsed **lazily** on first access via :meth:`get` and
    cached so that repeated lookups incur no I/O overhead.

    Parameters
    ----------
    overlays_dir : Path | None
        Directory containing the ``*.toml`` overlay files.  Defaults to
        the package's own ``overlays/`` directory.

    Notes
    -----
    ``__slots__`` is used to reduce per-instance memory overhead and to
    prevent accidental attribute assignment outside the defined interface.
    """

    __slots__ = ("_available_cache", "_cache", "_overlays_dir")

    def __init__(self, overlays_dir: Path | None = None) -> None:
        self._overlays_dir: Final[Path] = overlays_dir or _OVERLAYS_DIR
        self._cache: dict[str, StyleOverlay] = {}
        self._available_cache: list[str] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, name: str) -> StyleOverlay:
        """Retrieve a style overlay by key.

        Parameters
        ----------
        name : str
            Overlay identifier (e.g. ``"notebook"``).  Case-insensitive.

        Returns
        -------
        StyleOverlay

        Raises
        ------
        OverlayNotFoundError
            If no matching TOML file exists.
        TypeError
            If *name* is not a string.
        """
        if not isinstance(name, str):
            raise TypeError(f"Overlay name must be a string, got {type(name).__name__!r}.")

        key = name.lower()

        try:
            return self._cache[key]
        except KeyError:
            pass

        toml_path = self._overlays_dir / f"{key}.toml"

        if not toml_path.is_file():
            raise OverlayNotFoundError(name, available=self.list_available())

        raw_data = load_toml(toml_path)
        overlay = StyleOverlay.from_toml(raw_data, key=key)

        self._cache[key] = overlay
        return overlay

    def list_available(self, category: str | None = None) -> list[str]:
        """List available overlay keys, optionally filtered by category.

        Parameters
        ----------
        category : str | None
            When provided, only overlays whose ``category`` field matches
            this value are returned.

        Returns
        -------
        list[str]
            Alphabetically sorted list of overlay keys.

        Raises
        ------
        FileNotFoundError
            If the overlays directory is inaccessible.
        """
        if self._available_cache is None:
            try:
                self._available_cache = sorted(
                    Path(entry.path).stem
                    for entry in os.scandir(self._overlays_dir)
                    if entry.is_file()
                    and entry.name.endswith(".toml")
                    and not entry.name.startswith("_")
                )
            except OSError as exc:
                raise FileNotFoundError(
                    f"Overlays directory is inaccessible: {self._overlays_dir}"
                ) from exc

        if category is None:
            return list(self._available_cache)

        return [key for key in self._available_cache if self.get(key).category == category]

    def clear_cache(self) -> None:
        """Discard all cached :class:`.StyleOverlay` instances."""
        self._cache.clear()
        self._available_cache = None

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __contains__(self, name: str) -> bool:
        """Check whether an overlay is available (case-insensitive, no I/O if cached)."""
        key = name.lower()
        if key in self._cache:
            return True
        return (self._overlays_dir / f"{key}.toml").is_file()

    def __len__(self) -> int:
        """Return the number of discoverable non-private overlay files on disk."""
        return len(self.list_available())

    def __repr__(self) -> str:
        """Return a developer-friendly representation of the registry."""
        cached = len(self._cache)
        total = len(self)
        return (
            f"<{type(self).__name__} "
            f"overlays_dir={str(self._overlays_dir)!r} "
            f"cached={cached}/{total}>"
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

overlay_registry: Final[OverlayRegistry] = OverlayRegistry()
