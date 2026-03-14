#pragma once

#include "engine/core/errors.hpp"
#include "engine/core/settings.hpp"

namespace lift {

struct HoverMomentumResult {
  double thrust_N = 0.0;
  double A_total_m2 = 0.0;
  double disk_loading_N_per_m2 = 0.0;

  double P_induced_ideal_W = 0.0;
  double P_induced_W = 0.0;
  double P_total_W = 0.0;

  double FM_used = 0.0;
  double rho_used = 0.0;
};

HoverMomentumResult hover_momentum_power(double thrust_N,
                                         double A_total_m2,
                                         const EvalSettings& settings);

HoverMomentumResult hover_momentum_power_sized(double thrust_N,
                                               double A_total_m2,
                                               const EvalSettings& settings,
                                               double reserve_mult);

}  // namespace lift
