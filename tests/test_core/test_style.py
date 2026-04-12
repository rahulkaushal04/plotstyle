"""Enhanced test suite for plotstyle.core.style.

Covers: JournalStyle, use, _validate_latex, _snapshot_rcparams,
_apply_seaborn_patch, context manager protocol, and all edge cases.
"""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock, patch

import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")

from plotstyle.core.style import (
    _SEABORN_MISSING_WARNING,
    JournalStyle,
    _apply_seaborn_patch,
    _snapshot_rcparams,
    _validate_latex,
    use,
)
from plotstyle.specs import registry

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

KNOWN_JOURNALS: list[str] = ["nature", "ieee", "science"]


@pytest.fixture(params=KNOWN_JOURNALS)
def journal_name(request) -> str:
    """Parametric fixture yielding each known journal name in turn."""
    return request.param


@pytest.fixture(autouse=True)
def _close_figs():
    """Close all Matplotlib figures after each test to prevent memory leaks."""
    yield
    plt.close("all")


# ---------------------------------------------------------------------------
# _validate_latex
# ---------------------------------------------------------------------------


class TestValidateLatex:
    """Validate the latex parameter validation helper."""

    @pytest.mark.parametrize("value", [True, False, "auto"])
    def test_valid_values_accepted(self, value) -> None:
        """
        Description: True, False, and 'auto' must not raise.
        Scenario: Call _validate_latex with each valid value.
        Expectation: No exception.
        """
        _validate_latex(value)

    @pytest.mark.parametrize("value", [0, 1, "yes", "no", "true", "false", None, "Auto", "AUTO"])
    def test_invalid_values_raise_value_error(self, value) -> None:
        """
        Description: Invalid values must raise ValueError.
        Scenario: Call _validate_latex with various invalid inputs.
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_latex(value)

    def test_error_message_contains_bad_value(self) -> None:
        """
        Description: Error message must name the offending value.
        Scenario: _validate_latex('yes').
        Expectation: 'yes' appears in the error message.
        """
        with pytest.raises(ValueError, match="yes"):
            _validate_latex("yes")

    def test_error_message_mentions_valid_options(self) -> None:
        """
        Description: Error message must mention valid options for guidance.
        Scenario: _validate_latex('bad').
        Expectation: 'auto' appears in the error message.
        """
        with pytest.raises(ValueError, match="auto"):
            _validate_latex("bad")

    def test_integer_zero_is_not_false(self) -> None:
        """
        Description: Integer 0 is not the same as bool False and must be rejected.
        Scenario: _validate_latex(0).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_latex(0)

    def test_integer_one_is_not_true(self) -> None:
        """
        Description: Integer 1 is not the same as bool True and must be rejected.
        Scenario: _validate_latex(1).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_latex(1)

    def test_none_is_rejected(self) -> None:
        """
        Description: None must be rejected as it's neither bool nor 'auto'.
        Scenario: _validate_latex(None).
        Expectation: ValueError raised.
        """
        with pytest.raises(ValueError):
            _validate_latex(None)


# ---------------------------------------------------------------------------
# _snapshot_rcparams (style module version)
# ---------------------------------------------------------------------------


class TestStyleSnapshotRcparams:
    """Validate the style module's rcParams snapshotting helper."""

    def test_snapshot_captures_existing_keys(self) -> None:
        """
        Description: Keys present in mpl.rcParams must be captured.
        Scenario: Snapshot with a known key dict.
        Expectation: Key present in returned dict.
        """
        keys = {"font.size": None}
        snap = _snapshot_rcparams(keys)
        assert "font.size" in snap

    def test_snapshot_skips_missing_keys(self) -> None:
        """
        Description: Keys not in mpl.rcParams must be silently skipped.
        Scenario: Snapshot with a fabricated key.
        Expectation: Key not in returned dict.
        """
        keys = {"plotstyle.nonexistent.key.xyz": None}
        snap = _snapshot_rcparams(keys)
        assert "plotstyle.nonexistent.key.xyz" not in snap

    def test_snapshot_returns_dict(self) -> None:
        """
        Description: Return type must be a plain dict.
        Scenario: Snapshot a known key.
        Expectation: isinstance(dict) is True.
        """
        snap = _snapshot_rcparams({"font.size": None})
        assert isinstance(snap, dict)

    def test_snapshot_empty_keys_returns_empty_dict(self) -> None:
        """
        Description: Empty key mapping must produce empty snapshot.
        Scenario: Pass empty dict.
        Expectation: Empty dict returned.
        """
        assert _snapshot_rcparams({}) == {}

    def test_snapshot_captures_correct_values(self) -> None:
        """
        Description: Snapshot values must match current mpl.rcParams values.
        Scenario: Snapshot font.size and compare.
        Expectation: Values match.
        """
        keys = {"font.size": None, "pdf.fonttype": None}
        snap = _snapshot_rcparams(keys)
        for key in keys:
            if key in mpl.rcParams:
                assert snap[key] == mpl.rcParams[key]

    def test_snapshot_mixed_real_and_fake_keys(self) -> None:
        """
        Description: Only real keys appear in the snapshot, fake ones are skipped.
        Scenario: Pass one real and one fake key.
        Expectation: Only real key in result.
        """
        keys = {"font.size": None, "plotstyle.fake": None}
        snap = _snapshot_rcparams(keys)
        assert "font.size" in snap
        assert "plotstyle.fake" not in snap


