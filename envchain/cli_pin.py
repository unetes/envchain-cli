"""CLI commands for managing pinned keys in chains."""
from __future__ import annotations
import argparse
from envchain.pinner import PinIndex, PinError


def cmd_pin_add(args: argparse.Namespace, pin_index: PinIndex) -> int:
    """Pin a key in a chain."""
    try:
        pin_index.pin(args.chain, args.key)
        print(f"Pinned '{args.key}' in chain '{args.chain}'")
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}")
        return 1


def cmd_pin_remove(args: argparse.Namespace, pin_index: PinIndex) -> int:
    """Unpin a key in a chain."""
    try:
        pin_index.unpin(args.chain, args.key)
        print(f"Unpinned '{args.key}' from chain '{args.chain}'")
        return 0
    except PinError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_pin_list(args: argparse.Namespace, pin_index: PinIndex) -> int:
    """List all pinned keys, optionally filtered by chain."""
    if args.chain:
        keys = pin_index.pinned_keys(args.chain)
        if not keys:
            print(f"No pinned keys in chain '{args.chain}'")
            return 0
        print(f"Pinned keys in '{args.chain}':")
        for key in keys:
            print(f"  {key}")
    else:
        all_pins = pin_index.all_pins()
        if not all_pins:
            print("No pinned keys found.")
            return 0
        for chain, keys in sorted(all_pins.items()):
            print(f"{chain}:")
            for key in keys:
                print(f"  {key}")
    return 0


def build_pin_parser(subparsers) -> None:
    """Register pin subcommands onto an argparse subparsers object."""
    pin_parser = subparsers.add_parser("pin", help="Manage pinned keys")
    pin_sub = pin_parser.add_subparsers(dest="pin_cmd")

    p_add = pin_sub.add_parser("add", help="Pin a key in a chain")
    p_add.add_argument("chain", help="Chain name")
    p_add.add_argument("key", help="Variable key to pin")

    p_rm = pin_sub.add_parser("remove", help="Unpin a key from a chain")
    p_rm.add_argument("chain", help="Chain name")
    p_rm.add_argument("key", help="Variable key to unpin")

    p_ls = pin_sub.add_parser("list", help="List pinned keys")
    p_ls.add_argument("--chain", default=None, help="Filter by chain name")
