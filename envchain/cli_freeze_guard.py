"""Utility to guard write operations against frozen chains."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeVar

from envchain.freezer import FreezeError, is_frozen, freeze_reason, load_freeze_index

_DEFAULT_INDEX = Path(".envchain") / "freeze_index.json"

F = TypeVar("F", bound=Callable[..., int])


def check_not_frozen(chain_name: str, index_path: Path = _DEFAULT_INDEX) -> None:
    """Raise *FreezeError* if *chain_name* is currently frozen.

    This helper is intended to be called at the start of any CLI command that
    would modify a chain's variables.
    """
    idx = load_freeze_index(index_path)
    if is_frozen(idx, chain_name):
        reason = freeze_reason(idx, chain_name)
        msg = f"Chain '{chain_name}' is frozen and cannot be modified."
        if reason:
            msg += f" Reason: {reason}"
        raise FreezeError(msg)


def guarded(chain_attr: str = "chain", index_path: Path = _DEFAULT_INDEX) -> Callable[[F], F]:
    """Decorator that prevents a CLI command from running on a frozen chain.

    *chain_attr* is the attribute name on the ``args`` namespace that holds the
    chain name.

    Returns exit-code **3** when the chain is frozen so callers can distinguish
    it from other error codes.
    """
    def decorator(fn: F) -> F:
        def wrapper(args, *extra, **kw):  # type: ignore[no-untyped-def]
            chain_name = getattr(args, chain_attr, None)
            if chain_name:
                try:
                    check_not_frozen(chain_name, index_path)
                except FreezeError as exc:
                    print(f"Frozen: {exc}")
                    return 3
            return fn(args, *extra, **kw)
        return wrapper  # type: ignore[return-value]
    return decorator
