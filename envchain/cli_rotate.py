"""CLI commands for key rotation."""
from __future__ import annotations

import argparse
import json
from typing import Optional

from envchain.rotator import RotateError, rotate_keys


def cmd_rotate(
    args: argparse.Namespace,
    registry,
    out=None,
    err=None,
) -> int:
    """Rotate one or more keys in a chain, replacing values with generated ones."""
    import sys

    out = out or sys.stdout
    err = err or sys.stderr

    if not args.keys:
        err.write("error: at least one KEY must be specified\n")
        return 2

    try:
        report = rotate_keys(
            registry,
            chain_name=args.chain,
            keys=args.keys,
            dry_run=getattr(args, "dry_run", False),
        )
    except RotateError as exc:
        err.write(f"error: {exc}\n")
        return 1

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        payload = [e.to_dict() for e in report.entries]
        out.write(json.dumps(payload, indent=2) + "\n")
    else:
        if getattr(args, "dry_run", False):
            out.write("[dry-run] ")
        out.write(report.summary() + "\n")

    return 0


def build_rotate_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser(
        "rotate",
        help="Rotate key values in a chain with freshly generated secrets.",
    )
    p.add_argument("chain", help="Name of the chain to rotate keys in.")
    p.add_argument("keys", nargs="+", metavar="KEY", help="Key(s) to rotate.")
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be rotated without making changes.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_rotate)
    return p
