"""Integration helpers: resolve all vars for every chain in a profile."""

from __future__ import annotations

from typing import Dict, List

from envchain.chain import resolve
from envchain.profiler import ProfileIndex, chains_for_profile, ProfileError
from envchain.registry import ChainRegistry


class ProfileResolutionError(Exception):
    """Raised when a chain in a profile cannot be resolved."""


def resolve_profile(
    index: ProfileIndex,
    registry: ChainRegistry,
    profile: str,
) -> Dict[str, Dict[str, str]]:
    """Return a mapping of chain_name -> resolved vars for all chains in *profile*.

    Raises ProfileResolutionError if *profile* is empty / unknown, or if any
    chain listed in the profile is not present in *registry*.
    """
    chains = chains_for_profile(index, profile)
    if not chains:
        raise ProfileResolutionError(
            f"Profile '{profile}' is empty or does not exist."
        )

    result: Dict[str, Dict[str, str]] = {}
    for chain_name in chains:
        chain = registry.get(chain_name)
        if chain is None:
            raise ProfileResolutionError(
                f"Chain '{chain_name}' (in profile '{profile}') not found in registry."
            )
        result[chain_name] = resolve(chain, registry)
    return result


def merged_profile_vars(
    index: ProfileIndex,
    registry: ChainRegistry,
    profile: str,
    *,
    chain_order: List[str] | None = None,
) -> Dict[str, str]:
    """Merge resolved vars from all chains in *profile* into a single dict.

    Later chains in *chain_order* (or alphabetical order) override earlier ones.
    """
    resolved = resolve_profile(index, registry, profile)
    order = chain_order if chain_order is not None else sorted(resolved)
    merged: Dict[str, str] = {}
    for name in order:
        if name in resolved:
            merged.update(resolved[name])
    return merged
