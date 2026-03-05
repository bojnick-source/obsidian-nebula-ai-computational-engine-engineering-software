#pragma once
#include "forge/blackboard/typed_entry.hpp"
#include "forge/blackboard/concurrency_guard.hpp"
#include "forge/common/ids.hpp"
#include "forge/common/result.hpp"
#include <string>
#include <unordered_map>
#include <memory>
#include <shared_mutex>

namespace forge::blackboard {

/// Thread-safe shared state for a single FORGE task execution.
/// All agents, tools, and verifiers read/write through this interface.
class Blackboard {
public:
    explicit Blackboard(forge::common::TraceId trace_id,
                        forge::common::TaskId  task_id);

    /// Write a typed entry. Fails if field is locked by concurrent write.
    forge::common::VoidResult write(const std::string& field, TypedEntry entry);

    /// Read a typed entry. Returns nullopt if field doesn't exist.
    std::optional<TypedEntry> read(const std::string& field) const;

    /// Check if a field exists.
    bool has(const std::string& field) const;

    /// Get the trace ID for this blackboard.
    const forge::common::TraceId& trace_id() const noexcept;

    /// Get the task ID for this blackboard.
    const forge::common::TaskId& task_id() const noexcept;

    /// Validate the current blackboard state against schema v1.
    forge::common::VoidResult validate() const;

    /// Return all field names currently set.
    std::vector<std::string> fields() const;

private:
    forge::common::TraceId trace_id_;
    forge::common::TaskId  task_id_;

    mutable std::shared_mutex mutex_;
    std::unordered_map<std::string, TypedEntry> entries_;
    ConcurrencyGuard concurrency_guard_;
};

} // namespace forge::blackboard
