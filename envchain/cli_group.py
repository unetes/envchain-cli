"""CLI commands for chain group management."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from envchain.grouper import (
    GroupError,
    GroupIndex,
    add_chain_to_group,
    create_group,
    delete_group,
    list_groups,
    remove_chain_from_group,
)

_DEFAULT_PATH = Path(".envchain_groups.json")


def _load_index(path: Path) -> GroupIndex:
    if path.exists():
        return GroupIndex.from_dict(json.loads(path.read_text()))
    return GroupIndex()


def _save_index(index: GroupIndex, path: Path) -> None:
    path.write_text(json.dumps(index.to_dict(), indent=2))


def cmd_group_create(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    try:
        create_group(idx, args.name, description=getattr(args, "description", ""))
    except GroupError as exc:
        print(f"Error: {exc}")
        return 1
    _save_index(idx, path)
    print(f"Group '{args.name}' created.")
    return 0


def cmd_group_delete(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    try:
        delete_group(idx, args.name)
    except GroupError as exc:
        print(f"Error: {exc}")
        return 1
    _save_index(idx, path)
    print(f"Group '{args.name}' deleted.")
    return 0


def cmd_group_add(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    try:
        add_chain_to_group(idx, args.group, args.chain)
    except GroupError as exc:
        print(f"Error: {exc}")
        return 1
    _save_index(idx, path)
    print(f"Chain '{args.chain}' added to group '{args.group}'.")
    return 0


def cmd_group_remove(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    try:
        remove_chain_from_group(idx, args.group, args.chain)
    except GroupError as exc:
        print(f"Error: {exc}")
        return 1
    _save_index(idx, path)
    print(f"Chain '{args.chain}' removed from group '{args.group}'.")
    return 0


def cmd_group_list(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    groups = list_groups(idx)
    if not groups:
        print("No groups defined.")
        return 0
    for g in groups:
        print(str(g))
    return 0


def build_group_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("group", help="Manage chain groups")
    sp = p.add_subparsers(dest="group_cmd")

    pc = sp.add_parser("create", help="Create a new group")
    pc.add_argument("name")
    pc.add_argument("--description", default="")
    pc.set_defaults(func=cmd_group_create)

    pd = sp.add_parser("delete", help="Delete a group")
    pd.add_argument("name")
    pd.set_defaults(func=cmd_group_delete)

    pa = sp.add_parser("add", help="Add a chain to a group")
    pa.add_argument("group")
    pa.add_argument("chain")
    pa.set_defaults(func=cmd_group_add)

    pr = sp.add_parser("remove", help="Remove a chain from a group")
    pr.add_argument("group")
    pr.add_argument("chain")
    pr.set_defaults(func=cmd_group_remove)

    pl = sp.add_parser("list", help="List all groups")
    pl.set_defaults(func=cmd_group_list)
