"""Journal comparison and figure migration utilities.

``diff`` compares two journal specs and returns a :class:`SpecDiff`.
``migrate`` re-styles an existing figure for a different journal in-place.
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


def _format_list(value: object) -> str:
    """Return a comma-separated string for lists, or ``str(value)`` otherwise."""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _format_mm(value: object) -> str:
    """Return ``"<value>mm"``."""
    return f"{value}mm"


def _format_pt(value: object) -> str:
    """Return ``"<value>pt"``."""
    return f"{value}pt"


def _format_bool(value: object) -> str:
    """Return ``"Yes"`` or ``"No"``."""
    return "Yes" if value else "No"


def _resolve_attr(obj: object, dotted_path: str) -> object:
    """Resolve a dotted attribute path on a nested object (e.g. ``"typography.font_family"``)."""
    for part in dotted_path.split("."):
        obj = getattr(obj, part)
    return obj


# ---------------------------------------------------------------------------
# Diff field manifest
# ---------------------------------------------------------------------------

# (dotted_path, human_label, formatter) — append here to track new fields.
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

_SEPARATOR_WIDTH: Final[int] = 50

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SpecDifference:
    """Immutable record of a single parameter difference between two specs.

    Attributes
    ----------
    field : str
        Dotted attribute path on :class:`~plotstyle.specs.schema.JournalSpec`
        (e.g. ``"dimensions.single_column_mm"``).
    label : str
        Human-readable description of the field (e.g. ``"Column Width (single)"``).
    value_a : str
        Formatted string value from the first journal spec.
    value_b : str
        Formatted string value from the second journal spec.
    """

    field: str
    label: str
    value_a: str
    value_b: str


@dataclass(slots=True)
class SpecDiff:
    """Complete, structured comparison between two journal specifications.

    Returned by :func:`diff`.  Provides three access patterns:

    - **Human-readable** — pass the instance to :class:`str` or :func:`print`
      to get an aligned two-column table.
    - **Programmatic** — iterate over :attr:`differences`, test ``len()``, or
      use the instance directly in a boolean context (falsy when identical).
    - **Machine-readable** — call :meth:`to_dict` and serialise with
      :mod:`json`.

    Attributes
    ----------
    journal_a : str
        Display name of the first journal (from spec metadata).
    journal_b : str
        Display name of the second journal (from spec metadata).
    differences : list
        Ordered list of :class:`SpecDifference` records for each
        field where the two specs disagree.  Empty when the specs are
        identical across all tracked fields.

    Examples
    --------
    ::

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
        """Render the diff as a human-readable aligned table."""
        header = f"{self.journal_a} → {self.journal_b}"

        if not self.differences:
            return f"{header}\nNo differences."

        max_label_len = max(len(d.label) for d in self.differences)
        separator = "─" * _SEPARATOR_WIDTH

        rows = [
            f"{d.label + ':':<{max_label_len + 1}}  {d.value_a} → {d.value_b}"
            for d in self.differences
        ]

        return "\n".join([header, separator, *rows])

    def to_dict(self) -> dict[str, Any]:
        """Serialise the diff to a JSON-serialisable plain dictionary."""
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
    """Scale all Text artists in *fig* by *scale* and clamp to ``[min_pt, max_pt]``.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure whose Text artists are modified in-place.
    scale : float
        Multiplicative scaling factor applied to each artist's current
        font size.
    min_pt : float
        Lower bound for the resulting font size in points.
    max_pt : float
        Upper bound for the resulting font size in points.
    """
    for text_artist in fig.findobj(mpl.text.Text):
        raw_size = text_artist.get_fontsize()
        clamped = max(min_pt, min(max_pt, raw_size * scale))
        text_artist.set_fontsize(clamped)


def _emit_migration_warnings(
    from_spec: JournalSpec,
    to_spec: JournalSpec,
) -> None:
    """Emit :class:`~plotstyle._utils.warnings.PlotStyleWarning` for font, grayscale, and DPI changes.

    Parameters
    ----------
    from_spec : JournalSpec
        Source journal specification before migration.
    to_spec : JournalSpec
        Target journal specification after migration.
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

    Parameters
    ----------
    journal_a : str
        First journal preset name (e.g. ``"nature"``).
    journal_b : str
        Second journal preset name (e.g. ``"science"``).

    Returns
    -------
    SpecDiff
        A :class:`SpecDiff` with one :class:`SpecDifference` per differing
        field.  Empty (falsy) when the specs are identical.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If either journal is not registered.
    """
    spec_a = registry.get(journal_a)
    spec_b = registry.get(journal_b)

    differences = [
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
    """Re-style *fig* in-place for *to_journal* and return it.

    Applies the target journal's rcParams globally, resizes to its
    single-column width (preserving aspect ratio), and proportionally
    rescales all text artists to fit within the target's font-size range.

    Parameters
    ----------
    fig : Figure
        Matplotlib figure to migrate.  Modified in-place.
    from_journal : str
        Source journal preset name (e.g. ``"nature"``).
    to_journal : str
        Target journal preset name (e.g. ``"science"``).

    Returns
    -------
    Figure
        The same figure instance after restyling.

    Raises
    ------
    plotstyle.specs.SpecNotFoundError
        If either journal is not registered.

    Notes
    -----
    The target journal's rcParams are applied for the duration of this call
    and restored unconditionally before return.  Global Matplotlib state is
    unchanged after ``migrate()`` returns.

    Examples
    --------
    ::

        import numpy as np
        import plotstyle

        with plotstyle.use("nature") as style:
            fig, ax = style.figure()
            x = np.linspace(0, 10, 100)
            ax.plot(x, np.sin(x))

        plotstyle.migrate(fig, from_journal="nature", to_journal="science")
        plotstyle.savefig(fig, "figure_science.pdf", journal="science")
    """
    from_spec = registry.get(from_journal)
    to_spec = registry.get(to_journal)

    target_rc = build_rcparams(to_spec)
    saved_rc = {k: mpl.rcParams[k] for k in target_rc if k in mpl.rcParams}
    try:
        mpl.rcParams.update(target_rc)

        old_w, old_h = fig.get_size_inches()
        aspect_ratio = old_h / old_w if old_w else 1.0
        new_w = Dimension(to_spec.dimensions.single_column_mm, "mm").to_inches()
        fig.set_size_inches(new_w, new_w * aspect_ratio)

        font_scale = (
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

        _emit_migration_warnings(from_spec, to_spec)

    finally:
        mpl.rcParams.update(saved_rc)

    return fig
