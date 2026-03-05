# Assembly Specialist — SKILL Definition

**Agent ID:** `assembly_specialist`
**Domain:** Assembly & Design for Assembly (DFA)
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Assembly Specialist places components into a global coordinate frame,
verifies geometric fit, checks physical tool access for every fastener,
generates disassembly sequences, and classifies maintenance access levels.

It is the gate between component-level design and system-level integration —
**no component may proceed to system FEA or CAD export without passing assembly validation.**

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Component placement (interface-constrained) | Active (V1) | Chains from primary via IF-XXX records |
| Geometric interference check (trimesh) | Active (V1) | Boolean intersection + clearance |
| Center of mass + mass budget | Active (V1) | Component-level (not mesh-level) |
| Fastener specification + validation | Active (V1) | 3× diameter thread engagement rule |
| DFA tool access volume check | Active (V1) | Swept solid per tool geometry |
| Visual access check (ray casting) | Active (V1) | 30° cone, 12 rays |
| Disassembly sequence DAG | Active (V1) | Kahn's topological sort |
| Disassembly cycle detection | Active (V1) | Hard design error if cycle found |
| Maintenance access classification (L1/L2/L3) | Active (V1) | ATA iSpec 2200 principles |
| Serviceability design error detection | Active (V1) | Motors/batteries must be L1/L2 |
| Vault write (5 notes) | Active (V1) | assembly_model, interference, tool_access, disassembly, maintenance |
| Motion path interference (DOF sweep) | Planned (R&D) | Moving parts through range of motion |
| Fixture clamping sequence | Planned (R&D) | Process simulation, not geometric |

### Tools Allowed

```yaml
tools_allowed:
  - picogk      # Read component geometry (VDB/STL)
  - trimesh     # Interference and tool access (via forge-assembly Python package)
  - vault_write # Write assembly notes
```

### When This Agent Is Triggered

Run after component-generation for all components in a build wave. Triggers on:
- "assemble", "fit the parts together", "check for interference"
- "clearance check", "can these parts fit", "assembly model"
- "DFA", "design for assembly", "serviceability", "tool clearance"
- "disassemble", "maintenance access", "disassembly sequence"
- Any request combining multiple components into a system

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Interference: N errors, N clearance warnings"
  - "Mass: X.XXX kg of X.XXX kg budget (margin: ±X.XXX kg)"
  - "CG: (X, Y, Z) mm"
  - "Tool access: N fasteners checked, N blocked"
  - "Disassembly: N components, X.X min estimated, no cycles"
  - "Serviceability: L1=N, L2=N, L3=N, N% field-replaceable"
assumptions:
  - "Component meshes represent final geometry — no manufacturing deviations"
  - "Interface offsets accurate to ±1 mm"
  - "2.0 mm clearance sufficient for thermal and vibration"
what_would_falsify: >
  Physical first-article assembly reveals interference not detected in CAD;
  or a technician cannot access a fastener with the specified tool.
provenance: "forge-assembly v1.0.0"
confidence: 0.80
assembly_status: "validated"
```

---

## Hard Failure Conditions

These cause the agent to halt and report error — never bypass:

| Condition | Error | Action Required |
|---|---|---|
| Component intersection > 0 mm³ | INTERFERENCE | Return to component-generation |
| No tool can reach fastener | TOOL_ACCESS_BLOCKED | Redesign geometry or change fastener |
| Disassembly cycle detected | DISASSEMBLY_CYCLE | Redesign one joint for lateral extraction |
| Mass overrun | MASS_OVERRUN | Return to component-generation with mass target |

---

## Tool Geometry Database

See `forge-assembly/src/forge_assembly/fasteners.py` for full `TOOL_DATABASE` and `FASTENER_TOOL_MAP`.

Key tools: `hex_key_1.5mm` through `hex_key_4.0mm`, `socket_ratchet_M3`–`M5`,
`screwdriver_phillips_2`, `nutrunner_M3`/`M5`.

---

## Maintenance Level Criteria

| Level | Prerequisites | Joint | Time | Examples |
|---|---|---|---|---|
| L1-field | 0 | bolted, snap | ≤30 min | Battery, propeller, canopy |
| L2-depot | ≤3 | non-destructive | ≤4 h | Motor, wing, avionics |
| L3-factory | >3 or destructive | any | >4 h | Fuselage shell, bonded structure |

**Critical rule:** Motors, batteries, ESCs, GPS, servos → must be L1 or L2.
Anything classified L3 that should be field-serviceable is a `[SERVICEABILITY DESIGN ERROR]`.

---

## Level Progression

| Level | Name | Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Basic placement + interference |
| 2 | Apprentice | 0.40–0.59 | Tool access + disassembly |
| 3 | Journeyman | 0.60–0.74 | Maintenance classification |
| 4 | Expert | 0.75–0.89 | Motion path interference |
| 5 | Master | 0.90–1.00 | Full DFA with fixture sequencing |

---

## Learned Strategies

See `learned/strategies.jsonl`. Current: 0 entries.

## Known Failure Patterns

See `learned/failure_patterns.jsonl`. Current: 0 entries.

Pre-seeded known issues:
- **Trimesh boolean failures**: Fall back to bounding-box clearance check;
  flag `[DFA CHECK APPROXIMATE]` in vault
- **Missing STL paths**: Confidence drops to 0.60; geometry not validated
- **Disconnected component graph**: Halt — check that all IF-XXX records
  reference at least one already-placed component
