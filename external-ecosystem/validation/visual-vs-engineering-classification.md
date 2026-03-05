# Visual vs. Engineering Classification

> How FORGE classifies imported geometry.

---

## Classification Criteria

| Source | Default Classification | Override Rule |
|---|---|---|
| CATIA V5/V6 | engineering-ready | Inspect for dummy geometry |
| Solid Edge | engineering-ready | Inspect for dummy geometry |
| SolidWorks | engineering-ready | Inspect for dummy geometry |
| Fusion360 (engineering workflow) | engineering-ready | Confirm engineering intent |
| Fusion360 (concept workflow) | visual-only | |
| Blender | visual-only | Cannot be overridden |
| FreeCAD | engineering-ready (if from FEM workbench) | Inspect for mesh quality |
| OpenVSP | geometry-model (requires meshing before FEA) | |
| X-Plane OBJ format | visual-only | Cannot be overridden |

---

## Classification Gate

Before any geometry enters the FEA or CFD pipeline:
1. Source tool identified from file metadata or user declaration
2. Classification applied per table above
3. `visual-only` → rejected from engineering pipeline immediately
4. `engineering-ready` → proceed to Gates 2–6 (see geometry-import-gates.md)
5. `geometry-model` → requires meshing step, then treat as engineering-ready

---

## Consequences of Misclassification

Passing visual-only geometry into FEA will produce physically meaningless results
(wrong wall thicknesses, inverted normals, missing material assignments).
This is why the classification gate is mandatory and non-bypassable.
