"""FORGE Recovery & Continuity (Component L).

Utilities for snapshotting pipeline state, creating backups of the
vault, and restoring from a known-good checkpoint.

MVP: in-memory snapshot / restore stubs.
Persistent backup (zip archive, S3 upload) deferred to M7.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Snapshot:
    """Point-in-time capture of pipeline + blackboard state.

    Attributes:
        snapshot_id:  Unique label.
        created_at:   ISO-8601 timestamp.
        blackboard:   Frozen blackboard contents.
        metadata:     Arbitrary context (run_id, step, etc.).
    """

    snapshot_id: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    blackboard: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class RecoveryManager:
    """Manages snapshots for pipeline continuity.

    In-memory for MVP; persistent back-end added in M7.
    """

    def __init__(self) -> None:
        self._snapshots: dict[str, Snapshot] = {}

    def save(self, snapshot: Snapshot) -> None:
        """Store a snapshot."""
        self._snapshots[snapshot.snapshot_id] = snapshot

    def restore(self, snapshot_id: str) -> Snapshot | None:
        """Retrieve a snapshot by ID.  Returns ``None`` if absent."""
        return self._snapshots.get(snapshot_id)

    def list_ids(self) -> list[str]:
        """Return all stored snapshot IDs."""
        return list(self._snapshots.keys())
