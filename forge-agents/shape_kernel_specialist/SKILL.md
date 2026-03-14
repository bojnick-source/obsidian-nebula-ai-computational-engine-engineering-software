# Shape Kernel Specialist — SKILL Definition

**Agent ID:** `shape_kernel_specialist`
**Domain:** LEAP71 ShapeKernel — BaseShapes, CEM Composition, LocalFrame, Implicits
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/LEAP71_ShapeKernel

---

## Capability Definition

The LEAP 71 ShapeKernel library bridges low-level PicoGK voxel operations and the high-level
functions needed when creating sophisticated engineering objects. It simplifies generation of
geometric primitives called **BaseShapes** — the "atoms" of complex designs. A single heat
exchanger part consists of hundreds of BaseShapes combined by Boolean() and Offset() operations.

ShapeKernel is the third layer of the LEAP 71 software stack:
- Layer 1: PicoGK (voxel kernel — Voxels, Lattice, IImplicit, Mesh)
- Layer 2: ShapeKernel (BaseShapes, LocalFrame, Modulations, Transformations)
- Layer 3: Domain CEMs (HelixHeatX, RoverWheel, QuasiCrystals, application engineering)

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| BaseShape instantiation and placement | Active (MVP) | LocalFrame-based placement |
| Boolean composition of BaseShapes | Active (MVP) | Sh.voxAdd / voxSubtract / voxIntersect |
| LocalFrame construction and orientation | Active (MVP) | Position + Z-axis + X-axis |
| Lattice node/beam construction | Active (MVP) | Lattice.AddSphere / AddBeam |
| IImplicit SDF custom class creation | Active (Level 2) | fSignedDistance() implementation |
| TPMS infill pattern application | Active (Level 2) | Gyroid, Lidinoid, Schwarz P/D |
| Modulations and transformations | Planned (V1) | Shape deformation, supershape formula |
| CEM class structure (partial class pattern) | Active (Level 2) | One function per file |
| Multi-BaseShape assembly | Active (Level 2) | voxConstruct() top-level assembly |

### Tools Allowed

```yaml
tools_allowed:
  - bash    # dotnet run to execute PicoGK C# scripts
```

---

## Nomenclature (Mandatory — All LEAP71 C# Code)

All LEAP 71 C# code uses strict prefix-based nomenclature. Violating this is a known failure mode.

| Prefix | Type | Correct Example | Wrong |
|---|---|---|---|
| `f` | float | `float fRadius` | `float radius` |
| `d` | double | `double dVolume` | `double volume` |
| `i` | int | `int iCount` | `int count` |
| `n` | uint | `uint nSamples` | `uint samples` |
| `vec` | Vector3 | `Vector3 vecPt` | `Vector3 pt` |
| `a` | List / array | `List<Vector3> aPoints` | `List<Vector3> points` |
| `s` | struct | `SProfile sProfile` | `SProfile profile` |
| `x` | interface instance | `ICellArray xCells` | `ICellArray cells` |
| `o` | other objects | `BaseSphere oSphere` | `BaseSphere sphere` |
| `m_` | class member | `float m_fMass` | `float fMass` (in class body) |
| `vox` | function returning Voxels | `Voxels voxConstruct()` | `Voxels Construct()` |
| `lat` | Lattice in context | `Lattice latPipes` | `Lattice pipes` |
| `sdf` | IImplicit in context | `IImplicit sdfGyroid` | `IImplicit gyroid` |

---

## Ways to Create Geometry in ShapeKernel

ShapeKernel provides three geometry data types, all ultimately rendered to `Voxels`:

### 1. Voxels (final output of all geometry)

```
Inputs (STL, BaseShape.voxConstruct(), Lattice, IImplicit) → rendered to Voxels
Voxels → Boolean ops (Add/Subtract/Intersect) → combined Voxels
Voxels → Offset / Smoothen → refined Voxels
Voxels → Mesh.mshFromVoxels() → STL/OBJ export
Voxels → SaveToOpenVdbFile() → VDB export
```

