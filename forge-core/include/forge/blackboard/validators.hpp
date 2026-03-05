#pragma once
#include "forge/blackboard/typed_entry.hpp"
#include "forge/common/result.hpp"
#include <string>

namespace forge::blackboard {

/// Validate a single entry against the declared schema_type.
forge::common::VoidResult validate_entry_type(const TypedEntry& entry);

/// Validate that all required fields are present for a given task type.
/// Fields checked against blackboard schema v1.
forge::common::VoidResult validate_required_fields(
    const std::unordered_map<std::string, TypedEntry>& entries,
    const std::string& task_type);

/// Validate that numeric entries have units set.
forge::common::VoidResult validate_units_present(const TypedEntry& entry);

} // namespace forge::blackboard
