# Interface Change Process

> How to change a frozen interface without breaking the system.

---

## Process

1. **Identify the change.** Specify exactly which field, type, or behavior is changing.

2. **Determine the change type:**
   - Additive (new optional field) → minor version bump
   - Breaking → major version bump + migration plan

3. **Write an ADR** using `decision-log-template.md`. Include:
   - Which interface is affected
   - What is changing and why
   - Migration plan for existing consumers
   - Deprecation timeline

4. **Update the schema/contract document:**
   - Bump version number
   - Add version history entry
   - Mark old fields as deprecated (if keeping them temporarily)

5. **Update `forge-memory/schemas/schema_versions.yaml`**

6. **Update all consumers:**
   - List all components that depend on the interface
   - Update each consumer before merging
   - Merge in a single coordinated PR if breaking

7. **Update CI** to validate against new version

8. **Remove deprecated fields** after one milestone

---

## Who Can Approve Interface Changes?

- Minor version (additive): single reviewer + passing CI
- Major version (breaking): ADR required, two reviewers, explicit migration plan

---

## Emergency Changes

If a critical bug requires an urgent contract change:
1. Write ADR (even briefly)
2. Note it as `Status: Emergency`
3. Fix in patch
4. Properly document in next regular planning cycle
