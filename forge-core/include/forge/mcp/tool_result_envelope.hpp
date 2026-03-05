#pragma once
#include "forge/mcp/tool_invocation.hpp"
#include <string>
#include <optional>

namespace forge::mcp {

enum class ToolStatus { Success, Error, Timeout, Degraded };

struct ToolResultEnvelope {
    std::string      tool_id;
    std::string      wrapper_version;
    std::string      trace_id;
    std::string      invocation_id;
    std::string      timestamp;       ///< ISO8601
    long             duration_ms{0};
    ToolStatus       status{ToolStatus::Error};
    std::optional<std::string> error_code;
    std::optional<std::string> error_detail;
    Payload          output;

    // Audit fields
    std::string      stdout_hash;     ///< sha256 of subprocess stdout
    int              stderr_lines{0};
    int              exit_code{-1};
};

} // namespace forge::mcp
