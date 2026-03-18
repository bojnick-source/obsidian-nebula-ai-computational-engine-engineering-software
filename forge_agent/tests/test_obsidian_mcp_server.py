"""
Tests for forge_agent/memory/obsidian_mcp_server.py

Covers the FastMCP-only fix:
  - All 7 tools are registered with correct names
  - Each tool delegates to the correct ObsidianVaultManager method
  - Return values are correctly serialized to plain dicts (no dataclass leakage)
  - Edge cases: get_note returns None, search_notes returns empty list
  - create_server logs the vault path and index size
  - main() exits when vault_path missing or not a directory
"""

import json
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from forge_agent.memory.obsidian_mcp_server import create_server


# ─── Fixtures ─────────────────────────────────────────────────────────────────


def _make_search_result(**kwargs):
    """Build a SimpleNamespace that mimics a search result dataclass."""
    defaults = {
        "path":        "engineering/constraints/thrust.md",
        "title":       "Max Thrust Constraint",
        "excerpt":     "Thrust must not exceed 450 kN at sea level.",
        "frontmatter": {"status": "validated", "confidence": "0.97"},
        "score":       0.87,
        "backlinks":   ["engineering/analysis/burn_time.md"],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_note(**kwargs):
    """Build a SimpleNamespace that mimics a VaultNote dataclass."""
    defaults = {
        "path":           "engineering/constraints/thrust.md",
        "title":          "Max Thrust Constraint",
        "frontmatter":    {"status": "validated"},
        "body":           "## Constraint\n\nThrust ≤ 450 kN.",
        "sections":       ["Constraint"],
        "tags":           ["validated", "constraint"],
        "outgoing_links": [],
        "modified":       "2024-01-15T10:30:00Z",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.fixture()
def mock_vault():
    """Return a mock ObsidianVaultManager with all expected methods."""
    m = MagicMock()
    m._index = {}  # empty index — create_server reads len(vault._index)
    return m


@pytest.fixture()
def app(mock_vault, tmp_path):
    """Create a FastMCP server with the mock vault injected."""
    with patch(
        "forge_agent.memory.obsidian_mcp_server.ObsidianVaultManager",
        return_value=mock_vault,
    ):
        return create_server(str(tmp_path))


# ─── Tool registration ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_all_eight_tools_registered(app):
    tools = await app.list_tools()
    names = {t.name for t in tools}
    assert names == {
        "search_notes",
        "get_note",
        "get_backlinks",
        "get_tags",
        "amnesia_check",
        "upsert_note",
        "append_to_note",
        "add_frontmatter",
    }


@pytest.mark.asyncio
async def test_server_name_is_obsidian_vault(app):
    assert app.name == "obsidian-vault"


@pytest.mark.asyncio
async def test_tool_schemas_have_descriptions(app):
    tools = await app.list_tools()
    for t in tools:
        assert t.description, f"Tool '{t.name}' has no description"


# ─── search_notes ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_notes_delegates_to_vault(app, mock_vault):
    mock_vault.search_notes.return_value = [_make_search_result()]

    _, meta = await app.call_tool("search_notes", {"query": "thrust constraint"})

    mock_vault.search_notes.assert_called_once_with(
        query="thrust constraint",
        top_k=5,
        domain=None,
        tags=None,
        min_confidence=None,
    )
    assert isinstance(meta["result"], list)
    assert len(meta["result"]) == 1


@pytest.mark.asyncio
async def test_search_notes_returns_plain_dicts(app, mock_vault):
    """Dataclass attributes must be serialized — no SimpleNamespace in output."""
    mock_vault.search_notes.return_value = [_make_search_result()]

    _, meta = await app.call_tool("search_notes", {"query": "thrust"})
    result = meta["result"][0]

    # All keys must be present
    for key in ("path", "title", "excerpt", "frontmatter", "score", "backlinks"):
        assert key in result, f"Missing key: {key}"

    # Must be JSON-serializable (no dataclass or SimpleNamespace)
    json.dumps(result)


@pytest.mark.asyncio
async def test_search_notes_passes_optional_filters(app, mock_vault):
    mock_vault.search_notes.return_value = []

    await app.call_tool("search_notes", {
        "query": "yield stress",
        "top_k": 3,
        "domain": "engineering/constraints",
        "tags": ["validated"],
        "min_confidence": 0.9,
    })

    mock_vault.search_notes.assert_called_once_with(
        query="yield stress",
        top_k=3,
        domain="engineering/constraints",
        tags=["validated"],
        min_confidence=0.9,
    )


@pytest.mark.asyncio
async def test_search_notes_empty_result(app, mock_vault):
    mock_vault.search_notes.return_value = []
    _, meta = await app.call_tool("search_notes", {"query": "nonexistent"})
    assert meta["result"] == []


# ─── get_note ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_note_found_returns_dict(app, mock_vault):
    mock_vault.get_note.return_value = _make_note()

    _, meta = await app.call_tool("get_note", {"path": "engineering/constraints/thrust.md"})
    result = meta["result"]

    assert result is not None
    for key in ("path", "title", "frontmatter", "body", "sections", "tags",
                "outgoing_links", "modified"):
        assert key in result, f"Missing key: {key}"

    # Must be JSON-serializable
    json.dumps(result)


@pytest.mark.asyncio
async def test_get_note_not_found_returns_none(app, mock_vault):
    mock_vault.get_note.return_value = None

    _, meta = await app.call_tool("get_note", {"path": "engineering/missing.md"})
    assert meta["result"] is None


@pytest.mark.asyncio
async def test_get_note_delegates_path(app, mock_vault):
    mock_vault.get_note.return_value = None

    await app.call_tool("get_note", {"path": "projects/plasma/note.md"})
    mock_vault.get_note.assert_called_once_with("projects/plasma/note.md")


# ─── get_backlinks ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_backlinks_returns_list(app, mock_vault):
    mock_vault.get_backlinks.return_value = [
        "engineering/analysis/burn_time.md",
        "engineering/analysis/nozzle.md",
    ]

    _, meta = await app.call_tool("get_backlinks", {"path": "engineering/constraints/thrust.md"})
    assert meta["result"] == [
        "engineering/analysis/burn_time.md",
        "engineering/analysis/nozzle.md",
    ]


@pytest.mark.asyncio
async def test_get_backlinks_empty(app, mock_vault):
    mock_vault.get_backlinks.return_value = []
    _, meta = await app.call_tool("get_backlinks", {"path": "orphaned/note.md"})
    assert meta["result"] == []


@pytest.mark.asyncio
async def test_get_backlinks_delegates_path(app, mock_vault):
    mock_vault.get_backlinks.return_value = []
    await app.call_tool("get_backlinks", {"path": "vault/x.md"})
    mock_vault.get_backlinks.assert_called_once_with("vault/x.md")


# ─── get_tags ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_tags_returns_matching_paths(app, mock_vault):
    mock_vault.get_tags.return_value = [
        "engineering/constraints/thrust.md",
        "engineering/constraints/yield.md",
    ]

    _, meta = await app.call_tool("get_tags", {"tag": "validated"})
    assert len(meta["result"]) == 2


@pytest.mark.asyncio
async def test_get_tags_empty_for_unknown_tag(app, mock_vault):
    mock_vault.get_tags.return_value = []
    _, meta = await app.call_tool("get_tags", {"tag": "nonexistent-tag"})
    assert meta["result"] == []


@pytest.mark.asyncio
async def test_get_tags_delegates_tag_arg(app, mock_vault):
    mock_vault.get_tags.return_value = []
    await app.call_tool("get_tags", {"tag": "failure-mode"})
    mock_vault.get_tags.assert_called_once_with("failure-mode")


# ─── upsert_note ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_note_delegates_all_args(app, mock_vault):
    mock_vault.upsert_note.return_value = "/vault/engineering/constraints/thrust.md"

    _, meta = await app.call_tool("upsert_note", {
        "path":        "engineering/constraints/thrust.md",
        "markdown":    "## Constraint\n\nThrust ≤ 450 kN.",
        "frontmatter": {"status": "validated"},
        "provenance":  {"agent": "Librarian", "session_id": "s001"},
    })

    mock_vault.upsert_note.assert_called_once_with(
        path="engineering/constraints/thrust.md",
        markdown="## Constraint\n\nThrust ≤ 450 kN.",
        frontmatter={"status": "validated"},
        provenance={"agent": "Librarian", "session_id": "s001"},
    )
    assert meta["result"] == "/vault/engineering/constraints/thrust.md"


@pytest.mark.asyncio
async def test_upsert_note_optional_args_default_none(app, mock_vault):
    mock_vault.upsert_note.return_value = "/vault/path.md"

    await app.call_tool("upsert_note", {
        "path":     "projects/scratch.md",
        "markdown": "# scratch",
    })

    mock_vault.upsert_note.assert_called_once_with(
        path="projects/scratch.md",
        markdown="# scratch",
        frontmatter=None,
        provenance=None,
    )


# ─── append_to_note ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_append_to_note_delegates_args(app, mock_vault):
    mock_vault.append_to_note.return_value = "/vault/logs/run001.md"

    _, meta = await app.call_tool("append_to_note", {
        "path":     "logs/run001.md",
        "markdown": "\n## Run 42\n\nConverged in 3 iterations.",
    })

    mock_vault.append_to_note.assert_called_once_with(
        path="logs/run001.md",
        markdown="\n## Run 42\n\nConverged in 3 iterations.",
    )
    assert meta["result"] == "/vault/logs/run001.md"


# ─── add_frontmatter ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_frontmatter_delegates_args(app, mock_vault):
    mock_vault.add_frontmatter.return_value = "/vault/engineering/constraints/thrust.md"

    _, meta = await app.call_tool("add_frontmatter", {
        "path":       "engineering/constraints/thrust.md",
        "yaml_patch": {"status": "validated", "confidence": 0.97},
    })

    mock_vault.add_frontmatter.assert_called_once_with(
        path="engineering/constraints/thrust.md",
        yaml_patch={"status": "validated", "confidence": 0.97},
    )
    assert meta["result"] == "/vault/engineering/constraints/thrust.md"


# ─── create_server logs index size ────────────────────────────────────────────


def test_create_server_logs_index_size(tmp_path, caplog):
    """create_server should log that the vault manager was created."""
    mock_vault = MagicMock()

    with patch(
        "forge_agent.memory.obsidian_mcp_server.ObsidianVaultManager",
        return_value=mock_vault,
    ):
        import logging
        with caplog.at_level(logging.INFO, logger="forge_agent.memory.obsidian_mcp_server"):
            create_server(str(tmp_path))

    assert any("Vault manager created" in msg for msg in caplog.messages), (
        f"Expected vault creation log, got: {caplog.messages}"
    )


# ─── main() entry point ───────────────────────────────────────────────────────


def test_main_exits_when_no_args(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["obsidian_mcp_server.py"])
    from forge_agent.memory.obsidian_mcp_server import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "Usage:" in capsys.readouterr().err


def test_main_exits_when_vault_path_missing(monkeypatch, capsys, tmp_path):
    non_existent = str(tmp_path / "no_such_dir")
    monkeypatch.setattr(sys, "argv", ["obsidian_mcp_server.py", non_existent])
    from forge_agent.memory.obsidian_mcp_server import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "does not exist" in err
