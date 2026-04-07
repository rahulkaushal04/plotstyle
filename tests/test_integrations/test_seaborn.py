"""Test suite for plotstyle.integrations.seaborn.

Tests cover:
- capture_overrides / reapply_overrides round-trip
- patch_seaborn / unpatch_seaborn lifecycle
- plotstyle_theme composition
- Thread-safety documentation (single-threaded behaviour only)
- All documented edge cases (no-op guards, double-patch prevention, etc.)

External dependencies (seaborn, plotstyle) are mocked throughout so the suite
runs without either library installed.
"""

from __future__ import annotations

import sys
import types
from typing import Any
from unittest.mock import MagicMock, patch

import matplotlib
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")  # Non-interactive backend; no display required.

# ---------------------------------------------------------------------------
# Helpers to build lightweight fakes for seaborn and plotstyle.core.style
# ---------------------------------------------------------------------------


def _make_sns_module(set_theme_side_effect=None) -> types.ModuleType:
    """Return a minimal fake *seaborn* module with a trackable ``set_theme``."""
    sns = types.ModuleType("seaborn")
    mock_set_theme = MagicMock(name="set_theme", side_effect=set_theme_side_effect)
    sns.set_theme = mock_set_theme
    return sns


def _make_plotstyle_use() -> MagicMock:
    """Return a MagicMock standing in for ``plotstyle.core.style.use``."""
    return MagicMock(name="plotstyle.core.style.use")


# ---------------------------------------------------------------------------
# Module-level fixture: isolate module globals between every test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_module_globals():
    """Reset _PLOTSTYLE_OVERRIDES and _ORIGINAL_SET_THEME before each test.

    Description: Ensures module-level mutable state does not bleed between tests.
    Scenario: Each test starts with a clean slate for both globals.
    Expectation: Tests are fully isolated regardless of execution order.
    """
    import plotstyle.integrations.seaborn as ps_sns_module

    original_overrides = ps_sns_module._PLOTSTYLE_OVERRIDES
    original_set_theme = ps_sns_module._ORIGINAL_SET_THEME

    ps_sns_module._PLOTSTYLE_OVERRIDES = None
    ps_sns_module._ORIGINAL_SET_THEME = None

    yield

    ps_sns_module._PLOTSTYLE_OVERRIDES = original_overrides
    ps_sns_module._ORIGINAL_SET_THEME = original_set_theme


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ps_sns():
    """Return the module under test with matplotlib patched to Agg.

    Description: Provides a consistently importable module reference.
    Scenario: Standard import succeeding.
    Expectation: Module is available and plt.rcParams is writable.
    """
    import plotstyle.integrations.seaborn as mod

    return mod


@pytest.fixture()
def fake_sns():
    """Inject a fake seaborn module into sys.modules.

    Description: Allows tests that exercise seaborn-dependent paths without
                 requiring the real library.
    Scenario: sys.modules['seaborn'] is replaced with a controlled fake.
    Expectation: Code under test imports the fake transparently.
    """
    sns = _make_sns_module()
    with patch.dict(sys.modules, {"seaborn": sns}):
        yield sns


@pytest.fixture()
def fake_plotstyle_use():
    """Patch plotstyle.core.style.use for tests that call plotstyle_theme.

    Description: Isolates plotstyle_theme from the real plotstyle library.
    Scenario: plotstyle.core.style.use is replaced with a MagicMock.
    Expectation: Calls are recorded; no real journal preset is loaded.
    """
    mock_use = _make_plotstyle_use()
    with patch("plotstyle.integrations.seaborn.use", mock_use):
        yield mock_use


@pytest.fixture()
def sample_params() -> dict[str, Any]:
    """Return a representative subset of rcParams used across multiple tests."""
    return {"font.size": 8.0, "axes.linewidth": 0.8, "figure.dpi": 300}


# ===========================================================================
# capture_overrides
# ===========================================================================


