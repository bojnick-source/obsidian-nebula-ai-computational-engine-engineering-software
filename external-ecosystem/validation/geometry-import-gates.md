# Geometry Import Validation Gates

> Mandatory checks before any imported geometry is passed to the FEA/CFD pipeline.

---

## Gate 1: Classification
**Question:** Is this geometry engineering-ready or visual-only?

| Indicator | Classification |
|---|---|
| Exported from CATIA/Solid Edge/SolidWorks with engineering intent | engineering-ready |
| Exported from Blender for visualization | visual-only |
| Fusion360 export — depends on workflow | needs verification |

**Action:** Visual-only geometry CANNOT enter the FEA/CFD pipeline. Hard stop.

---

## Gate 2: Units and Scale
- Verify geometry units match expected (mm for structural FEA)
- Scale check: bounding box dimensions must be physically plausible
- **Fail:** `ERR_GEOM_UNITS_INVALID`

---

## Gate 3: Manifold Check
- All faces must be manifold (each edge shared by exactly 2 faces)
- No T-intersections
- No self-intersections
- **Fail:** `ERR_GEOM_NON_MANIFOLD`

---

## Gate 4: Normal Consistency
- All face normals must point consistently outward
- No inverted normals
- **Fail:** `ERR_GEOM_NORMALS_INVALID`

---

## Gate 5: Minimum Thickness
- No regions thinner than manufacturing minimum (1.5mm for CNC)
- Thin-wall warning if < 3× minimum element size for FEA
- **Warn:** `WARN_GEOM_THIN_WALL`

---

## Gate 6: Metadata
- Component name present
- Material assignment present (or flagged as missing)
- Coordinate system documented

---

## Status: V1 feature (not required at MVP)
MVP uses parametric geometry only — no external CAD import.
