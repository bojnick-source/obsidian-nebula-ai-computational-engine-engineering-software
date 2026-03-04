"""Tests for forge.cli — CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from forge.cli import main


def _write_minimal_config(path: Path) -> Path:
    """Write a minimal valid forge.yaml to the given directory and return its path."""
    config = {
        "forge": {"version": "0.1.0", "name": "test", "mode": "mvp"},
        "logging": {"format": "jsonl", "directory": str(path / "logs"), "level": "INFO", "trace_ids": True},
        "providers": {},
        "agents": {},
        "memory": {"mode": "degraded", "vault_path": "vault/", "supermemory": {"enabled": False}},
        "budget": {"daily_ceiling_usd": None, "alert_threshold_pct": 80},
        "tools": {},
    }
    config_file = path / "forge.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return config_file


class TestCLI:
    """Tests for FORGE CLI entry point."""

    def test_version_output(self, capsys) -> None:
        """CLI --version outputs version string."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "FORGE v" in captured.out

    def test_missing_config_returns_error(self, tmp_path) -> None:
        """CLI with missing config file returns error code 1."""
        missing = tmp_path / "does_not_exist.yaml"
        result = main(["--config", str(missing)])
        assert result == 1

    def test_smoke_test_with_valid_config(self, repo_root) -> None:
        """CLI --smoke-test with valid config returns 0."""
        config_path = repo_root / "forge.yaml"
        result = main(["--config", str(config_path), "--smoke-test"])
        assert result == 0
