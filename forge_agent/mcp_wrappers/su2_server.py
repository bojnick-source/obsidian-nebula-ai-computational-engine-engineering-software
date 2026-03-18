"""
forge_agent/mcp_wrappers/su2_server.py

SU2 MCP wrapper — runs CFD solves via SU2_CFD and returns results wrapped in
the frozen MCP Wrapper Envelope Contract v1
(docs/contracts/mcp-wrapper-envelope.md).

Returns status="degraded" when SU2_CFD binary is absent from PATH.

Entry point: python -m forge_agent.mcp_wrappers.su2_server
"""

from __future__ import annotations

import concurrent.futures
import csv
import logging
import shutil
import subprocess
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from forge_agent.mcp_wrappers._envelope import error_envelope, sha256, success_envelope

logger = logging.getLogger(__name__)

TOOL_ID = "su2"
WRAPPER_VERSION = "1.0.0"

# Cache binary lookup — PATH doesn't change at runtime.
_SU2_BIN: str | None = shutil.which("SU2_CFD")


def _parse_history(case_dir: Path) -> tuple[float | None, float | None, bool]:
    """Parse SU2 history.csv and return (cl, cd, converged).

    SU2 v7 uses 'CL'/'CD'; v8 uses 'CL(Total)'/'CD(Total)' or similar.
    Case-insensitive lookup handles both.
    """
    history_path = case_dir / "history.csv"
    if not history_path.exists():
        return None, None, False

    try:
        text = history_path.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(text.splitlines())
        rows = list(reader)
    except Exception:
        return None, None, False

    if not rows:
        return None, None, False

    # Build case-insensitive column map from the last row.
    last_row = rows[-1]
    col_map: dict[str, str] = {k.strip().lower(): k for k in last_row}

    def _get(key_lower: str) -> float | None:
        for candidate in (key_lower, key_lower + "(total)", key_lower + "_total"):
            col = col_map.get(candidate)
            if col is not None:
                try:
                    return float(last_row[col].strip())
                except (ValueError, KeyError):
                    pass
        return None

    cl = _get("cl")
    cd = _get("cd")

    # Convergence: SU2 writes "CONVERGED" in the Cauchy column when done.
    converged = any(
        "converged" in str(v).lower()
        for v in last_row.values()
    )
    return cl, cd, converged


def create_server() -> FastMCP:
    app = FastMCP(
        name="su2-wrapper",
        instructions=(
            "SU2 CFD solver wrapper. "
            "Use run_su2 with an SU2 .cfg file. "
            "All responses follow MCP Wrapper Envelope Contract v1."
        ),
    )

    @app.tool()
    def run_su2(
        trace_id: str,
        task_id: str,
        invocation_id: str,
        config_file: str,
        timeout_ms: int = 300000,
    ) -> dict:
        """Run an SU2 CFD solve.

        Args:
            trace_id:      Task trace ID
            task_id:       Task identifier
            invocation_id: Unique per-invocation ID
            config_file:   Absolute path to the SU2 .cfg file
            timeout_ms:    Timeout in milliseconds (default: 300000)

        Returns:
            MCP Wrapper Envelope v1 with output.{history_file, cl, cd, converged}
        """
        t0 = time.perf_counter()

        if _SU2_BIN is None:
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                "SU2_CFD binary not found on PATH — install SU2 or add to PATH",
                (time.perf_counter() - t0) * 1000,
                status="degraded",
            )
            result["metadata"]["task_id"] = task_id
            return result

        cfg_path = Path(config_file)
        if not cfg_path.is_file():
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"Config file not found: {config_file}",
                (time.perf_counter() - t0) * 1000,
            )
            result["metadata"]["task_id"] = task_id
            return result

        case_dir = cfg_path.parent

        def _run() -> tuple[int, str]:
            proc = subprocess.run(
                [_SU2_BIN, str(cfg_path)],
                cwd=str(case_dir),
                capture_output=True,
                text=True,
            )
            return proc.returncode, proc.stdout + proc.stderr

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_run)
                rc, stdout = future.result(timeout=timeout_ms / 1000)
        except concurrent.futures.TimeoutError:
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_TIMEOUT",
                f"SU2_CFD timed out after {timeout_ms}ms",
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
                f"SU2_CFD exited with rc={rc}",
                duration_ms,
                exit_code=rc,
            )
            result["metadata"]["task_id"] = task_id
            return result

        cl, cd, converged = _parse_history(case_dir)
        history_file = str(case_dir / "history.csv")

        if cl is None and cd is None:
            result = error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_OUTPUT_INVALID",
                "SU2_CFD output: could not parse CL/CD from history.csv",
                duration_ms,
            )
            result["metadata"]["task_id"] = task_id
            return result

        output = {
            "history_file": history_file,
            "cl": cl,
            "cd": cd,
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
