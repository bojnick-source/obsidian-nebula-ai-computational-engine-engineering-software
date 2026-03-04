"""FORGE Observability & Ops (Component G).

Extends the JSONL logger with metrics counters, error-code taxonomy,
and a cost tracker.  Grafana / dashboard integration deferred to V1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ErrorCode(Enum):
    """Canonical FORGE error codes.

    Using a fixed enum avoids typo-drift across agents and the CLI.
    """

    CONFIG_LOAD_FAILED = "E-CFG-001"
    PROVIDER_UNREACHABLE = "E-PRV-001"
    PROVIDER_RATE_LIMITED = "E-PRV-002"
    BUDGET_EXCEEDED = "E-BDG-001"
    AGENT_TIMEOUT = "E-AGT-001"
    AGENT_INVALID_OUTPUT = "E-AGT-002"
    VERIFICATION_FAILED = "E-VER-001"
    VAULT_READ_ERROR = "E-VLT-001"
    VAULT_WRITE_ERROR = "E-VLT-002"
    TOOL_INVOCATION_FAILED = "E-TLS-001"


@dataclass
class MetricsCounter:
    """Simple in-memory counters for pipeline observability.

    Attributes:
        api_calls:      Total LLM API calls.
        api_failures:   Total failed API calls.
        agent_runs:     Runs per agent ID.
        total_cost_usd: Accumulated cost.
    """

    api_calls: int = 0
    api_failures: int = 0
    agent_runs: dict[str, int] = field(default_factory=dict)
    total_cost_usd: float = 0.0

    def record_api_call(self, cost_usd: float = 0.0) -> None:
        """Record one successful API call."""
        self.api_calls += 1
        self.total_cost_usd += cost_usd

    def record_api_failure(self) -> None:
        """Record one failed API call."""
        self.api_failures += 1

    def record_agent_run(self, agent_id: str) -> None:
        """Increment the run counter for *agent_id*."""
        self.agent_runs[agent_id] = self.agent_runs.get(agent_id, 0) + 1
