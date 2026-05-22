"""Merge multiple chains or variable dicts with conflict resolution strategies."""

from typing import Dict, List, Literal, Optional

MergeStrategy = Literal["first_wins", "last_wins", "raise_on_conflict"]


class MergeConflictError(Exception):
    """Raised when conflicting keys are found and strategy is 'raise_on_conflict'."""

    def __init__(self, key: str, sources: List[str]):
        self.key = key
        self.sources = sources
        super().__init__(
            f"Merge conflict: key '{key}' found in multiple sources: {sources}"
        )


def merge_vars(
    sources: List[Dict[str, str]],
    labels: Optional[List[str]] = None,
    strategy: MergeStrategy = "last_wins",
) -> Dict[str, str]:
    """Merge a list of variable dicts using the given strategy.

    Args:
        sources: Ordered list of variable dicts to merge.
        labels: Optional human-readable names for each source (for error messages).
        strategy: How to handle key conflicts:
            - 'first_wins': first occurrence of a key takes precedence.
            - 'last_wins': last occurrence of a key takes precedence (default).
            - 'raise_on_conflict': raise MergeConflictError on duplicate keys.

    Returns:
        Merged dict of environment variables.
    """
    if labels is None:
        labels = [f"source[{i}]" for i in range(len(sources))]

    if len(labels) != len(sources):
        raise ValueError("Length of labels must match length of sources.")

    merged: Dict[str, str] = {}
    key_origin: Dict[str, str] = {}  # tracks which label first defined each key

    for label, source in zip(labels, sources):
        for key, value in source.items():
            if key in merged:
                if strategy == "raise_on_conflict":
                    raise MergeConflictError(key, [key_origin[key], label])
                elif strategy == "first_wins":
                    continue  # keep existing value
                else:  # last_wins
                    merged[key] = value
                    key_origin[key] = label
            else:
                merged[key] = value
                key_origin[key] = label

    return merged


def merge_chains(registry, chain_names: List[str], strategy: MergeStrategy = "last_wins") -> Dict[str, str]:
    """Resolve and merge multiple chains by name.

    Args:
        registry: A ChainRegistry instance.
        chain_names: Names of chains to merge in order.
        strategy: Conflict resolution strategy.

    Returns:
        Merged dict of resolved environment variables.
    """
    from envchain.chain import resolve

    sources = [resolve(registry, name) for name in chain_names]
    return merge_vars(sources, labels=chain_names, strategy=strategy)
