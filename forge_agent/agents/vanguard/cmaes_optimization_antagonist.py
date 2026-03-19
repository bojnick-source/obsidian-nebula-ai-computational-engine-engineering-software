"""CMA-ES Optimization Antagonist agent for the Void Vanguard project."""
from __future__ import annotations

from forge_agent.agents.antagonist_base import AntagonistAgent


class CMAESOptimizationAntagonist(AntagonistAgent):
    """Antagonist that validates CVaR gate passage and convergence quality."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="cmaes_optimization_antagonist",
            domain="cmaes_opt",
        )

    def _generate_critique(
        self,
        specialist_output: dict,
        context: dict,
    ) -> dict:
        _ = context  # consumed (P2)

        # AC 4: CVaR gate failed → fatal
        cvar_pass = specialist_output.get("cvar_pass")
        if cvar_pass is False:
            cvar_005 = specialist_output.get("cvar_005", "unknown")
            return {
                "error_code": None,
                "critique_type": "methodology",
                "severity": "fatal",
                "detail": (
                    f"CVaR gate FAILED (cvar_005={cvar_005}). The optimised parameter "
                    "set does not meet the 5th-percentile tracking error threshold of "
                    "8.0 degrees. This parameter set must not be used for actuator "
                    "control — it will fail under robustness test conditions. "
                    "Re-run with increased n_mc, adjusted cvar_threshold, or wider "
                    "parameter bounds."
                ),
                "evidence": (
                    "CMA-ES Optimization SKILL.md: cvar_pass=True is a mandatory gate "
                    "before parameter handoff to MuJoCo sim or hardware. "
                    "CVaR α=0.05, threshold=8.0 deg (Void Vanguard project spec)."
                ),
                "confidence_delta": -0.7,
            }

        # AC 5: stagnation → warning
        stagnation = specialist_output.get("stagnation")
        if stagnation is True:
            sigma_final = specialist_output.get("sigma_final", "unknown")
            sigma0 = specialist_output.get("sigma0", "unknown")
            return {
                "error_code": None,
                "critique_type": "methodology",
                "severity": "warning",
                "detail": (
                    f"CMA-ES stagnated (sigma_final={sigma_final}, sigma0={sigma0}). "
                    "The algorithm converged to a small sigma without meaningful "
                    "fitness improvement — a restart with a different x0 or larger "
                    "sigma0 is recommended. Stagnation can indicate a flat fitness "
                    "landscape, infeasible parameter bounds, or local minimum trapping."
                ),
                "evidence": (
                    "CMA-ES Optimization SKILL.md: stagnation detection flag. "
                    "Hansen (2016) — The CMA Evolution Strategy: a tutorial. "
                    "Stagnation criterion: sigma_k < stagnation_tol * sigma0."
                ),
                "confidence_delta": -0.25,
            }

        # Default: info
        return {
            "error_code": None,
            "critique_type": "methodology",
            "severity": "info",
            "detail": (
                "CMA-ES optimisation passed CVaR and convergence gates. "
                "Convergence curve quality was not inspected in this critique pass — "
                "verify that sigma_final/sigma0 < 0.01 for tight convergence. "
                "n_mc adequacy (≥ 500 samples) was assumed but not verified here."
            ),
            "evidence": (
                "Hansen (2016) — The CMA Evolution Strategy: a tutorial. "
                "CMA-ES Optimization SKILL.md convergence criteria."
            ),
            "confidence_delta": -0.05,
        }
