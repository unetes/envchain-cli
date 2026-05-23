"""CLI commands for CSV export and import of chains."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envchain.exporter_csv import CsvError, export_csv, export_multi_csv, parse_csv


def cmd_csv_export(
    args: argparse.Namespace,
    registry,  # ChainRegistry
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Export one or all chains to CSV."""
    chain_names = args.chains if args.chains else list(registry.all_names())
    if not chain_names:
        err.write("No chains available to export.\n")
        return 1

    if len(chain_names) == 1:
        name = chain_names[0]
        chain = registry.get(name)
        if chain is None:
            err.write(f"Chain '{name}' not found.\n")
            return 1
        csv_text = export_csv(name, chain.vars, include_header=True)
    else:
        chains_data = {}
        for name in chain_names:
            chain = registry.get(name)
            if chain is None:
                err.write(f"Chain '{name}' not found.\n")
                return 1
            chains_data[name] = chain.vars
        csv_text = export_multi_csv(chains_data)

    if args.output:
        Path(args.output).write_text(csv_text, encoding="utf-8")
        out.write(f"Exported to {args.output}\n")
    else:
        out.write(csv_text)
    return 0


def cmd_csv_import(
    args: argparse.Namespace,
    registry,  # ChainRegistry
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Import variables from a CSV file into the registry."""
    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except OSError as exc:
        err.write(f"Cannot read file: {exc}\n")
        return 1

    try:
        parsed = parse_csv(text, expected_chain=args.chain or None)
    except CsvError as exc:
        err.write(f"CSV error: {exc}\n")
        return 1

    for chain_name, variables in parsed.items():
        chain = registry.get(chain_name)
        if chain is None:
            err.write(f"Chain '{chain_name}' not found; skipping.\n")
            continue
        chain.vars.update(variables)
        out.write(f"Imported {len(variables)} variable(s) into '{chain_name}'.\n")
    return 0


def build_csv_parser(subparsers) -> None:
    """Attach csv sub-commands to *subparsers*."""
    p = subparsers.add_parser("csv", help="CSV export / import")
    sub = p.add_subparsers(dest="csv_cmd", required=True)

    exp = sub.add_parser("export", help="Export chains to CSV")
    exp.add_argument("chains", nargs="*", help="Chain names (default: all)")
    exp.add_argument("-o", "--output", help="Output file path")

    imp = sub.add_parser("import", help="Import variables from CSV")
    imp.add_argument("file", help="CSV file to import")
    imp.add_argument("--chain", help="Restrict import to this chain name")