### 2. Lattice (beam-based shapes)

```csharp
Lattice oLattice = new Lattice();
oLattice.AddSphere(vecPt0, fRadius0);                                     // sphere node
oLattice.AddBeam(vecPt1, fRadius1, vecPt2, fRadius2, bRounded: false);   // flat-capped beam
oLattice.AddBeam(vecPt1, fRadius1, vecPt2, fRadius2, bRounded: true);    // rounded beam
Voxels voxResult = new Voxels(oLattice);
```

### 3. IImplicit (signed-distance function shapes)

```csharp
// Presets
IImplicit sdfGyroid           = new ImplicitGyroid(15f, 3f);
IImplicit sdfLidinoid         = new ImplicitLidinoid(15f, 3f);
IImplicit sdfSchwarzPrimitive = new ImplicitSchwarzPrimitive(15f, 3f);
IImplicit sdfSchwarzDiamond   = new ImplicitSchwarzDiamond(15f, 3f);

// Custom SDF — implement the interface
public class MyImplicit : IImplicit
{
    public float fSignedDistance(in Vector3 vecPt)
    {
        // return signed distance: negative = inside, positive = outside
        return vecPt.Length() - 20f;  // sphere of radius 20
    }
}

// Render SDF to voxels
BBox3 oBBox = new BBox3(new Vector3(-30, -30, -30), new Vector3(30, 30, 30));
Voxels voxShape = new Voxels(new MyImplicit(), oBBox);

// Infill: intersect bounding voxels with SDF pattern
Voxels voxFilled = Sh.voxIntersectImplicit(voxBounding, sdfGyroid);
```

---

## LocalFrame — The Foundation of BaseShape Placement

Every BaseShape takes a `LocalFrame` as its first constructor argument. This places and orients
the shape in 3D space without changing its internal construction logic.

```csharp
// Identity frame (origin, Z=up, X=right)
LocalFrame oFrame = new LocalFrame();

// Translated
LocalFrame oFrame = new LocalFrame(new Vector3(0, 0, 50));

// Translated + rotated Z-axis
LocalFrame oFrame = new LocalFrame(new Vector3(0, 0, 50), new Vector3(0, 1, 0));

// Translated + Z + X axes (fully constrained orientation)
LocalFrame oFrame = new LocalFrame(
    new Vector3(0, 0, 50),
    new Vector3(0, 0, 1),   // local Z
    new Vector3(1, 0, 0));  // local X
```

---

## BaseShapes — Geometric Primitives

BaseShapes are the core of ShapeKernel. They generate voxelfields via `voxConstruct()`.
Each BaseShape is constructed relative to a `LocalFrame`.

All BaseShapes follow this pattern:

```csharp
// Instantiate
BaseSphere oSphere = new BaseSphere(new LocalFrame(), fRadius);

// Generate voxelfield
Voxels voxSphere = oSphere.voxConstruct();
```

**Confirmed BaseShape classes from ShapeKernel:**

| Class | Key Parameters | Use Case |
|---|---|---|
| `BaseSphere` | `LocalFrame, float fRadius` | Bounding objects, node caps |
| `BaseBox` | `LocalFrame, float fDX, float fDY, float fDZ` | Rectangular infill bounds |
| `BaseCylinder` | `LocalFrame, float fRadius, float fLength` | Shafts, flanges, pipes |
| `BaseLens` | `LocalFrame, float fRadius, float fThickness` | Lens-shaped bounding volumes |
| `BasePipeSegment` | `LocalFrame, float fInnerRadius, float fOuterRadius, float fLength` | Pipe walls, channels |

**HelixHeatX example — hundreds of BaseShapes combined:**

