/**
 * @file bemt_core.cpp
 * @brief Deterministic float64 BEMT inflow iteration solver implementation.
 *
 * See: forge-core/include/forge/solver/bemt_core.hpp
 */

#include "forge/solver/bemt_core.hpp"
#include "forge/common/result.hpp"

#include <algorithm>
#include <cmath>
#include <numbers>

namespace forge::solver {

// ── Element inflow solver ─────────────────────────────────────────────────────

forge::common::Result<StationResult>
solve_station(
    const BladeStationParams& station,
    const BemtCondition& cond,
    double dr
) noexcept {
    // Input validation
    if (station.radius_m <= 0.0)
        return forge::common::Result<StationResult>::err({"ERR_INVALID_INPUT", "radius_m must be > 0"});
    if (station.chord_m <= 0.0)
        return forge::common::Result<StationResult>::err({"ERR_INVALID_INPUT", "chord_m must be > 0"});
    if (cond.air_density_kg_m3 <= 0.0)
        return forge::common::Result<StationResult>::err({"ERR_INVALID_INPUT", "air_density must be > 0"});
    if (cond.tip_radius_m <= 0.0)
        return forge::common::Result<StationResult>::err({"ERR_INVALID_INPUT", "tip_radius_m must be > 0"});

    const double omega   = cond.omega_rad_s;
    const double v_c     = cond.climb_speed_ms;
    const double rho     = cond.air_density_kg_m3;
    const double r       = station.radius_m;
    const double r_tip   = cond.tip_radius_m;
    const int    b       = cond.n_blades;

    // Local solidity
    const double sigma_r = static_cast<double>(b) * station.chord_m
                           / (std::numbers::pi * r);

    // Initial inflow ratio guess from simplified momentum theory
    double lam = std::max(
        kBemtMinLambda,
        std::sqrt(sigma_r * station.cl_alpha / 16.0) - v_c / (omega * r_tip)
    );

    bool converged = false;
    for (int iter = 0; iter < kBemtMaxIter; ++iter) {
        const double ut = omega * r;
        const double up = omega * r_tip * lam + v_c;
        const double phi = std::atan2(up, ut);  // inflow angle

        const double alpha = station.twist_rad - phi;
        const double cl    = station.cl_alpha * alpha;

        // New inflow ratio from blade-element/momentum balance
        const double v_tip = omega * r_tip;
        const double lam_new = std::clamp(
            std::sqrt(std::max(
                0.0,
                (sigma_r * station.cl_alpha / 8.0) * alpha - v_c / (2.0 * v_tip)
            )),
            kBemtMinLambda,
            kBemtMaxLambda
        );

        const double delta = lam_new - lam;
        lam += kBemtRelax * delta;

        if (std::abs(delta) < kBemtTolerance) {
            converged = true;
            break;
        }
    }

    // Final aerodynamic loads
    const double ut      = omega * r;
    const double up      = omega * r_tip * lam + v_c;
    const double v_tot   = std::sqrt(ut * ut + up * up);
    const double phi     = std::atan2(up, ut);
    const double alpha   = station.twist_rad - phi;
    const double cl      = station.cl_alpha * alpha;
    const double cd      = station.cd0 + 0.01 * cl * cl;  // quadratic drag polar

    // Element thrust and torque (all blades combined)
    const double dL = 0.5 * rho * v_tot * v_tot * station.chord_m * cl * dr;
    const double dD = 0.5 * rho * v_tot * v_tot * station.chord_m * cd * dr;

    const double d_thrust = static_cast<double>(b)
                            * (dL * std::cos(phi) - dD * std::sin(phi));
    const double d_torque = static_cast<double>(b) * r
                            * (dD * std::cos(phi) + dL * std::sin(phi));

    return forge::common::Result<StationResult>::ok({
        r,
        lam,
        phi,
        alpha,
        cl,
        cd,
        d_thrust,
        d_torque,
        converged
    });
}

// ── Full rotor solver ─────────────────────────────────────────────────────────

forge::common::Result<RotorPerformance>
solve_rotor(
    std::span<const BladeStationParams> stations,
    const BemtCondition& cond
) {
    if (stations.empty()) {
        return forge::common::Result<RotorPerformance>::err({"ERR_EMPTY_MESH", "No blade stations provided"});
    }

    const double r_tip      = cond.tip_radius_m;
    const double r_hub      = stations.front().radius_m;
    const double dr         = (r_tip - r_hub) / static_cast<double>(stations.size());
    const double disk_area  = std::numbers::pi * r_tip * r_tip;
    const double v_tip      = cond.omega_rad_s * r_tip;
    const double rho        = cond.air_density_kg_m3;

    double total_thrust = 0.0;
    double total_torque = 0.0;
    bool   all_converged = true;

    for (const auto& station : stations) {
        auto res = solve_station(station, cond, dr);
        if (!res) return forge::common::Result<RotorPerformance>::err(res.error());

        const auto& s = res.value();
        total_thrust  += s.d_thrust_n;
        total_torque  += s.d_torque_nm;
        all_converged = all_converged && s.converged;
    }

    const double total_power = total_torque * cond.omega_rad_s;

    const double denom_ct = rho * disk_area * v_tip * v_tip;
    const double denom_cp = rho * disk_area * v_tip * v_tip * v_tip;

    const double ct = denom_ct > 0.0 ? total_thrust / denom_ct : 0.0;
    const double cp = denom_cp > 0.0 ? total_power  / denom_cp : 0.0;
    const double cq = denom_ct > 0.0
                      ? total_torque / (rho * disk_area * r_tip * v_tip * v_tip)
                      : 0.0;

    double fm = 0.0;
    if (total_power > 0.0 && total_thrust > 0.0) {
        const double p_ideal = total_thrust
                               * std::sqrt(total_thrust / (2.0 * rho * disk_area));
        fm = p_ideal / total_power;
    }

    const double disk_loading = disk_area > 0.0 ? total_thrust / disk_area : 0.0;

    return forge::common::Result<RotorPerformance>::ok({
        total_thrust,
        total_torque,
        total_power,
        ct, cq, cp,
        fm,
        disk_loading,
        all_converged
    });
}

}  // namespace forge::solver