class TestCaptureOverrides:
    """Tests for :func:`capture_overrides`."""

    def test_capture_stores_params(self, ps_sns, sample_params):
        """
        Description: Validates that capture_overrides stores the provided dict.
        Scenario: Called with a non-empty param dict.
        Expectation: _PLOTSTYLE_OVERRIDES equals the supplied params.
        """
        ps_sns.capture_overrides(sample_params)
        assert sample_params == ps_sns._PLOTSTYLE_OVERRIDES

    def test_capture_makes_shallow_copy(self, ps_sns, sample_params):
        """
        Description: Ensures the stored snapshot is independent of the caller's dict.
        Scenario: Caller mutates the original dict after capture_overrides returns.
        Expectation: _PLOTSTYLE_OVERRIDES is unaffected by the mutation.
        """
        ps_sns.capture_overrides(sample_params)
        sample_params["font.size"] = 99.0
        assert ps_sns._PLOTSTYLE_OVERRIDES["font.size"] == 8.0

    def test_capture_empty_dict(self, ps_sns):
        """
        Description: Validates behaviour with an empty param dict.
        Scenario: An empty dict is passed in.
        Expectation: _PLOTSTYLE_OVERRIDES is set to {}, not None.
        """
        ps_sns.capture_overrides({})
        assert ps_sns._PLOTSTYLE_OVERRIDES == {}

    def test_capture_overwrites_previous(self, ps_sns):
        """
        Description: Verifies a second call replaces the first snapshot.
        Scenario: capture_overrides is invoked twice with different dicts.
        Expectation: Only the second dict is retained.
        """
        ps_sns.capture_overrides({"font.size": 8.0})
        ps_sns.capture_overrides({"axes.linewidth": 1.5})
        assert ps_sns._PLOTSTYLE_OVERRIDES == {"axes.linewidth": 1.5}

    def test_capture_single_key(self, ps_sns):
        """
        Description: Validates minimal single-key input.
        Scenario: Dict with one entry.
        Expectation: That entry is stored correctly.
        """
        ps_sns.capture_overrides({"figure.dpi": 300})
        assert ps_sns._PLOTSTYLE_OVERRIDES == {"figure.dpi": 300}

    @pytest.mark.parametrize(
        "params",
        [
            {"font.size": 6, "axes.linewidth": 0.5},
            {"figure.figsize": [3.5, 2.5], "font.family": "serif"},
            {"lines.linewidth": 0.75, "legend.fontsize": 7},
        ],
    )
    def test_capture_various_param_shapes(self, ps_sns, params):
        """
        Description: Validates capture_overrides handles diverse rcParam shapes.
        Scenario: Various dicts including list-valued entries.
        Expectation: Stored dict equals the input.
        """
        ps_sns.capture_overrides(params)
        assert params == ps_sns._PLOTSTYLE_OVERRIDES


# ===========================================================================
# reapply_overrides
# ===========================================================================


class TestReapplyOverrides:
    """Tests for :func:`reapply_overrides`."""

    def test_reapply_updates_rcparams(self, ps_sns):
        """
        Description: Confirms reapply_overrides pushes stored params into rcParams.
        Scenario: A known param is captured then reapplied.
        Expectation: plt.rcParams reflects the captured value.
        """
        sentinel_size = 3.141592
        ps_sns.capture_overrides({"font.size": sentinel_size})
        ps_sns.reapply_overrides()
        assert plt.rcParams["font.size"] == pytest.approx(sentinel_size)

    def test_reapply_noop_when_never_captured(self, ps_sns):
        """
        Description: Guards against calling reapply before any capture.
        Scenario: _PLOTSTYLE_OVERRIDES is None (module freshly imported).
        Expectation: No exception is raised; rcParams is unchanged.
        """
        assert ps_sns._PLOTSTYLE_OVERRIDES is None
        before = dict(plt.rcParams)
        ps_sns.reapply_overrides()  # Must not raise
        # Font size should be unchanged (spot-check one stable key)
        assert plt.rcParams["font.size"] == before["font.size"]

    def test_reapply_noop_when_empty_dict(self, ps_sns):
        """
        Description: Verifies no rcParams mutation when the captured dict is empty.
        Scenario: capture_overrides({}) was called, then reapply_overrides().
        Expectation: plt.rcParams.update is effectively not called with real keys.
        """
        ps_sns.capture_overrides({})
        before_size = plt.rcParams["font.size"]
        ps_sns.reapply_overrides()
        assert plt.rcParams["font.size"] == before_size

    def test_reapply_multiple_params(self, ps_sns, sample_params):
        """
        Description: Verifies all captured params are written to rcParams.
        Scenario: Multiple distinct params are captured and reapplied.
        Expectation: Each param is present in plt.rcParams with the correct value.
        """
        ps_sns.capture_overrides(sample_params)
        ps_sns.reapply_overrides()
        for key, value in sample_params.items():
            assert plt.rcParams[key] == pytest.approx(value)

    def test_reapply_is_idempotent(self, ps_sns, sample_params):
        """
        Description: Calling reapply_overrides multiple times must be safe.
        Scenario: reapply_overrides is invoked three times in succession.
        Expectation: rcParams retains the correct values after all calls.
        """
        ps_sns.capture_overrides(sample_params)
        for _ in range(3):
            ps_sns.reapply_overrides()
        assert plt.rcParams["font.size"] == pytest.approx(sample_params["font.size"])

    def test_reapply_uses_update_internally(self, ps_sns, sample_params):
        """
        Description: Validates that plt.rcParams.update is the mechanism used.
        Scenario: Patch plt.rcParams.update and confirm it is called with the right dict.
        Expectation: update is called exactly once with the captured overrides.
        """
        ps_sns.capture_overrides(sample_params)
        with patch.object(plt, "rcParams") as mock_rc:
            ps_sns.reapply_overrides()
            mock_rc.update.assert_called_once_with(sample_params)


