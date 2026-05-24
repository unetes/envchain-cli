"""CLI commands for the chain inspector."""
from __future__ import annotations

import argparse
import json
from typing import Optional

from envchain.inspector import inspect_chain


def _format_text(report) -> str:
    lines = [
        f"Chain : {report.chain_name}",
        f"Parent: {report.parent or '(none)'}",
        f"Ancestry: {' -> '.join(report.ancestry) or '(root)'}",
        "",
        f"{'KEY':<30} {'VALUE':<30} {'SOURCE':<20} OVERRIDDEN",
        "-" * 90,
    ]
    for ki in report.keys:
        flag = "yes" if ki.overridden else ""
        lines.append(f"{ki.key:<30} {ki.value:<30} {ki.source_chain:<20} {flag}")
    lines.append("")
    lines.append(
        f"Total: {len(report.keys)} keys  "
        f"({len(report.own_keys)} own, {len(report.inherited_keys)} inherited)"
    )
    return "\n".join(lines)


def cmd_inspect(args: argparse.Namespace, registry, out=None) -> int:
    import sys

    out = out or sys.stdout

    try:
        report = inspect_chain(args.chain, registry)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if getattr(args, "format", "text") == "json":
        out.write(json.dumps(report.to_dict(), indent=2))
        out.write("\n")
    else:
        out.write(_format_text(report))
        out.write("\n")

    return 0


def build_inspect_parser(subparsers) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "inspect",
        help="Show a detailed breakdown of a chain's keys and their origins.",
    )
    p.add_argument("chain", help="Name of the chain to inspect.")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_inspect)
    return p
