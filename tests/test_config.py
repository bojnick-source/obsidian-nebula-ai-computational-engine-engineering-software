"""Tests for forge.config — configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.config import load_config


class TestLoadConfig:
    """Tests for load_config and ForgeConfig structure."""

    def test_load_config_succeeds(self, repo_root: Path) -> None:
        """load_config successfully loads the forge.yaml file."""
        config = load_config(repo_root / "forge.yaml")
        assert config is not None
        assert config.forge.name != ""

    def test_config_has_seven_agents(self, forge_config) -> None:
        """Config has exactly 7 agents."""
        assert len(forge_config.agents) == 7

    def test_config_has_three_providers(self, forge_config) -> None:
        """Config has exactly 3 providers (anthropic, openai, deepseek)."""
        assert len(forge_config.providers) == 3
        assert set(forge_config.providers.keys()) == {
            "anthropic",
            "openai",
            "deepseek",
        }

    def test_config_version(self, forge_config) -> None:
        """Config version is '0.1.0'."""
        assert forge_config.forge.version == "0.1.0"

    def test_config_memory_mode(self, forge_config) -> None:
        """Config memory mode is 'degraded'."""
        assert forge_config.memory.mode == "degraded"

    def test_each_agent_has_required_fields(self, forge_config) -> None:
        """Each agent has required fields: id, role, provider, model."""
        for name, agent in forge_config.agents.items():
            assert agent.id, f"Agent '{name}' missing id"
            assert agent.role, f"Agent '{name}' missing role"
            assert agent.provider, f"Agent '{name}' missing provider"
            assert agent.model, f"Agent '{name}' missing model"