# ===========================================================================
# patch_seaborn / unpatch_seaborn
# ===========================================================================


class TestPatchUnpatch:
    """Tests for the persistent monkey-patch strategy."""

    def test_patch_replaces_set_theme(self, ps_sns, fake_sns):
        """
        Description: Verifies patch_seaborn swaps sns.set_theme for a wrapper.
        Scenario: sns.set_theme is a known MagicMock; patch_seaborn is called.
        Expectation: sns.set_theme is no longer the original object.
        """
        original = fake_sns.set_theme
        ps_sns.patch_seaborn()
        assert fake_sns.set_theme is not original

    def test_patch_stores_original(self, ps_sns, fake_sns):
        """
        Description: Confirms _ORIGINAL_SET_THEME holds the pre-patch callable.
        Scenario: patch_seaborn is called once.
        Expectation: _ORIGINAL_SET_THEME is the original set_theme reference.
        """
        original = fake_sns.set_theme
        ps_sns.patch_seaborn()
        assert ps_sns._ORIGINAL_SET_THEME is original

    def test_patch_calls_original_set_theme(self, ps_sns, fake_sns, sample_params):
        """
        Description: The wrapper must delegate to the real sns.set_theme.
        Scenario: Patched set_theme is called with style and context kwargs.
        Expectation: The original MagicMock is called with the same arguments.
        """
        original_mock = fake_sns.set_theme
        ps_sns.capture_overrides(sample_params)
        ps_sns.patch_seaborn()

        fake_sns.set_theme(style="ticks", context="paper")

        original_mock.assert_called_once_with(style="ticks", context="paper")

    def test_patch_reapplies_overrides_after_set_theme(self, ps_sns, fake_sns):
        """
        Description: Core behaviour: overrides are restored after each set_theme.
        Scenario: Overrides captured, patch installed, set_theme called.
        Expectation: plt.rcParams['font.size'] equals the captured value.
        """
        ps_sns.capture_overrides({"font.size": 3.14})
        ps_sns.patch_seaborn()
        fake_sns.set_theme(style="white")
        assert plt.rcParams["font.size"] == pytest.approx(3.14)

    def test_patch_noop_when_already_patched(self, ps_sns, fake_sns):
        """
        Description: Double-patching must be silently ignored.
        Scenario: patch_seaborn is called twice.
        Expectation: _ORIGINAL_SET_THEME still holds the very first original.
        """
        original = fake_sns.set_theme
        ps_sns.patch_seaborn()
        wrapper_after_first_patch = fake_sns.set_theme
        ps_sns.patch_seaborn()  # Second call — must not double-wrap
        assert ps_sns._ORIGINAL_SET_THEME is original
        assert fake_sns.set_theme is wrapper_after_first_patch

    def test_patch_raises_if_seaborn_missing(self, ps_sns):
        """
        Description: Validates the ImportError contract when seaborn is absent.
        Scenario: 'seaborn' is removed from sys.modules and the import is blocked.
        Expectation: ImportError is raised by patch_seaborn.
        """
        with patch.dict(sys.modules, {"seaborn": None}), pytest.raises(ImportError):
            ps_sns.patch_seaborn()

    def test_unpatch_restores_original(self, ps_sns, fake_sns):
        """
        Description: unpatch_seaborn must put the original callable back.
        Scenario: Patch then unpatch.
        Expectation: sns.set_theme is the original MagicMock again.
        """
        original = fake_sns.set_theme
        ps_sns.patch_seaborn()
        ps_sns.unpatch_seaborn()
        assert fake_sns.set_theme is original

    def test_unpatch_clears_sentinel(self, ps_sns, fake_sns):
        """
        Description: After unpatching, _ORIGINAL_SET_THEME must be reset to None.
        Scenario: Patch then unpatch.
        Expectation: _ORIGINAL_SET_THEME is None, allowing re-patching.
        """
        ps_sns.patch_seaborn()
        ps_sns.unpatch_seaborn()
        assert ps_sns._ORIGINAL_SET_THEME is None

    def test_unpatch_noop_when_not_patched(self, ps_sns):
        """
        Description: unpatch_seaborn must be safe when called without a prior patch.
        Scenario: _ORIGINAL_SET_THEME is None.
        Expectation: No exception raised; nothing in sys.modules is mutated.
        """
        assert ps_sns._ORIGINAL_SET_THEME is None
        ps_sns.unpatch_seaborn()  # Must not raise

    def test_patch_unpatch_cycle_repeatable(self, ps_sns, fake_sns):
        """
        Description: Patch/unpatch may be cycled multiple times without corruption.
        Scenario: Three full patch-unpatch cycles.
        Expectation: sns.set_theme returns to the original after each cycle.
        """
        original = fake_sns.set_theme
        for _ in range(3):
            ps_sns.patch_seaborn()
            assert fake_sns.set_theme is not original
            ps_sns.unpatch_seaborn()
            assert fake_sns.set_theme is original

    def test_patch_set_theme_called_multiple_times(self, ps_sns, fake_sns):
        """
        Description: Overrides must be reapplied on every set_theme call, not just the first.
        Scenario: Patched set_theme is called three times.
        Expectation: The captured font.size is present in rcParams after each call.
        """
        ps_sns.capture_overrides({"font.size": 7.77})
        ps_sns.patch_seaborn()
        for _ in range(3):
            fake_sns.set_theme(style="ticks")
            assert plt.rcParams["font.size"] == pytest.approx(7.77)

    def test_patch_wrapper_passes_positional_args(self, ps_sns, fake_sns):
        """
        Description: The wrapper must forward positional arguments unchanged.
        Scenario: Patched set_theme is called with a positional argument.
        Expectation: The original mock records the positional argument.
        """
        original_mock = fake_sns.set_theme
        ps_sns.capture_overrides({})
        ps_sns.patch_seaborn()
        fake_sns.set_theme("ticks")
        original_mock.assert_called_once_with("ticks")

    def test_unpatch_requires_seaborn_importable(self, ps_sns, fake_sns):
        """
        Description: unpatch_seaborn should not silently swallow ImportError when
                     seaborn disappears between patch and unpatch calls (unusual but possible).
        Scenario: Patch installed successfully; then seaborn removed from sys.modules.
        Expectation: ImportError is propagated from the deferred import.
        """
        ps_sns.patch_seaborn()
        with patch.dict(sys.modules, {"seaborn": None}), pytest.raises(ImportError):
            ps_sns.unpatch_seaborn()


