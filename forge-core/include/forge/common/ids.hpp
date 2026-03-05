#pragma once
#include <string>
#include <string_view>

namespace forge::common {

/// UUID v4 string: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
using TraceId = std::string;
using TaskId  = std::string;
using NoteId  = std::string;
using InvocationId = std::string;

/// Generate a new UUID v4 trace ID.
TraceId generate_trace_id();

/// Generate a new UUID v4 task ID.
TaskId  generate_task_id();

/// Generate a new UUID v4 invocation ID (for MCP tool calls).
InvocationId generate_invocation_id();

/// Validate that a string looks like a UUID v4.
bool is_valid_uuid(std::string_view s);

} // namespace forge::common
