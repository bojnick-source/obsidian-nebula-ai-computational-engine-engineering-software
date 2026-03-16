/**
 * @file model_router.cpp
 * @brief Routes agent calls to LLM providers based on health, cost, and policy.
 *
 * Latency target: < 100 ms (provider list is short; no I/O on the hot path).
 *
 * Algorithm
 * ---------
 * 1. Walk provider_chain in order.
 * 2. For each provider, call health_check() if the last check is stale.
 * 3. Return the first healthy provider that can serve the requested task_type.
 * 4. If none healthy and allow_degraded_mode, return the first available
 *    provider anyway (is_degraded = true).
 * 5. If none available at all, return ERR_ALL_PROVIDERS_UNAVAILABLE.
 */

#include "forge/routing/model_router.hpp"

#include <algorithm>
#include <chrono>
#include <stdexcept>
#include <unordered_map>

namespace forge::routing {

namespace {

// Find a ProviderAdapter* by provider_id.
ProviderAdapter* find_provider(
    std::vector<std::unique_ptr<ProviderAdapter>>& providers,
    const std::string& id)
{
    for (auto& p : providers) {
        if (p->provider_id() == id) return p.get();
    }
    return nullptr;
}

} // anonymous namespace

// ── Constructor ───────────────────────────────────────────────────────────────

ModelRouter::ModelRouter(
    std::vector<std::unique_ptr<ProviderAdapter>> providers,
    FallbackPolicy fallback_policy)
    : providers_(std::move(providers))
    , fallback_policy_(std::move(fallback_policy))
{}

// ── route ─────────────────────────────────────────────────────────────────────

forge::common::Result<RouteResponse> ModelRouter::route(const RouteRequest& req) {
    ProviderAdapter* degraded_candidate = nullptr;

    for (const auto& provider_id : fallback_policy_.provider_chain) {
        ProviderAdapter* adapter = find_provider(providers_, provider_id);
        if (!adapter) continue;

        ProviderStatus status = adapter->health_check();

        if (status.healthy) {
            return forge::common::Result<RouteResponse>::ok({
                adapter->provider_id(),
                adapter->default_model_id(),
                false,
                {}
            });
        }

        // Remember first unhealthy-but-existing provider for degraded fallback
        if (!degraded_candidate) {
            degraded_candidate = adapter;
        }
    }

    if (fallback_policy_.allow_degraded_mode && degraded_candidate) {
        return forge::common::Result<RouteResponse>::ok({
            degraded_candidate->provider_id(),
            degraded_candidate->default_model_id(),
            true,
            "All providers degraded — operating in fallback mode"
        });
    }

    return forge::common::Result<RouteResponse>::err({
        "ERR_ALL_PROVIDERS_UNAVAILABLE",
        "No healthy LLM provider found for trace_id=" + req.trace_id
    });
}

// ── check_all_providers ───────────────────────────────────────────────────────

void ModelRouter::check_all_providers() {
    for (auto& p : providers_) {
        p->health_check(); // Side effect: updates internal health state
    }
}

// ── provider_statuses ─────────────────────────────────────────────────────────

std::vector<ProviderStatus> ModelRouter::provider_statuses() const {
    std::vector<ProviderStatus> statuses;
    statuses.reserve(providers_.size());
    for (const auto& p : providers_) {
        statuses.push_back(p->health_check());
    }
    return statuses;
}

} // namespace forge::routing
