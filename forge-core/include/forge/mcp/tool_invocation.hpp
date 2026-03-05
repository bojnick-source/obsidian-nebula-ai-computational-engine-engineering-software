#pragma once
#include "forge/common/ids.hpp"
#include "forge/common/result.hpp"
#include <string>
#include <unordered_map>

namespace forge::mcp {

/// JSON-like payload for tool input/output.
using Payload = std::unordered_map<std::string, std::string>; // simplified; use nlohmann::json in impl

struct ToolInvocationRequest {
    std::string                  tool_id;
    std::string                  wrapper_version;
    forge::common::TraceId       trace_id;
    forge::common::TaskId        task_id;
    forge::common::InvocationId  invocation_id;
    int                          timeout_ms{30000};
    Payload                      input;
    bool                         sandbox_enabled{true};
    int                          max_memory_mb{512};
    int                          max_cpu_seconds{60};
};

/// Abstract base for MCP tool invokers.
class ToolInvoker {
public:
    virtual ~ToolInvoker() = default;
    virtual std::string tool_id() const = 0;
    virtual std::string wrapper_version() const = 0;
    virtual forge::common::Result<Payload> invoke(const ToolInvocationRequest& req) = 0;
};

} // namespace forge::mcp
