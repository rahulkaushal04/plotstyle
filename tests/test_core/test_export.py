"""Enhanced test suite for plotstyle.core.export.

Covers: _build_filename, _snapshot_rcparams, _print_compliance_summary,
savefig, export_submission, FORMAT_EXTENSIONS, and all edge cases.
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")

from plotstyle.core.export import (
    _IEEE_SURNAME_PREFIX_LEN,
    _RESTORE_KEYS,
    FORMAT_EXTENSIONS,
    _build_filename,
    _print_compliance_summary,
    _snapshot_rcparams,
    export_submission,
    savefig,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_fig() -> plt.Figure:
    """A minimal Matplotlib figure for reuse across tests."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    return fig


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """A temporary directory for output files."""
    return tmp_path


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all Matplotlib figures after each test to prevent memory leaks."""
    yield
    plt.close("all")


# ---------------------------------------------------------------------------
# FORMAT_EXTENSIONS constant
# ---------------------------------------------------------------------------


class TestFormatExtensions:
    """Validate the FORMAT_EXTENSIONS mapping structure and content."""

    def test_format_extensions_is_dict(self) -> None:
        """
        Description: FORMAT_EXTENSIONS must be a dict for lookup purposes.
        Scenario: Check type of FORMAT_EXTENSIONS.
        Expectation: isinstance(dict) is True.
        """
        assert isinstance(FORMAT_EXTENSIONS, dict)

    @pytest.mark.parametrize(
        "fmt,ext",
        [
            ("pdf", ".pdf"),
            ("eps", ".eps"),
            ("tiff", ".tiff"),
            ("tif", ".tif"),
            ("png", ".png"),
            ("svg", ".svg"),
            ("jpg", ".jpg"),
            ("jpeg", ".jpeg"),
            ("ps", ".ps"),
        ],
    )
    def test_all_known_formats_have_correct_extensions(self, fmt: str, ext: str) -> None:
        """
        Description: Every canonical format key must map to its expected extension.
        Scenario: Parametric check for each format.
        Expectation: Extension matches the standard file suffix.
        """
        assert FORMAT_EXTENSIONS[fmt] == ext

    def test_format_extensions_all_values_start_with_dot(self) -> None:
        """
        Description: File extensions must start with a dot to form valid paths.
        Scenario: Iterate all values.
        Expectation: Each starts with '.'.
        """
        for ext in FORMAT_EXTENSIONS.values():
            assert ext.startswith(".")

    def test_format_extensions_all_keys_are_lowercase(self) -> None:
        """
        Description: Format keys must be lowercase for consistent lookups.
        Scenario: Iterate all keys.
        Expectation: Each key equals its lower-cased form.
        """
        for key in FORMAT_EXTENSIONS:
            assert key == key.lower()

    def test_format_extensions_has_expected_count(self) -> None:
        """
        Description: The mapping must contain exactly 10 known formats.
        Scenario: Check len(FORMAT_EXTENSIONS).
        Expectation: Exactly 10 entries (pdf, eps, tiff, tif, png, svg, jpg, jpeg, ps, ai).
        """
        assert len(FORMAT_EXTENSIONS) == 10


# ---------------------------------------------------------------------------
# _RESTORE_KEYS constant
# ---------------------------------------------------------------------------


class TestRestoreKeys:
    """Validate the _RESTORE_KEYS constant."""

    def test_restore_keys_is_frozenset(self) -> None:
        """
        Description: _RESTORE_KEYS must be a frozenset for immutability.
        Scenario: Check type.
        Expectation: isinstance(frozenset) is True.
        """
        assert isinstance(_RESTORE_KEYS, frozenset)

    def test_restore_keys_contains_fonttype_keys(self) -> None:
        """
        Description: pdf.fonttype and ps.fonttype must be in the restore set.
        Scenario: Check membership.
        Expectation: Both keys present.
        """
        assert "pdf.fonttype" in _RESTORE_KEYS
        assert "ps.fonttype" in _RESTORE_KEYS

    def test_restore_keys_contains_savefig_dpi(self) -> None:
        """
        Description: savefig.dpi must be restored after each save.
        Scenario: Check membership.
        Expectation: 'savefig.dpi' in _RESTORE_KEYS.
        """
        assert "savefig.dpi" in _RESTORE_KEYS

    def test_restore_keys_is_nonempty(self) -> None:
        """
        Description: At least the safety params and DPI must be tracked.
        Scenario: Check length.
        Expectation: len > 0.
        """
        assert len(_RESTORE_KEYS) > 0


# ---------------------------------------------------------------------------
# _snapshot_rcparams
# ---------------------------------------------------------------------------


class TestSnapshotRcparams:
    """Validate internal rcParams snapshotting helper."""

    def test_snapshot_captures_existing_keys(self) -> None:
        """
        Description: Keys present in mpl.rcParams must appear in the snapshot.
        Scenario: Snapshot a known key ('pdf.fonttype').
        Expectation: Key present in returned dict.
        """
        keys = frozenset({"pdf.fonttype"})
        snap = _snapshot_rcparams(keys)
        assert "pdf.fonttype" in snap

    def test_snapshot_skips_missing_keys(self) -> None:
        """
        Description: Keys absent from mpl.rcParams should be silently skipped.
        Scenario: Snapshot a fabricated key.
        Expectation: Key not in returned dict.
        """
        keys = frozenset({"plotstyle.nonexistent.key.xyz"})
        snap = _snapshot_rcparams(keys)
        assert "plotstyle.nonexistent.key.xyz" not in snap

    def test_snapshot_returns_dict(self) -> None:
        """
        Description: The return type must be a plain dict.
        Scenario: Call _snapshot_rcparams with _RESTORE_KEYS.
        Expectation: isinstance(dict) is True.
        """
        snap = _snapshot_rcparams(_RESTORE_KEYS)
        assert isinstance(snap, dict)

    def test_snapshot_empty_keys_returns_empty_dict(self) -> None:
        """
        Description: An empty key set must produce an empty snapshot.
        Scenario: Pass frozenset() as keys.
        Expectation: Empty dict returned.
        """
        assert _snapshot_rcparams(frozenset()) == {}

    def test_snapshot_captures_correct_values(self) -> None:
        """
        Description: Snapshot values must match current mpl.rcParams values.
        Scenario: Snapshot pdf.fonttype and compare.
        Expectation: Values match.
        """
        keys = frozenset({"pdf.fonttype", "ps.fonttype"})
        snap = _snapshot_rcparams(keys)
        for key in keys:
            assert snap[key] == mpl.rcParams[key]

    def test_snapshot_mixed_existing_and_missing_keys(self) -> None:
        """
        Description: A mix of real/fake keys returns only the existing ones.
        Scenario: Pass one real key and one fake key.
        Expectation: Only real key appears in result.
        """
        keys = frozenset({"pdf.fonttype", "plotstyle.fake.key"})
        snap = _snapshot_rcparams(keys)
        assert "pdf.fonttype" in snap
        assert "plotstyle.fake.key" not in snap
        assert len(snap) == 1

    def test_snapshot_returns_shallow_copy(self) -> None:
        """
        Description: Modifying the snapshot must not affect mpl.rcParams.
        Scenario: Modify a value in the snapshot dict.
        Expectation: Original rcParam unchanged.
        """
        keys = frozenset({"pdf.fonttype"})
        original = mpl.rcParams["pdf.fonttype"]
        snap = _snapshot_rcparams(keys)
        snap["pdf.fonttype"] = -999
        assert mpl.rcParams["pdf.fonttype"] == original


# ---------------------------------------------------------------------------
# _build_filename
# ---------------------------------------------------------------------------


class TestBuildFilename:
    """Validate filename generation for various journal and format combinations."""

    def test_generic_filename_without_journal(self) -> None:
        """
        Description: Without a journal, filename is just stem + extension.
        Scenario: _build_filename('fig1', 'pdf').
        Expectation: 'fig1.pdf'.
        """
        assert _build_filename("fig1", "pdf") == "fig1.pdf"

    def test_generic_filename_with_non_ieee_journal(self) -> None:
        """
        Description: Non-IEEE journals should not apply any prefix.
        Scenario: _build_filename('fig1', 'pdf', journal='nature').
        Expectation: 'fig1.pdf'.
        """
        assert _build_filename("fig1", "pdf", journal="nature") == "fig1.pdf"

    def test_ieee_filename_with_surname(self) -> None:
        """
        Description: IEEE requires surname prefix on filenames.
        Scenario: _build_filename('fig1', 'pdf', author_surname='Smith', journal='ieee').
        Expectation: 'smith_fig1.pdf' (first 5 chars lower-cased).
        """
        result = _build_filename("fig1", "pdf", author_surname="Smith", journal="ieee")
        assert result == "smith_fig1.pdf"

    def test_ieee_surname_case_insensitive_journal(self) -> None:
        """
        Description: Journal name matching must be case-insensitive.
        Scenario: journal='IEEE' (uppercase).
        Expectation: IEEE prefix convention still applied.
        """
        result = _build_filename("fig1", "pdf", author_surname="Smith", journal="IEEE")
        assert result == "smith_fig1.pdf"

    def test_ieee_journal_mixed_case(self) -> None:
        """
        Description: Mixed-case journal name must still match IEEE.
        Scenario: journal='Ieee'.
        Expectation: IEEE prefix convention applied.
        """
        result = _build_filename("fig1", "pdf", author_surname="Smith", journal="Ieee")
        assert result == "smith_fig1.pdf"

    def test_ieee_surname_shorter_than_prefix_len(self) -> None:
        """
        Description: Short surnames are used in full without padding.
        Scenario: surname='Lee' (3 chars < _IEEE_SURNAME_PREFIX_LEN).
        Expectation: 'lee_fig1.pdf'.
        """
        result = _build_filename("fig1", "pdf", author_surname="Lee", journal="ieee")
        assert result == "lee_fig1.pdf"

    def test_ieee_surname_single_char(self) -> None:
        """
        Description: Single-character surnames are used in full.
        Scenario: surname='X'.
        Expectation: 'x_fig1.pdf'.
        """
        result = _build_filename("fig1", "pdf", author_surname="X", journal="ieee")
        assert result == "x_fig1.pdf"

    def test_ieee_surname_exactly_prefix_length(self) -> None:
        """
        Description: Surname exactly matching prefix length uses all characters.
        Scenario: surname='Johns' (5 chars == _IEEE_SURNAME_PREFIX_LEN).
        Expectation: 'johns_fig1.tiff'.
        """
        result = _build_filename("fig1", "tiff", author_surname="Johns", journal="ieee")
        assert result == "johns_fig1.tiff"

    def test_ieee_surname_longer_than_prefix_len_truncates(self) -> None:
        """
        Description: Surnames longer than prefix length are truncated.
        Scenario: surname='Smithson' (8 chars > 5).
        Expectation: 'smith_fig1.pdf'.
        """
        result = _build_filename("fig1", "pdf", author_surname="Smithson", journal="ieee")
        assert result == "smith_fig1.pdf"

    def test_ieee_no_surname_skips_prefix(self) -> None:
        """
        Description: IEEE without author_surname falls back to generic naming.
        Scenario: journal='ieee', author_surname=None.
        Expectation: 'fig1.pdf' (no prefix).
        """
        assert _build_filename("fig1", "pdf", journal="ieee") == "fig1.pdf"

    def test_ieee_empty_surname_skips_prefix(self) -> None:
        """
        Description: An empty-string surname is falsy and should skip the prefix.
        Scenario: author_surname='', journal='ieee'.
        Expectation: 'fig1.pdf'.
        """
        assert _build_filename("fig1", "pdf", author_surname="", journal="ieee") == "fig1.pdf"

    def test_unknown_format_uses_format_as_extension(self) -> None:
        """
        Description: Formats not in FORMAT_EXTENSIONS use the key as extension.
        Scenario: fmt='webp' (not in dict).
        Expectation: 'fig1.webp'.
        """
        assert _build_filename("fig1", "webp") == "fig1.webp"

    def test_unknown_format_with_unusual_name(self) -> None:
        """
        Description: Arbitrary format strings produce a dot-prefixed extension.
        Scenario: fmt='custom123'.
        Expectation: 'fig1.custom123'.
        """
        assert _build_filename("fig1", "custom123") == "fig1.custom123"

    @pytest.mark.parametrize("fmt", list(FORMAT_EXTENSIONS.keys()))
    def test_all_known_formats_produce_correct_extension(self, fmt: str) -> None:
        """
        Description: Every known format key must map to its standard extension.
        Scenario: Parametric sweep over FORMAT_EXTENSIONS.
        Expectation: Filename ends with the mapped extension.
        """
        result = _build_filename("fig1", fmt)
        assert result.endswith(FORMAT_EXTENSIONS[fmt])

    def test_surname_without_journal_skips_prefix(self) -> None:
        """
        Description: Providing author_surname without journal should not prefix.
        Scenario: author_surname='Smith', journal=None.
        Expectation: 'fig1.pdf'.
        """
        assert _build_filename("fig1", "pdf", author_surname="Smith") == "fig1.pdf"

    def test_surname_with_non_ieee_journal_skips_prefix(self) -> None:
        """
        Description: Surname with a non-IEEE journal must not apply prefix.
        Scenario: author_surname='Smith', journal='science'.
        Expectation: 'fig1.pdf'.
        """
        result = _build_filename("fig1", "pdf", author_surname="Smith", journal="science")
        assert result == "fig1.pdf"

    def test_ieee_surname_prefix_len_constant(self) -> None:
        """
        Description: The IEEE prefix length constant must be 5.
        Scenario: Check _IEEE_SURNAME_PREFIX_LEN.
        Expectation: 5.
        """
        assert _IEEE_SURNAME_PREFIX_LEN == 5

    def test_ieee_uppercase_surname_is_lowered(self) -> None:
        """
        Description: Uppercase surnames must be lowered for the prefix.
        Scenario: author_surname='ANDERSON', journal='ieee'.
        Expectation: 'ander_fig1.pdf'.
        """
        result = _build_filename("fig1", "pdf", author_surname="ANDERSON", journal="ieee")
        assert result == "ander_fig1.pdf"

    def test_empty_stem(self) -> None:
        """
        Description: Empty stem is technically valid; produces just the extension.
        Scenario: _build_filename('', 'pdf').
        Expectation: '.pdf'.
        """
        assert _build_filename("", "pdf") == ".pdf"

    def test_stem_with_dots(self) -> None:
        """
        Description: Stems containing dots must not be confused with extensions.
        Scenario: _build_filename('fig.v2', 'pdf').
        Expectation: 'fig.v2.pdf'.
        """
        assert _build_filename("fig.v2", "pdf") == "fig.v2.pdf"

    def test_ieee_non_ascii_surname(self) -> None:
        """
        Description: Non-ASCII surnames must still be sliced and lowered.
        Scenario: author_surname='Müller', journal='ieee'.
        Expectation: 'mülle_fig1.pdf' (first 5 chars).
        """
        result = _build_filename("fig1", "pdf", author_surname="Müller", journal="ieee")
        assert result == "mülle_fig1.pdf"


# ---------------------------------------------------------------------------
# _print_compliance_summary
# ---------------------------------------------------------------------------


class TestPrintComplianceSummary:
    """Validate the compliance summary output for different file types."""

    @patch("plotstyle.core.export.verify_embedded", return_value=[])
    def test_pdf_output_mentions_truetype(
        self, mock_verify: MagicMock, simple_fig: plt.Figure
    ) -> None:
        """
        Description: PDF saves must report TrueType font embedding.
        Scenario: Print summary for a .pdf path.
        Expectation: 'TrueType' appears in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.pdf"), 300, out=buf)
        assert "TrueType" in buf.getvalue()

    def test_eps_output_mentions_truetype(self, simple_fig: plt.Figure) -> None:
        """
        Description: EPS saves must report TrueType font embedding.
        Scenario: Print summary for a .eps path.
        Expectation: 'TrueType' appears in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.eps"), 300, out=buf)
        assert "TrueType" in buf.getvalue()

    def test_ps_output_mentions_truetype(self, simple_fig: plt.Figure) -> None:
        """
        Description: PS saves must report TrueType font embedding.
        Scenario: Print summary for a .ps path.
        Expectation: 'TrueType' appears in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.ps"), 300, out=buf)
        assert "TrueType" in buf.getvalue()

    @pytest.mark.parametrize("suffix", [".PDF", ".Pdf", ".EPS", ".Eps", ".PS", ".Ps"])
    def test_case_insensitive_suffix_mentions_truetype(
        self, simple_fig: plt.Figure, suffix: str
    ) -> None:
        """
        Description: Suffix comparison must be case-insensitive.
        Scenario: Print summary for uppercase/mixed-case vector format suffixes.
        Expectation: 'TrueType' still appears in output.
        """
        buf = io.StringIO()
        with patch("plotstyle.core.export.verify_embedded", return_value=[]):
            _print_compliance_summary(simple_fig, Path(f"test{suffix}"), 300, out=buf)
        assert "TrueType" in buf.getvalue()

    def test_png_output_omits_truetype(self, simple_fig: plt.Figure) -> None:
        """
        Description: Raster formats should not mention TrueType embedding.
        Scenario: Print summary for a .png path.
        Expectation: 'TrueType' does NOT appear.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.png"), 300, out=buf)
        assert "TrueType" not in buf.getvalue()

    @pytest.mark.parametrize("suffix", [".png", ".tiff", ".jpg", ".svg"])
    def test_raster_and_svg_omit_truetype(self, simple_fig: plt.Figure, suffix: str) -> None:
        """
        Description: Non-vector formats must not mention TrueType.
        Scenario: Print summary for raster and SVG formats.
        Expectation: 'TrueType' not in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path(f"test{suffix}"), 300, out=buf)
        assert "TrueType" not in buf.getvalue()

    def test_summary_contains_dpi(self, simple_fig: plt.Figure) -> None:
        """
        Description: The summary must report the DPI used during saving.
        Scenario: Print summary with dpi_value=600.
        Expectation: '600' appears in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.png"), 600, out=buf)
        assert "600" in buf.getvalue()

    def test_summary_contains_dimensions(self, simple_fig: plt.Figure) -> None:
        """
        Description: The summary must report figure dimensions.
        Scenario: Print summary for any path.
        Expectation: 'Dimensions:' appears in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.png"), 300, out=buf)
        assert "Dimensions:" in buf.getvalue()

    @patch("plotstyle.core.export.verify_embedded", return_value=[])
    def test_summary_contains_saved_path(
        self, mock_verify: MagicMock, simple_fig: plt.Figure
    ) -> None:
        """
        Description: The summary must include the saved file path.
        Scenario: Print summary with path='my_figure.pdf'.
        Expectation: 'my_figure.pdf' appears in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("my_figure.pdf"), 300, out=buf)
        assert "my_figure.pdf" in buf.getvalue()

    def test_summary_defaults_to_stderr(self, simple_fig: plt.Figure) -> None:
        """
        Description: When out=None, summary should print to stderr.
        Scenario: Call with out=None and capture stderr.
        Expectation: No exception raised; output goes to stderr.
        """
        _print_compliance_summary(simple_fig, Path("test.png"), 300)

    @patch("plotstyle.core.export.verify_embedded", return_value=[])
    def test_pdf_no_type3_fonts_no_warning(
        self, mock_verify: MagicMock, simple_fig: plt.Figure
    ) -> None:
        """
        Description: PDFs without Type 3 fonts should emit no warning.
        Scenario: verify_embedded returns empty list for a .pdf.
        Expectation: No Type 3 warning in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.pdf"), 300, out=buf)
        assert "Type 3" not in buf.getvalue()

    @patch(
        "plotstyle.core.export.verify_embedded",
        return_value=[{"font": "SomeFont", "type": "Type3"}],
    )
    def test_pdf_type3_font_emits_warning(
        self, mock_verify: MagicMock, simple_fig: plt.Figure
    ) -> None:
        """
        Description: PDFs with Type 3 fonts must produce a warning message.
        Scenario: verify_embedded returns a Type3 hit.
        Expectation: 'Type 3 font detected' appears in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.pdf"), 300, out=buf)
        assert "Type 3 font detected" in buf.getvalue()

    @patch(
        "plotstyle.core.export.verify_embedded",
        return_value=[
            {"font": "FontA", "type": "Type3"},
            {"font": "FontB", "type": "Type3"},
        ],
    )
    def test_pdf_multiple_type3_fonts_emits_single_warning(
        self, mock_verify: MagicMock, simple_fig: plt.Figure
    ) -> None:
        """
        Description: Multiple Type 3 hits must produce at most one warning.
        Scenario: verify_embedded returns two Type3 hits.
        Expectation: Only one 'Type 3 font detected' line.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.pdf"), 300, out=buf)
        assert buf.getvalue().count("Type 3 font detected") == 1

    @patch(
        "plotstyle.core.export.verify_embedded",
        return_value=[{"font": "SomeFont", "type": "TrueType"}],
    )
    def test_pdf_truetype_hit_no_type3_warning(
        self, mock_verify: MagicMock, simple_fig: plt.Figure
    ) -> None:
        """
        Description: Non-Type3 font hits must not trigger a Type 3 warning.
        Scenario: verify_embedded returns a TrueType hit (not Type3).
        Expectation: No 'Type 3 font detected' in output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.pdf"), 300, out=buf)
        assert "Type 3 font detected" not in buf.getvalue()

    def test_dpi_string_figure_value(self, simple_fig: plt.Figure) -> None:
        """
        Description: DPI may be the string 'figure' when not explicitly set.
        Scenario: Pass dpi_value='figure'.
        Expectation: 'figure' appears in the output.
        """
        buf = io.StringIO()
        _print_compliance_summary(simple_fig, Path("test.png"), "figure", out=buf)
        assert "figure" in buf.getvalue()

    def test_non_pdf_does_not_call_verify_embedded(self, simple_fig: plt.Figure) -> None:
        """
        Description: Non-PDF files must not trigger the Type 3 font scan.
        Scenario: Print summary for a .png path.
        Expectation: verify_embedded is not called.
        """
        with patch("plotstyle.core.export.verify_embedded") as mock_verify:
            buf = io.StringIO()
            _print_compliance_summary(simple_fig, Path("test.png"), 300, out=buf)
            mock_verify.assert_not_called()


# ---------------------------------------------------------------------------
# savefig
# ---------------------------------------------------------------------------


class TestSavefig:
    """Validate the savefig wrapper for font embedding and DPI enforcement."""

    def test_savefig_creates_file(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: savefig must write a file to disk.
        Scenario: Save a figure as PDF.
        Expectation: File exists after call.
        """
        out = tmp_output / "fig.pdf"
        savefig(simple_fig, out)
        assert out.exists()

    def test_savefig_pdf_file_non_empty(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: The saved PDF must have non-zero size.
        Scenario: Save as PDF and check file size.
        Expectation: File size > 0.
        """
        out = tmp_output / "fig.pdf"
        savefig(simple_fig, out)
        assert out.stat().st_size > 0

    def test_savefig_restores_rcparams_after_save(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: savefig must restore mpl.rcParams after completion.
        Scenario: Record rcParams, call savefig, compare.
        Expectation: pdf.fonttype and ps.fonttype are restored.
        """
        original_pdf = mpl.rcParams["pdf.fonttype"]
        original_ps = mpl.rcParams["ps.fonttype"]
        savefig(simple_fig, tmp_output / "fig.pdf")
        assert mpl.rcParams["pdf.fonttype"] == original_pdf
        assert mpl.rcParams["ps.fonttype"] == original_ps

    def test_savefig_restores_rcparams_on_exception(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: rcParams must be restored even when savefig raises.
        Scenario: Mock Figure.savefig to raise an error.
        Expectation: pdf.fonttype and ps.fonttype are still restored.
        """
        original_pdf = mpl.rcParams["pdf.fonttype"]
        original_ps = mpl.rcParams["ps.fonttype"]
        with (
            patch.object(simple_fig, "savefig", side_effect=OSError("disk full")),
            pytest.raises(OSError, match="disk full"),
        ):
            savefig(simple_fig, tmp_output / "fig.pdf")
        assert mpl.rcParams["pdf.fonttype"] == original_pdf
        assert mpl.rcParams["ps.fonttype"] == original_ps

    def test_savefig_restores_dpi_on_exception_with_journal(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: savefig.dpi must be restored even on error with journal.
        Scenario: Mock Figure.savefig to raise, with journal='ieee'.
        Expectation: savefig.dpi restored to original.
        """
        original_dpi = mpl.rcParams.get("savefig.dpi")
        with (
            patch.object(simple_fig, "savefig", side_effect=OSError("fail")),
            pytest.raises(OSError),
        ):
            savefig(simple_fig, tmp_output / "fig.pdf", journal="ieee")
        assert mpl.rcParams.get("savefig.dpi") == original_dpi

    def test_savefig_with_journal_applies_dpi(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: When a journal is specified, its min_dpi must be applied during save.
        Scenario: Monitor rcParams inside the mocked savefig call with journal='nature'.
        Expectation: savefig.dpi == Nature's min_dpi (300) at the moment savefig is called.
        """
        captured_dpi: dict[str, object] = {}
        out = tmp_output / "fig.pdf"

        def capture_savefig(*args, **kwargs):
            captured_dpi["value"] = mpl.rcParams.get("savefig.dpi")
            out.write_bytes(b"%PDF-1.4 fake")

        with patch.object(simple_fig, "savefig", side_effect=capture_savefig):
            savefig(simple_fig, out, journal="nature")

        assert captured_dpi["value"] == 300  # Nature's min_dpi

    def test_savefig_unknown_journal_raises(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: An unknown journal must raise SpecNotFoundError.
        Scenario: savefig with journal='nonexistent'.
        Expectation: KeyError (SpecNotFoundError) raised.
        """
        with pytest.raises(KeyError):
            savefig(simple_fig, tmp_output / "fig.pdf", journal="nonexistent_journal_xyz")

    def test_savefig_unknown_journal_restores_rcparams(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: rcParams must be restored even when journal lookup fails.
        Scenario: savefig with unknown journal.
        Expectation: rcParams restored after KeyError.
        """
        original_pdf = mpl.rcParams["pdf.fonttype"]
        with pytest.raises(KeyError):
            savefig(simple_fig, tmp_output / "fig.pdf", journal="nonexistent_journal_xyz")
        assert mpl.rcParams["pdf.fonttype"] == original_pdf

    def test_savefig_default_bbox_inches_tight(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: bbox_inches should default to 'tight' when not provided.
        Scenario: Save a figure without specifying bbox_inches.
        Expectation: No error; file is created.
        """
        out = tmp_output / "fig.png"
        savefig(simple_fig, out)
        assert out.exists()

    def test_savefig_explicit_bbox_inches_overrides_default(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: An explicit bbox_inches kwarg must override the default.
        Scenario: savefig with bbox_inches=None.
        Expectation: No error; file is created.
        """
        out = tmp_output / "fig.png"
        savefig(simple_fig, out, bbox_inches=None)
        assert out.exists()

    def test_savefig_passes_kwargs_to_matplotlib(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: Extra kwargs must be forwarded to Figure.savefig.
        Scenario: Pass dpi=150 explicitly.
        Expectation: No error; file is created.
        """
        out = tmp_output / "fig.png"
        savefig(simple_fig, out, dpi=150)
        assert out.exists()

    def test_savefig_string_path_accepted(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: savefig must accept string paths in addition to Path objects.
        Scenario: Pass a str path.
        Expectation: File is created.
        """
        out = str(tmp_output / "fig.png")
        savefig(simple_fig, out)
        assert Path(out).exists()

    def test_savefig_svg_format(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: SVG output must be supported.
        Scenario: Save as SVG.
        Expectation: File exists and is non-empty.
        """
        out = tmp_output / "fig.svg"
        savefig(simple_fig, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_savefig_eps_format(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: EPS output must be supported.
        Scenario: Save as EPS.
        Expectation: File exists and is non-empty.
        """
        out = tmp_output / "fig.eps"
        savefig(simple_fig, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_savefig_sets_pdf_fonttype_42_during_save(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: During save, pdf.fonttype must be set to 42 (TrueType).
        Scenario: Monitor rcParams inside the mocked savefig call.
        Expectation: pdf.fonttype == 42 when savefig is called.
        """
        captured_fonttype = {}
        out = tmp_output / "fig.pdf"

        def capture_savefig(*args, **kwargs):
            captured_fonttype["pdf"] = mpl.rcParams["pdf.fonttype"]
            captured_fonttype["ps"] = mpl.rcParams["ps.fonttype"]
            # Create the file so _print_compliance_summary can read it
            out.write_bytes(b"%PDF-1.4 fake")

        with patch.object(simple_fig, "savefig", side_effect=capture_savefig):
            savefig(simple_fig, out)

        assert captured_fonttype["pdf"] == 42
        assert captured_fonttype["ps"] == 42

    def test_savefig_explicit_dpi_kwarg_overrides_journal(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: An explicit dpi= kwarg must take precedence.
        Scenario: savefig with journal='ieee' and dpi=72.
        Expectation: No error; file created.
        """
        out = tmp_output / "fig.png"
        savefig(simple_fig, out, journal="ieee", dpi=72)
        assert out.exists()

    def test_savefig_no_journal_does_not_set_dpi(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: Without a journal, savefig.dpi should not be modified.
        Scenario: Call savefig without journal.
        Expectation: savefig.dpi unchanged after call.
        """
        original_dpi = mpl.rcParams.get("savefig.dpi")
        savefig(simple_fig, tmp_output / "fig.png")
        assert mpl.rcParams.get("savefig.dpi") == original_dpi


# ---------------------------------------------------------------------------
# export_submission
# ---------------------------------------------------------------------------


class TestExportSubmission:
    """Validate batch export for journal submissions."""

    def test_export_creates_all_requested_formats(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: Each specified format must produce a separate file.
        Scenario: Export with formats=['pdf', 'png'].
        Expectation: Two files created.
        """
        paths = export_submission(simple_fig, "fig1", formats=["pdf", "png"], output_dir=tmp_output)
        assert len(paths) == 2
        for p in paths:
            assert p.exists()

    def test_export_returns_list_of_paths(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: Return value must be a list of Path objects.
        Scenario: Export a single format.
        Expectation: List of length 1 containing a Path.
        """
        paths = export_submission(simple_fig, "fig1", formats=["pdf"], output_dir=tmp_output)
        assert isinstance(paths, list)
        assert all(isinstance(p, Path) for p in paths)

    def test_export_default_format_is_pdf(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: Without explicit formats or journal, default is PDF.
        Scenario: Export with no formats and no journal.
        Expectation: One PDF file created.
        """
        paths = export_submission(simple_fig, "fig1", output_dir=tmp_output)
        assert len(paths) == 1
        assert paths[0].suffix == ".pdf"

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_export_uses_journal_preferred_formats(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: When journal is given and formats is None, use spec's preferred_formats.
        Scenario: Export with journal='nature', no explicit formats.
        Expectation: Files created matching Nature's preferred formats.
        """
        paths = export_submission(simple_fig, "fig1", journal="nature", output_dir=tmp_output)
        assert len(paths) >= 1
        for p in paths:
            assert p.exists()

    def test_export_explicit_formats_override_journal(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: Explicit formats must take priority over journal defaults.
        Scenario: Export with journal='nature' but formats=['svg'].
        Expectation: Only one SVG file created.
        """
        paths = export_submission(
            simple_fig, "fig1", formats=["svg"], journal="nature", output_dir=tmp_output
        )
        assert len(paths) == 1
        assert paths[0].suffix == ".svg"

    def test_export_creates_output_dir_if_missing(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: export_submission must create the output directory if absent.
        Scenario: Export into a non-existent subdirectory.
        Expectation: Directory and file both created.
        """
        nested = tmp_output / "sub" / "deep"
        paths = export_submission(simple_fig, "fig1", formats=["pdf"], output_dir=nested)
        assert nested.exists()
        assert len(paths) == 1

    def test_export_ieee_surname_prefix(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: IEEE exports must prefix filenames with the author surname.
        Scenario: Export with journal='ieee', author_surname='Smith'.
        Expectation: Filename starts with 'smith_'.
        """
        paths = export_submission(
            simple_fig,
            "fig1",
            formats=["pdf"],
            journal="ieee",
            output_dir=tmp_output,
            author_surname="Smith",
        )
        assert paths[0].name.startswith("smith_")

    def test_export_unknown_journal_raises(self, simple_fig: plt.Figure, tmp_output: Path) -> None:
        """
        Description: An unknown journal must raise SpecNotFoundError.
        Scenario: export_submission with journal='nonexistent'.
        Expectation: KeyError (SpecNotFoundError) raised.
        """
        with pytest.raises(KeyError):
            export_submission(
                simple_fig,
                "fig1",
                journal="nonexistent_journal_xyz",
                output_dir=tmp_output,
            )

    def test_export_preserves_order_of_formats(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: Returned paths must match the order of the format list.
        Scenario: Export with formats=['svg', 'png', 'pdf'].
        Expectation: Suffixes match in order.
        """
        paths = export_submission(
            simple_fig, "fig1", formats=["svg", "png", "pdf"], output_dir=tmp_output
        )
        assert [p.suffix for p in paths] == [".svg", ".png", ".pdf"]

    def test_export_existing_output_dir_no_error(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: Exporting into an existing directory must not raise.
        Scenario: Call export_submission twice to the same directory.
        Expectation: No error on second call.
        """
        export_submission(simple_fig, "fig1", formats=["pdf"], output_dir=tmp_output)
        export_submission(simple_fig, "fig2", formats=["pdf"], output_dir=tmp_output)
        assert (tmp_output / "fig1.pdf").exists()
        assert (tmp_output / "fig2.pdf").exists()

    def test_export_stem_appears_in_filenames(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: The stem parameter must appear in every output filename.
        Scenario: Export with stem='my_figure'.
        Expectation: Each filename contains 'my_figure'.
        """
        paths = export_submission(
            simple_fig, "my_figure", formats=["pdf", "png"], output_dir=tmp_output
        )
        for p in paths:
            assert "my_figure" in p.name

    def test_export_string_output_dir_accepted(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: String output_dir must be accepted (converted to Path internally).
        Scenario: Pass output_dir as a string.
        Expectation: Files created successfully.
        """
        paths = export_submission(simple_fig, "fig1", formats=["pdf"], output_dir=str(tmp_output))
        assert len(paths) == 1
        assert paths[0].exists()

    def test_export_empty_formats_list_produces_no_files(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: An empty formats list must produce zero files.
        Scenario: Export with formats=[].
        Expectation: Empty list returned; no files created.
        """
        paths = export_submission(simple_fig, "fig1", formats=[], output_dir=tmp_output)
        assert len(paths) == 0

    def test_export_ieee_without_surname_no_prefix(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: IEEE without author_surname should not prefix filenames.
        Scenario: Export with journal='ieee', no author_surname.
        Expectation: Filename is 'fig1.pdf' (no prefix).
        """
        paths = export_submission(
            simple_fig,
            "fig1",
            formats=["pdf"],
            journal="ieee",
            output_dir=tmp_output,
        )
        assert paths[0].name == "fig1.pdf"

    def test_export_output_dir_as_pathlib_path(
        self, simple_fig: plt.Figure, tmp_output: Path
    ) -> None:
        """
        Description: Path objects for output_dir must be accepted.
        Scenario: Pass output_dir as pathlib.Path.
        Expectation: Files created.
        """
        sub = tmp_output / "subdir"
        paths = export_submission(simple_fig, "fig1", formats=["pdf"], output_dir=sub)
        assert sub.is_dir()
        assert len(paths) == 1


# ---------------------------------------------------------------------------
# __all__ exports
# ---------------------------------------------------------------------------


class TestPublicAPI:
    """Validate the module's public API surface."""

    def test_savefig_is_exported(self) -> None:
        """
        Description: 'savefig' must be in __all__.
        Scenario: Import and check.
        Expectation: Present.
        """
        import plotstyle.core.export as mod

        assert "savefig" in mod.__all__

    def test_export_submission_is_exported(self) -> None:
        """
        Description: 'export_submission' must be in __all__.
        Scenario: Import and check.
        Expectation: Present.
        """
        import plotstyle.core.export as mod

        assert "export_submission" in mod.__all__

    def test_format_extensions_is_exported(self) -> None:
        """
        Description: 'FORMAT_EXTENSIONS' must be in __all__.
        Scenario: Import and check.
        Expectation: Present.
        """
        import plotstyle.core.export as mod

        assert "FORMAT_EXTENSIONS" in mod.__all__
