"""Journal comparison and figure migration utilities.

This module provides two public functions for working across journal specs:

``diff``
    Compare two journal specifications and return a structured
    :class:`SpecDiff` object describing every field that differs.  Pure
    function — no side effects.

``migrate``
    Re-style an existing Matplotlib figure for a different journal.
    Resizes the figure, rescales text proportionally, and applies the
    target journal's rcParams in-place.

Supporting types
----------------
``SpecDiff``
    Holds the full comparison result; supports pretty-printing via
    :func:`str`, length query via :func:`len`, and serialisation to
    ``dict`` via :meth:`~SpecDiff.to_dict`.

``SpecDifference``
    Immutable record for a single differing field — dotted path, human
    label, and both formatted values.

Design notes
------------
**Field manifest** — the set of spec fields included in a diff is defined
in :data:`_DIFF_FIELDS`, a module-level list of ``(dotted_path, label,
formatter)`` triples.  Adding or removing tracked fields requires only a
one-line change to that list; no function bodies need to be modified.

**Mutation contract** — :func:`migrate` mutates its *fig* argument in-place
and returns it to support call chaining.  Clone the figure first if you need
to preserve the original.

**rcParams scope** — :func:`migrate` calls ``mpl.rcParams.update`` with the
target journal's full rcParams dict.  Wrap the call in a
:func:`~plotstyle.core.style.use` context manager if you need the original
state restored afterwards.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final

import matplotlib as mpl

from plotstyle._utils.warnings import PlotStyleWarning
from plotstyle.engine.rcparams import build_rcparams
from plotstyle.specs import registry
from plotstyle.specs.units import Dimension

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec

__all__: list[str] = [
    "SpecDiff",
    "SpecDifference",
    "diff",
    "migrate",
]

# ---------------------------------------------------------------------------
# Internal formatting helpers
# ---------------------------------------------------------------------------
# Each helper converts a raw spec attribute value to a human-readable string
# for display in a SpecDiff table.  They are intentionally tiny so that the
# _DIFF_FIELDS manifest stays concise; keeping formatting logic out of the
# manifest itself also makes unit-testing each formatter trivial.


def _format_list(value: object) -> str:
    """Format a value as a comma-separated string.

    Lists are joined element-by-element; non-list values are passed through
    :func:`str` directly.  This uniformity means callers do not need to
    branch on the value type.

    Args:
        value: A :class:`list` whose items support :func:`str`, or any
            other value.

    Returns
    -------
        Comma-separated string representation (e.g. ``"pdf, tiff"``), or
        the plain string representation for non-list inputs.
    """
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _format_mm(value: object) -> str:
    """Format a numeric value as a millimetre measurement string.

    Args:
        value: Numeric dimension value.

    Returns
    -------
        String of the form ``"<value>mm"`` (e.g. ``"88mm"``).
    """
    return f"{value}mm"


def _format_pt(value: object) -> str:
    """Format a numeric value as a typographic point-size string.

    Args:
        value: Numeric point size.

    Returns
    -------
        String of the form ``"<value>pt"`` (e.g. ``"7pt"``).
    """
    return f"{value}pt"


def _format_bool(value: object) -> str:
    """Format a boolean as ``"Yes"`` or ``"No"``.

    Args:
        value: Any value interpreted as a boolean.

    Returns
    -------
        ``"Yes"`` if *value* is truthy, ``"No"`` otherwise.
    """
    return "Yes" if value else "No"


def _resolve_attr(obj: object, dotted_path: str) -> object:
    """Resolve a dotted attribute path on a nested object graph.

    Equivalent to a chain of :func:`getattr` calls, e.g.
    ``obj.typography.font_family`` for the path
    ``"typography.font_family"``.

    Args:
        obj: Root object to traverse.
        dotted_path: Dot-separated attribute path
            (e.g. ``"typography.font_family"``).

    Returns
    -------
        The value at the end of the attribute chain.

    Raises
    ------
        AttributeError: If any segment of *dotted_path* is not a valid
            attribute of the object at that level of traversal.
    """
    for part in dotted_path.split("."):
        obj = getattr(obj, part)
    return obj


# ---------------------------------------------------------------------------
# Diff field manifest
# ---------------------------------------------------------------------------

# Each entry is a (dotted_path, human_label, formatter) triple describing one
# spec field to compare.  The ordering is intentionally logical
# (dimensions → typography → export → color → line) so that printed diffs
# read top-to-bottom in a natural, grouped way.
#
# To add a new tracked field: append a single entry here.  No other code
# changes are required.
_DIFF_FIELDS: Final[list[tuple[str, str, Callable[[Any], str]]]] = [
    ("dimensions.single_column_mm", "Column Width (single)", _format_mm),
    ("dimensions.double_column_mm", "Column Width (double)", _format_mm),
    ("dimensions.max_height_mm", "Max Height", _format_mm),
    ("typography.font_family", "Font Family", _format_list),
    ("typography.min_font_pt", "Min Font Size", _format_pt),
    ("typography.max_font_pt", "Max Font Size", _format_pt),
    ("typography.panel_label_pt", "Panel Label Size", _format_pt),
    ("typography.panel_label_weight", "Panel Label Weight", str),
    ("typography.panel_label_case", "Panel Label Case", str),
    ("export.min_dpi", "Min DPI", str),
    ("export.preferred_formats", "Preferred Formats", _format_list),
    ("export.color_space", "Color Space", str),
    ("color.grayscale_required", "Grayscale Required", _format_bool),
    ("color.colorblind_required", "Colorblind Required", _format_bool),
    ("line.min_weight_pt", "Min Line Weight", _format_pt),
]

# Width of the separator line in __str__.  Wide enough to accommodate labels
# and typical formatted values side-by-side.
_SEPARATOR_WIDTH: Final[int] = 50

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SpecDifference:
    """Immutable record of a single parameter difference between two specs.

    Instances are produced by :func:`diff` and stored in
    :attr:`SpecDiff.differences`.  The frozen dataclass guarantees that
    records are safe to cache, hash, and share across threads.

    Attributes
    ----------
        field: Dotted attribute path on
            :class:`~plotstyle.specs.schema.JournalSpec`
            (e.g. ``"dimensions.single_column_mm"``).
        label: Human-readable description of the field
            (e.g. ``"Column Width (single)"``).
        value_a: Formatted string value from the first journal spec.
        value_b: Formatted string value from the second journal spec.
    """

    field: str
    label: str
    value_a: str
    value_b: str


@dataclass(slots=True)
class SpecDiff:
    """Complete, structured comparison between two journal specifications.

    Returned by :func:`diff`.  Provides three access patterns:

    - **Human-readable** — pass the instance to :func:`str` or :func:`print`
      to get an aligned two-column table.
    - **Programmatic** — iterate over :attr:`differences`, test ``len()``, or
      use the instance directly in a boolean context (falsy when identical).
    - **Machine-readable** — call :meth:`to_dict` and serialise with
      :mod:`json`.

    Attributes
    ----------
        journal_a: Display name of the first journal (from spec metadata).
        journal_b: Display name of the second journal (from spec metadata).
        differences: Ordered list of :class:`SpecDifference` records for each
            field where the two specs disagree.  Empty when the specs are
            identical across all tracked fields.

    Example::

        result = plotstyle.diff("nature", "science")
        print(result)  # human-readable aligned table
        print(len(result))  # number of differing fields
        data = result.to_dict()  # plain dict ready for JSON serialisation
    """

    journal_a: str
    journal_b: str
    differences: list[SpecDifference] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Return ``True`` when at least one field differs.

        Allows idiomatic usage such as ``if plotstyle.diff("a", "b"): ...``.
        """
        return bool(self.differences)

    def __len__(self) -> int:
        """Return the number of fields that differ between the two specs."""
        return len(self.differences)

    def __str__(self) -> str:
        """Render the diff as a human-readable, aligned two-column table.

        Returns
        -------
            Multi-line string with the journal pair on the first line, a
            separator, and one row per differing field formatted as
            ``"Label:   <value_a> → <value_b>"``.  Returns a
            ``"No differences."`` message when the specs are identical.
        """
        header: str = f"{self.journal_a} → {self.journal_b}"

        if not self.differences:
            return f"{header}\nNo differences."

        # Compute label-column width once so all rows align on the arrow.
        max_label_len: int = max(len(d.label) for d in self.differences)
        separator: str = "─" * _SEPARATOR_WIDTH

        rows: list[str] = [
            f"{d.label + ':':<{max_label_len + 1}}  {d.value_a} → {d.value_b}"
            for d in self.differences
        ]

        return "\n".join([header, separator, *rows])

    def to_dict(self) -> dict[str, Any]:
        """Serialise the diff to a plain dictionary.

        Returns
        -------
            A ``dict`` with keys ``"journal_a"``, ``"journal_b"``, and
            ``"differences"`` (a list of per-field dicts with ``"field"``,
            ``"label"``, ``"value_a"``, and ``"value_b"`` keys).
            All values are JSON-serialisable primitives.
        """
        return {
            "journal_a": self.journal_a,
            "journal_b": self.journal_b,
            "differences": [
                {
                    "field": d.field,
                    "label": d.label,
                    "value_a": d.value_a,
                    "value_b": d.value_b,
                }
                for d in self.differences
            ],
        }


