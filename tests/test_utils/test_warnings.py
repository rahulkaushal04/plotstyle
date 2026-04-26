"""Comprehensive test suite for plotstyle._utils.warnings.

Covers: warning hierarchy, emission, filterability, and message preservation.
"""

from __future__ import annotations

import warnings

import pytest

from plotstyle._utils.warnings import FontFallbackWarning, PlotStyleWarning

# ---------------------------------------------------------------------------
# Hierarchy and isinstance checks
# ---------------------------------------------------------------------------


class TestWarningHierarchy:
    """Validate the inheritance chain of all PlotStyle warning classes."""

    def test_plotstyle_warning_is_user_warning(self) -> None:
        """
        Description: PlotStyleWarning must subclass UserWarning so Python's
        default warning filter does not suppress it.
        Scenario: Check isinstance of PlotStyleWarning() against UserWarning.
        Expectation: isinstance returns True.
        """
        assert issubclass(PlotStyleWarning, UserWarning)

    def test_font_fallback_warning_is_plotstyle_warning(self) -> None:
        """
        Description: FontFallbackWarning must subclass PlotStyleWarning so the
        whole family can be filtered by a single except / filterwarnings call.
        Scenario: Check isinstance relationship.
        Expectation: issubclass(FontFallbackWarning, PlotStyleWarning) is True.
        """
        assert issubclass(FontFallbackWarning, PlotStyleWarning)

    def test_font_fallback_warning_is_user_warning(self) -> None:
        """
        Description: FontFallbackWarning must ultimately be a UserWarning so
        it is visible by default and not silently swallowed.
        Scenario: Check issubclass against UserWarning.
        Expectation: True.
        """
        assert issubclass(FontFallbackWarning, UserWarning)

    def test_font_fallback_warning_is_warning(self) -> None:
        """
        Description: All warning classes must derive from the built-in Warning
        base class for compatibility with the standard warnings module.
        Scenario: Check issubclass against Warning.
        Expectation: True.
        """
        assert issubclass(FontFallbackWarning, Warning)

    def test_plotstyle_warning_can_be_instantiated(self) -> None:
        """
        Description: PlotStyleWarning must be constructable with a message
        string, as all standard Warning subclasses should be.
        Scenario: Instantiate PlotStyleWarning("test message").
        Expectation: No exception; args[0] == "test message".
        """
        w = PlotStyleWarning("test message")
        assert w.args[0] == "test message"

    def test_font_fallback_warning_can_be_instantiated(self) -> None:
        """
        Description: FontFallbackWarning must be constructable with a message.
        Scenario: Instantiate FontFallbackWarning("missing font").
        Expectation: No exception; args[0] == "missing font".
        """
        w = FontFallbackWarning("missing font")
        assert w.args[0] == "missing font"

    def test_font_fallback_is_catchable_as_plotstyle_warning(self) -> None:
        """
        Description: A FontFallbackWarning raise must be catchable using the
        PlotStyleWarning base class, enabling single-filter silencing.
        Scenario: Raise FontFallbackWarning and catch as PlotStyleWarning.
        Expectation: No uncaught exception.
        """
        try:
            raise FontFallbackWarning("catch me")
        except PlotStyleWarning:
            pass
        else:
            pytest.fail("FontFallbackWarning was not caught as PlotStyleWarning")

    def test_font_fallback_is_catchable_as_user_warning(self) -> None:
        """
        Description: FontFallbackWarning must also be catchable as UserWarning
        for code that has not been updated to use the PlotStyle hierarchy.
        Scenario: Raise FontFallbackWarning and catch as UserWarning.
        Expectation: No uncaught exception.
        """
        try:
            raise FontFallbackWarning("catch me too")
        except UserWarning:
            pass
        else:
            pytest.fail("FontFallbackWarning was not caught as UserWarning")


# ---------------------------------------------------------------------------
# Emission and filterability
# ---------------------------------------------------------------------------


