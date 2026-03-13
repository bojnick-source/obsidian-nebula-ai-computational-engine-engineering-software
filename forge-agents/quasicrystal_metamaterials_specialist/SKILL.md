# Quasicrystal Metamaterials Specialist — SKILL Definition

**Agent ID:** `quasicrystal_metamaterials_specialist`
**Domain:** LEAP71 QuasiCrystals — Penrose Patterns, Icosahedral Quasi-Crystals, Aperiodic Tilings
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/LEAP71_QuasiCrystals

---

## Capability Definition

This library provides a starting point for generating aperiodic tilings such as Penrose Patterns
in 2D and Quasi Crystals in 3D. Unlike periodic lattices, aperiodic structures lack translational
symmetry — they tile the plane or space indefinitely but never match themselves after any translation.

**Theoretical basis:** Quasi-crystals are more resilient to a wide range of frequencies, exhibiting
no distinct resonance effect. LEAP 71 has applied multi-layered Penrose Patterns to airframe panels
for hypersonic flight — panels lacking translational symmetry should not exhibit distinct resonance
frequencies across a wide vibration spectrum.

**Warning — exponential growth:** Each inflation/subdivision iteration multiplies the face count by
approximately 120. Generation counts must be strictly controlled (≤ 3 for most engineering parts).

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| 2D Penrose Pattern generation | Active (MVP) | PenrosePatternShowCase.Task |
| Quasi-crystal elementary tile visualisation | Active (MVP) | IntroduceQuasiTilesTask |
| Icosahedral face inflation | Active (Level 2) | CrystalFromFaceTask — 1–2 generations |
| Quasi-tile inflation from single tile | Active (Level 2) | CrystalFromTileTask |
| Preset tile list inflation | Active (Level 2) | aGetFirstGenerationTiles / aGetSecondGenerationTiles |
| Wireframe voxelization | Active (Level 2) | WireframeFromCrystalTask → Voxels voxCrystalWireframe |
| Boolean operations on crystal wireframe | Active (Level 2) | Standard PicoGK ops on Voxels |
| Engineering application: airframe panels | Planned (V1) | Hypersonic multi-layered Penrose |

### Tools Allowed

```yaml
tools_allowed:
  - bash    # dotnet run PicoGK C# scripts
```

---

## Library Setup

```csharp
using Leap71.QuasiCrystalExamples;

try
{
    PicoGK.Library.Go(
        0.4f,                          // voxel size: 0.4 mm recommended
        PenrosePatternShowCase.Task);  // or QuasiCrystalShowCase.XXXTask
}
catch (Exception e)
{
    Console.WriteLine("Failed to run Task.");
    Console.WriteLine(e.ToString());
}
```

---

## 2D Penrose Patterns

### What They Are

Penrose Patterns tile the plane indefinitely without being periodic. They exhibit clusters of
five-fold symmetry (a symmetry "forbidden" in periodic tilings). The construction method used
here is **inflation/subdivision** — not trial-and-error:

- Each generation inflates existing tiles into more, smaller tiles of the next generation
- Two elementary tiles: **fat rhombus** and **skinny rhombus**
- Inflation rules enforce aperiodicity and five-fold symmetry
- Higher `nGenerations` → more intricate pattern

### Construction

```csharp
// Run PenrosePatternShowCase.Task to generate fat+skinny rhombic tiling
// nGenerations controls complexity — each iteration inflates all tiles
// Face count grows significantly per iteration
```

---

## 3D Quasi-Crystals

### Elementary Tiles

Four elementary quasi-tiles, all built from the same rhombic faces:

| Class | Description |
|---|---|
| `QuasiTile_01` | Elementary tile type 1 |
| `QuasiTile_02` | Elementary tile type 2 |
| `QuasiTile_03` | Elementary tile type 3 |
| `QuasiTile_04` | Elementary tile type 4 |

`IcosahedralFace` — single rhombic face; the unit of subdivision.