# ---------------------------------------------------------------------------
# Internal migration helpers
# ---------------------------------------------------------------------------


def _rescale_text_artists(
    fig: Figure,
    scale: float,
    min_pt: float,
    max_pt: float,
) -> None:
    """Rescale all Text artists in *fig* and clamp to ``[min_pt, max_pt]``.

    Walks the full artist tree via :meth:`~matplotlib.figure.Figure.findobj`
    and adjusts every :class:`~matplotlib.text.Text` instance in-place.
    Clamping prevents rescaled sizes from falling outside the target
    journal's permitted range.

    Args:
        fig: Figure whose text artists are mutated in-place.
        scale: Multiplicative scale factor to apply to each artist's current
            font size.
        min_pt: Lower bound (inclusive) of the target journal's allowed font
            size range, in typographic points.
        max_pt: Upper bound (inclusive) of the target journal's allowed font
            size range, in typographic points.
    """
    for text_artist in fig.findobj(mpl.text.Text):
        raw_size: float = text_artist.get_fontsize()
        # Clamp into [min_pt, max_pt] after scaling.
        clamped: float = max(min_pt, min(max_pt, raw_size * scale))
        text_artist.set_fontsize(clamped)


def _emit_migration_warnings(
    from_spec: JournalSpec,
    to_spec: JournalSpec,
) -> None:
    """Emit :class:`~plotstyle._utils.warnings.PlotStyleWarning` for notable spec changes.

    Issues warnings for the three categories of change most likely to require
    author action: font family change, newly required grayscale safety, and
    an increased DPI floor.

    Args:
        from_spec: Source journal spec.
        to_spec: Target journal spec.

    Notes
    -----
        ``stacklevel=3`` is used so that the warning points to the
        :func:`migrate` call site in user code rather than to this internal
        helper or its caller.
    """
    if from_spec.typography.font_family != to_spec.typography.font_family:
        warnings.warn(
            f"Font family changed: {from_spec.typography.font_family!r} "
            f"→ {to_spec.typography.font_family!r}. "
            "Update any hardcoded font references in your figure.",
            PlotStyleWarning,
            stacklevel=3,
        )

    # Warn only when the requirement is *newly introduced*, not when both
    # journals already require it — that case is not a migration concern.
    if to_spec.color.grayscale_required and not from_spec.color.grayscale_required:
        warnings.warn(
            f"{to_spec.metadata.name} requires grayscale-safe figures. "
            "Verify that all colors remain distinguishable when printed "
            "in grayscale.",
            PlotStyleWarning,
            stacklevel=3,
        )

    if to_spec.export.min_dpi > from_spec.export.min_dpi:
        warnings.warn(
            f"Minimum DPI increased: "
            f"{from_spec.export.min_dpi} → {to_spec.export.min_dpi}. "
            "Re-export the figure at the higher resolution.",
            PlotStyleWarning,
            stacklevel=3,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def diff(journal_a: str, journal_b: str) -> SpecDiff:
    """Return a structured comparison of two journal specifications.

    Evaluates every field declared in :data:`_DIFF_FIELDS` against both
    specs and collects those where the raw (pre-formatting) values differ.
    This is a pure function with no side effects.

    Args:
        journal_a: First journal preset name (e.g. ``"nature"``).
        journal_b: Second journal preset name (e.g. ``"science"``).

    Returns
    -------
        A :class:`SpecDiff` whose :attr:`~SpecDiff.differences` list
        contains one :class:`SpecDifference` per differing field.  When the
        specs are identical across all tracked fields, the list is empty and
        ``bool(result)`` is ``False``.

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If either journal name is not
            registered in the spec registry.

    Notes
    -----
        Journal names are normalised to lower-case by the registry, so
        ``"Nature"`` and ``"nature"`` are treated as equivalent inputs.

        The :attr:`~SpecDiff.journal_a` and :attr:`~SpecDiff.journal_b`
        fields in the returned object use the *display names* from the
        specs' metadata (e.g. ``"Nature"``), not the raw input strings.

    Example::

        result = plotstyle.diff("nature", "science")
        if result:
            print(result)
        data = result.to_dict()  # JSON-serialisable
    """
    spec_a: JournalSpec = registry.get(journal_a)
    spec_b: JournalSpec = registry.get(journal_b)

    # Compare raw values (before formatting) so that cosmetic string
    # differences in the formatter do not produce spurious diff entries.
    differences: list[SpecDifference] = [
        SpecDifference(
            field=dotted_path,
            label=label,
            value_a=formatter(_resolve_attr(spec_a, dotted_path)),
            value_b=formatter(_resolve_attr(spec_b, dotted_path)),
        )
        for dotted_path, label, formatter in _DIFF_FIELDS
        if _resolve_attr(spec_a, dotted_path) != _resolve_attr(spec_b, dotted_path)
    ]

    return SpecDiff(
        journal_a=spec_a.metadata.name,
        journal_b=spec_b.metadata.name,
        differences=differences,
    )


def migrate(
    fig: Figure,
    *,
    from_journal: str,
    to_journal: str,
) -> Figure:
    """Re-style a figure for a different journal.

    Applies the target journal's rcParams globally, resizes the figure to
    the target journal's single-column width (preserving the current aspect
    ratio), and proportionally rescales all text artists so font sizes remain
    within the target journal's permitted range.

    Mutates *fig* in-place and returns it to allow call chaining.

    Args:
        fig: Matplotlib figure to migrate.  Modified in-place.
        from_journal: Source journal preset name (e.g. ``"nature"``).
        to_journal: Target journal preset name (e.g. ``"science"``).

    Returns
    -------
        The same :class:`~matplotlib.figure.Figure` instance, resized and
        re-styled for *to_journal*.

    Raises
    ------
        plotstyle.specs.SpecNotFoundError: If either journal name is not
            registered in the spec registry.

    Notes
    -----
        **Font scaling** — each text artist's current size is multiplied by
        ``to_spec.max_font_pt / from_spec.max_font_pt``, then clamped to the
        target journal's ``[min_font_pt, max_font_pt]`` range.  When
        ``from_spec.max_font_pt`` is zero (a degenerate spec), the scale
        factor defaults to ``1.0`` to avoid division by zero.

        **Warnings** — a :class:`~plotstyle._utils.warnings.PlotStyleWarning`
        is emitted for each of the following significant changes:

        - The font family differs between source and target journals.
        - The target journal requires grayscale-safe figures and the source
          did not.
        - The target journal requires a higher minimum export DPI.

        **rcParams scope** — this function calls ``mpl.rcParams.update``
        with the target journal's full rcParams dict and does *not* restore
        the previous state on return.  Wrap the call in a
        :func:`~plotstyle.core.style.use` context manager if you need the
        global state restored afterwards.

    Example::

        import plotstyle
        import matplotlib.pyplot as plt

        with plotstyle.use("nature"):
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3])

        # Migrate the figure to Science column widths and typography.
        plotstyle.migrate(fig, from_journal="nature", to_journal="science")
        plotstyle.savefig(fig, "figure.pdf", journal="science")
    """
    from_spec: JournalSpec = registry.get(from_journal)
    to_spec: JournalSpec = registry.get(to_journal)

    # Apply the target journal's full rcParams before resizing or rescaling
    # so that any subsequent Matplotlib drawing operations inherit the correct
    # style immediately.
    mpl.rcParams.update(build_rcparams(to_spec))

    # ── Figure resize ──────────────────────────────────────────────────────
    # Compute the new width from the target spec and derive the new height by
    # preserving the current aspect ratio.  Guard against a zero-width figure
    # (a degenerate state) by defaulting the ratio to 1.0.
    old_w, old_h = fig.get_size_inches()
    aspect_ratio: float = old_h / old_w if old_w else 1.0
    new_w: float = Dimension(to_spec.dimensions.single_column_mm, "mm").to_inches()
    fig.set_size_inches(new_w, new_w * aspect_ratio)

    # ── Font rescaling ─────────────────────────────────────────────────────
    # Scale all text artists proportionally to the change in max font size
    # between the two journals, then clamp each artist into the target range.
    # Using max_font_pt as the scale reference preserves relative text
    # hierarchy (titles, labels, ticks) better than a flat offset would.
    font_scale: float = (
        to_spec.typography.max_font_pt / from_spec.typography.max_font_pt
        if from_spec.typography.max_font_pt
        else 1.0
    )

    _rescale_text_artists(
        fig,
        scale=font_scale,
        min_pt=to_spec.typography.min_font_pt,
        max_pt=to_spec.typography.max_font_pt,
    )

    # ── Migration warnings ─────────────────────────────────────────────────
    # Emit warnings for changes that require explicit author action and cannot
    # be corrected programmatically (color safety, resolution, font choice).
    _emit_migration_warnings(from_spec, to_spec)

    return fig
