"""Tag-based grouping and filtering of environment chains."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set


class TagError(Exception):
    """Raised when a tagging operation fails."""


@dataclass
class TagIndex:
    """Maps tags to sets of chain names."""
    _index: Dict[str, Set[str]] = field(default_factory=dict)

    def add_tag(self, chain_name: str, tag: str) -> None:
        """Associate *tag* with *chain_name*."""
        tag = _normalise(tag)
        if not tag:
            raise TagError("Tag must not be empty.")
        self._index.setdefault(tag, set()).add(chain_name)

    def remove_tag(self, chain_name: str, tag: str) -> None:
        """Remove *tag* from *chain_name*. Silently ignores missing entries."""
        tag = _normalise(tag)
        if tag in self._index:
            self._index[tag].discard(chain_name)
            if not self._index[tag]:
                del self._index[tag]

    def tags_for(self, chain_name: str) -> List[str]:
        """Return sorted list of tags associated with *chain_name*."""
        return sorted(t for t, chains in self._index.items() if chain_name in chains)

    def chains_for(self, tag: str) -> List[str]:
        """Return sorted list of chain names associated with *tag*."""
        tag = _normalise(tag)
        return sorted(self._index.get(tag, set()))

    def all_tags(self) -> List[str]:
        """Return sorted list of all known tags."""
        return sorted(self._index.keys())

    def remove_chain(self, chain_name: str) -> None:
        """Remove *chain_name* from every tag entry."""
        for tag in list(self._index):
            self._index[tag].discard(chain_name)
            if not self._index[tag]:
                del self._index[tag]

    def filter_chains(self, tags: List[str]) -> List[str]:
        """Return chains that have ALL of the given *tags*."""
        if not tags:
            return []
        sets = [self._index.get(_normalise(t), set()) for t in tags]
        return sorted(set.intersection(*sets))


def _normalise(tag: str) -> str:
    return tag.strip().lower()