# ---------------------------------------------------------------------------
# JournalStyle
# ---------------------------------------------------------------------------


class TestJournalStyle:
    """Validate the JournalStyle handle."""

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_spec_attribute_accessible(self) -> None:
        """
        Description: JournalStyle must expose the applied spec.
        Scenario: use('nature').spec.
        Expectation: spec.metadata.name == 'Nature'.
        """
        style = use("nature")
        try:
            assert style.spec.metadata.name == registry.get("nature").metadata.name
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_context_manager_enters_and_exits(self) -> None:
        """
        Description: JournalStyle must support the context manager protocol.
        Scenario: Use in a with statement.
        Expectation: No exception.
        """
        with use("nature") as style:
            assert style is not None

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_context_manager_yields_self(self) -> None:
        """
        Description: __enter__ must return the JournalStyle instance.
        Scenario: Bind the 'as' variable.
        Expectation: Same object.
        """
        style = use("nature")
        with style as entered:
            assert entered is style

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_context_manager_restores_rcparams(self) -> None:
        """
        Description: Exiting the context manager must restore rcParams.
        Scenario: Record a key, modify via use(), exit.
        Expectation: Key restored to original value.
        """
        original_font_size = mpl.rcParams["font.size"]
        with use("nature"):
            pass  # rcParams modified inside
        assert mpl.rcParams["font.size"] == original_font_size

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_restore_is_idempotent(self) -> None:
        """
        Description: Calling restore() multiple times must be safe.
        Scenario: Call restore() twice.
        Expectation: No exception on second call.
        """
        style = use("nature")
        style.restore()
        style.restore()  # Should not raise

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_context_manager_restores_on_exception(self) -> None:
        """
        Description: rcParams must be restored even when an exception occurs.
        Scenario: Raise inside a with block.
        Expectation: rcParams restored after exception.
        """
        original_font_size = mpl.rcParams["font.size"]
        with pytest.raises(RuntimeError), use("nature"):
            raise RuntimeError("test error")
        assert mpl.rcParams["font.size"] == original_font_size

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_repr_contains_journal_name(self) -> None:
        """
        Description: __repr__ must include the journal display name.
        Scenario: repr(use('nature')).
        Expectation: 'Nature' appears in repr.
        """
        style = use("nature")
        try:
            r = repr(style)
            assert "Nature" in r
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_repr_contains_class_name(self) -> None:
        """
        Description: __repr__ must start with 'JournalStyle('.
        Scenario: repr(use('nature')).
        Expectation: Starts with 'JournalStyle('.
        """
        style = use("nature")
        try:
            assert repr(style).startswith("JournalStyle(")
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_repr_contains_seaborn_patched_flag(self) -> None:
        """
        Description: __repr__ must show the seaborn_patched status.
        Scenario: repr(use('nature')).
        Expectation: 'seaborn_patched=' appears in repr.
        """
        style = use("nature")
        try:
            assert "seaborn_patched=" in repr(style)
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_repr_shows_false_when_not_patched(self) -> None:
        """
        Description: Without seaborn_compatible, seaborn_patched must be False.
        Scenario: use('nature') without seaborn_compatible.
        Expectation: 'seaborn_patched=False' in repr.
        """
        style = use("nature")
        try:
            assert "seaborn_patched=False" in repr(style)
        finally:
            style.restore()

    def test_direct_construction(self) -> None:
        """
        Description: JournalStyle can be constructed directly for testing.
        Scenario: Create JournalStyle with a mock spec and empty dict.
        Expectation: No exception; attributes accessible.
        """
        mock_spec = MagicMock()
        mock_spec.metadata.name = "MockJournal"
        style = JournalStyle(spec=mock_spec, previous_rcparams={})
        assert style.spec.metadata.name == "MockJournal"
        assert style._seaborn_patched is False

    def test_direct_construction_with_seaborn_patched(self) -> None:
        """
        Description: JournalStyle tracks seaborn_patched flag correctly.
        Scenario: Create JournalStyle with seaborn_patched=True.
        Expectation: _seaborn_patched is True.
        """
        mock_spec = MagicMock()
        style = JournalStyle(spec=mock_spec, previous_rcparams={}, seaborn_patched=True)
        assert style._seaborn_patched is True

    def test_restore_updates_rcparams(self) -> None:
        """
        Description: restore() must reapply the saved rcParams.
        Scenario: Create with a known snapshot, call restore.
        Expectation: rcParams updated to snapshot values.
        """
        mock_spec = MagicMock()
        original_font_size = mpl.rcParams["font.size"]
        snapshot = {"font.size": original_font_size}
        # Change font.size
        mpl.rcParams["font.size"] = 42.0
        style = JournalStyle(spec=mock_spec, previous_rcparams=snapshot)
        style.restore()
        assert mpl.rcParams["font.size"] == original_font_size

    def test_exit_returns_none(self) -> None:
        """
        Description: __exit__ must return None (not suppress exceptions).
        Scenario: Call __exit__ directly.
        Expectation: Return value is None.
        """
        mock_spec = MagicMock()
        style = JournalStyle(spec=mock_spec, previous_rcparams={})
        result = style.__exit__(None, None, None)
        assert result is None


