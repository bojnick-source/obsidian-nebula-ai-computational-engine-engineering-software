# Geometry Import Validation

> How imported geometry is validated before entering the engineering pipeline.

---

See `external-ecosystem/validation/geometry-import-gates.md` for the gate definitions.
See `external-ecosystem/validation/visual-vs-engineering-classification.md` for classification rules.

---

## Summary

1. Classify geometry (engineering-ready vs. visual-only)
2. If visual-only: **reject immediately** — cannot enter FEA/CFD pipeline
3. If engineering-ready: run 6 validation gates
4. All gates must pass before meshing (GMSH) is attempted

---

## Status: V1 Feature

MVP uses parametric geometry only. No external geometry imports at MVP.
