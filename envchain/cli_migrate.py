"""CLI commands for migrating keys between chains."""

from __future__ import annotations

import argparse
import json
from typing import List, Optional

from envchain.migrator import MigrateError, migrate_keys


def _parse_remap(remap_args: Optional[List[str]]) -> dict:
    """Parse 'OLD:NEW' remap strings into a dict."""
    result = {}
    for item in remap_args or []:
        if ":" not in item:
            raise ValueError(f"Invalid remap spec '{item}'. Expected OLD:NEW format.")
        old, new = item.split(":", 1)
        result[old.strip()] = new.strip()
    return result


def cmd_migrate(args, registry) -> int:
    try:
        remap = _parse_remap(getattr(args, "remap", None))
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    keys = getattr(args, "keys", None) or None

    try:
        report = migrate_keys(
            registry,
            source_name=args.source,
            dest_name=args.dest,
            keys=keys,
            remap=remap,
            overwrite=getattr(args, "overwrite", False),
            remove_source=getattr(args, "move", False),
        )
    except MigrateError as exc:
        print(f"Error: {exc}")
        return 1

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(
            json.dumps(
                {
                    "source": report.source,
                    "destination": report.destination,
                    "moved": report.moved,
                    "skipped": report.skipped,
                    "remapped": report.remapped,
                },
                indent=2,
            )
        )
    else:
        print(report.summary())
        if report.skipped:
            print(f"  Skipped (already exist): {', '.join(report.skipped)}")

    return 0


def build_migrate_parser(subparsers) -> argparse.ArgumentParser:
    p = subparsers.add_parser("migrate", help="Migrate keys between chains")
    p.add_argument("source", help="Source chain name")
    p.add_argument("dest", help="Destination chain name")
    p.add_argument("keys", nargs="*", help="Keys to migrate (default: all)")
    p.add_argument("--remap", nargs="+", metavar="OLD:NEW", help="Rename keys during migration")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing keys in dest")
    p.add_argument("--move", action="store_true", help="Remove keys from source after migration")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_migrate)
    return p
