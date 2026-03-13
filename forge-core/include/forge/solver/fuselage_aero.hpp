#pragma once

/**
 * @file fuselage_aero.hpp
 * @brief Deterministic float64 fuselage aerodynamic drag solver.
 *
 * Implements the Hoerner body drag method for axisymmetric fuselages:
 *   - Turbulent/laminar flat-plate skin friction (Prandtl-Schlichting)
 *   - Hoerner form drag: Cd_form = k·(d/l)³
 *   - Interference allowance (10% of skin + form)
 *
 * All arithmetic is float64; ISA atmosphere constants are declared inline.
 *
 * Design policy (FORGE polyglot accuracy layer):
 *   - No exceptions — errors returned as forge::common::Result<T>.
 *   - [[nodiscard]] on all pure computation functions.
 *   - No static mutable state.
 *
 * Python counterpart: forge-solver/src/forge_solver/smart_fuselage.py
 */

#include "forge/common/result.hpp"

namespace forge::solver {

// ── Physical constants (ISA sea level) ───────────────────────────────────────

inline constexpr double kIsaT0K      = 288.15;       ///< Sea-level temperature [K]
inline constexpr double kIsaP0Pa     = 101325.0;     ///< Sea-level pressure [Pa]
inline constexpr double kIsaRho0     = 1.225;        ///< Sea-level density [kg/m³]
inline constexpr double kIsaLapse    = 0.0065;       ///< Lapse rate [K/m]
inline constexpr double kIsaG0       = 9.80665;      ///< Standard gravity [m/s²]
inline constexpr double kIsaR        = 287.058;      ///< Specific gas constant [J/(kg·K)]
inline constexpr double kIsaTropo    = 11000.0;      ///< Tropopause altitude [m]
inline constexpr double kIsaStratT   = 216.65;       ///< Stratosphere temperature [K]
inline constexpr double kKinVisc     = 1.5e-5;       ///< Kinematic viscosity ISA SL [m²/s]

// ── Aerodynamic constants ─────────────────────────────────────────────────────

inline constexpr double kHoernerK    = 2.3;          ///< Hoerner fuselage form factor
inline constexpr double kInterferenceF = 0.10;       ///< Interference drag fraction

// ── Input / output types ──────────────────────────────────────────────────────

/// Fuselage geometry parameters (body of revolution, circular cross-section).
struct FuselageParams {
    double length_m;              ///< Total fuselage length [m]
    double max_diameter_m;        ///< Maximum diameter [m]
    double wetted_area_m2;        ///< Pre-computed wetted area [m²]
    double cross_section_area_m2; ///< Max cross-sectional area [m²]
};

/// Atmospheric state (density only needed for drag; pre-computed externally).
struct AeroCondition {
    double speed_ms;              ///< True airspeed [m/s]
    double air_density_kg_m3;     ///< Air density [kg/m³]
    double kinematic_viscosity;   ///< Kinematic viscosity [m²/s] (use kKinVisc if unsure)
};

/// Drag breakdown for a fuselage.
struct FuselageDrag {
    double friction_drag_n;       ///< Skin friction drag [N]
    double form_drag_n;           ///< Pressure/form drag [N]
    double interference_drag_n;   ///< Interference allowance [N]
    double total_drag_n;          ///< Sum of all drag components [N]
    double cd_body;               ///< Body drag coefficient (ref: max cross-section)
    double reynolds_number;       ///< Re = V·l / ν
};

// ── ISA atmosphere ────────────────────────────────────────────────────────────

/**
 * @brief Compute ISA air density at *altitude_m* above MSL.
 *
 * Troposphere (h ≤ 11 km): T = T0 - L·h, ρ from ideal gas.
 * Stratosphere (h > 11 km): isothermal at 216.65 K.
 *
 * @return Air density [kg/m³], or error if altitude is out of supported range.
 */
[[nodiscard]] forge::common::Result<double>
isa_density(double altitude_m) noexcept;

// ── Drag computation ──────────────────────────────────────────────────────────

/**
 * @brief Skin friction coefficient via Prandtl-Schlichting turbulent formula.
 *
 * Cf = 0.455 / (log10(Re))^2.58  for Re > 1e5
 * Cf = 1.328 / sqrt(Re)           for Re <= 1e5 (Blasius laminar)
 *
 * @param reynolds  Reynolds number (must be > 0).
 * @return Cf, or error if Re <= 0.
 */
[[nodiscard]] forge::common::Result<double>
flat_plate_cf(double reynolds) noexcept;

/**
 * @brief Compute Hoerner fuselage drag breakdown.
 *
 * @param fus   Fuselage geometry (lengths, areas).
 * @param cond  Flight condition (speed, density, viscosity).
 * @return FuselageDrag with full breakdown, or error on invalid inputs.
 */
[[nodiscard]] forge::common::Result<FuselageDrag>
compute_drag(const FuselageParams& fus, const AeroCondition& cond) noexcept;

}  // namespace forge::solver
