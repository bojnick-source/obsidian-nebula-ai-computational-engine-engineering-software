---
applyTo: "mesh-morph-lhs/**,forge-agents/picogk_geometry/**,forge-agents/shape_kernel_*/**,forge-agents/lattice_infill_*/**,forge-agents/quasicrystal_metamaterials_*/**,forge-agents/rover_wheel_*/**,forge-agents/heat_transfer_*/**"
---

# FORGE — LEAP 71 PicoGK Integration Instructions

## Software Stack

LEAP 71 publishes an open-source computational engineering stack. All of it is C#.
This repo integrates it as knowledge in FORGE agents. The `mesh-morph-lhs/` project is the
C# runtime that actually runs PicoGK. Everything else is Python FORGE agents that know the API.

```
Layer 1: PicoGK          — voxel geometry kernel (Voxels, Lattice, IImplicit, Mesh)
Layer 2: ShapeKernel     — BaseShapes, LocalFrame, Modulations
Layer 3: Domain libs     — LatticeLibrary, ImplicitLibrary, HelixHeatX, QuasiCrystals, RoverWheel
Layer 4: FORGE agents    — domain knowledge encoded in SKILL.md files
```

---

## Golden Rules (Never Violate)

### 1. Voxel-First — No B-Rep

All LEAP 71 geometry is voxel-based. Never build B-rep and convert to voxels.
The pipeline is: Lattice/IImplicit/BaseShape → `Voxels` → Boolean ops → export.

```csharp
// CORRECT
Voxels voxResult = Sh.voxSubtract(voxOuterVolume, voxInnerVolume);

// WRONG
// Building solid faces and converting to voxels is not how PicoGK works
```

### 2. Inverse Design — Fluid Voids First

All heat exchanger and fluidic CEM designs use inverse design:

```csharp
// CORRECT: design voids first, derive walls last
Voxels voxInnerVolume = /* union of all fluid voids + fins + inlet + outlet */;
Voxels voxOuterVolume = /* structural shell, ribs, flanges */;
Voxels voxResult      = Sh.voxSubtract(voxOuterVolume, voxInnerVolume);

// WRONG: constructing walls directly without fluid volumes first
```

### 3. Mandatory LEAP71 Nomenclature

All LEAP 71 C# code uses strict prefixes. Generate only compliant code:

| Prefix | Type | Example |
|---|---|---|
| `f` | float | `float fRadius` |
| `d` | double | `double dVolume` |
| `n` | uint | `uint nSamples` |
| `vec` | Vector3 | `Vector3 vecPt` |
| `a` | List/array | `List<Vector3> aPoints` |
| `x` | interface | `ICellArray xCells` |
| `o` | other objects | `BaseSphere oSphere` |
| `m_` | member var | `float m_fMass` |
| `vox` | returns Voxels | `Voxels voxResult` |
| `sdf` | IImplicit context | `IImplicit sdfGyroid` |

**Never generate `float radius` — it must be `float fRadius`.**

### 4. No Speculative Lattice / TPMS

NEVER add lattice or TPMS infill without a `topology_optimization` handoff prescribing it:

```yaml
# Required before calling voxGetFinalLatticeGeometry():
lattice_infill_handoff:
  cell_size_mm: 5.0
  lattice_type: "BodyCenteredLattice"
  beam_thickness_mm: 1.5
  target_volume_fraction: 0.35
```

### 5. Boolean Op Naming

Use LEAP71 `Sh` static class naming — not generic alternatives:

```csharp
// CORRECT (LEAP71)
Sh.voxAdd(voxA, voxB)
Sh.voxSubtract(voxA, voxB)
Sh.voxIntersect(voxA, voxB)
Sh.voxOffset(voxSource, fOffsetMM)
Sh.voxSmoothen(ref voxSource, fStrength)
Sh.voxOverOffset(voxLattice, fInitial, fFinal)
Sh.voxIntersectImplicit(voxBounding, sdfPattern)

// WRONG (generic names not used in LEAP71)
voxBoolUnion()
voxBoolSubtract()
```

---

## PicoGK Entry Point

```csharp
PicoGK.Library.Go(
    0.5f,            // voxel size in mm — see resolution guide below
    MyClass.Task);   // delegate function containing all construction logic
```

---

## Voxel Size Resolution Guide

| Scenario | Voxel size (mm) |
|---|---|
| Large shell > 200 mm, walls > 3 mm | 0.5 |
| Medium part 50–200 mm, walls 1.5–3 mm | 0.3 |
| Fine features < 50 mm or walls < 1.5 mm | 0.15 |
| Lattice / biomorphic infill | 0.2 |
| Final manufacturing export | 0.1 |
| **Rule** | Never > 1/5 of minimum wall thickness |
| **Default** | 0.3 |

---

## BaseShape Usage

All BaseShapes are constructed relative to a `LocalFrame`. Always specify the LocalFrame explicitly.

