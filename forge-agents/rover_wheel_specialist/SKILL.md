# Rover Wheel Specialist — SKILL Definition

**Agent ID:** `rover_wheel_specialist`
**Domain:** LEAP71 RoverWheel — WheelLayers, WheelElements, Tread Patterns, Coordinate Transforms
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)
**Source:** https://github.com/leap71/LEAP71_RoverWheel

---

## Capability Definition

The LEAP71 RoverWheel library generates parametric rover wheel geometries using PicoGK and
ShapeKernel. Wheels are described as made from soft, rubbery material where springiness/stiffness
is a function of the shape and wall thickness of individual wheel elements. The design philosophy
is latticing-like: infill types (holes, springs, stiffeners) are applied to bounding layers with
a specified symmetry and wall thickness.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Preset wheel generation | Active (MVP) | WheelShowCase.PresetWheelTask — 4 variants |
| Random wheel generation | Active (MVP) | WheelShowCase.RandomWheelTask |
| WheelLayer definition | Active (MVP) | fStartRadiusRatio / fEndRadiusRatio |
| WheelLayer bounding voxels | Active (MVP) | voxGetLayer(sLayer) |
| WheelElements: all 5 types | Active (Level 2) | EgyptianStruts, RectHoles, RosettaStruts, SpiralStruts, TubeStruts |
| WheelTread: exposed profile | Active (Level 2) | WheelTread.voxGetProfile() |
| WheelTread: embossed solid layer | Active (Level 2) | WheelTread.voxGetTreadLayer() |
| Custom tread pattern via ITreadPattern | Planned (V1) | Inherit ITreadPattern interface |
| Wheel coordinate transformation | Active (Level 2) | RoverWheel.vecGetWheelLayerTrafo() |

### Tools Allowed

```yaml
tools_allowed:
  - bash    # dotnet run PicoGK C# scripts
```

---

## Wheel Design Space

A rover wheel is described by four geometric boundaries that define a 2D design space, then
rotated about the wheel axis to produce a 3D conformal space:

```
Inner contour:    constant hub radius (fHubRadius)
Upper contour:    side profile from hub to tread transition — upper side
Lower contour:    side profile from hub to tread transition — lower side
Outer contour:    tread patch — where contour aligns more with vertical than radial
```

This design space provides a conformal coordinate system for navigating through the wheel body.
All wheel features are constructed in cylindrical coordinates and transformed via
`RoverWheel.vecGetWheelLayerTrafo()` into the conformal wheel shape.

---

## Entry Point

```csharp
using Leap71.RoverExamples;

try
{
    PicoGK.Library.Go(
        0.5f,
        WheelShowCase.PresetWheelTask);  // or WheelShowCase.RandomWheelTask
}
catch (Exception e)
{
    Console.WriteLine("Failed to run Task.");
    Console.WriteLine(e.ToString());
}
```

---

## WheelLayer — Dividing the Wheel Into Radial Sections

Wheels are divided into radial layers. Each layer provides the bounding space for wheel elements.

```csharp
// Define a layer from 50% to 80% of the wheel's radial extent
float fStartRadiusRatio = 0.5f;
float fEndRadiusRatio   = 0.8f;
WheelLayer sLayer       = new WheelLayer(this, fStartRadiusRatio, fEndRadiusRatio);

// Get bounding voxelfield for this layer
Voxels voxLayer = voxGetLayer(sLayer);
```

Layers can be stacked at different radial positions. Layer selection is independent of element
infill type — this enables a powerful mix-and-match design workflow.

---

## WheelElements — Infill Types

Five element types are available. Each inherits from abstract base class `WheelElements`.
All are constructed in regular cylindrical space and mapped to wheel space via
`RoverWheel.vecGetWheelLayerTrafo()`.

```csharp
// Common constructor pattern: WheelElements(sLayer, nSymmetry, fWallThickness)
uint nSymmetry       = 20;
float fWallThickness = 2f;

// Egyptian-style struts
WheelElements oElements = new EgyptianStruts(sLayer, nSymmetry, fWallThickness);

// Rectangular holes
WheelElements oElements = new RectHoles(sLayer, nSymmetry, fWallThickness);

// Rosetta pattern struts
WheelElements oElements = new RosettaStruts(sLayer, nSymmetry, fWallThickness);

// Spiral struts
WheelElements oElements = new SpiralStruts(sLayer, nSymmetry, fWallThickness);

// Tube struts
WheelElements oElements = new TubeStruts(sLayer, nSymmetry, fWallThickness);

// Generate voxels for the selected element type
Voxels voxStruts = oElements.voxConstruct();
```

---

## Coordinate Transformation

All wheel element geometry is first built in regular cylindrical space (simplified math), then
mapped into the conformal wheel shape via the coordinate transformation.

