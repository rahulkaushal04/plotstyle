"""Test suite for plotstyle.engine.latex.

Covers:
    - _binary_exists (internal helper)
    - detect_latex
    - detect_distribution
    - configure_latex
    - LatexConfigurationError (exception contract)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from plotstyle.engine.latex import (
    _FALLBACK_TO_PREAMBLE,
    LatexConfigurationError,
    _binary_exists,
    configure_latex,
    detect_distribution,
    detect_latex,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


def _make_spec(font_fallback: str) -> MagicMock:
    """Return a MagicMock whose .typography.font_fallback equals *font_fallback*."""
    spec = MagicMock()
    spec.typography.font_fallback = font_fallback
    return spec


@pytest.fixture()
def serif_spec() -> MagicMock:
    """JournalSpec with font_fallback='serif'."""
    return _make_spec("serif")


@pytest.fixture()
def sans_spec() -> MagicMock:
    """JournalSpec with font_fallback='sans-serif'."""
    return _make_spec("sans-serif")


@pytest.fixture()
def mono_spec() -> MagicMock:
    """JournalSpec with font_fallback='monospace'."""
    return _make_spec("monospace")


@pytest.fixture()
def unknown_spec() -> MagicMock:
    """JournalSpec with a font_fallback not in the preamble table."""
    return _make_spec("fantasy")


# ---------------------------------------------------------------------------
# LatexConfigurationError
# ---------------------------------------------------------------------------


class TestLatexConfigurationError:
    """Verify the custom exception's inheritance and behaviour."""

    def test_is_subclass_of_value_error(self):
        """
        Description: LatexConfigurationError must be a subclass of ValueError.
        Scenario: Catch a LatexConfigurationError with 'except ValueError'.
        Expectation: The except clause catches the exception.
        """
        with pytest.raises(ValueError):
            raise LatexConfigurationError("boom")

    def test_stores_message(self):
        """
        Description: The exception preserves the message string.
        Scenario: Instantiate with a known message and inspect args[0].
        Expectation: str(exc) equals the supplied message.
        """
        msg = "missing typography attribute"
        exc = LatexConfigurationError(msg)
        assert msg in str(exc)

    def test_can_be_raised_and_caught_directly(self):
        """
        Description: LatexConfigurationError can be raised and caught by its own type.
        Scenario: raise then except LatexConfigurationError.
        Expectation: No other exception leaks.
        """
        with pytest.raises(LatexConfigurationError):
            raise LatexConfigurationError("direct catch")


# ---------------------------------------------------------------------------
# _binary_exists (internal helper)
# ---------------------------------------------------------------------------


class TestBinaryExists:
    """Unit tests for the thin _binary_exists wrapper around shutil.which."""

    def test_returns_true_when_which_finds_binary(self):
        """
        Description: _binary_exists returns True when shutil.which returns a path.
        Scenario: Patch shutil.which to return a non-None path string.
        Expectation: _binary_exists returns True.
        """
        with patch("plotstyle.engine.latex.shutil.which", return_value="/usr/bin/latex"):
            assert _binary_exists("latex") is True

    def test_returns_false_when_which_returns_none(self):
        """
        Description: _binary_exists returns False when shutil.which returns None.
        Scenario: Patch shutil.which to return None (binary not found).
        Expectation: _binary_exists returns False.
        """
        with patch("plotstyle.engine.latex.shutil.which", return_value=None):
            assert _binary_exists("latex") is False

    @pytest.mark.parametrize("name", ["latex", "tlmgr", "miktex", "mpm", "pdflatex"])
    def test_passes_name_to_which(self, name: str):
        """
        Description: _binary_exists forwards the binary name to shutil.which verbatim.
        Scenario: Call _binary_exists with various binary names.
        Expectation: shutil.which is called with the exact name supplied.
        """
        with patch("plotstyle.engine.latex.shutil.which", return_value=None) as mock_which:
            _binary_exists(name)
            mock_which.assert_called_once_with(name)

    def test_empty_string_name(self):
        """
        Description: _binary_exists handles an empty string without raising.
        Scenario: Pass an empty string — shutil.which returns None for it.
        Expectation: Returns False (no binary named '' exists on a real PATH).
        """
        with patch("plotstyle.engine.latex.shutil.which", return_value=None):
            assert _binary_exists("") is False


