"""Export-safe figure saving and batch submission packaging.

This module provides two public functions for writing Matplotlib figures to
disk in a manner that satisfies most journal submission portals:

``savefig``
    A drop-in replacement for :func:`matplotlib.figure.Figure.savefig` that
    enforces TrueType font embedding (``pdf.fonttype=42``, ``ps.fonttype=42``)
    and optionally applies a journal's minimum DPI requirement.  A compliance
    summary is printed to *stderr* after each save.

``export_submission``
    A batch wrapper around :func:`savefig` that writes a figure in multiple
    formats, derives default formats from a journal spec, and applies
    journal-specific naming conventions (e.g. IEEE author-prefix filenames).

Design notes
------------
Both functions temporarily override ``pdf.fonttype`` and ``ps.fonttype`` in
``matplotlib.rcParams`` for the duration of the save call and restore the
original values unconditionally via a ``finally`` block.  This guarantees that
the caller's global rcParams state is unchanged after return, even when an
exception is raised during saving.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Final

import matplotlib as mpl

if TYPE_CHECKING:
    from matplotlib.figure import Figure

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
#: The dict is typed ``Final`` to signal that it must not be mutated at runtime.
FORMAT_EXTENSIONS: Final[dict[str, str]] = {
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

# rcParams keys whose original values are snapshotted and restored around
# every save call.  Defined once here to avoid rebuilding the set on each
# call to savefig.
_RESTORE_KEYS: Final[frozenset[str]] = frozenset(SAFETY_PARAMS) | {
    "savefig.dpi",
}

# IEEE requires filenames to be prefixed with the first N characters of the
# submitting author's surname.  Centralising this constant makes future
# journal-spec changes trivial.
_IEEE_SURNAME_PREFIX_LEN: Final[int] = 5

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _snapshot_rcparams(keys: frozenset[str]) -> dict[str, Any]:
    """Return a shallow copy of the current values for the given rcParam keys.

    Only keys that are actually present in ``mpl.rcParams`` are included in
    the snapshot.  Missing keys are silently skipped so that the function
    remains forward-compatible with Matplotlib versions that add or remove
    parameters.

    Args:
        keys: A set of ``mpl.rcParams`` key names to capture.

    Returns
    -------
        A ``dict`` mapping each present key to its current value.
    """
    return {key: mpl.rcParams[key] for key in keys if key in mpl.rcParams}


def _build_filename(
    stem: str,
    fmt: str,
    *,
    author_surname: str | None = None,
    journal: str | None = None,
) -> str:
    """Build a submission-ready filename for a given output format.

    Applies journal-specific naming conventions when the journal is
    recognised.  Currently the only convention implemented is IEEE, which
    prefixes filenames with the first :data:`_IEEE_SURNAME_PREFIX_LEN`
    characters of the author's surname followed by an underscore.

    For unrecognised format strings the key itself is used verbatim as the
    file extension (e.g. ``"webp"`` → ``".webp"``), ensuring graceful
    degradation for formats added after this module was written.

    Args:
        stem: Base filename stem without extension (e.g. ``"fig1"``).
        fmt: Output format key (e.g. ``"pdf"``, ``"tiff"``).
        author_surname: Author surname used for IEEE naming conventions.
            Ignored when *journal* is not ``"ieee"``.
        journal: Journal identifier.  Case-insensitive comparison is used
            so ``"IEEE"``, ``"Ieee"``, and ``"ieee"`` are all equivalent.

    Returns
    -------
        A complete filename string including the resolved extension
        (e.g. ``"smit_fig1.pdf"`` for IEEE with surname ``"Smith"``,
        or ``"fig1.pdf"`` for all other journals).

    Notes
    -----
        The IEEE prefix is formed from the first
        :data:`_IEEE_SURNAME_PREFIX_LEN` characters of the surname,
        lower-cased.  Surnames shorter than that limit are used in full
        (e.g. ``"Lee"`` → ``"lee_fig1.pdf"``).
    """
    ext: str = FORMAT_EXTENSIONS.get(fmt, f".{fmt}")

    # Apply the IEEE author-prefix convention only when *both* the surname and
    # journal are provided and the journal resolves to "ieee".  The explicit
    # truthiness check on author_surname guards against empty-string inputs.
    if author_surname and journal and journal.lower() == "ieee":
        prefix: str = author_surname[:_IEEE_SURNAME_PREFIX_LEN].lower()
        return f"{prefix}_{stem}{ext}"

    return f"{stem}{ext}"


def _print_compliance_summary(
    fig: Figure,
    output_path: Path,
    dpi_value: str | float,
    *,
    out: IO[str] | None = None,
) -> None:
    """Print a human-readable compliance summary to *out* (default: stderr).

    Reports resolution, figure dimensions, and the saved path.  For PDF, PS,
    and EPS outputs, also confirms TrueType font embedding.  For PDF outputs,
    additionally performs a heuristic scan for Type 3 fonts and emits a
    warning if any are detected.

    Type 3 fonts are device-dependent bitmaps that are rejected by many
    journal submission portals.  The scan is intentionally heuristic —
    false negatives are possible for heavily obfuscated PDFs, but false
    positives are rare in practice.

    Args:
        fig: The Matplotlib figure that was saved (used to read dimensions).
        output_path: Resolved path of the file that was written.
        dpi_value: DPI value applied during saving (may be the string
            ``"figure"`` when no explicit DPI was set).
        out: File-like object to write to.  Defaults to ``sys.stderr``.
    """
    out = out or sys.stderr
    width_in, height_in = fig.get_size_inches()

    if output_path.suffix.lower() in {".pdf", ".ps", ".eps"}:
        print("✓ TrueType fonts embedded (pdf.fonttype=42)", file=out)
    print(f"✓ Resolution: {dpi_value} DPI", file=out)
    print(f"✓ Dimensions: {width_in:.2f}in x {height_in:.2f}in", file=out)
    print(f"✓ Saved: {output_path}", file=out)

    # Heuristic Type 3 check is only meaningful for PDF files; other formats
    # do not embed font programs in a way this scanner can detect.
    if output_path.suffix.lower() != ".pdf":
        return

    type3_hits: list[dict[str, Any]] = verify_embedded(output_path)

    # Emit at most one warning per file to avoid log spam; the first hit is
    # sufficient to prompt the author to investigate.
    for hit in type3_hits:
        if hit.get("type") == "Type3":
            print(
                f"⚠ Warning: Type 3 font detected in '{output_path}'. "
                "Many submission portals will reject this file. "
                "Ensure all fonts are converted to TrueType before submitting.",
                file=out,
            )
            break


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def savefig(
    fig: Figure,
    path: str | Path,
    *,
    journal: str | None = None,
    **kwargs: object,
) -> None:
    """Save a figure with export-safe font embedding and optional journal DPI.

    Acts as a drop-in replacement for :meth:`~matplotlib.figure.Figure.savefig`
    with two additional guarantees:

    1. **TrueType font embedding** — ``pdf.fonttype`` and ``ps.fonttype`` are
       set to ``42`` for the duration of the save, ensuring fonts are embedded
       as TrueType rather than Type 3 bitmaps.
    2. **Journal DPI enforcement** — when *journal* is provided, the journal
       spec's ``min_dpi`` is applied as ``savefig.dpi`` for this call only.

    Both overrides are scoped to this function call: original ``mpl.rcParams``
    values are restored unconditionally in a ``finally`` block, so the caller's
    global state is never mutated on return.

    Args:
        fig: Matplotlib figure instance to save.
        path: Output file path.  The file extension determines the format
            unless *format* is also supplied via *kwargs*.
        journal: Optional journal preset name registered with
            the spec registry.  When given, the journal's ``min_dpi``
            overrides ``savefig.dpi`` for this call.
        **kwargs: Additional keyword arguments forwarded verbatim to
            :meth:`~matplotlib.figure.Figure.savefig`.  ``bbox_inches``
            defaults to ``"tight"`` if not explicitly provided.

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If *journal* is provided but is
            not registered in the spec registry.
        OSError: If the output path is not writable or the parent directory
            does not exist.

    Notes
    -----
        A compliance summary (dimensions, DPI, path, and any Type 3 font
        warnings) is always printed to *stderr* after a successful save.
        This output is intentional and aimed at CI pipelines and interactive
        use; redirect *stderr* to suppress it.

    Example::

        import plotstyle
        import matplotlib.pyplot as plt

        with plotstyle.use("nature"):
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])
            plotstyle.savefig(fig, "figure.pdf", journal="nature")
    """
    output_path = Path(path)

    # Capture the current values of every rcParams key we intend to modify so
    # they can be restored unconditionally in the finally block below.
    saved_rc: dict[str, Any] = _snapshot_rcparams(_RESTORE_KEYS)

    try:
        # Override font-type settings to force TrueType embedding.  These two
        # keys are the primary reason this wrapper exists: the Matplotlib
        # default (Type 3) is incompatible with most journal submission portals.
        mpl.rcParams["pdf.fonttype"] = 42
        mpl.rcParams["ps.fonttype"] = 42

        if journal is not None:
            spec = registry.get(journal)
            # Apply the journal's minimum DPI; this may result in a *larger*
            # file than the caller's default but ensures compliance.
            mpl.rcParams["savefig.dpi"] = spec.export.min_dpi

        # Tight bounding box prevents axis labels and titles from being clipped
        # at the figure edge — a common source of desk-reject feedback.
        kwargs.setdefault("bbox_inches", "tight")

        # Determine effective DPI before saving: an explicit dpi= kwarg
        # overrides both the journal minimum and the rcParam.
        dpi_value: Any = kwargs.get("dpi", mpl.rcParams.get("savefig.dpi", "figure"))

        fig.savefig(str(output_path), **kwargs)

        _print_compliance_summary(fig, output_path, dpi_value)

    finally:
        # Restore the original rcParams state.  Using update() in a single
        # call is atomic from Python's perspective and avoids partial-restore
        # bugs that could arise from iterating and setting keys individually.
        mpl.rcParams.update(saved_rc)


def export_submission(
    fig: Figure,
    stem: str,
    *,
    formats: list[str] | None = None,
    journal: str | None = None,
    output_dir: str | Path = ".",
    author_surname: str | None = None,
) -> list[Path]:
    """Export a figure in multiple formats for journal submission.

    Calls :func:`savefig` for each requested output format, applying
    journal-safe settings (TrueType embedding, correct DPI) to every file.
    The format list, DPI, and filename conventions are all derived from the
    journal spec when *journal* is supplied.

    Format resolution priority
    --------------------------
    1. Explicit *formats* argument (highest priority).
    2. Journal spec's ``preferred_formats`` list (when *journal* is given).
    3. ``["pdf"]`` fallback (lowest priority).

    Args:
        fig: Matplotlib figure instance to export.
        stem: Base filename stem shared by all output files (e.g. ``"fig1"``).
            Journal-specific prefixes and format extensions are appended
            automatically; do not include an extension here.
        formats: Explicit list of output format keys (e.g. ``["pdf", "tiff"]``).
            Overrides the journal spec's preferred formats when supplied.
        journal: Optional journal preset name registered with
            the spec registry.  Used to resolve default formats, apply
            DPI constraints, and select naming conventions.
        output_dir: Directory into which all output files are written.
            Created (including any missing parents) if it does not exist.
            Defaults to the current working directory.
        author_surname: Submitting author's surname, used by journals with
            surname-prefix filename conventions (currently only IEEE).
            Ignored for all other journals.

    Returns
    -------
        An ordered list of :class:`~pathlib.Path` objects, one for each file
        that was created, in the same order as the resolved format list.

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If *journal* is provided but is
            not registered in the spec registry.
        OSError: If *output_dir* cannot be created or any output file cannot
            be written.

    Notes
    -----
        A brief submission summary (file count and names) is printed to
        *stderr* after all formats have been saved.

    Example::

        import plotstyle
        import matplotlib.pyplot as plt

        with plotstyle.use("ieee"):
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])
            paths = plotstyle.export_submission(
                fig,
                "fig1",
                journal="ieee",
                author_surname="Smith",
            )
        # Produces: smit_fig1.pdf (and any other IEEE preferred formats).
    """
    out_dir = Path(output_dir)
    # exist_ok=True makes this idempotent; parents=True avoids requiring the
    # caller to pre-create intermediate directories.
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve the format list using the documented priority order.
    if formats is not None:
        fmt_list: list[str] = formats
    elif journal is not None:
        spec = registry.get(journal)
        fmt_list = list(spec.export.preferred_formats)
    else:
        fmt_list = ["pdf"]

    created: list[Path] = []

    for fmt in fmt_list:
        filename = _build_filename(
            stem,
            fmt,
            author_surname=author_surname,
            journal=journal,
        )
        file_path = out_dir / filename
        savefig(fig, file_path, journal=journal, format=fmt)
        created.append(file_path)

    # Emit a concise submission manifest to stderr so authors can quickly
    # verify that all expected files were produced without inspecting the
    # return value.
    journal_label: str = journal or "generic"
    print(
        f"\nExported {len(created)} file(s) for {journal_label} submission:",
        file=sys.stderr,
    )
    for p in created:
        print(f"  ✓ {p.name}", file=sys.stderr)

    return created
