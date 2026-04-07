"""Measure PlotStyle cold-import time.

Spawns a fresh Python interpreter for each trial so that no cached modules
from the current process pollute the measurement.  The target is a cold import
in under :data:`TARGET_MS` milliseconds.

Usage
-----
Run directly::

    python scripts/benchmark_import.py

Or with custom options::

    python scripts/benchmark_import.py --trials 5 --target-ms 150

Exit codes
----------
- ``0`` — all trials completed and the median import time is within the target.
- ``1`` — import failed in any trial, or the median exceeds the target.

Design notes
------------
- A single trial is vulnerable to OS scheduling jitter; the script runs
  :data:`DEFAULT_TRIALS` trials by default and reports the median, which is
  more robust than a single measurement or the mean (which is skewed by
  occasional cold-cache misses).
- The measurement code is kept as a one-liner injected via ``-c`` so there
  is no temporary file to clean up and no additional filesystem I/O between
  the timer start and the import statement.
- :func:`statistics.median` is used rather than ``sorted()[n//2]`` for
  clarity and correct behaviour on both odd and even trial counts.
"""

from __future__ import annotations

import argparse
import statistics
import subprocess
import sys
from typing import Final

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default number of subprocess trials to run.
DEFAULT_TRIALS: Final[int] = 3

#: Default maximum acceptable cold-import time in milliseconds.
TARGET_MS: Final[float] = 1000.0

# One-liner injected into each subprocess.  Using perf_counter gives
# sub-millisecond resolution on all supported platforms.
_MEASURE_CODE: Final[str] = (
    "import time as _t; _s = _t.perf_counter(); import plotstyle; print(_t.perf_counter() - _s)"
)


# ---------------------------------------------------------------------------
# Core measurement
# ---------------------------------------------------------------------------


def _run_single_trial() -> float:
    """Spawn a fresh interpreter and return the plotstyle import time in seconds.

    Returns
    -------
        Elapsed time in seconds as reported by :func:`time.perf_counter`
        inside the child process.

    Raises
    ------
        RuntimeError: If the child process exits with a non-zero return code,
            with the child's ``stderr`` included in the message so the caller
            can surface it to the user.
        ValueError: If the child's ``stdout`` cannot be parsed as a float,
            which indicates an unexpected output format.
    """
    result = subprocess.run(
        [sys.executable, "-c", _MEASURE_CODE],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Include stderr verbatim so the caller can display the full traceback.
        raise RuntimeError(result.stderr.strip())

    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise ValueError(
            f"Unexpected output from measurement subprocess: {result.stdout!r}"
        ) from exc


def _run_trials(n: int) -> list[float]:
    """Run *n* measurement trials and return all elapsed times in seconds.

    Args:
        n: Number of trials to execute.  Must be ≥ 1.

    Returns
    -------
        List of *n* float values (seconds), one per successful trial.

    Raises
    ------
        RuntimeError: Propagated from :func:`_run_single_trial` on the first
            failed trial.  Subsequent trials are not attempted.
        ValueError: If *n* is less than 1.
    """
    if n < 1:
        raise ValueError(f"Number of trials must be ≥ 1, got {n!r}.")

    times: list[float] = []
    for i in range(1, n + 1):
        elapsed = _run_single_trial()
        ms = elapsed * 1_000
        print(f"  Trial {i}/{n}: {ms:.1f}ms")
        times.append(elapsed)

    return times


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Return the configured argument parser for this script.

    Factored out of :func:`main` so tests can instantiate the parser without
    invoking :func:`sys.exit`.

    Returns
    -------
        A fully configured :class:`~argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="benchmark_import",
        description=(
            "Measure PlotStyle cold-import time over multiple trials.\n"
            f"Target: < {TARGET_MS:.0f}ms (median across trials)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=DEFAULT_TRIALS,
        metavar="N",
        help=f"Number of subprocess trials to run (default: {DEFAULT_TRIALS}).",
    )
    parser.add_argument(
        "--target-ms",
        type=float,
        default=TARGET_MS,
        metavar="MS",
        help=f"Maximum acceptable median import time in ms (default: {TARGET_MS:.0f}).",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the import-time benchmark and report results.

    Args:
        argv: Argument list to parse.  Pass ``None`` to use ``sys.argv[1:]``,
            or supply a list explicitly for testing.

    Returns
    -------
        ``0`` if the median import time is within *target_ms*; ``1`` otherwise.
    """
    args = _build_parser().parse_args(argv)
    n_trials: int = args.trials
    target_s: float = args.target_ms / 1_000

    print(f"Benchmarking plotstyle import ({n_trials} trial(s), target < {args.target_ms:.0f}ms) …")

    try:
        times = _run_trials(n_trials)
    except RuntimeError as exc:
        # A non-zero child exit code means the import itself failed.
        print(f"\nImport failed:\n{exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"\nMeasurement error: {exc}", file=sys.stderr)
        return 1

    median_s: float = statistics.median(times)
    median_ms: float = median_s * 1_000
    target_ms: float = args.target_ms

    print()
    print(f"Median import time : {median_ms:.1f}ms")
    print(f"Target             : < {target_ms:.0f}ms")

    if n_trials > 1:
        min_ms = min(times) * 1_000
        max_ms = max(times) * 1_000
        stdev_ms = statistics.stdev(times) * 1_000
        print(f"Min / Max          : {min_ms:.1f}ms / {max_ms:.1f}ms")
        print(f"Std dev            : {stdev_ms:.1f}ms")

    print()
    if median_s > target_s:
        over_ms = median_ms - target_ms
        print(
            f"⚠  SLOW — median {median_ms:.1f}ms exceeds target by {over_ms:.1f}ms.\n"
            '   Profile with: python -X importtime -c "import plotstyle"'
        )
        return 1

    print(f"✓  OK — median import time {median_ms:.1f}ms is within the {target_ms:.0f}ms target.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
