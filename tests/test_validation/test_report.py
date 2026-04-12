"""Comprehensive test suite for plotstyle.validation.report.

Covers: CheckStatus enum, CheckResult dataclass, and ValidationReport —
including construction, convenience properties, serialisation, and __str__.
"""

from __future__ import annotations

import json

import pytest

from plotstyle.validation.report import (
    _STATUS_ICONS,
    _TABLE_MIN_WIDTH,
    CheckResult,
    CheckStatus,
    ValidationReport,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pass_result() -> CheckResult:
    """A PASS CheckResult for reuse across multiple tests."""
    return CheckResult(
        status=CheckStatus.PASS,
        check_name="dimensions.width",
        message="Figure width 89.0mm matches single column spec.",
    )


@pytest.fixture
def fail_result() -> CheckResult:
    """A FAIL CheckResult with a fix suggestion."""
    return CheckResult(
        status=CheckStatus.FAIL,
        check_name="export.pdf_fonttype",
        message="pdf.fonttype = 3; must be 42.",
        fix_suggestion="Set mpl.rcParams['pdf.fonttype'] = 42.",
    )


@pytest.fixture
def warn_result() -> CheckResult:
    """A WARN CheckResult."""
    return CheckResult(
        status=CheckStatus.WARN,
        check_name="color.sole_differentiator",
        message="Colour is the only differentiator.",
        fix_suggestion="Add distinct markers.",
    )


@pytest.fixture
def empty_report() -> ValidationReport:
    """A ValidationReport with no check results."""
    return ValidationReport(journal="Test Journal", checks=[])


@pytest.fixture
def passing_report(pass_result: CheckResult) -> ValidationReport:
    """A ValidationReport with only PASS results."""
    return ValidationReport(
        journal="Nature",
        checks=[pass_result],
    )


@pytest.fixture
def failing_report(pass_result: CheckResult, fail_result: CheckResult) -> ValidationReport:
    """A ValidationReport with one PASS and one FAIL."""
    return ValidationReport(journal="IEEE", checks=[pass_result, fail_result])


@pytest.fixture
def mixed_report(
    pass_result: CheckResult,
    fail_result: CheckResult,
    warn_result: CheckResult,
) -> ValidationReport:
    """A ValidationReport with PASS, FAIL, and WARN results."""
    return ValidationReport(
        journal="Science",
        checks=[pass_result, fail_result, warn_result],
    )


# ---------------------------------------------------------------------------
# CheckStatus
# ---------------------------------------------------------------------------


class TestCheckStatus:
    """Validate the CheckStatus enum members and values."""

    def test_has_pass_member(self) -> None:
        """
        Description: CheckStatus must have a PASS member for successful checks.
        Scenario: Access CheckStatus.PASS.
        Expectation: No AttributeError; value is 'PASS'.
        """
        assert CheckStatus.PASS.value == "PASS"

    def test_has_fail_member(self) -> None:
        """
        Description: CheckStatus must have a FAIL member for failed checks.
        Scenario: Access CheckStatus.FAIL.
        Expectation: No AttributeError; value is 'FAIL'.
        """
        assert CheckStatus.FAIL.value == "FAIL"

    def test_has_warn_member(self) -> None:
        """
        Description: CheckStatus must have a WARN member for advisory checks.
        Scenario: Access CheckStatus.WARN.
        Expectation: No AttributeError; value is 'WARN'.
        """
        assert CheckStatus.WARN.value == "WARN"

    def test_exactly_three_members(self) -> None:
        """
        Description: The enum must have exactly three members (PASS, FAIL, WARN)
        — adding new statuses is a breaking change and should be deliberate.
        Scenario: Count enum members.
        Expectation: len == 3.
        """
        assert len(list(CheckStatus)) == 3

    @pytest.mark.parametrize(
        "status, expected_value",
        [
            (CheckStatus.PASS, "PASS"),
            (CheckStatus.FAIL, "FAIL"),
            (CheckStatus.WARN, "WARN"),
        ],
    )
    def test_value_is_uppercase_string(self, status: CheckStatus, expected_value: str) -> None:
        """
        Description: Each CheckStatus value must be the UPPERCASE string form
        used in JSON serialisation and to_dict output.
        Scenario: Compare status.value to expected uppercase string.
        Expectation: Equals the expected value.
        """
        assert status.value == expected_value

    def test_status_icons_covers_all_members(self) -> None:
        """
        Description: _STATUS_ICONS must have an entry for every CheckStatus member
        so that __str__ never raises a KeyError.
        Scenario: Check that every member has an entry in _STATUS_ICONS.
        Expectation: All three members appear as keys.
        """
        for member in CheckStatus:
            assert member in _STATUS_ICONS


# ---------------------------------------------------------------------------
# CheckResult
# ---------------------------------------------------------------------------


class TestCheckResult:
    """Validate CheckResult construction, properties, and immutability."""

    def test_status_attribute_stored(self, pass_result: CheckResult) -> None:
        """
        Description: CheckResult.status must store the provided CheckStatus.
        Scenario: Inspect pass_result.status.
        Expectation: CheckStatus.PASS.
        """
        assert pass_result.status is CheckStatus.PASS

    def test_check_name_attribute_stored(self, pass_result: CheckResult) -> None:
        """
        Description: check_name must be stored verbatim for use as a stable key.
        Scenario: Inspect pass_result.check_name.
        Expectation: 'dimensions.width'.
        """
        assert pass_result.check_name == "dimensions.width"

    def test_message_attribute_stored(self, pass_result: CheckResult) -> None:
        """
        Description: message must be stored exactly as provided.
        Scenario: Inspect pass_result.message.
        Expectation: Non-empty string matching the constructor argument.
        """
        assert "89.0" in pass_result.message

    def test_fix_suggestion_defaults_to_none(self, pass_result: CheckResult) -> None:
        """
        Description: fix_suggestion must default to None for PASS results since
        no corrective action is needed.
        Scenario: Inspect pass_result.fix_suggestion.
        Expectation: None.
        """
        assert pass_result.fix_suggestion is None

    def test_fix_suggestion_stored_when_provided(self, fail_result: CheckResult) -> None:
        """
        Description: fix_suggestion must store the provided string when given.
        Scenario: Inspect fail_result.fix_suggestion.
        Expectation: Non-empty string.
        """
        assert fail_result.fix_suggestion is not None
        assert len(fail_result.fix_suggestion) > 0

    def test_is_failure_true_for_fail_status(self, fail_result: CheckResult) -> None:
        """
        Description: is_failure must return True only for FAIL results.
        Scenario: Check fail_result.is_failure.
        Expectation: True.
        """
        assert fail_result.is_failure is True

    def test_is_failure_false_for_pass_status(self, pass_result: CheckResult) -> None:
        """
        Description: is_failure must return False for PASS results.
        Scenario: Check pass_result.is_failure.
        Expectation: False.
        """
        assert pass_result.is_failure is False

    def test_is_failure_false_for_warn_status(self, warn_result: CheckResult) -> None:
        """
        Description: is_failure must return False for WARN results; warnings
        do not constitute failures.
        Scenario: Check warn_result.is_failure.
        Expectation: False.
        """
        assert warn_result.is_failure is False

    def test_is_warning_true_for_warn_status(self, warn_result: CheckResult) -> None:
        """
        Description: is_warning must return True for WARN results.
        Scenario: Check warn_result.is_warning.
        Expectation: True.
        """
        assert warn_result.is_warning is True

    def test_is_warning_false_for_pass_status(self, pass_result: CheckResult) -> None:
        """
        Description: is_warning must return False for PASS results.
        Scenario: Check pass_result.is_warning.
        Expectation: False.
        """
        assert pass_result.is_warning is False

    def test_is_warning_false_for_fail_status(self, fail_result: CheckResult) -> None:
        """
        Description: is_warning must return False for FAIL results; failures
        are distinct from warnings.
        Scenario: Check fail_result.is_warning.
        Expectation: False.
        """
        assert fail_result.is_warning is False

    def test_result_fields_are_readable(self, pass_result: CheckResult) -> None:
        """
        Description: All CheckResult fields must be readable via attribute
        access (basic sanity check for the slots=True dataclass).
        Scenario: Access every field on pass_result.
        Expectation: No AttributeError; values match constructor arguments.
        """
        assert pass_result.status is CheckStatus.PASS
        assert isinstance(pass_result.check_name, str)
        assert isinstance(pass_result.message, str)
        # fix_suggestion is None for PASS results
        assert pass_result.fix_suggestion is None

    def test_result_can_be_mutated(self, pass_result: CheckResult) -> None:
        """
        Description: CheckResult is a slots=True dataclass (not frozen), so
        field mutation is technically allowed.  This test documents the current
        behaviour; do not rely on mutability in production code.
        Scenario: Assign a new status to pass_result.
        Expectation: Assignment succeeds without raising.
        """
        pass_result.status = CheckStatus.WARN
        assert pass_result.status is CheckStatus.WARN

    @pytest.mark.parametrize(
        "status",
        [CheckStatus.PASS, CheckStatus.FAIL, CheckStatus.WARN],
    )
    def test_all_statuses_can_be_constructed(self, status: CheckStatus) -> None:
        """
        Description: All three statuses must be usable in CheckResult so that
        check functions can return any outcome.
        Scenario: Construct CheckResult for each status.
        Expectation: No exception; result.status == status.
        """
        r = CheckResult(status=status, check_name="test.check", message="msg")
        assert r.status is status


# ---------------------------------------------------------------------------
# ValidationReport — properties
# ---------------------------------------------------------------------------


class TestValidationReportProperties:
    """Validate ValidationReport.passed, failures, and warnings properties."""

    def test_passed_true_when_no_checks(self, empty_report: ValidationReport) -> None:
        """
        Description: A report with no checks performed must pass by default —
        absence of evidence is not evidence of failure.
        Scenario: Empty report.passed.
        Expectation: True.
        """
        assert empty_report.passed is True

    def test_passed_true_for_all_pass_results(self, passing_report: ValidationReport) -> None:
        """
        Description: A report with only PASS results must have passed == True.
        Scenario: Inspect passing_report.passed.
        Expectation: True.
        """
        assert passing_report.passed is True

    def test_passed_false_when_any_failure(self, failing_report: ValidationReport) -> None:
        """
        Description: A single FAIL result must cause passed == False.
        Scenario: failing_report contains one FAIL.
        Expectation: False.
        """
        assert failing_report.passed is False

    def test_passed_true_when_only_warnings(self, warn_result: CheckResult) -> None:
        """
        Description: WARN results must NOT affect the passed outcome; warnings
        are advisory and do not constitute failures.
        Scenario: Report with only one WARN.
        Expectation: passed == True.
        """
        report = ValidationReport(journal="J", checks=[warn_result])
        assert report.passed is True

    def test_failures_returns_empty_when_no_failures(
        self, passing_report: ValidationReport
    ) -> None:
        """
        Description: failures must return an empty list when all checks pass.
        Scenario: All-PASS report.
        Expectation: failures == [].
        """
        assert passing_report.failures == []

    def test_failures_returns_only_fail_results(self, mixed_report: ValidationReport) -> None:
        """
        Description: failures must include only FAIL results, excluding PASS
        and WARN, so callers can iterate just the actionable items.
        Scenario: mixed_report with PASS + FAIL + WARN.
        Expectation: len(failures) == 1 and status is FAIL.
        """
        failures = mixed_report.failures
        assert len(failures) == 1
        assert all(r.is_failure for r in failures)

    def test_warnings_returns_empty_when_no_warnings(
        self, failing_report: ValidationReport
    ) -> None:
        """
        Description: warnings must return an empty list when no WARN results
        are present.
        Scenario: Report with PASS and FAIL but no WARN.
        Expectation: warnings == [].
        """
        assert failing_report.warnings == []

    def test_warnings_returns_only_warn_results(self, mixed_report: ValidationReport) -> None:
        """
        Description: warnings must include only WARN results.
        Scenario: mixed_report.
        Expectation: len(warnings) == 1 and all are WARN.
        """
        warns = mixed_report.warnings
        assert len(warns) == 1
        assert all(r.is_warning for r in warns)

    def test_checks_preserves_order(self) -> None:
        """
        Description: The checks list must preserve insertion order so that
        the report always displays results in a predictable sequence.
        Scenario: Build report with known order of check names.
        Expectation: checks list order matches construction order.
        """
        names = ["a.check", "b.check", "c.check"]
        checks = [CheckResult(CheckStatus.PASS, n, f"msg {n}") for n in names]
        report = ValidationReport(journal="J", checks=checks)
        assert [c.check_name for c in report.checks] == names

    def test_journal_attribute_stored(self, passing_report: ValidationReport) -> None:
        """
        Description: ValidationReport.journal must store the journal display name.
        Scenario: Inspect passing_report.journal.
        Expectation: 'Nature'.
        """
        assert passing_report.journal == "Nature"


# ---------------------------------------------------------------------------
# ValidationReport — to_dict
# ---------------------------------------------------------------------------


class TestValidationReportToDict:
    """Validate to_dict() output structure and JSON-serializability."""

    def test_to_dict_contains_journal_key(self, passing_report: ValidationReport) -> None:
        """
        Description: to_dict result must have a 'journal' key for downstream
        logging and API consumers.
        Scenario: Call passing_report.to_dict().
        Expectation: 'journal' in result.
        """
        d = passing_report.to_dict()
        assert "journal" in d

    def test_to_dict_journal_value(self, passing_report: ValidationReport) -> None:
        """
        Description: to_dict['journal'] must match the report's journal attribute.
        Scenario: Compare to_dict()['journal'] against report.journal.
        Expectation: Equal.
        """
        d = passing_report.to_dict()
        assert d["journal"] == passing_report.journal

    def test_to_dict_contains_passed_key(self, passing_report: ValidationReport) -> None:
        """
        Description: to_dict must include 'passed' so consumers can determine
        the overall outcome without re-computing it.
        Scenario: Inspect to_dict result.
        Expectation: 'passed' key present with bool value.
        """
        d = passing_report.to_dict()
        assert "passed" in d
        assert isinstance(d["passed"], bool)

    def test_to_dict_passed_value_consistent(self, failing_report: ValidationReport) -> None:
        """
        Description: to_dict['passed'] must equal report.passed at call time.
        Scenario: failing_report whose passed == False.
        Expectation: to_dict()['passed'] == False.
        """
        d = failing_report.to_dict()
        assert d["passed"] is failing_report.passed

    def test_to_dict_contains_checks_list(self, passing_report: ValidationReport) -> None:
        """
        Description: to_dict must include a 'checks' list with one entry per
        CheckResult.
        Scenario: Call to_dict on a one-check report.
        Expectation: 'checks' is a list of length 1.
        """
        d = passing_report.to_dict()
        assert "checks" in d
        assert isinstance(d["checks"], list)
        assert len(d["checks"]) == len(passing_report.checks)

    def test_to_dict_check_entry_has_required_keys(self, pass_result: CheckResult) -> None:
        """
        Description: Each checks entry must have status, check_name, message,
        and fix_suggestion keys for complete downstream processing.
        Scenario: Inspect first entry in to_dict()['checks'].
        Expectation: All four keys present.
        """
        report = ValidationReport(journal="J", checks=[pass_result])
        entry = report.to_dict()["checks"][0]
        for key in ("status", "check_name", "message", "fix_suggestion"):
            assert key in entry, f"Missing key: {key}"

    def test_to_dict_status_is_string(self, pass_result: CheckResult) -> None:
        """
        Description: to_dict status values must be strings (not enum instances)
        for JSON serialization compatibility.
        Scenario: Check type of status in first checks entry.
        Expectation: str.
        """
        report = ValidationReport(journal="J", checks=[pass_result])
        entry = report.to_dict()["checks"][0]
        assert isinstance(entry["status"], str)

    def test_to_dict_is_json_serializable(self, mixed_report: ValidationReport) -> None:
        """
        Description: to_dict output must be JSON-serializable with no custom
        encoder, since callers may log or transmit it.
        Scenario: json.dumps(mixed_report.to_dict()).
        Expectation: No TypeError; returns a string.
        """
        serialized = json.dumps(mixed_report.to_dict())
        assert isinstance(serialized, str)

    def test_to_dict_fix_suggestion_none_for_pass(self, pass_result: CheckResult) -> None:
        """
        Description: PASS checks have no fix_suggestion; to_dict must serialize
        this as None (not omit the key) for predictable consumer behaviour.
        Scenario: PASS result with fix_suggestion=None.
        Expectation: entry['fix_suggestion'] is None.
        """
        report = ValidationReport(journal="J", checks=[pass_result])
        entry = report.to_dict()["checks"][0]
        assert entry["fix_suggestion"] is None

    def test_to_dict_empty_checks_produces_empty_list(self, empty_report: ValidationReport) -> None:
        """
        Description: An empty report must produce an empty 'checks' list in
        to_dict, not None or a missing key.
        Scenario: empty_report.to_dict().
        Expectation: d['checks'] == [].
        """
        d = empty_report.to_dict()
        assert d["checks"] == []


# ---------------------------------------------------------------------------
# ValidationReport — __str__
# ---------------------------------------------------------------------------


class TestValidationReportStr:
    """Validate the __str__ box-drawing table output."""

    def test_str_returns_string(self, passing_report: ValidationReport) -> None:
        """
        Description: str(report) must return a str — not bytes or None.
        Scenario: Convert passing_report to string.
        Expectation: isinstance(str(report), str).
        """
        assert isinstance(str(passing_report), str)

    def test_str_contains_journal_name(self, passing_report: ValidationReport) -> None:
        """
        Description: The report table header must include the journal name so it
        is self-describing when printed to a terminal.
        Scenario: Inspect str(passing_report).
        Expectation: 'Nature' in the string.
        """
        assert "Nature" in str(passing_report)

    def test_str_contains_summary_line(self, passing_report: ValidationReport) -> None:
        """
        Description: The last line of the string must summarise pass/fail counts
        so the user gets an at-a-glance verdict.
        Scenario: Inspect the last line of str(passing_report).
        Expectation: 'checks passed' in the last line.
        """
        last_line = str(passing_report).splitlines()[-1]
        assert "checks passed" in last_line

    def test_str_contains_check_name(self, passing_report: ValidationReport) -> None:
        """
        Description: Each check result's message must appear somewhere in the
        rendered table so the user can see all check outcomes.
        Scenario: Check that dimensions.width message is in the string.
        Expectation: At least part of the message is present.
        """
        rendered = str(passing_report)
        assert "89.0" in rendered or "dimensions" in rendered or "width" in rendered

    def test_str_minimum_width_respected(self, empty_report: ValidationReport) -> None:
        """
        Description: The box-drawing table lines must be at least _TABLE_MIN_WIDTH
        characters wide even when the journal name is very short.
        Note: The trailing summary line (e.g. '0/0 checks passed ...') is a
        plain-text footer and is intentionally shorter.
        Scenario: Check box border lines (starting with '┌', '├', '└', '│').
        Expectation: Every box-drawing line is >= _TABLE_MIN_WIDTH characters.
        """
        box_prefixes = ("┌", "├", "└", "│")
        lines = str(empty_report).splitlines()
        # Last line is the summary footer — skip it
        box_lines = [ln for ln in lines[:-1] if ln.startswith(box_prefixes)]
        for line in box_lines:
            assert len(line) >= _TABLE_MIN_WIDTH, (
                f"Line too short ({len(line)} < {_TABLE_MIN_WIDTH}): {line!r}"
            )

    def test_str_long_message_is_truncated(self) -> None:
        """
        Description: Long messages must be truncated with '...' to prevent
        line wrapping that breaks the ASCII box-drawing table.
        Scenario: Create a CheckResult with 200-character message.
        Expectation: No line exceeds a reasonable width; '...' in output.
        """
        long_msg = "x" * 200
        r = CheckResult(CheckStatus.FAIL, "test.name", long_msg)
        report = ValidationReport(journal="J", checks=[r])
        rendered = str(report)
        assert "..." in rendered

    def test_str_fail_count_correct(self, failing_report: ValidationReport) -> None:
        """
        Description: The summary line must report the correct failure count.
        Scenario: failing_report has 1 failure.
        Expectation: '1 failure' in the summary line.
        """
        last_line = str(failing_report).splitlines()[-1]
        assert "1 failure" in last_line

    def test_str_warn_count_correct(self, mixed_report: ValidationReport) -> None:
        """
        Description: The summary line must report the correct warning count.
        Scenario: mixed_report has 1 warning.
        Expectation: '1 warning' in the summary line.
        """
        last_line = str(mixed_report).splitlines()[-1]
        assert "1 warning" in last_line

    def test_str_empty_report_shows_zero_checks(self, empty_report: ValidationReport) -> None:
        """
        Description: An empty report must show 0/0 in the summary line.
        Scenario: str(empty_report) summary line.
        Expectation: '0/0' in the last line.
        """
        last_line = str(empty_report).splitlines()[-1]
        assert "0/0" in last_line


# ---------------------------------------------------------------------------
# ValidationReport — edge cases
# ---------------------------------------------------------------------------


class TestValidationReportEdgeCases:
    """Validate boundary and edge-case behaviour of ValidationReport."""

    def test_report_with_many_checks(self) -> None:
        """
        Description: A report can hold many checks; all must be iterable in
        failures/warnings/to_dict without index errors.
        Scenario: Create report with 20 PASS checks.
        Expectation: passed == True; len(failures) == 0.
        """
        checks = [CheckResult(CheckStatus.PASS, f"check.{i}", f"Message {i}") for i in range(20)]
        report = ValidationReport(journal="J", checks=checks)
        assert report.passed is True
        assert len(report.failures) == 0

    def test_report_with_all_failures(self) -> None:
        """
        Description: A report where every check fails must have passed == False
        and len(failures) == len(checks).
        Scenario: 5 FAIL results.
        Expectation: passed False; failures has all 5.
        """
        checks = [CheckResult(CheckStatus.FAIL, f"check.{i}", "fail") for i in range(5)]
        report = ValidationReport(journal="J", checks=checks)
        assert report.passed is False
        assert len(report.failures) == 5

    def test_default_checks_is_empty_list(self) -> None:
        """
        Description: ValidationReport must default checks to an empty list (not
        None) to avoid AttributeError on property access.
        Scenario: Construct with only journal argument.
        Expectation: report.checks == [].
        """
        report = ValidationReport(journal="J")
        assert report.checks == []

    def test_journal_with_unicode_name_renders(self) -> None:
        """
        Description: Unicode journal names (e.g. containing accented characters)
        must not cause str() to raise an encoding error.
        Scenario: Create report with journal='Physique Revue Étude'.
        Expectation: str() returns a string without error.
        """
        report = ValidationReport(journal="Physique Revue Étude")
        rendered = str(report)
        assert "Physique" in rendered
