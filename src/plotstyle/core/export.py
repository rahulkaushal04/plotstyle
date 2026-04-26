"""Export-safe figure saving and batch submission packaging.

``savefig``
    A drop-in replacement for :func:`matplotlib.figure.Figure.savefig` that
    enforces TrueType font embedding and optionally applies a journal's minimum
    DPI requirement.

``export_submission``
    A batch wrapper around :func:`savefig` that writes a figure in multiple
    formats and applies journal-specific naming conventions.
"""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Final

import matplotlib as mpl

if TYPE_CHECKING:
    from matplotlib.figure import Figure

from plotstyle._utils.warnings import PlotStyleWarning
from plotstyle.engine.fonts import verify_embedded
from plotstyle.engine.rcparams import SAFETY_PARAMS
from plotstyle.specs import registry

__all__: list[str] = [
    "FORMAT_EXTENSIONS",
    "export_submission",
    "savefig",
]

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: Maps canonical format names to their standard file extensions.
FORMAT_EXTENSIONS: Final[dict[str, str]] = {
    "ai": ".ai",
    "pdf": ".pdf",
    "eps": ".eps",
    "tiff": ".tiff",
    "tif": ".tif",
    "png": ".png",
    "svg": ".svg",
    "jpg": ".jpg",
    "jpeg": ".jpeg",
    "ps": ".ps",
}

#: Formats that Matplotlib's savefig() can actually produce.
#: Journal specs may list additional formats (e.g. "ai") that require
#: external tools; these are skipped during export with a warning.
_MATPLOTLIB_FORMATS: Final[frozenset[str]] = frozenset(
    {"pdf", "eps", "svg", "tiff", "tif", "png", "jpg", "jpeg", "ps"}
)

_RESTORE_KEYS: Final[frozenset[str]] = frozenset(SAFETY_PARAMS) | {
    "savefig.dpi",
}

_IEEE_SURNAME_PREFIX_LEN: Final[int] = 5

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _snapshot_rcparams(keys: frozenset[str]) -> dict[str, Any]:
    """Return the current ``mpl.rcParams`` values for the given *keys*."""
    return {key: mpl.rcParams[key] for key in keys if key in mpl.rcParams}


def _build_filename(
    stem: str,
    fmt: str,
    *,
    author_surname: str | None = None,
    journal: str | None = None,
) -> str:
    """Build a submission-ready filename for a given output format.

    Applies journal-specific naming conventions; currently only IEEE prefixes
    filenames with the first few characters of the author's surname.
    Unknown format strings are used verbatim as the extension
    (e.g. ``"webp"`` → ``".webp"``).

    Parameters
    ----------
    stem : str
        Base filename stem without extension (e.g. ``"fig1"``).
    fmt : str
        Output format key (e.g. ``"pdf"``, ``"tiff"``).
    author_surname : str | None
        Author surname for IEEE naming conventions.
        Ignored when *journal* is not ``"ieee"``.
    journal : str | None
        Journal identifier (case-insensitive).

    Returns
    -------
    str
        Complete filename string including the resolved extension.
    """
    ext = FORMAT_EXTENSIONS.get(fmt, f".{fmt}")

    if author_surname and journal and journal.lower() == "ieee":
        prefix = author_surname[:_IEEE_SURNAME_PREFIX_LEN].lower()
        return f"{prefix}_{stem}{ext}"

    return f"{stem}{ext}"


