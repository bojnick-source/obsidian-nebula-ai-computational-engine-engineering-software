#pragma once
#include "forge/routing/provider_adapter.hpp"
#include "forge/routing/fallback_policy.hpp"
#include "forge/common/result.hpp"
#include "forge/common/ids.hpp"
#include <string>
#include <vector>
#include <memory>

namespace forge::routing {

/// Request to route to an LLM provider.
struct RouteRequest {
    forge::common::TraceId trace_id;
    std::string            agent_id;
    std::string            domain;
    std::string            task_type;     ///< "engineering_full" | "lite" | etc.
    size_t                 estimated_tokens{0};
};

/// Response from the router: which provider and model to use.
struct RouteResponse {
    std::string provider_id;   ///< e.g., "anthropic", "openai"
    std::string model_id;      ///< e.g., "claude-opus-4-6"
    bool        is_degraded{false};
    std::string degraded_reason;
};

/// Routes agent calls to LLM providers based on health, cost, and policy.
class ModelRouter {
public:
    explicit ModelRouter(std::vector<std::unique_ptr<ProviderAdapter>> providers,
                         FallbackPolicy fallback_policy);

    /// Route a request to the best available provider.
    forge::common::Result<RouteResponse> route(const RouteRequest& req);

    /// Force a health check on all providers.
    void check_all_providers();

    /// Get the current status of all providers.
    std::vector<ProviderStatus> provider_statuses() const;

private:
    std::vector<std::unique_ptr<ProviderAdapter>> providers_;
    FallbackPolicy fallback_policy_;
};

} // namespace forge::routing