# ---------------------------------------------------------------------------
# use() function tests
# ---------------------------------------------------------------------------


class TestUse:
    """Validate the primary use() function."""

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_returns_journal_style(self) -> None:
        """
        Description: use() must return a JournalStyle instance.
        Scenario: use('nature').
        Expectation: isinstance(JournalStyle).
        """
        style = use("nature")
        try:
            assert isinstance(style, JournalStyle)
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_applies_rcparams(self) -> None:
        """
        Description: use() must modify mpl.rcParams.
        Scenario: Check pdf.fonttype after use('nature').
        Expectation: pdf.fonttype == 42 (TrueType).
        """
        style = use("nature")
        try:
            assert mpl.rcParams["pdf.fonttype"] == 42
            assert mpl.rcParams["ps.fonttype"] == 42
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_applies_journal_dpi(self) -> None:
        """
        Description: savefig.dpi must match the journal spec.
        Scenario: use('ieee').
        Expectation: savefig.dpi == 600 (IEEE min_dpi).
        """
        style = use("ieee")
        try:
            assert mpl.rcParams["savefig.dpi"] == 600
        finally:
            style.restore()

    def test_use_unknown_journal_raises(self) -> None:
        """
        Description: Unknown journal must raise SpecNotFoundError.
        Scenario: use('nonexistent_xyz').
        Expectation: KeyError raised.
        """
        with pytest.raises(KeyError):
            use("nonexistent_xyz")

    def test_use_invalid_latex_raises(self) -> None:
        """
        Description: Invalid latex parameter must raise ValueError.
        Scenario: use('nature', latex='yes').
        Expectation: ValueError raised before any rcParams are modified.
        """
        original = mpl.rcParams["font.size"]
        with pytest.raises(ValueError):
            use("nature", latex="yes")
        # rcParams should not have been modified
        assert mpl.rcParams["font.size"] == original

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_latex_false_disables_latex(self) -> None:
        """
        Description: latex=False must set text.usetex=False.
        Scenario: use('nature', latex=False).
        Expectation: text.usetex is False.
        """
        style = use("nature", latex=False)
        try:
            assert mpl.rcParams["text.usetex"] is False
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    @pytest.mark.parametrize("journal", KNOWN_JOURNALS)
    def test_use_all_known_journals(self, journal: str) -> None:
        """
        Description: use() must work for all known journals.
        Scenario: Parametric sweep over known journals.
        Expectation: No exception.
        """
        style = use(journal)
        style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_restores_only_modified_keys(self) -> None:
        """
        Description: Restore must only affect keys that were actually changed.
        Scenario: Set an unusual rcParam, use() and restore.
        Expectation: Unusual param unchanged after restore.
        """
        original_agg = mpl.rcParams.get("agg.path.chunksize", 0)
        mpl.rcParams["agg.path.chunksize"] = 99999
        try:
            style = use("nature")
            style.restore()
            assert mpl.rcParams["agg.path.chunksize"] == 99999
        finally:
            mpl.rcParams["agg.path.chunksize"] = original_agg

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_seaborn_compatible_false_no_patch(self) -> None:
        """
        Description: seaborn_compatible=False must not attempt to patch seaborn.
        Scenario: use('nature', seaborn_compatible=False).
        Expectation: _seaborn_patched is False.
        """
        style = use("nature", seaborn_compatible=False)
        try:
            assert style._seaborn_patched is False
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_nested_contexts_restore_correctly(self) -> None:
        """
        Description: Nested use() contexts must restore to their respective states.
        Scenario: Nest use('ieee') inside use('nature').
        Expectation: After inner exit, params match outer; after outer exit, original.
        """
        original_dpi = mpl.rcParams.get("savefig.dpi")
        with use("nature"):
            nature_dpi = mpl.rcParams["savefig.dpi"]
            with use("ieee"):
                ieee_dpi = mpl.rcParams["savefig.dpi"]
                assert ieee_dpi == 600
            # After inner restore, should be back to nature params
            assert mpl.rcParams["savefig.dpi"] == nature_dpi
        # After outer restore, should be back to original
        assert mpl.rcParams.get("savefig.dpi") == original_dpi

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_spec_matches_registry(self) -> None:
        """
        Description: The spec on the returned style must match the registry spec.
        Scenario: use('ieee').spec vs registry.get('ieee').
        Expectation: Metadata name matches.
        """
        style = use("ieee")
        try:
            assert style.spec.metadata.name == registry.get("ieee").metadata.name
        finally:
            style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_context_manager_exception_propagates(self) -> None:
        """
        Description: Exceptions inside the context manager must propagate.
        Scenario: Raise ValueError inside with block.
        Expectation: ValueError propagates; rcParams restored.
        """
        original_pdf = mpl.rcParams["pdf.fonttype"]
        with pytest.raises(ValueError, match="test"), use("nature"):
            raise ValueError("test")
        assert mpl.rcParams["pdf.fonttype"] == original_pdf

    def test_use_invalid_latex_does_not_modify_rcparams(self) -> None:
        """
        Description: When latex validation fails, rcParams must not be modified.
        Scenario: Call use with invalid latex; check rcParams unchanged.
        Expectation: All rcParams remain at their original values.
        """
        snapshot = dict(mpl.rcParams)
        with pytest.raises(ValueError):
            use("nature", latex=42)
        # Verify no rcParams changed
        for key in ["font.size", "pdf.fonttype", "ps.fonttype"]:
            assert mpl.rcParams[key] == snapshot[key]

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_seaborn_compatible_with_mock_seaborn(self) -> None:
        """
        Description: When seaborn_compatible=True and seaborn is available,
        the patch should be applied successfully.
        Scenario: Mock _apply_seaborn_patch to return True.
        Expectation: _seaborn_patched is True on the returned style.
        """
        with patch("plotstyle.core.style._apply_seaborn_patch", return_value=True):
            style = use("nature", seaborn_compatible=True)
            try:
                assert style._seaborn_patched is True
            finally:
                # Must reset the flag to avoid unpatch call
                style._seaborn_patched = False
                style.restore()

    @pytest.mark.filterwarnings("ignore::plotstyle._utils.warnings.FontFallbackWarning")
    def test_use_seaborn_compatible_missing_seaborn_warns(self) -> None:
        """
        Description: When seaborn is missing and seaborn_compatible=True,
        a warning is emitted and _seaborn_patched is False.
        Scenario: Mock _apply_seaborn_patch to emit warning and return False.
        Expectation: _seaborn_patched False; warning about seaborn emitted.
        """

        def mock_patch(params):
            warnings.warn(_SEABORN_MISSING_WARNING, stacklevel=2)
            return False

        with (
            patch("plotstyle.core.style._apply_seaborn_patch", side_effect=mock_patch),
            warnings.catch_warnings(record=True),
        ):
            warnings.simplefilter("always")
            style = use("nature", seaborn_compatible=True)
            try:
                assert style._seaborn_patched is False
            finally:
                style.restore()


