#pragma once
#include <string>
#include <vector>

namespace forge::routing {

/// Policy for provider fallback chains.
struct FallbackPolicy {
    /// Ordered list of provider IDs to try (in priority order).
    std::vector<std::string> provider_chain;

    /// If true, activate degraded mode when all providers fail.
    /// If false, return error.
    bool allow_degraded_mode{true};

    /// Maximum retries per provider before moving to next.
    int max_retries_per_provider{2};

    /// Health check interval in seconds.
    int health_check_interval_s{30};
};

} // namespace forge::routing
