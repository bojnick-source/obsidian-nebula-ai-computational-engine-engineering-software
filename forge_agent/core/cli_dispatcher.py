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


# ── OpenFOAM / SU2 ───────────────────────────────────────────────────────────


@_register("openfoam_run")
async def _openfoam_run(args: dict) -> dict:
    """Run an OpenFOAM CFD case.

    args:
        case_dir  : str   — absolute path to the OpenFOAM case directory
        solver    : str   — solver binary name (default: simpleFoam)
        timeout_ms: int   — timeout in milliseconds (default: 300000)
    """
    solver = args.get("solver", "simpleFoam")
    if not shutil.which(solver) and not shutil.which("foamRun"):
        raise CliToolError(
            f"OpenFOAM binary '{solver}' (or foamRun) not found on PATH — "
            "install OpenFOAM or add to PATH"
        )

    case_dir = args.get("case_dir", "")
    case_path = Path(case_dir)
    if not case_path.is_dir():
        raise CliToolError(f"Case directory not found: {case_dir}")

    bin_path = shutil.which(solver) or shutil.which("foamRun")

    def _run() -> dict:
        import subprocess
        proc = subprocess.run(
            [bin_path],
            cwd=str(case_path),
            capture_output=True,
            text=True,
        )
        return {"returncode": proc.returncode, "stdout": proc.stdout + proc.stderr}

    return await asyncio.get_event_loop().run_in_executor(None, _run)


@_register("su2_run")
async def _su2_run(args: dict) -> dict:
    """Run an SU2 CFD solve.

    args:
        config_file: str  — absolute path to the SU2 .cfg file
        timeout_ms : int  — timeout in milliseconds (default: 300000)
    """
    if not shutil.which("SU2_CFD"):
        raise CliToolError("SU2_CFD binary not found on PATH — install SU2 or add to PATH")

    config_file = args.get("config_file", "")
    cfg_path = Path(config_file)
    if not cfg_path.is_file():
        raise CliToolError(f"Config file not found: {config_file}")

    def _run() -> dict:
        import subprocess
        proc = subprocess.run(
            [shutil.which("SU2_CFD"), str(cfg_path)],
            cwd=str(cfg_path.parent),
            capture_output=True,
            text=True,
        )
        return {"returncode": proc.returncode, "stdout": proc.stdout + proc.stderr}

    return await asyncio.get_event_loop().run_in_executor(None, _run)


# ── Void Vanguard — McKibben PAM / MuJoCo / CMA-ES ───────────────────────────
# synthmuscle_fit: fit PAM parameters to measured force-length-pressure data
# mujoco_step: run a deterministic MuJoCo trajectory rollout
# cmaes_optimize: run diagonal CMA-ES with Monte Carlo CVaR gating


