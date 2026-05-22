"""CLI commands for searching across chains."""

import argparse
from envchain.registry import ChainRegistry
from envchain.searcher import search_keys


def _format_result_text(r) -> str:
    """Format a single search result as a human-readable string."""
    tag = " [value]" if r.matched_value else ""
    return f"  [{r.chain_name}] {r.key}={r.value}{tag}"


def cmd_search(args: argparse.Namespace, registry: ChainRegistry) -> int:
    """Search for a key (and optionally value) across chains.

    Exit codes:
        0 — one or more results found
        1 — no results found
        2 — usage / argument error
    """
    query = args.query
    if not query:
        print("Error: query must not be empty.")
        return 2

    summary = search_keys(
        registry,
        query,
        search_values=getattr(args, "search_values", False),
        chain_filter=getattr(args, "chain", None),
        case_sensitive=getattr(args, "case_sensitive", False),
    )

    if summary.total == 0:
        print(f"No results for '{query}'.")
        return 1

    fmt = getattr(args, "format", "text")

    if fmt == "json":
        import json
        output = [
            {"chain": r.chain_name, "key": r.key, "value": r.value, "matched_value": r.matched_value}
            for r in summary.results
        ]
        print(json.dumps(output, indent=2))
    else:
        print(f"Found {summary.total} result(s) for '{query}':")
        for r in summary.results:
            print(_format_result_text(r))

    return 0


def build_search_parser(subparsers) -> argparse.ArgumentParser:
    p = subparsers.add_parser(
        "search",
        help="Search for keys (and optionally values) across chains.",
    )
    p.add_argument("query", help="Substring to search for.")
    p.add_argument(
        "--chain",
        default=None,
        metavar="CHAIN",
        help="Restrict search to a specific chain.",
    )
    p.add_argument(
        "--values",
        dest="search_values",
        action="store_true",
        default=False,
        help="Also search inside variable values.",
    )
    p.add_argument(
        "--case-sensitive",
        dest="case_sensitive",
        action="store_true",
        default=False,
        help="Use case-sensitive matching.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    p.set_defaults(func=cmd_search)
    return p
