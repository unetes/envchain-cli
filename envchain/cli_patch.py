"""CLI commands for patching chain variables."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envchain.patcher import PatchError, patch_vars


def _parse_key_value(token: str):
    """Parse 'KEY=VALUE' into a (key, value) tuple."""
    if "=" not in token:
        raise argparse.ArgumentTypeError(
            f"Expected KEY=VALUE, got: {token!r}"
        )
    key, _, value = token.partition("=")
    return key.strip(), value


def cmd_patch(args, registry) -> int:
    """Apply a partial update to a chain's variables.

    Returns 0 on success, 1 on error.
    """
    try:
        chain = registry.get(args.chain)
    except KeyError:
        print(f"error: chain '{args.chain}' not found", file=sys.stderr)
        return 1

    updates = {}
    for token in args.set or []:
        try:
            k, v = _parse_key_value(token)
        except argparse.ArgumentTypeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        updates[k] = v

    deletions: List[str] = args.delete or []

    try:
        report = patch_vars(
            chain,
            updates=updates,
            deletions=deletions,
            allow_new=not args.no_new,
        )
    except PatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(
            json.dumps(
                {
                    "chain": report.chain_name,
                    "added": report.added,
                    "updated": report.updated,
                    "deleted": report.deleted,
                    "total_changes": report.total_changes,
                }
            )
        )
    else:
        print(report.summary())

    return 0


def build_patch_parser(subparsers) -> None:
    p = subparsers.add_parser(
        "patch",
        help="Partially update variables in a chain",
    )
    p.add_argument("chain", help="Target chain name")
    p.add_argument(
        "--set",
        metavar="KEY=VALUE",
        nargs="+",
        help="Variables to add or update",
    )
    p.add_argument(
        "--delete",
        metavar="KEY",
        nargs="+",
        help="Variables to remove",
    )
    p.add_argument(
        "--no-new",
        action="store_true",
        default=False,
        help="Fail if --set references a key not already in the chain",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_patch)
