"""CLI commands for merging multiple chains."""

import json
import sys
from typing import List, Optional

from envchain.merger import MergeConflictError, merge_chains


def cmd_merge(
    registry,
    chain_names: List[str],
    strategy: str = "last_wins",
    output_format: str = "shell",
    out=None,
) -> int:
    """Merge multiple chains and print the result.

    Args:
        registry: A ChainRegistry instance.
        chain_names: Ordered list of chain names to merge.
        strategy: 'first_wins', 'last_wins', or 'raise_on_conflict'.
        output_format: 'shell', 'json', or 'dotenv'.
        out: Output stream (defaults to sys.stdout).

    Returns:
        Exit code (0 on success, 1 on error).
    """
    if out is None:
        out = sys.stdout

    if not chain_names:
        print("Error: at least one chain name is required.", file=sys.stderr)
        return 1

    valid_strategies = ("first_wins", "last_wins", "raise_on_conflict")
    if strategy not in valid_strategies:
        print(
            f"Error: unknown strategy '{strategy}'. Choose from: {', '.join(valid_strategies)}",
            file=sys.stderr,
        )
        return 1

    try:
        merged = merge_chains(registry, chain_names, strategy=strategy)  # type: ignore[arg-type]
    except MergeConflictError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyError as exc:
        print(f"Error: chain not found: {exc}", file=sys.stderr)
        return 1

    _render(merged, chain_names, output_format, out)
    return 0


def _render(vars_dict: dict, chain_names: List[str], fmt: str, out) -> None:
    """Render merged vars to the output stream in the requested format."""
    if fmt == "json":
        json.dump(vars_dict, out, indent=2)
        out.write("\n")
    elif fmt == "dotenv":
        out.write(f"# merged: {', '.join(chain_names)}\n")
        for key, value in sorted(vars_dict.items()):
            escaped = value.replace('"', '\\"')
            out.write(f'{key}="{escaped}"\n')
    else:  # shell
        out.write(f"# merged: {', '.join(chain_names)}\n")
        for key, value in sorted(vars_dict.items()):
            escaped = value.replace("'", "'\"'\"'")
            out.write(f"export {key}='{escaped}'\n")
