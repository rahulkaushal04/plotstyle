"""Comprehensive test suite for plotstyle.cli.main.

Covers: _build_parser, _cmd_list, _cmd_info, _cmd_diff, _cmd_fonts,
_cmd_validate, _cmd_export, and main() dispatch — including happy paths,
unknown journals, missing files, and argument-validation edge cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from plotstyle.cli.main import (
    _INFO_SEPARATOR,
    _LIST_NAME_WIDTH,
    _PANEL_LABEL_EXAMPLES,
    _build_parser,
    _cmd_export,
    _cmd_info,
    _cmd_list,
    _cmd_validate,
    main,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def nature_pdf(tmp_path: Path) -> Path:
    """Write a minimal (non-PDF-spec-compliant) PDF-suffixed file."""
    p = tmp_path / "figure.pdf"
    p.write_bytes(b"%PDF-1.4 fake content for testing")
    return p


@pytest.fixture
def non_pdf_figure(tmp_path: Path) -> Path:
    """Write a dummy PNG file for non-PDF validation path testing."""
    p = tmp_path / "figure.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    return p


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Validate module-level constants are correctly defined."""

    def test_list_name_width_is_positive_int(self) -> None:
        """
        Description: _LIST_NAME_WIDTH controls column alignment in 'plotstyle list'.
        Scenario: Inspect the constant.
        Expectation: Positive integer.
        """
        assert isinstance(_LIST_NAME_WIDTH, int)
        assert _LIST_NAME_WIDTH > 0

    def test_info_separator_is_non_empty_string(self) -> None:
        """
        Description: _INFO_SEPARATOR is a visual divider line used in 'plotstyle info'.
        Scenario: Inspect the constant.
        Expectation: Non-empty string.
        """
        assert isinstance(_INFO_SEPARATOR, str)
        assert len(_INFO_SEPARATOR) > 0

    def test_panel_label_examples_contains_expected_keys(self) -> None:
        """
        Description: _PANEL_LABEL_EXAMPLES must cover the four canonical
        panel-label-case values from the journal spec schema.
        Scenario: Check that lower, upper, parens_lower, parens_upper are present.
        Expectation: All four keys exist in the dict.
        """
        for key in ("lower", "upper", "parens_lower", "parens_upper"):
            assert key in _PANEL_LABEL_EXAMPLES, f"Missing key: {key}"

    def test_panel_label_examples_values_are_non_empty_strings(self) -> None:
        """
        Description: Every example value must be a non-empty string.
        Scenario: Iterate over all values in _PANEL_LABEL_EXAMPLES.
        Expectation: All values are non-empty str.
        """
        for val in _PANEL_LABEL_EXAMPLES.values():
            assert isinstance(val, str)
            assert len(val) > 0


