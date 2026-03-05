#pragma once
#include "forge/common/result.hpp"
#include <string>

namespace forge::routing {

struct ProviderStatus {
    std::string provider_id;
    bool        healthy{false};
    long        latency_ms{0};
    std::string last_error;
};

struct ProviderRequest {
    std::string trace_id;
    std::string model_id;
    std::string prompt;
    int         max_tokens{4096};
    float       temperature{0.2f};
};

struct ProviderResponse {
    std::string text;
    int         tokens_used{0};
    std::string stop_reason;
};

/// Abstract adapter for a single LLM provider (Anthropic, OpenAI, etc.).
class ProviderAdapter {
public:
    virtual ~ProviderAdapter() = default;

    virtual std::string provider_id() const = 0;
    virtual std::string default_model_id() const = 0;

    /// Check if the provider is currently healthy.
    virtual ProviderStatus health_check() = 0;

    /// Send a request to the provider.
    virtual forge::common::Result<ProviderResponse> call(
        const ProviderRequest& req) = 0;
};

} // namespace forge::routing
