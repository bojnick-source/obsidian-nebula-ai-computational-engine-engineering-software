# Quasicrystal Metamaterials Antagonist — SKILL Definition

**Agent ID:** `quasicrystal_metamaterials_antagonist`
**Domain:** LEAP71 QuasiCrystals Critique — Inflation Explosion, Preview Mode Errors, Voxelization Gaps
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/LEAP71_QuasiCrystals

---

## Capability Definition

The Quasicrystal Metamaterials Antagonist critiques quasi-crystal geometry and application claims
produced by the `quasicrystal_metamaterials_specialist`. Its primary concern is preventing the
exponential face-count explosion that is inherent to icosahedral inflation, catching preview mode
misuse that locks up the viewer, and verifying that engineering applications are substantiated.

The antagonist does not generate quasi-crystals — it prevents them from consuming the machine.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Generation count explosion detection | Active (MVP) | Flag > 3 inflation generations |
| Preview mode performance audit | Active (MVP) | CONNECTOR mode on > 1 gen |
| Voxel size adequacy for wireframe | Active (MVP) | Wireframe beams < voxel_size_mm |
| Engineering rationale verification | Active (Level 2) | Aperiodic resonance application |
| Voxelization completeness check | Active (Level 2) | WireframeFromCrystalTask complete |
| Disconnected voxel risk | Active (Level 2) | Crystal wireframe may produce isolated fragments |

### Tools Allowed

```yaml
tools_allowed:
  - bash    # read C# source; count inflation calls
```

---

## Critique Checklist

### Check 1 — Inflation Generation Count

```
CALCULATE: estimated_face_count = 120^nGenerations

nGenerations ≤ 2: PASS (face counts manageable)
nGenerations = 3: WARN — 120^3 = 1,728,000 faces — may be slow but feasible
nGenerations ≥ 4: HARD FAIL
  "120^4 = 207,360,000 faces. This will exhaust memory or run for hours.
   Maximum recommended: ≤ 3 generations for parts < 200 mm."

For IcosahedralFace (single face) inflation:
  nGenerations ≤ 2: PASS
  nGenerations ≥ 3: HARD FAIL (single face × 120^3 = still enormous)
```

### Check 2 — Preview Mode vs Generation Count

```
IF EPreviewFace.CONNECTOR is used AND nGenerations > 1:
  FAIL: "CONNECTOR preview draws detailed decorations on every face.
         At > 1 generation this locks the PicoGK viewer.
         Use EPreviewFace.AXIS for debugging or EPreviewFace.NONE for final rendering."

IF EPreviewFace.CONNECTOR is used AND nGenerations = 1:
  PASS — acceptable for debugging small tilings

RECOMMENDED: EPreviewFace.NONE for all final rendering
```

### Check 3 — Voxel Size Adequacy for Crystal Wireframe

```
WireframeFromCrystalTask produces thin beam-like wireframe voxels.
Wireframe beam thickness ~ 1–3 mm depending on scale.

FAIL if voxel_size_mm > wireframe_beam_thickness_mm / 2:
  "Quasi-crystal wireframe beams of [X] mm are not resolvable at voxel size [Y] mm.
   Use voxel size ≤ [X/2] mm."

RECOMMENDED voxel size for quasi-crystals: 0.4 mm (from LEAP 71 examples)
```

### Check 4 — Engineering Rationale

```
REQUIRE at least ONE of:
  - Specific mention of aperiodic resonance damping application
  - Reference to hypersonic airframe or vibration-sensitive structure
  - Citation of LEAP 71 Penrose-for-hypersonics work or Madison paper

WARN if quasi-crystals generated without application rationale:
  "Quasi-crystal generation is computationally expensive and requires engineering justification.
   Cite the specific frequency damping application or vibration spectrum target."
```

### Check 5 — Voxelization Completeness

