"""CLI helpers for snapshot-related sub-commands."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from envchain.snapshot import (
    create_snapshot,
    diff_snapshots,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


DEFAULT_SNAPSHOT_DIR = Path(".envchain") / "snapshots"


def cmd_snapshot_save(
    chain_name: str,
    variables: dict,
    label: Optional[str] = None,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> None:
    """Save a snapshot for *chain_name* and print the resulting file path."""
    snap = create_snapshot(chain_name, variables, label=label)
    dest = save_snapshot(snap, directory)
    print(f"Snapshot saved: {dest}")


def cmd_snapshot_list(
    chain_name: Optional[str] = None,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> None:
    """List available snapshots, optionally filtered by chain name."""
    paths = list_snapshots(directory, chain_name=chain_name)
    if not paths:
        print("No snapshots found.")
        return

    print(f"{'Chain':<20} {'Label':<20} {'Timestamp':<12} File")
    print("-" * 72)
    for p in paths:
        try:
            snap = load_snapshot(p)
            print(
                f"{snap['chain']:<20} "
                f"{snap.get('label', ''):<20} "
                f"{snap['timestamp']:<12} "
                f"{p.name}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  [error reading {p.name}: {exc}]")


def cmd_snapshot_diff(
    path_old: Path,
    path_new: Path,
) -> None:
    """Print a human-readable diff between two snapshot files."""
    try:
        old = load_snapshot(path_old)
        new = load_snapshot(path_new)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        sys.exit(1)

    diff = diff_snapshots(old, new)
    if not diff:
        print("No differences found.")
        return

    print(f"Diff: {path_old.name}  →  {path_new.name}")
    print("-" * 50)
    for key, change in diff.items():
        old_val = change["old"]
        new_val = change["new"]
        if old_val is None:
            print(f"  + {key}={new_val!r}")
        elif new_val is None:
            print(f"  - {key}={old_val!r}")
        else:
            print(f"  ~ {key}: {old_val!r} → {new_val!r}")