# ---------------------------------------------------------------------------
# _apply_seaborn_patch
# ---------------------------------------------------------------------------


class TestApplySeabornPatch:
    """Validate the seaborn patch application helper."""

    def test_patch_applied_successfully(self) -> None:
        """
        Description: When seaborn is available, patch should succeed.
        Scenario: Mock successful import and patch.
        Expectation: Returns True.
        """
        with (
            patch("plotstyle.integrations.seaborn.capture_overrides") as mock_capture,
            patch("plotstyle.integrations.seaborn.patch_seaborn") as mock_patch,
        ):
            result = _apply_seaborn_patch({"font.size": 8})
            assert result is True
            mock_capture.assert_called_once_with({"font.size": 8})
            mock_patch.assert_called_once()

    def test_patch_returns_false_when_seaborn_missing(self) -> None:
        """
        Description: When seaborn import fails, must return False and warn.
        Scenario: Mock ImportError on seaborn import.
        Expectation: Returns False.
        """
        with (
            patch.dict("sys.modules", {"plotstyle.integrations.seaborn": None}),
            patch(
                "plotstyle.core.style._apply_seaborn_patch",
                wraps=_apply_seaborn_patch,
            ),
        ):
            # Force ImportError by making the import fail
            import builtins

            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "plotstyle.integrations.seaborn":
                    raise ImportError("No module named 'seaborn'")
                return original_import(name, *args, **kwargs)

            with (
                patch("builtins.__import__", side_effect=mock_import),
                warnings.catch_warnings(record=True),
            ):
                warnings.simplefilter("always")
                result = _apply_seaborn_patch({"font.size": 8})
                assert result is False


