"""Mesh-LHS Morphogenesis Engine — main pipeline entry point.

Usage
-----
    python -m src.main
    python -m src.main --config config/design_space.yaml
    python -m src.main --config config/design_space.yaml --n-samples 30 --n-gen 3
    python -m src.main --mesh-type hex --n-samples 40 --n-gen 2 --seed 7
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
import yaml

# ── Geometry ──────────────────────────────────────────────────────────────────
from .geometry.parametric_mesh import ParametricMesh

# ── Sampling ──────────────────────────────────────────────────────────────────
from .sampling.lhs import lhs
from .sampling.parameter_map import specs_from_config, map_sample_to_params

# ── Simulation ────────────────────────────────────────────────────────────────
from .simulation.structural_model import build_structural_state
from .simulation.solver import solve_truss

# ── Optimization ──────────────────────────────────────────────────────────────
from .optimization.objectives import compute_objectives, aggregate_score
from .optimization.constraints import (
    check_hard_constraints,
    invalid_result,
    failed_sim_result,
)
from .optimization.ranking import rank_archive
from .optimization.refinement import next_population, convergence_check

# ── Utils ─────────────────────────────────────────────────────────────────────
from .utils.logging_utils import (
    get_logger,
    GenerationTimer,
    log_generation_summary,
    log_sample_progress,
)
from .utils.io import (
    save_metrics,
    save_top_meshes,
    write_summary_report,
    make_run_id,
)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(
    cfg: dict,
    n_samples: int | None = None,
    n_generations: int | None = None,
    seed: int | None = None,
    verbose: bool = False,
) -> list[dict]:
    """Run the full morphogenesis pipeline.

    Parameters
    ----------
    cfg:
        Parsed design_space.yaml configuration dict.
    n_samples:
        Overrides ``sampling.n_samples`` from config.
    n_generations:
        Overrides ``optimization.n_generations`` from config.
    seed:
        Global random seed.
    verbose:
        If True, log each sample individually (debug mode).

    Returns
    -------
    Ranked archive (list of result dicts, feasible first).
    """
    log = get_logger()
    run_id = make_run_id()
    log.info(f"Run ID: {run_id}")

    # ── Config resolution ─────────────────────────────────────────────────────
    samp_cfg = cfg.get("sampling", {})
    opt_cfg = cfg.get("optimization", {})
    out_cfg = cfg.get("output", {})
    scoring_cfg = cfg.get("scoring", {})

    N = n_samples or int(samp_cfg.get("n_samples", 40))
    G = n_generations or int(opt_cfg.get("n_generations", 3))
    _seed = seed if seed is not None else int(samp_cfg.get("seed", 42))
    maximin = int(samp_cfg.get("maximin_iters", 100))
    results_dir = str(out_cfg.get("results_dir", "results"))
    top_k = int(out_cfg.get("save_top_k", 10))

    specs = specs_from_config(cfg.get("parameters", []))
    n_dim = len(specs)

    log.info(f"Parameters: {n_dim}  Samples/gen: {N}  Generations: {G}")

    # ── Base mesh ─────────────────────────────────────────────────────────────
    pm = ParametricMesh.from_config(cfg.get("base_mesh", {}))
    log.info(f"Base mesh: {pm.base.n_nodes} nodes, {pm.base.n_edges} edges")

    # ── Initial LHS population ────────────────────────────────────────────────
    rng_global = np.random.default_rng(_seed)
    H = lhs(N, n_dim, seed=int(rng_global.integers(0, 2**31)), maximin_iters=maximin)

    archive: list[dict] = []

    # ── Generation loop ───────────────────────────────────────────────────────
    for gen in range(1, G + 1):
        with GenerationTimer(f"Generation {gen}/{G}", log):
            gen_results: list[dict] = []

            for si in range(len(H)):
                params = map_sample_to_params(H[si], specs)

                # 1. Morph
                morphed = pm.apply(params)

                # 2. Hard constraint: mesh validity
                if not morphed.is_simulation_ready:
                    r = invalid_result(params, morphed.quality, reason="mesh/topology invalid")
                    gen_results.append(r)
                    if verbose:
                        log_sample_progress(si, len(H), False, float("inf"), "invalid mesh", log)
                    continue

                # 3. Build structural state
                state = build_structural_state(morphed.mesh, params, cfg)

                # 4. Solve
                result = solve_truss(state)

                # 5. Check hard constraints (post-solve)
                feasible, reason = check_hard_constraints(morphed, state, result, cfg)
                if not feasible:
                    r = failed_sim_result(params, morphed.quality, reason)
                    gen_results.append(r)
                    if verbose:
                        log_sample_progress(si, len(H), False, float("inf"), reason, log)
                    continue

                # 6. Compute objectives and aggregate score
                objectives = compute_objectives(state, result, morphed.quality, scoring_cfg)
                score = aggregate_score(objectives, scoring_cfg)

                r = {
                    "params": params,
                    "mesh": morphed.mesh,
                    "objectives": objectives,
                    "quality": morphed.quality,
                    "score": score,
                    "feasible": True,
                    "reason": "ok",
                    "generation": gen,
                }
                gen_results.append(r)

                if verbose:
                    log_sample_progress(si, len(H), True, score, "ok", log)

            archive.extend(gen_results)

            # Generation summary
            feasible_gen = [r for r in gen_results if r.get("feasible")]
            best_score = min((r["score"] for r in feasible_gen), default=float("inf"))
            best_compliance = None
            best_mass = None
            if feasible_gen:
                best = min(feasible_gen, key=lambda r: r["score"])
                best_compliance = best["objectives"]["compliance"]
                best_mass = best["objectives"]["mass"]

            log_generation_summary(
                gen, len(gen_results), len(feasible_gen),
                len(gen_results) - len(feasible_gen),
                best_score, best_compliance, best_mass, log,
            )

            # Early stopping
            if convergence_check(archive):
                log.info("Convergence detected — stopping early.")
                break

            # Adaptive resampling for next generation (skip last gen)
            if gen < G:
                H = next_population(
                    gen_results, archive, specs, N, cfg,
                    seed=int(rng_global.integers(0, 2**31)),
                )

    # ── Rank and save ─────────────────────────────────────────────────────────
    pareto_obj = opt_cfg.get("pareto_objectives", ["compliance", "mass"])
    ranked = rank_archive(archive, pareto_objectives=pareto_obj)

    log.info(f"Saving results → {results_dir}")
    metric_path = save_metrics(ranked, results_dir, run_id)
    log.info(f"  Metrics: {metric_path}")

    if out_cfg.get("save_all_metrics", True):
        save_top_meshes(ranked, results_dir, run_id, top_k)

    report_path = write_summary_report(ranked, cfg, results_dir, run_id, top_k)
    log.info(f"  Report : {report_path}")

    # ── Print top-5 to stdout ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  TOP CANDIDATES")
    print("=" * 60)
    feasible_ranked = [r for r in ranked if r.get("feasible")]
    for r in feasible_ranked[:5]:
        obj = r.get("objectives", {})
        print(
            f"  Rank {r['rank']:3d} | Pareto {r.get('pareto_rank','?')} "
            f"| score {r['score']:.5f}"
        )
        print(
            f"    compliance={obj.get('compliance', float('inf')):.4e}"
            f"  mass={obj.get('mass', float('inf')):.4e}"
            f"  max_stress={obj.get('max_stress', float('inf')):.4e}"
        )
        print(f"    params: {r['params']}")
        print()

    return ranked


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mesh-LHS Morphogenesis Engine")
    p.add_argument(
        "--config", "-c",
        default="config/design_space.yaml",
        help="Path to design_space.yaml (default: config/design_space.yaml)",
    )
    p.add_argument("--n-samples", "-n", type=int, default=None, help="Samples per generation")
    p.add_argument("--n-gen", "-g", type=int, default=None, help="Number of generations")
    p.add_argument("--seed", type=int, default=None, help="Random seed")
    p.add_argument("--verbose", "-v", action="store_true", help="Log each sample")
    p.add_argument(
        "--mesh-type",
        choices=["grid", "hex", "radial"],
        default=None,
        help="Override base mesh type",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    config_path = pathlib.Path(args.config)
    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with config_path.open() as f:
        cfg = yaml.safe_load(f)

    cfg["__source"] = str(config_path)

    # CLI overrides
    if args.mesh_type:
        cfg.setdefault("base_mesh", {})["type"] = args.mesh_type

    run_pipeline(
        cfg,
        n_samples=args.n_samples,
        n_generations=args.n_gen,
        seed=args.seed,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
