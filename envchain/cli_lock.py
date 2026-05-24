"""CLI commands for chain locking."""
from __future__ import annotations

import argparse
from pathlib import Path

from envchain.locker import (
    LockError,
    list_locks,
    load_lock_index,
    lock_chain,
    lock_reason,
    save_lock_index,
    unlock_chain,
)

_DEFAULT_INDEX = Path(".envchain") / "locks.json"


def _get_index_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "index", None) or _DEFAULT_INDEX)


def cmd_lock_add(args: argparse.Namespace) -> int:
    path = _get_index_path(args)
    idx = load_lock_index(path)
    try:
        lock_chain(idx, args.chain, reason=args.reason or "")
    except LockError as exc:
        print(f"error: {exc}")
        return 1
    save_lock_index(idx, path)
    print(f"Locked chain '{args.chain}'.")
    return 0


def cmd_lock_remove(args: argparse.Namespace) -> int:
    path = _get_index_path(args)
    idx = load_lock_index(path)
    try:
        unlock_chain(idx, args.chain)
    except LockError as exc:
        print(f"error: {exc}")
        return 1
    save_lock_index(idx, path)
    print(f"Unlocked chain '{args.chain}'.")
    return 0


def cmd_lock_list(args: argparse.Namespace) -> int:
    path = _get_index_path(args)
    idx = load_lock_index(path)
    locked = list_locks(idx)
    if not locked:
        print("No locked chains.")
        return 0
    for name in locked:
        reason = lock_reason(idx, name)
        suffix = f"  # {reason}" if reason else ""
        print(f"{name}{suffix}")
    return 0


def build_lock_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("lock", help="Manage chain read-only locks")
    sp = p.add_subparsers(dest="lock_cmd", required=True)

    add_p = sp.add_parser("add", help="Lock a chain")
    add_p.add_argument("chain")
    add_p.add_argument("--reason", default="", help="Optional reason for locking")
    add_p.add_argument("--index", default=None)
    add_p.set_defaults(func=cmd_lock_add)

    rm_p = sp.add_parser("remove", help="Unlock a chain")
    rm_p.add_argument("chain")
    rm_p.add_argument("--index", default=None)
    rm_p.set_defaults(func=cmd_lock_remove)

    ls_p = sp.add_parser("list", help="List locked chains")
    ls_p.add_argument("--index", default=None)
    ls_p.set_defaults(func=cmd_lock_list)
