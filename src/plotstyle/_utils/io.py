"""File I/O helpers for PlotStyle.

This module provides thin wrappers around common file operations used
throughout PlotStyle:

- **TOML loading** — :func:`load_toml` reads journal specification and
  configuration files.  On Python 3.11+ the standard library
  :mod:`tomllib` module is used; on older Python versions the third-party
  :mod:`tomli` back-port is required.

Python version handling
-----------------------
TOML support was added to the Python standard library in 3.11 (PEP 680).
For Python 3.10 and earlier, PlotStyle requires the ``tomli`` package, which
is API-compatible with ``tomllib`` and is a zero-dependency pure-Python
library.  The import shim at module level ensures the rest of the codebase
imports only from this module, insulating it from the stdlib/backport split.

Example
-------
    >>> from pathlib import Path
    >>> from plotstyle._utils.io import load_toml
    >>> config = load_toml(Path("pyproject.toml"))
    >>> config["project"]["name"]
    'plotstyle'
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# TOML back-compat shim
# ---------------------------------------------------------------------------

# tomllib became part of the standard library in Python 3.11 (PEP 680).
# For earlier versions we fall back to the 'tomli' third-party package, which
# is API-identical and is a declared dependency of PlotStyle for Python < 3.11.
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "PlotStyle requires the 'tomli' package on Python < 3.11. "
            "Install it with:  pip install tomli"
        ) from exc


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def load_toml(path: Path) -> dict[str, Any]:
    """Load and parse a TOML file into a Python dictionary.

    Opens *path* in binary mode (as required by both :mod:`tomllib` and
    :mod:`tomli`) and returns the fully parsed document.  All standard TOML
    types are mapped to their Python equivalents: strings, integers, floats,
    booleans, datetimes, arrays, and inline tables.

    Args:
        path: Filesystem path to the ``.toml`` file.  Must be an existing,
            readable regular file.  :class:`~pathlib.Path` is the canonical
            type, but any object implementing the :meth:`open` protocol with
            binary-read support is accepted.

    Returns
    -------
        A :class:`dict` containing the top-level keys and values parsed from
        the TOML document.  Nested tables become nested dicts; TOML arrays
        become Python lists.

    Raises
    ------
        FileNotFoundError: If *path* does not exist on the filesystem.
        IsADirectoryError: If *path* points to a directory rather than a file.
        PermissionError: If the process does not have read permission for
            *path*.
        OSError: For other low-level I/O failures (e.g., broken filesystem,
            NFS timeout).
        tomllib.TOMLDecodeError: If the file content is not valid TOML.  The
            exception message includes the line and column of the syntax error.

    Example:
        >>> from pathlib import Path
        >>> from plotstyle._utils.io import load_toml
        >>> data = load_toml(Path("journals/nature.toml"))
        >>> data["journal"]["name"]
        'Nature'

    Notes
    -----
        - Both :mod:`tomllib` (stdlib, Python ≥ 3.11) and :mod:`tomli`
          (backport, Python < 3.11) require the file to be opened in *binary*
          mode (``"rb"``).  This module handles that detail internally so
          callers can treat :func:`load_toml` as a plain text-file loader.
        - No caching is performed; each call re-reads the file from disk.
          For files that are loaded repeatedly (e.g., palette data), callers
          should cache the result at the call site.
        - The function does not validate the contents of the parsed dictionary
          beyond what the TOML spec requires.  Schema validation is the
          responsibility of the caller.
    """
    with path.open("rb") as fh:
        return tomllib.load(fh)
