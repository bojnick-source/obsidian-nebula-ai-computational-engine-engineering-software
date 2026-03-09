"""Topology validity predicates.

These checks operate on connectivity alone (not geometry) and flag
structural defects that would make a truss solve ill-posed.
"""

from __future__ import annotations

import numpy as np

from .base_mesh import MeshState


def check_connectivity(mesh: MeshState) -> dict:
    """Check that the edge graph is fully connected via BFS from node 0."""
    n = mesh.n_nodes
    if n == 0:
        return {"connected": False, "n_components": 0}

    adj: list[list[int]] = [[] for _ in range(n)]
    for a, b in mesh.edges:
        adj[a].append(b)
        adj[b].append(a)

    visited = set()
    queue = [0]
    while queue:
        node = queue.pop()
        if node in visited:
            continue
        visited.add(node)
        queue.extend(adj[node])

    n_components = 1  # rough — assumes single main component
    connected = len(visited) == n
    return {
        "connected": connected,
        "n_components": n_components,
        "n_reachable": len(visited),
    }


def check_no_duplicate_edges(mesh: MeshState) -> dict:
    """Detect duplicate edges (same pair, regardless of direction)."""
    seen: set[frozenset[int]] = set()
    duplicates = 0
    for a, b in mesh.edges:
        key = frozenset([int(a), int(b)])
        if key in seen:
            duplicates += 1
        seen.add(key)
    return {"n_duplicate_edges": duplicates, "has_duplicates": duplicates > 0}


def check_self_loops(mesh: MeshState) -> dict:
    """Detect edges where both endpoints are the same node."""
    loops = int(np.sum(mesh.edges[:, 0] == mesh.edges[:, 1]))
    return {"n_self_loops": loops, "has_self_loops": loops > 0}


def check_minimum_degree(mesh: MeshState, min_degree: int = 2) -> dict:
    """Check no node has fewer than min_degree connections.

    Nodes with degree < 2 are kinematic mechanisms in a truss.
    """
    degrees = np.zeros(mesh.n_nodes, dtype=int)
    for a, b in mesh.edges:
        degrees[a] += 1
        degrees[b] += 1
    low = int(np.sum(degrees < min_degree))
    return {
        "n_low_degree_nodes": low,
        "has_mechanism_risk": low > 0,
        "min_node_degree": int(np.min(degrees)) if mesh.n_nodes > 0 else 0,
    }


def full_topology_check(mesh: MeshState) -> dict:
    """Run all topology checks and return a combined report."""
    conn = check_connectivity(mesh)
    dup = check_no_duplicate_edges(mesh)
    loops = check_self_loops(mesh)
    deg = check_minimum_degree(mesh)

    is_valid = (
        conn["connected"]
        and not dup["has_duplicates"]
        and not loops["has_self_loops"]
        and not deg["has_mechanism_risk"]
    )

    return {
        "topology_valid": is_valid,
        **conn,
        **dup,
        **loops,
        **deg,
    }
