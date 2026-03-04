"""Bridge base class — normalises external data into FORGE contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BridgeResult:
    """Standardised result from an import bridge.

    Attributes:
        bridge_id: Identifier for the bridge adapter.
        success:   Whether the import/export succeeded.
        data:      Normalised payload.
        error:     Error message on failure.
    """

    bridge_id: str
    success: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class BaseBridge(ABC):
    """Abstract base for external-ecosystem bridges.

    Subclasses implement ``import_data`` and ``export_data``
    for a specific external format or tool.
    """

    def __init__(self, bridge_id: str) -> None:
        self.bridge_id = bridge_id

    @abstractmethod
    def import_data(self, source: str) -> BridgeResult:
        """Import data from *source* into FORGE format."""
        ...  # pragma: no cover

    @abstractmethod
    def export_data(self, payload: dict[str, Any], dest: str) -> BridgeResult:
        """Export FORGE data to *dest* in the bridge's native format."""
        ...  # pragma: no cover
