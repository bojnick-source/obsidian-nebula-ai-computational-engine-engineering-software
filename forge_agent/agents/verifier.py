# RELOCATED — forge_agent/agents/verifier.py
#
# VerifierAgent is infrastructure (quality gate), not a domain specialist.
# The module has been moved to forge_agent/core/verifier.py.
#
# This shim re-exports everything for backwards compatibility during migration.
# New code must import from forge_agent.core.verifier directly.

from forge_agent.core.verifier import (  # noqa: F401
    VERIFIER_SYSTEM_PROMPT,
    AgentOutputContract,
    ContractViolation,
    VerificationResult,
    VerifierAgent,
)
