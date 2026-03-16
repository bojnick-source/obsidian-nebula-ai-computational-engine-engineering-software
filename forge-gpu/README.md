# FORGE GPU Tier

Language tier: **GPU (CUDA / Python / C++)**
Role per [Polyglot Architecture Doctrine](../docs/architecture/polyglot-doctrine.md):
Physics simulation at scale. GPU stacks are only justified by massively parallel physics.

Latency target: **< 10 ms per simulation step** (GPU-bound).

---

## Modules

| Directory | Engine | Language | Status |
|---|---|---|---|
| `warp/` | NVIDIA Warp 1.x — differentiable physics | Python → CUDA JIT | Scaffold |
| `physx/` | NVIDIA PhysX 5.6 — rigid/soft body | C++ / CUDA | Scaffold |
| `newton/` | NVIDIA Newton — robotics articulation | Python | Pending SDK |

---

## Warp (`warp/`)

NVIDIA Warp compiles Python kernels to CUDA at runtime.
No separate `.cu` files — the Python tier directly owns GPU dispatch.

```sh
pip install warp-lang
```

Entry point: `warp/warp_physics_bridge.py` → `WarpPhysicsBridge`

Called by: Python MCP server (`forge-tools/mcp-wrappers/`) via standard import.

## PhysX (`physx/`)

PhysX 5.6 runs natively in C++/CUDA. Compiled when `FORGE_ENABLE_PHYSX=ON`:

```sh
cmake -DFORGE_ENABLE_PHYSX=ON -DPHYSX_ROOT=/opt/PhysX-106 ..
```

Python access via pybind11 bindings (`physx_python_bindings.cpp` — planned).

## Newton (`newton/`)

NVIDIA Newton is in early access as of 2026-03.
Bridge stub is present; production wiring deferred pending public SDK release.

---

## Anti-pattern reminder

> GPU stacks for anything **not** requiring massively parallel physics are banned.
> CUDA adds build complexity only justified by simulation-at-scale.
> Never use this tier for MCP tool dispatch, routing, or logging.
