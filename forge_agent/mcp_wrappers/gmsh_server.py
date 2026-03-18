"""
forge_agent/mcp_wrappers/gmsh_server.py

GMSH MCP wrapper — exposes GMSH mesh generation via the frozen MCP Wrapper
Envelope Contract v1 (docs/contracts/mcp-wrapper-envelope.md).

Entry point: python -m forge_agent.mcp_wrappers.gmsh_server
Matches servers.yaml: forge_agent.mcp_wrappers.gmsh_server
"""

from __future__ import annotations

import concurrent.futures
import logging
import time

from mcp.server.fastmcp import FastMCP

from forge_agent.mcp_wrappers._envelope import error_envelope, sha256, success_envelope

logger = logging.getLogger(__name__)

TOOL_ID = "gmsh"
WRAPPER_VERSION = "1.0.0"


def create_server() -> FastMCP:
    app = FastMCP(
        name="gmsh-wrapper",
        instructions=(
            "GMSH mesh generation wrapper. "
            "Use generate_mesh for .geo files, generate_mesh_from_stl for .stl inputs. "
            "All responses follow MCP Wrapper Envelope Contract v1."
        ),
    )

    @app.tool()
    def generate_mesh(
        trace_id: str,
        task_id: str,
        invocation_id: str,
        geo_file: str,
        mesh_size: float = 0.1,
        dim: int = 3,
        timeout_ms: int = 60000,
    ) -> dict:
        """
        Generate a mesh from a .geo geometry file using GMSH.

        Args:
            trace_id:      Task trace ID (propagated to all artifacts)
            task_id:       Task identifier
            invocation_id: Unique per-invocation ID (new UUID for each retry)
            geo_file:      Absolute path to the .geo file
            mesh_size:     Maximum characteristic element length (default 0.1)
            dim:           Mesh dimension: 1, 2, or 3 (default 3)
            timeout_ms:    Timeout in milliseconds (default 60000)

        Returns:
            MCP Wrapper Envelope v1 with output.{output_file, element_count, stats}
        """
        t0 = time.perf_counter()

        try:
            import gmsh  # type: ignore[import-untyped]
        except ImportError:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                "gmsh Python package not installed — pip install gmsh",
                (time.perf_counter() - t0) * 1000,
            )

        out_file = geo_file.replace(".geo", ".msh")

        def _run() -> dict:
            gmsh.initialize()
            try:
                gmsh.option.setNumber("General.Terminal", 0)
                gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
                gmsh.merge(geo_file)
                gmsh.model.mesh.generate(dim)
                gmsh.write(out_file)
                stats = gmsh.model.mesh.getStats()
                element_count = int(sum(stats[2])) if stats and len(stats) > 2 else 0
                return {"output_file": out_file, "element_count": element_count, "stats": str(stats)}
            finally:
                gmsh.finalize()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_run)
                result = future.result(timeout=timeout_ms / 1000)
        except concurrent.futures.TimeoutError:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_TIMEOUT",
                f"GMSH timed out after {timeout_ms}ms",
                (time.perf_counter() - t0) * 1000,
                status="timeout",
            )
        except Exception as exc:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                str(exc),
                (time.perf_counter() - t0) * 1000,
            )

        duration_ms = (time.perf_counter() - t0) * 1000

        if result.get("element_count", 0) == 0:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_OUTPUT_INVALID",
                "GMSH produced zero elements — mesh is degenerate",
                duration_ms,
            )

        return success_envelope(
            TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id, result, duration_ms,
            stdout_hash=sha256(result.get("stats", "")),
        )

    @app.tool()
    def generate_mesh_from_stl(
        trace_id: str,
        task_id: str,
        invocation_id: str,
        stl_file: str,
        mesh_size: float = 1.0,
        timeout_ms: int = 60000,
    ) -> dict:
        """
        Generate a volumetric mesh from an STL surface using GMSH.

        Args:
            trace_id:      Task trace ID
            task_id:       Task identifier
            invocation_id: Unique per-invocation ID
            stl_file:      Absolute path to the .stl file
            mesh_size:     Maximum characteristic element length (default 1.0)
            timeout_ms:    Timeout in milliseconds (default 60000)

        Returns:
            MCP Wrapper Envelope v1 with output.{output_file, element_count}
        """
        t0 = time.perf_counter()

        try:
            import gmsh  # type: ignore[import-untyped]
        except ImportError:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                "gmsh Python package not installed — pip install gmsh",
                (time.perf_counter() - t0) * 1000,
            )

        out_file = stl_file.replace(".stl", ".msh")

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
                stats = gmsh.model.mesh.getStats()
                element_count = int(sum(stats[2])) if stats and len(stats) > 2 else 0
                return {"output_file": out_file, "element_count": element_count}
            finally:
                gmsh.finalize()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(_run)
                result = future.result(timeout=timeout_ms / 1000)
        except concurrent.futures.TimeoutError:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_TIMEOUT",
                f"GMSH timed out after {timeout_ms}ms",
                (time.perf_counter() - t0) * 1000,
                status="timeout",
            )
        except Exception as exc:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_SUBPROCESS_FAIL",
                str(exc),
                (time.perf_counter() - t0) * 1000,
            )

        duration_ms = (time.perf_counter() - t0) * 1000

        if result.get("element_count", 0) == 0:
            return error_envelope(
                TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id,
                "ERR_TOOL_OUTPUT_INVALID",
                "GMSH produced zero elements — mesh is degenerate",
                duration_ms,
            )

        return success_envelope(TOOL_ID, WRAPPER_VERSION, trace_id, invocation_id, result, duration_ms)

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    app = create_server()
    app.run()


if __name__ == "__main__":
    main()