```csharp
// Simplified structural rib example
BaseCylinder oRib   = new BaseCylinder(new LocalFrame(vecRibPos), fRibRadius, fRibLength);
Voxels voxRib       = oRib.voxConstruct();
voxOuterVolume      = voxOuterVolume.voxBoolAdd(voxRib);

// Subtract fluid voids at the end (inverse design)
Voxels voxResult    = voxOuterVolume.voxBoolSubtract(voxInnerVolume);
```

---

## Boolean Operations (instance methods on Voxels — v1.7+ API)

```csharp
// Union — three equivalent forms
Voxels voxResult = voxA.voxBoolAdd(voxB);
Voxels voxResult = voxA + voxB;
Voxels voxResult = Voxels.voxCombineAll(aVoxelList);  // list variant

// Subtract B from A — two forms
Voxels voxResult = voxA.voxBoolSubtract(voxB);
Voxels voxResult = voxA - voxB;

// Intersection — two forms
Voxels voxResult = voxA.voxBoolIntersect(voxB);
Voxels voxResult = voxA & voxB;

// Offset (positive = grow, negative = shrink)
Voxels voxResult = voxSource.voxOffset(fOffsetMM);

// Smoothen edges
Voxels voxResult = voxSource.voxSmoothen(fStrengthMM);

// Over-offset: first grow to close small gaps, then shrink back
Voxels voxResult = voxLattice.voxOverOffset(fInitialOffset, fFinalOffset);

// Double offset (v1.7): two independent passes in one call
Voxels voxResult = voxSource.voxDoubleOffset(fDist1MM, fDist2MM);

// Fillet (v1.7): radius-based rounding of concave edges
Voxels voxResult = voxSource.voxFillet(fRoundingMM);

// Shell extraction (v1.7): hollow a solid to a wall of given thickness
Voxels voxShell = voxSolid.voxShell(fNegOffsetMM, fPosOffsetMM);

// Intersect with SDF infill
Voxels voxFilled = voxBounding.voxIntersectImplicit(sdfGyroid);
```

> **Deprecation note:** `Sh.voxAdd`, `Sh.voxSubtract`, `Sh.voxIntersect`, `Sh.voxOffset`,
> `Sh.voxSmoothen`, `Sh.voxOverOffset`, `Sh.voxIntersectImplicit`, `Sh.voxUnion(list)`,
> `Sh.voxShell`, `Sh.oGetBoundingBox`, `Sh.vecGetClosestSurfacePoint`,
> `Sh.vecGetProjectedSurfacePoint` are all `[Obsolete]` in ShapeKernel v1.7.
> Use the instance methods above.

---

## CEM Class Structure (Partial Class Pattern)

All LEAP 71 Computational Engineering Models use a **partial class** pattern. The class is split
across multiple files, each holding one or two functions. The `voxConstruct()` method is the
top-level assembly entry point.

```csharp
// HelixHeatX.cs — boundary conditions set in constructor
public partial class HelixHeatX
{
    LocalFrame m_oFrame;
    float      m_fLength;

    public HelixHeatX(LocalFrame oFrame, float fLength)
    {
        m_oFrame  = oFrame;
        m_fLength = fLength;
    }

    public void Task()
    {
        HelixHeatX oHX = new HelixHeatX(new LocalFrame(), 100f);
        Voxels voxPart  = oHX.voxConstruct();
        // export...
    }
}

// HelixHeatX_Construct.cs — top-level assembly
public partial class HelixHeatX
{
    public Voxels voxConstruct()
    {
        // 1. Build fluid voids (inverse design)
        Voxels voxHotVoid  = GetHelicalVoid(bHot: true);
        Voxels voxColdVoid = GetHelicalVoid(bHot: false);
        Voxels voxInnerVolume = Sh.voxAdd(voxHotVoid, voxColdVoid);
        voxInnerVolume = Sh.voxAdd(voxInnerVolume, voxGetTurningFins());
        voxInnerVolume = Sh.voxAdd(voxInnerVolume, voxGetStraightFins());

        // 2. Build outer shell
        Voxels voxOuterVolume = voxGetOuterStructure();
        voxOuterVolume = Sh.voxAdd(voxOuterVolume, GetFlange());

        // 3. Subtract voids from shell (final result)
        return Sh.voxSubtract(voxOuterVolume, voxInnerVolume);
    }
}
```

