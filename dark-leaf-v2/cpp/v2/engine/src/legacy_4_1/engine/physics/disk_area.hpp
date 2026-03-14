#pragma once

#include <string>

#include "engine/core/design.hpp"
#include "engine/core/errors.hpp"

namespace lift {

struct DiskAreaResult {
  double A_single_m2 = 0.0;
  double A_total_m2 = 0.0;
  int effective_disk_count = 0;
  std::string notes;
};

DiskAreaResult compute_effective_disk_area(const Design& d);

}  // namespace lift
