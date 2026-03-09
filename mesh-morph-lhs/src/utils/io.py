"""IO helpers — save/load results, meshes, and reports."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime

import numpy as np

from ..geometry.base_mesh import MeshState


# ── JSON serialisation helpers ────────────────────────────────────────────────

class _SafeEncoder(json.JSONEncoder):
    def default(self, obj: object) -> object:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            f = float(obj)
            if not (f == f):   # NaN
                return None
            if f == float("inf") or f == float("-inf"):
                return None
            return f
        if isinstance(obj, MeshState):
            return {
                "vertices": obj.vertices.tolist(),
                "edges": obj.edges.tolist(),
                "faces": obj.faces.tolist() if obj.faces is not None else None,
                "metadata": obj.metadata,
            }
        return super().default(obj)


def _prepare_for_json(obj: object) -> object:
    """Recursively convert non-serialisable objects in a nested structure."""
    if isinstance(obj, dict):
        return {k: _prepare_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_prepare_for_json(v) for v in obj]
    if isinstance(obj, MeshState):
        return {
            "vertices": obj.vertices.tolist(),
            "edges": obj.edges.tolist(),
            "metadata": obj.metadata,
        }
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and (obj != obj or abs(obj) == float("inf")):
        return None
    return obj


# ── Save results ──────────────────────────────────────────────────────────────

def save_metrics(results: list[dict], results_dir: str | pathlib.Path, run_id: str) -> pathlib.Path:
    """Serialise the ranked results archive to JSON."""
    out_dir = pathlib.Path(results_dir) / "metrics"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{run_id}_results.json"
    cleaned = _prepare_for_json(
        [
            {
                "rank": r.get("rank"),
                "pareto_rank": r.get("pareto_rank"),
                "score": r.get("score"),
                "feasible": r.get("feasible"),
                "reason": r.get("reason", "ok"),
                "params": r.get("params"),
                "objectives": r.get("objectives"),
                "quality": r.get("quality"),
            }
            for r in results
        ]
    )
    path.write_text(json.dumps(cleaned, indent=2))
    return path


def save_mesh_npz(mesh: MeshState, path: str | pathlib.Path) -> None:
    """Save a mesh to a compressed NumPy archive."""
    np.savez_compressed(
        str(path),
        vertices=mesh.vertices,
        edges=mesh.edges,
        **({} if mesh.faces is None else {"faces": mesh.faces}),
    )


def load_mesh_npz(path: str | pathlib.Path) -> MeshState:
    data = np.load(str(path))
    faces = data["faces"] if "faces" in data else None
    return MeshState(
        vertices=data["vertices"],
        edges=data["edges"],
        faces=faces,
    )


def save_top_meshes(
    ranked: list[dict],
    results_dir: str | pathlib.Path,
    run_id: str,
    top_k: int = 10,
) -> None:
    """Save the top-K meshes to the meshes/ sub-directory."""
    mesh_dir = pathlib.Path(results_dir) / "meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    for r in ranked[:top_k]:
        if r.get("mesh") is None:
            continue
        rank = r.get("rank", 0)
        path = mesh_dir / f"{run_id}_rank{rank:03d}.npz"
        save_mesh_npz(r["mesh"], path)


def make_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S")


# ── Text report ───────────────────────────────────────────────────────────────

def write_summary_report(
    ranked: list[dict],
    config: dict,
    results_dir: str | pathlib.Path,
    run_id: str,
    top_k: int = 10,
) -> pathlib.Path:
    """Write a human-readable text report of the top-K candidates."""
    report_dir = pathlib.Path(results_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{run_id}_report.txt"

    lines: list[str] = [
        "=" * 72,
        f"  Mesh-LHS Morphogenesis Engine — Run Report",
        f"  Run ID : {run_id}",
        f"  Config : {config.get('__source', 'design_space.yaml')}",
        "=" * 72,
        "",
        f"Total evaluated : {len(ranked)}",
        f"Feasible        : {sum(1 for r in ranked if r.get('feasible'))}",
        f"Infeasible      : {sum(1 for r in ranked if not r.get('feasible'))}",
        "",
        f"Top {min(top_k, len(ranked))} candidates:",
        "-" * 72,
    ]

    for r in ranked[:top_k]:
        obj = r.get("objectives") or {}
        lines += [
            f"  Rank {r.get('rank', '?')} | Pareto {r.get('pareto_rank', '?')} | score {r.get('score', float('inf')):.5f}",
            f"    compliance={obj.get('compliance', float('inf')):.4e}  mass={obj.get('mass', float('inf')):.4e}",
            f"    max_stress={obj.get('max_stress', float('inf')):.4e}  max_disp={obj.get('max_displacement', float('inf')):.4e}",
            f"    params: {r.get('params', {})}",
            "",
        ]

    path.write_text("\n".join(lines))
    return path
