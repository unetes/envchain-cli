"""Summarise a chain or registry into a human-readable report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ChainSummary:
    chain_name: str
    parent: Optional[str]
    var_count: int
    keys: List[str] = field(default_factory=list)
    inherited_keys: List[str] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(set(self.keys) | set(self.inherited_keys))

    def to_dict(self) -> Dict:
        return {
            "chain": self.chain_name,
            "parent": self.parent,
            "own_var_count": self.var_count,
            "inherited_var_count": len(self.inherited_keys),
            "total_var_count": self.total_keys,
            "keys": sorted(self.keys),
            "inherited_keys": sorted(self.inherited_keys),
        }


@dataclass
class RegistrySummary:
    chain_count: int
    chain_summaries: List[ChainSummary] = field(default_factory=list)

    @property
    def total_vars(self) -> int:
        return sum(s.var_count for s in self.chain_summaries)

    def to_dict(self) -> Dict:
        return {
            "chain_count": self.chain_count,
            "total_own_vars": self.total_vars,
            "chains": [s.to_dict() for s in self.chain_summaries],
        }


def summarise_chain(chain) -> ChainSummary:
    """Produce a summary for a single chain."""
    own_vars = chain.vars or {}
    own_keys = list(own_vars.keys())

    inherited_keys: List[str] = []
    if chain.parent:
        try:
            resolved = chain.resolve()
        except Exception:
            resolved = own_vars
        inherited_keys = [k for k in resolved if k not in own_vars]

    return ChainSummary(
        chain_name=chain.name,
        parent=chain.parent,
        var_count=len(own_keys),
        keys=own_keys,
        inherited_keys=inherited_keys,
    )


def summarise_registry(registry) -> RegistrySummary:
    """Produce a summary for all chains in a registry."""
    names = registry.list() if hasattr(registry, "list") else []
    summaries = []
    for name in sorted(names):
        chain = registry.get(name)
        if chain is not None:
            summaries.append(summarise_chain(chain))
    return RegistrySummary(chain_count=len(summaries), chain_summaries=summaries)
