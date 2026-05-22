"""CLI commands for copying chains."""

from __future__ import annotations

import argparse
import json
import sys

from envchain.copier import CopyError, copy_chain
from envchain.registry import ChainRegistry


def cmd_copy_chain(args: argparse.Namespace, registry: ChainRegistry) -> int:
    """Handle the ``copy`` sub-command.

    Expected args attributes:
        src (str): source chain name
        dst (str): destination chain name
        include (list[str] | None): keys to include
        exclude (list[str] | None): keys to exclude
        no_parent (bool): drop parent inheritance
        overwrite (bool): allow overwriting existing dst chain
        format (str): output format — 'text' or 'json'
    """
    include = args.include or None
    exclude = args.exclude or None

    try:
        new_chain = copy_chain(
            registry,
            args.src,
            args.dst,
            include_keys=include,
            exclude_keys=exclude,
            inherit_parent=not args.no_parent,
            overwrite=args.overwrite,
        )
    except CopyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "format", "text") == "json":
        print(json.dumps(new_chain, indent=2))
    else:
        var_count = len(new_chain.get("vars", {}))
        parent_info = f" (parent: {new_chain['parent']})" if new_chain.get("parent") else ""
        print(f"Copied '{args.src}' → '{args.dst}'{parent_info} [{var_count} var(s)]")

    return 0


def build_copy_parser(subparsers) -> None:  # pragma: no cover
    """Register the 'copy' sub-command on *subparsers*."""
    p = subparsers.add_parser("copy", help="Copy a chain to a new name")
    p.add_argument("src", help="Source chain name")
    p.add_argument("dst", help="Destination chain name")
    p.add_argument(
        "--include", nargs="+", metavar="KEY", help="Only copy these keys"
    )
    p.add_argument(
        "--exclude", nargs="+", metavar="KEY", help="Exclude these keys from the copy"
    )
    p.add_argument(
        "--no-parent", action="store_true", help="Do not inherit parent from source"
    )
    p.add_argument(
        "--overwrite", action="store_true", help="Overwrite destination if it exists"
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    p.set_defaults(func=cmd_copy_chain)
