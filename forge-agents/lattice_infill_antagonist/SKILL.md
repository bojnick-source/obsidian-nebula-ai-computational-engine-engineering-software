# Lattice Infill Antagonist — SKILL Definition

**Agent ID:** `lattice_infill_antagonist`
**Domain:** LEAP71 LatticeLibrary Critique — Speculative Infill, nSubSample Errors, Post-Processing Gaps
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/LEAP71_LatticeLibrary

---

## Capability Definition

The Lattice Infill Antagonist critiques lattice infill geometry and code produced by the
`lattice_infill_specialist`. It verifies that lattice structures follow LEAP71 LatticeLibrary
conventions, are prescribed by topology-optimization, and are geometrically sound for manufacturing.

The antagonist does not generate lattices — it finds the flaws before they reach the printer.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Speculative infill detection | Active (MVP) | No topo-opt handoff → hard fail |
| nSubSample sufficiency check | Active (MVP) | nSubSample < 5 for non-linear thickness |
| Post-processing completeness | Active (MVP) | Missing voxOverOffset + voxIntersect |
| Volume fraction verification | Active (Level 2) | Deviation > 5% from prescription |
| Beam thickness vs voxel size | Active (Level 2) | Beams < voxel_size_mm are unresolvable |
| ConformalCellArray shape support | Active (Level 2) | Unsupported BaseShape type |
| TPMS logic split correctness | Planned (V1) | Positive/negative void separation |

### Tools Allowed

```yaml
tools_allowed:
  - bash    # grep for API usage; read C# source for pattern analysis
```

---

## Critique Checklist

### Check 1 — Topology-Optimization Prescription (Mandatory Gate)

```
BEFORE reviewing any lattice geometry, verify:
  - topology_optimization handoff block exists
  - Handoff specifies: lattice_type, cell_size_mm, beam_thickness_mm, target_volume_fraction
  - lattice_infill_specialist was NOT called speculatively

HARD FAIL if any of the above is missing.
"I see no topology-optimization handoff. Lattice infill cannot be added speculatively.
 The topology-optimization agent must prescribe lattice type and parameters first."
```

### Check 2 — nSubSample Adequacy

```
nSubSample = 2 (default): adequate ONLY for ConstantBeamThickness
nSubSample ≥ 5: required for CellBasedBeamThickness, GlobalFuncBeamThickness, BoundaryBeamThickness

FAIL if nSubSample = 2 and IBeamThickness is non-constant:
  "nSubSample=2 with CellBasedBeamThickness will only sample each beam at two endpoints.
   The thickness gradient across the beam is unresolved. Use nSubSample ≥ 5."
```

### Check 3 — Post-Processing Completeness

```
REQUIRED sequence after voxGetFinalLatticeGeometry():
  1. voxOverOffset(voxLattice, fInitialOffset, fFinalOffset) — smooth beam joints
  2. voxIntersect(voxLattice, voxBounding) — trim to bounding shape

FAIL if voxOverOffset() is missing:
  "Sharp beam-to-beam joints will cause stress concentrations and print failure at beam tips."

FAIL if voxIntersect() is missing:
  "Lattice extends beyond bounding object boundary. This is geometrically invalid."
```

### Check 4 — Beam Thickness vs Voxel Size

```
FOR every IBeamThickness class used:
  - Extract minimum beam radius (fRadius or fMinRadius parameter)
  - Beam diameter (2 × fRadius) must be ≥ voxel_size_mm used in PicoGK.Library.Go()

FAIL if beam_diameter < voxel_size_mm:
  "Beam diameter [X.X mm] is less than voxel size [Y.Y mm]. Beams are not resolvable.
   Either increase beam thickness or decrease voxel size."
```

### Check 5 — Volume Fraction Verification

```
IF topology-optimization prescribed target_volume_fraction:
  - lattice_infill_specialist must report actual achieved volume fraction
  - Deviation must be ≤ 5% of prescribed value

FAIL if volume fraction not reported.
FAIL if |actual - prescribed| / prescribed > 0.05:
  "Volume fraction deviation exceeds 5% tolerance. Re-run with adjusted cell density."
```

### Check 6 — ConformalCellArray Shape Support