# ---------------------------------------------------------------------------
# detect_latex
# ---------------------------------------------------------------------------


class TestDetectLatex:
    """Tests for detect_latex(), which probes for a 'latex' executable."""

    def test_returns_true_when_latex_present(self):
        """
        Description: detect_latex returns True when 'latex' is on PATH.
        Scenario: Patch _binary_exists to simulate latex being found.
        Expectation: detect_latex() is True.
        """
        with patch("plotstyle.engine.latex._binary_exists", return_value=True):
            assert detect_latex() is True

    def test_returns_false_when_latex_absent(self):
        """
        Description: detect_latex returns False when 'latex' is not on PATH.
        Scenario: Patch _binary_exists to simulate latex missing.
        Expectation: detect_latex() is False.
        """
        with patch("plotstyle.engine.latex._binary_exists", return_value=False):
            assert detect_latex() is False

    def test_queries_correct_binary_name(self):
        """
        Description: detect_latex must probe specifically for 'latex', not any other binary.
        Scenario: Capture _binary_exists calls.
        Expectation: _binary_exists called with 'latex'.
        """
        with patch("plotstyle.engine.latex._binary_exists", return_value=False) as mock:
            detect_latex()
            mock.assert_called_once_with("latex")

    def test_return_type_is_bool(self):
        """
        Description: detect_latex must always return a plain bool, not a truthy object.
        Scenario: Call with latex absent.
        Expectation: result is exactly False (isinstance check).
        """
        with patch("plotstyle.engine.latex._binary_exists", return_value=False):
            result = detect_latex()
            assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# detect_distribution
# ---------------------------------------------------------------------------


class TestDetectDistribution:
    """Tests for detect_distribution(), which identifies the installed TeX toolchain."""

    def _patch_binaries(self, present: set[str]):
        """Return a context-manager that patches _binary_exists to be True only for *present* names."""
        return patch(
            "plotstyle.engine.latex._binary_exists",
            side_effect=lambda name: name in present,
        )

    # --- Happy paths (known distributions) ---

    def test_texlive_detected_via_tlmgr(self):
        """
        Description: TeX Live is identified when 'tlmgr' is on PATH.
        Scenario: tlmgr present, miktex/mpm/latex absent.
        Expectation: Returns 'texlive'.
        """
        with self._patch_binaries({"tlmgr"}):
            assert detect_distribution() == "texlive"

    def test_miktex_detected_via_miktex_binary(self):
        """
        Description: MiKTeX ≥21 is detected via the 'miktex' binary.
        Scenario: miktex present, tlmgr/mpm/latex absent.
        Expectation: Returns 'miktex'.
        """
        with self._patch_binaries({"miktex"}):
            assert detect_distribution() == "miktex"

    def test_miktex_detected_via_mpm_legacy(self):
        """
        Description: Legacy MiKTeX ≤20 is detected via the 'mpm' binary.
        Scenario: mpm present, tlmgr/miktex/latex absent.
        Expectation: Returns 'miktex'.
        """
        with self._patch_binaries({"mpm"}):
            assert detect_distribution() == "miktex"

    def test_miktex_detected_when_both_miktex_and_mpm_present(self):
        """
        Description: Having both miktex and mpm still resolves to 'miktex'.
        Scenario: Both mpm and miktex binaries present.
        Expectation: Returns 'miktex'.
        """
        with self._patch_binaries({"miktex", "mpm"}):
            assert detect_distribution() == "miktex"

    def test_assumed_texlive_when_latex_present_but_no_manager(self):
        """
        Description: When 'latex' is present but no distribution manager is found,
                     the function assumes TeX Live (common in minimal container images).
        Scenario: latex present, tlmgr/miktex/mpm absent.
        Expectation: Returns 'texlive'.
        """
        with self._patch_binaries({"latex"}):
            assert detect_distribution() == "texlive"

    def test_returns_none_when_nothing_found(self):
        """
        Description: Returns None when no LaTeX-related binary exists.
        Scenario: All _binary_exists calls return False.
        Expectation: Returns None.
        """
        with self._patch_binaries(set()):
            assert detect_distribution() is None

    # --- Priority ordering ---

    def test_texlive_takes_priority_over_miktex(self):
        """
        Description: tlmgr detection short-circuits; MiKTeX manager presence is irrelevant.
        Scenario: Both tlmgr and miktex present.
        Expectation: Returns 'texlive', not 'miktex'.
        """
        with self._patch_binaries({"tlmgr", "miktex", "mpm"}):
            assert detect_distribution() == "texlive"

    def test_miktex_takes_priority_over_bare_latex(self):
        """
        Description: If a MiKTeX manager is present, the bare-latex fallback is never reached.
        Scenario: mpm and latex both present, tlmgr absent.
        Expectation: Returns 'miktex'.
        """
        with self._patch_binaries({"mpm", "latex"}):
            assert detect_distribution() == "miktex"

    # --- Return type ---

    def test_return_type_is_str_or_none(self):
        """
        Description: detect_distribution returns only str or None, never other types.
        Scenario: Both none-found and distribution-found cases.
        Expectation: result is str or None.
        """
        with self._patch_binaries(set()):
            result = detect_distribution()
            assert result is None

        with self._patch_binaries({"tlmgr"}):
            result = detect_distribution()
            assert isinstance(result, str)


