# Schema Versioning Policy v1

> How FORGE schemas and contracts are versioned and evolved.

---

## Version Format

Schemas use integer major versions: `v1`, `v2`, `v3`, ...

Additive changes (new optional fields) use minor versions: `v1.1`, `v1.2`, ...

Patch versions are not used for schemas.

---

## What Triggers a Version Bump

| Change Type | Version Impact | ADR Required? |
|---|---|---|
| Add optional field | Minor (v1 → v1.1) | No |
| Add required field | Major (v1 → v2) | Yes |
| Remove field | Major (v1 → v2) | Yes |
| Change field type | Major (v1 → v2) | Yes |
| Rename field | Major (v1 → v2) | Yes |
| Change enum values | Major (v1 → v2) | Yes |
| Add enum value | Minor (v1 → v1.1) | No |

---

## Compatibility Rules

- **Minor versions** (v1 → v1.1): fully backward compatible. Old consumers ignore new optional fields.
- **Major versions** (v1 → v2): breaking. All consumers must be updated. Old version supported for one milestone.

---

## Schema Registration

All schema versions are registered in `forge-memory/schemas/schema_versions.yaml`.

Each entry:
```yaml
schema_id: blackboard_entry
current_version: "v1"
versions:
  v1:
    file: forge-memory/schemas/blackboard_entry.schema.yaml
    frozen_at: "2026-03-05"
    status: active
```
