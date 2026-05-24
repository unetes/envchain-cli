"""Migrate variables between chains with optional key remapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class MigrateError(Exception):
    """Raised when a migration cannot be completed."""


@dataclass
class MigrateReport:
    source: str
    destination: str
    moved: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    remapped: Dict[str, str] = field(default_factory=dict)

    @property
    def total_moved(self) -> int:
        return len(self.moved)

    def summary(self) -> str:
        parts = [f"Migrated {self.total_moved} key(s) from '{self.source}' to '{self.destination}'."]
        if self.skipped:
            parts.append(f"Skipped {len(self.skipped)} key(s): {', '.join(self.skipped)}.")
        if self.remapped:
            remap_str = ", ".join(f"{k}->{v}" for k, v in self.remapped.items())
            parts.append(f"Remapped: {remap_str}.")
        return " ".join(parts)


def migrate_keys(
    registry,
    source_name: str,
    dest_name: str,
    keys: Optional[List[str]] = None,
    remap: Optional[Dict[str, str]] = None,
    overwrite: bool = False,
    remove_source: bool = False,
) -> MigrateReport:
    """Copy (or move) keys from source chain to destination chain."""
    source = registry.get(source_name)
    if source is None:
        raise MigrateError(f"Source chain '{source_name}' not found.")
    dest = registry.get(dest_name)
    if dest is None:
        raise MigrateError(f"Destination chain '{dest_name}' not found.")

    remap = remap or {}
    source_vars: Dict[str, str] = dict(source.vars)
    dest_vars: Dict[str, str] = dict(dest.vars)

    candidate_keys = keys if keys is not None else list(source_vars.keys())

    report = MigrateReport(source=source_name, destination=dest_name)

    for key in candidate_keys:
        if key not in source_vars:
            raise MigrateError(f"Key '{key}' not found in source chain '{source_name}'.")
        dest_key = remap.get(key, key)
        if dest_key != key:
            report.remapped[key] = dest_key
        if dest_key in dest_vars and not overwrite:
            report.skipped.append(key)
            continue
        dest_vars[dest_key] = source_vars[key]
        report.moved.append(key)
        if remove_source:
            del source_vars[key]

    dest.vars = dest_vars
    if remove_source:
        source.vars = source_vars

    return report
