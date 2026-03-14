#pragma once

#include "v2/physics/interfaces/disk_area_calculator.hpp"

namespace v2::physics::baseline {

class DiskAreaCalculator final : public v2::physics::DiskAreaCalculator {
public:
    DiskAreaResult compute(const RotorGeometry& geometry) const override;
};

} // namespace v2::physics::baseline