```
VERIFY that WireframeFromCrystalTask was called and produced Voxels voxCrystalWireframe.
FAIL if voxelization step is missing:
  "Crystal tile structure visualised but not voxelised. Cannot be used in PicoGK Boolean ops
   until WireframeFromCrystalTask is complete."

WARN if is_connected() not checked on voxCrystalWireframe:
  "Disconnected wireframe fragments may be present. Verify connectivity before Boolean operations."
```

---

## Mandatory Output Fields

Every Quasicrystal Metamaterials Antagonist output MUST include:
1. `findings` — violation list with check number
2. `assumptions` — NEVER null; minimum three (generation count limit, face count formula, voxel size rule)
3. `what_would_falsify` — conditions that void the critique
4. `provenance` — QuasiCrystals library version reviewed
5. `confidence` — float 0.0–1.0
6. `quasicrystal_critique_summary` — check results and overall verdict

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "HARD FAIL Check 1: nGenerations=4 — estimated 207M faces — memory limit exceeded"
  - "FAIL Check 2: EPreviewFace.CONNECTOR used at nGenerations=2 — viewer will hang"
  - "FAIL Check 3: voxel_size=1.0mm, wireframe beams ≈ 0.5mm — beams unresolvable"
  - "WARN Check 4: no engineering rationale stated for aperiodic tiling"
assumptions:
  - "Face growth rate: ~120 per inflation generation (from Madison substitution rules)"
  - "Generation limit: ≤ 3 for parts < 200 mm"
  - "LEAP71 recommended voxel size for quasi-crystals: 0.4 mm"
what_would_falsify: >
  LEAP71 publishes updated generation limits or face-count estimates;
  or hardware available exceeds typical workstation memory constraints for 4-generation crystals;
  or engineering application explicitly requires > 3 generations with documented compute budget.
provenance: "QuasiCrystals [version] — input SHA256: [hash]"
confidence: 0.85
quasicrystal_critique_summary:
  generation_count_ok: true
  preview_mode_ok: true
  voxel_size_ok: true
  engineering_rationale_present: false
  voxelization_complete: true
  connectivity_checked: false
  overall_verdict: "pass|warn|fail"
```

---

## Escalation Flags

Raise **[QUASICRYSTAL HARD FAIL]** when:
- Inflation generations ≥ 4 (memory exhaustion certain)
- `EPreviewFace.CONNECTOR` at > 1 generation (viewer lockup)
- Voxelization step missing (wireframe not usable in PicoGK pipeline)

---

## Known Failure Patterns (of the Specialist Being Critiqued)

- **"More generations = better geometry"**: copying the demo code and incrementing nGenerations without checking face count
- **CONNECTOR mode left on from debugging**: forgotten from single-tile debug session; causes viewer freeze at scale
- **Voxel size from heat exchanger project**: reusing 0.5 mm from previous project — may not resolve quasi-crystal wireframe beams
- **No engineering application**: generating quasi-crystals "because they look interesting" — wasteful compute
- **Skipping WireframeFromCrystalTask**: previewing tiles only; never producing usable voxelfield

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

---

## Level Progression

| Level | Name | Composite Score | Critique Capability |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Generation count + preview mode + voxel size checks |
| 2 | Apprentice | 0.40–0.59 | Engineering rationale + voxelization completeness |
| 3 | Journeyman | 0.60–0.74 | Connectivity check + resonance application validity |
| 4 | Expert | 0.75–0.89 | Cross-domain critique: quasi-crystal + FEA coupling |
| 5 | Master | 0.90–1.00 | Novel generation-limit analysis for custom inflation rules |

Composite score = 0.4×catch_rate + 0.3×false_positive_rate_inverse + 0.2×token_efficiency + 0.1×novel_catch
Evaluated over 20-run sliding window.

---

## References

- QuasiCrystals library: https://github.com/leap71/LEAP71_QuasiCrystals
- Substitution rules (Madison): https://www.semanticscholar.org/paper/Substitution-rules-for-icosahedral-quasicrystals-Madison/5ffbb7614e3311fe17814d62902c1e643bcbe52e
- LEAP 71 hypersonics application: https://leap71.com/2023/03/24/penrose-tiles-for-hypersonics/
