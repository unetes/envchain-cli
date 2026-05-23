"""CLI commands for chain freeze/unfreeze management."""

from __future__ import annotations

import argparse
from pathlib import Path

from envchain.freezer import (
    FreezeError,
    freeze,
    unfreeze,
    is_frozen,
    frozen_chains,
    freeze_reason,
    save_freeze_index,
    load_freeze_index,
)

_DEFAULT_INDEX = Path(".envchain") / "freeze_index.json"


def _get_index_path(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "index_path", None) or _DEFAULT_INDEX)


def cmd_freeze_add(args: argparse.Namespace) -> int:
    path = _get_index_path(args)
    idx = load_freeze_index(path)
    try:
        freeze(idx, args.chain, reason=args.reason or "")
    except FreezeError as exc:
        print(f"Error: {exc}")
        return 1
    save_freeze_index(idx, path)
    print(f"Chain '{args.chain}' frozen.")
    return 0


def cmd_freeze_remove(args: argparse.Namespace) -> int:
    path = _get_index_path(args)
    idx = load_freeze_index(path)
    try:
        unfreeze(idx, args.chain)
    except FreezeError as exc:
        print(f"Error: {exc}")
        return 1
    save_freeze_index(idx, path)
    print(f"Chain '{args.chain}' unfrozen.")
    return 0


def cmd_freeze_list(args: argparse.Namespace) -> int:
    path = _get_index_path(args)
    idx = load_freeze_index(path)
    chains = frozen_chains(idx)
    if not chains:
        print("No chains are currently frozen.")
        return 0
    for name in chains:
        reason = freeze_reason(idx, name)
        suffix = f"  # {reason}" if reason else ""
        print(f"{name}{suffix}")
    return 0


def build_freeze_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("freeze", help="Manage chain freezes")
    sub = p.add_subparsers(dest="freeze_cmd", required=True)

    add_p = sub.add_parser("add", help="Freeze a chain")
    add_p.add_argument("chain")
    add_p.add_argument("--reason", default="", help="Optional reason for freezing")
    add_p.set_defaults(func=cmd_freeze_add)

    rm_p = sub.add_parser("remove", help="Unfreeze a chain")
    rm_p.add_argument("chain")
    rm_p.set_defaults(func=cmd_freeze_remove)

    ls_p = sub.add_parser("list", help="List frozen chains")
    ls_p.set_defaults(func=cmd_freeze_list)