```csharp
// Primitive BaseShapes — always first arg is LocalFrame
BaseSphere oSphere       = new BaseSphere(new LocalFrame(), fRadius);
BaseBox oBox             = new BaseBox(new LocalFrame(vecPos), fDX, fDY, fDZ);
BaseCylinder oCyl        = new BaseCylinder(new LocalFrame(vecPos, vecZ), fRadius, fLength);
BaseLens oLens           = new BaseLens(new LocalFrame(), fRadius, fThickness);
BasePipeSegment oPipe    = new BasePipeSegment(new LocalFrame(), fInnerR, fOuterR, fLength);

// Always call voxConstruct() to get the voxelfield
Voxels voxShape = oShape.voxConstruct();
```

---

## LatticeLibrary Usage

Three interfaces, one function call. Order matters: cell array → lattice type → beam thickness.

```csharp
// Step 1: bounding voxels
Voxels voxBounding = new BaseSphere(new LocalFrame(), 50).voxConstruct();

// Step 2: interfaces
ICellArray xCellArray         = new RegularCellArray(voxBounding, 10, 10, 10);
ILattice xLatticeType         = new BodyCenteredLattice();
IBeamThickness xBeamThickness = new BoundaryBeamThickness(voxBounding, 2f, 0.8f);

// Step 3: generate
uint nSubSample   = 5;  // ≥5 for non-constant beam thickness
Voxels voxLattice = voxGetFinalLatticeGeometry(xCellArray, xLatticeType, xBeamThickness, nSubSample);

// Step 4: post-process (always both steps)
voxLattice = Sh.voxOverOffset(voxLattice, 3f, 0f);
voxLattice = Sh.voxIntersect(voxLattice, voxBounding);
```

---

## TPMS Implicit Infill

```csharp
// TPMS presets (LatticeLibrary ImplicitLibrary)
IImplicit sdfGyroid           = new ImplicitGyroid(fUnitSize, fWallThickness);
IImplicit sdfLidinoid         = new ImplicitLidinoid(fUnitSize, fWallThickness);
IImplicit sdfSchwarzPrimitive = new ImplicitSchwarzPrimitive(fUnitSize, fWallThickness);
IImplicit sdfSchwarzDiamond   = new ImplicitSchwarzDiamond(fUnitSize, fWallThickness);

// Apply to bounding voxels
Voxels voxFilled = Sh.voxIntersectImplicit(voxBounding, sdfGyroid);
```

---

## QuasiCrystals — Generation Limit Enforcement

```
MAXIMUM inflation generations: ≤ 3 (face count ≈ 120^N grows exponentially)
PREVIEW MODE for > 1 generation: EPreviewFace.NONE (CONNECTOR mode hangs the viewer)
MINIMUM voxel size for wireframe: 0.4 mm
```

```csharp
// Elementary tiles
QuasiTile oTile               = new QuasiTile_04(new LocalFrame(), 50);
List<QuasiTile> aInitialTiles = QuasiCrystal.aGetFirstGenerationTiles();

// Preview modes
oTile.Preview(QuasiTile.EPreviewFace.NONE);      // final rendering
oTile.Preview(QuasiTile.EPreviewFace.AXIS);      // debugging medium-scale
oTile.Preview(QuasiTile.EPreviewFace.CONNECTOR); // debugging single tile only
```

---

## OpenVDB Multi-Field Export (PicoGK v1.5+)

```csharp
// Single .vdb file carries geometry + physics fields together
// Boundary conditions are derived from the geometry — never re-entered manually
oVoxels.SaveToOpenVdbFile(Path.Combine(Library.strLogFolder, "output.vdb"));
```

Multi-field contents:
- `voxFluidDomain` — flowable region
- `voxSolidDomain` — structural boundaries
- `vecVelocityField` — inlet velocity (from CEM parameters)
- `sclDensityField` — fluid density (from CEM parameters)
- `sclViscosityField` — kinematic viscosity (from CEM parameters)

---

## CEM Partial Class Pattern

All LEAP 71 engineering classes are `partial` — one or two functions per file.

```csharp
// HelixHeatX.cs — boundary conditions
public partial class HelixHeatX { /* constructor + member vars */ }

// HelixHeatX_Fins.cs — sub-component
public partial class HelixHeatX { public Voxels voxGetTurningFins() { ... } }

// HelixHeatX_Construct.cs — top-level assembly entry point
public partial class HelixHeatX { public Voxels voxConstruct() { ... } }
```

`voxConstruct()` must be **readable without understanding internal math**.

---

## Known Pitfalls (Do Not Repeat)

| Pitfall | Correct pattern |
|---|---|
| Naming variable `radius` | Must be `fRadius` |
| Subtracting void before shell is complete | Complete outer shell first, then subtract voids |
| `nSubSample=2` with `BoundaryBeamThickness` | Use `nSubSample ≥ 5` for non-constant thickness |
| Missing `voxIntersect` after lattice | Always intersect lattice with bounding voxels |
| Speculative `ImplicitGyroid` infill | Only when `topology_optimization` prescribes it |
| `EPreviewFace.CONNECTOR` on large crystal | Use `NONE` for > 1 inflation generation |
| Voxel size > min wall / 2 | Thin features silently disappear at export |
| Building walls directly | Use inverse design: derive walls by subtracting voids |