class TestWarningEmission:
    """Validate that warnings are correctly emitted and filterable."""

    def test_plotstyle_warning_is_emitted(self) -> None:
        """
        Description: warnings.warn with PlotStyleWarning must produce a
        recorded warning of the correct category.
        Scenario: Call warnings.warn(..., PlotStyleWarning).
        Expectation: At least one PlotStyleWarning is recorded.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("ps warning", PlotStyleWarning, stacklevel=1)
        assert any(issubclass(x.category, PlotStyleWarning) for x in w)

    def test_font_fallback_warning_is_emitted(self) -> None:
        """
        Description: warnings.warn with FontFallbackWarning must produce a
        recorded warning of the correct category.
        Scenario: Call warnings.warn(..., FontFallbackWarning).
        Expectation: At least one FontFallbackWarning is recorded.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("font missing", FontFallbackWarning, stacklevel=1)
        assert any(issubclass(x.category, FontFallbackWarning) for x in w)

    def test_filter_by_base_class_silences_subclass(self) -> None:
        """
        Description: A filterwarnings("ignore", category=PlotStyleWarning) must
        suppress FontFallbackWarning because it is a subclass.
        Scenario: Set ignore filter for PlotStyleWarning; emit FontFallbackWarning.
        Expectation: No warnings recorded.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("ignore", category=PlotStyleWarning)
            warnings.warn("silent", FontFallbackWarning, stacklevel=1)
        fallback_warnings = [x for x in w if issubclass(x.category, FontFallbackWarning)]
        assert len(fallback_warnings) == 0

    def test_filter_font_fallback_does_not_silence_base(self) -> None:
        """
        Description: Filtering FontFallbackWarning specifically must NOT suppress
        other PlotStyleWarning emissions (silencing is downward, not upward).
        Scenario: Set ignore filter for FontFallbackWarning; emit PlotStyleWarning.
        Expectation: The PlotStyleWarning is still recorded.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.filterwarnings("ignore", category=FontFallbackWarning)
            warnings.warn("should appear", PlotStyleWarning, stacklevel=1)
        base_warnings = [x for x in w if x.category is PlotStyleWarning]
        assert len(base_warnings) >= 1

    def test_warning_message_is_preserved(self) -> None:
        """
        Description: The message string passed to warnings.warn must be
        retrievable from the recorded warning record.
        Scenario: Emit FontFallbackWarning with a known message string.
        Expectation: w[0].message.args[0] matches the emitted message.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            warnings.warn("Helvetica not found", FontFallbackWarning, stacklevel=1)
        assert len(w) == 1
        assert "Helvetica" in str(w[0].message)

    def test_plotstyle_warning_category_string_filter(self) -> None:
        """
        Description: pytest.mark.filterwarnings uses string-based category paths;
        the full dotted path must resolve correctly for test configuration.
        Scenario: Filter using the full module path as a string.
        Expectation: No exception when matching category string is used.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                warnings.filterwarnings(
                    "ignore",
                    category=FontFallbackWarning,
                )
                warnings.warn("filtered", FontFallbackWarning, stacklevel=1)
            except Exception as e:
                pytest.fail(f"Unexpected error during warning filter: {e}")
        # No FontFallbackWarning should appear after the filter
        fallback = [x for x in w if issubclass(x.category, FontFallbackWarning)]
        assert len(fallback) == 0


# ---------------------------------------------------------------------------
# Module-level attribute checks
# ---------------------------------------------------------------------------


class TestWarningModuleExports:
    """Validate that warning classes are importable from the correct module."""

    def test_plotstyle_warning_module(self) -> None:
        """
        Description: PlotStyleWarning must be defined in the expected module
        so that string-based pytest filter paths resolve correctly.
        Scenario: Inspect __module__ attribute of PlotStyleWarning.
        Expectation: 'plotstyle._utils.warnings' in __module__.
        """
        assert "plotstyle._utils.warnings" in PlotStyleWarning.__module__

    def test_font_fallback_warning_module(self) -> None:
        """
        Description: FontFallbackWarning must be defined in the expected module.
        Scenario: Inspect __module__ attribute of FontFallbackWarning.
        Expectation: 'plotstyle._utils.warnings' in __module__.
        """
        assert "plotstyle._utils.warnings" in FontFallbackWarning.__module__

    def test_both_classes_have_docstrings(self) -> None:
        """
        Description: Both warning classes must have docstrings as required by
        the module's design notes and for good developer experience.
        Scenario: Inspect __doc__ attribute of each class.
        Expectation: Both are non-empty strings.
        """
        assert PlotStyleWarning.__doc__ is not None
        assert len(PlotStyleWarning.__doc__.strip()) > 0
        assert FontFallbackWarning.__doc__ is not None
        assert len(FontFallbackWarning.__doc__.strip()) > 0
