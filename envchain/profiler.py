"""Profile management: group chains under named profiles (e.g. dev, staging, prod)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ProfileError(Exception):
    """Raised for invalid profile operations."""


@dataclass
class ProfileIndex:
    """Maps profile names to lists of chain names."""
    _data: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: list(v) for k, v in self._data.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "ProfileIndex":
        idx = cls()
        for profile, chains in data.items():
            idx._data[profile] = list(chains)
        return idx


def add_to_profile(index: ProfileIndex, profile: str, chain: str) -> None:
    """Add *chain* to *profile*, creating the profile if necessary."""
    if not profile:
        raise ProfileError("Profile name must not be empty.")
    if not chain:
        raise ProfileError("Chain name must not be empty.")
    chains = index._data.setdefault(profile, [])
    if chain not in chains:
        chains.append(chain)
        chains.sort()


def remove_from_profile(index: ProfileIndex, profile: str, chain: str) -> None:
    """Remove *chain* from *profile*."""
    chains = index._data.get(profile, [])
    if chain not in chains:
        raise ProfileError(f"Chain '{chain}' is not in profile '{profile}'.")
    chains.remove(chain)
    if not chains:
        del index._data[profile]


def chains_for_profile(index: ProfileIndex, profile: str) -> List[str]:
    """Return sorted list of chains belonging to *profile*."""
    return sorted(index._data.get(profile, []))


def profiles_for_chain(index: ProfileIndex, chain: str) -> List[str]:
    """Return sorted list of profiles that contain *chain*."""
    return sorted(p for p, chains in index._data.items() if chain in chains)


def list_profiles(index: ProfileIndex) -> List[str]:
    """Return all profile names in sorted order."""
    return sorted(index._data.keys())


def delete_profile(index: ProfileIndex, profile: str) -> None:
    """Delete an entire profile."""
    if profile not in index._data:
        raise ProfileError(f"Profile '{profile}' does not exist.")
    del index._data[profile]
