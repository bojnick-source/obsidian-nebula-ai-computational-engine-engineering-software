"""FORGE Actuator Safety Antagonist — heuristic critique of safety analysis output."""
from forge_agent.agents.antagonist_base import AntagonistAgent

_MIN_SAFETY_FACTOR = 2.0
_REQUIRED_FAILURE_MODES = frozenset({"burst", "braid_failure", "fitting_leak"})


class ActuatorSafetyAntagonist(AntagonistAgent):
    """Antagonist that validates actuator safety analysis output.

    Heuristic paths (in priority order):
    1. safety_factor missing → fatal
    2. safety_factor < 2.0 → fatal
    3. burst_pressure_kPa absent → warning
    4. All primary checks pass → info
    """

    def __init__(self) -> None:
        super().__init__(
            agent_id="actuator_safety_antagonist",
            domain="actuator_safety",
        )

    def _generate_critique(
        self,
        specialist_output: dict,
        context: dict,
    ) -> dict:
        _ = context  # consumed (P2 guard)

        safety_factor = specialist_output.get("safety_factor")

        if safety_factor is None:
            # AC3: missing safety_factor entirely → fatal
            return {
                "error_code": None,
                "critique_type": "provenance",
                "severity": "fatal",
                "detail": (
                    "No safety_factor was present in the specialist output. "
                    "A safety analysis without a computed safety factor is incomplete "
                    "and cannot be approved. The safety factor (burst_pressure / "
                    "max_operating_pressure) must be explicitly calculated and "
                    "compared against the 2.0 minimum threshold."
                ),
                "evidence": (
                    "Actuator Safety SKILL.md: safety_factor is a mandatory output field."
                ),
                "confidence_delta": -0.8,
            }

        try:
            sf_val = float(safety_factor)
        except (TypeError, ValueError):
            sf_val = None

        if sf_val is not None and sf_val < _MIN_SAFETY_FACTOR:
            # AC4: safety_factor < 2.0 → fatal
            return {
                "error_code": None,
                "critique_type": "dimensional",
                "severity": "fatal",
                "detail": (
                    f"Safety factor {sf_val:.2f} is below the mandatory minimum "
                    f"of {_MIN_SAFETY_FACTOR:.1f} for McKibben PAM pressure systems. "
                    "This design MUST NOT be used in hardware experiments. "
                    "A safety factor below 2.0 provides insufficient margin against "
                    "burst failure from manufacturing variation, pressure spike, or "
                    "connector fatigue. Redesign or re-rate the operating pressure."
                ),
                "evidence": (
                    "Void Vanguard project requirement: safety factor ≥ 2.0. "
                    "ISO 1402:2009 — hydraulic fluid power hoses: 3× burst/working. "
                    "Actuator Safety SKILL.md: safety_factor ≥ 2.0 is a hard gate."
                ),
                "confidence_delta": -0.8,
            }

        # AC5: safety_factor ≥ 2.0 but burst_pressure_kPa absent → warning
        if "burst_pressure_kPa" not in specialist_output:
            return {
                "error_code": None,
                "critique_type": "provenance",
                "severity": "warning",
                "detail": (
                    "burst_pressure_kPa is absent from the safety analysis output. "
                    "Without the measured or specified burst pressure, the safety factor "
                    "cannot be independently verified. Burst pressure must be stated "
                    "with its source (physical test, manufacturer datasheet, or standard)."
                ),
                "evidence": (
                    "Actuator Safety SKILL.md: burst_pressure_kPa is a mandatory "
                    "output field for pressure system safety analysis."
                ),
                "confidence_delta": -0.3,
            }

        # AC6: primary checks passed → info (check failure mode coverage)
        failure_modes = specialist_output.get("failure_modes", [])
        if isinstance(failure_modes, list):
            modes_set = {str(m).lower() for m in failure_modes}
        else:
            modes_set = set()
        missing_modes = _REQUIRED_FAILURE_MODES - modes_set
        if missing_modes:
            missing_str = ", ".join(sorted(missing_modes))
            detail = (
                f"Safety analysis passed primary thresholds. However, "
                f"the following required failure modes were not enumerated: "
                f"{missing_str}. Complete failure mode analysis is required "
                f"before hardware approval."
            )
        else:
            detail = (
                "Safety analysis passed all primary checks: safety_factor ≥ 2.0, "
                "burst_pressure present, core failure modes enumerated. "
                "Connector fatigue life and pressure spike analysis were not "
                "verified in this critique pass."
            )
        return {
            "error_code": None,
            "critique_type": "methodology",
            "severity": "info",
            "detail": detail,
            "evidence": (
                "Actuator Safety SKILL.md acceptance criteria. "
                "Void Vanguard actuator safety gate requirements."
            ),
            "confidence_delta": -0.05,
        }
