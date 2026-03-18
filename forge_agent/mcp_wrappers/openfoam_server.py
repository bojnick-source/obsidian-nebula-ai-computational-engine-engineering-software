"""
forge_agent/mcp_wrappers/openfoam_server.py

OpenFOAM MCP wrapper — runs CFD cases via foamRun/simpleFoam and returns
results wrapped in the frozen MCP Wrapper Envelope Contract v1
(docs/contracts/mcp-wrapper-envelope.md).

Returns status="degraded" when OpenFOAM binaries are absent from PATH.

Entry point: python -m forge_agent.mcp_wrappers.openfoam_server
"""

from __future__ import annotations

import concurrent.futures
import logging
import re
import shutil
import subprocess
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from forge_agent.mcp_wrappers._envelope import error_envelope, sha256, success_envelope

logger = logging.getLogger(__name__)

TOOL_ID = "openfoam"
WRAPPER_VERSION = "1.0.0"

# Cache binary lookup — PATH doesn't change at runtime.
# Prefer foamRun (OpenFOAM v11+), fall back to simpleFoam.
_FOAM_BIN: str | None = shutil.which("foamRun") or shutil.which("simpleFoam")

# Precompiled residual pattern for log parsing.
_RESIDUAL_RE = re.compile(
    r"^(?:Solving for \w+,\s+)?Initial residual\s*=\s*([\d.eE+\-]+)",
    re.MULTILINE,
)
_CONVERGED_RE = re.compile(r"SIMPLE solution converged", re.IGNORECASE)


def _parse_log(log_text: str) -> tuple[float | None, bool]:
    """Return (final_residual, converged) from an OpenFOAM log."""
    matches = _RESIDUAL_RE.findall(log_text)
    final_residual: float | None = None
    if matches:
        try:
            final_residual = float(matches[-1])
        except ValueError:
            pass
    converged = bool(_CONVERGED_RE.search(log_text))
    return final_residual, converged


def create_server() -> FastMCP:
    app = FastMCP(
        name="openfoam-wrapper",
        instructions=(
            "OpenFOAM CFD solver wrapper. "
            "Use run_openfoam with an OpenFOAM case directory. "
            "Supports foamRun (v11+) and simpleFoam. "
            "All responses follow MCP Wrapper Envelope Contract v1."
        ),
    )

    @app.tool()
    def run_openfoam(
        trace_id: str,
        task_id: str,
        invocation_id: str,
        case_dir: str,
        solver: str = "simpleFoam",
        timeout_ms: int = 300000,
    ) -> dict:
        """Run an OpenFOAM CFD case.

        Args:
            trace_id:      Task trace ID
            task_id:       Task identifier
            invocation_id: Unique per-invocation ID
            case_dir:      Absolute path to the OpenFOAM case directory
            solver:        Solver name (default: simpleFoam)
            timeout_ms:    Timeout in milliseconds (default: 300000)

        Returns:
            MCP Wrapper Envelope v1 with output.{log_file, residuals, converged}
        """
        t0 = time.perf_counter()

        bin_path = shutil.which(solver) or _FOAM_BIN
        if bin_path is None:
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"OpenFOAM binary '{solver}' (or foamRun) not found on PATH — "
                "install OpenFOAM or add to PATH",
                (time.perf_counter() - t0) * 1000,
                status="degraded",
            )
            result["metadata"]["task_id"] = task_id
            return result

        case_path = Path(case_dir)
        if not case_path.is_dir():
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"Case directory not found: {case_dir}",
                (time.perf_counter() - t0) * 1000,
            )
            result["metadata"]["task_id"] = task_id
            return result

        log_file = case_path / f"log.{solver}"

        def _run() -> tuple[int, str]:
            proc = subprocess.run(
                [bin_path],
                cwd=str(case_path),
                capture_output=True,
                text=True,
            )
            log_file.write_text(proc.stdout + proc.stderr, encoding="utf-8")
            return proc.returncode, proc.stdout + proc.stderr

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_run)
                rc, stdout = future.result(timeout=timeout_ms / 1000)
        except concurrent.futures.TimeoutError:
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_TIMEOUT",
                f"OpenFOAM timed out after {timeout_ms}ms",
                (time.perf_counter() - t0) * 1000,
                status="timeout",
            )
            result["metadata"]["task_id"] = task_id
            return result
        except Exception as exc:
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                str(exc),
                (time.perf_counter() - t0) * 1000,
            )
            result["metadata"]["task_id"] = task_id
            return result

        duration_ms = (time.perf_counter() - t0) * 1000

        if rc != 0:
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"OpenFOAM exited with rc={rc}",
                duration_ms,
                exit_code=rc,
            )
            result["metadata"]["task_id"] = task_id
            return result

        final_residual, converged = _parse_log(stdout)

        output = {
            "log_file": str(log_file),
            "residuals": final_residual,
            "converged": converged,
        }

        result = success_envelope(
            TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id, output, duration_ms,
            stdout_hash=sha256(stdout),
        )
        result["metadata"]["task_id"] = task_id
        return result

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = create_server()
    app.run()


if __name__ == "__main__":
    main()
