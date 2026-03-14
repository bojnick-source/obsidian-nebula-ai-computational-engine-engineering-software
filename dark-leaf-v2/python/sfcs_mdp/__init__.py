"""SFCS MDP — Smart Fuselage Construction System Manufacturing Data Package.

Digital-thread integrity, CyPhER Forge orchestration, and C++ engine bridge.

Submodules
----------
cypher_forge    CyPhER Forge: HMAC integrity + cipher loop + BEMT surrogate
v2_engine       Python ↔ C++ v2_engine_cli bridge
"""
from __future__ import annotations

from sfcs_mdp.cypher_forge import (
    DARPA_CIPHER_ALGORITHM,
    DARPA_CIPHER_DOMAIN,
    DARPA_CIPHER_VERSION,
    AssimilationResult,
    CipherLoopStep,
    CypherForgeSession,
    NextTestPoint,
    SafetyAssurance,
    SurrogatePrediction,
    UncertaintyEstimate,
    assimilate_observation,
    check_safety,
    cipher_metadata,
    compute_hmac,
    make_bemt_predict_fn,
    maximise_knowledge,
    quantify_uncertainty,
    sign_session_result,
    verify_hmac,
)
from sfcs_mdp.v2_engine import (
    find_engine_cli,
    run_engine,
)

__all__ = [
    # integrity
    "DARPA_CIPHER_ALGORITHM",
    "DARPA_CIPHER_DOMAIN",
    "DARPA_CIPHER_VERSION",
    "cipher_metadata",
    "compute_hmac",
    "verify_hmac",
    # cypher forge
    "AssimilationResult",
    "CipherLoopStep",
    "CypherForgeSession",
    "NextTestPoint",
    "SafetyAssurance",
    "SurrogatePrediction",
    "UncertaintyEstimate",
    "assimilate_observation",
    "check_safety",
    "make_bemt_predict_fn",
    "maximise_knowledge",
    "quantify_uncertainty",
    "sign_session_result",
    # v2_engine
    "find_engine_cli",
    "run_engine",
]
