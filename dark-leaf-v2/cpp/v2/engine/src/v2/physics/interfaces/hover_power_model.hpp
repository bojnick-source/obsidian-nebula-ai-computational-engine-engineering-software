#pragma once
/*
================================================================================
v2 Physics Interfaces — Hover Power Model
FILE: v2/physics/interfaces/hover_power_model.hpp

Purpose:
  - Abstract base class for hover power computation
  - Shared POD structs: AtmosphereConditions, RotorPerformance, HoverPowerResult
================================================================================
*/

#include <stdexcept>

namespace v2::physics {

// ---------------------------------------------------------------------------
// Input PODs
// ---------------------------------------------------------------------------

struct AtmosphereConditions {
    double rho_kg_m3 = 1.225;   // Air density [kg/m³] — ISA SL default
};

struct RotorPerformance {
    double hover_FM    = 0.70;  // Figure of merit ∈ (0, 1]
    double induced_k   = 1.15;  // Induced power correction factor ≥ 1.0
};

// ---------------------------------------------------------------------------
// Output POD
// ---------------------------------------------------------------------------

struct HoverPowerResult {
    double thrust_N               = 0.0;
    double A_total_m2             = 0.0;
    double rho_used_kg_m3         = 0.0;
    double FM_used                = 0.0;
    double disk_loading_N_per_m2  = 0.0;
    double P_induced_ideal_W      = 0.0;
    double P_induced_W            = 0.0;
    double P_total_W              = 0.0;
};

// ---------------------------------------------------------------------------
// Abstract interface
// ---------------------------------------------------------------------------

class HoverPowerModel {
public:
    virtual ~HoverPowerModel() = default;

    virtual HoverPowerResult compute_power(
        double thrust_N,
        double A_total_m2,
        const AtmosphereConditions& atmosphere,
        const RotorPerformance& rotor_perf) const = 0;

    virtual HoverPowerResult compute_power_sized(
        double thrust_N,
        double A_total_m2,
        const AtmosphereConditions& atmosphere,
        const RotorPerformance& rotor_perf,
        double reserve_mult) const = 0;
};

} // namespace v2::physics
