#pragma once
/*
================================================================================
Legacy 4-1 Engine Core — Design Descriptor
FILE: engine/core/design.hpp
================================================================================
*/

#include "engine/core/errors.hpp"

namespace lift {

struct Design {
    double rotor_radius_m        = 0.0;  // Tip radius of one rotor [m]
    int    rotor_count           = 1;    // Total number of rotors
    bool   is_coaxial            = false;
    int    coax_pairs            = 0;    // Number of coaxial stacks (0 when not coaxial)
    bool   has_shroud            = false;
    double shroud_inner_radius_m = 0.0;  // Inlet radius used when has_shroud == true

    void validate_or_throw() const {
        if (!(rotor_radius_m > 0.0))
            throw ValidationError("Design: rotor_radius_m must be > 0");
        if (!(rotor_count > 0))
            throw ValidationError("Design: rotor_count must be > 0");
        if (is_coaxial && coax_pairs <= 0)
            throw ValidationError("Design: is_coaxial=true requires coax_pairs > 0");
        if (has_shroud && !(shroud_inner_radius_m > 0.0))
            throw ValidationError("Design: shroud_inner_radius_m must be > 0 when has_shroud");
    }
};

} // namespace lift
