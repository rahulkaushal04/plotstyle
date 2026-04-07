"""PlotStyle CLI — journal-compliant Matplotlib figure toolkit.

Entry point for the ``plotstyle`` console command, installed via the
``[project.scripts]`` table in ``pyproject.toml``:

    plotstyle = "plotstyle.cli.main:main"

The CLI provides quick access to the most common PlotStyle workflows without
requiring a Python session:

    $ plotstyle list
    $ plotstyle info nature
    $ plotstyle diff nature ieee
    $ plotstyle fonts --journal science
    $ plotstyle validate figure1.pdf --journal nature
    $ plotstyle export figure1.png --journal ieee --formats pdf,eps

Design decisions
----------------
- **Stdlib only** — :mod:`argparse` is the sole CLI dependency so that the
  command is available in minimal environments where optional dependencies
  (e.g., Rich, Click) may not be installed.
- **Lazy imports inside command handlers** — PlotStyle sub-packages import
  Matplotlib and other heavy dependencies.  Deferring those imports to the
  individual ``_cmd_*`` functions means that ``plotstyle --help`` and
  ``plotstyle list`` start instantly without loading the full package graph.
- **Integer exit codes** — every handler returns ``0`` on success and ``1``
  on error, matching the POSIX convention expected by shell scripts and CI
  pipelines.  :func:`main` re-raises nothing; all user-visible errors are
  caught and printed to ``stderr``.
- **Separation of concerns** — the ``_cmd_*`` functions contain only
  display logic; all domain logic lives in the PlotStyle library.

Adding a new sub-command
------------------------
1. Implement a ``_cmd_<name>`` function with the signature
   ``(...) -> int`` that returns ``0`` on success or ``1`` on error.
2. Add a ``subparsers.add_parser(...)`` block in :func:`_build_parser`.
3. Add a dispatch branch in the ``try`` block inside :func:`main`.
"""

from __future__ import annotations

import argparse
import sys
from typing import Final

from plotstyle.specs import SpecNotFoundError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maps panel_label_case spec values to a human-readable example string shown
# in ``plotstyle info``.  Defined at module level so it is constructed once.
_PANEL_LABEL_EXAMPLES: Final[dict[str, str]] = {
    "lower": "a, b, c",
    "upper": "A, B, C",
    "parens_lower": "(a), (b), (c)",
    "parens_upper": "(A), (B), (C)",
}

# Width of the journal-name column in ``plotstyle list`` output.
_LIST_NAME_WIDTH: int = 15

# Separator line used in ``plotstyle info`` output.
_INFO_SEPARATOR: str = "──────────────────────────"


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_list() -> int:
    """List all journal presets available in the spec registry.

    Prints one line per journal in the format::

        nature          Springer Nature
        ieee            IEEE

    Returns
    -------
        ``0`` always (listing cannot fail if the registry loads).
    """
    from plotstyle.specs import registry

    for name in sorted(registry.list_available()):
        spec = registry.get(name)
        print(f"  {name:<{_LIST_NAME_WIDTH}} {spec.metadata.publisher}")

    return 0


