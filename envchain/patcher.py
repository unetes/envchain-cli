"""Patch (partial update) variables in a chain without replacing the whole set."""

from __future__ import annotations

from typing import Dict, List, Optional


class PatchError(Exception):
    """Raised when a patch operation cannot be completed."""


class PatchReport:
    """Summary of a patch operation."""

    def __init__(
        self,
        chain_name: str,
        added: List[str],
        updated: List[str],
        deleted: List[str],
    ) -> None:
        self.chain_name = chain_name
        self.added = sorted(added)
        self.updated = sorted(updated)
        self.deleted = sorted(deleted)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.updated) + len(self.deleted)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.updated:
            parts.append(f"~{len(self.updated)} updated")
        if self.deleted:
            parts.append(f"-{len(self.deleted)} deleted")
        if not parts:
            return f"[{self.chain_name}] no changes"
        return f"[{self.chain_name}] " + ", ".join(parts)


def patch_vars(
    chain,
    updates: Optional[Dict[str, str]] = None,
    deletions: Optional[List[str]] = None,
    allow_new: bool = True,
) -> PatchReport:
    """Apply a partial update to a chain's variables.

    Args:
        chain: A Chain object with a `.vars` dict attribute.
        updates: Keys to set or update.
        deletions: Keys to remove.
        allow_new: If False, raise PatchError when *updates* contains a key
                   not already present in the chain.

    Returns:
        PatchReport describing what changed.
    """
    updates = updates or {}
    deletions = deletions or []

    current: Dict[str, str] = dict(chain.vars)

    added: List[str] = []
    updated: List[str] = []
    deleted: List[str] = []

    for key, value in updates.items():
        if key in current:
            if current[key] != value:
                updated.append(key)
            current[key] = value
        else:
            if not allow_new:
                raise PatchError(
                    f"Key '{key}' does not exist in chain '{chain.name}' "
                    "and allow_new is False."
                )
            added.append(key)
            current[key] = value

    for key in deletions:
        if key not in current:
            raise PatchError(
                f"Cannot delete '{key}': not found in chain '{chain.name}'."
            )
        del current[key]
        deleted.append(key)

    chain.vars = current
    return PatchReport(
        chain_name=chain.name,
        added=added,
        updated=updated,
        deleted=deleted,
    )
