# Lattice Infill Specialist — SKILL Definition

**Agent ID:** `lattice_infill_specialist`
**Domain:** LEAP71 LatticeLibrary — ICellArray, ILatticeType, IBeamThickness, TPMS Implicits
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/LEAP71_LatticeLibrary

---

## Capability Definition

The LEAP 71 LatticeLibrary provides a flexible, open framework for procedural lattice design
in PicoGK. It is structured around three independent interfaces — cell array, lattice type, and
beam thickness — that can be freely combined to produce any beam-based or implicit infill structure.
This agent executes lattice prescriptions from `topology_optimization` handoffs. It does NOT
add lattice speculatively.

**Dependency:** Lattice infill is ONLY initiated after `topology_optimization` has produced a
handoff block prescribing: `lattice_type`, `cell_size_mm`, `beam_thickness_mm`, and
`target_volume_fraction`.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| ICellArray: regular and conformal cell arrays | Active (MVP) | RegularCellArray, ConformalCellArray |
| ILatticeType: BodyCentered, Octahedron, RandomSpline | Active (MVP) | From standard library |
| IBeamThickness: Constant, CellBased, GlobalFunc, Boundary | Active (MVP) | All four variants |
| voxGetFinalLatticeGeometry() workflow | Active (MVP) | Full beam→voxels pipeline |
| Post-processing: voxIntersect + voxOverOffset | Active (Level 2) | Bounding intersect + smoothing |
| TPMS implicit infill: Gyroid, Lidinoid, Schwarz P/D | Active (Level 2) | ImplicitLibrary presets |
| Radial TPMS: ImplicitRadialGyroid | Active (Level 2) | Cylindrical coordinate TPMS |
| Modular implicit workflow | Planned (V1) | IRawTPMSPattern + ISplittingLogic + ICoordinateTrafo |
| Custom ILatticeType implementation | Planned (V1) | RandomSplineLattice extension |
| Topology-opt-driven gradient lattice | Planned (V2) | Volume fraction gradient from handoff |

### Tools Allowed

```yaml
tools_allowed:
  - bash    # dotnet run PicoGK C# scripts
```

---

## Workflow Overview

```
topology_optimization handoff
    → specifies: lattice_type, cell_size_mm, beam_thickness_mm, target_volume_fraction
    → lattice_infill_specialist executes:
        1. Create bounding voxels (BaseSphere, BaseBox, or from params)
        2. Choose ICellArray (Regular or Conformal)
        3. Choose ILatticeType (BodyCentered / Octahedron / RandomSpline)
        4. Choose IBeamThickness (Constant / CellBased / GlobalFunc / Boundary)
        5. Call voxGetFinalLatticeGeometry(xCellArray, xLatticeType, xBeamThickness, nSubSample)
        6. Post-process: voxIntersect with bounding voxels + voxOverOffset/voxSmoothen
        7. Verify volume fraction vs prescription
        8. Hand off to picogk_geometry or simulation_fea
```

---

## Three Core Interfaces

### Interface 1 — ICellArray

Provides a list of every unit cell in the space. Not one unit cell repeated — a list of all cells.
This allows non-identical cells (randomised, wedged, conformal) for maximum flexibility.

**Implemented classes:**

```csharp
// Single cell for testing; optional noise on corner vertices
RegularUnitCell(fCellSizeX, fCellSizeY, fCellSizeZ, fNoiseLevel: 0f)

// Regular repeating grid; fills bounding box automatically
RegularCellArray(voxBounding, nCellsX, nCellsY, nCellsZ)

// Noised regular grid
NoisedRegularCellArray(voxBounding, nCellsX, nCellsY, nCellsZ, fNoiseLevel)

// Surface-conformal grid — supported base shapes: BaseBox, BaseLens, BasePipeSegment
ConformalCellArray(oBaseShape, nCellsU, nCellsV, nCellsW)
```

**Bounding voxels (always required for RegularCellArray and ConformalCellArray):**

```csharp
BaseSphere oSphere     = new BaseSphere(new LocalFrame(), 50);
Voxels voxBounding     = oSphere.voxConstruct();
```

### Interface 2 — ILatticeType

Holds the logic of how to connect cell corner points into beams. Standard types work on
cuboid cells with 8 corners; custom types can handle variable-corner cells.

**Implemented classes:**

```csharp
BodyCenteredLattice()       // connects each corner to the cell centre — standard BCC
OctahedronLattice()         // octahedral connection pattern — standard literature type
RandomSplineLattice()       // randomly selects corners, connects with B-spline curves
                            // handles any number of corners; adds randomness
```

Custom implementation pattern:

