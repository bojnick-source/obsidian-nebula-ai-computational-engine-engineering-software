"""SFCS MDP — Smart Fuselage Construction System Manufacturing Data Package.

Digital-thread integrity, CyPhER Forge orchestration, and C++ engine bridge.

Submodules
----------
darpa_cipher    HMAC-SHA-256 build-artifact integrity (DARPA LIFT digital thread)
cypher_forge    CyPhER Forge cipher loop: surrogate + UQ + Kalman + safety gates
v2_engine       Python ↔ C++ v2_engine_cli bridge
"""
from __future__ import annotations

from sfcs_mdp.cypher_forge import (
    AssimilationResult,
    CipherLoopStep,
    CypherForgeSession,
    NextTestPoint,
    SafetyAssurance,
    SurrogatePrediction,
    UncertaintyEstimate,
    assimilate_observation,
    check_safety,
    make_bemt_predict_fn,
    maximise_knowledge,
    quantify_uncertainty,
    sign_session_result,
)
from sfcs_mdp.darpa_cipher import (
    DARPA_CIPHER_ALGORITHM,
    DARPA_CIPHER_DOMAIN,
    DARPA_CIPHER_VERSION,
    cipher_metadata,
    compute_hmac,
    verify_hmac,
)
from sfcs_mdp.v2_engine import (
    find_engine_cli,
    run_engine,
)

__all__ = [
    # cypher_forge
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
    # darpa_cipher
    "DARPA_CIPHER_ALGORITHM",
    "DARPA_CIPHER_DOMAIN",
    "DARPA_CIPHER_VERSION",
    "cipher_metadata",
    "compute_hmac",
    "verify_hmac",
    # v2_engine
    "find_engine_cli",
    "run_engine",
]
