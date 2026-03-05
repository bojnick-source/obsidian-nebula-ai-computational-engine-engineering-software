"""Engineering Constitution automated gate checks.

All checks are deterministic Python — never run inside an LLM debate.
Tier 1 (Math) and Tier 2 (Physics) violations halt the run.
Tier 3 (Engineering code) violations raise warnings.
Tier 4 (Best practice) violations are logged only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class ConstitutionGateResult:
    gate: str
    tier: int
    passed: bool
    message: str
    values: dict[str, Any]


@dataclass
class SingularityWarning:
    location: str
    max_stress_mpa: float
    element_count_at_peak: int


# ─────────────────────────────────────────────────────────────────────────────
# Tier 1: Math — inviolable
# ─────────────────────────────────────────────────────────────────────────────

def check_reaction_equilibrium(
    result: dict[str, Any],
    applied_loads: dict[str, float],
    tolerance_pct: float = 1.0,
) -> ConstitutionGateResult:
    """Verify that sum of reaction forces balances applied loads (Newton's 3rd law)."""
    reaction_forces = result.get("reaction_forces", {})
    total_applied = sum(abs(v) for v in applied_loads.values())
    total_reaction = sum(abs(v) for v in reaction_forces.values())

    if total_applied == 0:
        return ConstitutionGateResult(
            gate="reaction_equilibrium",
            tier=1,
            passed=True,
            message="No applied loads — equilibrium trivially satisfied",
            values={"total_applied": 0, "total_reaction": total_reaction},
        )

    error_pct = abs(total_reaction - total_applied) / total_applied * 100
    passed = error_pct <= tolerance_pct
    return ConstitutionGateResult(
        gate="reaction_equilibrium",
        tier=1,
        passed=passed,
        message=(
            f"Equilibrium error {error_pct:.2f}% ({'OK' if passed else 'VIOLATION'})"
        ),
        values={
            "total_applied_n": total_applied,
            "total_reaction_n": total_reaction,
            "error_pct": error_pct,
            "tolerance_pct": tolerance_pct,
        },
    )


def check_energy_balance(
    result: dict[str, Any],
    tolerance_pct: float = 5.0,
) -> ConstitutionGateResult:
    """Verify strain energy ≤ work done by applied loads (energy cannot be created)."""
    strain_energy = result.get("strain_energy_j", None)
    external_work = result.get("external_work_j", None)

    if strain_energy is None or external_work is None:
        return ConstitutionGateResult(
            gate="energy_balance",
            tier=1,
            passed=True,
            message="Insufficient data — skipping energy balance check",
            values={},
        )

    # Strain energy should be ≤ external work (some energy may be dissipated)
    ratio = strain_energy / external_work if external_work > 0 else float("inf")
    passed = ratio <= (1.0 + tolerance_pct / 100)
    return ConstitutionGateResult(
        gate="energy_balance",
        tier=1,
        passed=passed,
        message=f"Strain energy ratio {ratio:.4f} ({'OK' if passed else 'VIOLATION — energy created'})",
        values={
            "strain_energy_j": strain_energy,
            "external_work_j": external_work,
            "ratio": ratio,
            "tolerance_pct": tolerance_pct,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tier 2: Physics — must not violate
# ─────────────────────────────────────────────────────────────────────────────

def check_mesh_convergence(
    coarse: float,
    medium: float,
    fine: float,
    qoi_field: str = "von_mises",
    target_gci_pct: float = 5.0,
) -> ConstitutionGateResult:
    """Richardson extrapolation / GCI for mesh convergence (ASME V&V 10).

    Assumes refinement ratio r = 2 between each level.
    """
    r = 2.0
    if medium == coarse:
        return ConstitutionGateResult(
            gate="mesh_convergence",
            tier=2,
            passed=False,
            message="Coarse and medium solutions identical — check mesh setup",
            values={},
        )

    p = math.log(abs(fine - medium) / abs(medium - coarse)) / math.log(r) if abs(medium - coarse) > 0 else 1.0
    f_exact = fine + (fine - medium) / (r**p - 1)
    gci = 1.25 * abs(fine - medium) / (abs(fine) * (r**p - 1)) * 100 if fine != 0 else 0

    passed = gci <= target_gci_pct
    return ConstitutionGateResult(
        gate="mesh_convergence",
        tier=2,
        passed=passed,
        message=f"GCI = {gci:.2f}% (target ≤ {target_gci_pct}%) — {'OK' if passed else 'REFINE MESH'}",
        values={
            "qoi_field": qoi_field,
            "coarse": coarse,
            "medium": medium,
            "fine": fine,
            "convergence_order_p": round(p, 3),
            "extrapolated_exact": round(f_exact, 6),
            "gci_pct": round(gci, 3),
        },
    )


def check_stress_singularity(
    result: dict[str, Any],
    singularity_threshold_mpa: float = 1000.0,
    min_element_count: int = 5,
) -> list[SingularityWarning]:
    """Detect potential stress singularities (unrealistically high local stress).

    Returns list of warnings (empty = no singularity detected).
    """
    warnings: list[SingularityWarning] = []
    high_stress_locations = result.get("high_stress_locations", [])
    for loc in high_stress_locations:
        stress = loc.get("max_stress_mpa", 0)
        elem_count = loc.get("element_count_at_peak", 999)
        if stress > singularity_threshold_mpa and elem_count < min_element_count:
            warnings.append(SingularityWarning(
                location=loc.get("location", "unknown"),
                max_stress_mpa=stress,
                element_count_at_peak=elem_count,
            ))
    return warnings


# ─────────────────────────────────────────────────────────────────────────────
# CFD-specific checks (Tier 2)
# ─────────────────────────────────────────────────────────────────────────────

def check_residual_convergence(
    log: dict[str, Any],
    threshold: float = 1e-4,
) -> ConstitutionGateResult:
    """Check that CFD residuals dropped below convergence threshold."""
    final_residual = log.get("final_residual", None)
    if final_residual is None:
        return ConstitutionGateResult(
            gate="residual_convergence",
            tier=2,
            passed=True,
            message="No residual data available",
            values={},
        )
    passed = final_residual <= threshold
    return ConstitutionGateResult(
        gate="residual_convergence",
        tier=2,
        passed=passed,
        message=f"Final residual {final_residual:.2e} (target ≤ {threshold:.2e})",
        values={"final_residual": final_residual, "threshold": threshold},
    )


def check_mass_conservation(
    log: dict[str, Any],
    tolerance_pct: float = 0.1,
) -> ConstitutionGateResult:
    """Check CFD mass conservation: inlet flux ≈ outlet flux."""
    inlet_flux = log.get("inlet_mass_flux_kg_s", None)
    outlet_flux = log.get("outlet_mass_flux_kg_s", None)
    if inlet_flux is None or outlet_flux is None:
        return ConstitutionGateResult(
            gate="mass_conservation",
            tier=2,
            passed=True,
            message="Flux data unavailable — skipping",
            values={},
        )
    error_pct = abs(inlet_flux - outlet_flux) / abs(inlet_flux) * 100 if inlet_flux != 0 else 0
    passed = error_pct <= tolerance_pct
    return ConstitutionGateResult(
        gate="mass_conservation",
        tier=2,
        passed=passed,
        message=f"Mass imbalance {error_pct:.4f}% ({'OK' if passed else 'VIOLATION'})",
        values={
            "inlet_flux": inlet_flux,
            "outlet_flux": outlet_flux,
            "imbalance_pct": error_pct,
        },
    )


def check_y_plus(
    result: dict[str, Any],
    wall_treatment: str = "standard",
) -> ConstitutionGateResult:
    """Check y+ value compatibility with turbulence model wall treatment.

    Standard wall functions: 30 ≤ y+ ≤ 300
    Enhanced/Low-Re:          y+ ≤ 1
    """
    y_plus = result.get("y_plus_max", None)
    if y_plus is None:
        return ConstitutionGateResult(
            gate="y_plus",
            tier=2,
            passed=True,
            message="No y+ data available",
            values={},
        )

    if wall_treatment == "low_re":
        passed = y_plus <= 1.0
        target = "y+ ≤ 1"
    else:
        passed = 30 <= y_plus <= 300
        target = "30 ≤ y+ ≤ 300"

    return ConstitutionGateResult(
        gate="y_plus",
        tier=2,
        passed=passed,
        message=f"y+ = {y_plus:.1f} (target: {target}) — {'OK' if passed else 'RECONSIDER MESH/MODEL'}",
        values={"y_plus_max": y_plus, "wall_treatment": wall_treatment},
    )