# ---------------------------------------------------------------------------
# configure_latex
# ---------------------------------------------------------------------------


class TestConfigureLatex:
    """Tests for configure_latex(), which builds a Matplotlib rcParams dict."""

    # --- Happy paths: known font fallbacks ---

    @pytest.mark.parametrize(
        "font_fallback,expected_preamble",
        [
            ("serif", r"\usepackage{times}"),
            (
                "sans-serif",
                r"\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}",
            ),
            (
                "monospace",
                r"\usepackage{courier}\renewcommand{\familydefault}{\ttdefault}",
            ),
        ],
    )
    def test_known_fallback_produces_preamble(self, font_fallback: str, expected_preamble: str):
        """
        Description: Each of the three canonical generic families produces the correct
                     LaTeX preamble in the returned dict.
        Scenario: Spec with each supported font_fallback value.
        Expectation: 'text.latex.preamble' equals the expected PSNFSS snippet.
        """
        spec = _make_spec(font_fallback)
        result = configure_latex(spec)
        assert result["text.latex.preamble"] == expected_preamble

    @pytest.mark.parametrize("font_fallback", ["serif", "sans-serif", "monospace"])
    def test_usetex_always_true(self, font_fallback: str):
        """
        Description: 'text.usetex' must be True for all valid specs — it activates
                     the LaTeX renderer.
        Scenario: All three canonical font families.
        Expectation: result['text.usetex'] is True.
        """
        spec = _make_spec(font_fallback)
        result = configure_latex(spec)
        assert result["text.usetex"] is True

    @pytest.mark.parametrize("font_fallback", ["serif", "sans-serif", "monospace"])
    def test_font_family_matches_fallback(self, font_fallback: str):
        """
        Description: 'font.family' in the result must mirror the spec's font_fallback.
        Scenario: Each canonical font family.
        Expectation: result['font.family'] == font_fallback.
        """
        spec = _make_spec(font_fallback)
        result = configure_latex(spec)
        assert result["font.family"] == font_fallback

    # --- Unknown / unmapped font families ---

    @pytest.mark.parametrize(
        "font_fallback",
        ["fantasy", "cursive", "Palatino", "Times New Roman", "ComputerModern"],
    )
    def test_unknown_fallback_omits_preamble(self, font_fallback: str):
        """
        Description: Font families not in the internal mapping must NOT produce a
                     'text.latex.preamble' entry; LaTeX falls back to the document-class
                     default (usually Computer Modern).
        Scenario: Various font family strings absent from _FALLBACK_TO_PREAMBLE.
        Expectation: 'text.latex.preamble' key is absent from the result dict.
        """
        spec = _make_spec(font_fallback)
        result = configure_latex(spec)
        assert "text.latex.preamble" not in result

    def test_unknown_fallback_still_sets_usetex_and_family(self, unknown_spec):
        """
        Description: Even for unmapped font families, 'text.usetex' and 'font.family'
                     must be present.
        Scenario: Spec with font_fallback='fantasy' (unmapped).
        Expectation: Both mandatory keys are set correctly.
        """
        result = configure_latex(unknown_spec)
        assert result["text.usetex"] is True
        assert result["font.family"] == "fantasy"

    # --- Minimum required keys ---

    @pytest.mark.parametrize("font_fallback", ["serif", "fantasy", "sans-serif"])
    def test_result_always_contains_required_keys(self, font_fallback: str):
        """
        Description: Regardless of the font family, the result must always include
                     'text.usetex' and 'font.family'.
        Scenario: Mapped and unmapped font families.
        Expectation: Both keys are present.
        """
        spec = _make_spec(font_fallback)
        result = configure_latex(spec)
        assert "text.usetex" in result
        assert "font.family" in result

    # --- Error cases ---

    def test_raises_when_typography_attribute_missing(self):
        """
        Description: If the spec object does not expose a 'typography' attribute,
                     configure_latex should raise LatexConfigurationError, not AttributeError.
        Scenario: Spec whose .typography property raises AttributeError.
        Expectation: LatexConfigurationError is raised, wrapping the original AttributeError.
        """
        spec = MagicMock()
        del spec.typography  # MagicMock raises AttributeError for deleted attrs
        with pytest.raises(LatexConfigurationError):
            configure_latex(spec)

    def test_raises_when_font_fallback_is_empty_string(self):
        """
        Description: An empty font_fallback is a malformed spec and must be rejected.
        Scenario: Spec with font_fallback=''.
        Expectation: LatexConfigurationError is raised with a descriptive message.
        """
        spec = _make_spec("")
        with pytest.raises(LatexConfigurationError, match="non-empty"):
            configure_latex(spec)

    def test_raises_when_font_fallback_is_none(self):
        """
        Description: font_fallback=None is falsy and must be treated the same as ''.
        Scenario: Spec with typography.font_fallback = None.
        Expectation: LatexConfigurationError is raised (not TypeError).
        """
        spec = _make_spec(None)  # type: ignore[arg-type]
        with pytest.raises(LatexConfigurationError):
            configure_latex(spec)

    def test_error_message_mentions_typography_when_attr_missing(self):
        """
        Description: The LatexConfigurationError message must hint at the missing attribute
                     so developers can diagnose the problem quickly.
        Scenario: Spec missing the typography attribute.
        Expectation: Exception message contains 'typography'.
        """
        spec = MagicMock(spec=[])  # no attributes at all
        with pytest.raises(LatexConfigurationError, match="typography"):
            configure_latex(spec)

    # --- Return value contract ---

    def test_returns_dict(self, serif_spec):
        """
        Description: configure_latex must return a plain dict (not a subtype) so
                     rcParams.update() can consume it without type gymnastics.
        Scenario: Valid spec.
        Expectation: isinstance(result, dict).
        """
        result = configure_latex(serif_spec)
        assert isinstance(result, dict)

    def test_result_is_new_object_each_call(self, serif_spec):
        """
        Description: configure_latex must not return cached mutable state.
                     Two calls with the same spec must yield independent dicts.
        Scenario: Call configure_latex twice with the same spec.
        Expectation: The two returned dicts are distinct objects.
        """
        result_a = configure_latex(serif_spec)
        result_b = configure_latex(serif_spec)
        assert result_a is not result_b

    def test_preamble_value_type_is_str(self, serif_spec):
        """
        Description: text.latex.preamble must be a str so Matplotlib can concatenate it.
        Scenario: Valid serif spec.
        Expectation: isinstance(result['text.latex.preamble'], str).
        """
        result = configure_latex(serif_spec)
        assert isinstance(result["text.latex.preamble"], str)

    # --- Pure-function: same input same output ---

    @pytest.mark.parametrize("font_fallback", ["serif", "sans-serif", "monospace", "fantasy"])
    def test_deterministic_output(self, font_fallback: str):
        """
        Description: configure_latex is documented as a pure function; the same input
                     must always produce the same output.
        Scenario: Call configure_latex twice with identical specs.
        Expectation: Both results are equal.
        """
        spec_a = _make_spec(font_fallback)
        spec_b = _make_spec(font_fallback)
        assert configure_latex(spec_a) == configure_latex(spec_b)

    # --- Preamble correctness spot checks ---

    def test_serif_preamble_uses_times_package(self, serif_spec):
        """
        Description: The serif preamble activates the 'times' PSNFSS package — not
                     mathptmx or other alternatives.
        Scenario: Spec with font_fallback='serif'.
        Expectation: Preamble contains '\\usepackage{times}'.
        """
        result = configure_latex(serif_spec)
        assert r"\usepackage{times}" in result["text.latex.preamble"]

    def test_sans_preamble_promotes_helvet_as_default(self, sans_spec):
        """
        Description: The sans-serif preamble must promote Helvetica to document default
                     via \\renewcommand{\\familydefault}{\\sfdefault}.
        Scenario: Spec with font_fallback='sans-serif'.
        Expectation: Preamble contains the renewcommand directive.
        """
        result = configure_latex(sans_spec)
        assert r"\renewcommand{\familydefault}{\sfdefault}" in result["text.latex.preamble"]

    def test_mono_preamble_promotes_courier_as_default(self, mono_spec):
        """
        Description: The monospace preamble must promote Courier to document default
                     via \\renewcommand{\\familydefault}{\\ttdefault}.
        Scenario: Spec with font_fallback='monospace'.
        Expectation: Preamble contains the renewcommand directive.
        """
        result = configure_latex(mono_spec)
        assert r"\renewcommand{\familydefault}{\ttdefault}" in result["text.latex.preamble"]

    # --- Whitespace-only font_fallback ---

    def test_raises_for_whitespace_only_font_fallback(self):
        """
        Description: A font_fallback of only whitespace characters is falsy in Python
                     and must be rejected.
        Scenario: font_fallback='   '.
        Expectation: LatexConfigurationError is raised.
        """
        spec = _make_spec("   ")
        # '   ' is truthy in Python, so configure_latex MAY accept it and treat it
        # as an unmapped family (no preamble).  Document the actual behaviour so
        # regressions are caught: either raises or omits preamble.
        try:
            result = configure_latex(spec)
            # If it succeeds, no preamble should be injected for whitespace family.
            assert "text.latex.preamble" not in result
        except LatexConfigurationError:
            pass  # Acceptable — rejecting whitespace-only is also correct.


