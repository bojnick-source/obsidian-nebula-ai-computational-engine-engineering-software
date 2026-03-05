# CATIA Import Bridge

**Status:** V1 (not in MVP scope)

## Purpose

Import CATIA V5/V6 geometry into FORGE for FEA/CFD analysis.

## Export Format

- Recommended: `.step` (ISO 10303) for neutral exchange
- Alternative: `.iges` (older, less reliable)
- Native `.CATpart`/`.CATproduct` if OCCT can open directly

## Validation Gate

All imports pass through `external-ecosystem/validation/geometry-import-gates.md`.

## Known Issues

- CATIA PMI (Product Manufacturing Information) not automatically imported — manual review required
- Large assemblies: import components individually to avoid memory issues
