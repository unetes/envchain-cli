"""In-memory registry for managing Chain instances."""

from __future__ import annotations

from typing import Dict, Iterator, List, Optional

from envchain.chain import Chain


class ChainRegistry:
    """Stores and manages all chains for a project."""

    def __init__(self) -> None:
        self._chains: Dict[str, Chain] = {}

    def add(self, chain: Chain) -> None:
        """Register a chain.  Raises ValueError if name already exists."""
        if chain.name in self._chains:
            raise ValueError(f"Chain '{chain.name}' already exists.")
        self._chains[chain.name] = chain

    def get(self, name: str) -> Chain:
        """Retrieve a chain by name.  Raises KeyError if not found."""
        if name not in self._chains:
            raise KeyError(f"Chain '{name}' not found.")
        return self._chains[name]

    def remove(self, name: str) -> None:
        """Delete a chain by name.  Raises KeyError if not found."""
        if name not in self._chains:
            raise KeyError(f"Chain '{name}' not found.")
        del self._chains[name]

    def list_names(self) -> List[str]:
        """Return sorted list of all chain names."""
        return sorted(self._chains.keys())

    def resolve(self, name: str) -> Dict[str, str]:
        """Resolve and return the merged environment variables for a chain."""
        chain = self.get(name)
        return chain.resolve(self._chains)

    def __iter__(self) -> Iterator[Chain]:
        return iter(self._chains.values())

    def __len__(self) -> int:
        return len(self._chains)
