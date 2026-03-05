#pragma once
#include "forge/a2a/a2a_transport.hpp"
#include <functional>
#include <unordered_map>

namespace forge::a2a {

/// In-process A2A shim for testing. Routes messages to registered handlers.
class A2ALocalShim : public A2ATransport {
public:
    using Handler = std::function<A2AResponse(const A2AMessage&)>;

    void register_agent(const std::string& agent_id, Handler handler);

    forge::common::Result<A2AResponse> send(const A2AMessage& msg) override;
    bool is_connected() const override { return true; }

private:
    std::unordered_map<std::string, Handler> handlers_;
};

} // namespace forge::a2a
