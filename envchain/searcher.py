"""Search for keys across chains in the registry."""

from dataclasses import dataclass, field
from typing import Optional
from envchain.registry import ChainRegistry


@dataclass
class SearchResult:
    chain_name: str
    key: str
    value: str
    matched_value: bool = False


@dataclass
class SearchSummary:
    query: str
    results: list = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def chains_matched(self) -> list:
        return list(dict.fromkeys(r.chain_name for r in self.results))


def search_keys(
    registry: ChainRegistry,
    query: str,
    *,
    search_values: bool = False,
    chain_filter: Optional[str] = None,
    case_sensitive: bool = False,
) -> SearchSummary:
    """Search for keys (and optionally values) across all chains.

    Args:
        registry: The chain registry to search.
        query: Substring to search for.
        search_values: If True, also match against variable values.
        chain_filter: If provided, restrict search to this chain name.
        case_sensitive: If False (default), comparison is case-insensitive.

    Returns:
        A SearchSummary containing all matching results.
    """
    if not case_sensitive:
        needle = query.lower()
    else:
        needle = query

    summary = SearchSummary(query=query)
    chain_names = registry.list()

    if chain_filter is not None:
        if chain_filter not in chain_names:
            return summary
        chain_names = [chain_filter]

    for name in chain_names:
        chain = registry.get(name)
        for key, value in chain.vars.items():
            k = key if case_sensitive else key.lower()
            v = value if case_sensitive else value.lower()

            key_match = needle in k
            value_match = search_values and needle in v

            if key_match or value_match:
                summary.results.append(
                    SearchResult(
                        chain_name=name,
                        key=key,
                        value=value,
                        matched_value=value_match and not key_match,
                    )
                )

    return summary
