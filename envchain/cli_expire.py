"""CLI commands for managing variable expiry."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from envchain.expirer import (
    ExpiryIndex,
    ExpireError,
    set_expiry,
    remove_expiry,
    expired_entries,
    expiring_soon,
)

_DEFAULT_INDEX = Path(".envchain_expiry.json")


def _load_index(path: Path) -> ExpiryIndex:
    if path.exists():
        return ExpiryIndex.from_dict(json.loads(path.read_text()))
    return ExpiryIndex()


def _save_index(index: ExpiryIndex, path: Path) -> None:
    path.write_text(json.dumps(index.to_dict(), indent=2))


def cmd_expire_set(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_INDEX))
    index = _load_index(path)
    try:
        expires_at = datetime.fromisoformat(args.expires_at).replace(tzinfo=timezone.utc)
        entry = set_expiry(index, args.chain, args.key, expires_at, note=getattr(args, "note", ""))
        _save_index(index, path)
        print(f"Expiry set: {entry.chain}/{entry.key} expires {entry.expires_at.isoformat()}")
        return 0
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_expire_remove(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_INDEX))
    index = _load_index(path)
    try:
        remove_expiry(index, args.chain, args.key)
        _save_index(index, path)
        print(f"Removed expiry for {args.chain}/{args.key}")
        return 0
    except ExpireError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_expire_list(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_INDEX))
    index = _load_index(path)
    now = datetime.now(timezone.utc)
    soon_secs = getattr(args, "warn_within", 86400)
    entries = index.entries
    if not entries:
        print("No expiry entries.")
        return 0
    for e in sorted(entries, key=lambda x: x.expires_at):
        status = "EXPIRED" if e.is_expired(now) else ("SOON" if e.expires_at <= now.__class__(now.year, now.month, now.day, tzinfo=timezone.utc) else "ok")
        note = f"  # {e.note}" if e.note else ""
        print(f"[{status}] {e.chain}/{e.key}  {e.expires_at.isoformat()}{note}")
    return 0


def cmd_expire_check(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_INDEX))
    index = _load_index(path)
    now = datetime.now(timezone.utc)
    expired = expired_entries(index, now)
    soon = expiring_soon(index, within_seconds=getattr(args, "warn_within", 86400), now=now)
    if expired:
        print(f"{len(expired)} expired variable(s):")
        for e in expired:
            print(f"  {e.chain}/{e.key}")
    if soon:
        print(f"{len(soon)} variable(s) expiring soon:")
        for e in soon:
            print(f"  {e.chain}/{e.key} at {e.expires_at.isoformat()}")
    if not expired and not soon:
        print("All variables are within expiry.")
        return 0
    return 1


def build_expire_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("expire", help="Manage variable expiry")
    sp = p.add_subparsers(dest="expire_cmd")

    ps = sp.add_parser("set", help="Set expiry for a key")
    ps.add_argument("chain")
    ps.add_argument("key")
    ps.add_argument("expires_at", help="ISO-8601 datetime")
    ps.add_argument("--note", default="")
    ps.set_defaults(func=cmd_expire_set)

    pr = sp.add_parser("remove", help="Remove expiry for a key")
    pr.add_argument("chain")
    pr.add_argument("key")
    pr.set_defaults(func=cmd_expire_remove)

    pl = sp.add_parser("list", help="List all expiry entries")
    pl.set_defaults(func=cmd_expire_list)

    pc = sp.add_parser("check", help="Report expired or soon-expiring keys")
    pc.add_argument("--warn-within", type=int, default=86400, dest="warn_within")
    pc.set_defaults(func=cmd_expire_check)
