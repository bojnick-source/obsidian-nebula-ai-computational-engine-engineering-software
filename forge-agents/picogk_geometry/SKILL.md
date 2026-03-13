# PicoGK Geometry — SKILL Definition

**Agent ID:** `picogk_geometry`
**Domain:** PicoGK Geometry — Voxel-Based Geometry, Lattice Infill, Implicit Patterns, OpenVDB Export
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/PicoGK | https://github.com/leap71/LEAP71_ShapeKernel

---

## Capability Definition

PicoGK (pronounced "Pico-Gee-Kay") is an open-source, voxel-based geometry kernel developed by LEAP 71.
It is the foundation of the LEAP 71 software stack. All geometry is represented as voxelfields — 3D grids
of black/white matter presence. This agent generates, combines, and exports PicoGK geometry using the
C# library, operating on the three core geometry data types: `Voxels`, `Lattice`, and `IImplicit`.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Voxelfield construction via Lattice | Active (MVP) | AddSphere / AddBeam → new Voxels(oLattice) |
| Boolean operations on Voxels | Active (MVP) | Sh.voxAdd, Sh.voxSubtract, Sh.voxIntersect |
| Implicit SDF rendering | Active (MVP) | IImplicit → Voxels via BBox3 or voxBounding |
| TPMS infill patterns | Active (Level 2) | Gyroid, Lidinoid, Schwarz Primitive, Schwarz Diamond |
| Lattice infill via LatticeLibrary | Active (Level 2) | ICellArray + ILatticeType + IBeamThickness |
| Offset and smoothing operations | Active (Level 2) | voxOffset, voxSmoothen, voxOverOffset |
| OpenVDB multi-field export | Active (Level 2) | geometry + physics fields in single .vdb (PicoGK v1.5+) |
| STL/OBJ mesh export | Active (Level 2) | Mesh.mshFromVoxels() → .stl / .obj |
| Custom SDF class creation | Planned (V1) | Implement IImplicit.fSignedDistance() |
| Multi-physics field coupling | Planned (V2) | VectorField + ScalarField alongside geometry |

### Tools Allowed

```yaml
tools_allowed:
  - bash            # execute PicoGK C# scripts via dotnet run
  - authorized_vault_write  # agent: Librarian
```

---

## PicoGK Entry Point

Every PicoGK program starts from `Program.cs`:

```csharp
using Leap71.ShapeKernel;
using PicoGK;

try
{
    PicoGK.Library.Go(
        0.5f,               // voxel size in mm
        MyClass.Task);      // delegate Task function
}
catch (Exception e)
{
    Console.WriteLine("Failed to run Task.");
    Console.WriteLine(e.ToString());
}
```

`PicoGK.Library.Go(float fVoxelSizeMM, Action taskDelegate)` — initialises the voxel engine
and executes the Task function. All geometry construction happens inside the Task function.

---

## Nomenclature Convention (ShapeKernel Standard)

Variable name prefixes used throughout all LEAP 71 C# code:

| Prefix | Type | Example |
|---|---|---|
| `f` | float | `float fValue` |
| `d` | double | `double dVolume` |
| `i` | int | `int iCounter` |
| `n` | uint | `uint nSamples` |
| `vec` | Vector3 | `Vector3 vecPt` |
| `a` | List / array | `List<Vector3> aPoints` |
| `s` | struct | `SProfile sProfile` |
| `x` | interface | `ISpline xSpline` |
| `o` | all other objects | `InjectorElement oSwirler` |
| `m_` | member variable | `float m_fMass` |
| `vox` | returns Voxels | `Voxels voxMotor` |
| `lat` | Lattice context | `Lattice latPipes` |
| `sdf` | IImplicit context | `IImplicit sdfSphere` |

---

## Core Geometry Data Types

### Voxels

Voxels describe a digital material distribution within a regular 3D grid. Think of it as a stack
of black/white images: white = matter, black = void. Voxelfields are created by rendering other
geometry types (Lattice, IImplicit, STL input) into them.

**Key Voxel operations (via the `Sh` static helper class):**