def _cmd_info(journal: str) -> int:
    """Print a detailed human-readable summary of a journal specification.

    Covers dimensions (mm and inches), typography, export requirements, and
    accessibility constraints.

    Args:
        journal: Case-insensitive journal identifier (e.g., ``"nature"``).

    Returns
    -------
        ``0`` on success.

    Raises
    ------
        KeyError: Propagated to :func:`main` if *journal* is not registered.
    """
    from plotstyle.specs import registry
    from plotstyle.specs.units import Dimension

    spec = registry.get(journal)
    dim = spec.dimensions
    typo = spec.typography
    exp = spec.export
    col = spec.color
    meta = spec.metadata

    # Convert column widths from mm to inches for readability in mixed-unit labs.
    single_in: float = Dimension(dim.single_column_mm, "mm").to_inches()
    double_in: float = Dimension(dim.double_column_mm, "mm").to_inches()

    fonts: str = ", ".join(typo.font_family)
    formats: str = ", ".join(exp.preferred_formats)

    # Resolve the panel label example; fall back to the raw case string if
    # the value is not one of the four canonical variants.
    label_example: str = _PANEL_LABEL_EXAMPLES.get(typo.panel_label_case, typo.panel_label_case)

    avoid: str = ", ".join("-".join(pair) for pair in col.avoid_combinations) or "none"

    print(f"Journal: {meta.name}")
    print(f"Publisher: {meta.publisher}")
    print(f"Source: {meta.source_url}")
    print(f"Last Verified: {meta.last_verified}")
    print(_INFO_SEPARATOR)
    print("Dimensions:")
    print(f"  Single column: {dim.single_column_mm}mm ({single_in:.2f}in)")
    print(f"  Double column: {dim.double_column_mm}mm ({double_in:.2f}in)")
    print(f"  Max height:    {dim.max_height_mm}mm")
    print("Typography:")
    print(f"  Font:          {fonts} (fallback: {typo.font_fallback})")
    print(f"  Size range:    {typo.min_font_pt}-{typo.max_font_pt}pt")
    print(
        f"  Panel labels:  {typo.panel_label_pt}pt "
        f"{typo.panel_label_weight} {typo.panel_label_case} "
        f"({label_example})"
    )
    print("Export:")
    print(f"  Formats:  {formats}")
    print(f"  Min DPI:  {exp.min_dpi}")
    print(f"  Color:    {exp.color_space}")
    print("Accessibility:")
    print(f"  Colorblind safe: {'Required' if col.colorblind_required else 'Not required'}")
    print(f"  Grayscale safe:  {'Required' if col.grayscale_required else 'Not required'}")
    print(f"  Avoid:           {avoid}")

    return 0


def _cmd_diff(journal_a: str, journal_b: str) -> int:
    """Print a structured comparison of two journal specifications.

    Args:
        journal_a: Identifier of the first journal.
        journal_b: Identifier of the second journal.

    Returns
    -------
        ``0`` on success.

    Raises
    ------
        KeyError: Propagated to :func:`main` if either journal is not
            registered.

    Example:
        $ plotstyle diff nature ieee
    """
    from plotstyle.core.migrate import diff

    # ``diff`` returns a SpecDiff whose __str__ renders the comparison table.
    print(diff(journal_a, journal_b))
    return 0


def _cmd_fonts(journal: str) -> int:
    """Check which of a journal's required fonts are available on this system.

    Reports the best available font and whether it is an exact match or an
    acceptable substitute.

    Args:
        journal: Case-insensitive journal identifier.

    Returns
    -------
        ``0`` on success.

    Raises
    ------
        KeyError: Propagated to :func:`main` if *journal* is not registered.

    Example:
        $ plotstyle fonts --journal nature
    """
    from plotstyle.engine.fonts import detect_available, select_best
    from plotstyle.specs import registry

    spec = registry.get(journal)
    available = detect_available(spec.typography.font_family)
    best, is_exact = select_best(spec)

    print(f"Font check for: {spec.metadata.name}")
    print(f"Required:        {', '.join(spec.typography.font_family)}")
    print(f"Available:       {', '.join(available) if available else 'none'}")
    print(f"Selected:        {best}")
    print(f"Exact match:     {'Yes' if is_exact else 'No (using acceptable substitute)'}")

    return 0


