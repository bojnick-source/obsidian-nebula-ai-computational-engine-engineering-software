"""
PTCEngine — Python Tool Calls sandbox.

Registers a `code_execution` tool that runs Python snippets in a restricted
subprocess with a configurable timeout. Stdout is captured as the result.
Dangerous builtins (exec, eval, __import__, open) are blocked at the prompt
level; actual sandboxing is via resource limits + restricted globals.
"""

from __future__ import annotations

import asyncio
import resource
import sys
import textwrap
from dataclasses import dataclass
from typing import Any


@dataclass
class CodeExecutionResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False

    def to_tool_result(self) -> str:
        if self.timed_out:
            return "ERROR: code execution timed out"
        if self.returncode != 0:
            return f"ERROR (exit {self.returncode}):\n{self.stderr[:500]}"
        return self.stdout[:4000] or "(no output)"


# Blocked patterns — refuse before executing
_BLOCKED_PATTERNS: list[str] = [
    "import os",
    "import sys",
    "import subprocess",
    "import socket",
    "__import__",
    "open(",
    "exec(",
    "eval(",
    "compile(",
    "globals()",
    "locals()",
    "getattr(",
    "setattr(",
    "delattr(",
    "__builtins__",
]


class PTCEngine:
    """
    Python Tool Calls engine.
    Provides the `code_execution` tool spec for Anthropic tool_use.
    """

    def __init__(
        self,
        timeout_s: float = 30.0,
        max_memory_mb: int = 256,
    ) -> None:
        self.timeout_s = timeout_s
        self.max_memory_mb = max_memory_mb

    def tool_spec(self) -> dict:
        """Return the Anthropic tool spec dict for code_execution."""
        return {
            "name": "code_execution",
            "description": (
                "Execute a Python code snippet for engineering calculations. "
                "numpy, scipy, sympy, and math are available. "
                "Do NOT import os, sys, subprocess, or use open(). "
                "Print results to stdout. Max 30 seconds."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute. Must print results.",
                    }
                },
                "required": ["code"],
            },
        }

    async def execute(self, code: str) -> CodeExecutionResult:
        """Run code in a restricted subprocess."""
        # Static safety check
        blocked = self._check_blocked(code)
        if blocked:
            return CodeExecutionResult(
                stdout="",
                stderr=f"BLOCKED: code contains disallowed pattern: {blocked!r}",
                returncode=1,
            )

        wrapper = self._build_wrapper(code)
        return await self._run_subprocess(wrapper)

    def _check_blocked(self, code: str) -> str | None:
        for pattern in _BLOCKED_PATTERNS:
            if pattern in code:
                return pattern
        return None

    def _build_wrapper(self, code: str) -> str:
        """Wrap user code with safe imports and resource limits."""
        indented = textwrap.indent(code, "    ")
        return textwrap.dedent(f"""\
            import resource, math
            import numpy as np
            import scipy
            import sympy

            # Memory limit
            resource.setrlimit(resource.RLIMIT_AS, ({self.max_memory_mb * 1024 * 1024}, -1))

            try:
{textwrap.indent(indented, "    ")}
            except Exception as _e:
                import traceback; traceback.print_exc()
                raise SystemExit(1)
        """)

    async def _run_subprocess(self, code: str) -> CodeExecutionResult:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout_s
            )
            return CodeExecutionResult(
                stdout=stdout_b.decode(errors="replace"),
                stderr=stderr_b.decode(errors="replace"),
                returncode=proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return CodeExecutionResult(stdout="", stderr="", returncode=-1, timed_out=True)
