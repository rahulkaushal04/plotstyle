"""Base check infrastructure — registration decorator and type definitions.

Internal module; not part of the public API.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from matplotlib.figure import Figure

from plotstyle.specs.schema import JournalSpec
from plotstyle.validation.report import CheckResult

CheckFunc = Callable[[Figure, JournalSpec], list[CheckResult]]

_REGISTERED_CHECKS: Final[list[CheckFunc]] = []


def check(func: CheckFunc) -> CheckFunc:
    """Register a validation check function and return it unchanged.

    Use as a decorator on any function with the signature
    ``(Figure, JournalSpec) -> list[CheckResult]``.

    Parameters
    ----------
    func : CheckFunc
        The validation check function to register.

    Returns
    -------
    CheckFunc
        *func* unchanged.
    """
    _REGISTERED_CHECKS.append(func)
    return func


def get_registered_checks() -> list[CheckFunc]:
    """Return a snapshot of all registered validation check functions.

    Returns
    -------
    list[CheckFunc]
        All functions registered via ``check``, in registration order.
        Mutating the returned list does not affect the internal registry.
    """
    return list(_REGISTERED_CHECKS)
