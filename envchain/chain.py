"""Core chain model for envchain-cli.

Represents a named environment variable chain with optional parent
inheritance and per-chain overrides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Chain:
    """A named collection of environment variables that can inherit from a parent chain."""

    name: str
    variables: Dict[str, str] = field(default_factory=dict)
    parent: Optional[str] = None

    def resolve(self, registry: Dict[str, "Chain"]) -> Dict[str, str]:
        """Return the fully-resolved environment variables for this chain.

        Resolution order (last writer wins):
        1. Root ancestor variables
        2. Each intermediate ancestor's variables
        3. This chain's own variables

        Args:
            registry: Mapping of chain name -> Chain for all known chains.

        Returns:
            A flat dict of resolved environment variables.

        Raises:
            ValueError: If a circular inheritance reference is detected.
        """
        ancestors = self._ancestors(registry)
        resolved: Dict[str, str] = {}
        for ancestor in reversed(ancestors):
            resolved.update(ancestor.variables)
        resolved.update(self.variables)
        return resolved

    def _ancestors(self, registry: Dict[str, "Chain"]) -> List["Chain"]:
        """Return ordered list of ancestor chains (closest first)."""
        ancestors: List[Chain] = []
        visited = {self.name}
        current_name = self.parent

        while current_name is not None:
            if current_name in visited:
                raise ValueError(
                    f"Circular inheritance detected: '{current_name}' is already in the chain."
                )
            if current_name not in registry:
                raise ValueError(f"Parent chain '{current_name}' does not exist.")
            visited.add(current_name)
            parent_chain = registry[current_name]
            ancestors.append(parent_chain)
            current_name = parent_chain.parent

        return ancestors
