"""Chain aliasing: create short aliases that point to existing chains."""

from __future__ import annotations

from typing import Dict, List


class AliasError(Exception):
    """Raised for alias-related failures."""


class AliasIndex:
    """In-memory index mapping alias names to chain names."""

    def __init__(self, data: Dict[str, str] | None = None) -> None:
        self._map: Dict[str, str] = dict(data or {})

    def to_dict(self) -> Dict[str, str]:
        return dict(self._map)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "AliasIndex":
        return cls(data)


def add_alias(index: AliasIndex, alias: str, chain_name: str, overwrite: bool = False) -> None:
    """Register *alias* as a shorthand for *chain_name*."""
    if not alias:
        raise AliasError("Alias name must not be empty.")
    if not chain_name:
        raise AliasError("Chain name must not be empty.")
    if alias == chain_name:
        raise AliasError(f"Alias '{alias}' cannot point to itself.")
    if alias in index._map and not overwrite:
        raise AliasError(
            f"Alias '{alias}' already exists (points to '{index._map[alias]}'). "
            "Use overwrite=True to replace it."
        )
    index._map[alias] = chain_name


def remove_alias(index: AliasIndex, alias: str) -> None:
    """Remove an existing alias."""
    if alias not in index._map:
        raise AliasError(f"Alias '{alias}' does not exist.")
    del index._map[alias]


def resolve_alias(index: AliasIndex, alias: str) -> str:
    """Return the chain name that *alias* points to."""
    if alias not in index._map:
        raise AliasError(f"Alias '{alias}' does not exist.")
    return index._map[alias]


def list_aliases(index: AliasIndex) -> List[tuple[str, str]]:
    """Return all (alias, chain_name) pairs sorted by alias."""
    return sorted(index._map.items())


def aliases_for_chain(index: AliasIndex, chain_name: str) -> List[str]:
    """Return all aliases that point to *chain_name*, sorted."""
    return sorted(alias for alias, target in index._map.items() if target == chain_name)
