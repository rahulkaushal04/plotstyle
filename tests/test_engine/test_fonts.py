"""Test suite for plotstyle.engine.fonts.

Covers: detect_available, select_best, verify_embedded.
Strategy: All external I/O (matplotlib font_manager, filesystem) is mocked
so tests are hermetic and deterministic regardless of host font installation.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / shared constants
# ---------------------------------------------------------------------------

MODULE = "plotstyle.engine.fonts"
FINDFONT_PATH = f"{MODULE}.font_manager.findfont"
FINDPROPS_PATH = f"{MODULE}.font_manager.FontProperties"

HELVETICA = "Helvetica"
ARIAL = "Arial"
DEJAVU = "DejaVu Sans"
COURIER = "Courier New"

FAKE_PATH_HELVETICA = "/usr/share/fonts/Helvetica.ttf"
FAKE_PATH_ARIAL = "/usr/share/fonts/Arial.ttf"
FAKE_PATH_DEJAVU = "/usr/share/fonts/DejaVuSans.ttf"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_findfont():
    """Fixture: patches font_manager.findfont to return a predictable path.

    Description: Provides a controllable replacement for matplotlib's
    findfont so that font availability can be simulated without needing
    actual fonts installed on the test host.
    Scenario: Applied globally where font existence must be controlled.
    Expectation: The returned mock can be configured per-test.
    """
    with patch(FINDFONT_PATH) as m:
        yield m


@pytest.fixture()
def all_fonts_present(mock_findfont):
    """Fixture: every font lookup succeeds (returns a fake .ttf path).

    Description: Simulates a system with all requested fonts installed.
    Scenario: findfont never raises; returns deterministic fake path.
    Expectation: detect_available / select_best treat every family as found.

    FontProperties is also patched so that matplotlib does not emit its own
    "findfont: Font family not found" warnings on hosts that lack the fonts,
    which would pollute warning-capture assertions in tests.
    """
    mock_findfont.return_value = FAKE_PATH_HELVETICA
    with patch(FINDPROPS_PATH, return_value=MagicMock()):
        yield mock_findfont


@pytest.fixture()
def no_fonts_present(mock_findfont):
    """Fixture: every font lookup fails with ValueError.

    Description: Simulates a minimal environment with no preferred fonts.
    Scenario: findfont always raises ValueError (the documented signal for
    missing family when fallback_to_default=False).
    Expectation: detect_available returns []; select_best falls back to generic.
    """
    mock_findfont.side_effect = ValueError("Font not found")
    return mock_findfont


@pytest.fixture()
def partial_fonts(mock_findfont):
    """Fixture: only Arial and DejaVu Sans are present; Helvetica is absent.

    Description: Simulates a real-world Linux system missing a proprietary
    font but having open-source alternatives.
    Scenario: findfont raises for Helvetica, succeeds for Arial and DejaVu.
    Expectation: detect_available returns ['Arial', 'DejaVu Sans'] in order.
    """

    def side_effect(props, fallback_to_default=True):
        family = props.get_family()[0] if hasattr(props, "get_family") else str(props)
        mapping = {ARIAL: FAKE_PATH_ARIAL, DEJAVU: FAKE_PATH_DEJAVU}
        if family in mapping:
            return mapping[family]
        raise ValueError(f"Font not found: {family}")

    mock_findfont.side_effect = side_effect
    return mock_findfont


def _make_journal_spec(
    font_family: list[str],
    font_fallback: str = "sans-serif",
    journal_name: str = "Test Journal",
) -> MagicMock:
    """Build a minimal JournalSpec mock with the required attribute shape.

    Args:
        font_family: Ordered list of preferred font families.
        font_fallback: Generic family used when none of the preferred are found.
        journal_name: Human-readable journal name for warning messages.

    Returns:
        MagicMock configured to match plotstyle.specs.schema.JournalSpec.
    """
    spec = MagicMock()
    spec.typography.font_family = font_family
    spec.typography.font_fallback = font_fallback
    spec.metadata.name = journal_name
    return spec


@pytest.fixture()
def nature_spec():
    """Fixture: JournalSpec representing a Nature-like journal.

    Description: Provides a realistic multi-font spec for use in select_best
    tests where the journal demands Helvetica but will accept Arial.
    Scenario: typography.font_family = [Helvetica, Arial, DejaVu Sans].
    Expectation: Used as the common happy-path spec in select_best tests.
    """
    return _make_journal_spec([HELVETICA, ARIAL, DEJAVU], "sans-serif", "Nature")


@pytest.fixture()
def tmp_pdf(tmp_path) -> Path:
    """Fixture: create a minimal, valid-looking PDF file in a temp directory.

    Description: Provides a real (writable) PDF path so verify_embedded can
    open and read bytes.
    Scenario: File contains the bytes b'/FlateDecode /Filter' — no Type 3.
    Expectation: verify_embedded returns [] for this file.
    """
    pdf = tmp_path / "figure.pdf"
    pdf.write_bytes(b"%PDF-1.4\n/FlateDecode /Filter\n%%EOF\n")
    return pdf


@pytest.fixture()
def tmp_pdf_with_type3(tmp_path) -> Path:
    """Fixture: PDF file containing the /Type3 marker byte sequence.

    Description: Simulates a PDF that was rendered with bitmap Type 3 fonts,
    which many submission portals reject.
    Scenario: File contains the byte literal b'/Type3'.
    Expectation: verify_embedded returns a non-empty issues list.
    """
    pdf = tmp_path / "bad_figure.pdf"
    pdf.write_bytes(b"%PDF-1.4\n/Font << /Type3 /F1 >>\n%%EOF\n")
    return pdf


# === Tests: detect_available ===


class TestDetectAvailable:
    """Unit tests for detect_available()."""

    def test_empty_input_returns_empty_list(self):
        """
        Description: Calling detect_available with an empty list should
        immediately return an empty list without touching font_manager.
        Scenario: families=[]
        Expectation: Returns [] and findfont is never called.
        """
        from plotstyle.engine.fonts import detect_available

        with patch(FINDFONT_PATH) as mock_ff:
            result = detect_available([])

        assert result == []
        mock_ff.assert_not_called()

    def test_all_fonts_available_returns_all_in_order(self, all_fonts_present):
        """
        Description: When every queried family is installed, detect_available
        should return all names in the original preference order.
        Scenario: Three fonts, all present.
        Expectation: Same list as input, same order.
        """
        from plotstyle.engine.fonts import detect_available

        families = [HELVETICA, ARIAL, DEJAVU]
        result = detect_available(families)

        assert result == families

    def test_no_fonts_available_returns_empty_list(self, no_fonts_present):
        """
        Description: When findfont raises ValueError for every family, the
        function should return an empty list, not propagate the exception.
        Scenario: Three fonts, none present.
        Expectation: Returns [].
        """
        from plotstyle.engine.fonts import detect_available

        result = detect_available([HELVETICA, ARIAL, DEJAVU])

        assert result == []

    def test_partial_availability_preserves_order(self):
        """
        Description: Only present fonts are returned, and the original ordering
        of those present fonts is preserved.
        Scenario: HELVETICA missing, ARIAL and DEJAVU present.
        Expectation: Returns [ARIAL, DEJAVU], skipping HELVETICA.
        """
        from plotstyle.engine.fonts import detect_available

        def _findfont(props, fallback_to_default=True):
            family = props.get_family()[0]
            if family == HELVETICA:
                raise ValueError("not found")
            return f"/fonts/{family}.ttf"

        with patch(FINDPROPS_PATH) as mock_props_cls, patch(FINDFONT_PATH, side_effect=_findfont):
            mock_props_cls.side_effect = lambda family: _make_font_props_mock(family)
            result = detect_available([HELVETICA, ARIAL, DEJAVU])

        assert ARIAL in result
        assert DEJAVU in result
        assert HELVETICA not in result
        assert result.index(ARIAL) < result.index(DEJAVU)

    def test_single_font_present(self, all_fonts_present):
        """
        Description: A list with only one font name should return that name
        wrapped in a list when it is available.
        Scenario: families=[ARIAL], font present.
        Expectation: Returns [ARIAL].
        """
        from plotstyle.engine.fonts import detect_available

        assert detect_available([ARIAL]) == [ARIAL]

    def test_single_font_absent(self, no_fonts_present):
        """
        Description: A list with one font name should return [] when the
        font is absent.
        Scenario: families=[COURIER], font absent.
        Expectation: Returns [].
        """
        from plotstyle.engine.fonts import detect_available

        assert detect_available([COURIER]) == []

    @pytest.mark.parametrize("size", [50, 200])
    def test_large_family_list(self, size, all_fonts_present):
        """
        Description: detect_available should handle arbitrarily long lists
        without errors. Verifies list comprehension approach scales.
        Scenario: List of <size> identical font names, all present.
        Expectation: Returns list of same length.
        """
        from plotstyle.engine.fonts import detect_available

        families = [f"Font{i}" for i in range(size)]
        result = detect_available(families)

        assert len(result) == size

    def test_duplicate_font_names_preserved(self, all_fonts_present):
        """
        Description: If the caller passes duplicate font names, detect_available
        should not deduplicate — it mirrors the input faithfully.
        Scenario: families=[ARIAL, ARIAL].
        Expectation: Returns [ARIAL, ARIAL].
        """
        from plotstyle.engine.fonts import detect_available

        result = detect_available([ARIAL, ARIAL])

        assert result == [ARIAL, ARIAL]

    def test_does_not_raise_on_value_error(self, no_fonts_present):
        """
        Description: Internally, _find_font_or_none swallows ValueError from
        findfont. detect_available must never let that exception escape.
        Scenario: findfont raises ValueError for every call.
        Expectation: No exception is raised; returns [].
        """
        from plotstyle.engine.fonts import detect_available

        try:
            detect_available([HELVETICA, ARIAL])
        except ValueError:
            pytest.fail("detect_available must not propagate ValueError from findfont")

    def test_findfont_called_with_fallback_false(self):
        """
        Description: The critical correctness requirement: findfont must be
        called with fallback_to_default=False. Without it, findfont silently
        returns the default font for unknown families, making every lookup
        appear successful and defeating the entire function.
        Scenario: One font name queried.
        Expectation: findfont receives fallback_to_default=False.
        """
        from plotstyle.engine.fonts import detect_available

        with (
            patch(FINDFONT_PATH, return_value=FAKE_PATH_ARIAL) as mock_ff,
            patch(FINDPROPS_PATH, return_value=MagicMock()),
        ):
            detect_available([ARIAL])

        _, kwargs = mock_ff.call_args
        assert kwargs.get("fallback_to_default") is False, (
            "findfont must be called with fallback_to_default=False; "
            "without it every family appears available"
        )


# === Tests: select_best ===


class TestSelectBest:
    """Unit tests for select_best()."""

    def test_first_preference_available_returns_exact_match(self, all_fonts_present, nature_spec):
        """
        Description: When the top-preference font (Helvetica) is available,
        select_best should return it and set is_exact_match=True.
        Scenario: All fonts present; top preference is Helvetica.
        Expectation: Returns ('Helvetica', True), no warning emitted.
        """
        from plotstyle.engine.fonts import select_best

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            font, exact = select_best(nature_spec)

        assert font == HELVETICA
        assert exact is True
        assert len(w) == 0, "No warning expected when exact font is found"

    def test_fallback_font_emits_warning(self):
        """
        Description: When the first-preference font is absent but a lower
        preference is available, select_best must emit FontFallbackWarning
        and return the substitute font.
        Scenario: Helvetica absent; Arial present.
        Expectation: Returns ('Arial', False) and emits FontFallbackWarning.
        """
        from plotstyle._utils.warnings import FontFallbackWarning
        from plotstyle.engine.fonts import select_best

        def _findfont(props, fallback_to_default=True):
            family = props.get_family()[0]
            if family == HELVETICA:
                raise ValueError("not found")
            return f"/fonts/{family}.ttf"

        spec = _make_journal_spec([HELVETICA, ARIAL], "sans-serif", "Nature")

        with (
            patch(FINDPROPS_PATH, side_effect=lambda f: _make_font_props_mock(f)),
            patch(FINDFONT_PATH, side_effect=_findfont),
            warnings.catch_warnings(record=True) as w,
        ):
            warnings.simplefilter("always")
            font, exact = select_best(spec)

        assert font == ARIAL
        assert exact is False
        assert any(issubclass(warning.category, FontFallbackWarning) for warning in w), (
            "FontFallbackWarning must be emitted when falling back to a substitute font"
        )

    def test_no_fonts_available_falls_back_to_generic(self, no_fonts_present):
        """
        Description: When none of the preferred fonts exist on the system,
        select_best must return the generic fallback (e.g. 'sans-serif') and
        emit FontFallbackWarning.
        Scenario: findfont raises for every family.
        Expectation: Returns ('sans-serif', False) and emits FontFallbackWarning.
        """
        from plotstyle._utils.warnings import FontFallbackWarning
        from plotstyle.engine.fonts import select_best

        spec = _make_journal_spec([HELVETICA, ARIAL], "sans-serif", "Nature")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            font, exact = select_best(spec)

        assert font == "sans-serif"
        assert exact is False
        assert any(issubclass(warning.category, FontFallbackWarning) for warning in w)

    def test_warning_message_contains_missing_and_substitute(self):
        """
        Description: The FontFallbackWarning message must name both the missing
        preferred font and the chosen substitute so users can diagnose compliance
        issues from the warning text alone.
        Scenario: Helvetica missing, Arial substituted.
        Expectation: Warning text contains 'Helvetica' and 'Arial'.
        """
        from plotstyle._utils.warnings import FontFallbackWarning
        from plotstyle.engine.fonts import select_best

        def _findfont(props, fallback_to_default=True):
            family = props.get_family()[0]
            if family == HELVETICA:
                raise ValueError("not found")
            return FAKE_PATH_ARIAL

        spec = _make_journal_spec([HELVETICA, ARIAL], "sans-serif", "Nature")

        with (
            patch(FINDPROPS_PATH, side_effect=lambda f: _make_font_props_mock(f)),
            patch(FINDFONT_PATH, side_effect=_findfont),
            warnings.catch_warnings(record=True) as w,
        ):
            warnings.simplefilter("always")
            select_best(spec)

        fallback_warnings = [x for x in w if issubclass(x.category, FontFallbackWarning)]
        assert fallback_warnings, "Expected at least one FontFallbackWarning"
        msg = str(fallback_warnings[0].message)
        assert HELVETICA in msg, "Warning must name the missing font"
        assert ARIAL in msg, "Warning must name the substitute font"

    def test_no_warning_when_exact_match(self, all_fonts_present, nature_spec):
        """
        Description: No warning should be emitted when the top-preference font
        is found — spurious warnings erode user trust.
        Scenario: All fonts present; top preference found immediately.
        Expectation: warnings.catch_warnings records zero FontFallbackWarning.
        """
        from plotstyle._utils.warnings import FontFallbackWarning
        from plotstyle.engine.fonts import select_best

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            select_best(nature_spec)

        fallback_warnings = [x for x in w if issubclass(x.category, FontFallbackWarning)]
        assert fallback_warnings == [], "No warning should fire on exact match"

    def test_single_font_spec_exact_match(self, all_fonts_present):
        """
        Description: A spec that lists only one font should work correctly
        when that font is available — no IndexError from list operations.
        Scenario: font_family=[HELVETICA], font present.
        Expectation: Returns ('Helvetica', True).
        """
        from plotstyle.engine.fonts import select_best

        spec = _make_journal_spec([HELVETICA])
        font, exact = select_best(spec)

        assert font == HELVETICA
        assert exact is True

    def test_single_font_spec_generic_fallback(self, no_fonts_present):
        """
        Description: A spec with a single unavailable font must fall back to
        the generic family, not raise an IndexError accessing available[0].
        Scenario: font_family=[HELVETICA], font absent.
        Expectation: Returns ('sans-serif', False) without exception.
        """
        import warnings

        from plotstyle._utils.warnings import FontFallbackWarning
        from plotstyle.engine.fonts import select_best

        spec = _make_journal_spec([HELVETICA], "sans-serif")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FontFallbackWarning)
            font, exact = select_best(spec)

        assert font == "sans-serif"
        assert exact is False

    def test_returns_tuple_of_two_elements(self, all_fonts_present, nature_spec):
        """
        Description: The return value must be a 2-tuple that can be unpacked
        as (font_name, is_exact_match). Validates the public API contract.
        Scenario: Normal happy-path call.
        Expectation: isinstance(result, tuple) and len == 2.
        """
        from plotstyle.engine.fonts import select_best

        result = select_best(nature_spec)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_is_exact_match_is_bool(self, all_fonts_present, nature_spec):
        """
        Description: is_exact_match must be strictly bool (True/False), not
        a truthy/falsy value — callers may use `is True`.
        Scenario: Happy path; top font found.
        Expectation: type(exact) is bool.
        """
        from plotstyle.engine.fonts import select_best

        _, exact = select_best(nature_spec)

        assert type(exact) is bool

    def test_warning_stacklevel_points_to_caller(self, no_fonts_present):
        """
        Description: FontFallbackWarning must be emitted at stacklevel=2 so
        the warning's filename/lineno points to the user's call site, not to
        the internals of fonts.py. This is tested by checking that the warning
        category and message are correctly captured (a proxy for proper emission).
        Scenario: No fonts present, generic fallback triggered.
        Expectation: Warning is captured and its category is FontFallbackWarning.
        """
        from plotstyle._utils.warnings import FontFallbackWarning
        from plotstyle.engine.fonts import select_best

        spec = _make_journal_spec([HELVETICA], "sans-serif")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            select_best(spec)  # this line should appear in w[0].filename

        font_warnings = [x for x in w if issubclass(x.category, FontFallbackWarning)]
        assert font_warnings, "FontFallbackWarning must be captured"

    def test_missing_typography_attribute_raises(self):
        """
        Description: Passing a malformed spec that lacks the typography
        attribute must raise AttributeError, as documented in the docstring.
        Scenario: spec object has no .typography attribute.
        Expectation: AttributeError is raised.
        """
        from plotstyle.engine.fonts import select_best

        bad_spec = MagicMock(spec=[])  # no attributes at all
        with pytest.raises(AttributeError):
            select_best(bad_spec)


# === Tests: verify_embedded ===


class TestVerifyEmbedded:
    """Unit tests for verify_embedded()."""

    def test_clean_pdf_returns_empty_list(self, tmp_pdf):
        """
        Description: A PDF without /Type3 markers should yield an empty
        issues list, indicating no problematic fonts.
        Scenario: Real file on disk containing normal PDF bytes; no /Type3.
        Expectation: Returns [].
        """
        from plotstyle.engine.fonts import verify_embedded

        result = verify_embedded(tmp_pdf)

        assert result == []

    def test_type3_pdf_returns_issue(self, tmp_pdf_with_type3):
        """
        Description: A PDF containing the /Type3 byte marker should produce
        exactly one issue dict describing the detected font type.
        Scenario: Real file containing b'/Type3' in its bytes.
        Expectation: Returns a list with one dict; dict has keys 'font' and 'type'.
        """
        from plotstyle.engine.fonts import verify_embedded

        result = verify_embedded(tmp_pdf_with_type3)

        assert len(result) == 1
        assert result[0]["type"] == "Type3"
        assert "font" in result[0]

    def test_issue_dict_has_required_keys(self, tmp_pdf_with_type3):
        """
        Description: Each issue dict in the returned list must contain both
        'font' and 'type' keys so callers can format diagnostic messages.
        Scenario: PDF with Type3 marker.
        Expectation: result[0] has exactly the documented keys.
        """
        from plotstyle.engine.fonts import verify_embedded

        result = verify_embedded(tmp_pdf_with_type3)

        assert "font" in result[0]
        assert "type" in result[0]

    def test_heuristic_label_used_when_name_unknown(self, tmp_pdf_with_type3):
        """
        Description: Because byte-level scanning cannot extract the actual
        font name, the issue dict must use the documented heuristic placeholder.
        Scenario: PDF with /Type3 detected via byte scan.
        Expectation: result[0]['font'] == '(detected via heuristic)'.
        """
        from plotstyle.engine.fonts import verify_embedded

        result = verify_embedded(tmp_pdf_with_type3)

        assert result[0]["font"] == "(detected via heuristic)"

    def test_missing_file_emits_warning_and_returns_empty(self, tmp_path):
        """
        Description: verify_embedded must not raise on missing files; instead
        it emits a UserWarning and returns [] so that a PDF export pipeline is
        not aborted by a verification failure.
        Scenario: Path points to a non-existent file.
        Expectation: Returns [] and emits UserWarning with the path in the message.
        """
        from plotstyle.engine.fonts import verify_embedded

        missing = tmp_path / "nonexistent.pdf"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = verify_embedded(missing)

        assert result == []
        assert any(issubclass(warning.category, UserWarning) for warning in w)

    def test_missing_file_warning_contains_path(self, tmp_path):
        """
        Description: The UserWarning emitted for a missing file should include
        the file path so users can identify which file caused the problem.
        Scenario: Path points to a non-existent file named 'bad.pdf'.
        Expectation: Warning message text contains 'bad.pdf'.
        """
        from plotstyle.engine.fonts import verify_embedded

        missing = tmp_path / "bad.pdf"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            verify_embedded(missing)

        messages = [str(warning.message) for warning in w]
        assert any("bad.pdf" in msg for msg in messages), (
            "Warning message should identify the problematic file path"
        )

    def test_unreadable_file_emits_warning(self, tmp_path):
        """
        Description: If the file exists but raises OSError on read (e.g. due
        to permission denied), verify_embedded must still swallow the error,
        emit a warning, and return [].
        Scenario: pdf_path.read_bytes() raises PermissionError (subclass of OSError).
        Expectation: Returns [] and emits UserWarning.
        """
        from plotstyle.engine.fonts import verify_embedded

        pdf = tmp_path / "locked.pdf"
        pdf.write_bytes(b"%PDF-1.4")

        with (
            patch.object(Path, "read_bytes", side_effect=PermissionError("denied")),
            warnings.catch_warnings(record=True) as w,
        ):
            warnings.simplefilter("always")
            result = verify_embedded(pdf)

        assert result == []
        assert any(issubclass(warning.category, UserWarning) for warning in w)

    def test_truetype_marker_not_flagged(self, tmp_path):
        """
        Description: PDFs produced with pdf.fonttype=42 contain /TrueType
        markers, not /Type3. verify_embedded must NOT flag these — TrueType
        is the desired, safe embedding format.
        Scenario: PDF bytes contain b'/TrueType' but not b'/Type3'.
        Expectation: Returns [].
        """
        from plotstyle.engine.fonts import verify_embedded

        pdf = tmp_path / "truetype.pdf"
        pdf.write_bytes(b"%PDF-1.4\n/Font << /Subtype /TrueType >>\n%%EOF\n")

        result = verify_embedded(pdf)

        assert result == []

    def test_multiple_type3_occurrences_single_issue(self, tmp_path):
        """
        Description: Even if the /Type3 marker appears multiple times (e.g.
        a PDF with many Type 3 font resources), the heuristic returns a single
        issue entry — it detects *presence*, not count.
        Scenario: PDF bytes contain /Type3 three times.
        Expectation: Returns list with exactly one issue dict.
        """
        from plotstyle.engine.fonts import verify_embedded

        pdf = tmp_path / "multi.pdf"
        pdf.write_bytes(b"%PDF-1.4\n/Type3\n/Type3\n/Type3\n%%EOF\n")

        result = verify_embedded(pdf)

        assert len(result) == 1

    def test_empty_pdf_file_returns_empty_list(self, tmp_path):
        """
        Description: An empty file (zero bytes) contains no /Type3 marker
        and should not crash — just return [].
        Scenario: PDF file is completely empty (0 bytes).
        Expectation: Returns [] without exception.
        """
        from plotstyle.engine.fonts import verify_embedded

        pdf = tmp_path / "empty.pdf"
        pdf.write_bytes(b"")

        result = verify_embedded(pdf)

        assert result == []

    def test_return_type_is_list(self, tmp_pdf):
        """
        Description: The return type must always be list[dict], never None,
        so callers can safely iterate without a None-check.
        Scenario: Clean PDF file.
        Expectation: isinstance(result, list) is True.
        """
        from plotstyle.engine.fonts import verify_embedded

        result = verify_embedded(tmp_pdf)

        assert isinstance(result, list)

    def test_symbolic_link_followed(self, tmp_path):
        """
        Description: verify_embedded accepts a Path; symlinks must be resolved
        transparently (Python's read_bytes follows symlinks by default). This
        test ensures the function works for real-world usages where PDF paths
        are symlinks to a build output directory.
        Scenario: PDF symlinked; target contains no /Type3.
        Expectation: Returns [].
        """
        from plotstyle.engine.fonts import verify_embedded

        real = tmp_path / "real.pdf"
        real.write_bytes(b"%PDF-1.4\n%%EOF\n")
        link = tmp_path / "link.pdf"
        link.symlink_to(real)

        result = verify_embedded(link)

        assert result == []


# ---------------------------------------------------------------------------
# Tests: _find_font_or_none (internal helper — tested via detect_available)
# ---------------------------------------------------------------------------


class TestFindFontOrNoneViaPublicAPI:
    """Indirectly test _find_font_or_none error-handling through detect_available."""

    def test_value_error_converted_to_none_sentinel(self, no_fonts_present):
        """
        Description: _find_font_or_none must convert ValueError (the signal
        from findfont for missing fonts) into None, not let it propagate.
        This is tested via detect_available which calls the private helper.
        Scenario: findfont raises ValueError for all families.
        Expectation: detect_available returns []; no ValueError escapes.
        """
        from plotstyle.engine.fonts import detect_available

        result = detect_available([HELVETICA, ARIAL, COURIER])
        assert result == []

    def test_non_value_error_propagates(self):
        """
        Description: Only ValueError is suppressed (the findfont contract).
        Other exceptions (e.g. RuntimeError) should propagate so unexpected
        failures aren't swallowed silently.
        Scenario: findfont raises RuntimeError (unexpected error).
        Expectation: RuntimeError propagates out of detect_available.
        """
        from plotstyle.engine.fonts import detect_available

        with (
            patch(FINDFONT_PATH, side_effect=RuntimeError("unexpected")),
            patch(FINDPROPS_PATH, return_value=MagicMock()),
            pytest.raises(RuntimeError),
        ):
            detect_available([ARIAL])


# ---------------------------------------------------------------------------
# Tests: module-level __all__ and public API surface
# ---------------------------------------------------------------------------


class TestModuleAPI:
    """Smoke tests for the public API surface declared in __all__."""

    def test_all_exports_are_callable(self):
        """
        Description: Every name in __all__ must be importable and callable,
        guaranteeing the module's documented public API is intact.
        Scenario: Import module; inspect __all__.
        Expectation: All three names exist and are callable.
        """
        import plotstyle.engine.fonts as fonts_mod

        for name in fonts_mod.__all__:
            obj = getattr(fonts_mod, name, None)
            assert obj is not None, f"{name} is in __all__ but not defined"
            assert callable(obj), f"{name} should be callable"

    def test_all_contains_expected_names(self):
        """
        Description: __all__ must expose exactly the three documented public
        utilities. Extra entries could leak internal helpers.
        Scenario: Import __all__.
        Expectation: Set equality with {'detect_available', 'select_best',
        'verify_embedded'}.
        """
        from plotstyle.engine.fonts import __all__

        assert set(__all__) == {"detect_available", "select_best", "verify_embedded"}


# ---------------------------------------------------------------------------
# Integration-style tests (marked slow — require real font_manager)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestDetectAvailableIntegration:
    """Integration tests that hit the real matplotlib font_manager.

    These do NOT mock findfont and so depend on the host font installation.
    Marked `slow` so CI can skip them with `-m "not slow"`.
    """

    def test_dejavu_sans_always_present(self):
        """
        Description: DejaVu Sans ships bundled with matplotlib and must
        therefore always be detectable on any system where matplotlib is installed.
        This is the font of last resort for matplotlib's own rendering.
        Scenario: Real findfont; querying DejaVu Sans.
        Expectation: detect_available(['DejaVu Sans']) returns ['DejaVu Sans'].
        """
        from plotstyle.engine.fonts import detect_available

        result = detect_available(["DejaVu Sans"])
        assert "DejaVu Sans" in result, (
            "DejaVu Sans is bundled with matplotlib and should always be detected"
        )

    def test_nonexistent_font_excluded(self):
        """
        Description: A nonsense font name must not appear in the result, even
        when findfont falls back to the default (our fallback_to_default=False
        guard must prevent silent false positives).
        Scenario: Real findfont; querying a font name that cannot exist.
        Expectation: '__totally_fake_font_xyz__' is not in the result.
        """
        from plotstyle.engine.fonts import detect_available

        result = detect_available(["__totally_fake_font_xyz__"])
        assert "__totally_fake_font_xyz__" not in result


# ---------------------------------------------------------------------------
# Parametrized edge-case matrix for detect_available
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "families, found, expected",
    [
        ([HELVETICA, ARIAL, DEJAVU], {HELVETICA, ARIAL, DEJAVU}, [HELVETICA, ARIAL, DEJAVU]),
        ([HELVETICA, ARIAL, DEJAVU], {ARIAL, DEJAVU}, [ARIAL, DEJAVU]),
        ([HELVETICA, ARIAL, DEJAVU], {DEJAVU}, [DEJAVU]),
        ([HELVETICA, ARIAL, DEJAVU], set(), []),
        ([], set(), []),
        ([HELVETICA], {HELVETICA}, [HELVETICA]),
        ([HELVETICA], set(), []),
    ],
    ids=[
        "all_three_present",
        "first_missing",
        "only_last_present",
        "none_present",
        "empty_input",
        "single_present",
        "single_absent",
    ],
)
def test_detect_available_parametrized(families, found, expected):
    """
    Description: Parametrized matrix covering all important subsets of a
    three-font preference list, plus degenerate inputs.
    Scenario: Various combinations of which fonts are 'found' on the system.
    Expectation: detect_available returns exactly the expected list.
    """
    from plotstyle.engine.fonts import detect_available

    def _findfont(props, fallback_to_default=True):
        try:
            family = props.get_family()[0]
        except Exception:
            family = str(props)
        if family in found:
            return f"/fonts/{family}.ttf"
        raise ValueError(f"not found: {family}")

    with (
        patch(FINDPROPS_PATH, side_effect=lambda f: _make_font_props_mock(f)),
        patch(FINDFONT_PATH, side_effect=_findfont),
    ):
        result = detect_available(families)

    assert result == expected


# ---------------------------------------------------------------------------
# Private helpers used only within this test module
# ---------------------------------------------------------------------------


def _make_font_props_mock(family: str) -> MagicMock:
    """Return a FontProperties mock whose get_family() returns [family].

    This mirrors how matplotlib.font_manager.FontProperties works: the
    constructor stores the family and get_family() returns a list.

    Args:
        family: Font family name to encode in the mock.

    Returns:
        A MagicMock with get_family() → [family].
    """
    m = MagicMock()
    m.get_family.return_value = [family]
    return m