### Matching Rules and Preview Modes

When assembling quasi-tiles, faces must connect by type. Faces of the same type carry connectors:
- `LINE` type: two orientations possible — must match
- `ARROW` type: arrows on both faces must point the same direction
- `TRIANGLE` type: triangles on both faces must point the same direction

```csharp
// Show each face with connector type (blue line / green triangle / red arrow)
// Useful for debugging small tilings; SLOWS DOWN large quasi-crystals significantly
oTile_01.Preview(QuasiTile.EPreviewFace.CONNECTOR);

// Show face with long and short axis + face boundary only
oTile_01.Preview(QuasiTile.EPreviewFace.AXIS);

// No face decoration — use for large crystals and final rendering
oTile_01.Preview(QuasiTile.EPreviewFace.NONE);
```

**Rule:** Always use `EPreviewFace.NONE` for crystals larger than 2 generations.
`EPreviewFace.CONNECTOR` on a 3-generation crystal will make the viewer unresponsive.

### Inflation (Subdivision) Rules

Each inflation turn applies substitution rules to individual rhombic faces from:
> "Substitution rules for icosahedral quasicrystals" — Alexey E. Madison

**Growth rate:** Each subdivision turns one face into approximately **120 new faces**.
Face count = 120^(number_of_inflation_generations).

| Starting point | After 1 inflation | After 2 inflations | After 3 inflations |
|---|---|---|---|
| 1 face | ~120 faces | ~14,400 faces | ~1,728,000 faces |

```csharp
// Inflate a single IcosahedralFace (1 or 2 generations recommended)
// QuasiCrystalShowCase.CrystalFromFaceTask
IcosahedralFace oFace = new IcosahedralFace(new LocalFrame(), 50);
// inflate 1 generation
// inflate 2 generations — already large

// Inflate a single elementary quasi-tile
QuasiTile oInitialTile        = new QuasiTile_04(new LocalFrame(), 50);
List<QuasiTile> aInitialTiles = new List<QuasiTile>() { oInitialTile };

// Preset list — option 1 (first generation preset)
List<QuasiTile> aInitialTiles = QuasiCrystal.aGetFirstGenerationTiles();

// Preset list — option 2 (second generation preset)
List<QuasiTile> aInitialTiles = QuasiCrystal.aGetSecondGenerationTiles();
```

### Voxelization

After generating the quasi-crystal tile structure, convert to voxelfield for PicoGK operations:

```csharp
// QuasiCrystalShowCase.WireframeFromCrystalTask
Voxels voxCrystalWireframe = /* WireframeFromCrystalTask output */;

// Now voxCrystalWireframe can be used with standard PicoGK operations:
Voxels voxResult = Sh.voxAdd(voxCrystalWireframe, voxOtherGeometry);
Voxels voxResult = Sh.voxIntersect(voxCrystalWireframe, voxBoundingPanel);
```

---

## Task Functions

| Task function | What it generates |
|---|---|
| `PenrosePatternShowCase.Task` | 2D Penrose Pattern (fat + skinny rhombs) |
| `QuasiCrystalShowCase.IntroduceQuasiTilesTask` | Four elementary tiles, visualised |
| `QuasiCrystalShowCase.CrystalFromFaceTask` | Inflated IcosahedralFace (1–2 generations) |
| `QuasiCrystalShowCase.CrystalFromTileTask` | Inflated quasi-tiles from single or preset lists |
| `QuasiCrystalShowCase.WireframeFromCrystalTask` | Voxelized crystal wireframe → `Voxels voxCrystalWireframe` |

---

## Engineering Applications

From LEAP 71 published work:
- **Multi-layered Penrose patterns on hypersonic airframe panels**: resilience to multi-frequency
  vibrational-structural coupling; no distinct resonance frequencies
- **Vibration-sensitive aerospace components**: any structure that must not resonate at a specific
  frequency is a candidate for aperiodic lattice patterning
