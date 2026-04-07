"""Validate all TOML journal specifications against the PlotStyle schema.

Walks every ``*.toml`` file in the specs data directory, performs a two-phase
validation, and reports results to ``stdout``.  Exits with code ``0`` if all
specs are valid, or ``1`` if any errors are found.

Two-phase validation
--------------------
1. **Required-field check** — verifies that a set of mandatory dotted-path
   keys are present in the raw TOML dict before attempting schema parsing.
   This produces a specific, human-readable "Missing fields: …" message
   instead of a cryptic Pydantic / dataclass error when a top-level section
   is absent entirely.

2. **Full schema parse** — calls :meth:`~plotstyle.specs.schema.JournalSpec.from_toml`
   to construct the complete typed object, which validates types, ranges, and
   cross-field constraints defined in the schema.

Usage
-----
Run from the repository root::

    python scripts/validate_all_specs.py

Or with a custom specs directory::

    python scripts/validate_all_specs.py --specs-dir path/to/specs

Exit codes
----------
- ``0`` — every spec file parsed without errors.
- ``1`` — one or more files are missing, invalid, or unparseable; or no spec
  files were found at all.

Notes
-----
- Files whose names begin with ``_`` are intentionally skipped; the convention
  is used for internal template or partial-spec files that are not intended for
  direct use.
- The ``# noqa: E402`` comments on the plotstyle imports are removed: this
  script is run from the repository root with the package on ``sys.path``,
  so no path manipulation is needed and the noqa markers were misleading.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from plotstyle._utils.io import load_toml
from plotstyle.specs.schema import JournalSpec

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default location of spec TOML files, relative to this script's parent.
_DEFAULT_SPECS_DIR: Final[Path] = (
    Path(__file__).resolve().parent.parent / "src" / "plotstyle" / "specs"
)

#: Dotted key paths that must be present in every spec file.
#: Checked against the raw TOML dict before full schema parsing so that
#: absent top-level sections produce a clear "Missing fields" message rather
#: than an opaque schema error.
REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "metadata.name",
    "metadata.source_url",
    "dimensions.single_column_mm",
    "dimensions.double_column_mm",
    "dimensions.max_height_mm",
    "typography.font_family",
    "export.min_dpi",
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class _SpecResult:
    """Outcome of validating a single spec file.

    Attributes
    ----------
        path:    The spec file that was validated.
        passed:  ``True`` if both validation phases succeeded.
        message: Human-readable detail — ``"OK"`` on success, or a
                 description of the first failure encountered.
    """

    path: Path
    passed: bool
    message: str

    def format(self) -> str:
        """Return a single terminal line summarising this result.

        Returns
        -------
            A string of the form ``"✓ nature.toml — OK"`` or
            ``"✗ ieee.toml — Missing fields: export.min_dpi"``.
        """
        icon = "✓" if self.passed else "✗"
        return f"{icon} {self.path.name} — {self.message}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _field_exists(data: dict, dotted_path: str) -> bool:
    """Return ``True`` if *dotted_path* resolves to a value in *data*.

    Traverses nested dicts by splitting *dotted_path* on ``"."``.  Returns
    ``False`` as soon as any intermediate key is absent or the traversal
    reaches a non-dict value before the path is exhausted.

    Args:
        data:        The parsed TOML document (may be arbitrarily nested).
        dotted_path: A dot-separated key path such as ``"metadata.name"``.

    Returns
    -------
        ``True`` if the full path exists and resolves to any value (including
        ``None``, ``0``, or ``""``); ``False`` otherwise.

    Example:
        >>> _field_exists({"a": {"b": 1}}, "a.b")
        True
        >>> _field_exists({"a": {}}, "a.b")
        False
    """
    node: object = data
    for part in dotted_path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def _validate_spec(path: Path) -> _SpecResult:
    """Load and validate a single TOML spec file.

    Performs the two-phase validation described in the module docstring:
    required-field presence check followed by full schema parsing.

    Args:
        path: Filesystem path to the ``.toml`` file.

    Returns
    -------
        A :class:`_SpecResult` indicating whether validation passed and
        providing a human-readable message.  Exceptions are caught and
        converted to failure results so that one bad file does not prevent
        the remaining files from being validated.
    """
    try:
        data = load_toml(path)
    except Exception as exc:
        return _SpecResult(path=path, passed=False, message=f"Failed to load TOML: {exc}")

    # Phase 1 — required field presence.
    missing = [f for f in REQUIRED_FIELDS if not _field_exists(data, f)]
    if missing:
        return _SpecResult(
            path=path,
            passed=False,
            message=f"Missing required fields: {', '.join(missing)}",
        )

    # Phase 2 — full schema parse.
    try:
        JournalSpec.from_toml(data)
    except Exception as exc:
        # Include the exception type in the message so schema errors (e.g.,
        # ValidationError, TypeError) are distinguishable from missing-field
        # errors without requiring the user to re-run with --verbose.
        return _SpecResult(
            path=path,
            passed=False,
            message=f"{type(exc).__name__}: {exc}",
        )

    return _SpecResult(path=path, passed=True, message="OK")


def _discover_specs(specs_dir: Path) -> list[Path]:
    """Return a sorted list of spec TOML files in *specs_dir*.

    Files whose names begin with ``_`` are excluded by convention (they are
    internal templates or partial specs not intended for direct parsing).

    Args:
        specs_dir: Directory to search.

    Returns
    -------
        Sorted list of :class:`~pathlib.Path` objects for matching files.

    Raises
    ------
        SystemExit: Not raised here; the caller is responsible for handling
            an empty list.
    """
    return sorted(p for p in specs_dir.glob("*.toml") if not p.name.startswith("_"))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Return the configured argument parser for this script.

    Returns
    -------
        A fully configured :class:`~argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="validate_all_specs",
        description=(
            "Validate all PlotStyle TOML journal specs against the schema.\n"
            "Exits 0 if all valid, 1 if any errors are found."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--specs-dir",
        type=Path,
        default=_DEFAULT_SPECS_DIR,
        metavar="DIR",
        help=(f"Directory containing spec TOML files (default: {_DEFAULT_SPECS_DIR})."),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print full tracebacks for schema parse failures.",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Validate all specs and report results.

    Args:
        argv: Argument list to parse.  ``None`` defaults to ``sys.argv[1:]``.

    Returns
    -------
        ``0`` if every spec is valid; ``1`` if any spec fails or the specs
        directory contains no eligible files.
    """
    args = _build_parser().parse_args(argv)
    specs_dir: Path = args.specs_dir
    verbose: bool = args.verbose

    if not specs_dir.is_dir():
        print(f"Error: specs directory not found: {specs_dir}", file=sys.stderr)
        return 1

    toml_files = _discover_specs(specs_dir)
    if not toml_files:
        print(f"No spec files found in: {specs_dir}", file=sys.stderr)
        return 1

    print(f"Validating {len(toml_files)} spec(s) in {specs_dir} …\n")

    results: list[_SpecResult] = []
    for path in toml_files:
        result = _validate_spec(path)
        results.append(result)
        print(result.format())

        # On verbose mode, print the full traceback for failures so developers
        # can diagnose schema errors without running the script again manually.
        if verbose and not result.passed:
            try:
                data = load_toml(path)
                JournalSpec.from_toml(data)
            except Exception:
                print()
                traceback.print_exc()
                print()

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    print()
    print(f"Results: {passed}/{total} specs valid", end="")
    if failed:
        failed_names = ", ".join(r.path.name for r in results if not r.passed)
        print(f", {failed} failed ({failed_names})", end="")
    print(".")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
