"""
Tests for forge_agent/core/governance.py — covers both fixes:
  FIX 1: Authorization check before provenance recording
  FIX 2: SHA-256 for sensitive paths, MD5 for non-sensitive paths
"""

import hashlib
import json
from pathlib import Path


from forge_agent.core.governance import (
    WRITE_PERMISSIONS,
    _content_hash,
    _normalize_path,
    _requires_sha256,
    authorized_vault_write,
    record_verification,
)

SESSION = "test-session-abc"
MODEL = "claude-opus-4-6"


# ─── FIX 1: Authorization order ───────────────────────────────────────────────


class TestAuthorizationCheckFirst:
    def test_authorized_write_returns_true_and_provenance_id(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        ok, prov_id = authorized_vault_write(
            agent="Librarian",
            path="vault/projects/test.md",
            content="# Test",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        assert ok is True
        assert prov_id is not None
        assert len(prov_id) == 24

    def test_authorized_write_appends_to_provenance_log(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        authorized_vault_write(
            agent="Librarian",
            path="vault/projects/test.md",
            content="# Test",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        lines = Path(log).read_text().strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["agent"] == "Librarian"
        assert record["path"] == "vault/projects/test.md"

    def test_blocked_write_returns_false_with_reason(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        ok, reason = authorized_vault_write(
            agent="ME",           # ME can only write blackboard/
            path="vault/projects/me_note.md",
            content="injected",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        assert ok is False
        assert "not authorized" in reason
        assert "ME" in reason

    def test_blocked_write_does_not_appear_in_provenance_log(self, tmp_path):
        """FIX 1 core assertion: blocked writes must not be logged."""
        log = str(tmp_path / "prov.jsonl")
        authorized_vault_write(
            agent="ME",
            path="vault/projects/me_note.md",
            content="injected",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        # Log file should not exist (no writes occurred)
        assert not Path(log).exists()

    def test_blocked_then_authorized_only_logs_authorized(self, tmp_path):
        """Blocked write followed by authorized write — log has exactly 1 entry."""
        log = str(tmp_path / "prov.jsonl")
        # Blocked
        authorized_vault_write(
            agent="PTCEngine",
            path="vault/projects/not_allowed.md",
            content="bad",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        # Authorized
        authorized_vault_write(
            agent="Orchestrator",
            path="blackboard/run001.json",
            content="{}",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        lines = Path(log).read_text().strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["agent"] == "Orchestrator"

    def test_unknown_agent_is_blocked(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        ok, reason = authorized_vault_write(
            agent="ShadowAgent",
            path="vault/projects/x.md",
            content="x",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        assert ok is False
        assert not Path(log).exists()

    def test_sensitive_path_blocked_for_non_verifier(self, tmp_path):
        """Orchestrator has vault/ prefix but must be blocked on verification/ paths."""
        log = str(tmp_path / "prov.jsonl")
        ok, reason = authorized_vault_write(
            agent="Orchestrator",
            path="vault/verification/stamp.json",
            content="{}",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        assert ok is False
        assert "sensitive path" in reason
        assert not Path(log).exists()

    def test_sensitive_path_allowed_for_verifier(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        ok, prov_id = authorized_vault_write(
            agent="Verifier",
            path="vault/verification/stamp.json",
            content='{"verdict": "PASS"}',
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        assert ok is True
        assert prov_id is not None

    def test_sensitive_path_allowed_for_librarian(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        ok, _ = authorized_vault_write(
            agent="Librarian",
            path="vault/engineering/constraints/yield_stress.md",
            content="# Yield stress constraint",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        assert ok is True

    def test_provenance_record_has_all_required_fields(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        authorized_vault_write(
            agent="Orchestrator",
            path="blackboard/run.json",
            content='{"k": "v"}',
            session_id=SESSION,
            model=MODEL,
            iteration=3,
            provenance_log_path=log,
        )
        record = json.loads(Path(log).read_text().strip())
        for field in (
            "provenance_id", "timestamp", "agent", "model",
            "session_id", "iteration", "path",
            "hash_algorithm", "content_hash", "content_length",
        ):
            assert field in record, f"Missing field: {field}"
        assert record["iteration"] == 3


# ─── FIX 2: Hash algorithm selection ─────────────────────────────────────────


class TestHashAlgorithmSelection:
    def test_verification_path_uses_sha256(self):
        h = _content_hash("some content", "vault/verification/stamp.json")
        assert len(h) == 64   # SHA-256 hex = 64 chars
        assert h == hashlib.sha256(b"some content").hexdigest()

    def test_constraints_path_uses_sha256(self):
        h = _content_hash("constraint body", "vault/engineering/constraints/x.md")
        assert len(h) == 64
        assert h == hashlib.sha256(b"constraint body").hexdigest()

    def test_normal_vault_path_uses_md5(self):
        h = _content_hash("note body", "vault/projects/note.md")
        assert len(h) == 32   # MD5 hex = 32 chars
        assert h == hashlib.md5(b"note body").hexdigest()

    def test_blackboard_path_uses_md5(self):
        h = _content_hash("{}", "blackboard/run001.json")
        assert len(h) == 32

    def test_requires_sha256_verification(self):
        assert _requires_sha256("vault/verification/x.json") is True

    def test_requires_sha256_constraints(self):
        assert _requires_sha256("vault/engineering/constraints/y.md") is True

    def test_requires_sha256_false_for_projects(self):
        assert _requires_sha256("vault/projects/note.md") is False

    def test_requires_sha256_false_for_blackboard(self):
        assert _requires_sha256("blackboard/run.json") is False

    def test_authorized_write_records_correct_algorithm_sha256(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        authorized_vault_write(
            agent="Verifier",
            path="vault/verification/stamp.json",
            content='{"verdict": "PASS"}',
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        record = json.loads(Path(log).read_text().strip())
        assert record["hash_algorithm"] == "sha256"
        assert len(record["content_hash"]) == 64

    def test_authorized_write_records_correct_algorithm_md5(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        authorized_vault_write(
            agent="Librarian",
            path="vault/projects/ordinary.md",
            content="# ordinary note",
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        record = json.loads(Path(log).read_text().strip())
        assert record["hash_algorithm"] == "md5"
        assert len(record["content_hash"]) == 32


# ─── Path normalization ────────────────────────────────────────────────────────


class TestNormalizePath:
    def test_vault_prefix_preserved(self):
        assert _normalize_path("vault/projects/x.md") == "vault/projects/x.md"

    def test_blackboard_prefix_preserved(self):
        assert _normalize_path("blackboard/run.json") == "blackboard/run.json"

    def test_container_prefix_preserved(self):
        assert _normalize_path("container/scratch.py") == "container/scratch.py"

    def test_bare_path_gets_vault_prefix(self):
        assert _normalize_path("projects/x.md") == "vault/projects/x.md"

    def test_leading_slash_stripped(self):
        assert _normalize_path("/vault/projects/x.md") == "vault/projects/x.md"

    def test_whitespace_stripped(self):
        assert _normalize_path("  vault/projects/x.md  ") == "vault/projects/x.md"


# ─── record_verification ─────────────────────────────────────────────────────


class TestRecordVerification:
    def test_returns_provenance_id(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        prov_id = record_verification(
            path="vault/verification/r001.json",
            verdict="PASS",
            confidence=0.92,
            violations=[],
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        assert len(prov_id) == 24

    def test_always_uses_sha256(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        record_verification(
            path="vault/projects/ordinary.md",   # non-sensitive path
            verdict="PASS",
            confidence=0.9,
            violations=[],
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        record = json.loads(Path(log).read_text().strip())
        assert record["hash_algorithm"] == "sha256"
        assert len(record["content_hash"]) == 64

    def test_logs_verdict_and_confidence(self, tmp_path):
        log = str(tmp_path / "prov.jsonl")
        record_verification(
            path="vault/verification/r002.json",
            verdict="REJECT",
            confidence=0.3,
            violations=[{"field": "units", "detail": "missing SI"}],
            session_id=SESSION,
            model=MODEL,
            provenance_log_path=log,
        )
        record = json.loads(Path(log).read_text().strip())
        assert record["verdict"] == "REJECT"
        assert record["confidence"] == 0.3
        assert record["violations"][0]["field"] == "units"


# ─── Permission matrix sanity ─────────────────────────────────────────────────


class TestWritePermissionsMatrix:
    def test_all_specialist_agents_can_only_write_blackboard(self):
        specialists = [
            "ME", "EE", "SE", "Controls", "Thermal", "Materials",
            "Manufacturing", "Safety", "Acoustics", "NumericalMethods", "Plasma",
        ]
        for agent in specialists:
            perms = WRITE_PERMISSIONS[agent]
            assert perms == {"blackboard/"}, (
                f"{agent} should only have blackboard/ permission, got {perms}"
            )

    def test_all_math_agents_can_only_write_blackboard(self):
        math_agents = [
            "Math_Symbolic", "Math_Optimization", "Math_PDE",
            "Math_NumericalAnalysis", "Math_Geometry", "Math_Probability",
            "MathSynthesizer",
        ]
        for agent in math_agents:
            perms = WRITE_PERMISSIONS[agent]
            assert perms == {"blackboard/"}, (
                f"{agent} should only have blackboard/ permission, got {perms}"
            )

    def test_ptc_engine_can_only_write_container(self):
        assert WRITE_PERMISSIONS["PTCEngine"] == {"container/"}

    def test_verifier_cannot_write_arbitrary_vault(self):
        verifier_perms = WRITE_PERMISSIONS["Verifier"]
        assert "vault/" not in verifier_perms  # no unrestricted vault/ access

    def test_librarian_has_full_vault_access(self):
        assert "vault/" in WRITE_PERMISSIONS["Librarian"]