def _print_compliance_summary(
    fig: Figure,
    output_path: Path,
    dpi_value: str | float,
    *,
    type3_hits: list[dict[str, Any]] | None = None,
    out: IO[str] | None = None,
) -> None:
    """Print a compliance summary to *out* (default: stderr).

    Parameters
    ----------
    fig : Figure
        The saved figure (used to read dimensions).
    output_path : Path
        Path of the file that was written.
    dpi_value : str | float
        DPI used during saving (``"figure"`` when no explicit DPI was set).
    type3_hits : list[dict[str, Any]] | None
        Pre-computed :func:`~plotstyle.engine.fonts.verify_embedded` result.
        Pass ``None`` to call ``verify_embedded`` internally.
    out : IO[str] | None
        Output stream.  Defaults to ``sys.stderr``.
    """
    out = out or sys.stderr
    width_in, height_in = fig.get_size_inches()

    if output_path.suffix.lower() in {".pdf", ".ps", ".eps"}:
        if output_path.suffix.lower() == ".pdf":
            # Use pre-computed hits when available to avoid re-reading the file.
            hits = type3_hits if type3_hits is not None else verify_embedded(output_path)
            type3_found = any(h.get("type") == "Type3" for h in hits)
            if type3_found:
                print("✗ Type 3 font detected: many submission portals will reject this.", file=out)
            else:
                print("✓ TrueType fonts embedded (pdf.fonttype=42)", file=out)
        else:
            print("✓ TrueType fonts embedded (ps.fonttype=42)", file=out)
    print(f"✓ Resolution: {dpi_value} DPI", file=out)
    print(f"✓ Dimensions: {width_in:.2f}in x {height_in:.2f}in", file=out)
    print(f"✓ Saved: {output_path}", file=out)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def savefig(
    fig: Figure,
    path: str | Path,
    *,
    journal: str | None = None,
    quiet: bool = False,
    **kwargs: object,
) -> None:
    """Save a figure with export-safe font embedding and optional journal DPI.

    Acts as a drop-in replacement for :meth:`~matplotlib.figure.Figure.savefig`
    with two additional guarantees:

    1. **TrueType font embedding**: ``pdf.fonttype`` and ``ps.fonttype`` are
       set to ``42`` for the duration of the save, ensuring fonts are embedded
       as TrueType rather than Type 3 bitmaps.
    2. **Journal DPI enforcement**: when *journal* is provided, the journal
       spec's ``min_dpi`` is applied as ``savefig.dpi`` for this call only.

    Both overrides are scoped to this function call: original ``mpl.rcParams``
    values are restored unconditionally in a ``finally`` block, so the caller's
    global state is never mutated on return.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure instance to save.
    path : str | Path
        Output file path.  The file extension determines the format
        unless *format* is also supplied via *kwargs*.
    journal : str | None
        Optional journal preset name registered with
        the spec registry.  When given, the journal's ``min_dpi``
        overrides ``savefig.dpi`` for this call.
    quiet : bool
        When ``True``, the compliance summary (dimensions, DPI, saved
        path) is not printed.  Type 3 font warnings are still emitted via
        :mod:`warnings` regardless of this flag.
    **kwargs : dict
        Additional keyword arguments forwarded verbatim to
        :meth:`~matplotlib.figure.Figure.savefig`.  ``bbox_inches``
        defaults to ``"tight"`` if not explicitly provided.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If *journal* is provided but is not registered in the spec registry.
    OSError
        If the output path is not writable or the parent directory does not
        exist.

    Notes
    -----
    A compliance summary is printed to ``sys.stderr`` unless *quiet* is
    ``True``.  Type 3 font detections are always emitted via
    :func:`warnings.warn` regardless of *quiet*.
    """
    output_path = Path(path)

    # Snapshot rcParams for unconditional restoration in the finally block.
    saved_rc = _snapshot_rcparams(_RESTORE_KEYS)

    try:
        # Force TrueType embedding; Matplotlib's default (Type 3) is rejected by most submission portals.
        mpl.rcParams["pdf.fonttype"] = 42
        mpl.rcParams["ps.fonttype"] = 42

        if journal is not None:
            spec = registry.get(journal)
            mpl.rcParams["savefig.dpi"] = spec.export.min_dpi

        # Tight bounding box prevents clipped labels, a common source of desk-reject feedback.
        kwargs.setdefault("bbox_inches", "tight")

        # An explicit dpi= kwarg overrides both the journal minimum and the rcParam.
        dpi_value = kwargs.get("dpi", mpl.rcParams.get("savefig.dpi", "figure"))

        _fonttools_logger = logging.getLogger("fontTools")
        _prev_level = _fonttools_logger.level
        _fonttools_logger.setLevel(logging.ERROR)
        try:
            fig.savefig(str(output_path), **kwargs)
        finally:
            _fonttools_logger.setLevel(_prev_level)

        type3_hits: list[dict[str, Any]] | None = None
        if output_path.suffix.lower() == ".pdf":
            type3_hits = verify_embedded(output_path)
            for hit in type3_hits:
                if hit.get("type") == "Type3":
                    warnings.warn(
                        f"Type 3 font detected in '{output_path}'. "
                        "Many submission portals will reject this file. "
                        "Ensure all fonts are converted to TrueType before submitting.",
                        PlotStyleWarning,
                        stacklevel=2,
                    )
                    break

        if not quiet:
            _print_compliance_summary(fig, output_path, dpi_value, type3_hits=type3_hits)

    finally:
        # Restore atomically via update() to avoid partial-restore if a key fails.
        mpl.rcParams.update(saved_rc)


