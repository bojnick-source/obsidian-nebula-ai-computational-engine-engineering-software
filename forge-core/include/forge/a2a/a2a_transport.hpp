#pragma once
#include "forge/common/result.hpp"
#include "forge/common/ids.hpp"
#include <string>
#include <unordered_map>

namespace forge::a2a {

using Payload = std::unordered_map<std::string, std::string>;

struct A2AMessage {
    std::string                  message_id;
    forge::common::TraceId       trace_id;
    std::string                  from_agent;
    std::string                  to_agent;
    std::string                  message_type;  ///< "task_packet" | "agent_output" | "debate_msg"
    Payload                      payload;
    std::string                  timestamp;
};

struct A2AResponse {
    std::string  message_id;      ///< echo of request message_id
    Payload      payload;
    bool         success{false};
    std::string  error_code;
};

/// Abstract A2A transport. Implement as gRPC (production) or in-process (testing).
class A2ATransport {
public:
    virtual ~A2ATransport() = default;

    virtual forge::common::Result<A2AResponse> send(const A2AMessage& msg) = 0;
    virtual bool is_connected() const = 0;
};

} // namespace forge::a2a
