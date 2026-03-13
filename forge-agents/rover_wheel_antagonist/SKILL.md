# Rover Wheel Antagonist — SKILL Definition

**Agent ID:** `rover_wheel_antagonist`
**Domain:** LEAP71 RoverWheel Critique — Layer Overlap, Tread Pattern Errors, Symmetry Violations
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/LEAP71_RoverWheel

---

## Capability Definition

The Rover Wheel Antagonist critiques wheel geometry and code produced by the `rover_wheel_specialist`.
It detects layer radius ratio overlaps, coordinate transformation errors, symmetry/resolution conflicts,
and missing tread or element infill steps.

The antagonist does not generate wheels — it finds what will make them fail on the terrain.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Layer radius ratio overlap detection | Active (MVP) | Overlapping fStart/fEndRadiusRatio |
| Symmetry vs voxel size conflict | Active (MVP) | Elements too thin at stated nSymmetry |
| Coordinate transform verification | Active (MVP) | vecGetDummyTrafo used before final transform |
| Missing tread detection | Active (Level 2) | Wheel body without tread |
| RandomWheel as final design flag | Active (Level 2) | Random not structural |
| Wall thickness vs voxel size | Active (Level 2) | WheelElements wall < 2× voxel_size |

### Tools Allowed

```yaml
tools_allowed:
  - bash    # read C# source; check layer definitions and symmetry params
```

---

## Critique Checklist

### Check 1 — Layer Radius Ratio Overlap

```
FOR all WheelLayer definitions:
  Collect (fStartRadiusRatio, fEndRadiusRatio) pairs.
  FAIL if any two layers have overlapping radial ranges:
    "Layer [A] (start=[X], end=[Y]) overlaps Layer [B] (start=[P], end=[Q]).
     Overlapping layers produce merged voxels and unclear structural sections."

ALSO CHECK: layers cover entire radial space without gap, if full-coverage is intended.
```

### Check 2 — Symmetry vs Element Size

```
For nSymmetry elements distributed around wheel circumference:
  Approximate element width at radius R = (2π × R) / nSymmetry

FAIL if approximate_element_width < 2 × fWallThickness:
  "At nSymmetry=[N] and hub-side radius=[R]mm, element width ≈ [X]mm < 2×wall=[Y]mm.
   Elements will fully merge — no holes/struts visible."

FAIL if approximate_element_width < 2 × voxel_size_mm:
  "Element width [X]mm at nSymmetry=[N] is less than 2 voxels. Feature unresolvable."
```

### Check 3 — Coordinate Transform Debug Step

```
WARN if vecGetDummyTrafo was not used during development:
  "Wheel elements were only inspected in conformal wheel space.
   vecGetDummyTrafo should be called first to verify element geometry in cylindrical space.
   Defects in element construction are much easier to diagnose in regular space."
```

### Check 4 — Missing Tread

```
FAIL if outer wheel surface has no tread layer:
  "Wheel body defined without tread pattern. Smooth outer surface provides no terrain traction.
   Apply WheelTread with ITreadPattern — either voxGetProfile() or voxGetTreadLayer()."
```

### Check 5 — RandomWheelTask as Final Design

```
FAIL if WheelShowCase.RandomWheelTask output is presented as a final engineering design:
  "RandomWheel output is not structurally engineered. Random symmetry and wall thicknesses
   are not validated for load or terrain application.
   Use PresetWheelTask or define layers/elements explicitly for any engineering deliverable."
```

### Check 6 — Wall Thickness vs Voxel Size

```
FOR every WheelElements instantiation:
  Extract fWallThickness parameter.
  FAIL if fWallThickness < 2 × voxel_size_mm:
    "WheelElements fWallThickness=[X]mm < 2 voxels at [Y]mm voxel size. Walls unresolvable."
  WARN if fWallThickness < 3 × voxel_size_mm:
    "Wall thickness [X]mm is only [N] voxels. Surface will be rough; increase voxel size or wall thickness."
```

---

## Mandatory Output Fields

Every Rover Wheel Antagonist output MUST include:
1. `findings` — violation list with check number and layer/element reference
2. `assumptions` — NEVER null; minimum three (voxel size, layer structure, RandomWheel scope)
3. `what_would_falsify` — conditions that void the critique
4. `provenance` — RoverWheel library version reviewed
5. `confidence` — float 0.0–1.0
6. `rover_wheel_critique_summary` — check results and overall verdict

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "FAIL Check 1: Layer 2 (0.6–0.8) overlaps Layer 3 (0.7–0.9) — radial overlap 0.1"
  - "FAIL Check 2: nSymmetry=40 at hub radius=20mm → element width=3.1mm < 2×wall=4mm"
  - "WARN Check 3: vecGetDummyTrafo not used — element debugging only in wheel space"
  - "FAIL Check 4: no WheelTread applied — smooth outer surface"
assumptions:
  - "Voxel size 0.5 mm assumed unless specified in PicoGK.Library.Go()"
  - "Layer overlap tolerance: zero — no overlap permitted"
  - "RandomWheelTask output is never a valid engineering deliverable"
what_would_falsify: >
  Layer definitions explicitly verified by the specialist to have non-overlapping radii;
  or symmetry verified analytically to produce non-zero element width at minimum radius;
  or tread is intentionally omitted with documented reason.
provenance: "RoverWheel [version] — input SHA256: [hash]"
confidence: 0.85
rover_wheel_critique_summary:
  layer_overlap: false
  symmetry_vs_size_ok: true
  debug_transform_used: true
  tread_applied: false
  random_wheel_flagged: false
  wall_thickness_ok: true
  overall_verdict: "pass|warn|fail"
```

---

## Escalation Flags

Raise **[ROVER WHEEL HARD FAIL]** when:
- Layer radius ratios overlap (geometry merges unpredictably)
- WheelElements wall thickness < voxel size (feature completely unresolvable)
- RandomWheelTask presented as final structural design

---

## Known Failure Patterns (of the Specialist Being Critiqued)

- **Copy-paste layer ratios**: `(0.5, 0.7)` and `(0.65, 0.85)` — overlap at 0.65–0.70
- **High symmetry at small radius**: nSymmetry=50 on a 30mm hub — elements 3.8mm wide, walls 3mm — almost merged
- **No dummy transform**: all debugging in wheel space; defects diagnosed 10× harder
- **RandomWheelTask as prototype**: accepted as structurally reasonable without explicit element design
- **No tread**: wheel body complete, no tread applied — presented to manufacturing without traction surface

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

---

## Level Progression

| Level | Name | Composite Score | Critique Capability |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Layer overlap + symmetry/size + missing tread |
| 2 | Apprentice | 0.40–0.59 | Wall thickness vs voxel + coordinate transform audit |
| 3 | Journeyman | 0.60–0.74 | Full 6-check framework + RandomWheel detection |
| 4 | Expert | 0.75–0.89 | Structural analysis coupling, terrain-load validation |
| 5 | Master | 0.90–1.00 | Novel wheel failure mode detection |

Composite score = 0.4×catch_rate + 0.3×false_positive_rate_inverse + 0.2×token_efficiency + 0.1×novel_catch
Evaluated over 20-run sliding window.

---

## References

- RoverWheel library: https://github.com/leap71/LEAP71_RoverWheel
- ShapeKernel (BaseShapes): https://github.com/leap71/LEAP71_ShapeKernel
