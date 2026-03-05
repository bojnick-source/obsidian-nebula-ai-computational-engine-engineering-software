# X-Plane Simulator Bridge

**Status:** V1 (not in MVP scope)

## Purpose

Connect X-Plane (flight simulator) as a behavior feedback channel for aircraft designs. Visual models are tested in X-Plane for subjective behavior; validated behaviors are returned to the engineering channel for quantitative analysis.

## Channel Classification

X-Plane is a **Visual/Concept Channel** — NOT an engineering-authoritative channel.

Results from X-Plane simulation inform engineering decisions but do not replace FEA/CFD analysis. All engineering conclusions must come from the engineering channel (CalculiX, OpenFOAM, etc.).

## Integration Pattern

```
Aero design (OpenVSP + SU2 aerodynamic results)
  │
  ▼
X-Plane visual model preparation (Blender or Plane Maker)
  │
  ▼
X-Plane simulation (behavior feedback)
  │
  ▼
"Does it fly like expected?" feedback
  │
  ▼ (if behavioral discrepancy found)
Return to engineering channel (ME/Controls specialist)
  for quantitative investigation
```

## Import Validation

X-Plane OBJ/ACF files are classified as `visual-only` — they cannot enter the FEA pipeline.
