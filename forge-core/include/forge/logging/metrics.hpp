#pragma once
#include <string>
#include <unordered_map>
#include <atomic>
#include <mutex>

namespace forge::logging {

/// Simple in-process metrics registry.
/// In production, export to Prometheus or similar.
class MetricsRegistry {
public:
    /// Increment a counter by delta.
    void increment(const std::string& metric,
                   const std::unordered_map<std::string, std::string>& labels = {},
                   long delta = 1);

    /// Record a histogram observation (e.g., duration_ms).
    void observe(const std::string& metric, long value,
                 const std::unordered_map<std::string, std::string>& labels = {});

    /// Set a gauge value.
    void set_gauge(const std::string& metric, double value,
                   const std::unordered_map<std::string, std::string>& labels = {});

    /// Return all current counter values (for testing).
    std::unordered_map<std::string, long> snapshot_counters() const;

private:
    mutable std::mutex mutex_;
    std::unordered_map<std::string, long> counters_;
    std::unordered_map<std::string, double> gauges_;
};

} // namespace forge::logging
