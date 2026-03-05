"""Tests for VaultWriter."""

from __future__ import annotations

from pathlib import Path

import frontmatter
import pytest

from forge_output.vault.writer import VaultWriter


@pytest.fixture()
def vault(tmp_path: Path) -> VaultWriter:
    return VaultWriter(vault_root=tmp_path)


def test_write_finding_note(vault: VaultWriter, tmp_path: Path):
    path = vault.write_note(
        note_type="finding",
        title="Max stress under motor mount load",
        body="The maximum von Mises stress is 45 MPa at the fillet radius.",
        metadata={
            "provenance": "CalculiX 2.21 output",
            "confidence": 0.9,
            "tags": ["fea", "aladdin-3b"],
        },
        run_id="run-0001",
        trace_id="00000000-0000-4000-8000-000000000001",
        agent_id="me_specialist",
        quality_score=0.92,
    )
    assert path.exists()
    post = frontmatter.load(str(path))
    assert post["note_type"] == "finding"
    assert post["confidence"] == 0.9
    assert post["quality_score"] == 0.92
    assert "fea" in post["tags"]


def test_slug_generation(vault: VaultWriter, tmp_path: Path):
    path = vault.write_note(
        note_type="gap",
        title="Missing fatigue data for 4130 steel at -40°C",
        body="Gap in material data library.",
        metadata={},
        run_id="run-0002",
        trace_id="00000000-0000-4000-8000-000000000002",
        agent_id="librarian",
    )
    # Slug should be URL-safe
    assert " " not in path.stem
    assert "°" not in path.stem


def test_vault_directory_created(tmp_path: Path):
    nested = tmp_path / "nested" / "vault"
    writer = VaultWriter(vault_root=nested)
    writer.write_note(
        note_type="finding",
        title="Test note",
        body="body",
        metadata={},
        run_id="r1",
        trace_id="t1",
        agent_id="a1",
    )
    assert nested.exists()
