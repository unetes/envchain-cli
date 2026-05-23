"""Notification hooks for envchain events (key set, chain created, etc.)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class NotifierError(Exception):
    """Raised when a notification hook fails."""


@dataclass
class NotifyEvent:
    """Represents a single envchain event to be dispatched."""

    event_type: str          # e.g. 'key_set', 'chain_created', 'chain_deleted'
    chain: str
    key: Optional[str] = None
    meta: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "chain": self.chain,
            "key": self.key,
            "meta": self.meta,
        }

    def __str__(self) -> str:
        parts = [f"[{self.event_type}] chain={self.chain}"]
        if self.key:
            parts.append(f"key={self.key}")
        return " ".join(parts)


HookFn = Callable[[NotifyEvent], None]


class NotifierIndex:
    """Registry of named notification hooks."""

    def __init__(self) -> None:
        self._hooks: Dict[str, HookFn] = {}

    def register(self, name: str, fn: HookFn) -> None:
        """Register a hook under *name*. Overwrites any existing hook."""
        if not name:
            raise NotifierError("Hook name must not be empty.")
        self._hooks[name] = fn

    def unregister(self, name: str) -> None:
        """Remove a previously registered hook."""
        if name not in self._hooks:
            raise NotifierError(f"No hook registered under '{name}'.")
        del self._hooks[name]

    def hook_names(self) -> List[str]:
        return sorted(self._hooks)

    def dispatch(self, event: NotifyEvent) -> List[str]:
        """Call all hooks with *event*. Returns list of hooks that raised."""
        failed: List[str] = []
        for name, fn in self._hooks.items():
            try:
                fn(event)
            except Exception:
                failed.append(name)
        return failed
