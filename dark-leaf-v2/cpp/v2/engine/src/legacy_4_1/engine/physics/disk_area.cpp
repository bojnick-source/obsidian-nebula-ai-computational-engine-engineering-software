#include "engine/physics/disk_area.hpp"

#include <cmath>
#include <sstream>

namespace lift {

namespace {

// Use a portable constant — M_PI is not guaranteed by the C++ standard
// (it requires _USE_MATH_DEFINES on MSVC or _GNU_SOURCE on some platforms).
constexpr double kPi = 3.14159265358979323846;

inline double disk_area(double radius_m) {
  return kPi * radius_m * radius_m;
}

}  // namespace

DiskAreaResult compute_effective_disk_area(const Design& d) {
  d.validate_or_throw();

  DiskAreaResult r{};

  const bool use_shroud = d.has_shroud && d.shroud_inner_radius_m > 0.0;
  const double effective_radius = use_shroud ? d.shroud_inner_radius_m : d.rotor_radius_m;

  if (!(effective_radius > 0.0)) {
    throw ValidationError("compute_effective_disk_area: effective_radius must be > 0");
  }

  r.A_single_m2 = disk_area(effective_radius);

  std::ostringstream notes;

  if (d.is_coaxial) {
    if (d.coax_pairs <= 0) {
      throw ValidationError("compute_effective_disk_area: is_coaxial true but coax_pairs <= 0");
    }
    r.effective_disk_count = d.coax_pairs;
    r.A_total_m2 = r.A_single_m2 * static_cast<double>(d.coax_pairs);
    notes << "Coaxial stacks: footprint counted per stack, not per stage; "
          << "coax_pairs=" << d.coax_pairs
          << ", effective_radius_m=" << effective_radius
          << (use_shroud ? " (shroud inlet used)" : " (rotor disk used)")
          << ".";
  } else {
    r.effective_disk_count = d.rotor_count;
    r.A_total_m2 = r.A_single_m2 * static_cast<double>(d.rotor_count);
    notes << "Distributed rotors: A_total = rotor_count * A_single; "
          << "effective_radius_m=" << effective_radius
          << (use_shroud ? " (shroud inlet used)" : " (rotor disk used)")
          << ".";
  }

  r.notes = notes.str();
  return r;
}

}  // namespace lift
