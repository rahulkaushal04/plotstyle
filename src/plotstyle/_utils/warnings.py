"""Warning hierarchy for PlotStyle.

All warnings emitted by PlotStyle derive from :class:`PlotStyleWarning`, which
itself subclasses the built-in :class:`UserWarning`.  This two-level hierarchy
lets users selectively filter or silence PlotStyle-specific warnings without
affecting unrelated user warnings from other packages:

.. code-block:: python

    import warnings
    from plotstyle._utils.warnings import PlotStyleWarning

    # Silence all PlotStyle warnings at once.
    warnings.filterwarnings("ignore", category=PlotStyleWarning)

    # Or silence only a specific sub-class.
    from plotstyle._utils.warnings import FontFallbackWarning

    warnings.filterwarnings("ignore", category=FontFallbackWarning)

Warning classes
---------------
.. autosummary::

    PlotStyleWarning
    FontFallbackWarning

Design notes
------------
- All warning classes are intentionally kept as thin stubs.  They carry no
  data attributes beyond the message string inherited from :class:`Warning`.
  If structured warning data is ever needed, add it as constructor arguments
  on the specific subclass rather than on the base class.
- ``pass`` is omitted from class bodies by convention (a docstring is
  sufficient to make the body non-empty), improving readability in IDEs and
  documentation renderers.
- Inheriting from :class:`UserWarning` (via :class:`PlotStyleWarning`) ensures
  that ``warnings.warn(..., stacklevel=2)`` displays the caller's frame, not
  the internals of PlotStyle, in the warning message.
"""

from __future__ import annotations


class PlotStyleWarning(UserWarning):
    """Base class for all PlotStyle warnings.

    Subclass :class:`UserWarning` so that PlotStyle warnings are visible by
    default (Python does not suppress ``UserWarning`` the way it suppresses
    :class:`DeprecationWarning`), while still being filterable as a group.

    All other PlotStyle warning classes inherit from this class.  To silence
    every warning from PlotStyle in one call, filter on this base class:

    .. code-block:: python

        import warnings

        warnings.filterwarnings("ignore", category=PlotStyleWarning)

    Example:
        >>> import warnings
        >>> from plotstyle._utils.warnings import PlotStyleWarning
        >>> warnings.warn("example", PlotStyleWarning, stacklevel=2)
    """


class FontFallbackWarning(PlotStyleWarning):
    """Raised when a preferred font is unavailable and a fallback is used.

    PlotStyle attempts to activate journal-specific fonts (e.g., Helvetica
    Neue for Nature, Times New Roman for IEEE).  When the requested font is
    not installed on the system, Matplotlib falls back to its default font
    family.  This warning is emitted in that situation so that authors are
    aware the rendered figure may not match the journal's typographic
    requirements.

    Example:
        >>> import warnings
        >>> from plotstyle._utils.warnings import FontFallbackWarning
        >>> warnings.warn(
        ...     "Font 'Helvetica Neue' not found; falling back to 'DejaVu Sans'.",
        ...     FontFallbackWarning,
        ...     stacklevel=2,
        ... )
    """
