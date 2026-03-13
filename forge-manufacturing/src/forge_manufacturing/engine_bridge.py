"""Python → C++ engine bridge via subprocess.

The C++ v2_engine_cli binary is optional.  The Python manufacturing pipeline
runs fully without it; the bridge is invoked only when a spec step explicitly
requests numerical engine computation.

Adapted from: https://github.com/bojnick-source/DARK_leaf_drone_4-1_V2 (src/sfcs_mdp/v2_engine.py)
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

_ENGINE_BINARY_NAME: str = "v2_engine_cli"


def find_engine_cli(hint: str | None = None) -> str | None:
    """Locate the ``v2_engine_cli`` binary.

    Search order:
      1. *hint* path (if provided) — validated with :func:`pathlib.Path.is_file`.
      2. System PATH via :func:`shutil.which`.

    Args:
        hint: Explicit path to the binary, or ``None`` for PATH search.

    Returns:
        Absolute path string if found, otherwise ``None``.
    """
    if hint is not None:
        if Path(hint).is_file():
            return hint
        return None
    return shutil.which(_ENGINE_BINARY_NAME)


def run_engine(
    engine_cli: str,
    canonical_input: dict[str, Any],
    artifact_root: Path | None = None,
    no_write: bool = False,
) -> dict[str, Any]:
    """Execute the C++ engine binary and return its parsed JSON output.

    Args:
        engine_cli:      Path to the ``v2_engine_cli`` binary (from
                         :func:`find_engine_cli`).
        canonical_input: Input payload serialised to JSON and piped to stdin.
        artifact_root:   Optional directory for engine-generated artifacts.
        no_write:        If True, pass ``--no-write`` to suppress file output.

    Returns:
        Parsed ``dict`` from the engine's stdout.

    Raises:
        RuntimeError: If the binary is not found, exits non-zero, or returns
            invalid JSON.
    """
    cmd: list[str] = [engine_cli]
    if artifact_root is not None:
        cmd += ["--artifact-root", str(artifact_root)]
    if no_write:
        cmd.append("--no-write")

    input_json = json.dumps(canonical_input).encode("utf-8")

    try:
        result = subprocess.run(
            cmd,
            input=input_json,
            capture_output=True,
            check=False,  # We handle non-zero ourselves for a cleaner error message.
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Engine binary not found: {engine_cli!r}"
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"Engine exited with code {result.returncode}. Stderr: {stderr}"
        )

    stdout = result.stdout.decode("utf-8", errors="replace")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Engine returned non-JSON output: {stdout[:200]!r}"
        ) from exc
