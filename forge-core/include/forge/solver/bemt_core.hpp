#pragma once

/**
 * @file bemt_core.hpp
 * @brief Deterministic float64 BEMT inflow iteration solver.
 *
 * Implements the Blade Element Momentum Theory inner iteration loop that
 * finds the induced inflow ratio λ matching momentum-theory and blade-element-
 * theory predictions at each radial station.
 *
 * Design policy (FORGE polyglot accuracy layer):
 *   - All arithmetic is double (float64).
 *   - Convergence controlled by named constants (no magic numbers).
 *   - Returns forge::common::Result<T> — no exceptions.
 *   - Thread-safe (no static mutable state).
 *
 * Python counterpart: forge-solver/src/forge_solver/bemt.py
 */

#include "forge/common/result.hpp"

#include <cstddef>
#include <span>
#include <vector>

namespace forge::solver {

// ── Solver parameters ─────────────────────────────────────────────────────────

inline constexpr int    kBemtMaxIter   = 200;
inline constexpr double kBemtTolerance = 1.0e-6;  ///< Inflow ratio convergence
inline constexpr double kBemtRelax     = 0.5;      ///< Under-relaxation factor
inline constexpr double kBemtMinLambda = 1.0e-4;  ///< Inflow ratio lower clamp
inline constexpr double kBemtMaxLambda = 1.0;      ///< Inflow ratio upper clamp

// ── Input types ───────────────────────────────────────────────────────────────

/// Geometric and aerodynamic properties of one radial blade station.
struct BladeStationParams {
    double radius_m;       ///< Radial position [m]
    double chord_m;        ///< Chord length [m]
    double twist_rad;      ///< Local geometric pitch angle [rad]
    double cl_alpha;       ///< Lift-curve slope [1/rad]
    double cd0;            ///< Zero-lift parasitic drag coefficient
};

/// Operating condition for the BEMT solve.
struct BemtCondition {
    double omega_rad_s;          ///< Angular velocity [rad/s]
    double climb_speed_ms;       ///< Axial (freestream/climb) speed [m/s]; 0 = hover
    double air_density_kg_m3;    ///< Air density [kg/m³]
    double tip_radius_m;         ///< Rotor tip radius [m] (for normalisation)
    int    n_blades;             ///< Number of blades
};

// ── Output types ─────────────────────────────────────────────────────────────

/// Result at one radial station.
struct StationResult {
    double radius_m;
    double inflow_ratio;       ///< λ = (v_c + v_i) / (Ω·R)
    double inflow_angle_rad;   ///< φ = atan2(up, ut)
    double alpha_rad;          ///< Angle of attack = twist - φ
    double cl;                 ///< Lift coefficient
    double cd;                 ///< Drag coefficient
    double d_thrust_n;         ///< Element thrust contribution [N]
    double d_torque_nm;        ///< Element torque contribution [N·m]
    bool   converged;          ///< True if iteration converged within kBemtMaxIter
};

/// Integrated rotor performance.
struct RotorPerformance {
    double total_thrust_n;
    double total_torque_nm;
    double total_power_w;
    double ct;               ///< Thrust coefficient
    double cq;               ///< Torque coefficient
    double cp;               ///< Power coefficient
    double figure_of_merit;  ///< FM = P_ideal / P_actual (hover)
    double disk_loading_pa;  ///< T / A_disk [Pa]
    bool   all_converged;    ///< True if all stations converged
};

// ── Element-level solver ──────────────────────────────────────────────────────

/**
 * @brief Solve the inflow ratio for one blade station.
 *
 * Iterates the OGE (Out-of-Ground-Effect) BEMT equations:
 *   momentum:      T' = 4·ρ·π·r·dr·(Ω·R)·λ·(λ + v_c/(Ω·R))
 *   blade element: T' = (1/2)·ρ·(Ω·r)²·c·(Cl·cos(φ) - Cd·sin(φ))·dr·B
 *
 * @param station   Blade station geometry and aerodynamic properties.
 * @param cond      Operating condition.
 * @param dr        Element radial width [m].
 * @return StationResult, or error if inputs are invalid.
 */
[[nodiscard]] forge::common::Result<StationResult>
solve_station(
    const BladeStationParams& station,
    const BemtCondition& cond,
    double dr
) noexcept;

// ── Full rotor solver ─────────────────────────────────────────────────────────

/**
 * @brief Solve BEMT for all blade stations and integrate rotor performance.
 *
 * Calls solve_station() on each element independently and sums contributions.
 *
 * @param stations  Radial blade stations (ordered root → tip).
 * @param cond      Operating condition.
 * @return RotorPerformance, or error if any station input is invalid.
 */
[[nodiscard]] forge::common::Result<RotorPerformance>
solve_rotor(
    std::span<const BladeStationParams> stations,
    const BemtCondition& cond
);

}  // namespace forge::solver
