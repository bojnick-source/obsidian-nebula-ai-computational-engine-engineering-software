# RELOCATED — forge_agent/agents/multi_agent_orchestrator.py
#
# MultiAgentOrchestrator (v2, XML parsing, dependency graph, vault persistence)
# has been moved to forge_agent/core/multi_agent_orchestrator.py.
# Orchestration is infrastructure, not a domain agent.
#
# This shim re-exports everything for backwards compatibility.
# New code must import from forge_agent.core.multi_agent_orchestrator directly.

from forge_agent.core.multi_agent_orchestrator import (  # noqa: F401
    HumanEscalation,
    MultiAgentOrchestrator,
    ORCHESTRATOR_ASSIGNMENT_SCHEMA,
    TaskAssignment,
    find_independent_groups,
    parse_assignments_from_xml,
)
