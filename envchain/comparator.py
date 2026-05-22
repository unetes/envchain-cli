"""Compare two chains side-by-side, showing resolved variable values."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envchain.chain import resolve
from envchain.registry import ChainRegistry


@dataclass
class CompareRow:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]

    @property
    def is_same(self) -> bool:
        return self.left_value == self.right_value

    @property
    def status(self) -> str:
        if self.left_value is None:
            return "right_only"
        if self.right_value is None:
            return "left_only"
        if self.left_value == self.right_value:
            return "same"
        return "different"


@dataclass
class CompareResult:
    left_chain: str
    right_chain: str
    rows: List[CompareRow] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return any(not r.is_same for r in self.rows)

    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"same": 0, "different": 0, "left_only": 0, "right_only": 0}
        for row in self.rows:
            counts[row.status] += 1
        return counts


def compare_chains(
    registry: ChainRegistry,
    left_name: str,
    right_name: str,
    resolved: bool = True,
) -> CompareResult:
    """Compare two chains, optionally using fully resolved (inherited) vars."""
    left_chain = registry.get(left_name)
    right_chain = registry.get(right_name)

    if resolved:
        left_vars = resolve(left_chain, registry)
        right_vars = resolve(right_chain, registry)
    else:
        left_vars = dict(left_chain.vars)
        right_vars = dict(right_chain.vars)

    all_keys = sorted(set(left_vars) | set(right_vars))
    rows = [
        CompareRow(
            key=k,
            left_value=left_vars.get(k),
            right_value=right_vars.get(k),
        )
        for k in all_keys
    ]
    return CompareResult(left_chain=left_name, right_chain=right_name, rows=rows)
