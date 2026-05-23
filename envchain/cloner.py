"""Deep-clone a chain into a new name, optionally remapping its parent."""

from __future__ import annotations

from typing import Optional


class CloneError(Exception):
    """Raised when a clone operation cannot be completed."""


def clone_chain(
    registry,
    source_name: str,
    dest_name: str,
    *,
    new_parent: Optional[str] = None,
    keep_parent: bool = True,
    overwrite: bool = False,
) -> object:
    """Clone *source_name* into *dest_name* within *registry*.

    Parameters
    ----------
    registry:
        A :class:`~envchain.registry.ChainRegistry` instance.
    source_name:
        Name of the chain to clone.
    dest_name:
        Name for the new chain.
    new_parent:
        If given, the cloned chain will use this as its parent instead of
        the source chain's parent.
    keep_parent:
        When *True* (default) and *new_parent* is ``None``, the source
        chain's parent is copied to the clone.  Set to *False* to create
        a root chain with no parent.
    overwrite:
        Allow replacing an existing chain with *dest_name*.

    Returns
    -------
    The newly created chain object.
    """
    source = registry.get(source_name)
    if source is None:
        raise CloneError(f"Source chain '{source_name}' does not exist.")

    if dest_name == source_name:
        raise CloneError("Destination name must differ from source name.")

    if registry.get(dest_name) is not None and not overwrite:
        raise CloneError(
            f"Chain '{dest_name}' already exists. Use overwrite=True to replace it."
        )

    # Determine parent for the clone.
    if new_parent is not None:
        if registry.get(new_parent) is None:
            raise CloneError(f"Requested parent chain '{new_parent}' does not exist.")
        parent = new_parent
    elif keep_parent:
        parent = getattr(source, "parent", None)
    else:
        parent = None

    # Copy vars from the source chain (own vars only, not resolved).
    vars_copy = dict(source.vars)

    if overwrite and registry.get(dest_name) is not None:
        registry.remove(dest_name)

    registry.add(dest_name, vars=vars_copy, parent=parent)
    return registry.get(dest_name)
