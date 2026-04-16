"""PlotStyle CLI entry point (``plotstyle`` console command).

Provides sub-commands: ``list``, ``info``, ``diff``, ``fonts``,
``validate``, and ``export``.  The public entry point is :func:`main`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Final

from plotstyle.specs import SpecNotFoundError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PANEL_LABEL_EXAMPLES: Final[dict[str, str]] = {
    "lower": "a, b, c",
    "upper": "A, B, C",
    "parens_lower": "(a), (b), (c)",
    "parens_upper": "(A), (B), (C)",
}

_LIST_NAME_WIDTH: Final[int] = 15
_INFO_SEPARATOR: Final[str] = "──────────────────────────"


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_list() -> int:
    """Print all available journal presets."""
    from plotstyle.specs import registry

    for name in sorted(registry.list_available()):
        spec = registry.get(name)
        print(f"  {name:<{_LIST_NAME_WIDTH}} {spec.metadata.publisher}")

    return 0


def _cmd_info(journal: str) -> int:
    """Print a detailed summary of a journal specification."""
    from plotstyle.specs import registry
    from plotstyle.specs.units import Dimension

    spec = registry.get(journal)
    dim = spec.dimensions
    typo = spec.typography
    exp = spec.export
    col = spec.color
    meta = spec.metadata

    single_in: float = Dimension(dim.single_column_mm, "mm").to_inches()
    double_in: float = Dimension(dim.double_column_mm, "mm").to_inches()

    fonts: str = ", ".join(typo.font_family)
    formats: str = ", ".join(exp.preferred_formats)

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
    """Print a comparison of two journal specifications."""
    from plotstyle.core.migrate import diff

    print(diff(journal_a, journal_b))
    return 0


def _cmd_fonts(journal: str) -> int:
    """Check which fonts required by *journal* are installed on this system."""
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
    """Validate a saved figure file against a journal specification."""
    from plotstyle.engine.fonts import verify_embedded
    from plotstyle.specs import registry

    path = Path(file)
    if not path.exists():
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
    """Print a tailored Python snippet for re-exporting the figure."""
    stem = Path(file).stem
    kwargs: list[str] = [f"journal={journal!r}"]
    if formats:
        fmt_list = [f.strip() for f in formats.split(",")]
        kwargs.append(f"formats={fmt_list!r}")
    if author:
        kwargs.append(f"author_surname={author!r}")
    if output_dir != ".":
        kwargs.append(f"output_dir={output_dir!r}")

    print(
        "Re-export requires the original Matplotlib Figure object.\n"
        "Use plotstyle.export_submission(fig, ...) in Python.\n\n"
        "Example:\n"
        "  import plotstyle\n"
        f"  plotstyle.export_submission(fig, {stem!r}, {', '.join(kwargs)})"
    )
    return 0


# ---------------------------------------------------------------------------
# Argument parser factory
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser with all sub-commands."""
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
            "  plotstyle export figure1.png --journal ieee --formats pdf,eps  # prints snippet"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    subparsers.add_parser(
        "list",
        help="List all available journal presets",
    )

    sub_info = subparsers.add_parser(
        "info",
        help="Show detailed specification for a journal",
    )
    sub_info.add_argument(
        "journal",
        type=str,
        help="Journal identifier (e.g., 'nature', 'ieee')",
    )

    sub_diff = subparsers.add_parser(
        "diff",
        help="Compare two journal specifications side-by-side",
    )
    sub_diff.add_argument("journal_a", type=str, help="First journal identifier")
    sub_diff.add_argument("journal_b", type=str, help="Second journal identifier")

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

    sub_export = subparsers.add_parser(
        "export",
        help="Print a Python snippet for re-exporting a figure in journal-compliant formats",
        description=(
            "Prints a ready-to-run Python snippet that calls "
            "plotstyle.export_submission() with the requested settings. "
            "No file is created — re-export requires the original Matplotlib "
            "Figure object, which cannot be recovered from a saved file."
        ),
    )
    sub_export.add_argument(
        "file",
        type=str,
        help="Path to the figure file (used to derive the output stem)",
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
        help="Comma-separated output formats to include in the generated snippet",
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
        help="Output directory to include in the generated snippet (default: current directory)",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to the appropriate sub-command handler.

    Parameters
    ----------
    argv : list[str] | None
        Argument list to parse.  ``None`` falls back to ``sys.argv[1:]``.

    Returns
    -------
    int
        POSIX exit code: ``0`` on success, ``1`` on error or unknown command.
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
        print(
            f"Error: unknown journal {exc.name!r}.\n"
            "Run 'plotstyle list' to see all available journal identifiers.",
            file=sys.stderr,
        )
        return 1

    print(f"Error: unhandled command {args.command!r}.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
