"""Copy or clone chains, with optional variable filtering."""

from __future__ import annotations

from typing import Iterable

from envchain.registry import ChainRegistry
from envchain.validator import validate_chain_name, validate_key


class CopyError(Exception):
    """Raised when a chain copy operation cannot be completed."""


def copy_chain(
    registry: ChainRegistry,
    src: str,
    dst: str,
    *,
    include_keys: Iterable[str] | None = None,
    exclude_keys: Iterable[str] | None = None,
    inherit_parent: bool = True,
    overwrite: bool = False,
) -> dict:
    """Copy *src* chain to *dst*, returning the new chain dict.

    Parameters
    ----------
    include_keys:
        When provided, only these keys are copied.
    exclude_keys:
        Keys to omit from the copy (applied after *include_keys* filter).
    inherit_parent:
        If True, the copied chain keeps the parent of *src*.
    overwrite:
        Allow overwriting an existing *dst* chain.
    """
    validate_chain_name(dst)

    src_chain = registry.get(src)
    if src_chain is None:
        raise CopyError(f"Source chain '{src}' does not exist.")

    if not overwrite and registry.get(dst) is not None:
        raise CopyError(
            f"Destination chain '{dst}' already exists. Use overwrite=True to replace it."
        )

    src_vars: dict = src_chain.get("vars", {})

    # Apply include filter
    if include_keys is not None:
        include_set = set(include_keys)
        for k in include_set:
            validate_key(k)
        src_vars = {k: v for k, v in src_vars.items() if k in include_set}

    # Apply exclude filter
    if exclude_keys is not None:
        exclude_set = set(exclude_keys)
        src_vars = {k: v for k, v in src_vars.items() if k not in exclude_set}

    parent = src_chain.get("parent") if inherit_parent else None

    registry.add(dst, vars=dict(src_vars), parent=parent)
    return registry.get(dst)
