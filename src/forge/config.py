"""FORGE configuration loader.

Loads forge.yaml and validates it into typed Pydantic models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


# --- Sub-models ---

class ForgeMetadata(BaseModel):
    version: str
    name: str
    mode: str = "mvp"


class LoggingConfig(BaseModel):
    format: str = "jsonl"
    directory: str = "logs"
    level: str = "INFO"
    trace_ids: bool = True


class ProviderModel(BaseModel):
    id: str
    tier: str
    roles: list[str] = Field(default_factory=list)
    validated: bool = True


class ProviderConfig(BaseModel):
    models: list[ProviderModel] = Field(default_factory=list)
    api_base: str = ""
    env_key: str = ""


class AgentConfig(BaseModel):
    id: str
    role: str
    provider: str
    model: str


class MemoryConfig(BaseModel):
    mode: str = "degraded"
    vault_path: str = "vault/"
    supermemory: dict[str, Any] = Field(default_factory=dict)


class BudgetConfig(BaseModel):
    daily_ceiling_usd: float | None = None
    alert_threshold_pct: int = 80


class ToolConfig(BaseModel):
    id: str
    status: str = "planned"


class ForgeConfig(BaseModel):
    """Top-level FORGE configuration."""

    forge: ForgeMetadata
    logging: LoggingConfig = LoggingConfig()
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    memory: MemoryConfig = MemoryConfig()
    budget: BudgetConfig = BudgetConfig()
    tools: dict[str, ToolConfig] = Field(default_factory=dict)


def load_config(path: Path) -> ForgeConfig:
    """Load and validate forge.yaml into a ForgeConfig model."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ForgeConfig.model_validate(raw)
