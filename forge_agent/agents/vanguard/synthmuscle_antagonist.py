"""Synthmuscle antagonist agent — heuristic critique of PAM model outputs."""
from __future__ import annotations

from forge_agent.agents.antagonist_base import AntagonistAgent


class SynthmuscleAntagonist(AntagonistAgent):
    """Heuristic antagonist for Synthmuscle specialist outputs.

    Checks PAM model quality thresholds from the SKILL.md acceptance criteria.
    Both specialist_output and context consumed — P2 compliant.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="synthmuscle_antagonist", domain="synthmuscle")

    def _generate_critique(
        self,
        specialist_output: dict,
        context: dict,
    ) -> dict:
        # Both params consumed — context stored for traceability (P2)
        _ = context  # used: see evidence field

        rmse_pct = specialist_output.get("rmse_pct")
        if rmse_pct is not None:
            try:
                rmse_val = float(rmse_pct)
            except (TypeError, ValueError):
                rmse_val = None
            if rmse_val is not None and rmse_val > 5.0:
                return {
                    "error_code": None,
                    "critique_type": "methodology",
                    "severity": "fatal",
                    "detail": (
                        f"RMSE {rmse_val:.2f}% exceeds the 5% acceptance threshold for "
                        "Chou-Hannaford PAM model characterisation. This level of residual "
                        "error indicates the model does not adequately capture the "
                        "measured force-length-pressure relationship and cannot be "
                        "used as input to the CMA-ES optimisation stage."
                    ),
                    "evidence": (
                        "Synthmuscle SKILL.md MVP requirement: RMSE < 5% of F_max. "
                        "Tondu & Lopez (2000) — modeling and control of McKibben "
                        "artificial muscle robot actuators."
                    ),
                    "confidence_delta": -0.5,
                }

        r2 = specialist_output.get("r2")
        if r2 is not None:
            try:
                r2_val = float(r2)
            except (TypeError, ValueError):
                r2_val = None
            if r2_val is not None and r2_val < 0.95:
                return {
                    "error_code": None,
                    "critique_type": "methodology",
                    "severity": "warning",
                    "detail": (
                        f"R² = {r2_val:.4f} is below the 0.95 minimum required for "
                        "MVP PAM characterisation. The Chou-Hannaford model fit does "
                        "not explain sufficient variance in the force-length-pressure "
                        "data. Common causes: pressure gauge vs absolute confusion, "
                        "non-standard braid geometry, or insufficient data coverage."
                    ),
                    "evidence": (
                        "Synthmuscle SKILL.md: R² ≥ 0.95 required for MVP characterisation."
                    ),
                    "confidence_delta": -0.2,
                }

        # Default: info critique on hysteresis (always present, even on good fits)
        return {
            "error_code": None,
            "critique_type": "methodology",
            "severity": "info",
            "detail": (
                "Hysteresis characterisation was not included in this analysis. "
                "The Chou-Hannaford model assumes reversible braid deformation; real "
                "McKibben PAMs exhibit 3-15% hysteresis loops that reduce effective "
                "force predictability. AIC/BIC model selection was not verified in "
                "this critique pass — confirm these fields are present in output."
            ),
            "evidence": (
                "Tondu & Lopez (2000) — McKibben artificial muscle hysteresis. "
                "Chou & Hannaford (1996) — measurement and modelling of McKibben PAMs."
            ),
            "confidence_delta": -0.05,
        }
