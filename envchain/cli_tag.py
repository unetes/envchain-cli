"""CLI commands for managing chain tags."""

from __future__ import annotations
import argparse
from typing import List
from envchain.tagger import TagIndex, TagError


def cmd_tag_add(args: argparse.Namespace, index: TagIndex) -> int:
    """Add one or more tags to a chain."""
    try:
        for tag in args.tags:
            index.add_tag(args.chain, tag)
        print(f"Tagged '{args.chain}' with: {', '.join(args.tags)}")
        return 0
    except TagError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_tag_remove(args: argparse.Namespace, index: TagIndex) -> int:
    """Remove one or more tags from a chain."""
    for tag in args.tags:
        index.remove_tag(args.chain, tag)
    print(f"Removed tags from '{args.chain}': {', '.join(args.tags)}")
    return 0


def cmd_tag_list(args: argparse.Namespace, index: TagIndex) -> int:
    """List tags for a chain, or chains for a tag."""
    if args.chain:
        tags = index.tags_for(args.chain)
        if tags:
            print("\n".join(tags))
        else:
            print(f"No tags for chain '{args.chain}'.")
        return 0
    if args.tag:
        chains = index.chains_for(args.tag)
        if chains:
            print("\n".join(chains))
        else:
            print(f"No chains tagged '{args.tag}'.")
        return 0
    # list all tags
    all_tags = index.all_tags()
    if all_tags:
        print("\n".join(all_tags))
    else:
        print("No tags defined.")
    return 0


def cmd_tag_filter(args: argparse.Namespace, index: TagIndex) -> int:
    """Print chains that match ALL given tags."""
    chains = index.filter_chains(args.tags)
    if chains:
        print("\n".join(chains))
        return 0
    print("No chains match the given tags.")
    return 1


def build_tag_parser(subparsers) -> None:
    p = subparsers.add_parser("tag", help="Manage chain tags")
    sub = p.add_subparsers(dest="tag_cmd")

    add_p = sub.add_parser("add", help="Add tags to a chain")
    add_p.add_argument("chain")
    add_p.add_argument("tags", nargs="+")

    rm_p = sub.add_parser("remove", help="Remove tags from a chain")
    rm_p.add_argument("chain")
    rm_p.add_argument("tags", nargs="+")

    ls_p = sub.add_parser("list", help="List tags or chains")
    ls_p.add_argument("--chain", default=None)
    ls_p.add_argument("--tag", default=None)

    fi_p = sub.add_parser("filter", help="Filter chains by tags")
    fi_p.add_argument("tags", nargs="+")
