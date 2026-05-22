"""CLI commands for profile management."""

from __future__ import annotations

import argparse
from typing import Any

from envchain.profiler import (
    ProfileError,
    ProfileIndex,
    add_to_profile,
    chains_for_profile,
    delete_profile,
    list_profiles,
    profiles_for_chain,
    remove_from_profile,
)


def cmd_profile_add(args: Any, index: ProfileIndex) -> int:
    """Add a chain to a profile."""
    try:
        add_to_profile(index, args.profile, args.chain)
        print(f"Added '{args.chain}' to profile '{args.profile}'.")
        return 0
    except ProfileError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_profile_remove(args: Any, index: ProfileIndex) -> int:
    """Remove a chain from a profile."""
    try:
        remove_from_profile(index, args.profile, args.chain)
        print(f"Removed '{args.chain}' from profile '{args.profile}'.")
        return 0
    except ProfileError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_profile_list(args: Any, index: ProfileIndex) -> int:
    """List all profiles or chains within a profile."""
    if args.profile:
        chains = chains_for_profile(index, args.profile)
        if not chains:
            print(f"Profile '{args.profile}' is empty or does not exist.")
            return 0
        for chain in chains:
            print(chain)
    else:
        profiles = list_profiles(index)
        if not profiles:
            print("No profiles defined.")
            return 0
        for profile in profiles:
            count = len(chains_for_profile(index, profile))
            print(f"{profile}  ({count} chain(s))")
    return 0


def cmd_profile_delete(args: Any, index: ProfileIndex) -> int:
    """Delete an entire profile."""
    try:
        delete_profile(index, args.profile)
        print(f"Deleted profile '{args.profile}'.")
        return 0
    except ProfileError as exc:
        print(f"Error: {exc}")
        return 1


def build_profile_parser(subparsers: Any) -> None:
    p = subparsers.add_parser("profile", help="Manage chain profiles")
    sub = p.add_subparsers(dest="profile_cmd", required=True)

    add_p = sub.add_parser("add", help="Add chain to profile")
    add_p.add_argument("profile")
    add_p.add_argument("chain")

    rm_p = sub.add_parser("remove", help="Remove chain from profile")
    rm_p.add_argument("profile")
    rm_p.add_argument("chain")

    ls_p = sub.add_parser("list", help="List profiles or chains in a profile")
    ls_p.add_argument("profile", nargs="?", default=None)

    del_p = sub.add_parser("delete", help="Delete a profile")
    del_p.add_argument("profile")
