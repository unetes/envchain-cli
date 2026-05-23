"""CLI commands for archiving and restoring chain bundles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envchain.archiver import (
    ArchiveError,
    create_archive,
    deserialise_archive,
    restore_archive,
    serialise_archive,
)


def cmd_archive_save(args, registry) -> int:
    """Bundle one or more chains into an archive file."""
    try:
        archive = create_archive(registry, args.chains, label=args.label or "")
    except ArchiveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    raw = serialise_archive(archive)
    output_path = Path(args.output)
    output_path.write_text(raw, encoding="utf-8")

    chain_list = ", ".join(args.chains)
    print(f"Archived {len(args.chains)} chain(s) [{chain_list}] -> {output_path}")
    return 0


def cmd_archive_restore(args, registry) -> int:
    """Restore chains from an archive file into the registry."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: file not found: {input_path}", file=sys.stderr)
        return 1

    raw = input_path.read_text(encoding="utf-8")
    try:
        archive = deserialise_archive(raw)
    except ArchiveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    chain_names = args.chains if args.chains else None
    try:
        restored = restore_archive(
            archive, registry, overwrite=args.overwrite, chain_names=chain_names
        )
    except ArchiveError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for name in restored:
        print(f"  restored: {name}")
    print(f"Restored {len(restored)} chain(s) from {input_path}")
    return 0


def build_archive_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register 'archive' sub-commands onto an existing subparsers object."""
    archive_p = subparsers.add_parser("archive", help="Bundle chains into a file")
    archive_sub = archive_p.add_subparsers(dest="archive_cmd")

    # save
    save_p = archive_sub.add_parser("save", help="Save chains to an archive file")
    save_p.add_argument("chains", nargs="+", help="Chain names to archive")
    save_p.add_argument("-o", "--output", required=True, help="Output file path")
    save_p.add_argument("--label", default="", help="Optional label for the archive")
    save_p.set_defaults(func=cmd_archive_save)

    # restore
    restore_p = archive_sub.add_parser("restore", help="Restore chains from an archive file")
    restore_p.add_argument("-i", "--input", required=True, help="Archive file path")
    restore_p.add_argument("chains", nargs="*", help="Specific chains to restore (default: all)")
    restore_p.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing chains"
    )
    restore_p.set_defaults(func=cmd_archive_restore)
