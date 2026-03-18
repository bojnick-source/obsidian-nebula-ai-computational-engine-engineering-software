"""
forge_agent/mcp_wrappers/calculix_server.py

CalculiX MCP wrapper — runs linear static FEA via the ccx binary and returns
von Mises stress results wrapped in the frozen MCP Wrapper Envelope Contract v1
(docs/contracts/mcp-wrapper-envelope.md).

Retry policy: 4 total attempts (1 initial + 3 retries), backoff 1s / 2s / 4s.
FRD parser: extracts max von Mises stress from CalculiX ASCII .frd output.

Entry point: python -m forge_agent.mcp_wrappers.calculix_server
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import shutil
import time
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from forge_agent.mcp_wrappers._envelope import error_envelope, sha256, success_envelope

logger = logging.getLogger(__name__)

TOOL_ID = "calculix"
WRAPPER_VERSION = "1.0.0"

# Retry delays between attempts (seconds). Index 0 = before first attempt (no sleep).
_ALL_RETRY_DELAYS: tuple[float, ...] = (0.0, 1.0, 2.0, 4.0)  # 4 total attempts

# Cache binary lookup — PATH doesn't change at runtime.
_CCX_BIN: str | None = shutil.which("ccx") or shutil.which("ccx_2.22")

# Precompiled FRD patterns — avoid recompilation on every parse call.
_FRD_STRESS_BLOCK = re.compile(r"^\s*-4\s+S\b", re.MULTILINE)
_FRD_NODE_LINE = re.compile(
    r"^\s*-1\s+\d+\s+([-\d.E+]+)\s+([-\d.E+]+)\s+([-\d.E+]+)"
    r"\s+([-\d.E+]+)\s+([-\d.E+]+)\s+([-\d.E+]+)",
    re.MULTILINE,
)
_FRD_BLOCK_END = re.compile(r"^\s*-3\b", re.MULTILINE)


# ─────────────────────────────────────────────────────────────────────────────
# FRD stress parser
# ─────────────────────────────────────────────────────────────────────────────

def _parse_von_mises_from_frd(frd_path: Path) -> tuple[float | None, int]:
    """Parse CalculiX .frd file and return (max_von_mises, node_count).

    CalculiX FRD format:
    - Stress block opened by:  -4  S
    - Node stress components:  -1  NODE_ID  SXX  SYY  SZZ  SXY  SXZ  SYZ
    - von Mises = sqrt(0.5*((Sxx-Syy)^2+(Syy-Szz)^2+(Szz-Sxx)^2 + 6*(Sxy^2+Sxz^2+Syz^2)))
    - Block closed by:  -3

    Returns None for max_von_mises if the stress block is absent or unreadable.
    Units follow the model's unit system (typically MPa for mm/N/MPa input).
    """
    if not frd_path.exists():
        return None, 0

    try:
        text = frd_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, 0

    match = _FRD_STRESS_BLOCK.search(text)
    if not match:
        return None, 0

    block_start = match.end()
    end_match = _FRD_BLOCK_END.search(text, block_start)
    block_text = text[block_start:end_match.start()] if end_match else text[block_start:]

    max_vm = 0.0
    node_count = 0

    for m in _FRD_NODE_LINE.finditer(block_text):
        try:
            sxx, syy, szz, sxy, sxz, syz = (float(m.group(i)) for i in range(1, 7))
        except ValueError:
            continue
        vm = math.sqrt(0.5 * (
            (sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2
            + 6 * (sxy ** 2 + sxz ** 2 + syz ** 2)
        ))
        max_vm = max(max_vm, vm)
        node_count += 1

    return (max_vm, node_count) if node_count > 0 else (None, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Core FEA runner (async — called via asyncio.run())
# ─────────────────────────────────────────────────────────────────────────────

async def _run_ccx(inp_file: Path, timeout_s: float) -> tuple[int, str]:
    """Run the ccx binary and return (returncode, stdout_combined)."""
    if _CCX_BIN is None:
        raise FileNotFoundError(
            "CalculiX (ccx) not found on PATH. "
            "Install: apt install calculix  or  brew install calculix"
        )
    base = str(inp_file.with_suffix(""))
    proc = await asyncio.create_subprocess_exec(
        _CCX_BIN, base,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(inp_file.parent),
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        raise TimeoutError(f"CalculiX timed out after {timeout_s}s")
    return proc.returncode, stdout.decode(errors="replace")


# ─────────────────────────────────────────────────────────────────────────────
# Server factory
# ─────────────────────────────────────────────────────────────────────────────

def create_server() -> FastMCP:
    app = FastMCP(
        name="calculix-wrapper",
        instructions=(
            "CalculiX linear static FEA wrapper. "
            "Call run_fea with a prepared .inp file. "
            "Responses follow MCP Wrapper Envelope Contract v1. "
            "Includes von Mises stress extraction from .frd output."
        ),
    )

    @app.tool()
    def run_fea(
        trace_id: str,
        task_id: str,
        invocation_id: str,
        input_file: str,
        timeout_ms: int = 600000,
    ) -> dict:
        """
        Run a CalculiX linear static FEA job and extract von Mises stress results.

        Retries up to 4 total attempts (1 initial + 3 retries) with exponential
        backoff (1s, 2s, 4s) before returning an error envelope.

        Args:
            trace_id:      Task trace ID (propagated to all artifacts)
            task_id:       Task identifier
            invocation_id: Unique per-invocation ID (caller generates new UUID per retry)
            input_file:    Absolute path to the CalculiX .inp file
            timeout_ms:    Per-attempt timeout in milliseconds (default 600000 = 10 min)

        Returns:
            MCP Wrapper Envelope v1 with output.{frd_file, dat_file, log_tail,
            max_von_mises_mpa, node_count, stress_extracted}
        """
        t0 = time.perf_counter()
        inp_path = Path(input_file)

        if not inp_path.exists():
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"Input file not found: {input_file}",
                (time.perf_counter() - t0) * 1000,
            )

        if _CCX_BIN is None:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                "CalculiX (ccx) not found on PATH. Install: apt install calculix",
                (time.perf_counter() - t0) * 1000,
            )

        timeout_s = timeout_ms / 1000
        last_error = ""
        last_rc = -1
        stdout = ""

        for attempt, delay in enumerate(_ALL_RETRY_DELAYS):
            if delay > 0:
                time.sleep(delay)
            try:
                last_rc, stdout = asyncio.run(_run_ccx(inp_path, timeout_s))
            except TimeoutError:
                return error_envelope(
                    TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                    "ERR_TOOL_TIMEOUT",
                    f"CalculiX timed out after {timeout_s}s",
                    (time.perf_counter() - t0) * 1000,
                    status="timeout",
                )

            if last_rc == 0:
                break
            last_error = f"CalculiX exited rc={last_rc}"
            logger.warning("CalculiX attempt %d/%d failed rc=%d", attempt + 1, len(_ALL_RETRY_DELAYS), last_rc)
        else:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                f"All {len(_ALL_RETRY_DELAYS)} attempts failed. Last: {last_error}",
                (time.perf_counter() - t0) * 1000,
                exit_code=last_rc,
            )

        frd_path = inp_path.with_suffix(".frd")
        dat_path = inp_path.with_suffix(".dat")
        duration_ms = (time.perf_counter() - t0) * 1000

        max_vm, node_count = _parse_von_mises_from_frd(frd_path)

        output = {
            "frd_file": str(frd_path) if frd_path.exists() else None,
            "dat_file": str(dat_path) if dat_path.exists() else None,
            "log_tail": stdout[-1000:],
            "max_von_mises_mpa": max_vm,
            "node_count": node_count,
            "stress_extracted": max_vm is not None,
        }

        return success_envelope(
            TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id, output, duration_ms,
            stdout_hash=sha256(stdout),
            stderr_lines=stdout.count("\n"),
        )

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = create_server()
    app.run()


if __name__ == "__main__":
    main()