@_register("synthmuscle_fit")
async def _synthmuscle_fit(args: dict) -> dict:
    """
    Fit Chou–Hannaford PAM model parameters to measured F(L, P) data.

    args:
        data_file  : str  — path to CSV with columns [length_m, pressure_kPa, force_N]
        L0_init    : float — initial guess for rest length [m] (default 0.10)
        D0_init    : float — initial guess for rest diameter [m] (default 0.025)
        alpha0_init: float — initial guess for braid angle [deg] (default 25.0)
        n_turns    : int   — number of braid turns (optional; uses geometric fit if absent)

    returns:
        dict with keys: L0_m, D0_m, alpha0_deg, rmse_N, rmse_pct, r2, aic, bic,
                        F_max_N (at ε=0, P=P_max in data), provenance
    """
    try:
        import numpy as np  # type: ignore[import-untyped]
        from scipy.optimize import least_squares  # type: ignore[import-untyped]
    except ImportError:
        raise CliToolError("numpy/scipy not installed — pip install numpy scipy")

    data_file = Path(args["data_file"]).expanduser()
    if not data_file.exists():
        raise CliToolError(f"Data file not found: {data_file}")

    def _run() -> dict:
        import hashlib

        data = np.loadtxt(str(data_file), delimiter=",", skiprows=1)
        L = data[:, 0]       # length [m]
        P = data[:, 1] * 1e3  # convert kPa → Pa for model
        F_meas = data[:, 2]  # force [N]

        L0_init = args.get("L0_init", 0.10)
        D0_init = args.get("D0_init", 0.025)
        alpha0_init_deg = args.get("alpha0_init", 25.0)

        # Chou–Hannaford model: F = (π D0²/4) · P · [3(L/L0)²cos²α0 - 1] / tan²α0
        def model(params, L, P):
            L0, D0, alpha0_deg = params
            alpha0 = np.radians(alpha0_deg)
            cos2a = np.cos(alpha0) ** 2
            tan2a = np.tan(alpha0) ** 2
            length_ratio = L / L0
            F = (np.pi * D0**2 / 4) * P * (3 * length_ratio**2 * cos2a - 1) / tan2a
            return F

        def residuals(params):
            return model(params, L, P) - F_meas

        x0 = [L0_init, D0_init, alpha0_init_deg]
        bounds = ([0.05, 0.005, 15.0], [0.30, 0.10, 40.0])
        result = least_squares(
            residuals, x0, bounds=bounds, method="trf", loss="soft_l1"
        )

        L0, D0, alpha0_deg = result.x
        F_pred = model(result.x, L, P)
        residuals_fit = F_meas - F_pred
        n = len(F_meas)
        k = 3  # number of fitted parameters

        rmse = float(np.sqrt(np.mean(residuals_fit**2)))
        F_max = float(np.max(F_meas))
        rmse_pct = 100.0 * rmse / F_max if F_max > 0 else float("nan")
        ss_res = float(np.sum(residuals_fit**2))
        ss_tot = float(np.sum((F_meas - np.mean(F_meas))**2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        # AIC / BIC (assuming Gaussian residuals)
        sigma2 = ss_res / n
        log_likelihood = -n / 2 * np.log(2 * np.pi * sigma2) - ss_res / (2 * sigma2)
        aic = float(2 * k - 2 * log_likelihood)
        bic = float(k * np.log(n) - 2 * log_likelihood)

        # provenance
        sha256 = hashlib.sha256(data_file.read_bytes()).hexdigest()[:16]

        return {
            "L0_m": float(L0),
            "D0_m": float(D0),
            "alpha0_deg": float(alpha0_deg),
            "rmse_N": rmse,
            "rmse_pct": rmse_pct,
            "r2": float(r2),
            "aic": aic,
            "bic": bic,
            "F_max_N": F_max,
            "n_samples": n,
            "provenance": f"scipy least_squares trf — data SHA256: {sha256}",
        }

    return await asyncio.get_event_loop().run_in_executor(None, _run)


@_register("mujoco_step")
async def _mujoco_step(args: dict) -> dict:
    """
    Run a deterministic MuJoCo trajectory rollout.

    args:
        mjcf_file    : str   — path to MJCF XML model file
        ctrl_sequence: list  — list of [n_actuators] control vectors per step
        seed         : int   — random seed for DR sampling (default 42)
        dt_s         : float — override model timestep [s] (default: use model value)
        record_joints: list  — joint names to record (default: all)

    returns:
        dict with keys: steps, duration_s, dt_s, joint_trajectories (dict name→list),
                        qpos_final, qvel_final, reproducibility, provenance
    """
    try:
        import mujoco  # type: ignore[import-untyped]
        import numpy as np  # type: ignore[import-untyped]
    except ImportError:
        raise CliToolError("mujoco not installed — pip install mujoco")

    mjcf_file = Path(args["mjcf_file"]).expanduser()
    if not mjcf_file.exists():
        raise CliToolError(f"MJCF file not found: {mjcf_file}")

    def _run() -> dict:
        import hashlib

        seed = args.get("seed", 42)
        np.random.seed(seed)

        model = mujoco.MjModel.from_xml_path(str(mjcf_file))
        if "dt_s" in args:
            model.opt.timestep = args["dt_s"]

        dt = float(model.opt.timestep)
        ctrl_sequence = args.get("ctrl_sequence", [])

        # Run first pass
        data = mujoco.MjData(model)
        mujoco.mj_resetData(model, data)

        record_joints = args.get("record_joints", None)
        joint_names = [
            mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
            for i in range(model.njnt)
        ]
        if record_joints:
            record_idx = [
                i for i, name in enumerate(joint_names) if name in record_joints
            ]
        else:
            record_idx = list(range(model.njnt))

        trajectories: dict[str, list] = {joint_names[i]: [] for i in record_idx}

        for ctrl in ctrl_sequence:
            data.ctrl[:] = ctrl
            mujoco.mj_step(model, data)
            for i in record_idx:
                trajectories[joint_names[i]].append(float(data.qpos[i]))

        qpos_final = data.qpos.tolist()
        qvel_final = data.qvel.tolist()
        steps = len(ctrl_sequence)

        # Reproducibility check: second identical run
        data2 = mujoco.MjData(model)
        np.random.seed(seed)
        mujoco.mj_resetData(model, data2)
        for ctrl in ctrl_sequence:
            data2.ctrl[:] = ctrl
            mujoco.mj_step(model, data2)
        repro = bool(np.allclose(data.qpos, data2.qpos, atol=1e-6))

        sha256 = hashlib.sha256(mjcf_file.read_bytes()).hexdigest()[:16]

        return {
            "steps": steps,
            "duration_s": steps * dt,
            "dt_s": dt,
            "joint_trajectories": trajectories,
            "qpos_final": qpos_final,
            "qvel_final": qvel_final,
            "reproducibility": "PASS" if repro else "FAIL",
            "seed": seed,
            "provenance": f"mujoco — MJCF SHA256: {sha256} — seed: {seed}",
        }

    return await asyncio.get_event_loop().run_in_executor(None, _run)


@_register("cmaes_optimize")
async def _cmaes_optimize(args: dict) -> dict:
    """
    Run diagonal CMA-ES with Monte Carlo CVaR gating for Void Vanguard PAM control.

    args:
        fitness_tool  : str   — name of CLI tool to call for fitness evaluation
        fitness_args  : dict  — base args for fitness_tool (updated per candidate)
        param_names   : list  — parameter names (length = n)
        param_bounds  : list  — [[lo, hi], ...] per parameter
        sigma0        : float — initial step size (default: 1/3 of param range)
        max_generations: int  — max generations (default 300)
        seed          : int   — random seed (default 42)
        n_mc          : int   — MC samples per CVaR evaluation (default 500)
        cvar_alpha    : float — CVaR quantile (default 0.05)
        cvar_threshold: float — CVaR acceptance threshold (default 8.0)
        stagnation_tol: float — σ_k below this fraction of σ₀ → restart signal (default 1e-6)

    returns:
        dict with keys: best_params, best_fitness, cvar_005, cvar_pass, generations,
                        sigma_final, sigma0, lambda_pop, lambda_min, stagnation,
                        convergence_curve, provenance
    """
    try:
        import cma  # type: ignore[import-untyped]
        import numpy as np  # type: ignore[import-untyped]
    except ImportError:
        raise CliToolError(
            "cma not installed — pip install cma  "
            "(Hansen's CMA-ES Python package)"
        )

    import math

    param_names = args["param_names"]
    param_bounds = args["param_bounds"]
    n = len(param_names)
    lo = np.array([b[0] for b in param_bounds])
    hi = np.array([b[1] for b in param_bounds])
    ranges = hi - lo

    # Population size: λ ≥ 4 + floor(3·ln(n))
    lambda_min = 4 + int(3 * math.log(n))
    lambda_pop = max(lambda_min, args.get("lambda_pop", lambda_min))

    sigma0 = args.get("sigma0", float(np.mean(ranges) / 3))
    max_generations = args.get("max_generations", 300)
    seed = args.get("seed", 42)
    n_mc = args.get("n_mc", 500)
    cvar_alpha = args.get("cvar_alpha", 0.05)
    cvar_threshold = args.get("cvar_threshold", 8.0)
    stagnation_tol = args.get("stagnation_tol", 1e-6)

    # x0: midpoint of parameter space
    x0 = ((lo + hi) / 2).tolist()

    fitness_tool = args.get("fitness_tool", None)
    fitness_fn = _REGISTRY.get(fitness_tool) if fitness_tool else None

    async def evaluate(x: list[float]) -> float:
        """Evaluate fitness for a single candidate. Returns scalar cost."""
        if fitness_fn is None:
            # No fitness tool: return dummy (callers inject real fitness via fitness_args)
            return float(np.sum(np.array(x) ** 2))
        candidate_args = dict(args.get("fitness_args", {}))
        for name, val in zip(param_names, x):
            candidate_args[name] = val
        try:
            result = await fitness_fn(candidate_args)
            return float(result.get("tracking_error_deg", 1e9))
        except Exception:
            return 1e9  # infeasible candidate

    def _run_sync() -> dict:
        import asyncio as _aio

        loop = _aio.new_event_loop()

        es = cma.CMAEvolutionStrategy(
            x0,
            sigma0,
            {
                "popsize": lambda_pop,
                "seed": seed,
                "bounds": [lo.tolist(), hi.tolist()],
                "verbose": -9,
                "CMA_diagonal": True,  # diagonal CMA-ES
            },
        )

        convergence_curve = []
        stagnated = False

        for gen in range(max_generations):
            solutions = es.ask()
            fitnesses = [
                loop.run_until_complete(evaluate(x)) for x in solutions
            ]
            es.tell(solutions, fitnesses)
            best_f = float(min(fitnesses))
            convergence_curve.append(best_f)

            sigma_k = es.sigma
            if sigma_k < stagnation_tol * sigma0:
                stagnated = True
                break

        best_x = es.result.xbest.tolist()
        best_fitness = float(es.result.fbest)
        sigma_final = float(es.sigma)
        generations = len(convergence_curve)

        # Monte Carlo CVaR evaluation of best candidate
        np.random.seed(seed + 1)
        mc_losses = []
        for _ in range(n_mc):
            # Perturb candidate by DR noise (±5% uniform)
            x_mc = [
                float(np.clip(v * (1 + np.random.uniform(-0.05, 0.05)), lo[i], hi[i]))
                for i, v in enumerate(best_x)
            ]
            mc_losses.append(loop.run_until_complete(evaluate(x_mc)))

        mc_losses.sort()
        var_idx = int(np.ceil((1 - cvar_alpha) * n_mc)) - 1
        cvar_005 = float(np.mean(mc_losses[var_idx:]))
        cvar_pass = cvar_005 <= cvar_threshold

        loop.close()

        return {
            "best_params": dict(zip(param_names, best_x)),
            "best_fitness": best_fitness,
            "cvar_005": cvar_005,
            "cvar_pass": cvar_pass,
            "cvar_threshold": cvar_threshold,
            "generations": generations,
            "sigma_final": sigma_final,
            "sigma0": sigma0,
            "lambda_pop": lambda_pop,
            "lambda_min": lambda_min,
            "n_params": n,
            "stagnation": stagnated,
            "n_mc": n_mc,
            "cvar_alpha": cvar_alpha,
            "convergence_curve": convergence_curve,
            "provenance": f"cma — seed: {seed} — n: {n} — lambda: {lambda_pop}",
        }

    return await asyncio.get_event_loop().run_in_executor(None, _run_sync)