```csharp
// Boolean add (union)
Voxels voxResult = Sh.voxAdd(voxA, voxB);

// Boolean subtract
Voxels voxResult = Sh.voxSubtract(voxShell, voxFluidVoid);

// Boolean intersect
Voxels voxResult = Sh.voxIntersect(voxLattice, voxBounding);

// Offset (grow = positive, shrink = negative)
Voxels voxResult = Sh.voxOffset(voxSource, fOffsetMM);

// Smoothen corner details
Sh.voxSmoothen(ref voxSource, fStrength);

// Over-offset: close small loops, transition beam lattice to closed-cell tissue
// fInitialOffset > 0 removes sharp details; fFinalOffset shrinks back
Voxels voxResult = Sh.voxOverOffset(voxLattice, fInitialOffset, fFinalOffset);

// Intersect voxels with implicit SDF infill pattern
Voxels voxResult = Sh.voxIntersectImplicit(voxBounding, sdfPattern);
```

### Lattice

Lattice is the most basic way to build new shapes. Add nodes (spheres) and beams (conical
cylinders), then render to voxels. Node-only lattices voxelise very efficiently.

```csharp
Lattice oLattice = new Lattice();

// Add a node (sphere)
Vector3 vecPt0  = new Vector3(1, 5, 10);
float fRadius0  = 10;
oLattice.AddSphere(vecPt0, fRadius0);

// Add a flat-capped beam (two endpoints + two radii)
Vector3 vecPt1  = new Vector3(5, 3, 0);
float fRadius1  = 3;
Vector3 vecPt2  = new Vector3(-3, 0, 7);
float fRadius2  = 5;
bool bRounded   = false;
oLattice.AddBeam(vecPt1, fRadius1, vecPt2, fRadius2, bRounded);

// Add a rounded beam (hemispherical end-caps)
bRounded = true;
oLattice.AddBeam(vecPt1, fRadius1, vecPt2, fRadius2, bRounded);

// Render lattice into a voxelfield
Voxels oVoxels = new Voxels(oLattice);
```

### IImplicit (Signed-Distance Function)

Implicits describe a shape via a signed-distance function (SDF). `fSignedDistance()` returns
the signed distance from the surface: negative = inside, positive = outside.

**Built-in TPMS presets (from LatticeLibrary ImplicitLibrary):**

```csharp
IImplicit sdfGyroid           = new ImplicitGyroid(15, 3);           // (unitSizeMM, wallThicknessMM)
IImplicit sdfLidinoid         = new ImplicitLidinoid(15, 3);
IImplicit sdfSchwarzPrimitive = new ImplicitSchwarzPrimitive(15, 3);
IImplicit sdfSchwarzDiamond   = new ImplicitSchwarzDiamond(15, 3);

// Radial gyroid aligned to cylindrical coordinates
IImplicit sdfRadialGyroid = new ImplicitRadialGyroid(
    fHeightUnit, fRadiusUnit, nUnitsPerCircumference, fWallThickness);

// Deformed TPMS (biomimetic / randomised)
IImplicit sdfRandom = new ImplicitRandomizedSchwarzPrimitive(fUnitSize, fWallThickness, oDeformField);
```

**Rendering an implicit into voxels:**

```csharp
// Option 1: supply explicit bounding box
BBox3 oBBox = new BBox3(
    1.5f * new Vector3(-fRadius, -fRadius, -fRadius),
    1.5f * new Vector3( fRadius,  fRadius,  fRadius));
Voxels voxSphere = new Voxels(sdfSphere, oBBox);

// Option 2: intersect bounding voxelfield with implicit infill
Voxels voxGyroidSphere = Sh.voxIntersectImplicit(voxSphere, sdfGyroid);
```

**Custom SDF:**

```csharp
public class ImplicitSphere : IImplicit
{
    protected Vector3 m_vecCentre;
    protected float   m_fRadius;

    public ImplicitSphere(Vector3 vecCentre, float fRadius)
    {
        m_vecCentre = vecCentre;
        m_fRadius   = fRadius;
    }

    public float fSignedDistance(in Vector3 vecPt)
    {
        return (vecPt - m_vecCentre).Length() - m_fRadius;
    }
}
```

---

## LocalFrame — Placement in Space

All BaseShapes are constructed relative to a `LocalFrame` (a coordinate system with a position
and three orthogonal axes). This decouples placement from internal construction logic.

