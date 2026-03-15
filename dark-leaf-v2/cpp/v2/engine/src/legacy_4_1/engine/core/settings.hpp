#pragma once
/*
================================================================================
Legacy 4-1 Engine Core — Evaluation Settings
FILE: engine/core/settings.hpp
================================================================================
*/

#include "engine/core/errors.hpp"

namespace lift {

struct AtmosphereSettings {
    double rho_kg_m3 = 1.225;   // Air density [kg/m³] — ISA SL default
};

struct RotorSettings {
    double hover_FM  = 0.70;    // Figure of merit ∈ (0, 1]
    double induced_k = 1.15;    // Induced power correction factor ≥ 1.0
};

struct EvalSettings {
    AtmosphereSettings atmosphere;
    RotorSettings      rotor;

    void validate_or_throw() const {
        if (!(atmosphere.rho_kg_m3 > 0.0))
            throw ValidationError("EvalSettings: rho_kg_m3 must be > 0");
        if (!(rotor.hover_FM > 0.0 && rotor.hover_FM <= 1.0))
            throw ValidationError("EvalSettings: hover_FM must be in (0, 1]");
        if (!(rotor.induced_k >= 1.0))
            throw ValidationError("EvalSettings: induced_k must be >= 1.0");
    }
};

} // namespace lift
