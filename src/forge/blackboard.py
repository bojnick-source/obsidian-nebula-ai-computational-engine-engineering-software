"""FORGE Blackboard — typed dict store for inter-agent communication.

The blackboard is the shared state between agents during a pipeline run.
MVP implementation: Python dict + Pydantic validation.
Target: <50ms read/write (trivially achievable with in-memory dict).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class BlackboardEntry(BaseModel):
    """A single entry in the blackboard."""

    key: str
    value: Any
    written_by: str = "system"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Blackboard:
    """In-memory typed-dict blackboard for FORGE agent communication.

    Agents write analysis results, verification outcomes, and intermediate
    data here. The orchestrator reads from the blackboard to assemble
    final outputs and route tasks.
    """

    def __init__(self) -> None:
        self._store: dict[str, BlackboardEntry] = {}

    def put(self, key: str, value: Any, written_by: str = "system") -> None:
        """Write a value to the blackboard."""
        self._store[key] = BlackboardEntry(
            key=key, value=value, written_by=written_by
        )

    def get(self, key: str) -> Any | None:
        """Read a value from the blackboard. Returns None if key missing."""
        entry = self._store.get(key)
        return entry.value if entry is not None else None

    def get_entry(self, key: str) -> BlackboardEntry | None:
        """Read the full entry (with metadata) from the blackboard."""
        return self._store.get(key)

    def keys(self) -> list[str]:
        """List all keys in the blackboard."""
        return list(self._store.keys())

    def has(self, key: str) -> bool:
        """Check if a key exists in the blackboard."""
        return key in self._store

    def clear(self) -> None:
        """Clear all entries from the blackboard."""
        self._store.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return a snapshot of all blackboard values."""
        return {k: v.value for k, v in self._store.items()}
