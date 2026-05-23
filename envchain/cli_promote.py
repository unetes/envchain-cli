"""CLI commands for promoting environment variables between chains."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from envchain.promoter import PromoteError, promote_keys


def cmd_promote(
    args: argparse.Namespace,
    registry,
    *,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Promote one or more keys from a source chain to a target chain.

    Returns 0 on success, 1 on error.
    """
    keys: Sequence[str] = args.keys
    if not keys:
        err.write("Error: at least one KEY must be specified.\n")
        return 2

    try:
        promoted = promote_keys(
            registry,
            source_chain=args.source,
            target_chain=args.target,
            keys=keys,
            overwrite=getattr(args, "overwrite", False),
            remove_from_source=getattr(args, "move", False),
        )
    except PromoteError as exc:
        err.write(f"Error: {exc}\n")
        return 1

    action = "Moved" if getattr(args, "move", False) else "Promoted"
    for key, value in promoted.items():
        out.write(
            f"{action} {key}={value!r} from '{args.source}' to '{args.target}'\n"
        )

    out.write(
        f"\n{len(promoted)} key(s) {action.lower()} successfully.\n"
    )
    return 0


def build_promote_parser(subparsers) -> argparse.ArgumentParser:
    """Register the 'promote' sub-command."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "promote",
        help="Promote variables from a child chain to a parent (or any target) chain.",
    )
    parser.add_argument("source", help="Chain to promote variables FROM.")
    parser.add_argument("target", help="Chain to promote variables INTO.")
    parser.add_argument(
        "keys",
        nargs="+",
        metavar="KEY",
        help="One or more variable keys to promote.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the key in the target chain if it already exists.",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        default=False,
        help="Remove the key from the source chain after promoting (move semantics).",
    )
    parser.set_defaults(func=cmd_promote)
    return parser