# ===========================================================================
# plotstyle_theme
# ===========================================================================


class TestPlotStyleTheme:
    """Tests for the one-shot :func:`plotstyle_theme` helper."""

    def test_plotstyle_theme_calls_set_theme_first(self, ps_sns, fake_sns, fake_plotstyle_use):
        """
        Description: seaborn's set_theme must be called before plotstyle.use.
        Scenario: plotstyle_theme('nature') with default style and context.
        Expectation: set_theme is called with style='ticks' and context='paper'.
        """
        ps_sns.plotstyle_theme("nature")
        fake_sns.set_theme.assert_called_once_with(style="ticks", context="paper")

    def test_plotstyle_theme_calls_use_with_journal(self, ps_sns, fake_sns, fake_plotstyle_use):
        """
        Description: plotstyle.use must receive the supplied journal name.
        Scenario: plotstyle_theme('ieee').
        Expectation: use is called exactly once with 'ieee'.
        """
        ps_sns.plotstyle_theme("ieee")
        fake_plotstyle_use.assert_called_once_with("ieee")

    def test_plotstyle_theme_ordering(self, ps_sns, fake_sns, fake_plotstyle_use):
        """
        Description: set_theme must precede use so PlotStyle wins conflicts.
        Scenario: Track call ordering via a shared call list.
        Expectation: set_theme call index is lower than use call index.
        """
        call_order: list[str] = []
        fake_sns.set_theme.side_effect = lambda **kw: call_order.append("set_theme")
        fake_plotstyle_use.side_effect = lambda *a: call_order.append("use")

        ps_sns.plotstyle_theme("nature")

        assert call_order == ["set_theme", "use"]

    @pytest.mark.parametrize(
        "seaborn_style",
        ["darkgrid", "whitegrid", "dark", "white", "ticks"],
    )
    def test_plotstyle_theme_accepts_all_seaborn_styles(
        self, ps_sns, fake_sns, fake_plotstyle_use, seaborn_style
    ):
        """
        Description: All documented seaborn_style values must be forwarded.
        Scenario: Each valid seaborn_style string.
        Expectation: set_theme receives the exact style string.
        """
        ps_sns.plotstyle_theme("nature", seaborn_style=seaborn_style)
        fake_sns.set_theme.assert_called_once_with(style=seaborn_style, context="paper")

    @pytest.mark.parametrize(
        "seaborn_context",
        ["paper", "notebook", "talk", "poster"],
    )
    def test_plotstyle_theme_accepts_all_seaborn_contexts(
        self, ps_sns, fake_sns, fake_plotstyle_use, seaborn_context
    ):
        """
        Description: All documented seaborn_context values must be forwarded.
        Scenario: Each valid seaborn_context string.
        Expectation: set_theme receives the exact context string.
        """
        ps_sns.plotstyle_theme("nature", seaborn_context=seaborn_context)
        fake_sns.set_theme.assert_called_once_with(style="ticks", context=seaborn_context)

    def test_plotstyle_theme_raises_importerror_without_seaborn(self, ps_sns, fake_plotstyle_use):
        """
        Description: plotstyle_theme must surface ImportError when seaborn is absent.
        Scenario: seaborn is removed from sys.modules.
        Expectation: ImportError propagates from the deferred import.
        """
        with patch.dict(sys.modules, {"seaborn": None}), pytest.raises(ImportError):
            ps_sns.plotstyle_theme("nature")

    def test_plotstyle_theme_propagates_use_valueerror(self, ps_sns, fake_sns, fake_plotstyle_use):
        """
        Description: An unrecognised journal name must raise ValueError (from use).
        Scenario: fake_plotstyle_use is configured to raise ValueError.
        Expectation: ValueError propagates out of plotstyle_theme.
        """
        fake_plotstyle_use.side_effect = ValueError("Unknown journal: 'unknown'")
        with pytest.raises(ValueError, match="Unknown journal"):
            ps_sns.plotstyle_theme("unknown")

    def test_plotstyle_theme_does_not_install_persistent_patch(
        self, ps_sns, fake_sns, fake_plotstyle_use
    ):
        """
        Description: plotstyle_theme is documented as a one-shot helper; it must
                     not install the monkey-patch on sns.set_theme.
        Scenario: plotstyle_theme is called; then _ORIGINAL_SET_THEME is inspected.
        Expectation: _ORIGINAL_SET_THEME remains None.
        """
        ps_sns.plotstyle_theme("nature")
        assert ps_sns._ORIGINAL_SET_THEME is None

    @pytest.mark.parametrize(
        "journal",
        ["nature", "ieee", "science", "acs"],
    )
    def test_plotstyle_theme_forwards_journal_name(
        self, ps_sns, fake_sns, fake_plotstyle_use, journal
    ):
        """
        Description: The journal argument must reach plotstyle.use unchanged.
        Scenario: Various journal preset name strings.
        Expectation: use is invoked with the exact journal string.
        """
        ps_sns.plotstyle_theme(journal)
        fake_plotstyle_use.assert_called_once_with(journal)


