"""File I/O helpers for PlotStyle.

Uses :mod:`tomllib` (stdlib, Python ≥ 3.11) or the :mod:`tomli` backport
on older Python versions.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


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


def load_toml(path: Path) -> dict[str, Any]:
    """Load and parse a TOML file.

    Parameters
    ----------
    path : Path
        Path to the ``.toml`` file.

    Returns
    -------
    dict[str, Any]
        Parsed TOML contents.

    Raises
    ------
    OSError
        If the file cannot be opened or read.
    tomllib.TOMLDecodeError
        If the file content is not valid TOML.
    """
    with path.open("rb") as fh:
        return tomllib.load(fh)