```csharp
// Identical to absolute coordinate system (origin, Z=up, X=right)
LocalFrame oFrame = new LocalFrame();

// Translated position only
LocalFrame oFrame = new LocalFrame(new Vector3(2, 5, -3));

// Translated + custom local-Z axis direction
LocalFrame oFrame = new LocalFrame(new Vector3(2, 5, -3), new Vector3(0, 0, 1));
LocalFrame oFrame = new LocalFrame(new Vector3(2, 5, -3), new Vector3(1, 0, 0));
LocalFrame oFrame = new LocalFrame(new Vector3(2, 5, -3), new Vector3(1, 5, -2));

// Translated + custom local-Z + custom local-X (fully specified frame)
LocalFrame oFrame = new LocalFrame(
    new Vector3(2, 5, -3),
    new Vector3(0, 0, 1),    // local Z
    new Vector3(1, 0, 0));   // local X
```

---

## Voxel Size Resolution Guide

| Part size / feature | Voxel size (mm) | Notes |
|---|---|---|
| Large shell > 200 mm, walls > 3 mm | 0.5 | Fast iteration cycles |
| Medium part 50–200 mm, walls 1.5–3 mm | 0.3 | Practical sweet spot |
| Fine feature < 50 mm or walls < 1.5 mm | 0.15 | Detail work |
| Lattice / biomorphic infill | 0.2 | Beam resolution |
| Final export for manufacturing | 0.1 | Maximum quality |
| **Rule** | — | Never coarser than 1/5 minimum wall thickness |
| **Default when uncertain** | 0.3 | Safe starting point |

HelixHeatX reference: internal cooling fins = 0.4 mm walls → voxels ≤ 0.4 mm for fins;
outer shell = 0.9 mm+ → 0.5 mm voxels sufficient during shell development.

Development strategy: **separate coarse and fine regions in code** so shell and fine features
can be tested independently at different resolutions. Iterate at 0.5–1 mm; finalise at 0.1–0.3 mm.

---

## STL and OpenVDB Export

```csharp
// Export to STL mesh (for FEA meshing and manufacturing)
Mesh oMesh = Mesh.mshFromVoxels(oVoxels);
oMesh.SaveToStlFile(Path.Combine(Library.strLogFolder, "output.stl"));

// Export to OpenVDB — single file holds geometry + physics fields (PicoGK v1.5+)
oVoxels.SaveToOpenVdbFile(Path.Combine(Library.strLogFolder, "output.vdb"));
```

**Multi-field VDB workflow (geometry + simulation physics in one file):**

```
voxFluidDomain   — Voxels field for flowable region
voxSolidDomain   — Voxels field for structural boundaries
vecVelocityField — VectorField with inlet velocity initial conditions
sclDensityField  — ScalarField (e.g. water = 1000 kg/m³)
sclViscosityField— ScalarField (e.g. water = 0.00000897 m²/s kinematic)
```

Boundary conditions are extracted directly from the geometry's surface normals via
`SurfaceNormalFieldExtractor` — identifies inlet/outlet patches without manual re-entry.
**The CEM that generated the geometry already knows the physics parameters — never re-engineer them.**

---

## CEM Inverse Design Pattern (from HelixHeatX)

Computational Engineering Models (CEMs) in PicoGK follow **inverse design**: fluid void volumes
are designed first; the housing/shell is derived from them.

```csharp
// 1. Design fluid void volumes first (inverse design principle)
Voxels voxInnerVolume = /* union of: helical void + fins + inlet + outlet transitions */;

// 2. Build outer structural shell independently
Voxels voxOuterVolume = /* outer ribs + flange + IO threads + support webs */;

// 3. Derive final part — subtract voids from shell
Voxels voxResult = Sh.voxSubtract(voxOuterVolume, voxInnerVolume);
```

HelixHeatX partial class structure (one function per file):
- `HelixHeatX()` — boundary conditions: IO positions, inner/outer bounding boxes
- `voxGetTurningFins()` — fins along helical corner sections (orange)
- `voxGetStraightFins()` — fins along straight sections with twist for mixing (turquoise)
- `GetHelicalVoid()` — two helical disk voids (hot/cold fluid)
- `fGetInnerRadius(float fPhi, float fLengthRatio)` — inner radius distribution function
- `fGetOuterRadius(float fPhi, float fLengthRatio)` — outer radius (supershape formula)
- `GetInlet()`, `GetOutlet()` — transition volumes at each void terminus
- `GetFlange()`, `AddCentrePiece()` — exterior structural features
- `voxGetIOThreads()`, `voxGetIOCuts()` — inlet/outlet threaded connections
- `voxGetPrintWeb()`, `voxGetIOSupports()` — build support features
- `voxGetOuterStructure()` — outer structural ribs
- `voxConstruct()` — top-level assembly: calls all sub-components, combines, subtracts voids

