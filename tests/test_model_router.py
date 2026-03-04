"""Tests for forge.model_router — provider routing, fallback, and budget."""

from __future__ import annotations

import pytest

from forge.config import (
    ForgeConfig,
    ForgeMetadata,
    ProviderConfig,
    ProviderModel,
    AgentConfig,
    BudgetConfig,
)
from forge.model_router import ModelRouter


@pytest.fixture()
def minimal_config() -> ForgeConfig:
    """Create a minimal ForgeConfig for router tests."""
    return ForgeConfig(
        forge=ForgeMetadata(version="0.1.0", name="test"),
        providers={
            "anthropic": ProviderConfig(
                models=[
                    ProviderModel(id="claude-opus-4-6", tier="frontier", roles=["orchestrator"]),
                ],
                api_base="https://api.anthropic.com",
                env_key="ANTHROPIC_API_KEY",
            ),
            "openai": ProviderConfig(
                models=[
                    ProviderModel(id="gpt-5.2", tier="frontier", roles=["me_specialist"]),
                ],
                api_base="https://api.openai.com/v1",
                env_key="OPENAI_API_KEY",
            ),
            "deepseek": ProviderConfig(
                models=[
                    ProviderModel(id="deepseek-reasoner", tier="mid", roles=["backup"]),
                ],
                api_base="https://api.deepseek.com",
                env_key="DEEPSEEK_API_KEY",
            ),
        },
        agents={
            "orchestrator": AgentConfig(
                id="ORCH-01",
                role="orchestration",
                provider="anthropic",
                model="claude-opus-4-6",
            ),
            "me_specialist": AgentConfig(
                id="E-01",
                role="mechanical analysis",
                provider="openai",
                model="gpt-5.2",
            ),
        },
        budget=BudgetConfig(daily_ceiling_usd=None),
    )


@pytest.fixture()
def capped_config() -> ForgeConfig:
    """Create a ForgeConfig with a budget ceiling for budget gate tests."""
    return ForgeConfig(
        forge=ForgeMetadata(version="0.1.0", name="test"),
        providers={
            "anthropic": ProviderConfig(
                models=[
                    ProviderModel(id="claude-opus-4-6", tier="frontier", roles=[]),
                ],
            ),
        },
        agents={
            "orchestrator": AgentConfig(
                id="ORCH-01",
                role="orchestration",
                provider="anthropic",
                model="claude-opus-4-6",
            ),
        },
        budget=BudgetConfig(daily_ceiling_usd=10.0),
    )


class TestModelRouter:
    """Tests for ModelRouter routing logic."""

    def test_route_returns_correct_provider_orchestrator(self, minimal_config) -> None:
        """route() returns anthropic for orchestrator agent."""
        router = ModelRouter(minimal_config)
        result = router.route("orchestrator")
        assert result.provider == "anthropic"
        assert result.model == "claude-opus-4-6"
        assert result.agent_id == "ORCH-01"

    def test_route_returns_correct_provider_me_specialist(self, minimal_config) -> None:
        """route() returns openai for me_specialist agent."""
        router = ModelRouter(minimal_config)
        result = router.route("me_specialist")
        assert result.provider == "openai"
        assert result.model == "gpt-5.2"
        assert result.agent_id == "E-01"

    def test_route_raises_for_unknown_agent(self, minimal_config) -> None:
        """route() raises ValueError for unknown agent."""
        router = ModelRouter(minimal_config)
        with pytest.raises(ValueError, match="Unknown agent"):
            router.route("nonexistent_agent")

    def test_fallback_when_primary_unhealthy(self, minimal_config) -> None:
        """Fallback works when primary provider is marked unhealthy."""
        router = ModelRouter(minimal_config)
        # Mark anthropic as unhealthy (3 consecutive failures)
        for _ in range(3):
            router.report_failure("anthropic", "timeout")
        result = router.route("orchestrator")
        assert result.fallback_used is True
        assert result.provider != "anthropic"

    def test_budget_gate_returns_true_no_ceiling(self, minimal_config) -> None:
        """Budget gate returns True when no ceiling is set."""
        router = ModelRouter(minimal_config)
        assert router.check_budget(100.0) is True

    def test_budget_gate_returns_false_over_ceiling(self, capped_config) -> None:
        """Budget gate returns False when cost exceeds ceiling."""
        router = ModelRouter(capped_config)
        router.record_cost(9.0)
        assert router.check_budget(2.0) is False

    def test_provider_health_tracking(self, minimal_config) -> None:
        """Provider health tracking: report_failure degrades, report_success resets."""
        router = ModelRouter(minimal_config)
        # Initially healthy
        assert router._is_healthy("anthropic") is True

        # Two failures — still healthy
        router.report_failure("anthropic", "error1")
        router.report_failure("anthropic", "error2")
        assert router._is_healthy("anthropic") is True

        # Third failure — unhealthy
        router.report_failure("anthropic", "error3")
        assert router._is_healthy("anthropic") is False

        # Success resets
        router.report_success("anthropic")
        assert router._is_healthy("anthropic") is True