# ===========================================================================
# Public __all__ contract
# ===========================================================================


class TestPublicAPI:
    """Verify the module's declared public interface."""

    @pytest.mark.parametrize(
        "name",
        [
            "capture_overrides",
            "reapply_overrides",
            "patch_seaborn",
            "unpatch_seaborn",
            "plotstyle_theme",
        ],
    )
    def test_all_contains_expected_names(self, ps_sns, name):
        """
        Description: Each documented public function must appear in __all__.
        Scenario: Inspect ps_sns.__all__ for each expected name.
        Expectation: The name is present.
        """
        assert name in ps_sns.__all__

    def test_all_length(self, ps_sns):
        """
        Description: __all__ must not silently expose undocumented symbols.
        Scenario: Count entries in __all__.
        Expectation: Exactly 5 names are exported.
        """
        assert len(ps_sns.__all__) == 5

    @pytest.mark.parametrize(
        "name",
        [
            "capture_overrides",
            "reapply_overrides",
            "patch_seaborn",
            "unpatch_seaborn",
            "plotstyle_theme",
        ],
    )
    def test_functions_are_callable(self, ps_sns, name):
        """
        Description: Every name in __all__ must resolve to a callable.
        Scenario: getattr on the module for each exported name.
        Expectation: callable() returns True.
        """
        assert callable(getattr(ps_sns, name))


