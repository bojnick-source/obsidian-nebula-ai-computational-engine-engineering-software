#pragma once
#include "forge/common/result.hpp"
#include <string>
#include <unordered_set>
#include <mutex>

namespace forge::blackboard {

/// Optimistic concurrency control for blackboard fields.
/// Tracks which fields are currently being written to prevent concurrent writes.
class ConcurrencyGuard {
public:
    /// Attempt to acquire write lock for a field.
    /// Returns error if field is already being written.
    forge::common::VoidResult try_lock_write(const std::string& field);

    /// Release write lock for a field.
    void unlock_write(const std::string& field);

    /// RAII write lock guard.
    class WriteGuard {
    public:
        explicit WriteGuard(ConcurrencyGuard& guard, const std::string& field);
        ~WriteGuard();
        WriteGuard(const WriteGuard&) = delete;
        WriteGuard& operator=(const WriteGuard&) = delete;
    private:
        ConcurrencyGuard& guard_;
        std::string field_;
        bool active_{false};
    };

private:
    mutable std::mutex mutex_;
    std::unordered_set<std::string> locked_fields_;
};

} // namespace forge::blackboard
