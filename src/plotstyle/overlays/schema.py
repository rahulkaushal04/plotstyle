"""StyleOverlay dataclass: a named, flat rcParam patch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

__all__: list[str] = ["StyleOverlay"]

_VALID_CATEGORIES: Final[frozenset[str]] = frozenset(
    {"color", "context", "rendering", "script", "plot-type"}
)


@dataclass(frozen=True, slots=True)
class StyleOverlay:
    """A named overlay that patches a flat set of rcParams.

    Overlay instances are immutable.  They are loaded from TOML files by
    :class:`~plotstyle.overlays.OverlayRegistry` and applied on top of a
    journal spec's base rcParams by ``apply_overlays``.

    Attributes
    ----------
    key : str
        Lower-case registry identifier (matches the TOML file stem).
    name : str
        Human-readable display name.
    category : str
        Functional category.  Must be one of ``"color"``, ``"context"``,
        ``"rendering"``, ``"script"``, or ``"plot-type"``.
    description : str
        One-sentence description of what the overlay does.
    rcparams : dict[str, Any]
        Flat mapping of ``matplotlib.rcParams`` keys to new values.

        **Special key ``_palette``**: a list of hex colour strings.
        ``apply_overlays`` converts this to a
        ``cycler('color', ...)`` object stored under ``axes.prop_cycle``.
        Use this convention in TOML files because TOML has no native type for
        matplotlib's ``cycler`` objects.
    rendering : dict[str, Any] | None
        Optional rendering directives parsed from the ``[rendering]`` TOML
        section.  Supported keys:

        - ``latex``: ``false`` / ``true`` / ``"pgf"``: the LaTeX mode to
          activate.  ``"pgf"`` enables the PGF backend in addition to LaTeX.
        - ``font_family``: ``"sans-serif"`` / ``"serif"`` / ``"monospace"``:
          overrides the font family used for LaTeX rendering.

        ``None`` when the TOML file has no ``[rendering]`` section.
    script : dict[str, Any] | None
        Optional script-specific directives parsed from the ``[script]`` TOML
        section.  Supported keys:

        - ``latex_preamble``: list of LaTeX preamble lines to append to
          ``text.latex.preamble`` when LaTeX rendering is active.

        ``None`` when the TOML file has no ``[script]`` section.
    requires : dict[str, Any] | None
        Optional font requirements parsed from the ``[requires]`` TOML section.
        Supported keys:

        - ``fonts``: list of font family names that this overlay needs.  Used by
          :func:`~plotstyle.engine.fonts.check_overlay_fonts` and the CLI
          ``fonts --overlay`` sub-command.

        ``None`` when the TOML file has no ``[requires]`` section.
    """

    key: str
    name: str
    category: str
    description: str
    rcparams: dict[str, Any]
    rendering: dict[str, Any] | None = None
    script: dict[str, Any] | None = None
    requires: dict[str, Any] | None = None

    @classmethod
    def from_toml(cls, data: dict[str, Any], key: str) -> StyleOverlay:
        """Parse a TOML dict with ``[metadata]`` and ``[rcparams]`` sections.

        Parameters
        ----------
        data : dict[str, Any]
            Raw parsed TOML content.
        key : str
            Lower-case registry identifier assigned by the caller.

        Returns
        -------
        StyleOverlay

        Raises
        ------
        ValueError
            If ``metadata.category`` is not a recognised value.
        """
        meta = data.get("metadata", {})
        name = str(meta.get("name", key))
        category = str(meta.get("category", ""))
        description = str(meta.get("description", ""))

        if category not in _VALID_CATEGORIES:
            raise ValueError(
                f"[metadata.category] Expected one of "
                f"{sorted(_VALID_CATEGORIES)}, got {category!r}."
            )

        rcparams = dict(data.get("rcparams", {}))
        rendering = dict(data["rendering"]) if "rendering" in data else None
        script = dict(data["script"]) if "script" in data else None
        requires = dict(data["requires"]) if "requires" in data else None

        return cls(
            key=key,
            name=name,
            category=category,
            description=description,
            rcparams=rcparams,
            rendering=rendering,
            script=script,
            requires=requires,
        )
