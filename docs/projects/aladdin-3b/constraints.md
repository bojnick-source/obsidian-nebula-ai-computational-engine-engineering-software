# Aladdin-3B Constraints

---

## Structural Constraints

| Constraint | Value | Source |
|---|---|---|
| Primary structural material | 6061-T6 aluminum | Design requirement |
| Max von Mises stress (flight) | < 0.6 × σ_yield = < 165.6 MPa | Safety factor 1.67 minimum |
| Max deflection (motor mount) | < 0.5 mm under max thrust | Operational requirement |
| Fatigue life (motor mount) | > 1000 flight cycles | Design life requirement |
| Temperature range | -20°C to +60°C operational | Environmental |

## Mass Constraints

| Constraint | Value |
|---|---|
| Motor mount bracket budget | < 50g |
| Total structural mass budget | TBD |

## Manufacturing Constraints

| Constraint | Value |
|---|---|
| Manufacturing process | CNC machining (primary), 3D printing (prototypes) |
| Minimum wall thickness (CNC) | 1.5 mm |
| Minimum radius (CNC) | 0.5 mm |

## Analysis Constraints (MVP)

- Linear elastic analysis only at MVP
- Static loading only at MVP
- No thermal effects at MVP
- No fatigue analysis at MVP
- Simplified geometry (parametric bracket, not imported CAD) at MVP
