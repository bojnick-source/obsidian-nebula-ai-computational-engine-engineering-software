"""Pipeline registry — catalogues available project pipelines.

Each entry maps a pipeline name to its configuration.
Concrete pipeline implementations are added from M5 onward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineSpec:
    """Declarative specification for a project pipeline.

    Attributes:
        name:     Human-readable pipeline name.
        agents:   Ordered list of agent IDs to invoke.
        tools:    Tool IDs available for this pipeline.
        metadata: Arbitrary project-specific metadata.
    """

    name: str
    agents: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PipelineRegistry:
    """In-memory registry of available pipelines."""

    def __init__(self) -> None:
        self._pipelines: dict[str, PipelineSpec] = {}

    def register(self, spec: PipelineSpec) -> None:
        """Register a pipeline specification."""
        self._pipelines[spec.name] = spec

    def get(self, name: str) -> PipelineSpec | None:
        """Retrieve a pipeline spec by name."""
        return self._pipelines.get(name)

    def list_names(self) -> list[str]:
        """Return all registered pipeline names."""
        return list(self._pipelines.keys())
