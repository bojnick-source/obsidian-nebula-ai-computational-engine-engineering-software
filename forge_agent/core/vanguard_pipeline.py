"""
forge_agent/core/vanguard_pipeline.py

Domain-routed PipelineRunner for Void Vanguard agent pairs.

Selects the correct specialist SYSTEM_PROMPT and AntagonistClass for a given
domain string and delegates execution to PipelineRunner with a wired
DebateOrchestrator.

Valid domains: "synthmuscle", "mujoco_sim", "cmaes_opt", "actuator_safety"
"""

from __future__ import annotations

from typing import Any

from forge_agent.core.pipeline import PipelineRunner, TaskRequest, TaskResult
from forge_agent.core.debate_orchestrator import DebateOrchestrator
from forge_agent.agents.vanguard import synthmuscle, mujoco_simulation
from forge_agent.agents.vanguard import cmaes_optimization, actuator_safety
from forge_agent.agents.vanguard.synthmuscle_antagonist import SynthmuscleAntagonist
from forge_agent.agents.vanguard.mujoco_simulation_antagonist import MuJoCoSimulationAntagonist
from forge_agent.agents.vanguard.cmaes_optimization_antagonist import CMAESOptimizationAntagonist
from forge_agent.agents.vanguard.actuator_safety_antagonist import ActuatorSafetyAntagonist

_VALID_DOMAINS = frozenset({"synthmuscle", "mujoco_sim", "cmaes_opt", "actuator_safety"})

_DOMAIN_MAP: dict[str, tuple[str, type]] = {
    "synthmuscle":     (synthmuscle.SYSTEM_PROMPT,        SynthmuscleAntagonist),
    "mujoco_sim":      (mujoco_simulation.SYSTEM_PROMPT,  MuJoCoSimulationAntagonist),
    "cmaes_opt":       (cmaes_optimization.SYSTEM_PROMPT, CMAESOptimizationAntagonist),
    "actuator_safety": (actuator_safety.SYSTEM_PROMPT,    ActuatorSafetyAntagonist),
}


class VanguardPipelineRunner:
    """Domain-routed PipelineRunner for Void Vanguard agent pairs.

    Selects the correct specialist system prompt and antagonist for the given
    domain, wires them through DebateOrchestrator, and delegates to PipelineRunner.

    Parameters
    ----------
    domain:
        One of "synthmuscle", "mujoco_sim", "cmaes_opt", "actuator_safety".
    config:
        Forge runtime configuration dict (passed to PipelineRunner).
    tool_executor:
        Optional tool executor override (passed to PipelineRunner).
    vault_manager:
        Optional vault manager override (passed to PipelineRunner).
    anthropic_client:
        Optional Anthropic client (passed to PipelineRunner).
    """

    def __init__(
        self,
        domain: str,
        config: dict,
        tool_executor: Any = None,
        vault_manager: Any = None,
        anthropic_client: Any = None,
    ) -> None:
        # All 5 params stored and used — P2 compliant.
        if domain not in _VALID_DOMAINS:
            raise ValueError(
                f"VanguardPipelineRunner: unknown domain {domain!r}. "
                f"Valid domains: {sorted(_VALID_DOMAINS)}"
            )
        self._domain = domain   # stored for repr / debugging (P2)

        specialist_prompt, AntagonistClass = _DOMAIN_MAP[domain]
        antagonist = AntagonistClass()

        # specialist=None — stored but not called in current single-round impl (P2).
        # If a future run_debate() calls self._specialist, a clear AttributeError
        # is raised rather than silently passing wrong data.
        debate_orchestrator = DebateOrchestrator(
            specialist=None,
            antagonist=antagonist,
        )

        self._runner = PipelineRunner(
            config=config,
            tool_executor=tool_executor,
            vault_manager=vault_manager,
            anthropic_client=anthropic_client,
            specialist_prompt=specialist_prompt,
            debate_orchestrator=debate_orchestrator,
        )

    def run(self, request: TaskRequest) -> TaskResult:
        """Delegate to the underlying PipelineRunner.run()."""
        return self._runner.run(request)
