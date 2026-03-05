# forge-agents

Agent definitions, cards, registries, and versioned prompts for the FORGE agent system.

## Structure

```
registry/
  agent_registry.yaml       # Master list of all registered agents
  specialist_roster.yaml    # Specialist agents by domain
  antagonist_pairs.yaml     # Specialist ↔ antagonist pairings
  agent_cards/              # Per-agent YAML cards
  mathematicians/           # Math specialist cards
prompts/
  me_specialist/            # ME specialist prompts (versioned)
  materials_antagonist/     # Materials antagonist prompts
  structural_verifier/
  adversarial_verifier/
  librarian/
  prompt_engineer/
prompt_tests/               # Expected-behavior assertions for prompts
docs/
  agent-leveling.md
  ilc-link-detection.md
  emergent-agent-synthesis.md
```

## Adding a New Agent

1. Create an agent card in `registry/agent_cards/<id>.yaml`
2. Register it in `registry/agent_registry.yaml`
3. Create a versioned prompt in `prompts/<id>/v1.0.0.md`
4. Add prompt tests in `prompt_tests/<id>/`
5. Write an ADR if this is a new agent type (not an existing domain specialist)
