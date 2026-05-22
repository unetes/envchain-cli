"""Rename keys across one or more variable dictionaries."""

from typing import Dict, List, Optional


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


def rename_key(
    vars_dict: Dict[str, str],
    old_key: str,
    new_key: str,
    *,
    overwrite: bool = False,
) -> Dict[str, str]:
    """Return a new dict with *old_key* renamed to *new_key*.

    Args:
        vars_dict: Source variable mapping.
        old_key: The key to rename.
        new_key: The desired new key name.
        overwrite: If True, silently replace an existing *new_key* value.
                   If False (default) raise :class:`RenameError`.

    Returns:
        A new dictionary with the rename applied.

    Raises:
        RenameError: If *old_key* is not found, *new_key* already exists and
                     *overwrite* is False, or either key is empty.
    """
    if not old_key:
        raise RenameError("old_key must not be empty")
    if not new_key:
        raise RenameError("new_key must not be empty")
    if old_key not in vars_dict:
        raise RenameError(f"Key '{old_key}' not found in vars")
    if new_key in vars_dict and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists; pass overwrite=True to replace it"
        )

    result = {k: v for k, v in vars_dict.items() if k != old_key}
    result[new_key] = vars_dict[old_key]
    return result


def rename_key_in_chains(
    chains: Dict[str, Dict[str, str]],
    old_key: str,
    new_key: str,
    *,
    chain_names: Optional[List[str]] = None,
    overwrite: bool = False,
    skip_missing: bool = True,
) -> Dict[str, Dict[str, str]]:
    """Apply :func:`rename_key` across multiple chain variable dicts.

    Args:
        chains: Mapping of chain-name -> vars dict.
        old_key: Key to rename.
        new_key: New key name.
        chain_names: Subset of chains to operate on; defaults to all.
        overwrite: Forwarded to :func:`rename_key`.
        skip_missing: When True, chains that do not contain *old_key* are
                      left unchanged instead of raising an error.

    Returns:
        A new dict with the same chain names but updated variable dicts.
    """
    targets = set(chain_names) if chain_names is not None else set(chains.keys())
    result: Dict[str, Dict[str, str]] = {}
    for name, vars_dict in chains.items():
        if name not in targets or (skip_missing and old_key not in vars_dict):
            result[name] = dict(vars_dict)
        else:
            result[name] = rename_key(vars_dict, old_key, new_key, overwrite=overwrite)
    return result
