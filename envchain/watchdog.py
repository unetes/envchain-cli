"""Watch chains for value changes and report drift."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class WatchEntry:
    chain_name: str
    key: str
    expected_value: str
    recorded_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "chain_name": self.chain_name,
            "key": self.key,
            "expected_value": self.expected_value,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatchEntry":
        return cls(
            chain_name=data["chain_name"],
            key=data["key"],
            expected_value=data["expected_value"],
            recorded_at=data.get("recorded_at", 0.0),
        )


@dataclass
class DriftResult:
    chain_name: str
    key: str
    expected: str
    actual: Optional[str]  # None means key is missing

    @property
    def is_missing(self) -> bool:
        return self.actual is None

    def __str__(self) -> str:
        if self.is_missing:
            return f"[{self.chain_name}] {self.key}: MISSING (expected {self.expected!r})"
        return f"[{self.chain_name}] {self.key}: changed from {self.expected!r} to {self.actual!r}"


class WatchIndex:
    def __init__(self) -> None:
        self._entries: Dict[str, Dict[str, WatchEntry]] = {}

    def add(self, entry: WatchEntry) -> None:
        self._entries.setdefault(entry.chain_name, {})[entry.key] = entry

    def remove(self, chain_name: str, key: str) -> None:
        chain = self._entries.get(chain_name, {})
        if key not in chain:
            raise KeyError(f"No watch for {chain_name!r}/{key!r}")
        del chain[key]
        if not chain:
            del self._entries[chain_name]

    def entries_for(self, chain_name: str) -> List[WatchEntry]:
        return sorted(self._entries.get(chain_name, {}).values(), key=lambda e: e.key)

    def all_entries(self) -> List[WatchEntry]:
        result = []
        for chain in sorted(self._entries):
            result.extend(self.entries_for(chain))
        return result

    def to_dict(self) -> dict:
        return {
            chain: {key: e.to_dict() for key, e in keys.items()}
            for chain, keys in self._entries.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WatchIndex":
        idx = cls()
        for chain, keys in data.items():
            for key, raw in keys.items():
                idx.add(WatchEntry.from_dict(raw))
        return idx


def check_drift(index: WatchIndex, registry) -> List[DriftResult]:
    """Compare watched values against current chain state."""
    results: List[DriftResult] = []
    for entry in index.all_entries():
        chain = registry.get(entry.chain_name)
        if chain is None:
            results.append(DriftResult(entry.chain_name, entry.key, entry.expected_value, None))
            continue
        from envchain.chain import resolve
        resolved = resolve(chain, registry)
        actual = resolved.get(entry.key)
        if actual != entry.expected_value:
            results.append(DriftResult(entry.chain_name, entry.key, entry.expected_value, actual))
    return results
