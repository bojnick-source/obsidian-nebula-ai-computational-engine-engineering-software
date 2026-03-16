"""
forge_agent/core/cli_dispatcher.py

CLI-first tool dispatcher for FORGE.

Architecture
------------
CLI is the primary dispatch path. MCP is the fallback.

Why CLI first:
  - No JSON-RPC round-trip overhead
  - No server subprocess lifecycle (start/stop/health-check)
  - Direct Python imports for Python tools (gmsh, fenicsx) are ~10× faster
    than spawning an MCP server and sending a request over stdio
  - subprocess.run() for native CLIs (ccx, freecad) is simpler to debug
  - MCPs were designed for LLM ↔ tool integration; CLI is correct for
    agent ↔ tool integration when both are in the same process

MCP stays as backup because:
  - Some tools only expose an MCP interface (third-party servers)
  - MCP handles tool discovery / schema — useful for dynamic tool lists
  - Keeps the option open for remote tools over HTTP transport

Usage
-----
    dispatcher = CliDispatcher()

    result, handled = await dispatcher.call("read_file", {"path": "/vault/note.md"})
    if not handled:
        result = await mcp_manager.call_tool("read_file", {"path": "/vault/note.md"})

Registering a new CLI handler
------------------------------
    @CliDispatcher.register("my_tool_name")
    async def _my_tool(args: dict) -> Any:
        ...
        return result

The handler must be an async function. Raise CliToolError to signal a
recoverable failure (MCP fallback will be attempted). Raise any other
exception to propagate as a hard error.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import Any, Callable


# ── Exceptions ────────────────────────────────────────────────────────────────


class CliToolError(RuntimeError):
    """Raised when a CLI handler fails in a way that should trigger MCP fallback."""


# ── Registry ──────────────────────────────────────────────────────────────────

_REGISTRY: dict[str, Callable] = {}


def _register(tool_name: str):
    """Decorator: register an async function as the CLI handler for tool_name."""
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[tool_name] = fn
        return fn
    return decorator


# ── CliDispatcher ─────────────────────────────────────────────────────────────


class CliDispatcher:
    """
    Tries each tool call via its registered CLI handler before MCP.

    Returns (result, handled):
        handled=True  — CLI succeeded; result contains the tool output
        handled=False — no CLI handler exists or it raised CliToolError;
                        caller should try MCP
    """

    async def call(self, tool_name: str, arguments: dict) -> tuple[Any, bool]:
        handler = _REGISTRY.get(tool_name)
        if handler is None:
            return None, False
        try:
            result = await handler(arguments)
            return result, True
        except CliToolError:
            return None, False

    def registered_tools(self) -> list[str]:
        """Return the list of tool names with CLI implementations."""
        return list(_REGISTRY.keys())

    @staticmethod
    def register(tool_name: str):
        """Expose the decorator for external registrations."""
        return _register(tool_name)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════════

# ── Filesystem tools (replaces @modelcontextprotocol/server-filesystem MCP) ──


@_register("read_file")
async def _read_file(args: dict) -> str:
    path = Path(args["path"]).expanduser()
    if not path.exists():
        raise CliToolError(f"File not found: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


@_register("write_file")
async def _write_file(args: dict) -> dict:
    path = Path(args["path"]).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(args["content"], encoding="utf-8")
    return {"written": str(path), "bytes": len(args["content"])}


@_register("create_directory")
async def _create_directory(args: dict) -> dict:
    path = Path(args["path"]).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return {"created": str(path)}


@_register("list_directory")
async def _list_directory(args: dict) -> list[dict]:
    path = Path(args["path"]).expanduser()
    if not path.is_dir():
        raise CliToolError(f"Not a directory: {path}")
    entries = []
    for entry in sorted(path.iterdir()):
        entries.append({
            "name": entry.name,
            "type": "directory" if entry.is_dir() else "file",
            "size": entry.stat().st_size if entry.is_file() else None,
        })
    return entries


@_register("search_files")
async def _search_files(args: dict) -> list[str]:
    root = Path(args["path"]).expanduser()
    pattern = args.get("pattern", "*")
    return [str(p) for p in sorted(root.rglob(pattern))]


@_register("move_file")
async def _move_file(args: dict) -> dict:
    src = Path(args["source"]).expanduser()
    dst = Path(args["destination"]).expanduser()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return {"moved": str(dst)}


@_register("delete_file")
async def _delete_file(args: dict) -> dict:
    path = Path(args["path"]).expanduser()
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)
    return {"deleted": str(path)}


@_register("get_file_info")
async def _get_file_info(args: dict) -> dict:
    path = Path(args["path"]).expanduser()
    if not path.exists():
        raise CliToolError(f"Path not found: {path}")
    stat = path.stat()
    return {
        "path": str(path),
        "type": "directory" if path.is_dir() else "file",
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }


# ── Obsidian / vault tools ────────────────────────────────────────────────────
# Direct Python calls to ObsidianManager — no MCP subprocess needed.


@_register("vault_read_note")
async def _vault_read_note(args: dict) -> str:
    from forge_agent.memory.obsidian_manager import ObsidianManager
    vault_path = os.environ.get("FORGE_VAULT_PATH", "forge-vault")
    mgr = ObsidianManager(vault_path)
    result = await mgr.read_note(args["path"])
    return result


@_register("vault_write_note")
async def _vault_write_note(args: dict) -> dict:
    from forge_agent.memory.obsidian_manager import ObsidianManager
    vault_path = os.environ.get("FORGE_VAULT_PATH", "forge-vault")
    mgr = ObsidianManager(vault_path)
    await mgr.write_note(args["path"], args["content"])
    return {"written": args["path"]}


@_register("vault_search")
async def _vault_search(args: dict) -> list[dict]:
    from forge_agent.memory.obsidian_manager import ObsidianManager
    vault_path = os.environ.get("FORGE_VAULT_PATH", "forge-vault")
    mgr = ObsidianManager(vault_path)
    return await mgr.search(args["query"], limit=args.get("limit", 10))


# ── Gmsh — mesh generation ────────────────────────────────────────────────────
# Direct Python import is ~10× faster than MCP subprocess for small meshes.


@_register("gmsh_generate_mesh")
async def _gmsh_generate(args: dict) -> dict:
    try:
        import gmsh  # type: ignore[import-untyped]
    except ImportError:
        raise CliToolError("gmsh Python package not installed — pip install gmsh")

    geo_file = args["geo_file"]
    out_file = args.get("output", geo_file.replace(".geo", ".msh"))
    dim = args.get("dim", 3)
    mesh_size = args.get("mesh_size", 0.1)

    def _run() -> dict:
        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
            gmsh.merge(geo_file)
            gmsh.model.mesh.generate(dim)
            gmsh.write(out_file)
            info = gmsh.model.mesh.getStats()
            return {"output": out_file, "stats": str(info)}
        finally:
            gmsh.finalize()

    return await asyncio.get_event_loop().run_in_executor(None, _run)


@_register("gmsh_generate_from_stl")
async def _gmsh_from_stl(args: dict) -> dict:
    try:
        import gmsh  # type: ignore[import-untyped]
    except ImportError:
        raise CliToolError("gmsh Python package not installed — pip install gmsh")

    stl_file = args["stl_file"]
    out_file = args.get("output", stl_file.replace(".stl", ".msh"))
    mesh_size = args.get("mesh_size", 1.0)

    def _run() -> dict:
        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
            gmsh.merge(stl_file)
            gmsh.model.mesh.classifySurfaces(
                angle=0.3, boundary=True, forReparametrization=False
            )
            gmsh.model.mesh.createGeometry()
            gmsh.model.mesh.generate(3)
            gmsh.write(out_file)
            return {"output": out_file}
        finally:
            gmsh.finalize()

    return await asyncio.get_event_loop().run_in_executor(None, _run)


# ── CalculiX — FEA solver ─────────────────────────────────────────────────────
# ccx is a native CLI binary. Direct subprocess is the natural interface.


@_register("calculix_run_fea")
async def _calculix_run(args: dict) -> dict:
    ccx_bin = shutil.which("ccx") or shutil.which("ccx_2.22")
    if ccx_bin is None:
        raise CliToolError(
            "CalculiX (ccx) not found on PATH. "
            "Install: apt install calculix  or  brew install calculix"
        )

    inp_file = Path(args["input_file"])
    if not inp_file.exists():
        raise CliToolError(f"CalculiX input file not found: {inp_file}")

    # ccx takes the base name without extension
    base = str(inp_file.with_suffix(""))
    timeout = args.get("timeout_s", 600)

    proc = await asyncio.create_subprocess_exec(
        ccx_bin, base,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(inp_file.parent),
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise CliToolError(f"CalculiX timed out after {timeout}s")

    log = stdout.decode(errors="replace")
    frd = inp_file.with_suffix(".frd")
    dat = inp_file.with_suffix(".dat")

    if proc.returncode != 0:
        raise CliToolError(f"CalculiX failed (rc={proc.returncode}):\n{log[-2000:]}")

    return {
        "returncode": proc.returncode,
        "frd_file": str(frd) if frd.exists() else None,
        "dat_file": str(dat) if dat.exists() else None,
        "log_tail": log[-1000:],
    }


# ── FreeCAD — CAD export ──────────────────────────────────────────────────────
# FreeCAD has a CLI mode: freecad --console --run script.py


@_register("freecad_export")
async def _freecad_export(args: dict) -> dict:
    freecad_bin = (
        shutil.which("freecad")
        or shutil.which("FreeCAD")
        or shutil.which("freecadcmd")
    )
    if freecad_bin is None:
        raise CliToolError(
            "FreeCAD not found on PATH. "
            "Install: https://www.freecad.org/downloads.php"
        )

    input_file = args["input_file"]
    output_file = args["output_file"]
    export_format = args.get("format", "step").lower()

    script = (
        f"import FreeCAD, Part\n"
        f"doc = FreeCAD.openDocument({input_file!r})\n"
        f"Part.export(doc.Objects, {output_file!r})\n"
        f"print('exported')\n"
    )
    script_path = Path(output_file).with_suffix(".tmp_export.py")
    script_path.write_text(script)

    try:
        proc = await asyncio.create_subprocess_exec(
            freecad_bin, "--console", "--run", str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        proc.kill()
        raise CliToolError("FreeCAD export timed out after 120s")
    finally:
        script_path.unlink(missing_ok=True)

    log = stdout.decode(errors="replace")
    if proc.returncode != 0 or "exported" not in log:
        raise CliToolError(f"FreeCAD export failed:\n{log[-1000:]}")

    return {"output_file": output_file, "format": export_format}


# ── MATLAB / FreeTO ───────────────────────────────────────────────────────────
# Calls freeto_wrapper.m via MATLAB Engine API (Python tier → MATLAB tier).
# Falls back to MCP if MATLAB Engine is not installed.


@_register("freeto_optimize")
async def _freeto_optimize(args: dict) -> dict:
    try:
        import matlab.engine as _me  # type: ignore[import-untyped]
    except ImportError:
        raise CliToolError(
            "MATLAB Engine for Python not installed. "
            "See: https://mathworks.com/help/matlab/matlab-engine-for-python.html"
        )

    wrapper_dir = str(
        Path(__file__).parents[2] / "forge-tools" / "matlab-wrappers" / "freeto"
    )

    def _run() -> dict:
        eng = _me.start_matlab("-nojvm -nodisplay -nosplash")
        try:
            eng.addpath(wrapper_dir, nargout=0)
            result = eng.freeto_wrapper(args, nargout=1)
            return dict(result)
        finally:
            eng.quit()

    return await asyncio.get_event_loop().run_in_executor(None, _run)


@_register("swan_optimize")
async def _swan_optimize(args: dict) -> dict:
    try:
        import matlab.engine as _me  # type: ignore[import-untyped]
    except ImportError:
        raise CliToolError(
            "MATLAB Engine for Python not installed. "
            "See: https://mathworks.com/help/matlab/matlab-engine-for-python.html"
        )

    wrapper_dir = str(
        Path(__file__).parents[2] / "forge-tools" / "matlab-wrappers"
    )

    def _run() -> dict:
        eng = _me.start_matlab("-nojvm -nodisplay -nosplash")
        try:
            eng.addpath(eng.genpath(wrapper_dir), nargout=0)
            result = eng.swan_wrapper(args, nargout=1)
            return dict(result)
        finally:
            eng.quit()

    return await asyncio.get_event_loop().run_in_executor(None, _run)
