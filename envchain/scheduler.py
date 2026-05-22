"""Schedule-based auto-export of environment chains to files."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ScheduleError(Exception):
    """Raised when a schedule operation fails."""


@dataclass
class ScheduleEntry:
    chain_name: str
    output_path: str
    format: str = "dotenv"  # dotenv | shell | json
    interval_seconds: int = 3600
    last_run: float = 0.0
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "chain_name": self.chain_name,
            "output_path": self.output_path,
            "format": self.format,
            "interval_seconds": self.interval_seconds,
            "last_run": self.last_run,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleEntry":
        return cls(
            chain_name=data["chain_name"],
            output_path=data["output_path"],
            format=data.get("format", "dotenv"),
            interval_seconds=int(data.get("interval_seconds", 3600)),
            last_run=float(data.get("last_run", 0.0)),
            enabled=bool(data.get("enabled", True)),
        )

    def is_due(self, now: Optional[float] = None) -> bool:
        if not self.enabled:
            return False
        now = now if now is not None else time.time()
        return (now - self.last_run) >= self.interval_seconds


class ScheduleIndex:
    def __init__(self) -> None:
        self._entries: Dict[str, ScheduleEntry] = {}

    def add(self, entry: ScheduleEntry) -> None:
        key = f"{entry.chain_name}::{entry.output_path}"
        self._entries[key] = entry

    def remove(self, chain_name: str, output_path: str) -> None:
        key = f"{chain_name}::{output_path}"
        if key not in self._entries:
            raise ScheduleError(f"No schedule found for '{chain_name}' -> '{output_path}'")
        del self._entries[key]

    def list_all(self) -> List[ScheduleEntry]:
        return sorted(self._entries.values(), key=lambda e: e.chain_name)

    def due_entries(self, now: Optional[float] = None) -> List[ScheduleEntry]:
        return [e for e in self._entries.values() if e.is_due(now)]

    def to_dict(self) -> dict:
        return {k: v.to_dict() for k, v in self._entries.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleIndex":
        idx = cls()
        for v in data.values():
            idx.add(ScheduleEntry.from_dict(v))
        return idx