```csharp
public class CustomLattice : ILattice
{
    public void AddCell(ref Lattice oLattice, IUnitCell xCell,
                        IBeamThickness xBeamThickness, uint nSubSample)
    {
        // Access cell corners: xCell.aGetCornerPoints()
        // Draw beams: oLattice.AddBeam(vecPt1, fR1, vecPt2, fR2, bRounded)
    }
}
```

### Interface 3 — IBeamThickness

Returns beam radius for any queried point in space. Called per beam, per subsampling point.

**Implemented classes:**

```csharp
// Always returns a constant radius — most basic
ConstantBeamThickness(fRadius)

// Radius varies across each cell (local gradient per cell)
// Beams thinner at cell centre, thicker at corners (or vice versa)
CellBasedBeamThickness(fMinRadius, fMaxRadius)

// Radius varies by absolute XYZ coordinate (global gradient)
GlobalFuncBeamThickness(/* lambda or subclass */)

// Radius varies by distance to bounding voxel surface
// Thicker at surface → smooth lattice-to-wall transition (recommended for DfAM)
BoundaryBeamThickness(voxBounding, fSurfaceRadius, fInteriorRadius)
```

`BoundaryBeamThickness` is the recommended choice for parts that need smooth transitions
at the boundary between lattice infill and solid outer shell.

---

## Full Workflow Code Example

```csharp
// 1. Bounding shape
BaseSphere oSphere     = new BaseSphere(new LocalFrame(), 50);
Voxels voxBounding     = oSphere.voxConstruct();

// 2. Interfaces
ICellArray xCellArray         = new NoisedRegularCellArray(voxBounding, 20, 20, 20);
ILattice xLatticeType         = new CustomLattice();
IBeamThickness xBeamThickness = new CellBasedBeamThickness(1f, 4f);
xBeamThickness.SetBoundingVoxels(voxBounding);

// 3. Generate lattice voxels
// nSubSample = 2 default: each beam queried at 2 points for beam thickness
// nSubSample = 5+: use for intricate non-linear thickness distributions
uint nSubSample   = 5;
Voxels voxLattice = voxGetFinalLatticeGeometry(
                        xCellArray,
                        xLatticeType,
                        xBeamThickness,
                        nSubSample);

// 4. Post-processing
// Over-offset: initial positive offset closes sharp beam corners;
// final zero offset keeps size (or slightly negative to restore size)
voxLattice = voxLattice.voxOverOffset(3f, 0f);

// Intersect with bounding voxels to trim lattice to shape
voxLattice = voxLattice.voxBoolIntersect(voxBounding);
```

**Internal implementation of voxGetFinalLatticeGeometry:**

```csharp
public Voxels voxGetFinalLatticeGeometry(
    ICellArray xCellArray,
    ILattice xLatticeType,
    IBeamThickness xBeamThickness,
    uint nSubSample = 2)
{
    Lattice oLattice = new Lattice();
    foreach (IUnitCell xCell in xCellArray.aGetUnitCells())
    {
        xBeamThickness.UpdateCell(xCell);
        xLatticeType.AddCell(ref oLattice, xCell, xBeamThickness, nSubSample);
    }
    Voxels voxLattice = new Voxels(oLattice);
    return voxLattice;
}
```

---

## TPMS Implicit Infill (ImplicitLibrary)

Alternative to beam lattice: TPMS structures via SDF. Rendered by sampling every voxel in
bounding space — computationally heavier than lattice beams for equivalent resolution.

```csharp
// Regular TPMS presets (Cartesian coordinates)
IImplicit sdfGyroid           = new ImplicitGyroid(fUnitSize, fWallThickness);
IImplicit sdfLidinoid         = new ImplicitLidinoid(fUnitSize, fWallThickness);
IImplicit sdfSchwarzPrimitive = new ImplicitSchwarzPrimitive(fUnitSize, fWallThickness);
IImplicit sdfSchwarzDiamond   = new ImplicitSchwarzDiamond(fUnitSize, fWallThickness);

// Radial TPMS (cylindrical coordinates — for pipes, heat exchangers)
IImplicit sdfRadialGyroid = new ImplicitRadialGyroid(
    fHeightUnit, fRadiusUnit, nUnitsPerCircumference, fWallThickness);

// Randomized TPMS (biomimetic variation)
IImplicit sdfRandom = new ImplicitRandomizedSchwarzPrimitive(
    fUnitSize, fWallThickness, oDeformField);

// Apply TPMS infill to bounding voxels
Voxels voxFilled = voxBounding.voxIntersectImplicit(sdfGyroid);
```

**Logic split — extracting separate regions from a TPMS field:**

```csharp
// Positive void (one fluid channel of two-fluid heat exchanger)
float fFinalSD = (float)(Math.Max(0, fRawSD) - 0.5f * fWallThickness);
return -fFinalSD;

// Negative void (second fluid channel)
float fFinalSD = (float)(Math.Max(0, -fRawSD) - 0.5f * fWallThickness);
return -fFinalSD;
```

