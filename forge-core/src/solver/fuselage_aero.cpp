/**
 * @file fuselage_aero.cpp
 * @brief Hoerner fuselage drag implementation (float64, deterministic).
 *
 * See: forge-core/include/forge/solver/fuselage_aero.hpp
 */

#include "forge/solver/fuselage_aero.hpp"
#include "forge/common/result.hpp"

#include <cmath>

namespace forge::solver {

// ── ISA density ───────────────────────────────────────────────────────────────

forge::common::Result<double> isa_density(double altitude_m) noexcept {
    constexpr double kMaxAlt = 86000.0;  // ICAO standard atmosphere limit [m]
    if (altitude_m > kMaxAlt) {
        return forge::common::Result<double>::err({
            "ERR_ALTITUDE_OUT_OF_RANGE",
            "Altitude above 86 km is outside the supported ISA model"
        });
    }

    double temperature_k = 0.0;
    double pressure_pa   = 0.0;

    if (altitude_m <= kIsaTropo) {
        temperature_k = kIsaT0K - kIsaLapse * altitude_m;
        const double exp = kIsaG0 / (kIsaLapse * kIsaR);
        pressure_pa = kIsaP0Pa * std::pow(temperature_k / kIsaT0K, exp);
    } else {
        // Tropopause boundary values
        const double t_trop = kIsaT0K - kIsaLapse * kIsaTropo;
        const double exp_trop = kIsaG0 / (kIsaLapse * kIsaR);
        const double p_trop = kIsaP0Pa * std::pow(t_trop / kIsaT0K, exp_trop);
        temperature_k = kIsaStratT;
        pressure_pa   = p_trop * std::exp(
            -kIsaG0 * (altitude_m - kIsaTropo) / (kIsaR * kIsaStratT)
        );
    }

    const double density = pressure_pa / (kIsaR * temperature_k);
    return forge::common::Result<double>::ok(density);
}

// ── Skin friction coefficient ─────────────────────────────────────────────────

forge::common::Result<double> flat_plate_cf(double reynolds) noexcept {
    if (reynolds <= 0.0) {
        return forge::common::Result<double>::err({
            "ERR_INVALID_INPUT", "Reynolds number must be positive"
        });
    }
    double cf = 0.0;
    if (reynolds <= 1.0e5) {
        // Blasius laminar
        cf = 1.328 / std::sqrt(reynolds);
    } else {
        // Prandtl-Schlichting turbulent
        const double log10_re = std::log10(reynolds);
        cf = 0.455 / std::pow(log10_re, 2.58);
    }
    return forge::common::Result<double>::ok(cf);
}

// ── Hoerner drag computation ──────────────────────────────────────────────────

forge::common::Result<FuselageDrag>
compute_drag(const FuselageParams& fus, const AeroCondition& cond) noexcept {
    if (cond.speed_ms <= 0.0) {
        return forge::common::Result<FuselageDrag>::err({
            "ERR_INVALID_INPUT", "speed_ms must be positive"
        });
    }
    if (fus.length_m <= 0.0 || fus.max_diameter_m <= 0.0) {
        return forge::common::Result<FuselageDrag>::err({
            "ERR_INVALID_INPUT", "Fuselage dimensions must be positive"
        });
    }

    const double q  = 0.5 * cond.air_density_kg_m3 * cond.speed_ms * cond.speed_ms;
    const double re = cond.speed_ms * fus.length_m / cond.kinematic_viscosity;

    auto cf_result = flat_plate_cf(re);
    if (!cf_result) return forge::common::Result<FuselageDrag>::err(cf_result.error());
    const double cf = cf_result.value();

    // Skin friction drag
    const double d_friction = cf * fus.wetted_area_m2 * q;

    // Form drag (Hoerner): Cd_form = kH * (d/l)^3 referenced to max cross-section
    const double d_over_l  = fus.max_diameter_m / fus.length_m;
    const double cd_form   = kHoernerK * d_over_l * d_over_l * d_over_l;
    const double d_form    = cd_form * fus.cross_section_area_m2 * q;

    // Interference allowance
    const double d_interf  = kInterferenceF * (d_friction + d_form);

    const double total     = d_friction + d_form + d_interf;
    const double cd_body   = (q * fus.cross_section_area_m2 > 0.0)
                             ? total / (q * fus.cross_section_area_m2)
                             : 0.0;

    return forge::common::Result<FuselageDrag>::ok({
        d_friction,
        d_form,
        d_interf,
        total,
        cd_body,
        re
    });
}

}  // namespace forge::solver
