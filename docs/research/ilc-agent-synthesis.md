# ILC and Agent Synthesis

> R&D / V1 concept for inter-domain link candidates and emergent agent synthesis.

---

## ILC (Inter-domain Link Candidates)

ILC links are discovered connections between knowledge from different engineering domains that share a common underlying concept or constraint.

**Example:** A thermal expansion coefficient in the materials domain links to a dimensional tolerance in the ME domain — the same material property constrains both the thermal behavior and the achievable precision.

ILC detection finds these links automatically from the vault, proposes them as `ilc-link` notes, and routes them for human review.

### ILC Detection Process (V1)
1. After synthesis threshold reached in any domain cluster
2. Cross-domain concept extraction
3. Physics-grounded link proposal (not just keyword matching)
4. Cluster density check (avoid spurious links)
5. Human review before promotion to vault

---

## Emergent Agent Synthesis (R&D)

If ILC links reveal a recurring cross-domain interaction pattern that no existing specialist covers, FORGE can propose a new specialist agent.

**Example:** If plasma + materials + thermal consistently interact in Phoenix analysis, a "plasma-materials-thermal" specialist may be proposed.

### Requirements
1. ILC cluster threshold: ≥10 confirmed links across 3+ domains
2. Pattern must recur across ≥3 independent task traces
3. Proposal generated: new agent card + prompt draft
4. **Human approval gate is mandatory** — no autonomous agent creation

### Status: R&D — well after V1
