# Manufacturing Files — Source Reference

The three YAML manufacturing data packages are retained verbatim from
`bojnick-source/DARK_leaf_drone_4-1_V2`. Fetch them directly from the
upstream repository if needed:

| File | URL |
|---|---|
| `sfcs_drone_mdp_v0.yaml` | https://raw.githubusercontent.com/bojnick-source/DARK_leaf_drone_4-1_V2/main/manufacturing/sfcs_drone_mdp_v0.yaml |
| `am_mdp_v0.yaml` | https://raw.githubusercontent.com/bojnick-source/DARK_leaf_drone_4-1_V2/main/manufacturing/am_mdp_v0.yaml |
| `mathlib_v0.yaml` | https://raw.githubusercontent.com/bojnick-source/DARK_leaf_drone_4-1_V2/main/manufacturing/mathlib_v0.yaml |

## sfcs_drone_mdp_v0.yaml — Summary

Smart Fuselage Construction System (SFCS) Manufacturing Data Package v0.
Owner: OLYTHI.EONS. Scope: non-weaponised smart airframe manufacturing
(structure + embedded sensing/comms/power distribution).

Five maturity blocks:
- BLOCK_0: composite structure + metallic interfaces
- BLOCK_1: structural health monitoring (optical fibre sensing)
- BLOCK_2: embedded power distribution
- BLOCK_3: distributed sensor tiles + comms nodes
- BLOCK_4: conformal energy modules

14-step process flow: gate review → AFP layup → insert integration → cure
cycle → machining → NDI inspection → embedded system installation.

Digital thread: frozen manifest (build ID, block level, material lot IDs,
operator IDs, calibration sets, environmental conditions) required before
each build. NCR + MRB disposition for all nonconformances.

## am_mdp_v0.yaml — Summary

Additive Manufacturing Data Package v0. Covers powder-bed fusion (PBF),
directed energy deposition (DED), and fused deposition modelling (FDM)
process parameter registries, acceptance criteria, and traceability
requirements for SFCS structural inserts.

## mathlib_v0.yaml — Summary

Manufacturing Math Library v0. SI unit definitions and prefixes,
domain allowlist (risf, additive, subtractive, metrology,
composites_3d_woven, structures), 150+ variable registry with units
and domain tags, and tripwire rules enforcing determinism (no NaN/Inf,
mandatory unit checking, domain validation, full audit provenance).
