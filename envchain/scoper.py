"""Scoper: restrict variable visibility to a defined set of allowed keys per chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised when a scoping operation fails."""


@dataclass
class ScopeRule:
    chain: str
    allowed_keys: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"chain": self.chain, "allowed_keys": sorted(self.allowed_keys)}

    @classmethod
    def from_dict(cls, data: dict) -> "ScopeRule":
        return cls(chain=data["chain"], allowed_keys=list(data.get("allowed_keys", [])))


@dataclass
class ScopeIndex:
    _rules: Dict[str, ScopeRule] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {name: rule.to_dict() for name, rule in self._rules.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "ScopeIndex":
        idx = cls()
        for name, rule_data in data.items():
            idx._rules[name] = ScopeRule.from_dict(rule_data)
        return idx


def set_scope(index: ScopeIndex, chain: str, allowed_keys: List[str]) -> ScopeRule:
    """Define or replace the scope rule for a chain."""
    if not chain:
        raise ScopeError("Chain name must not be empty.")
    rule = ScopeRule(chain=chain, allowed_keys=list(allowed_keys))
    index._rules[chain] = rule
    return rule


def remove_scope(index: ScopeIndex, chain: str) -> None:
    """Remove the scope rule for a chain."""
    if chain not in index._rules:
        raise ScopeError(f"No scope rule found for chain '{chain}'.")
    del index._rules[chain]


def get_scope(index: ScopeIndex, chain: str) -> Optional[ScopeRule]:
    """Return the scope rule for a chain, or None if not scoped."""
    return index._rules.get(chain)


def apply_scope(index: ScopeIndex, chain: str, vars_: Dict[str, str]) -> Dict[str, str]:
    """Filter vars to only those permitted by the scope rule, if one exists."""
    rule = get_scope(index, chain)
    if rule is None:
        return dict(vars_)
    allowed = set(rule.allowed_keys)
    return {k: v for k, v in vars_.items() if k in allowed}


def list_scopes(index: ScopeIndex) -> List[ScopeRule]:
    """Return all scope rules sorted by chain name."""
    return [index._rules[k] for k in sorted(index._rules)]
