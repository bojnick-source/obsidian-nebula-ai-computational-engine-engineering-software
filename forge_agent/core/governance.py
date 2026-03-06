"""
forge_agent/core/governance.py

FIXES APPLIED:

1. Authorization check FIRST — record_provenance() only called on authorized writes.
   Previously: provenance was recorded even for writes that were then blocked,
   creating misleading audit logs of "successful" writes that never happened.

2. hashlib.sha256() for sensitive path hashing.
   Previously: hashlib.md5() used everywhere.
   MD5 is trivially collision-exploitable (Flame malware used it in production).
   SHA-256 is required for verification/ and engineering/constraints/ paths.
   MD5 kept for cheap content-addressed cache keys where collision is not a
   security concern (non-sensitive notes in projects/ and patterns/).
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Write permission matrix ───────────────────────────────────────────────────
#
# Keys: agent roles (must match role strings in model_router.yaml)
# Values: set of vault path prefixes the agent is allowed to write to
#
# Rule: a write is authorized if and only if:
#   the path starts with one of the agent's permitted prefixes.

WRITE_PERMISSIONS: dict[str, set[str]] = {
    "Librarian":     {"vault/"},                      # full vault write
    "Orchestrator":  {"vault/", "blackboard/"},
    "Verifier":      {"vault/verification/",           # stamp validated or disputed ONLY
                      "vault/engineering/constraints/"},
    # All specialist agents write to blackboard only — never directly to vault
    "ME":            {"blackboard/"},
    "EE":            {"blackboard/"},
    "SE":            {"blackboard/"},
    "Controls":      {"blackboard/"},
    "Thermal":       {"blackboard/"},
    "Materials":     {"blackboard/"},
    "Manufacturing": {"blackboard/"},
    "Safety":        {"blackboard/"},
    "Acoustics":     {"blackboard/"},
    "NumericalMethods": {"blackboard/"},
    "Plasma":        {"blackboard/"},
    # Math agents
    "Math_Symbolic":          {"blackboard/"},
    "Math_Optimization":      {"blackboard/"},
    "Math_PDE":               {"blackboard/"},
    "Math_NumericalAnalysis": {"blackboard/"},
    "Math_Geometry":          {"blackboard/"},
    "Math_Probability":       {"blackboard/"},
    "MathSynthesizer":        {"blackboard/"},
    # PTC engine writes to container scratch space only; Librarian promotes post-run
    "PTCEngine":     {"container/"},
}

# ── Paths that require SHA-256 (not MD5) ─────────────────────────────────────
#
# Collision-resistant hashing mandatory for:
#   - Verification records (integrity proofs)
#   - Engineering constraints (safety-critical, immutable once validated)
#
# All other paths may use MD5 for cache-key cheapness.

SHA256_REQUIRED_PREFIXES = (
    "vault/verification/",
    "vault/engineering/constraints/",
)


def _requires_sha256(normalized_path: str) -> bool:
    return any(normalized_path.startswith(p) for p in SHA256_REQUIRED_PREFIXES)


def _content_hash(content: str, path: str) -> str:
    """
    FIX 2: Return SHA-256 hex digest for sensitive paths, MD5 for others.
    """
    content_bytes = content.encode("utf-8")
    if _requires_sha256(path):
        return hashlib.sha256(content_bytes).hexdigest()
    else:
        return hashlib.md5(content_bytes).hexdigest()  # noqa: S324 — intentional, non-sensitive


# ── Core governance function ──────────────────────────────────────────────────


def authorized_vault_write(
    agent: str,
    path: str,
    content: str,
    session_id: str,
    model: str,
    iteration: int = 0,
    provenance_log_path: str | None = None,
) -> tuple[bool, str | None]:
    """
    Gate all vault writes through authorization + provenance.

    FIX 1: Authorization check happens FIRST.
    record_provenance() is ONLY called after authorization succeeds.

    Previously the code called record_provenance() before checking
    authorization, meaning blocked writes appeared in audit logs as
    successful. A blocked write must never appear in the provenance log.

    Args:
        agent:              Role key from WRITE_PERMISSIONS
        path:               Vault-relative path being written
        content:            Content being written (for hash)
        session_id:         Unique session identifier
        model:              Model string that produced the content
        iteration:          Which solve iteration this comes from
        provenance_log_path: Where to append provenance records (JSONL)

    Returns:
        (True, provenance_id)   — authorized and logged
        (False, reason_string)  — rejected, not logged
    """
    # ── STEP 1: Authorization check ───────────────────────────────────────────
    # This is now unconditionally first. Nothing else runs until this passes.

    normalized_path = _normalize_path(path)
    permitted_prefixes = WRITE_PERMISSIONS.get(agent, set())

    is_authorized = any(
        normalized_path.startswith(prefix)
        for prefix in permitted_prefixes
    )

    if not is_authorized:
        reason = (
            f"Agent '{agent}' is not authorized to write to '{normalized_path}'. "
            f"Permitted prefixes: {sorted(permitted_prefixes) or 'none'}."
        )
        logger.warning("WRITE BLOCKED: %s", reason)
        # Do NOT call record_provenance here — blocked writes are not logged
        return False, reason

    # ── STEP 2: Extra check for sensitive paths ───────────────────────────────
    # Verifier may write to verification/ and engineering/constraints/ but
    # no other agent may, even if they somehow pass the prefix check above.

    is_sensitive = _requires_sha256(normalized_path)
    verifier_only_agents = {"Verifier", "Librarian"}  # Librarian has full vault

    if is_sensitive and agent not in verifier_only_agents:
        reason = (
            f"Agent '{agent}' attempted to write to sensitive path '{normalized_path}'. "
            f"Only Verifier and Librarian may write to verification/ or "
            f"engineering/constraints/ paths."
        )
        logger.warning("WRITE BLOCKED (sensitive path): %s", reason)
        return False, reason

    # ── STEP 3: Record provenance ─────────────────────────────────────────────
    # Only reached if BOTH authorization checks above passed.
    # FIX 2: Use sha256 for sensitive paths, md5 for others.

    content_hash = _content_hash(content, normalized_path)

    provenance_record = {
        "provenance_id":  _generate_provenance_id(session_id, normalized_path),
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "agent":          agent,
        "model":          model,
        "session_id":     session_id,
        "iteration":      iteration,
        "path":           normalized_path,
        "hash_algorithm": "sha256" if _requires_sha256(normalized_path) else "md5",
        "content_hash":   content_hash,
        "content_length": len(content),
    }

    _append_provenance(provenance_record, provenance_log_path)

    logger.debug(
        "WRITE AUTHORIZED: agent=%s path=%s hash_algo=%s hash=%s",
        agent, normalized_path,
        provenance_record["hash_algorithm"],
        content_hash[:16] + "…",
    )

    return True, provenance_record["provenance_id"]


# ── Verification record ───────────────────────────────────────────────────────


def record_verification(
    path: str,
    verdict: str,               # "PASS" | "REJECT"
    confidence: float,
    violations: list[dict],
    session_id: str,
    model: str,
    provenance_log_path: str | None = None,
) -> str:
    """
    Write a verification record to the provenance log.

    Uses SHA-256 unconditionally — verification records are integrity-sensitive.
    This function does not check write permission because it writes to the log
    only, not to the vault itself. Vault stamping is done via authorized_vault_write().

    Returns provenance_id of the verification record.
    """
    record_content = json.dumps({
        "path": path,
        "verdict": verdict,
        "confidence": confidence,
        "violations": violations,
    }, sort_keys=True)

    # Verification records always use SHA-256 regardless of path
    content_hash = hashlib.sha256(record_content.encode()).hexdigest()

    record = {
        "provenance_id":  _generate_provenance_id(session_id, f"verification:{path}"),
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        "type":           "verification",
        "agent":          "Verifier",
        "model":          model,
        "session_id":     session_id,
        "path":           path,
        "verdict":        verdict,
        "confidence":     confidence,
        "violations":     violations,
        "hash_algorithm": "sha256",
        "content_hash":   content_hash,
    }

    _append_provenance(record, provenance_log_path)
    return record["provenance_id"]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _normalize_path(path: str) -> str:
    """
    Normalize vault-relative paths to a canonical form.
    Ensures 'vault/engineering/constraints/x.md' and
    'engineering/constraints/x.md' both resolve correctly.
    """
    p = path.strip().lstrip("/")
    special_namespaces = ("blackboard/", "container/", "vault/")
    if not any(p.startswith(ns) for ns in special_namespaces):
        p = "vault/" + p
    return p


def _generate_provenance_id(session_id: str, path: str) -> str:
    """Short, stable, collision-resistant ID for a provenance entry."""
    raw = f"{session_id}:{path}:{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _append_provenance(record: dict, log_path: str | None) -> None:
    """Append a provenance record as JSONL."""
    line = json.dumps(record, ensure_ascii=False) + "\n"

    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    else:
        # Fallback: emit to structured log (captured by AgentLogger)
        logger.info("PROVENANCE: %s", line.rstrip())
