"""Tests for ObsidianVaultManager read/write/search roundtrip."""
import asyncio
import pytest
import tempfile
from pathlib import Path

from forge_agent.memory.obsidian_manager import ObsidianVaultManager, _slug, _tokenize


@pytest.fixture
def tmp_vault(tmp_path):
    return tmp_path / "vault"


@pytest.mark.asyncio
async def test_write_and_read_note(tmp_vault):
    vm = ObsidianVaultManager(vault_path=tmp_vault)
    await vm.start()

    note_path = await vm.write_note(
        title="Test Stress Analysis",
        content="Von Mises stress σ = 250 MPa at fillet radius.",
        frontmatter={"type": "derivation", "problem_id": "TEST-001"},
    )
    await vm.flush()

    assert note_path.exists()
    content = await vm.read_note("Test Stress Analysis")
    assert "Von Mises" in content
    await vm.stop()


@pytest.mark.asyncio
async def test_search_returns_relevant_note(tmp_vault):
    vm = ObsidianVaultManager(vault_path=tmp_vault)
    await vm.start()

    await vm.write_note("FEA Convergence Study", "Mesh convergence for finite element analysis stress")
    await vm.write_note("CFD Pressure Drop", "Navier-Stokes flow pressure drop pipe")
    await vm.flush()

    # Force re-index
    vm._indexed = False
    await vm._ensure_indexed()

    results = await vm.search("finite element stress analysis", top_k=3)
    assert len(results) > 0
    titles = [r["title"] for r in results]
    assert any("FEA" in t or "Convergence" in t or "finite" in t.lower() for t in titles)
    await vm.stop()


@pytest.mark.asyncio
async def test_write_creates_correct_frontmatter(tmp_vault):
    vm = ObsidianVaultManager(vault_path=tmp_vault)
    await vm.start()

    path = await vm.write_note(
        "Decision Log 001",
        "We chose Al 7075 over Ti-6Al-4V for cost reasons.",
        frontmatter={"type": "decision", "problem_id": "PROB-001"},
    )
    await vm.flush()

    raw = path.read_text()
    assert "type:" in raw
    assert "decision" in raw
    assert "Al 7075" in raw
    await vm.stop()


@pytest.mark.asyncio
async def test_empty_vault_search_returns_empty(tmp_vault):
    vm = ObsidianVaultManager(vault_path=tmp_vault)
    await vm.start()
    results = await vm.search("stress analysis")
    assert results == []
    await vm.stop()


def test_slug_helper():
    assert _slug("Test Note 123") == "test_note_123"
    assert _slug("FEA/CFD Analysis") == "fea_cfd_analysis"


def test_tokenize_helper():
    tokens = _tokenize("Von Mises stress 250 MPa")
    assert "von" in tokens
    assert "mises" in tokens
    assert "stress" in tokens
    assert "250" in tokens
