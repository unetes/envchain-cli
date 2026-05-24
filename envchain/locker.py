"""Read-only lock for chains — prevents accidental writes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class LockError(Exception):
    """Raised when a lock operation fails."""


class LockIndex:
    """Persisted index of locked chains."""

    def __init__(self) -> None:
        self._locks: Dict[str, str] = {}  # chain_name -> reason

    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        return {"locks": dict(self._locks)}

    @classmethod
    def from_dict(cls, data: dict) -> "LockIndex":
        idx = cls()
        idx._locks = dict(data.get("locks", {}))
        return idx


def lock_chain(idx: LockIndex, chain_name: str, reason: str = "") -> None:
    """Mark *chain_name* as locked.  Raises LockError if already locked."""
    if chain_name in idx._locks:
        raise LockError(f"Chain '{chain_name}' is already locked.")
    idx._locks[chain_name] = reason


def unlock_chain(idx: LockIndex, chain_name: str) -> None:
    """Remove the lock on *chain_name*.  Raises LockError if not locked."""
    if chain_name not in idx._locks:
        raise LockError(f"Chain '{chain_name}' is not locked.")
    del idx._locks[chain_name]


def is_locked(idx: LockIndex, chain_name: str) -> bool:
    """Return True if *chain_name* is locked."""
    return chain_name in idx._locks


def lock_reason(idx: LockIndex, chain_name: str) -> str:
    """Return the reason stored for *chain_name*, or empty string."""
    return idx._locks.get(chain_name, "")


def list_locks(idx: LockIndex) -> List[str]:
    """Return sorted list of locked chain names."""
    return sorted(idx._locks.keys())


def load_lock_index(path: Path) -> LockIndex:
    if path.exists():
        return LockIndex.from_dict(json.loads(path.read_text()))
    return LockIndex()


def save_lock_index(idx: LockIndex, path: Path) -> None:
    path.write_text(json.dumps(idx.to_dict(), indent=2))