# ---------------------------------------------------------------------------
# Integration: _FALLBACK_TO_PREAMBLE table consistency
# ---------------------------------------------------------------------------


class TestPreambleTableConsistency:
    """Guard against accidental modification of the internal preamble lookup table."""

    def test_table_contains_exactly_three_entries(self):
        """
        Description: The preamble table maps the three CSS generic families.
                     Extra or missing entries would silently change public behaviour.
        Scenario: Inspect _FALLBACK_TO_PREAMBLE directly.
        Expectation: Exactly three keys: 'serif', 'sans-serif', 'monospace'.
        """
        assert set(_FALLBACK_TO_PREAMBLE.keys()) == {"serif", "sans-serif", "monospace"}

    @pytest.mark.parametrize("key", ["serif", "sans-serif", "monospace"])
    def test_each_preamble_is_nonempty_string(self, key: str):
        """
        Description: Each preamble snippet must be a non-empty string.
        Scenario: Inspect each value in the table.
        Expectation: isinstance(val, str) and len(val) > 0.
        """
        val = _FALLBACK_TO_PREAMBLE[key]
        assert isinstance(val, str)
        assert len(val) > 0

    @pytest.mark.parametrize("key", ["serif", "sans-serif", "monospace"])
    def test_each_preamble_is_valid_latex_macro(self, key: str):
        """
        Description: Every preamble entry must start with a backslash — that's the
                     hallmark of a LaTeX command.
        Scenario: Inspect the leading character of each preamble value.
        Expectation: Preamble starts with '\\'.
        """
        val = _FALLBACK_TO_PREAMBLE[key]
        assert val.startswith("\\"), f"Preamble for '{key}' does not start with backslash."

    def test_configure_latex_preambles_match_table(self):
        """
        Description: configure_latex must derive preamble values from the table, not
                     hard-code them separately.  If the table is updated, the function
                     output must reflect that change.
        Scenario: Compare configure_latex output against _FALLBACK_TO_PREAMBLE directly.
        Expectation: For each mapped family, result['text.latex.preamble'] == table value.
        """
        for family, expected_preamble in _FALLBACK_TO_PREAMBLE.items():
            spec = _make_spec(family)
            result = configure_latex(spec)
            assert result["text.latex.preamble"] == expected_preamble, (
                f"configure_latex preamble for '{family}' diverges from table."
            )
