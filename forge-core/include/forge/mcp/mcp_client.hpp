#pragma once
#include "forge/mcp/tool_invocation.hpp"
#include "forge/mcp/tool_result_envelope.hpp"
#include "forge/common/result.hpp"
#include <memory>
#include <string>
#include <unordered_map>

namespace forge::mcp {

/// Registry of available MCP tool wrappers.
class ToolRegistry {
public:
    void register_tool(std::string tool_id, std::unique_ptr<ToolInvoker> invoker);
    ToolInvoker* get(const std::string& tool_id) const;
    bool has(const std::string& tool_id) const;
private:
    std::unordered_map<std::string, std::unique_ptr<ToolInvoker>> tools_;
};

/// MCP client that routes tool invocations to the correct wrapper.
class McpClient {
public:
    struct Config {
        int default_timeout_ms{30000};
        int max_retries{3};
        bool allow_degraded_stubs{true};
    };

    explicit McpClient(Config config, std::unique_ptr<ToolRegistry> registry);

    /// Invoke a tool by ID with the given input payload.
    forge::common::Result<ToolResultEnvelope> invoke(
        const ToolInvocationRequest& req);

private:
    Config config_;
    std::unique_ptr<ToolRegistry> registry_;
};

} // namespace forge::mcp
