"""FORGE Agent base class (Component B).

Every MVP agent (specialist, verifier, antagonist, librarian) inherits
from ``BaseAgent``.  The base class enforces the contract that every
agent can be invoked with a blackboard context and must return a typed
``AgentResult``.

Concrete agent implementations live alongside their SKILL.yaml files
under ``agents/<name>/`` and are registered in *forge.yaml*.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    """Standardised return value from any FORGE agent.

    Attributes:
        agent_id:  The agent's registered ID (e.g. ``ORCH-01``).
        status:    ``"ok"`` | ``"error"`` | ``"partial"``.
        payload:   Free-form result dict.
        confidence: Optional confidence score (0.0–1.0).
        sources:   Provenance references.
    """

    agent_id: str
    status: str = "ok"
    payload: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    sources: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """Abstract base for all FORGE agents.

    Sub-classes must implement ``run`` which receives context from the
    blackboard and returns an ``AgentResult``.
    """

    def __init__(self, agent_id: str, role: str) -> None:
        self.agent_id = agent_id
        self.role = role

    @abstractmethod
    def run(self, context: dict[str, Any]) -> AgentResult:
        """Execute the agent's task given a blackboard snapshot.

        Parameters:
            context: A dict snapshot from the blackboard.

        Returns:
            AgentResult with the agent's output.
        """
        ...  # pragma: no cover
