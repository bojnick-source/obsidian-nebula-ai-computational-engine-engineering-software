"""Shared pytest fixtures for FORGE test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.config import ForgeConfig, load_config


@pytest.fixture()
def repo_root() -> Path:
    """Return the Path to the repository root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture()
def forge_config(repo_root: Path) -> ForgeConfig:
    """Load the real forge.yaml from the repository root."""
    return load_config(repo_root / "forge.yaml")
