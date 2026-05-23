"""Promote variables from a child chain up to a parent chain."""

from __future__ import annotations

from typing import Sequence

from envchain.registry import ChainRegistry


class PromoteError(Exception):
    """Raised when a promotion operation fails."""


def promote_keys(
    registry: ChainRegistry,
    source_chain: str,
    target_chain: str,
    keys: Sequence[str],
    *,
    overwrite: bool = False,
    remove_from_source: bool = False,
) -> dict[str, str]:
    """Copy *keys* from *source_chain* into *target_chain*.

    Returns a mapping of {key: value} for every key that was promoted.

    Raises
    ------
    PromoteError
        If either chain does not exist, a key is missing from the source,
        or a key already exists in the target and *overwrite* is False.
    """
    source = registry.get(source_chain)
    if source is None:
        raise PromoteError(f"Source chain '{source_chain}' not found.")

    target = registry.get(target_chain)
    if target is None:
        raise PromoteError(f"Target chain '{target_chain}' not found.")

    source_vars: dict[str, str] = dict(source.vars)
    target_vars: dict[str, str] = dict(target.vars)

    promoted: dict[str, str] = {}

    for key in keys:
        if key not in source_vars:
            raise PromoteError(
                f"Key '{key}' not found in source chain '{source_chain}'."
            )
        if key in target_vars and not overwrite:
            raise PromoteError(
                f"Key '{key}' already exists in target chain '{target_chain}'. "
                "Use overwrite=True to replace it."
            )
        promoted[key] = source_vars[key]

    # Apply changes
    target_vars.update(promoted)
    registry.update_vars(target_chain, target_vars)

    if remove_from_source:
        for key in keys:
            source_vars.pop(key, None)
        registry.update_vars(source_chain, source_vars)

    return promoted
