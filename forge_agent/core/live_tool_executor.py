"""
forge_agent/core/live_tool_executor.py

LiveToolExecutor — exercises real Python code paths for GMSH and CalculiX,
including ImportError / PATH checks from the MCP wrapper modules.

Returns full MCP Wrapper Envelope v1 dicts (via error_envelope /
success_envelope from _envelope.py) in all cases, including when tools are
absent from the CI environment.

CRITICAL: absent-tool paths return status="degraded" (not status="error") so
that PipelineRunner._run_phase_tool_execution() (pipeline.py line 437) sets
blackboard["tool_execution.degraded"] = True and TaskResult.status becomes
"degraded". Using status="error" would silently suppress degraded-mode
detection.
"""
from __future__ import annotations

import shutil
import time
import uuid

from forge_agent.mcp_wrappers._envelope import error_envelope, success_envelope

TOOL_ID_GMSH = "gmsh"
TOOL_ID_CCX = "calculix"
WRAPPER_VERSION = "1.0.0"


class LiveToolExecutor:
    """
    Executes tool code paths directly (no MCP network/subprocess transport).

    Both methods return a full MCP Wrapper Envelope v1 dict. When tools are
    absent, the envelope carries status="degraded" and
    error_code="ERR_TOOL_SUBPROCESS_FAIL" so the pipeline correctly marks the
    run as degraded.
    """

    def run_gmsh(
        self,
        trace_id: str = "",
        task_id: str = "",
        invocation_id: str = "",
        geo_file: str = "",
        **kwargs,
    ) -> dict:
        """
        Attempt to import gmsh and run a mesh generation.

        Returns a full MCP envelope. When gmsh is not importable or geo_file
        does not exist, returns error_envelope with status="degraded".

        task_id is written to metadata so it is never silently dropped (P2).
        """
        if not invocation_id:
            invocation_id = str(uuid.uuid4())

        t0 = time.monotonic()

        # Attempt to import gmsh (real code path check)
        try:
            import gmsh  # noqa: F401 (intentional import probe)
            gmsh_available = True
        except ImportError:
            gmsh_available = False

        if not gmsh_available:
            duration_ms = (time.monotonic() - t0) * 1000
            env = error_envelope(
                TOOL_ID_GMSH,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                "gmsh Python package not importable in this environment",
                duration_ms,
                status="degraded",
            )
            env["metadata"]["task_id"] = task_id
            return env

        # gmsh is available — check geo_file
        from pathlib import Path

        if not geo_file or not Path(geo_file).exists():
            duration_ms = (time.monotonic() - t0) * 1000
            env = error_envelope(
                TOOL_ID_GMSH,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"geo_file not found or empty: {geo_file!r}",
                duration_ms,
                status="degraded",
            )
            env["metadata"]["task_id"] = task_id
            return env

        # gmsh available and file exists — run mesh generation
        import gmsh  # noqa: F811

        mesh_file = str(Path(geo_file).with_suffix(".msh"))
        try:
            gmsh.initialize()
            gmsh.merge(geo_file)
            gmsh.model.mesh.generate(3)
            gmsh.write(mesh_file)
            duration_ms = (time.monotonic() - t0) * 1000
            env = success_envelope(
                TOOL_ID_GMSH,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                output={"mesh_file": mesh_file},
                duration_ms=duration_ms,
            )
            env["metadata"]["task_id"] = task_id
            return env
        except Exception as exc:
            duration_ms = (time.monotonic() - t0) * 1000
            env = error_envelope(
                TOOL_ID_GMSH,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                str(exc),
                duration_ms,
                status="degraded",
            )
            env["metadata"]["task_id"] = task_id
            return env
        finally:
            try:
                gmsh.finalize()
            except Exception:
                pass

    def run_calculix(
        self,
        trace_id: str = "",
        task_id: str = "",
        invocation_id: str = "",
        input_file: str = "",
        **kwargs,
    ) -> dict:
        """
        Attempt to locate and run the CalculiX ccx binary.

        Returns a full MCP envelope. When ccx is not on PATH or input_file
        does not exist, returns error_envelope with status="degraded".

        task_id is written to metadata so it is never silently dropped (P2).
        """
        if not invocation_id:
            invocation_id = str(uuid.uuid4())

        t0 = time.monotonic()

        # Check for ccx binary on PATH (real code path check)
        ccx_binary = shutil.which("ccx") or shutil.which("ccx_2.22")

        if ccx_binary is None:
            duration_ms = (time.monotonic() - t0) * 1000
            env = error_envelope(
                TOOL_ID_CCX,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                "ccx / ccx_2.22 not found on PATH",
                duration_ms,
                status="degraded",
            )
            env["metadata"]["task_id"] = task_id
            return env

        # ccx available — check input_file
        from pathlib import Path

        if not input_file or not Path(input_file).exists():
            duration_ms = (time.monotonic() - t0) * 1000
            env = error_envelope(
                TOOL_ID_CCX,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"input_file not found or empty: {input_file!r}",
                duration_ms,
                status="degraded",
            )
            env["metadata"]["task_id"] = task_id
            return env

        # ccx available and file exists — run the solver
        import asyncio

        async def _run_ccx() -> tuple[int, str, str]:
            proc = await asyncio.create_subprocess_exec(
                ccx_binary,
                "-i",
                input_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await proc.communicate()
            return (
                proc.returncode or 0,
                stdout_bytes.decode(errors="replace"),
                stderr_bytes.decode(errors="replace"),
            )

        try:
            exit_code, stdout, stderr = asyncio.run(_run_ccx())
            duration_ms = (time.monotonic() - t0) * 1000
            if exit_code != 0:
                env = error_envelope(
                    TOOL_ID_CCX,
                    WRAPPER_VERSION,
                    trace_id,
                    invocation_id,
                    "ERR_TOOL_SUBPROCESS_FAIL",
                    stderr[:500] if stderr else f"ccx exited with code {exit_code}",
                    duration_ms,
                    status="degraded",
                    exit_code=exit_code,
                )
                env["metadata"]["task_id"] = task_id
                return env
            env = success_envelope(
                TOOL_ID_CCX,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                output={"stdout": stdout[:500]},
                duration_ms=duration_ms,
                exit_code=exit_code,
            )
            env["metadata"]["task_id"] = task_id
            return env
        except Exception as exc:
            duration_ms = (time.monotonic() - t0) * 1000
            env = error_envelope(
                TOOL_ID_CCX,
                WRAPPER_VERSION,
                trace_id,
                invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                str(exc),
                duration_ms,
                status="degraded",
            )
            env["metadata"]["task_id"] = task_id
            return env

    def run_gmsh_subprocess(
        self,
        trace_id: str = "",
        task_id: str = "",
        invocation_id: str = "",
        geo_file: str = "",
        **kwargs,
    ) -> dict:
        """Alias kept for forward-compatibility. Delegates to run_gmsh."""
        return self.run_gmsh(
            trace_id=trace_id,
            task_id=task_id,
            invocation_id=invocation_id,
            geo_file=geo_file,
            **kwargs,
        )
