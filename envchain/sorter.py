"""Sort environment variable keys within chains by various strategies."""

from __future__ import annotations

from typing import Dict, List, Literal

SortStrategy = Literal["alpha", "alpha_desc", "length", "length_desc"]

AVAILABLE_STRATEGIES: List[SortStrategy] = [
    "alpha",
    "alpha_desc",
    "length",
    "length_desc",
]


class SortError(Exception):
    """Raised when sorting cannot be performed."""


def sort_vars(
    vars_: Dict[str, str],
    strategy: SortStrategy = "alpha",
) -> Dict[str, str]:
    """Return a new dict with keys ordered according to *strategy*.

    Args:
        vars_: Mapping of key -> value to sort.
        strategy: One of the AVAILABLE_STRATEGIES.

    Returns:
        Ordered dict with the same contents, keys in sorted order.

    Raises:
        SortError: If an unknown strategy is supplied.
    """
    if strategy not in AVAILABLE_STRATEGIES:
        raise SortError(
            f"Unknown sort strategy '{strategy}'. "
            f"Available: {', '.join(AVAILABLE_STRATEGIES)}"
        )

    if strategy == "alpha":
        keys = sorted(vars_.keys(), key=str.lower)
    elif strategy == "alpha_desc":
        keys = sorted(vars_.keys(), key=str.lower, reverse=True)
    elif strategy == "length":
        keys = sorted(vars_.keys(), key=lambda k: (len(k), k.lower()))
    elif strategy == "length_desc":
        keys = sorted(vars_.keys(), key=lambda k: (-len(k), k.lower()))
    else:  # pragma: no cover
        keys = list(vars_.keys())

    return {k: vars_[k] for k in keys}


def sort_chain_vars(chain_name: str, registry, strategy: SortStrategy = "alpha") -> Dict[str, str]:
    """Resolve and sort a chain's *own* variables from the registry.

    Returns the sorted mapping (does not mutate the registry).
    """
    chain = registry.get(chain_name)
    if chain is None:
        raise SortError(f"Chain '{chain_name}' not found in registry.")
    return sort_vars(chain.vars, strategy)
