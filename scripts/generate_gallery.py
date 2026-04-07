"""Generate gallery preview images for all registered journal presets.

Produces one PNG per journal and writes them to the documentation static
assets directory so they can be embedded in the PlotStyle docs site.

Output files follow the naming convention::

    docs/_static/gallery_{journal}.png

Usage
-----
Run from the repository root::

    python scripts/generate_gallery.py

Or customise output location, DPI, or column count::

    python scripts/generate_gallery.py --output-dir docs/_static --dpi 200 --columns 1

Restricting to specific journals::

    python scripts/generate_gallery.py --journals nature ieee

Exit codes
----------
- ``0`` — all gallery images generated successfully.
- ``1`` — one or more images failed to generate, or no journals were found.

Design notes
------------
- ``matplotlib.use("Agg")`` is called **before** any pyplot import to force
  the non-interactive Agg backend.  This is required in headless CI/CD
  environments where no display server is available.  The call must precede
  the first ``import matplotlib.pyplot`` anywhere in the process; placing it
  at module level (after ``import matplotlib``) satisfies this constraint
  regardless of import order in calling code.
- :func:`plt.close` is called immediately after saving each figure to release
  the Matplotlib figure memory.  Without this, generating many journals in a
  loop accumulates figures in memory and triggers a Matplotlib
  "Too many open figures" warning at 20+ figures.
- Each failed journal is reported and counted rather than raising immediately,
  so a single broken spec does not prevent the remaining journals from being
  processed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ``matplotlib.use`` must be called before pyplot is imported anywhere in the
# process.  Placing it here at module level, immediately after the bare
# matplotlib import, guarantees ordering regardless of how this script is
# invoked (directly or via importlib).
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from plotstyle.preview.gallery import gallery
from plotstyle.specs import registry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default output directory for gallery PNGs, relative to this script.
_DEFAULT_OUTPUT_DIR: Path = Path(__file__).resolve().parent.parent / "docs" / "_static"

#: Default resolution for saved gallery images.
_DEFAULT_DPI: int = 150

#: Default number of example plot columns inside each gallery figure.
_DEFAULT_COLUMNS: int = 2

#: Filename template for each gallery image; receives the journal identifier.
_FILENAME_TEMPLATE: str = "gallery_{journal}.png"


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
        prog="generate_gallery",
        description=(
            "Generate gallery preview PNGs for all PlotStyle journal presets.\n"
            f"Default output: {_DEFAULT_OUTPUT_DIR}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_DEFAULT_OUTPUT_DIR,
        metavar="DIR",
        help=f"Directory for generated PNG files (default: {_DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=_DEFAULT_DPI,
        metavar="DPI",
        help=f"Resolution of saved images in dots per inch (default: {_DEFAULT_DPI}).",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=_DEFAULT_COLUMNS,
        metavar="N",
        help=f"Number of example plot columns per gallery figure (default: {_DEFAULT_COLUMNS}).",
    )
    parser.add_argument(
        "--journals",
        nargs="+",
        metavar="JOURNAL",
        default=None,
        help=("One or more journal identifiers to generate. Defaults to all registered journals."),
    )
    return parser


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------


def _generate_one(
    journal: str,
    output_dir: Path,
    *,
    dpi: int,
    columns: int,
) -> Path:
    """Generate and save the gallery figure for a single journal.

    Args:
        journal:    Journal identifier recognised by the spec registry.
        output_dir: Directory in which to write the PNG file.  Must exist.
        dpi:        Output resolution in dots per inch.
        columns:    Number of example plot columns inside the gallery figure.

    Returns
    -------
        The :class:`~pathlib.Path` of the saved PNG file.

    Raises
    ------
        KeyError:  If *journal* is not registered in the spec registry.
        OSError:   If the output file cannot be written.
        Exception: Any exception raised by :func:`~plotstyle.preview.gallery.gallery`
                   or :meth:`~matplotlib.figure.Figure.savefig` propagates
                   unchanged so the caller can decide whether to skip or abort.
    """
    fig = gallery(journal, columns=columns)
    try:
        out_path = output_dir / _FILENAME_TEMPLATE.format(journal=journal)
        # bbox_inches="tight" trims surrounding whitespace so the PNG is as
        # compact as possible for documentation embedding.
        fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    finally:
        # Always release the figure's memory, even if savefig raised, to
        # prevent Matplotlib's "Too many open figures" warning during long runs.
        plt.close(fig)

    return out_path


def _process_one(
    journal: str,
    output_dir: Path,
    *,
    dpi: int,
    columns: int,
) -> tuple[Path | None, str | None]:
    """Attempt to generate the gallery image for *journal*, capturing errors.

    Wraps :func:`_generate_one` to convert exceptions into ``(None, message)``
    pairs so the calling loop avoids a ``try``/``except`` in its body
    (see :pep:`PERF203 <203>`).

    Args:
        journal:    Journal identifier recognised by the spec registry.
        output_dir: Directory in which to write the PNG file.  Must exist.
        dpi:        Output resolution in dots per inch.
        columns:    Number of example plot columns inside the gallery figure.

    Returns
    -------
        ``(out_path, None)`` on success, or ``(None, error_message)`` on failure.
    """
    try:
        return _generate_one(journal, output_dir, dpi=dpi, columns=columns), None
    except KeyError:
        return None, "unknown journal — not in registry (run 'plotstyle list')"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Generate gallery images for all (or selected) journal presets.

    Args:
        argv: Argument list to parse.  ``None`` defaults to ``sys.argv[1:]``.

    Returns
    -------
        ``0`` if every requested journal was generated successfully; ``1`` if
        any failed or no journals were found.
    """
    args = _build_parser().parse_args(argv)
    output_dir: Path = args.output_dir
    dpi: int = args.dpi
    columns: int = args.columns

    # Resolve the list of journals: explicit --journals flag, or all available.
    requested: list[str] = args.journals or sorted(registry.list_available())

    if not requested:
        print("No journal presets found in the registry.", file=sys.stderr)
        return 1

    # Ensure the output directory exists before attempting any writes.
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Generating {len(requested)} gallery image(s) "
        f"→ {output_dir}  (dpi={dpi}, columns={columns})\n"
    )

    succeeded: list[str] = []
    failed: list[tuple[str, str]] = []

    for journal in requested:
        out_path, err = _process_one(journal, output_dir, dpi=dpi, columns=columns)
        if err is None:
            print(f"  ✓ {out_path.name}")
            succeeded.append(journal)
        else:
            print(f"  ✗ {journal} — {err}")
            failed.append((journal, err))

    # Summary
    print()
    print(f"Done: {len(succeeded)}/{len(requested)} image(s) generated in {output_dir}.")

    if failed:
        print(f"\n{len(failed)} failure(s):")
        for journal, msg in failed:
            print(f"  • {journal}: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