def _cmd_validate(file: str, journal: str) -> int:
    """Validate a saved figure file against a journal's publication spec.

    CLI validation is intentionally limited to checks that can be performed
    on a saved file (e.g., PDF font embedding).  Full validation — which
    inspects live Matplotlib artists — requires a Python session.

    Args:
        file: Path to the saved figure file (PDF, PNG, SVG, …).
        journal: Case-insensitive journal identifier.

    Returns
    -------
        ``0`` on success; ``1`` if the file is not found.

    Raises
    ------
        KeyError: Propagated to :func:`main` if *journal* is not registered.

    Example:
        $ plotstyle validate figure1.pdf --journal nature
    """
    from pathlib import Path

    from plotstyle.engine.fonts import verify_embedded
    from plotstyle.specs import registry

    path = Path(file)
    if not path.exists():
        # Use stderr so the error is visible even when stdout is redirected.
        print(f"Error: file not found: {file}", file=sys.stderr)
        return 1

    spec = registry.get(journal)
    print(f"Validation against: {spec.metadata.name}")
    print()

    if path.suffix.lower() == ".pdf":
        hits = verify_embedded(path)
        type3_found = any(h.get("type") == "Type3" for h in hits)
        if type3_found:
            print("✗ FAIL  Type 3 fonts detected — submission systems may reject this.")
        else:
            print("✓ PASS  No Type 3 fonts detected (TrueType embedding OK).")
    else:
        print(f"File format: {path.suffix}")
        print("Font embedding check is only available for PDF files.")

    print()
    print(
        "Note: Full validation requires a live Matplotlib Figure object.\n"
        f"      Use plotstyle.validate(fig, journal={journal!r}) in Python\n"
        "      for complete checks (dimensions, typography, colour, line weights)."
    )

    return 0


def _cmd_export(
    file: str,
    journal: str,
    formats: str | None,
    author: str | None,
    output_dir: str,
) -> int:
    """Print guidance for re-exporting a figure in journal-compliant formats.

    Re-export from the CLI is not supported because it requires the original
    Matplotlib ``Figure`` object.  This handler prints an actionable message
    showing the equivalent Python call.

    Args:
        file: Path to the figure file (used only for display purposes).
        journal: Journal identifier (used for the example snippet).
        formats: Comma-separated output formats, or ``None`` for the journal
            default.
        author: Author surname for IEEE-style file naming, or ``None``.
        output_dir: Target directory for exported files.

    Returns
    -------
        ``0`` always (the message is informational, not an error).

    Notes
    -----
        All parameters are accepted so that the argument parser can validate
        them, even though the handler itself uses only *journal* in its output.
        This preserves forward compatibility if re-export support is added later.
    """
    # Suppress "unused variable" warnings from linters; the parameters are
    # intentionally accepted for API stability but not yet used in output.
    _ = file, formats, author, output_dir

    print(
        "Re-export requires the original Matplotlib Figure object.\n"
        "Use plotstyle.export_submission(fig, ...) in Python.\n\n"
        "Example:\n"
        "  import plotstyle\n"
        f"  plotstyle.export_submission(fig, 'fig1', journal={journal!r})"
    )
    return 0


