"""Check registry — discovers and executes all registered validation checks.

This package serves two roles:

1. **Auto-discovery** — importing this package causes each check sub-module
   (``colors``, ``dimensions``, ``export``, ``lines``, ``typography``) to be
   imported, which triggers their ``@check`` decorators and populates the
   global registry in :mod:`plotstyle.validation.checks._base`.

2. **Execution** — :func:`run_all` iterates over every registered check
   function in registration order and aggregates their results.

Adding a new check module
-------------------------
1. Create ``plotstyle/validation/checks/my_check.py`` and decorate at least
   one function with ``@check``.
2. Add ``from plotstyle.validation.checks import my_check  # noqa: F401``
   to the imports below so the module is loaded when this package is imported.

Example
-------
    >>> import matplotlib.pyplot as plt
    >>> from plotstyle.specs import registry
    >>> from plotstyle.validation.checks import run_all
    >>> fig, ax = plt.subplots()
    >>> spec = registry.get("nature")
    >>> results = run_all(fig, spec)
    >>> [r.check_name for r in results]
    ['color.red_green', 'dimensions.width', ...]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------
# Side-effect imports — trigger @check decorators to populate the registry.
# The unused-import warnings are suppressed because the import itself is the
# intended side effect.
# ---------------------------------------------------------------------------
from plotstyle.validation.checks import (
    colors,  # noqa: F401
    dimensions,  # noqa: F401
    export,  # noqa: F401
    lines,  # noqa: F401
    typography,  # noqa: F401
)
from plotstyle.validation.checks._base import get_registered_checks

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from plotstyle.specs.schema import JournalSpec
    from plotstyle.validation.report import CheckResult


def run_all(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    """Execute every registered validation check and return the aggregated results.

    Check functions are invoked in registration order (which follows the import
    order of the sub-modules listed above).  Each function may return zero or
    more :class:`~plotstyle.validation.report.CheckResult` objects; all results
    are collected into a single flat list.

    Args:
        fig: The :class:`~matplotlib.figure.Figure` to validate.  Passed
            unchanged to every check function.
        spec: The :class:`~plotstyle.specs.schema.JournalSpec` that defines
            the validation rules.  Passed unchanged to every check function.

    Returns
    -------
        A flat :class:`list` of :class:`~plotstyle.validation.report.CheckResult`
        objects from all executed checks, in execution order.  An empty list is
        returned if no checks are registered (which should not happen in normal
        usage).

    Raises
    ------
        Any exception raised by an individual check function propagates
        immediately without wrapping.  Check functions are expected not to
        raise; they should represent failures as ``CheckStatus.FAIL`` results.

    Example:
        >>> from plotstyle.validation.checks import run_all
        >>> results = run_all(fig, spec)
        >>> failures = [r for r in results if r.is_failure]
    """
    results: list[CheckResult] = []

    for check_fn in get_registered_checks():
        # Each check returns a list (possibly empty); extend to flatten.
        results.extend(check_fn(fig, spec))

    return results