# ===========================================================================
# Integration-style: capture → patch → set_theme → reapply round-trip
# ===========================================================================


class TestIntegrationRoundTrip:
    """End-to-end tests combining multiple public functions."""

    def test_full_patch_round_trip(self, ps_sns, fake_sns):
        """
        Description: Simulates the complete seaborn_compatible=True workflow.
        Scenario: capture → patch → set_theme (which would normally reset rcParams)
                  → verify PlotStyle params survived.
        Expectation: plt.rcParams retains the captured font.size after set_theme.
        """
        ps_sns.capture_overrides({"font.size": 6.0})
        ps_sns.patch_seaborn()
        fake_sns.set_theme(style="ticks", context="paper")
        assert plt.rcParams["font.size"] == pytest.approx(6.0)
        ps_sns.unpatch_seaborn()

    def test_unpatch_stops_reapply_on_subsequent_set_theme(self, ps_sns, fake_sns, sample_params):
        """
        Description: After unpatching, set_theme no longer triggers reapply.
        Scenario: Patch installed and removed; a new set_theme call happens;
                  then a rcParam is manually changed to a sentinel value.
        Expectation: The sentinel value from manual override is not clobbered by
                     an unexpected reapply_overrides call.
        """
        ps_sns.capture_overrides(sample_params)
        ps_sns.patch_seaborn()
        ps_sns.unpatch_seaborn()

        # At this point set_theme is the original mock — no reapply side effect.
        # Manually change font.size to something different.
        plt.rcParams["font.size"] = 99.0
        fake_sns.set_theme(style="dark")  # original mock; no reapply

        # Font size should remain 99.0 — reapply was NOT called.
        assert plt.rcParams["font.size"] == pytest.approx(99.0)

    def test_capture_then_reapply_without_patch(self, ps_sns):
        """
        Description: capture + reapply can be used without the patch machinery.
        Scenario: No patch; capture then reapply called directly (Strategy 2 style).
        Expectation: plt.rcParams updated as documented.
        """
        ps_sns.capture_overrides({"axes.linewidth": 0.5})
        ps_sns.reapply_overrides()
        assert plt.rcParams["axes.linewidth"] == pytest.approx(0.5)

    def test_plotstyle_theme_set_theme_kwargs_complete(self, ps_sns, fake_sns, fake_plotstyle_use):
        """
        Description: plotstyle_theme must pass both style and context to set_theme.
        Scenario: Explicit non-default arguments.
        Expectation: set_theme called with correct keyword arguments.
        """
        ps_sns.plotstyle_theme("nature", seaborn_style="whitegrid", seaborn_context="notebook")
        fake_sns.set_theme.assert_called_once_with(style="whitegrid", context="notebook")
        fake_plotstyle_use.assert_called_once_with("nature")
