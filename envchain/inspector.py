"""Inspector: produce a detailed breakdown of a single chain's state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeyInfo:
    key: str
    value: str
    source_chain: str  # which chain in the ancestry actually defines it
    overridden: bool = False  # True when a child chain shadows this key

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source_chain": self.source_chain,
            "overridden": self.overridden,
        }


@dataclass
class InspectReport:
    chain_name: str
    parent: Optional[str]
    ancestry: List[str]  # ordered root → direct parent
    keys: List[KeyInfo] = field(default_factory=list)

    @property
    def own_keys(self) -> List[KeyInfo]:
        return [k for k in self.keys if k.source_chain == self.chain_name]

    @property
    def inherited_keys(self) -> List[KeyInfo]:
        return [k for k in self.keys if k.source_chain != self.chain_name]

    def to_dict(self) -> dict:
        return {
            "chain_name": self.chain_name,
            "parent": self.parent,
            "ancestry": self.ancestry,
            "keys": [k.to_dict() for k in self.keys],
        }


def inspect_chain(chain_name: str, registry) -> InspectReport:
    """Build an InspectReport for *chain_name* using *registry*."""
    chain = registry.get(chain_name)
    if chain is None:
        raise ValueError(f"Chain '{chain_name}' not found in registry.")

    from envchain.chain import _ancestors  # avoid circular at module level

    ancestry = list(_ancestors(chain_name, registry))
    parent = chain.parent if hasattr(chain, "parent") else None

    # Walk ancestry from root → direct-parent to build source map
    source_map: Dict[str, str] = {}
    for ancestor in ancestry:
        anc_chain = registry.get(ancestor)
        if anc_chain is None:
            continue
        for k, v in anc_chain.vars.items():
            source_map[k] = ancestor  # later ancestor wins (closer to child)

    # Own vars override everything
    for k in chain.vars:
        source_map[k] = chain_name

    # Determine which ancestor keys are shadowed by the target chain
    resolved = dict(chain.vars)
    for ancestor in ancestry:
        anc_chain = registry.get(ancestor)
        if anc_chain:
            for k, v in anc_chain.vars.items():
                if k not in resolved:
                    resolved[k] = v

    keys: List[KeyInfo] = []
    for k in sorted(resolved):
        src = source_map.get(k, chain_name)
        overridden = (src != chain_name) and (k in chain.vars)
        # If the child defines it, source is chain_name; overridden flag on
        # ancestor entries that the child shadows would need inverse logic —
        # here we mark a key as overridden when child redefines an ancestor key.
        actual_src = chain_name if k in chain.vars else src
        overridden = (k in chain.vars) and (src != chain_name or any(
            k in (registry.get(a).vars if registry.get(a) else {}) for a in ancestry
        ))
        keys.append(KeyInfo(key=k, value=resolved[k], source_chain=actual_src, overridden=overridden))

    return InspectReport(
        chain_name=chain_name,
        parent=parent,
        ancestry=ancestry,
        keys=keys,
    )
