"""Tests for OpenFOAM and SU2 MCP wrappers — plan 4-004 acceptance criteria."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from forge_agent.mcp_wrappers import openfoam_server, su2_server
from forge_agent.core.cli_dispatcher import CliDispatcher
from forge_agent.core.pipeline import DefaultToolExecutor


# ---------------------------------------------------------------------------
# AC 1 / AC 2: Both server modules return $schema == "forge/mcp/response/v1"
# ---------------------------------------------------------------------------


def test_openfoam_schema_when_binary_absent():
    """openfoam_server returns correct $schema even when binary is absent."""
    with patch("shutil.which", return_value=None):
        server = openfoam_server.create_server()
        # Call the tool function directly via the registered tool
        tool_fn = None
        for tool in server._tool_manager.list_tools():
            if tool.name == "run_openfoam":
                tool_fn = tool.fn
                break
        assert tool_fn is not None, "run_openfoam tool not registered"
        result = tool_fn(
            trace_id="t1",
            task_id="task-1",
            invocation_id="inv-1",
            case_dir="/tmp/case",
        )
    assert result.get("$schema") == "forge/mcp/response/v1"


def test_su2_schema_when_binary_absent():
    """su2_server returns correct $schema even when binary is absent."""
    with patch("shutil.which", return_value=None):
        server = su2_server.create_server()
        tool_fn = None
        for tool in server._tool_manager.list_tools():
            if tool.name == "run_su2":
                tool_fn = tool.fn
                break
        assert tool_fn is not None, "run_su2 tool not registered"
        result = tool_fn(
            trace_id="t1",
            task_id="task-2",
            invocation_id="inv-2",
            config_file="/tmp/case.cfg",
        )
    assert result.get("$schema") == "forge/mcp/response/v1"


# ---------------------------------------------------------------------------
# AC 3: openfoam_server returns status="degraded" + correct error_code
# ---------------------------------------------------------------------------


def test_openfoam_degraded_when_binary_absent():
    with patch("shutil.which", return_value=None):
        server = openfoam_server.create_server()
        tool_fn = next(
            t.fn for t in server._tool_manager.list_tools() if t.name == "run_openfoam"
        )
        result = tool_fn(
            trace_id="t1",
            task_id="task-3",
            invocation_id="inv-3",
            case_dir="/nonexistent",
        )
    assert result["status"] == "degraded"
    assert result["error_code"] == "ERR_TOOL_SUBPROCESS_FAIL"


# ---------------------------------------------------------------------------
# AC 4: su2_server returns status="degraded" + correct error_code
# ---------------------------------------------------------------------------


def test_su2_degraded_when_binary_absent():
    with patch("shutil.which", return_value=None):
        server = su2_server.create_server()
        tool_fn = next(
            t.fn for t in server._tool_manager.list_tools() if t.name == "run_su2"
        )
        result = tool_fn(
            trace_id="t1",
            task_id="task-4",
            invocation_id="inv-4",
            config_file="/nonexistent.cfg",
        )
    assert result["status"] == "degraded"
    assert result["error_code"] == "ERR_TOOL_SUBPROCESS_FAIL"


# ---------------------------------------------------------------------------
# AC 5: Both envelopes include task_id in metadata when provided
# ---------------------------------------------------------------------------


def test_openfoam_task_id_in_metadata():
    with patch("shutil.which", return_value=None):
        server = openfoam_server.create_server()
        tool_fn = next(
            t.fn for t in server._tool_manager.list_tools() if t.name == "run_openfoam"
        )
        result = tool_fn(
            trace_id="t1",
            task_id="my-task-id",
            invocation_id="inv-5",
            case_dir="/nonexistent",
        )
    assert result.get("metadata", {}).get("task_id") == "my-task-id"


def test_su2_task_id_in_metadata():
    with patch("shutil.which", return_value=None):
        server = su2_server.create_server()
        tool_fn = next(
            t.fn for t in server._tool_manager.list_tools() if t.name == "run_su2"
        )
        result = tool_fn(
            trace_id="t1",
            task_id="my-task-id",
            invocation_id="inv-6",
            config_file="/nonexistent.cfg",
        )
    assert result.get("metadata", {}).get("task_id") == "my-task-id"


# ---------------------------------------------------------------------------
# AC 6: DefaultToolExecutor.run_openfoam() and run_su2() return degraded
# ---------------------------------------------------------------------------


def test_executor_run_openfoam_degraded():
    executor = DefaultToolExecutor()
    with patch("shutil.which", return_value=None):
        result = executor.run_openfoam(
            trace_id="t1", task_id="task-7", invocation_id="inv-7"
        )
    assert result["status"] == "degraded"
    assert result["tool"] == "openfoam"


def test_executor_run_su2_degraded():
    executor = DefaultToolExecutor()
    with patch("shutil.which", return_value=None):
        result = executor.run_su2(
            trace_id="t1", task_id="task-8", invocation_id="inv-8"
        )
    assert result["status"] == "degraded"
    assert result["tool"] == "su2"


# ---------------------------------------------------------------------------
# AC 7: cli_dispatcher has registered handlers for "openfoam_run" and "su2_run"
# ---------------------------------------------------------------------------


def test_cli_dispatcher_has_openfoam_handler():
    dispatcher = CliDispatcher()
    assert "openfoam_run" in dispatcher.registered_tools(), (
        "openfoam_run handler not registered in CliDispatcher"
    )


def test_cli_dispatcher_has_su2_handler():
    dispatcher = CliDispatcher()
    assert "su2_run" in dispatcher.registered_tools(), (
        "su2_run handler not registered in CliDispatcher"
    )


# ---------------------------------------------------------------------------
# AC 8: CliDispatcher.call("openfoam_run", ...) returns (None, False) when absent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatcher_openfoam_no_binary_returns_none_false():
    dispatcher = CliDispatcher()
    with patch("shutil.which", return_value=None):
        result, handled = await dispatcher.call("openfoam_run", {"case_dir": "/tmp"})
    assert result is None
    assert handled is False


@pytest.mark.asyncio
async def test_dispatcher_su2_no_binary_returns_none_false():
    dispatcher = CliDispatcher()
    with patch("shutil.which", return_value=None):
        result, handled = await dispatcher.call("su2_run", {"config_file": "/tmp/c.cfg"})
    assert result is None
    assert handled is False