# ---------------------------------------------------------------------------
# Argument parser factory
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Construct and return the top-level argument parser.

    Factored out of :func:`main` so that the parser can be instantiated in
    tests without invoking :func:`sys.exit`.

    Returns
    -------
        A fully configured :class:`~argparse.ArgumentParser` with all
        sub-commands registered.
    """
    parser = argparse.ArgumentParser(
        prog="plotstyle",
        description="PlotStyle — journal-compliant Matplotlib figure toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  plotstyle list\n"
            "  plotstyle info nature\n"
            "  plotstyle diff nature ieee\n"
            "  plotstyle fonts --journal science\n"
            "  plotstyle validate figure1.pdf --journal nature\n"
            "  plotstyle export figure1.png --journal ieee --formats pdf,eps"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    # ── plotstyle list ────────────────────────────────────────────────────
    subparsers.add_parser(
        "list",
        help="List all available journal presets",
    )

    # ── plotstyle info <journal> ──────────────────────────────────────────
    sub_info = subparsers.add_parser(
        "info",
        help="Show detailed specification for a journal",
    )
    sub_info.add_argument(
        "journal",
        type=str,
        help="Journal identifier (e.g., 'nature', 'ieee')",
    )

    # ── plotstyle diff <journal_a> <journal_b> ────────────────────────────
    sub_diff = subparsers.add_parser(
        "diff",
        help="Compare two journal specifications side-by-side",
    )
    sub_diff.add_argument("journal_a", type=str, help="First journal identifier")
    sub_diff.add_argument("journal_b", type=str, help="Second journal identifier")

    # ── plotstyle fonts --journal <journal> ───────────────────────────────
    sub_fonts = subparsers.add_parser(
        "fonts",
        help="Check font availability for a journal on this system",
    )
    sub_fonts.add_argument(
        "--journal",
        type=str,
        required=True,
        metavar="JOURNAL",
        help="Journal identifier",
    )

    # ── plotstyle validate <file> --journal <journal> ─────────────────────
    sub_validate = subparsers.add_parser(
        "validate",
        help="Validate a saved figure file against a journal specification",
    )
    sub_validate.add_argument(
        "file",
        type=str,
        help="Path to the figure file (PDF for font-embedding checks; PNG/SVG for format info)",
    )
    sub_validate.add_argument(
        "--journal",
        type=str,
        required=True,
        metavar="JOURNAL",
        help="Journal identifier",
    )

    # ── plotstyle export <file> --journal <journal> ───────────────────────
    sub_export = subparsers.add_parser(
        "export",
        help="Re-export a figure in journal-compliant formats (see note)",
    )
    sub_export.add_argument(
        "file",
        type=str,
        help="Path to the figure file",
    )
    sub_export.add_argument(
        "--journal",
        type=str,
        required=True,
        metavar="JOURNAL",
        help="Journal identifier",
    )
    sub_export.add_argument(
        "--formats",
        type=str,
        default=None,
        metavar="FMT,...",
        help="Comma-separated output formats (default: journal preferred formats)",
    )
    sub_export.add_argument(
        "--author",
        type=str,
        default=None,
        metavar="SURNAME",
        help="Author surname for IEEE-style file naming",
    )
    sub_export.add_argument(
        "--output-dir",
        type=str,
        default=".",
        metavar="DIR",
        help="Directory for exported files (default: current directory)",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``plotstyle`` console command.

    Parses *argv* (or ``sys.argv[1:]`` when *argv* is ``None``), dispatches
    to the appropriate ``_cmd_*`` handler, and returns a POSIX exit code.
    All :exc:`KeyError` exceptions — which indicate an unrecognised journal
    identifier — are caught here and reported to ``stderr`` with an
    actionable suggestion.

    Args:
        argv: Argument list to parse.  Pass ``None`` (the default) to use
            ``sys.argv[1:]``, or supply a list explicitly for testing.

    Returns
    -------
        ``0`` on success; ``1`` on any error (unknown journal, file not
        found, or no sub-command given).

    Example:
        >>> from plotstyle.cli.main import main
        >>> main(["list"])
        0
        >>> main(["info", "nature"])
        0
        >>> main([])
        1

    Notes
    -----
        - Only :exc:`~plotstyle.specs.SpecNotFoundError` is caught; all other
          exceptions propagate so that unexpected errors produce a full
          traceback rather than a misleading one-line message.
        - :func:`main` is the value of the ``plotstyle`` console-script entry
          point; it must never call :func:`sys.exit` directly — callers
          (including the ``if __name__ == "__main__"`` guard below) are
          responsible for passing the return value to :class:`SystemExit`.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    try:
        if args.command == "list":
            return _cmd_list()

        if args.command == "info":
            return _cmd_info(args.journal)

        if args.command == "diff":
            return _cmd_diff(args.journal_a, args.journal_b)

        if args.command == "fonts":
            return _cmd_fonts(args.journal)

        if args.command == "validate":
            return _cmd_validate(args.file, args.journal)

        if args.command == "export":
            return _cmd_export(
                args.file,
                args.journal,
                args.formats,
                args.author,
                args.output_dir,
            )

    except SpecNotFoundError as exc:
        # SpecNotFoundError is raised by registry.get() for unknown journal identifiers.
        # Extract the journal name from the exception for a clearer message.
        print(
            f"Error: unknown journal {exc.name!r}.\n"
            "Run 'plotstyle list' to see all available journal identifiers.",
            file=sys.stderr,
        )
        return 1

    # Defensive fallthrough: should be unreachable if all sub-commands are
    # dispatched above, but guards against future parser additions where the
    # dispatch block is not updated.
    print(f"Error: unhandled command {args.command!r}.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
