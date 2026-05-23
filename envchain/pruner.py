"""Pruner: remove unused or duplicate variables from a chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class PruneError(Exception):
    """Raised when pruning cannot be completed."""


@dataclass
class PruneReport:
    chain_name: str
    removed_keys: List[str] = field(default_factory=list)
    kept_keys: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed_keys)

    def summary(self) -> str:
        if not self.removed_keys:
            return f"{self.chain_name}: nothing to prune"
        removed = ", ".join(sorted(self.removed_keys))
        return f"{self.chain_name}: removed {self.total_removed} key(s): {removed}"


def prune_empty_values(vars_: Dict[str, str]) -> PruneReport:
    """Return a PruneReport describing which keys have empty/whitespace values."""
    removed: List[str] = []
    kept: List[str] = []
    for key, value in vars_.items():
        if value.strip() == "":
            removed.append(key)
        else:
            kept.append(key)
    report = PruneReport(chain_name="", removed_keys=sorted(removed), kept_keys=sorted(kept))
    return report


def prune_chain(
    registry,
    chain_name: str,
    *,
    remove_empty: bool = True,
    keys: Optional[List[str]] = None,
    dry_run: bool = False,
) -> PruneReport:
    """Prune variables from *chain_name* in *registry*.

    Args:
        registry: A ChainRegistry instance.
        chain_name: Name of the chain to prune.
        remove_empty: When True, remove keys whose value is blank/whitespace.
        keys: Explicit list of keys to remove (overrides remove_empty logic).
        dry_run: When True, compute the report but do not mutate the registry.

    Returns:
        A PruneReport describing what was (or would be) removed.
    """
    chain = registry.get(chain_name)
    if chain is None:
        raise PruneError(f"Chain '{chain_name}' not found")

    vars_: Dict[str, str] = dict(chain.vars)

    if keys is not None:
        missing = [k for k in keys if k not in vars_]
        if missing:
            raise PruneError(f"Keys not found in '{chain_name}': {missing}")
        removed = sorted(keys)
        kept = sorted(k for k in vars_ if k not in keys)
    elif remove_empty:
        report = prune_empty_values(vars_)
        removed = report.removed_keys
        kept = report.kept_keys
    else:
        removed = []
        kept = sorted(vars_.keys())

    if not dry_run and removed:
        new_vars = {k: v for k, v in vars_.items() if k not in removed}
        chain.vars = new_vars

    report = PruneReport(chain_name=chain_name, removed_keys=removed, kept_keys=kept)
    return report
