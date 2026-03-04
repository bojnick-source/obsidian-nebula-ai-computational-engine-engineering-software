"""FORGE Core Runtime — orchestration spine (Component A).

Provides the top-level pipeline runner that wires agents, memory,
tools, verification, and observability into a single execution loop.
MVP: synchronous 12-step loop.  V1: async DAG executor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar


class PipelineStatus(Enum):
    """Lifecycle states of a pipeline run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StepResult:
    """Outcome of a single pipeline step."""

    step: int
    name: str
    status: PipelineStatus = PipelineStatus.PENDING
    output: Any = None
    error: str | None = None


@dataclass
class PipelineRun:
    """A single end-to-end analysis run through the 12-step loop.

    Attributes:
        run_id: Unique identifier for this run.
        steps: Ordered results for each step.
        status: Overall pipeline status.
    """

    # Step names matching the 12-step loop in FORGE_CATALOG §2.4
    STEP_NAMES: ClassVar[list[str]] = [
        "receive_query",
        "vault_context_assembly",
        "task_decomposition",
        "dispatch_to_specialists",
        "specialist_analysis",
        "structural_verification",
        "adversarial_verification",
        "confidence_scoring",
        "result_synthesis",
        "vault_persistence",
        "gap_detection",
        "return_response",
    ]

    run_id: str = ""
    steps: list[StepResult] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.PENDING

    def init_steps(self) -> None:
        """Populate *steps* with pending entries for all 12 steps."""
        self.steps = [
            StepResult(step=i + 1, name=name)
            for i, name in enumerate(self.STEP_NAMES)
        ]
        self.status = PipelineStatus.RUNNING