# ---------------------------------------------------------------------------
# _build_parser
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Validate that _build_parser() produces a correctly configured parser."""

    def test_returns_argument_parser(self) -> None:
        """
        Description: _build_parser() must return an ArgumentParser so that
        argument parsing can be tested independently of main().
        Scenario: Call _build_parser() with no arguments.
        Expectation: Returns ArgumentParser instance.
        """
        import argparse

        parser = _build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_prog_name_is_plotstyle(self) -> None:
        """
        Description: The program name in the parser must be 'plotstyle' to
        match the console-script entry point.
        Scenario: Inspect parser.prog.
        Expectation: 'plotstyle'.
        """
        parser = _build_parser()
        assert parser.prog == "plotstyle"

    @pytest.mark.parametrize(
        "subcommand",
        ["list", "info", "diff", "fonts", "validate", "export"],
    )
    def test_all_subcommands_are_registered(self, subcommand: str) -> None:
        """
        Description: Each sub-command that main() dispatches must be parseable
        without raising SystemExit.
        Scenario: Parse a minimal valid invocation of each sub-command.
        Expectation: No SystemExit; args.command == subcommand.
        """
        parser = _build_parser()
        # Construct a minimal argv that satisfies required positional/keyword args.
        argv_map = {
            "list": ["list"],
            "info": ["info", "nature"],
            "diff": ["diff", "nature", "ieee"],
            "fonts": ["fonts", "--journal", "ieee"],
            "validate": ["validate", "fig.pdf", "--journal", "nature"],
            "export": ["export", "fig.png", "--journal", "ieee"],
        }
        args = parser.parse_args(argv_map[subcommand])
        assert args.command == subcommand

    def test_no_subcommand_sets_command_to_none(self) -> None:
        """
        Description: Parsing an empty argv must set args.command to None so
        that main() can print help and return 1.
        Scenario: parse_args([]).
        Expectation: args.command is None.
        """
        parser = _build_parser()
        args = parser.parse_args([])
        assert args.command is None


# ---------------------------------------------------------------------------
# main() dispatch and return codes
# ---------------------------------------------------------------------------


class TestMainDispatch:
    """Validate the return codes and error handling of main()."""

    def test_no_args_returns_one(self, capsys) -> None:
        """
        Description: main([]) must return 1 to indicate no sub-command was
        given; the exit code is used by shell scripts and CI pipelines.
        Scenario: Call main with empty argv.
        Expectation: Returns 1.
        """
        result = main([])
        assert result == 1

    def test_list_returns_zero(self, capsys) -> None:
        """
        Description: 'plotstyle list' must return 0 on success when the
        default spec registry is accessible.
        Scenario: main(["list"]).
        Expectation: Returns 0.
        """
        result = main(["list"])
        assert result == 0

    def test_list_output_contains_known_journals(self, capsys) -> None:
        """
        Description: 'plotstyle list' must print at least the known built-in
        journal identifiers so that users can discover available presets.
        Scenario: Capture stdout from main(["list"]).
        Expectation: 'nature' and 'ieee' appear in stdout.
        """
        main(["list"])
        out = capsys.readouterr().out
        assert "nature" in out
        assert "ieee" in out

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_info_known_journal_returns_zero(self, capsys) -> None:
        """
        Description: 'plotstyle info <journal>' must return 0 for a registered
        journal so that CI scripts can use the exit code for validation.
        Scenario: main(["info", "nature"]).
        Expectation: Returns 0.
        """
        result = main(["info", "nature"])
        assert result == 0

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_info_output_contains_journal_name(self, capsys) -> None:
        """
        Description: 'plotstyle info' output must include the journal's display
        name so the user can confirm they are viewing the right spec.
        Scenario: Capture stdout from main(["info", "nature"]).
        Expectation: 'Nature' appears in stdout.
        """
        main(["info", "nature"])
        out = capsys.readouterr().out
        assert "Nature" in out

    def test_info_unknown_journal_returns_one(self, capsys) -> None:
        """
        Description: 'plotstyle info <unknown>' must return 1 and print to
        stderr when the journal is not registered.
        Scenario: main(["info", "__no_such_journal__"]).
        Expectation: Returns 1; error text appears in stderr.
        """
        result = main(["info", "__no_such_journal__"])
        assert result == 1
        err = capsys.readouterr().err
        assert "unknown journal" in err.lower()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_diff_known_journals_returns_zero(self, capsys) -> None:
        """
        Description: 'plotstyle diff <a> <b>' must return 0 for two registered
        journals — this is a key discoverability feature.
        Scenario: main(["diff", "nature", "ieee"]).
        Expectation: Returns 0.
        """
        result = main(["diff", "nature", "ieee"])
        assert result == 0

    def test_diff_unknown_first_journal_returns_one(self, capsys) -> None:
        """
        Description: 'plotstyle diff' with an unregistered first journal must
        return 1 with an error on stderr.
        Scenario: main(["diff", "__ghost__", "ieee"]).
        Expectation: Returns 1.
        """
        result = main(["diff", "__ghost__", "ieee"])
        assert result == 1

    def test_diff_unknown_second_journal_returns_one(self, capsys) -> None:
        """
        Description: 'plotstyle diff' with an unregistered second journal must
        return 1.
        Scenario: main(["diff", "nature", "__ghost__"]).
        Expectation: Returns 1.
        """
        result = main(["diff", "nature", "__ghost__"])
        assert result == 1

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_fonts_known_journal_returns_zero(self, capsys) -> None:
        """
        Description: 'plotstyle fonts --journal <journal>' must return 0 for a
        registered journal regardless of whether its preferred font is installed.
        Scenario: main(["fonts", "--journal", "ieee"]).
        Expectation: Returns 0.
        """
        result = main(["fonts", "--journal", "ieee"])
        assert result == 0

    def test_fonts_unknown_journal_returns_one(self, capsys) -> None:
        """
        Description: 'plotstyle fonts' with unknown journal must return 1.
        Scenario: main(["fonts", "--journal", "__ghost__"]).
        Expectation: Returns 1.
        """
        result = main(["fonts", "--journal", "__ghost__"])
        assert result == 1

    def test_validate_missing_file_returns_one(self, capsys) -> None:
        """
        Description: 'plotstyle validate' with a non-existent file must return
        1 and print an error to stderr.
        Scenario: Pass a path that does not exist.
        Expectation: Returns 1; 'not found' in stderr.
        """
        result = main(["validate", "/tmp/does_not_exist_xyz.pdf", "--journal", "nature"])
        assert result == 1
        err = capsys.readouterr().err
        assert "not found" in err.lower() or "error" in err.lower()

    def test_validate_non_pdf_file_returns_zero(self, capsys, non_pdf_figure: Path) -> None:
        """
        Description: 'plotstyle validate' on a non-PDF file (PNG) must return 0
        and print informational output about the non-PDF format.
        Scenario: Pass a PNG file with journal='nature'.
        Expectation: Returns 0.
        """
        result = main(["validate", str(non_pdf_figure), "--journal", "nature"])
        assert result == 0

    def test_validate_pdf_no_type3_returns_zero(self, capsys, nature_pdf: Path) -> None:
        """
        Description: 'plotstyle validate' on a PDF file that has no Type 3
        fonts (mocked) must return 0 and print a PASS message.
        Scenario: Mock verify_embedded to return an empty list (no fonts found).
        Expectation: Returns 0; '✓ PASS' or 'PASS' in stdout.
        """
        with patch("plotstyle.engine.fonts.verify_embedded", return_value=[]):
            result = main(["validate", str(nature_pdf), "--journal", "nature"])
        assert result == 0
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_validate_pdf_type3_found_prints_fail(self, capsys, nature_pdf: Path) -> None:
        """
        Description: When verify_embedded reports a Type 3 font, validate must
        print a FAIL message to alert the user.
        Scenario: Mock verify_embedded to return a Type3 font entry.
        Expectation: Returns 0 (info command); 'FAIL' in stdout.
        """
        with patch(
            "plotstyle.engine.fonts.verify_embedded",
            return_value=[{"type": "Type3", "name": "Helvetica"}],
        ):
            result = main(["validate", str(nature_pdf), "--journal", "nature"])
        assert result == 0
        out = capsys.readouterr().out
        assert "FAIL" in out

    def test_validate_unknown_journal_returns_one(self, capsys, non_pdf_figure: Path) -> None:
        """
        Description: An unknown journal in 'plotstyle validate' must return 1.
        Scenario: Pass an existing file but an unregistered journal.
        Expectation: Returns 1.
        """
        result = main(["validate", str(non_pdf_figure), "--journal", "__ghost__"])
        assert result == 1

    def test_export_returns_zero(self, capsys, non_pdf_figure: Path) -> None:
        """
        Description: 'plotstyle export' always returns 0 (guidance message)
        regardless of the file or journal, since it cannot perform the actual
        export without a live Figure object.
        Scenario: main(["export", "fig.png", "--journal", "ieee"]).
        Expectation: Returns 0.
        """
        result = main(["export", str(non_pdf_figure), "--journal", "ieee"])
        assert result == 0

    def test_export_output_contains_python_snippet(self, capsys, non_pdf_figure: Path) -> None:
        """
        Description: 'plotstyle export' must print an example Python snippet
        so the user knows how to re-export from within Python.
        Scenario: Capture stdout from export command.
        Expectation: 'import plotstyle' or 'export_submission' in stdout.
        """
        main(["export", str(non_pdf_figure), "--journal", "ieee"])
        out = capsys.readouterr().out
        assert "plotstyle" in out


# ---------------------------------------------------------------------------
# _cmd_list
# ---------------------------------------------------------------------------


class TestCmdList:
    """Validate _cmd_list() directly."""

    def test_returns_zero(self, capsys) -> None:
        """
        Description: _cmd_list() must always return 0 since listing the
        registry cannot fail if the package is installed correctly.
        Scenario: Call _cmd_list() directly.
        Expectation: Returns 0.
        """
        assert _cmd_list() == 0

    def test_prints_at_least_one_journal(self, capsys) -> None:
        """
        Description: The listing must include at least one journal so it is
        not empty (the package ships built-in specs).
        Scenario: Capture stdout from _cmd_list().
        Expectation: stdout is non-empty.
        """
        _cmd_list()
        out = capsys.readouterr().out
        assert len(out.strip()) > 0

    def test_output_contains_publisher_info(self, capsys) -> None:
        """
        Description: Each line should contain a journal name and publisher;
        verify the Nature entry contains 'Springer Nature'.
        Scenario: Look for 'Springer' in the 'nature' line of output.
        Expectation: 'Springer' appears in stdout.
        """
        _cmd_list()
        out = capsys.readouterr().out
        assert "Springer" in out


# ---------------------------------------------------------------------------
# _cmd_info
# ---------------------------------------------------------------------------


class TestCmdInfo:
    """Validate _cmd_info() for known journals and error cases."""

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_returns_zero_for_nature(self, capsys) -> None:
        """
        Description: _cmd_info() must return 0 for a valid, registered journal.
        Scenario: Call _cmd_info("nature").
        Expectation: Returns 0.
        """
        assert _cmd_info("nature") == 0

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_output_contains_dimensions_section(self, capsys) -> None:
        """
        Description: The info output must include a Dimensions section so the
        user can see column widths at a glance.
        Scenario: Capture stdout from _cmd_info("nature").
        Expectation: 'Dimensions' or 'column' in stdout.
        """
        _cmd_info("nature")
        out = capsys.readouterr().out
        assert "Dimensions" in out or "column" in out.lower()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_output_contains_typography_section(self, capsys) -> None:
        """
        Description: The info output must include typography information.
        Scenario: Capture stdout from _cmd_info("ieee").
        Expectation: 'Typography' or 'Font' in stdout.
        """
        _cmd_info("ieee")
        out = capsys.readouterr().out
        assert "Typography" in out or "Font" in out

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_output_contains_export_section(self, capsys) -> None:
        """
        Description: The info output must include export requirements (DPI,
        formats, colour space).
        Scenario: Capture stdout from _cmd_info("nature").
        Expectation: 'Export' or 'DPI' in stdout.
        """
        _cmd_info("nature")
        out = capsys.readouterr().out
        assert "Export" in out or "DPI" in out

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    @pytest.mark.parametrize("journal", ["nature", "ieee", "science"])
    def test_known_journals_return_zero(self, journal: str) -> None:
        """
        Description: All built-in journals must produce a successful info
        display with exit code 0.
        Scenario: Call _cmd_info for each known journal.
        Expectation: Returns 0 each time.
        """
        assert _cmd_info(journal) == 0


# ---------------------------------------------------------------------------
# _cmd_validate
# ---------------------------------------------------------------------------


class TestCmdValidate:
    """Validate _cmd_validate() for various file types and conditions."""

    def test_missing_file_returns_one(self, tmp_path: Path, capsys) -> None:
        """
        Description: A non-existent file path must cause _cmd_validate to
        return 1 and emit an error to stderr.
        Scenario: Pass a path that doesn't exist on disk.
        Expectation: Returns 1.
        """
        missing = str(tmp_path / "no_such_file.pdf")
        result = _cmd_validate(missing, "nature")
        assert result == 1
        err = capsys.readouterr().err
        assert "not found" in err.lower() or len(err) > 0

    def test_non_pdf_file_returns_zero(self, non_pdf_figure: Path, capsys) -> None:
        """
        Description: A non-PDF file must return 0 with an informational message
        (font-embedding check only applies to PDF).
        Scenario: Pass a PNG file.
        Expectation: Returns 0; output mentions file format.
        """
        result = _cmd_validate(str(non_pdf_figure), "nature")
        assert result == 0
        out = capsys.readouterr().out
        assert ".png" in out.lower() or "format" in out.lower() or "pdf" in out.lower()

    def test_pdf_no_type3_returns_zero(self, nature_pdf: Path, capsys) -> None:
        """
        Description: A PDF file with no Type 3 fonts must return 0 with a PASS.
        Scenario: Mock verify_embedded to return [].
        Expectation: Returns 0; PASS in stdout.
        """
        with patch("plotstyle.engine.fonts.verify_embedded", return_value=[]):
            result = _cmd_validate(str(nature_pdf), "nature")
        assert result == 0
        out = capsys.readouterr().out
        assert "PASS" in out

    def test_pdf_with_type3_prints_fail(self, nature_pdf: Path, capsys) -> None:
        """
        Description: A PDF file with Type 3 fonts must produce a FAIL message.
        Scenario: Mock verify_embedded to return a Type 3 entry.
        Expectation: 'FAIL' in stdout.
        """
        with patch(
            "plotstyle.engine.fonts.verify_embedded",
            return_value=[{"type": "Type3"}],
        ):
            _cmd_validate(str(nature_pdf), "nature")
        out = capsys.readouterr().out
        assert "FAIL" in out

    def test_output_includes_note_about_full_validation(self, non_pdf_figure: Path, capsys) -> None:
        """
        Description: The validate output must guide users toward full
        programmatic validation so they do not assume CLI gives complete checks.
        Scenario: Capture stdout from _cmd_validate on a PNG.
        Expectation: 'validate' or 'Python' in stdout.
        """
        _cmd_validate(str(non_pdf_figure), "nature")
        out = capsys.readouterr().out
        assert "validate" in out.lower() or "python" in out.lower()


# ---------------------------------------------------------------------------
# _cmd_export
# ---------------------------------------------------------------------------


class TestCmdExport:
    """Validate _cmd_export() informational output."""

    def test_returns_zero(self, capsys) -> None:
        """
        Description: _cmd_export() always returns 0 because it only prints
        guidance — no actual work is performed.
        Scenario: Call with typical arguments.
        Expectation: Returns 0.
        """
        result = _cmd_export("fig.png", "ieee", None, None, ".")
        assert result == 0

    def test_output_contains_journal_name(self, capsys) -> None:
        """
        Description: The export guidance must reference the requested journal
        so the user can construct the correct Python call.
        Scenario: Call with journal='nature'.
        Expectation: 'nature' in stdout.
        """
        _cmd_export("fig.png", "nature", None, None, ".")
        out = capsys.readouterr().out
        assert "nature" in out

    def test_output_references_export_submission(self, capsys) -> None:
        """
        Description: The guidance must mention export_submission so users
        know the correct Python API to call.
        Scenario: Capture stdout from _cmd_export.
        Expectation: 'export_submission' in stdout.
        """
        _cmd_export("fig.png", "nature", None, None, ".")
        out = capsys.readouterr().out
        assert "export_submission" in out


# ---------------------------------------------------------------------------
# main() error message content
# ---------------------------------------------------------------------------


class TestMainErrorMessages:
    """Validate that error messages are actionable and include expected content."""

    def test_unknown_journal_error_mentions_journal_name(self, capsys) -> None:
        """
        Description: The error message for an unknown journal must include the
        journal name so the user can see what they typed wrong.
        Scenario: main(["info", "xyzzy"]).
        Expectation: 'xyzzy' appears in stderr.
        """
        main(["info", "xyzzy"])
        err = capsys.readouterr().err
        assert "xyzzy" in err

    def test_unknown_journal_error_suggests_list_command(self, capsys) -> None:
        """
        Description: The error message must suggest running 'plotstyle list'
        so the user knows how to discover valid journal identifiers.
        Scenario: Trigger a SpecNotFoundError via main().
        Expectation: 'list' appears in stderr.
        """
        main(["info", "nonexistent_journal"])
        err = capsys.readouterr().err
        assert "list" in err

    def test_no_command_prints_help(self, capsys) -> None:
        """
        Description: main([]) must print help content (at minimum the prog name)
        so users know what commands are available.
        Scenario: main([]) with stdout captured.
        Expectation: 'plotstyle' appears in stdout.
        """
        main([])
        out = capsys.readouterr().out
        assert "plotstyle" in out
