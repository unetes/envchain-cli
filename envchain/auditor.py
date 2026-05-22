"""Audit log for tracking changes to chains and variables."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    action: str          # e.g. "set", "delete", "rename", "copy", "merge"
    chain: str
    key: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: float = field(default_factory=time.time)
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "AuditEntry":
        return AuditEntry(**d)

    def __str__(self) -> str:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.timestamp))
        key_part = f" [{self.key}]" if self.key else ""
        return f"{ts}  {self.action:<10} {self.chain}{key_part}"


def record(log_path: Path, entry: AuditEntry) -> None:
    """Append a single audit entry to the JSONL log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")


def load_log(log_path: Path) -> List[AuditEntry]:
    """Load all audit entries from the JSONL log file."""
    if not log_path.exists():
        return []
    entries: List[AuditEntry] = []
    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    return entries


def filter_log(
    entries: List[AuditEntry],
    chain: Optional[str] = None,
    action: Optional[str] = None,
    since: Optional[float] = None,
) -> List[AuditEntry]:
    """Filter audit entries by chain name, action type, or timestamp."""
    result = entries
    if chain:
        result = [e for e in result if e.chain == chain]
    if action:
        result = [e for e in result if e.action == action]
    if since is not None:
        result = [e for e in result if e.timestamp >= since]
    return result
