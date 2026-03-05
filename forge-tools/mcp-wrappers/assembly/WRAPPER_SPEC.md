# Assembly MCP Wrapper Specification

**Tool ID:** `assembly`
**Version:** `1.0.0`
**Status:** V1
**Wrapper envelope:** MCP Wrapper Envelope v1 (see `docs/contracts/mcp-wrapper-envelope.md`)

---

## Invocation Model

The assembly wrapper is a **Python subprocess** wrapping `forge-assembly`.
It runs the full 9-step AssemblyOrchestrator pipeline and returns a
structured result conforming to the MCP response envelope.

```
[Orchestrator]
    │ MCP tool call: assembly
    ▼
[Assembly MCP Wrapper]
    │ subprocess: python -m forge_assembly.assembler
    ▼
[forge-assembly package]
    ├── placement.py      (Steps 1-2)
    ├── interference.py   (Step 3)  ← requires trimesh
    ├── mass_props.py     (Step 4)
    ├── fasteners.py      (Step 5)
    ├── tool_access.py    (Step 6)  ← requires trimesh
    ├── disassembly.py    (Step 7)
    ├── maintenance.py    (Step 8)
    └── vault_writer.py   (Step 9)
    │
    ▼
[MCP Response Envelope]
```

---

## Sandbox Policy

- **Filesystem access:** Read component STL/VDB files; write 5 vault notes
- **Network:** None
- **Process spawn:** None
- **Max wall time:** 300 s (trimesh boolean operations can be slow on large meshes)
- **Max memory:** 4 GB (large mesh unions may exceed 1 GB)
- **Degraded mode on timeout:** `DEGRADED_SOLVER` — return bounding-box interference
  check only, skip tool access swept volumes

---

## Degraded Mode

If trimesh is unavailable or boolean operations fail:
1. Fall back to AABB (axis-aligned bounding box) clearance check
2. Skip swept-volume tool access check
3. Mark result: `degraded: true`, `degraded_reason: "trimesh_boolean_failed"`
4. Set confidence: 0.4 (geometry not fully validated)
5. Flag `[DFA CHECK APPROXIMATE]` in all vault outputs

---

## Timeout Policy

- 300 s hard timeout
- On timeout: activate `DEGRADED_SOLVER`, return partial results
- Retry: 0 (assembly is deterministic — retrying will produce same result)

---

## Error Codes

| Code | Condition |
|---|---|
| `ERR_TOOL_ASSEMBLY_INTERFERENCE` | Hard interference (intersection > 0) |
| `ERR_TOOL_ASSEMBLY_TOOL_BLOCKED` | No tool can reach fastener |
| `ERR_TOOL_ASSEMBLY_CYCLE` | Disassembly cycle detected |
| `ERR_TOOL_ASSEMBLY_UNPLACED` | Component(s) cannot be placed (missing interface) |
| `ERR_TOOL_ASSEMBLY_MASS_OVERRUN` | Mass exceeds budget |
| `WARN_TOOL_ASSEMBLY_CLEARANCE` | Clearance < 2 mm (not zero) |
| `WARN_TOOL_ASSEMBLY_BLIND` | Visual access blocked — blind assembly required |
| `WARN_TOOL_ASSEMBLY_SERVICEABILITY` | Frequently-replaced component at L3-factory |
