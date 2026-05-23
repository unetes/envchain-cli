"""Freeze a chain so its variables cannot be modified until unfrozen."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class FreezeError(Exception):
    """Raised when a freeze/unfreeze operation fails."""


class FreezeIndex:
    """Tracks which chains are currently frozen."""

    def __init__(self, frozen: Dict[str, str] | None = None) -> None:
        # mapping of chain_name -> reason
        self._frozen: Dict[str, str] = frozen or {}

    def to_dict(self) -> Dict[str, str]:
        return dict(self._frozen)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "FreezeIndex":
        return cls(frozen=data)


def freeze(index: FreezeIndex, chain_name: str, reason: str = "") -> None:
    """Mark *chain_name* as frozen, optionally recording a *reason*."""
    if chain_name in index._frozen:
        raise FreezeError(f"Chain '{chain_name}' is already frozen.")
    index._frozen[chain_name] = reason


def unfreeze(index: FreezeIndex, chain_name: str) -> None:
    """Remove the freeze on *chain_name*."""
    if chain_name not in index._frozen:
        raise FreezeError(f"Chain '{chain_name}' is not frozen.")
    del index._frozen[chain_name]


def is_frozen(index: FreezeIndex, chain_name: str) -> bool:
    """Return True if *chain_name* is currently frozen."""
    return chain_name in index._frozen


def frozen_chains(index: FreezeIndex) -> List[str]:
    """Return a sorted list of all frozen chain names."""
    return sorted(index._frozen.keys())


def freeze_reason(index: FreezeIndex, chain_name: str) -> str:
    """Return the freeze reason for *chain_name*, or empty string if not frozen."""
    return index._frozen.get(chain_name, "")


def save_freeze_index(index: FreezeIndex, path: Path) -> None:
    path.write_text(json.dumps(index.to_dict(), indent=2))


def load_freeze_index(path: Path) -> FreezeIndex:
    if not path.exists():
        return FreezeIndex()
    return FreezeIndex.from_dict(json.loads(path.read_text()))