- **Meta-material research**: theoretical basis for non-repeating micro-architectures

**Reference:** https://leap71.com/2023/03/24/penrose-tiles-for-hypersonics/

---

## Mandatory Output Fields

Every Quasicrystal Metamaterials Specialist output MUST include:
1. `findings` — tile type used, inflation generations, face count, voxel size, export paths
2. `assumptions` — NEVER null; minimum three (generation count limit, preview mode, voxel size choice)
3. `what_would_falsify` — face count explosion / voxel timeout / viewer unresponsive
4. `provenance` — QuasiCrystals library version + PicoGK version + initial tile configuration hash
5. `confidence` — float 0.0–1.0
6. `quasicrystal_summary` — tile type, inflation generations, final face count, voxelization status

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Tile type: [QuasiTile_01–04 | IcosahedralFace | PenrosePattern]"
  - "Inflation generations: [N] (face count ≈ 120^N = [X])"
  - "Preview mode: EPreviewFace.[CONNECTOR|AXIS|NONE]"
  - "Voxel size: [X] mm"
  - "Voxelization: [complete | pending | failed]"
assumptions:
  - "Inflation generations ≤ 3 for parts < 200 mm — face count limit enforced"
  - "Preview mode NONE for > 1 inflation generation — performance constraint"
  - "Voxel size 0.4 mm used per LEAP71 recommended starting point"
what_would_falsify: >
  Face count exceeds available memory (viewer unresponsive or OOM crash);
  or voxelization produces disconnected voxels;
  or inflation more than 3 generations is specified without explicit performance budget.
provenance: "QuasiCrystals [version] / PicoGK [version] — initial tile SHA256: [hash]"
confidence: 0.75
quasicrystal_summary:
  tile_type: "QuasiTile_04"
  inflation_generations: 1
  estimated_face_count: 120
  preview_mode: "NONE"
  voxelization_complete: false
  status: "unverified"
```

---

## Escalation Flags

Raise **[QUASICRYSTAL GENERATION LIMIT]** when:
- Inflation generations requested > 3 — face count will exceed practical limits
- `EPreviewFace.CONNECTOR` selected for > 1 generation — viewer will be unresponsive
- Engineering application not cited — do not generate quasi-crystals "for aesthetics"

---

## Known Failure Patterns

Pre-seeded known failure modes:
- **Generation count explosion**: requesting 4+ inflation generations — 120^4 ≈ 207 million faces
- **CONNECTOR preview on large crystal**: viewer hangs; use AXIS or NONE for > 1 generation
- **Voxel size too coarse**: quasi-crystal wireframe beams may be < 1 voxel at 1 mm resolution; use ≤ 0.4 mm
- **No engineering rationale**: generating quasi-crystals without specific aperiodic-resonance application — not justified

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | 2D Penrose patterns + elementary tile visualisation |
| 2 | Apprentice | 0.40–0.59 | CrystalFromFaceTask + CrystalFromTileTask + voxelization |
| 3 | Journeyman | 0.60–0.74 | Engineering application targeting + multi-layer Penrose panels |
| 4 | Expert | 0.75–0.89 | Custom inflation rules, resonance analysis coupling |
| 5 | Master | 0.90–1.00 | Novel aperiodic meta-materials for specific frequency spectra |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## References

- QuasiCrystals library: https://github.com/leap71/LEAP71_QuasiCrystals
- Penrose tiling: https://en.wikipedia.org/wiki/Penrose_tiling
- Substitution rules for icosahedral quasicrystals (Madison): https://www.semanticscholar.org/paper/Substitution-rules-for-icosahedral-quasicrystals-Madison/5ffbb7614e3311fe17814d62902c1e643bcbe52e
- The Second Kind of Impossible — Paul J. Steinhardt (book)
- LEAP 71 hypersonics application: https://leap71.com/2023/03/24/penrose-tiles-for-hypersonics/
