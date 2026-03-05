#pragma once
#include "forge/routing/provider_adapter.hpp"
#include <vector>
#include <memory>
#include <thread>
#include <atomic>
#include <mutex>

namespace forge::routing {

/// Background health monitor that polls all providers at a configurable interval.
class ProviderHealthMonitor {
public:
    explicit ProviderHealthMonitor(
        std::vector<ProviderAdapter*> providers,
        int interval_s = 30);

    ~ProviderHealthMonitor();

    /// Start background polling.
    void start();

    /// Stop background polling.
    void stop();

    /// Get the last known status of a provider.
    ProviderStatus get_status(const std::string& provider_id) const;

    /// Get all statuses.
    std::vector<ProviderStatus> all_statuses() const;

private:
    void poll_loop();

    std::vector<ProviderAdapter*> providers_;
    int interval_s_;

    std::atomic<bool> running_{false};
    std::thread poll_thread_;

    mutable std::mutex status_mutex_;
    std::vector<ProviderStatus> statuses_;
};

} // namespace forge::routing
