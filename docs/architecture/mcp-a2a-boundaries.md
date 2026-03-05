# MCP / A2A Boundaries

> Where MCP ends and A2A begins. How they interact. What crosses which boundary.

---

## MCP (Model Context Protocol)

**Purpose:** Tool invocation. Agent → external tool (solver, geometry engine, etc.).

**Direction:** Outbound from agent system to external tools.

**What crosses MCP:**
- Tool input (typed, schema-validated per `docs/contracts/mcp-wrapper-envelope.md`)
- Tool output (parsed, validated, wrapped in result envelope)
- Error codes and status

**What does NOT cross MCP:**
- Agent reasoning
- Debate state
- Memory operations

**Wrappers:** All tools have MCP wrapper contracts in `forge-tools/mcp-wrappers/`.

---

## A2A (Agent-to-Agent Protocol)

**Purpose:** Inter-agent communication. Specialist ↔ Antagonist, Orchestrator → Specialist.

**Direction:** Internal to agent system.

**What crosses A2A:**
- Task packets (from orchestrator to specialist)
- Agent output packets (from specialist to orchestrator/verifier)
- Debate messages (specialist ↔ antagonist in V1)
- Arbitration requests (to orchestrator)

**What does NOT cross A2A:**
- Tool invocation (that's MCP)
- Direct memory access (agents interact with memory only via Librarian)

**Transport:** gRPC in production; local in-process shim for testing.

---

## Interaction Pattern

```
ORCHESTRATOR
     │ A2A: task packet
     ▼
SPECIALIST
     │ MCP: tool invocation
     ▼
TOOL (CalculiX, GMSH, etc.)
     │ MCP: result envelope
     ▼
SPECIALIST
     │ A2A: agent output packet
     ▼
ORCHESTRATOR
     │ A2A: verification request
     ▼
VERIFIER(S)
     │ A2A: verification result
     ▼
ORCHESTRATOR → LIBRARIAN → VAULT
```

---

## Boundary Violations (forbidden)

1. Agent calling a tool directly (bypassing MCP wrapper) — FORBIDDEN
2. Tool accessing memory directly — FORBIDDEN
3. Specialist writing to vault without Librarian mediation — FORBIDDEN
4. Orchestrator bypassing verification before vault write — FORBIDDEN

---

## Protocol References

- MCP wrapper envelope: `docs/contracts/mcp-wrapper-envelope.md`
- A2A transport header: `forge-core/include/forge/a2a/a2a_transport.hpp`
- Debate lifecycle: `forge-core/include/forge/a2a/debate_lifecycle.hpp`
