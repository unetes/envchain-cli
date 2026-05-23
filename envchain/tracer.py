"""Trace the resolution path of a key through a chain's inheritance hierarchy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class TraceError(Exception):
    """Raised when tracing fails."""


@dataclass
class TraceStep:
    """A single step in the resolution trace."""

    chain_name: str
    key: str
    value: Optional[str]
    resolved: bool  # True if the key was found at this level

    def to_dict(self) -> dict:
        return {
            "chain": self.chain_name,
            "key": self.key,
            "value": self.value,
            "resolved": self.resolved,
        }

    def __str__(self) -> str:
        if self.resolved:
            return f"[{self.chain_name}] {self.key}={self.value!r}  <-- resolved here"
        return f"[{self.chain_name}] {self.key} (not set)"


@dataclass
class TraceResult:
    """Full trace for a key lookup."""

    key: str
    steps: List[TraceStep] = field(default_factory=list)
    final_value: Optional[str] = None
    found: bool = False

    def summary(self) -> str:
        lines = [f"Trace for key '{self.key}':"] + [str(s) for s in self.steps]
        if not self.found:
            lines.append(f"Key '{self.key}' not found in any ancestor.")
        return "\n".join(lines)


def trace_key(registry, chain_name: str, key: str) -> TraceResult:
    """Walk the inheritance chain and record where *key* is first defined.

    Parameters
    ----------
    registry:
        A :class:`~envchain.registry.ChainRegistry` instance.
    chain_name:
        The name of the chain to start tracing from.
    key:
        The environment variable key to trace.

    Returns
    -------
    TraceResult
        Ordered list of steps from *chain_name* up to the root.
    """
    from envchain.chain import _ancestors  # avoid circular at module level

    result = TraceResult(key=key)

    chain = registry.get(chain_name)
    if chain is None:
        raise TraceError(f"Chain '{chain_name}' not found.")

    # Build ordered list: current chain first, then ancestors
    chain_names = [chain_name] + list(_ancestors(registry, chain_name))

    for name in chain_names:
        c = registry.get(name)
        if c is None:
            continue
        own_vars = c.vars if hasattr(c, "vars") else {}
        if key in own_vars:
            step = TraceStep(
                chain_name=name, key=key, value=own_vars[key], resolved=True
            )
            result.steps.append(step)
            result.final_value = own_vars[key]
            result.found = True
            break
        else:
            step = TraceStep(chain_name=name, key=key, value=None, resolved=False)
            result.steps.append(step)

    return result
