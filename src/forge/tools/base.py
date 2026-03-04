"""FORGE Tool wrapper base (Component D).

Every external solver/geometry tool (CalculiX, GMSH, …) is wrapped as
a ``ToolWrapper`` subclass.  The wrapper validates inputs, invokes the
tool as a subprocess, and parses outputs into structured Python objects.

MVP tools (T-01 CalculiX, T-06 GMSH) are *planned* for M6.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Standardised result from a tool invocation.

    Attributes:
        tool_id:   Tool identifier from forge.yaml.
        success:   Whether the invocation succeeded.
        output:    Parsed output data.
        exit_code: Subprocess exit code (``None`` when not yet invoked).
        error:     Error message on failure.
    """

    tool_id: str
    success: bool = False
    output: dict[str, Any] = field(default_factory=dict)
    exit_code: int | None = None
    error: str | None = None


class ToolWrapper(ABC):
    """Abstract base for MCP tool wrappers.

    Subclasses implement ``invoke`` to call the underlying solver
    and return a ``ToolResult``.
    """

    def __init__(self, tool_id: str, status: str = "planned") -> None:
        self.tool_id = tool_id
        self.status = status

    @abstractmethod
    def invoke(self, params: dict[str, Any]) -> ToolResult:
        """Run the wrapped tool with the given parameters."""
        ...  # pragma: no cover
