"""FORGE Model Router — provider selection and failover.

MVP: role-tier resolution, provider health check stub, fallback chains.
Actual API calls deferred to M1 Phase 0.2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from forge.config import ForgeConfig, AgentConfig


@dataclass
class RouteResult:
    """Result of a routing decision."""

    agent_id: str
    provider: str
    model: str
    tier: str
    fallback_used: bool = False


@dataclass
class ProviderHealth:
    """Health status for a provider."""

    provider: str
    healthy: bool = True
    last_error: str | None = None
    consecutive_failures: int = 0


class ModelRouter:
    """Routes agent requests to the correct provider and model.

    MVP scope:
    - Role-tier resolution from forge.yaml
    - Provider health tracking (in-memory)
    - Fallback chains (if primary unhealthy, try next)
    - Budget gate stub (halts at ceiling)
    """

    # Default fallback order for MVP providers
    FALLBACK_ORDER = ["anthropic", "openai", "deepseek"]

    def __init__(self, config: ForgeConfig) -> None:
        self._config = config
        self._health: dict[str, ProviderHealth] = {
            name: ProviderHealth(provider=name)
            for name in config.providers
        }
        self._total_cost_usd: float = 0.0

    def route(self, agent_name: str) -> RouteResult:
        """Resolve the provider and model for a given agent."""
        agent_cfg = self._config.agents.get(agent_name)
        if agent_cfg is None:
            raise ValueError(f"Unknown agent: {agent_name}")

        primary_provider = agent_cfg.provider
        primary_model = agent_cfg.model

        # Check primary health
        if self._is_healthy(primary_provider):
            return RouteResult(
                agent_id=agent_cfg.id,
                provider=primary_provider,
                model=primary_model,
                tier=self._get_tier(primary_provider, primary_model),
            )

        # Fallback: try other providers in order
        for fb_provider in self.FALLBACK_ORDER:
            if fb_provider == primary_provider:
                continue
            if self._is_healthy(fb_provider):
                fb_model = self._first_model(fb_provider)
                if fb_model:
                    return RouteResult(
                        agent_id=agent_cfg.id,
                        provider=fb_provider,
                        model=fb_model,
                        tier=self._get_tier(fb_provider, fb_model),
                        fallback_used=True,
                    )

        raise RuntimeError(
            f"No healthy provider available for agent '{agent_name}'"
        )

    def check_budget(self, estimated_cost_usd: float) -> bool:
        """Return True if the estimated cost fits within budget ceiling."""
        ceiling = self._config.budget.daily_ceiling_usd
        if ceiling is None:
            return True  # No ceiling set yet (pre-validation)
        return (self._total_cost_usd + estimated_cost_usd) <= ceiling

    def record_cost(self, cost_usd: float) -> None:
        """Record an API call cost."""
        self._total_cost_usd += cost_usd

    def report_failure(self, provider: str, error: str) -> None:
        """Report a provider failure for health tracking."""
        health = self._health.get(provider)
        if health:
            health.consecutive_failures += 1
            health.last_error = error
            if health.consecutive_failures >= 3:
                health.healthy = False

    def report_success(self, provider: str) -> None:
        """Report a provider success, resetting failure count."""
        health = self._health.get(provider)
        if health:
            health.consecutive_failures = 0
            health.healthy = True

    def _is_healthy(self, provider: str) -> bool:
        health = self._health.get(provider)
        return health.healthy if health else False

    def _get_tier(self, provider: str, model_id: str) -> str:
        pcfg = self._config.providers.get(provider)
        if pcfg:
            for m in pcfg.models:
                if m.id == model_id:
                    return m.tier
        return "unknown"

    def _first_model(self, provider: str) -> str | None:
        pcfg = self._config.providers.get(provider)
        if pcfg and pcfg.models:
            return pcfg.models[0].id
        return None

    @property
    def total_cost_usd(self) -> float:
        return self._total_cost_usd
