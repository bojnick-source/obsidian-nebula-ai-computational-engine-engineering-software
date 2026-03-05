# Assembly & DFA Architecture

**Status:** V1
**Agent:** `assembly_specialist`
**Package:** `forge-assembly`

---

## Purpose

The assembly skill is the geometric integration gate between component-level
design and system-level analysis. No component may proceed to system FEA or CAD
export without passing assembly validation.

Three problems it solves that CAD software alone does not:

1. **Tool access** — can a human physically reach every fastener with the actual
   tool, including the tool handle swing arc and hand envelope?

2. **Disassembly cycle detection** — can every component actually be removed in
   some finite sequence, or do components mutually block each other?

3. **Maintenance classification** — are components that need periodic replacement
   accessible in the field, or do they require factory teardown?

---

## Architecture Overview

```
System Decomposition
  └─ IF-XXX Interface Records
       │
       ▼
  ┌──────────────────────────────────────────────────────┐
  │  Assembly Specialist                                  │
  │                                                       │
  │  Step 1: Coordinate system                           │
  │  Step 2: Component placement (interface DAG)         │
  │  Step 3: Geometric interference (trimesh boolean)    │
  │  Step 4: Mass + CG                                   │
  │  Step 5: Fastener spec validation                    │
  │  Step 6: DFA tool access (swept solid volumes)       │──→ HARD FAILURE if blocked
  │  Step 7: Disassembly sequence (Kahn's topo sort)     │──→ HARD FAILURE if cycle
  │  Step 8: Maintenance access (L1/L2/L3)              │──→ WARNING/ERROR per type
  │  Step 9: Vault write (5 notes)                       │
  └──────────────────────────────────────────────────────┘
       │                    │
       ▼                    ▼
  Vault (5 notes)    Handoff Block
                      (→ system-fea, cad-export)
```

---

## Component Placement

All components are placed in a global frame:
- Origin: configurable per project (default: nose tip)
- X: aft, Y: starboard, Z: up, units: mm

The placer resolves a dependency graph: starting from the primary component
(placed at origin), each additional component is placed relative to a
previously-placed neighbour via the `offset_mm` and `rotation_deg` in its
interface record. If any component cannot reach a placed neighbour, placement
halts with an error.

---

## Interference Checking

Uses `trimesh` boolean intersection:

```
For each pair (A, B):
  1. AABB pre-filter (fast rejection)
  2. trimesh.boolean.intersection([mesh_A, mesh_B])
     → volume > 0 → HARD FAILURE (interference)
     → volume = 0 → compute min gap
        < 0.5 mm  → error (clearance violation)
        0.5–2.0 mm → warning
        > 2.0 mm   → clear
```

Fallback when boolean fails: AABB clearance check + `[DFA CHECK APPROXIMATE]` flag.

---

## DFA Tool Access Volume Check

The key insight: a design passes interference checks at nominal positions but
can still be impossible to build if the tool cannot physically reach the fastener.

**Tool swept solid = 3 cylinders:**

```
                fastener axis (insertion direction)
                      ↑
  ┌───────────────────┼──────────────────────────────────┐
  │   Hand envelope   │  Approach cylinder  │  Swing arc │
  │  (grip clearance) │  (tool head fits)   │  (handle   │
  │                   │                     │   rotation) │
  └───────────────────┼──────────────────────────────────┘
                 [fastener head]
```

- **Approach cylinder:** tool head OD × approach_length along fastener axis
- **Swing annulus:** radius = handle length, height = handle cross-section
- **Hand envelope:** grip diameter × grip length (0 for automated tools)

All three are unioned into one solid and boolean-intersected with the full
assembled geometry. If the intersection volume > 1 mm³ for ALL candidate tools
for that fastener type → `ERR_TOOL_ASSEMBLY_TOOL_BLOCKED` (hard failure).

Visual access check: 12 rays cast in a 30° cone around fastener axis.
If all 12 rays hit geometry → blind assembly required (warning).

---

## Disassembly Sequence DAG

```
component A blocks removal of component B if:
  (a) A is within 100 mm laterally of B's extraction path (+Z default), OR
  (b) A's tool access volume collides with B (physical constraint)

DAG → Kahn's algorithm (in_degree sort) → topological removal order

Cycle detection: if len(removal_order) < len(components) after Kahn's:
  → identify cycle components
  → HARD FAILURE: "DISASSEMBLY CYCLE DETECTED"
```

**Recovery from cycle:** At least one joint in the cycle must be redesigned.
Typical fix: convert a bolted joint to a slot/rail system that allows lateral
extraction without removing the blocking component.

---

## Maintenance Access Classification

```
L1-field:    prerequisites=0, non-destructive, bolted/snap, time ≤ 30 min
L2-depot:    prerequisites≤3, non-destructive, time ≤ 240 min
L3-factory:  everything else
```

**Critical rule:** Any component matching `{motor, battery, esc, avionics,
flight controller, servo, gps, receiver, propeller}` that is classified
L3-factory triggers `[SERVICEABILITY DESIGN ERROR]`.

**Target:** field-replaceable mass fraction ≥ 30%.

---

## Vault Outputs (5 Notes)

| Note | Frontmatter Key | Purpose |
|---|---|---|
| `assembly_model.md` | `type: assembly` | Placement table, CG, mass, status summary |
| `interference_report.md` | `type: assembly_interference` | All clearance/interference issues |
| `tool_access_report.md` | `type: assembly_dfa` | DFA blocked fasteners + blind assembly |
| `disassembly_sequence.md` | `type: assembly_disassembly` | Removal order, times, DAG |
| `maintenance_access.md` | `type: assembly_maintenance` | L1/L2/L3 classification per component |

---

## Error Codes

| Code | Type | Condition |
|---|---|---|
| `ERR_TOOL_ASSEMBLY_INTERFERENCE` | Hard | Mesh intersection > 0 |
| `ERR_TOOL_ASSEMBLY_TOOL_BLOCKED` | Hard | No tool reaches fastener |
| `ERR_TOOL_ASSEMBLY_CYCLE` | Hard | Disassembly cycle |
| `ERR_TOOL_ASSEMBLY_UNPLACED` | Hard | Component missing interface link |
| `ERR_TOOL_ASSEMBLY_MASS_OVERRUN` | Hard | Total > budget (without user approval) |
| `WARN_TOOL_ASSEMBLY_CLEARANCE` | Warning | 0.5–2.0 mm gap |
| `WARN_TOOL_ASSEMBLY_BLIND` | Warning | Blind assembly required |
| `WARN_TOOL_ASSEMBLY_SERVICEABILITY` | Warning | Critical component at L3-factory |

---

## What This Skill Does NOT Do

- Generate component geometry → `picogk-geometry`
- Validate individual component strength → `simulation-fea`
- System-level structural FEA → `simulation-fea` with assembly model
- Manufacturing drawings / G-code → `cad-export`
- Fastener torque from first principles → manufacturer specs
- Electrical / fluid / thermal routing
- Replace physical first-article assembly trials

---

## Dependencies

| Package | Purpose | Required |
|---|---|---|
| `trimesh` | Mesh loading, boolean ops, interference, ray casting | Yes (errors gracefully if absent) |
| `scipy` | Spatial queries (used by trimesh) | Yes |
| `numpy` | Vector math | Yes |
| `python-frontmatter` | Vault note serialization | Yes |
| `pyyaml` | Config parsing | Yes |

Install: `pip install trimesh scipy numpy python-frontmatter pyyaml`
