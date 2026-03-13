"""Tests for forge_manufacturing.artifacts — path safety and file writers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from forge_manufacturing.artifacts import (
    create_placeholder_dir,
    create_placeholder_file,
    expand_placeholders,
    normalize_optional_name,
    resolve_path,
    safe_relative_path,
    write_json,
    write_text,
    write_yaml,
)


# ── Placeholder expansion ─────────────────────────────────────────────────────


def test_expand_placeholders_basic():
    result = expand_placeholders(
        "builds/<build_id>/report.json",
        {"build_id": "BLD-001"},
    )
    assert result == "builds/BLD-001/report.json"


def test_expand_placeholders_multiple():
    result = expand_placeholders(
        "<build_id>-<REV_TAG>",
        {"build_id": "BLD-001", "REV_TAG": "REV_A"},
    )
    assert result == "BLD-001-REV_A"


def test_expand_placeholders_unknown_key_unchanged():
    """Unknown keys are not replaced."""
    result = expand_placeholders("<unknown>", {"build_id": "X"})
    assert result == "<unknown>"


# ── Optional name parsing ─────────────────────────────────────────────────────


def test_normalize_optional_name_suffix():
    name, is_opt = normalize_optional_name("NDI scan (if applicable)")
    assert name == "NDI scan"
    assert is_opt is True


def test_normalize_optional_name_plain():
    name, is_opt = normalize_optional_name("Cure cycle")
    assert name == "Cure cycle"
    assert is_opt is False


# ── Path safety ───────────────────────────────────────────────────────────────


def test_safe_relative_path_ok():
    p = safe_relative_path("builds/BLD-001/ledger.json")
    assert str(p) == "builds/BLD-001/ledger.json"


def test_safe_relative_path_rejects_absolute():
    with pytest.raises(ValueError, match="absolute"):
        safe_relative_path("/etc/passwd")


def test_safe_relative_path_rejects_traversal():
    with pytest.raises(ValueError, match="traversal"):
        safe_relative_path("../../secrets")


def test_resolve_path_joins_correctly(tmp_path: Path):
    result = resolve_path(tmp_path, "sub/file.txt")
    assert result == tmp_path / "sub" / "file.txt"


# ── File writers ──────────────────────────────────────────────────────────────


def test_write_text(tmp_path: Path):
    p = tmp_path / "sub" / "out.txt"
    write_text(p, "hello forge")
    assert p.read_text() == "hello forge"


def test_write_json(tmp_path: Path):
    p = tmp_path / "data.json"
    write_json(p, {"key": "value", "num": 42})
    loaded = json.loads(p.read_text())
    assert loaded == {"key": "value", "num": 42}


def test_write_yaml(tmp_path: Path):
    p = tmp_path / "data.yaml"
    write_yaml(p, {"key": "value"})
    loaded = yaml.safe_load(p.read_text())
    assert loaded == {"key": "value"}


def test_create_placeholder_file(tmp_path: Path):
    p = tmp_path / "sub" / "placeholder.txt"
    create_placeholder_file(p, "# placeholder\n")
    assert p.read_text() == "# placeholder\n"


def test_create_placeholder_dir(tmp_path: Path):
    p = tmp_path / "new_dir"
    create_placeholder_dir(p)
    assert p.is_dir()