---

## Conformal Lattice on Specific BaseShapes

ConformalCellArray is available for three ShapeKernel BaseShape types:

```csharp
// Conformal on BaseBox (rectangular conformal grid)
ConformalCellArray oCA = new ConformalCellArray(
    new BaseBox(new LocalFrame(), 80, 40, 40), 8, 4, 4);

// Conformal on BaseLens (lens-shaped conformal grid)
ConformalCellArray oCA = new ConformalCellArray(
    new BaseLens(new LocalFrame(), fRadius, fThickness), 6, 6, 3);

// Conformal on BasePipeSegment (pipe wall conformal grid)
ConformalCellArray oCA = new ConformalCellArray(
    new BasePipeSegment(new LocalFrame(), fInnerR, fOuterR, fLength), 8, 4, 2);
```

---

## Mandatory Output Fields

Every Lattice Infill Specialist output MUST include:
1. `findings` — cell array type, lattice type, beam thickness distribution, final volume fraction
2. `assumptions` — NEVER null; minimum three (topo-opt handoff values, nSubSample choice, post-processing rationale)
3. `what_would_falsify` — volume fraction deviation > 5% from prescription / disconnected lattice
4. `provenance` — LatticeLibrary version + PicoGK version + topo-opt handoff hash
5. `confidence` — float 0.0–1.0
6. `lattice_summary` — cell count, beam count, volume fraction, post-processing steps applied

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Cell array: [type] — [N] cells total"
  - "Lattice type: [BodyCentered|Octahedron|RandomSpline|Custom]"
  - "Beam thickness: [type] — range [fMin]–[fMax] mm"
  - "nSubSample: [N] (justified by: [linear/non-linear thickness distribution])"
  - "Final volume fraction: X.XX (prescribed: X.XX, deviation: ±X.X%)"
assumptions:
  - "Topo-opt handoff prescribes lattice_type=[type], cell_size=[N]mm, beam_thickness=[N]mm"
  - "nSubSample=[N] chosen to resolve beam thickness gradient — minimum 5 for non-linear"
  - "BoundaryBeamThickness used to ensure smooth lattice-to-wall transition"
what_would_falsify: >
  Volume fraction deviates > 5% from topology-optimization prescription;
  or disconnected lattice voxels found after intersection with bounding voxelfield;
  or beam thickness < voxel_size_mm (beams not resolvable at stated resolution).
provenance: "LatticeLibrary [version] / PicoGK [version] — topo-opt handoff SHA256: [hash]"
confidence: 0.80
lattice_summary:
  cell_array_type: "RegularCellArray"
  lattice_type: "BodyCenteredLattice"
  beam_thickness_type: "BoundaryBeamThickness"
  n_sub_sample: 5
  volume_fraction: 0.0
  post_processing: []
  status: "unverified"
```

---

## Escalation Flags

Raise **[LATTICE INFILL HARD FAIL]** when:
- No topology-optimization handoff found — lattice cannot be added speculatively
- Beam thickness < voxel_size_mm — beams unresolvable, manufacturing impossible
- Volume fraction deviation > 5% from prescription — re-run with adjusted parameters
- Disconnected lattice voxels after intersection — investigate cause, do not ignore

---

## Known Failure Patterns

Pre-seeded known failure modes:
- **Speculative lattice**: adding infill without topo-opt handoff — structural benefit unproven
- **nSubSample = 2 for non-linear thickness**: gradient unresolved — use ≥ 5 for CellBased/GlobalFunc
- **No bounding intersection**: lattice extends beyond bounding object — invalid geometry
- **No post-processing smoothing**: sharp beam joints cause stress concentrations — always apply voxOverOffset
- **ConformalCellArray on unsupported BaseShape**: only BaseBox, BaseLens, BasePipeSegment supported

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | RegularCellArray + BodyCenteredLattice + ConstantBeamThickness |
| 2 | Apprentice | 0.40–0.59 | ConformalCellArray, BoundaryBeamThickness, TPMS presets |
| 3 | Journeyman | 0.60–0.74 | Custom ILatticeType, modular TPMS workflow |
| 4 | Expert | 0.75–0.89 | Gradient lattice from topo-opt prescription, volume fraction verification |
| 5 | Master | 0.90–1.00 | Novel lattice types, multi-physics infill coupling |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## References

- LatticeLibrary (beam lattice): https://github.com/leap71/LEAP71_LatticeLibrary
- ImplicitLibrary (TPMS): https://github.com/leap71/LEAP71_LatticeLibrary/blob/main/README_ImplicitLibrary.md
- ShapeKernel (BaseShapes): https://github.com/leap71/LEAP71_ShapeKernel
- PicoGK (voxel kernel): https://github.com/leap71/PicoGK
