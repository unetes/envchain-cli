"""Group chains by shared keys or tags, producing logical collections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class GroupError(Exception):
    """Raised when a grouping operation fails."""


@dataclass
class ChainGroup:
    name: str
    chains: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "chains": sorted(self.chains),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChainGroup":
        return cls(
            name=data["name"],
            chains=list(data.get("chains", [])),
            description=data.get("description", ""),
        )

    def __str__(self) -> str:
        return f"[{self.name}] {len(self.chains)} chain(s): {', '.join(sorted(self.chains))}"


@dataclass
class GroupIndex:
    _groups: Dict[str, ChainGroup] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {name: g.to_dict() for name, g in self._groups.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "GroupIndex":
        idx = cls()
        for name, raw in data.items():
            idx._groups[name] = ChainGroup.from_dict(raw)
        return idx


def create_group(index: GroupIndex, name: str, description: str = "") -> ChainGroup:
    if name in index._groups:
        raise GroupError(f"Group '{name}' already exists.")
    group = ChainGroup(name=name, description=description)
    index._groups[name] = group
    return group


def delete_group(index: GroupIndex, name: str) -> None:
    if name not in index._groups:
        raise GroupError(f"Group '{name}' does not exist.")
    del index._groups[name]


def add_chain_to_group(index: GroupIndex, group_name: str, chain_name: str) -> None:
    if group_name not in index._groups:
        raise GroupError(f"Group '{group_name}' does not exist.")
    group = index._groups[group_name]
    if chain_name not in group.chains:
        group.chains.append(chain_name)


def remove_chain_from_group(index: GroupIndex, group_name: str, chain_name: str) -> None:
    if group_name not in index._groups:
        raise GroupError(f"Group '{group_name}' does not exist.")
    group = index._groups[group_name]
    if chain_name not in group.chains:
        raise GroupError(f"Chain '{chain_name}' is not in group '{group_name}'.")
    group.chains.remove(chain_name)


def list_groups(index: GroupIndex) -> List[ChainGroup]:
    return sorted(index._groups.values(), key=lambda g: g.name)


def get_group(index: GroupIndex, name: str) -> Optional[ChainGroup]:
    return index._groups.get(name)
