#pragma once
/*
================================================================================
v2 Physics Interfaces — Disk Area Calculator
FILE: v2/physics/interfaces/disk_area_calculator.hpp

Purpose:
  - Abstract base class for rotor disk area computation
  - Shared POD structs: RotorGeometry, DiskAreaResult
================================================================================
*/

#include <string>

namespace v2::physics {

// ---------------------------------------------------------------------------
// Input POD
// ---------------------------------------------------------------------------

struct RotorGeometry {
    double rotor_radius_m        = 0.0;  // Tip radius of one rotor [m]
    double rotor_count           = 1.0;  // Number of rotors (must be integer value)
    bool   is_coaxial            = false;
    int    coax_pairs            = 0;    // Explicit coaxial-stack count (0 = auto)
    bool   has_shroud            = false;
    double shroud_inner_radius_m = 0.0;  // Used when has_shroud == true
};

// ---------------------------------------------------------------------------
// Output POD
// ---------------------------------------------------------------------------

struct DiskAreaResult {
    double      A_single_m2         = 0.0;
    double      A_total_m2          = 0.0;
    int         effective_disk_count = 0;
    std::string notes;
};

// ---------------------------------------------------------------------------
// Abstract interface
// ---------------------------------------------------------------------------

class DiskAreaCalculator {
public:
    virtual ~DiskAreaCalculator() = default;

    virtual DiskAreaResult compute(const RotorGeometry& geometry) const = 0;
};

} // namespace v2::physics
