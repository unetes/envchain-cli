"""CLI commands for managing chain aliases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from envchain.aliaser import (
    AliasError,
    AliasIndex,
    add_alias,
    aliases_for_chain,
    list_aliases,
    remove_alias,
    resolve_alias,
)

_DEFAULT_PATH = Path(".envchain") / "aliases.json"


def _load_index(path: Path) -> AliasIndex:
    if path.exists():
        return AliasIndex.from_dict(json.loads(path.read_text()))
    return AliasIndex()


def _save_index(index: AliasIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index.to_dict(), indent=2))


def cmd_alias_add(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    try:
        add_alias(idx, args.alias, args.chain, overwrite=getattr(args, "overwrite", False))
    except AliasError as exc:
        print(f"error: {exc}")
        return 1
    _save_index(idx, path)
    print(f"Alias '{args.alias}' -> '{args.chain}' added.")
    return 0


def cmd_alias_remove(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    try:
        remove_alias(idx, args.alias)
    except AliasError as exc:
        print(f"error: {exc}")
        return 1
    _save_index(idx, path)
    print(f"Alias '{args.alias}' removed.")
    return 0


def cmd_alias_list(args: argparse.Namespace) -> int:
    path = Path(getattr(args, "index_path", _DEFAULT_PATH))
    idx = _load_index(path)
    chain_filter = getattr(args, "chain", None)
    pairs = (
        [(a, resolve_alias(idx, a)) for a in aliases_for_chain(idx, chain_filter)]
        if chain_filter
        else list_aliases(idx)
    )
    if not pairs:
        print("No aliases defined.")
        return 0
    for alias, target in pairs:
        print(f"{alias:20s} -> {target}")
    return 0


def build_alias_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("alias", help="Manage chain aliases")
    sp = p.add_subparsers(dest="alias_cmd")

    add_p = sp.add_parser("add", help="Add an alias")
    add_p.add_argument("alias", help="Short alias name")
    add_p.add_argument("chain", help="Target chain name")
    add_p.add_argument("--overwrite", action="store_true", help="Replace existing alias")
    add_p.set_defaults(func=cmd_alias_add)

    rm_p = sp.add_parser("remove", help="Remove an alias")
    rm_p.add_argument("alias", help="Alias to remove")
    rm_p.set_defaults(func=cmd_alias_remove)

    ls_p = sp.add_parser("list", help="List aliases")
    ls_p.add_argument("--chain", default=None, help="Filter by target chain")
    ls_p.set_defaults(func=cmd_alias_list)
