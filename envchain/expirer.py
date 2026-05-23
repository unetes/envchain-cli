"""Expiry tracking for chain variables."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class ExpireError(Exception):
    """Raised when an expiry operation fails."""


@dataclass
class ExpiryEntry:
    chain: str
    key: str
    expires_at: datetime
    note: str = ""

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now >= self.expires_at

    def to_dict(self) -> dict:
        return {
            "chain": self.chain,
            "key": self.key,
            "expires_at": self.expires_at.isoformat(),
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryEntry":
        return cls(
            chain=data["chain"],
            key=data["key"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            note=data.get("note", ""),
        )


@dataclass
class ExpiryIndex:
    entries: List[ExpiryEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}

    @classmethod
    def from_dict(cls, data: dict) -> "ExpiryIndex":
        return cls(entries=[ExpiryEntry.from_dict(e) for e in data.get("entries", [])])


def set_expiry(index: ExpiryIndex, chain: str, key: str, expires_at: datetime, note: str = "") -> ExpiryEntry:
    """Add or replace an expiry entry for a chain/key pair."""
    index.entries = [e for e in index.entries if not (e.chain == chain and e.key == key)]
    entry = ExpiryEntry(chain=chain, key=key, expires_at=expires_at, note=note)
    index.entries.append(entry)
    return entry


def remove_expiry(index: ExpiryIndex, chain: str, key: str) -> None:
    """Remove an expiry entry. Raises ExpireError if not found."""
    before = len(index.entries)
    index.entries = [e for e in index.entries if not (e.chain == chain and e.key == key)]
    if len(index.entries) == before:
        raise ExpireError(f"No expiry set for '{key}' in chain '{chain}'")


def expired_entries(index: ExpiryIndex, now: Optional[datetime] = None) -> List[ExpiryEntry]:
    """Return all entries that have expired."""
    return [e for e in index.entries if e.is_expired(now)]


def expiring_soon(index: ExpiryIndex, within_seconds: int, now: Optional[datetime] = None) -> List[ExpiryEntry]:
    """Return entries expiring within the given number of seconds."""
    from datetime import timedelta
    now = now or datetime.now(timezone.utc)
    cutoff = now + timedelta(seconds=within_seconds)
    return [e for e in index.entries if not e.is_expired(now) and e.expires_at <= cutoff]