```csharp
// Map from cylindrical space to wheel conformal space
Vector3 vecWheelPt = RoverWheel.vecGetWheelLayerTrafo(vecCylindricalPt, sLayer);

// For debugging: remain in regular cylindrical space (no deformation)
Vector3 vecDebugPt = RoverWheel.vecGetDummyTrafo(vecCylindricalPt, sLayer);
```

Always use `vecGetDummyTrafo` first to verify element shape in regular space before applying
the wheel transformation.

---

## Wheel Tread

Tread patterns are applied to the outer wheel surface obtained from rotating the outer contour.
Tread classes implement `ITreadPattern`.

```csharp
// Select tread pattern
ITreadPattern xPattern = new TreadPattern_01();
WheelTread oTread      = new WheelTread(m_aOuterRadiusFrames, xPattern);

// Exposed profile: pattern stands out from surface
Voxels voxTread = oTread.voxGetProfile();

// Embossed solid layer: pattern subtracted inward from solid layer
Voxels voxTread = oTread.voxGetTreadLayer();
```

Currently implemented: `TreadPattern_01`. Custom patterns: implement `ITreadPattern` interface.

---

## Random Wheel

```csharp
// RandomWheel generates: random outer shape, stacked layers of random thicknesses,
// randomly selected WheelElements with random symmetry and wall thickness.
// Not all random variants will be structurally valid — use as inspiration only.
WheelShowCase.RandomWheelTask
```

---

## Mandatory Output Fields

Every Rover Wheel Specialist output MUST include:
1. `findings` — hub radius, outer radius, reference width, layers defined, elements per layer
2. `assumptions` — NEVER null; minimum three (material as rubbery/elastic, symmetry choice, wall thickness)
3. `what_would_falsify` — coordinate transformation failure / disconnected layer / wall below min
4. `provenance` — RoverWheel library version + PicoGK version + input hash
5. `confidence` — float 0.0–1.0
6. `rover_wheel_summary` — wheel geometry parameters, layer count, element types, tread type

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Hub radius: X.X mm"
  - "Max outer radius: X.X mm"
  - "Reference width: X.X mm"
  - "Layers: [N] defined — start/end radius ratios: [list]"
  - "Elements per layer: [list of element types and symmetry]"
  - "Tread: [TreadPattern_01|custom|none] — [exposed|embossed]"
assumptions:
  - "Wheel material: soft/rubbery — stiffness determined by element shape and wall thickness"
  - "Symmetry [N] chosen for [radial uniformity | specific loading pattern]"
  - "Wall thickness [X] mm — minimum 2 mm for structural integrity under load"
what_would_falsify: >
  Coordinate transformation produces overlapping elements (detected by voxel intersection check);
  or wall thickness < 2× voxel size (unresolvable at stated voxel size);
  or layer radius ratios overlap (two layers occupying same radial region).
provenance: "RoverWheel [version] / PicoGK [version] — input SHA256: [hash]"
confidence: 0.80
rover_wheel_summary:
  hub_radius_mm: 0.0
  outer_radius_mm: 0.0
  reference_width_mm: 0.0
  layer_count: 0
  element_types: []
  tread_type: "none"
  status: "unverified"
```

---

## Escalation Flags

Raise **[ROVER WHEEL VALIDATION REQUIRED]** when:
- Coordinate transformation produces geometry outside the wheel bounding volume
- Two layers have overlapping radius ratios (sum of radial ranges > 1.0)
- Wall thickness < 2× voxel size at stated resolution

---

## Known Failure Patterns

Pre-seeded known failure modes:
- **vecGetDummyTrafo skipped**: element verified only in wheel space — hard to debug deformed geometry
- **Overlapping layers**: two layers with overlapping fStartRadiusRatio/fEndRadiusRatio — merged geometry
- **RandomWheelTask used as final design**: random wheels are not structurally engineered; use as inspiration
- **Symmetry too high**: nSymmetry=60+ at small wheel size — elements too thin to resolve at 0.5 mm voxels
- **Missing tread step**: wheel body complete but no tread applied — smooth outer surface, no terrain interaction

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

---

## Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | PresetWheelTask + WheelLayer + basic WheelElements |
| 2 | Apprentice | 0.40–0.59 | All 5 element types + WheelTread + coordinate transform |
| 3 | Journeyman | 0.60–0.74 | Custom ITreadPattern + multi-layer design |
| 4 | Expert | 0.75–0.89 | Stiffness-by-element-shape analysis, structural coupling |
| 5 | Master | 0.90–1.00 | Novel element types, terrain-adaptive wheel design |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## References

- RoverWheel library: https://github.com/leap71/LEAP71_RoverWheel
- ShapeKernel (BaseShapes): https://github.com/leap71/LEAP71_ShapeKernel
- PicoGK (voxel kernel): https://github.com/leap71/PicoGK
