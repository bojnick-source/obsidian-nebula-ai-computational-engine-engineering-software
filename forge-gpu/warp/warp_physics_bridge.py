"""
forge-gpu/warp/warp_physics_bridge.py

NVIDIA Warp differentiable physics bridge for FORGE.

Language tier: GPU (Python → CUDA JIT)
Role per Polyglot Architecture Doctrine: physics simulation at scale.
Warp compiles Python kernels to CUDA at runtime — no separate .cu files.

Latency target: < 10 ms per simulation step (GPU-bound).

Dependencies
------------
    pip install warp-lang        # NVIDIA Warp
    # CUDA 11.8+ and a CUDA-capable GPU required at runtime.

Usage
-----
    bridge = WarpPhysicsBridge(device="cuda:0")
    result = bridge.run_rigid_body_step(state)

This module is called by the Python MCP server (forge-tools/mcp-wrappers/)
which runs in the Python language tier. Warp is the bridge from Python
into the GPU tier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    import warp as wp
    _WARP_AVAILABLE = True
except ImportError:
    _WARP_AVAILABLE = False


# ── Data contracts ─────────────────────────────────────────────────────────────

@dataclass
class RigidBodyState:
    """Input state for a rigid-body simulation step."""
    positions: Any          # (N, 3) float32 — body positions in metres
    velocities: Any         # (N, 3) float32 — linear velocities m/s
    orientations: Any       # (N, 4) float32 — quaternions [w, x, y, z]
    angular_velocities: Any # (N, 3) float32 — rad/s
    masses: Any             # (N,) float32 — kg
    dt: float = 1.0 / 60.0 # simulation timestep in seconds


@dataclass
class RigidBodyResult:
    """Output from one simulation step."""
    positions: Any
    velocities: Any
    orientations: Any
    angular_velocities: Any
    step_time_ms: float
    error: str = ""


# ── Warp kernels ───────────────────────────────────────────────────────────────

if _WARP_AVAILABLE:
    @wp.kernel
    def _integrate_positions(
        pos:  wp.array(dtype=wp.vec3),
        vel:  wp.array(dtype=wp.vec3),
        dt:   float,
        out:  wp.array(dtype=wp.vec3),
    ):
        """Semi-implicit Euler integration: x_{n+1} = x_n + v_n * dt."""
        i = wp.tid()
        out[i] = pos[i] + vel[i] * dt

    @wp.kernel
    def _apply_gravity(
        vel:  wp.array(dtype=wp.vec3),
        dt:   float,
        g:    float,
        out:  wp.array(dtype=wp.vec3),
    ):
        """Apply gravitational acceleration (y-down convention)."""
        i = wp.tid()
        out[i] = wp.vec3(vel[i][0], vel[i][1] - g * dt, vel[i][2])


# ── Bridge class ───────────────────────────────────────────────────────────────

class WarpPhysicsBridge:
    """
    Thin Python bridge between the FORGE MCP server and NVIDIA Warp GPU kernels.

    The MCP server (Python tier) owns the I/O and message serialisation.
    This class owns the GPU arrays and kernel dispatch.

    Parameters
    ----------
    device : str
        Warp device string, e.g. "cuda:0" or "cpu" (for unit-test fallback).
    gravity : float
        Gravitational acceleration in m/s² (default: 9.81).
    """

    GRAVITY_MS2 = 9.81

    def __init__(self, device: str = "cuda:0", gravity: float = GRAVITY_MS2) -> None:
        if not _WARP_AVAILABLE:
            raise RuntimeError(
                "NVIDIA Warp is not installed. "
                "Run: pip install warp-lang\n"
                "CUDA 11.8+ and a CUDA-capable GPU are required at runtime."
            )
        wp.init()
        self.device = device
        self.gravity = gravity

    def run_rigid_body_step(self, state: RigidBodyState) -> RigidBodyResult:
        """Execute one semi-implicit Euler step on the GPU.

        Returns updated state. All array I/O is in numpy format.
        """
        import time

        t0 = time.perf_counter()

        # Upload to GPU
        pos  = wp.array(state.positions,  dtype=wp.vec3, device=self.device)
        vel  = wp.array(state.velocities, dtype=wp.vec3, device=self.device)

        vel_out = wp.zeros_like(vel)
        pos_out = wp.zeros_like(pos)

        n = pos.shape[0]

        # Apply gravity
        wp.launch(_apply_gravity, dim=n, inputs=[vel, state.dt, self.gravity, vel_out],
                  device=self.device)

        # Integrate positions
        wp.launch(_integrate_positions, dim=n, inputs=[pos, vel_out, state.dt, pos_out],
                  device=self.device)

        wp.synchronize_device(self.device)
        step_ms = (time.perf_counter() - t0) * 1000.0

        return RigidBodyResult(
            positions=pos_out.numpy(),
            velocities=vel_out.numpy(),
            orientations=state.orientations,      # rotation integration: TODO
            angular_velocities=state.angular_velocities,
            step_time_ms=round(step_ms, 3),
        )
