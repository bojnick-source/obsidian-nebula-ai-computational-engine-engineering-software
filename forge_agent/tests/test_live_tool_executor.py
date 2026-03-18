"""
forge_agent/tests/test_live_tool_executor.py

Unit tests for LiveToolExecutor.

In CI (gmsh not installed, ccx not on PATH), all tool calls return
error_envelope with status="degraded" and error_code="ERR_TOOL_SUBPROCESS_FAIL".
"""
import uuid

import pytest

from forge_agent.core.live_tool_executor import LiveToolExecutor

SCHEMA = "forge/mcp/response/v1"


@pytest.fixture()
def executor():
    return LiveToolExecutor()


@pytest.fixture()
def ids():
    return {
        "trace_id": str(uuid.uuid4()),
        "task_id": "test-task-001",
        "invocation_id": str(uuid.uuid4()),
    }


# ---------------------------------------------------------------------------
# GMSH tests
# ---------------------------------------------------------------------------


def test_run_gmsh_returns_full_schema_envelope(executor, ids):
    result = executor.run_gmsh(**ids)
    assert result["$schema"] == SCHEMA


def test_run_gmsh_absent_returns_error_envelope(executor, ids):
    """When gmsh is not installed, status must be 'degraded' (not 'error')."""
    result = executor.run_gmsh(**ids)
    # status must be one of {"degraded", "success"} — never "error" or None
    assert result["status"] in {"degraded", "success"}
    if result["status"] == "degraded":
        assert result["error_code"] == "ERR_TOOL_SUBPROCESS_FAIL"


def test_run_gmsh_propagates_trace_id(executor, ids):
    result = executor.run_gmsh(**ids)
    assert result["trace_id"] == ids["trace_id"]


def test_run_gmsh_propagates_invocation_id(executor, ids):
    result = executor.run_gmsh(**ids)
    assert result["invocation_id"] == ids["invocation_id"]


def test_run_gmsh_task_id_in_metadata(executor, ids):
    """task_id must NOT be silently dropped (P2 guard)."""
    result = executor.run_gmsh(**ids)
    assert result["metadata"]["task_id"] == ids["task_id"]


# ---------------------------------------------------------------------------
# CalculiX tests
# ---------------------------------------------------------------------------


def test_run_calculix_returns_full_schema_envelope(executor, ids):
    result = executor.run_calculix(**ids)
    assert result["$schema"] == SCHEMA


def test_run_calculix_absent_returns_error_envelope(executor, ids):
    """When ccx is not on PATH, status must be 'degraded' (not 'error')."""
    result = executor.run_calculix(**ids)
    assert result["status"] in {"degraded", "success"}
    if result["status"] == "degraded":
        assert result["error_code"] == "ERR_TOOL_SUBPROCESS_FAIL"


def test_run_calculix_propagates_trace_id(executor, ids):
    result = executor.run_calculix(**ids)
    assert result["trace_id"] == ids["trace_id"]


def test_run_calculix_propagates_invocation_id(executor, ids):
    result = executor.run_calculix(**ids)
    assert result["invocation_id"] == ids["invocation_id"]


def test_run_calculix_task_id_in_metadata(executor, ids):
    result = executor.run_calculix(**ids)
    assert result["metadata"]["task_id"] == ids["task_id"]


# ---------------------------------------------------------------------------
# Shared envelope shape tests
# ---------------------------------------------------------------------------


def test_envelope_has_tool_id_and_wrapper_version_gmsh(executor, ids):
    result = executor.run_gmsh(**ids)
    assert result["tool_id"] == "gmsh"
    assert result["wrapper_version"] == "1.0.0"


def test_envelope_has_tool_id_and_wrapper_version_ccx(executor, ids):
    result = executor.run_calculix(**ids)
    assert result["tool_id"] == "calculix"
    assert result["wrapper_version"] == "1.0.0"


def test_envelope_has_timestamp_and_duration(executor, ids):
    result_gmsh = executor.run_gmsh(**ids)
    result_ccx = executor.run_calculix(**ids)
    for result in (result_gmsh, result_ccx):
        assert "timestamp" in result
        assert isinstance(result["duration_ms"], int)
        assert result["duration_ms"] >= 0


def test_run_gmsh_auto_generates_invocation_id_when_missing(executor):
    """If invocation_id is omitted, executor must not crash and must fill the field."""
    trace_id = str(uuid.uuid4())
    result = executor.run_gmsh(trace_id=trace_id, task_id="t1")
    assert result["invocation_id"] != ""


def test_run_calculix_auto_generates_invocation_id_when_missing(executor):
    trace_id = str(uuid.uuid4())
    result = executor.run_calculix(trace_id=trace_id, task_id="t1")
    assert result["invocation_id"] != ""
