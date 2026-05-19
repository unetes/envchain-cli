"""Snapshot support for envchain: save and restore chain variable states."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional


SNAPSHOT_VERSION = 1


def create_snapshot(chain_name: str, variables: Dict[str, str], label: Optional[str] = None) -> dict:
    """Create a snapshot dict for the given chain and its resolved variables."""
    return {
        "version": SNAPSHOT_VERSION,
        "chain": chain_name,
        "label": label or "",
        "timestamp": int(time.time()),
        "variables": dict(variables),
    }


def save_snapshot(snapshot: dict, directory: Path) -> Path:
    """Persist a snapshot to disk under *directory*.

    Returns the path of the written file.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    chain_name = snapshot["chain"]
    timestamp = snapshot["timestamp"]
    filename = f"{chain_name}_{timestamp}.json"
    dest = directory / filename

    dest.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return dest


def load_snapshot(path: Path) -> dict:
    """Load and return a snapshot from *path*."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != SNAPSHOT_VERSION:
        raise ValueError(
            f"Unsupported snapshot version: {data.get('version')!r}"
        )
    return data


def list_snapshots(directory: Path, chain_name: Optional[str] = None) -> List[Path]:
    """Return snapshot paths inside *directory*, optionally filtered by chain name."""
    directory = Path(directory)
    if not directory.exists():
        return []

    paths = sorted(directory.glob("*.json"))
    if chain_name:
        paths = [p for p in paths if p.name.startswith(f"{chain_name}_")]
    return paths


def diff_snapshots(old: dict, new: dict) -> Dict[str, dict]:
    """Return a diff between two snapshots.

    Returns a mapping of variable names to ``{"old": ..., "new": ...}`` entries
    for variables that were added, removed, or changed.
    """
    old_vars: Dict[str, str] = old.get("variables", {})
    new_vars: Dict[str, str] = new.get("variables", {})

    all_keys = set(old_vars) | set(new_vars)
    result: Dict[str, dict] = {}
    for key in sorted(all_keys):
        o = old_vars.get(key)
        n = new_vars.get(key)
        if o != n:
            result[key] = {"old": o, "new": n}
    return result
