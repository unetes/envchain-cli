"""CLI commands for the watchdog feature."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envchain.watchdog import WatchEntry, WatchIndex, check_drift


def _load_index(path: Path) -> WatchIndex:
    if path.exists():
        return WatchIndex.from_dict(json.loads(path.read_text()))
    return WatchIndex()


def _save_index(index: WatchIndex, path: Path) -> None:
    path.write_text(json.dumps(index.to_dict(), indent=2))


def cmd_watch_add(args: argparse.Namespace, registry) -> int:
    """Pin the current value of a key in a chain for drift detection."""
    from envchain.chain import resolve
    chain = registry.get(args.chain)
    if chain is None:
        print(f"error: chain {args.chain!r} not found", file=sys.stderr)
        return 1
    resolved = resolve(chain, registry)
    if args.key not in resolved:
        print(f"error: key {args.key!r} not found in chain {args.chain!r}", file=sys.stderr)
        return 1
    idx = _load_index(Path(args.index))
    entry = WatchEntry(chain_name=args.chain, key=args.key, expected_value=resolved[args.key])
    idx.add(entry)
    _save_index(idx, Path(args.index))
    print(f"Watching {args.chain}/{args.key} = {resolved[args.key]!r}")
    return 0


def cmd_watch_remove(args: argparse.Namespace) -> int:
    idx = _load_index(Path(args.index))
    try:
        idx.remove(args.chain, args.key)
    except KeyError:
        print(f"error: no watch for {args.chain!r}/{args.key!r}", file=sys.stderr)
        return 1
    _save_index(idx, Path(args.index))
    print(f"Removed watch for {args.chain}/{args.key}")
    return 0


def cmd_watch_list(args: argparse.Namespace) -> int:
    idx = _load_index(Path(args.index))
    entries = idx.all_entries()
    if not entries:
        print("No watches registered.")
        return 0
    for e in entries:
        print(f"{e.chain_name}/{e.key} = {e.expected_value!r}")
    return 0


def cmd_watch_check(args: argparse.Namespace, registry) -> int:
    idx = _load_index(Path(args.index))
    drifts = check_drift(idx, registry)
    if not drifts:
        print("No drift detected.")
        return 0
    for d in drifts:
        print(str(d))
    return 1


def build_watch_parser(subparsers, default_index: str = ".envchain_watches.json"):
    p = subparsers.add_parser("watch", help="Monitor chains for value drift")
    p.add_argument("--index", default=default_index, help="Path to watch index file")
    sub = p.add_subparsers(dest="watch_cmd")

    add_p = sub.add_parser("add", help="Start watching a key")
    add_p.add_argument("chain")
    add_p.add_argument("key")

    rm_p = sub.add_parser("remove", help="Stop watching a key")
    rm_p.add_argument("chain")
    rm_p.add_argument("key")

    sub.add_parser("list", help="List all watches")
    sub.add_parser("check", help="Check for drift against current values")
    return p
