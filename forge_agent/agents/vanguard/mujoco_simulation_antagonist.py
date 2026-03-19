"""FORGE MuJoCo Simulation Antagonist — heuristic critique agent."""
from __future__ import annotations

from forge_agent.agents.antagonist_base import AntagonistAgent


class MuJoCoSimulationAntagonist(AntagonistAgent):
    """Antagonist agent for the MuJoCo Simulation Specialist.

    Validates determinism (seed presence) and trajectory quality (step count).
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="mujoco_simulation_antagonist",
            domain="mujoco_sim",
        )

    def _generate_critique(
        self,
        specialist_output: dict,
        context: dict,
    ) -> dict:
        _ = context  # consumed (P2)

        # AC 4: missing seed → non-deterministic → fatal
        if "seed" not in specialist_output:
            return {
                "error_code": None,
                "critique_type": "methodology",
                "severity": "fatal",
                "detail": (
                    "No random seed was specified in the simulation output. "
                    "Without a fixed seed, the MuJoCo simulation trajectory is "
                    "non-deterministic and cannot be reproduced for verification, "
                    "CMA-ES fitness evaluation, or sim-to-real gap measurement. "
                    "Every FORGE simulation must record the seed used."
                ),
                "evidence": (
                    "MuJoCo Simulation SKILL.md: deterministic step validation "
                    "requires fixed seed (MVP requirement). mujoco_step CLI "
                    "handler always returns seed in output."
                ),
                "confidence_delta": -0.6,
            }

        # AC 5: steps < 100 → insufficient duration → warning
        steps = specialist_output.get("steps")
        if steps is not None:
            try:
                steps_val = int(steps)
            except (TypeError, ValueError):
                steps_val = None
            if steps_val is not None and steps_val < 100:
                return {
                    "error_code": None,
                    "critique_type": "methodology",
                    "severity": "warning",
                    "detail": (
                        f"Simulation ran only {steps_val} steps, below the 100-step "
                        "minimum required for trajectory quality assessment. Short "
                        "trajectories do not cover sufficient state space for "
                        "CMA-ES fitness evaluation or contact force characterisation."
                    ),
                    "evidence": (
                        "MuJoCo Simulation SKILL.md: trajectory must be ≥ 100 steps "
                        "minimum (MVP gate)."
                    ),
                    "confidence_delta": -0.2,
                }

        # Default: info on sim-to-real gap
        return {
            "error_code": None,
            "critique_type": "methodology",
            "severity": "info",
            "detail": (
                "Simulation trajectory meets basic determinism and duration requirements. "
                "Sim-to-real gap has not been quantified in this output. Domain "
                "randomisation (DR) perturbation ranges are not verified here. "
                "Contact model parameters (solimp/solref) should be validated against "
                "measured PAM contact behaviour before handoff to CMA-ES."
            ),
            "evidence": (
                "MuJoCo Simulation SKILL.md: sim-to-real gap quantification is "
                "a Level 3 (V1) capability. DR configuration required for CMA-ES input."
            ),
            "confidence_delta": -0.05,
        }
