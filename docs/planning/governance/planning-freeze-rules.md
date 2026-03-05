# Planning Freeze Rules

> Rules for when planning is frozen and how addenda are handled.

---

## When Planning Is Frozen

The planning baseline is declared frozen when:
1. All P0 items in `docs/planning/roadmap/planning-priority-map.md` are complete
2. All contracts are marked FROZEN
3. Master Index is accurate and current
4. Risk register has been reviewed
5. Decision log has no pending ADRs

After freeze, no new subsystems may be added to P0 scope without a new ADR.

---

## Addendum Intake Rules

Before adding any new planning document or expanding scope:

1. **Does it affect the MVP critical path?**
   - If yes: requires ADR + explicit prioritization
   - If no: can be added as P1 or P2, but does not block build start

2. **Can it wait?**
   - If it can wait until after v0.1 build starts: classify as P1
   - If it can wait until V1: classify as P2

3. **If added, what document is canonical?**
   - All new additions must reference a single canonical document
   - No duplicate specs (addenda must be integrated, not accumulated)

---

## Normalization Schedule

- After v0.1 build starts: integrate any P0 addenda into main catalog, retire fragments
- After v0.1 complete: integrate V1 planning docs
- After V1 complete: integrate R&D planning docs

---

## What "Frozen" Means for Planning Docs

- Frozen planning docs can be referenced but not re-opened for debate
- To change a frozen decision: write a new ADR that supersedes it
- Frozen contracts: version bump required, see `docs/contracts/schema-versioning-policy.md`