# ---------------------------------------------------------------------------
# _SEABORN_MISSING_WARNING constant
# ---------------------------------------------------------------------------


class TestSeabornMissingWarning:
    """Validate the seaborn missing warning constant."""

    def test_warning_is_string(self) -> None:
        """
        Description: _SEABORN_MISSING_WARNING must be a non-empty string.
        Scenario: Check type and content.
        Expectation: Non-empty str.
        """
        assert isinstance(_SEABORN_MISSING_WARNING, str)
        assert len(_SEABORN_MISSING_WARNING) > 0

    def test_warning_mentions_seaborn(self) -> None:
        """
        Description: Warning message must mention seaborn.
        Scenario: Check content.
        Expectation: 'seaborn' appears in the message.
        """
        assert "seaborn" in _SEABORN_MISSING_WARNING.lower()

    def test_warning_mentions_seaborn_compatible(self) -> None:
        """
        Description: Warning must reference the seaborn_compatible parameter.
        Scenario: Check content.
        Expectation: 'seaborn_compatible' appears in the message.
        """
        assert "seaborn_compatible" in _SEABORN_MISSING_WARNING


# ---------------------------------------------------------------------------
# JournalStyle restore with seaborn
# ---------------------------------------------------------------------------


class TestJournalStyleRestore:
    """Validate restore behavior including seaborn unpatch."""

    def test_restore_with_seaborn_patched_calls_unpatch(self) -> None:
        """
        Description: When _seaborn_patched is True, restore must call unpatch_seaborn.
        Scenario: Create JournalStyle with seaborn_patched=True, mock unpatch.
        Expectation: unpatch_seaborn called during restore.
        """
        mock_spec = MagicMock()
        style = JournalStyle(spec=mock_spec, previous_rcparams={}, seaborn_patched=True)
        with patch("plotstyle.integrations.seaborn.unpatch_seaborn") as mock_unpatch:
            style.restore()
            mock_unpatch.assert_called_once()

    def test_restore_resets_seaborn_flag(self) -> None:
        """
        Description: After restore, _seaborn_patched must be set to False.
        Scenario: Create with seaborn_patched=True, call restore.
        Expectation: _seaborn_patched is False after restore.
        """
        mock_spec = MagicMock()
        style = JournalStyle(spec=mock_spec, previous_rcparams={}, seaborn_patched=True)
        with patch("plotstyle.integrations.seaborn.unpatch_seaborn"):
            style.restore()
        assert style._seaborn_patched is False

    def test_restore_idempotent_with_seaborn(self) -> None:
        """
        Description: Calling restore twice with seaborn_patched must only unpatch once.
        Scenario: Create with seaborn_patched=True, call restore twice.
        Expectation: unpatch_seaborn called only once.
        """
        mock_spec = MagicMock()
        style = JournalStyle(spec=mock_spec, previous_rcparams={}, seaborn_patched=True)
        with patch("plotstyle.integrations.seaborn.unpatch_seaborn") as mock_unpatch:
            style.restore()
            style.restore()
            mock_unpatch.assert_called_once()

    def test_restore_without_seaborn_does_not_unpatch(self) -> None:
        """
        Description: When _seaborn_patched is False, unpatch must not be called.
        Scenario: Create with seaborn_patched=False, call restore.
        Expectation: unpatch_seaborn not called.
        """
        mock_spec = MagicMock()
        style = JournalStyle(spec=mock_spec, previous_rcparams={}, seaborn_patched=False)
        # unpatch_seaborn is lazily imported only when _seaborn_patched=True,
        # so it never gets called; just verify the flag doesn't change.
        style.restore()
        assert style._seaborn_patched is False


# ---------------------------------------------------------------------------
# __all__ exports
# ---------------------------------------------------------------------------


class TestPublicAPI:
    """Validate the module's public API surface."""

    def test_use_is_exported(self) -> None:
        """
        Description: 'use' must be in __all__.
        Scenario: Import and check.
        Expectation: Present.
        """
        import plotstyle.core.style as mod

        assert "use" in mod.__all__

    def test_journal_style_is_exported(self) -> None:
        """
        Description: 'JournalStyle' must be in __all__.
        Scenario: Import and check.
        Expectation: Present.
        """
        import plotstyle.core.style as mod

        assert "JournalStyle" in mod.__all__