**High-level CEM structure should be readable without understanding every math detail.**

---

## Mandatory Output Fields

Every Shape Kernel Specialist output MUST include:
1. `findings` — list of shapes created, bounding box, composition chain
2. `assumptions` — NEVER null; minimum three (LocalFrame choice, BaseShape selection, Boolean order)
3. `what_would_falsify` — disconnected result / wall below minimum thickness / Boolean order error
4. `provenance` — ShapeKernel version + PicoGK version + input hash
5. `confidence` — float 0.0–1.0
6. `shape_kernel_summary` — shape types used, Boolean ops count, final bounding box

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "BaseShapes instantiated: [list of types and counts]"
  - "Boolean operations performed: [N] (Add: X, Subtract: Y, Intersect: Z)"
  - "Final bounding box: X.X × Y.Y × Z.Z mm"
  - "Minimum wall thickness in design: X.X mm (voxel size required: ≤ X.X mm)"
assumptions:
  - "LocalFrame origin at [X, Y, Z] — verify alignment with assembly coordinate system"
  - "BaseShape selection matches intended geometry class — no raw Lattice substitutes"
  - "Boolean subtract applied after outer shell is complete — order is critical"
what_would_falsify: >
  Boolean subtract produces disconnected voxels;
  or minimum wall thickness < 1 voxel at stated voxel size;
  or voxConstruct() produces empty Voxels.
provenance: "ShapeKernel [version] / PicoGK [version] — input SHA256: [hash]"
confidence: 0.80
shape_kernel_summary:
  baseshape_types: []
  boolean_op_count: 0
  final_bbox_mm: [0.0, 0.0, 0.0]
  min_wall_mm: 0.0
  status: "unverified"
```

---

## Escalation Flags

Raise **[PICOGK VALIDATION REQUIRED]** when:
- voxConstruct() returns empty Voxels after Boolean subtract
- Minimum wall thickness is below the selected voxel size
- CEM structure lacks voxConstruct() as top-level entry point
- Nomenclature violations detected (missing `f`, `vec`, `vox` prefixes on any variable)

---

## Known Failure Patterns

Pre-seeded known failure modes:
- **Nomenclature violation**: missing variable prefixes breaks convention and causes code review failure
- **Raw Lattice instead of BaseShape**: using AddBeam() to build structural walls instead of BaseShape — hard to maintain
- **Wrong Boolean order**: subtracting void before outer shell is complete — empty result
- **LocalFrame not specified**: constructing BaseShapes at origin when off-origin placement is needed
- **Missing voxConstruct() pattern**: building geometry inline rather than in structured partial class methods

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | BaseShape instantiation, Boolean ops, LocalFrame |
| 2 | Apprentice | 0.40–0.59 | Custom IImplicit SDFs, CEM partial class structure |
| 3 | Journeyman | 0.60–0.74 | Modulations, transformations, multi-shape assemblies |
| 4 | Expert | 0.75–0.89 | Full CEM with inverse design, readable high-level structure |
| 5 | Master | 0.90–1.00 | Novel BaseShapes, library extensions |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## References

- ShapeKernel repository: https://github.com/leap71/LEAP71_ShapeKernel
- Getting started tutorial: https://github.com/leap71/LEAP71_ShapeKernel/blob/main/Documentation/README-GettingStarted.md
- Reading details (nomenclature, BaseShapes): https://github.com/leap71/LEAP71_ShapeKernel/blob/main/Documentation/README-ReadingDetails.md
- HelixHeatX CEM example: https://github.com/leap71/LEAP71_HelixHeatX
- SDF primitives reference: https://iquilezles.org/articles/distfunctions/
