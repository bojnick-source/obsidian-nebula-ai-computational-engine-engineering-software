#pragma once
#include "forge/common/time.hpp"
#include <string>
#include <variant>
#include <vector>
#include <optional>

namespace forge::blackboard {

/// Primitive value types allowed in a blackboard entry.
using EntryValue = std::variant<
    std::monostate,       // null / unset
    bool,
    int64_t,
    double,
    std::string,
    std::vector<std::string>
>;

/// A single typed entry on the blackboard.
struct TypedEntry {
    std::string              field;        ///< Field name (e.g., "task.type")
    EntryValue               value;        ///< The value
    std::string              schema_type;  ///< Expected type name (for validation)
    std::string              agent_id;     ///< Agent that wrote this entry
    forge::common::TimePoint written_at;
    std::string              trace_id;     ///< Trace ID of the task

    /// Version counter for optimistic concurrency control.
    uint64_t version{0};

    /// Optional units for numeric values (e.g., "MPa", "N", "mm").
    std::optional<std::string> units;
};

} // namespace forge::blackboard
