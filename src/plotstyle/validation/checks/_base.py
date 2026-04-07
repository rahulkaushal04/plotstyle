"""Base check infrastructure — registration decorator and type definitions.

This module is the backbone of PlotStyle's validation system.  It provides:

- :data:`CheckFunc` — a type alias for the callable signature that every
  validation check function must implement.
- :data:`_REGISTERED_CHECKS` — the module-level list that acts as the check
  registry.
- :func:`check` — a decorator that appends a function to the registry.
- :func:`get_registered_checks` — the only public accessor to the registry,
  returning a snapshot copy.

Adding a new check
------------------
1. Create a new module inside :mod:`plotstyle.validation.checks`
   (e.g., ``my_check.py``).
2. Define a function with the signature
   ``(fig: Figure, spec: JournalSpec) -> list[CheckResult]`` and decorate it
   with ``@check``.
3. Import the new module in ``plotstyle/validation/checks/__init__.py`` so
   that the decorator runs at import time and registers the function.

Example
-------
    >>> from plotstyle.validation.checks._base import check, get_registered_checks
    >>> from matplotlib.figure import Figure
    >>> from plotstyle.specs.schema import JournalSpec
    >>> from plotstyle.validation.report import CheckResult, CheckStatus
    >>>
    >>> @check
    ... def check_my_property(fig: Figure, spec: JournalSpec) -> list[CheckResult]:
    ...     return [CheckResult(CheckStatus.PASS, "my.property", "All good.")]
    >>>
    >>> check_my_property in get_registered_checks()
    True

Notes
-----
- The registry is a plain :class:`list`; registration order is preserved and
  determines the order in which checks appear in :class:`ValidationReport`.
- :func:`get_registered_checks` returns a *shallow copy* so that external
  callers cannot accidentally mutate the registry (e.g., by calling
  ``get_registered_checks().clear()``).
- The :class:`~typing.Final` annotation on ``_REGISTERED_CHECKS`` prevents
  reassignment of the list object itself; items may still be appended by the
  :func:`check` decorator (which is the intended mutation path).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from matplotlib.figure import Figure

from plotstyle.specs.schema import JournalSpec
from plotstyle.validation.report import CheckResult

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

#: Callable type for all registered validation check functions.
#:
#: Every function decorated with :func:`check` must accept exactly these two
#: positional arguments and return a (possibly empty) list of results.
CheckFunc = Callable[[Figure, JournalSpec], list[CheckResult]]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# The list is intentionally module-global so that the @check decorator can
# append to it from any submodule without needing a shared mutable object to
# be passed around.  Final prevents reassignment; the list itself is mutable.
_REGISTERED_CHECKS: Final[list[CheckFunc]] = []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check(func: CheckFunc) -> CheckFunc:
    """Register a function as a PlotStyle validation check.

    This decorator appends *func* to the global registry and returns it
    unchanged, so the decorated function can still be called directly in
    tests or composed into other checks.

    Args:
        func: A callable with signature
            ``(fig: Figure, spec: JournalSpec) -> list[CheckResult]``.
            The function should be pure with respect to the registry (i.e.,
            it should not call :func:`get_registered_checks` or mutate the
            figure or spec).

    Returns
    -------
        *func* unchanged, enabling the decorator to be used transparently.

    Raises
    ------
        TypeError: Implicitly, if *func* is not callable — the
            :class:`list.append` call will succeed, but mypy / pyright will
            flag the type mismatch at the call site.

    Example:
        >>> @check
        ... def check_my_rule(fig, spec):
        ...     return [CheckResult(CheckStatus.PASS, "my.rule", "OK.")]
        >>> check_my_rule in get_registered_checks()
        True

    Notes
    -----
        - Each call to ``@check`` appends exactly once; applying the decorator
          twice (which would be a bug) would register the function twice.
        - Registration is permanent for the lifetime of the Python process.
          Tests that need an isolated registry should patch ``_REGISTERED_CHECKS``
          directly (e.g., via ``unittest.mock.patch``).
    """
    _REGISTERED_CHECKS.append(func)
    return func


def get_registered_checks() -> list[CheckFunc]:
    """Return a snapshot of all currently registered validation check functions.

    Returns a *shallow copy* of the internal registry so that mutations to
    the returned list do not affect the registry itself.  The order of
    functions in the returned list matches their registration order, which
    determines the order of :class:`~plotstyle.validation.report.CheckResult`
    entries in a :class:`~plotstyle.validation.report.ValidationReport`.

    Returns
    -------
        A new :class:`list` containing every :data:`CheckFunc` that has been
        registered via the :func:`check` decorator since the interpreter
        started.

    Example:
        >>> checks = get_registered_checks()
        >>> len(checks) >= 5  # at least the built-in check modules
        True
    """
    # Return a copy so external callers cannot mutate the registry.
    return list(_REGISTERED_CHECKS)
