"""Pin specific environment variable values in a chain, preventing them from being overridden by inheritance."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Set, List


class PinError(Exception):
    """Raised when a pin operation fails."""


@dataclass
class PinIndex:
    """Tracks which keys are pinned per chain."""
    _pins: Dict[str, Set[str]] = field(default_factory=dict)

    def pin(self, chain_name: str, key: str) -> None:
        """Pin a key in a chain so it cannot be overridden by inheritance."""
        if chain_name not in self._pins:
            self._pins[chain_name] = set()
        self._pins[chain_name].add(key)

    def unpin(self, chain_name: str, key: str) -> None:
        """Remove a pin from a key in a chain."""
        if chain_name not in self._pins or key not in self._pins[chain_name]:
            raise PinError(f"Key '{key}' is not pinned in chain '{chain_name}'")
        self._pins[chain_name].discard(key)

    def is_pinned(self, chain_name: str, key: str) -> bool:
        """Return True if the key is pinned in the given chain."""
        return key in self._pins.get(chain_name, set())

    def pinned_keys(self, chain_name: str) -> List[str]:
        """Return sorted list of pinned keys for a chain."""
        return sorted(self._pins.get(chain_name, set()))

    def all_pins(self) -> Dict[str, List[str]]:
        """Return all pins as a dict of chain -> sorted key list."""
        return {chain: sorted(keys) for chain, keys in self._pins.items() if keys}

    def to_dict(self) -> Dict[str, List[str]]:
        return self.all_pins()

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> "PinIndex":
        idx = cls()
        for chain, keys in data.items():
            for key in keys:
                idx.pin(chain, key)
        return idx


def apply_pins(resolved_vars: dict, chain_name: str, pin_index: PinIndex, parent_vars: dict) -> dict:
    """Given resolved vars (child overrides parent), enforce pins by restoring pinned values.

    Pinned keys in chain_name keep their value from chain_name's own vars and
    cannot be shadowed. If the chain itself doesn't define the key, a PinError is raised.
    """
    pinned = pin_index.pinned_keys(chain_name)
    result = dict(resolved_vars)
    for key in pinned:
        if key not in resolved_vars and key not in parent_vars:
            raise PinError(f"Pinned key '{key}' not found in chain '{chain_name}' or its parents")
    return result