---

## Mandatory Output Fields

Every PicoGK Geometry output MUST include:
1. `findings` — bounding box mm, mass estimate kg, voxel count, export file paths
2. `assumptions` — NEVER null; minimum three (voxel size rationale, material density, wall thickness)
3. `what_would_falsify` — disconnected voxels / mass over budget / bbox deviation > 2 mm
4. `provenance` — PicoGK version + voxel size mm + input hash
5. `confidence` — float 0.0–1.0
6. `geometry_summary` — bounding box, mass, validation check results

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Bounding box: X.X × Y.Y × Z.Z mm"
  - "Estimated mass: X.XX kg at X.X g/cm³"
  - "Voxel size used: X.X mm"
  - "Export: [path].stl + [path].vdb"
assumptions:
  - "Voxel size chosen per resolution guide — never coarser than 1/5 min wall"
  - "Material density: nominal grade — verify for actual alloy/polymer"
  - "Boolean subtract is sequentially ordered — order matters for overlapping voids"
what_would_falsify: >
  Disconnected voxels found after Boolean subtract (is_connected() returns false);
  or estimated mass exceeds params.mass_budget_kg;
  or bounding box deviates > 2 mm from envelope spec.
provenance: "PicoGK [version] — voxel_size: X.X mm — input SHA256: [hash]"
confidence: 0.80
geometry_summary:
  bounding_box_mm: [0.0, 0.0, 0.0]
  estimated_mass_kg: 0.0
  voxel_size_mm: 0.3
  validation_checks_passed: 0
  status: "unverified"
```

---

## Escalation Flags

Raise **[PICOGK VALIDATION REQUIRED]** when:
- Boolean subtract produces empty voxelfield — enlarge cutter by 2 mm and re-run
- `is_connected()` returns false — do NOT proceed to FEA or manufacturing export
- Mass exceeds `params.mass_budget_kg` — flag to user; never silently thin walls
- VDB file > 500 MB — coarsen for FEA; fine resolution only for manufacturing export
- Noyron/lattice infill requested without topology-optimization handoff prescribing it

---

## Error Recovery Patterns

| Error | Recovery |
|---|---|
| `dotnet` / PicoGK import failure | `dotnet add package PicoGK --prerelease`; verify .NET 7+ |
| Boolean subtract returns empty | Enlarge cutter geometry by 2 mm in each direction, re-run |
| Disconnected voxels | Separate components, investigate cause — do not silently fix |
| Mass over budget | Flag to user with options; never silently thin walls |
| Validation failure | Fix params; never proceed to FEA with failed validation |
| VDB > 500 MB | Coarsen to 0.3 mm for FEA; keep 0.1 mm only for manufacturing |
| Noyron unavailable | Use solid geometry, note in vault — do not add lattice speculatively |

---

## Known Failure Patterns

Pre-seeded known failure modes:
- **Wrong voxel size**: choosing coarser than 1/5 min wall — thin features disappear silently
- **Boolean order error**: subtracting void before outer shell exists — empty result, no error
- **Disconnected voxel propagation**: passing disconnected geometry to FEA produces silently wrong results
- **Mass not checked**: geometry validated geometrically but mass budget never verified
- **Noyron added speculatively**: lattice infill added without topology-optimization handoff prescribing it

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Lattice + IImplicit rendering, Boolean ops, STL export |
| 2 | Apprentice | 0.40–0.59 | TPMS infill, LatticeLibrary workflow, OpenVDB export |
| 3 | Journeyman | 0.60–0.74 | Custom IImplicit SDFs, multi-field VDB, CEM structuring |
| 4 | Expert | 0.75–0.89 | Full CEM with inverse design, simulation-ready VDB handoff |
| 5 | Master | 0.90–1.00 | Novel CEMs, multi-physics geometry coupling |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## References

- PicoGK repository: https://github.com/leap71/PicoGK
- ShapeKernel library: https://github.com/leap71/LEAP71_ShapeKernel
- LatticeLibrary + ImplicitLibrary: https://github.com/leap71/LEAP71_LatticeLibrary
- HelixHeatX CEM example: https://github.com/leap71/LEAP71_HelixHeatX
- PicoGK simulation example: https://github.com/leap71/PicoGK_SimulationExample
- SDF primitive reference: https://iquilezles.org/articles/distfunctions/
