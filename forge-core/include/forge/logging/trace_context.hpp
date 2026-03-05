#pragma once
#include <string>

namespace forge::logging {

/// Trace context carried through all log events for a task.
struct TraceContext {
    std::string trace_id;    ///< Task trace ID (UUID v4)
    std::string task_id;     ///< Task ID
    std::string phase;       ///< Current phase name
    std::string agent_id;    ///< Active agent (if any)
    std::string tool_id;     ///< Active tool (if any)
    std::string invocation_id; ///< Active invocation (if any)
};

} // namespace forge::logging