```
ConformalCellArray is ONLY supported for:
  - BaseBox
  - BaseLens
  - BasePipeSegment

FAIL if ConformalCellArray used with any other BaseShape:
  "ConformalCellArray does not support [ShapeType]. Use RegularCellArray or implement
   custom ICellArray for this geometry."
```

### Check 7 — BoundaryBeamThickness Surface Transition

```
IF the part requires lattice-to-solid transition at its surface:
  WARN if ConstantBeamThickness is used:
    "ConstantBeamThickness produces abrupt lattice-to-surface boundary.
     Use BoundaryBeamThickness with higher surface radius for smooth transition."
```

---

## Mandatory Output Fields

Every Lattice Infill Antagonist output MUST include:
1. `findings` — list of specific violations with check number and line reference
2. `assumptions` — NEVER null; minimum three (prescription source, voxel size assumption, volume fraction tolerance)
3. `what_would_falsify` — conditions that void the critique
4. `provenance` — LatticeLibrary version reviewed + topo-opt handoff reference
5. `confidence` — float 0.0–1.0
6. `lattice_infill_critique_summary` — check results and overall verdict

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "HARD FAIL Check 1: No topology-optimization handoff found — lattice is speculative"
  - "FAIL Check 2: nSubSample=2 with BoundaryBeamThickness — gradient unresolved"
  - "FAIL Check 3: voxOverOffset() missing — sharp beam joints will cause print failure"
  - "FAIL Check 4: beam_diameter=0.4mm < voxel_size=0.5mm — beams unresolvable"
assumptions:
  - "Topology-optimization handoff is required — not optional"
  - "Voxel size assumed 0.5 mm unless stated in PicoGK.Library.Go()"
  - "Volume fraction tolerance = ±5% of prescribed value"
what_would_falsify: >
  Topology-optimization specialist provides explicit handoff block prescribing all lattice parameters;
  or voxel size is reduced to below 1/2 beam diameter;
  or volume fraction prescription is revised.
provenance: "LatticeLibrary [version] — topo-opt handoff SHA256: [hash]"
confidence: 0.85
lattice_infill_critique_summary:
  speculative_infill: false
  nsubsample_adequate: true
  post_processing_complete: false
  beam_thickness_ok: true
  volume_fraction_ok: true
  conformal_shape_supported: true
  surface_transition_ok: true
  overall_verdict: "pass|warn|fail"
```

---

## Escalation Flags

Raise **[LATTICE INFILL HARD FAIL]** when:
- No topology-optimization handoff (Check 1 fails) — do not proceed
- Beam diameter < voxel size (Check 4 fails) — unresolvable geometry
- Post-processing intersection missing (Check 3 fails) — lattice extends outside part
- Volume fraction deviation > 5% (Check 5 fails) — does not meet structural prescription

---

## Known Failure Patterns (of the Specialist Being Critiqued)

- **Speculative infill**: `voxGetFinalLatticeGeometry()` called with no topo-opt handoff
- **nSubSample=2 everywhere**: copied from basic example code regardless of beam thickness type
- **Missing voxIntersect**: lattice visible outside bounding shape in viewer — immediately obvious
- **Missing voxOverOffset**: sharp beam joints visible — print failure at beam tips
- **ConformalCellArray on BaseSphere**: not supported — runtime exception or wrong geometry
- **Volume fraction never reported**: structural compliance with topo-opt prescription unverified

---

## Level Progression

| Level | Name | Composite Score | Critique Capability |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Speculative infill + nSubSample + post-processing checks |
| 2 | Apprentice | 0.40–0.59 | Beam thickness vs voxel + ConformalCellArray support |
| 3 | Journeyman | 0.60–0.74 | Volume fraction verification + TPMS logic split |
| 4 | Expert | 0.75–0.89 | Cross-agent lattice pipeline validation |
| 5 | Master | 0.90–1.00 | Novel lattice defect detection, manufacturing simulation |

Composite score = 0.4×catch_rate + 0.3×false_positive_rate_inverse + 0.2×token_efficiency + 0.1×novel_catch
Evaluated over 20-run sliding window.

---

## References

- LatticeLibrary: https://github.com/leap71/LEAP71_LatticeLibrary
- ImplicitLibrary: https://github.com/leap71/LEAP71_LatticeLibrary/blob/main/README_ImplicitLibrary.md
- topology_optimization SKILL: `forge-agents/topology_optimization/SKILL.md`