def export_submission(
    fig: Figure,
    stem: str,
    *,
    formats: list[str] | None = None,
    journal: str | None = None,
    output_dir: str | Path = ".",
    author_surname: str | None = None,
    quiet: bool = False,
) -> list[Path]:
    """Export a figure in multiple formats for journal submission.

    Calls :func:`savefig` for each format, applying journal-safe font embedding
    and DPI settings.

    Format resolution order
    -----------------------
    1. Explicit *formats* argument.
    2. Journal spec's ``preferred_formats`` (when *journal* is given).
    3. ``["pdf"]`` fallback.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure instance to export.
    stem : str
        Base filename stem shared by all output files (e.g. ``"fig1"``).
        Journal-specific prefixes and format extensions are appended
        automatically; do not include an extension here.
    formats : list[str] | None
        Explicit list of output format keys (e.g. ``["pdf", "tiff"]``).
        Overrides the journal spec's preferred formats when supplied.
    journal : str | None
        Optional journal preset name registered with
        the spec registry.  Used to resolve default formats, apply
        DPI constraints, and select naming conventions.
    output_dir : str | Path
        Directory into which all output files are written.
        Created (including any missing parents) if it does not exist.
        Defaults to the current working directory.
    author_surname : str | None
        Submitting author's surname, used by journals with
        surname-prefix filename conventions (currently only IEEE).
        Ignored for all other journals.
    quiet : bool
        When ``True``, the per-file compliance summaries and the
        final submission manifest are not printed.  Type 3 font warnings
        are still emitted via :mod:`warnings` for each file regardless
        of this flag.

    Returns
    -------
    list[Path]
        An ordered list of :class:`~pathlib.Path` objects, one for each file
        that was created, in the same order as the resolved format list.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If *journal* is provided but is not registered in the spec registry.
    OSError
        If *output_dir* cannot be created or any output file cannot be
        written.

    Notes
    -----
    A submission manifest is printed to ``sys.stderr`` unless *quiet* is
    ``True``.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if formats is not None:
        fmt_list = formats
    elif journal is not None:
        spec = registry.get(journal)
        fmt_list = list(spec.export.preferred_formats)
    else:
        fmt_list = ["pdf"]

    created: list[Path] = []
    skipped: list[str] = []

    for fmt in fmt_list:
        if fmt.lower() not in _MATPLOTLIB_FORMATS:
            skipped.append(fmt)
            continue
        filename = _build_filename(
            stem,
            fmt,
            author_surname=author_surname,
            journal=journal,
        )
        file_path = out_dir / filename
        savefig(fig, file_path, journal=journal, format=fmt, quiet=quiet)
        created.append(file_path)

    if not quiet:
        journal_label = journal or "generic"
        print(
            f"\nExported {len(created)} file(s) for {journal_label} submission:",
            file=sys.stderr,
        )
        for p in created:
            print(f"  ✓ {p.name}", file=sys.stderr)
        for fmt in skipped:
            print(
                f"  ⊘ {fmt} skipped (requires external tool, not supported by Matplotlib)",
                file=sys.stderr,
            )

    return created
