"""Archive and restore chains to/from a portable bundle format."""

from __future__ import annotations

import json
import time
from typing import Dict, List, Optional

ARCHIVE_VERSION = 1


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


def create_archive(
    registry,
    chain_names: List[str],
    label: str = "",
) -> Dict:
    """Build an archive dict containing the given chains and their resolved vars."""
    if not chain_names:
        raise ArchiveError("No chains specified for archiving.")

    entries = {}
    for name in chain_names:
        chain = registry.get(name)
        if chain is None:
            raise ArchiveError(f"Chain '{name}' not found in registry.")
        entries[name] = {
            "parent": chain.parent,
            "vars": dict(chain.vars),
        }

    return {
        "version": ARCHIVE_VERSION,
        "label": label,
        "created_at": time.time(),
        "chains": entries,
    }


def serialise_archive(archive: Dict) -> str:
    """Serialise an archive dict to a JSON string."""
    return json.dumps(archive, indent=2)


def deserialise_archive(raw: str) -> Dict:
    """Parse a JSON string into an archive dict."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArchiveError(f"Invalid archive JSON: {exc}") from exc

    if data.get("version") != ARCHIVE_VERSION:
        raise ArchiveError(
            f"Unsupported archive version: {data.get('version')}"
        )
    if "chains" not in data:
        raise ArchiveError("Archive is missing 'chains' key.")
    return data


def restore_archive(
    archive: Dict,
    registry,
    overwrite: bool = False,
    chain_names: Optional[List[str]] = None,
) -> List[str]:
    """Restore chains from an archive into the registry.

    Returns the list of chain names that were restored.
    """
    to_restore = chain_names or list(archive["chains"].keys())
    restored = []

    for name in to_restore:
        if name not in archive["chains"]:
            raise ArchiveError(f"Chain '{name}' not found in archive.")
        entry = archive["chains"][name]
        if registry.get(name) is not None and not overwrite:
            raise ArchiveError(
                f"Chain '{name}' already exists. Use overwrite=True to replace it."
            )
        registry.add(name, parent=entry.get("parent"), vars=entry.get("vars", {}))
        restored.append(name)

    return restored
