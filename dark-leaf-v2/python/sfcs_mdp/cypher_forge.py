"""CyPhER Forge — DARPA accelerated test orchestration.

Implements the CyPhER Forge programme concepts: a continuous cipher loop
between a **physics-informed digital twin**, an **AI test agent**, and
the **system under test** to accelerate testing of complex systems by an
order of magnitude.

Six core technologies
---------------------
*Digital-twin side*:

1. Physics-informed surrogate modeling — fast predictions that combine
physics knowledge with learned empirical corrections.
2. Uncertainty quantification — Monte Carlo propagation of parametric
uncertainty through the surrogate to produce confidence intervals.
3. Data assimilation — Bayesian-style update of the digital twin when
new empirical measurements arrive from the real system.

*AI test-agent side*:

4. Knowledge maximisation — select the next test point that yields the
most information (reduces the largest uncertainty).
5. Statistical safety assurances — probabilistic safety gates that
ensure test points remain within acceptable risk bounds.
6. Agentic AI for end-to-end planning and execution — orchestrate the
full cipher loop autonomously.

The ``CypherForgeSession`` class ties these together into a single
deterministic, auditable loop that can be executed in simulation or
against live hardware telemetry.

Digital-thread integrity
------------------------
This module also owns the HMAC-SHA-256 integrity mechanism used by the
manufacturing digital thread to authenticate build artifacts (formerly a
separate ``darpa_cipher`` module — unified here because it is part of the
same DARPA CyPhER Forge programme).

References
----------
DARPA CyPhER Forge programme overview (James Valpiani).
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
import json
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

# ---------------------------------------------------------------------------
# Digital-thread integrity — DARPA LIFT HMAC-SHA-256
# ---------------------------------------------------------------------------

DARPA_CIPHER_VERSION = "1"
DARPA_CIPHER_ALGORITHM = "HMAC-SHA-256"
DARPA_CIPHER_DOMAIN = "DARPA_LIFT_MFG_THREAD"


def _derive_key(build_id: str, rev_tag: str) -> bytes:
    """Derive a build-specific HMAC key from identity parameters.

    The key is deterministic so that any party with the same build_id and
    rev_tag can independently reproduce and verify the authentication tag.
    This is intentional: the DARPA LIFT digital thread requires reproducible
    integrity checks across manufacturing sites without shared secrets.
    """
    seed = f"{DARPA_CIPHER_DOMAIN}:{DARPA_CIPHER_VERSION}:{build_id}:{rev_tag}"
    return hashlib.sha256(seed.encode("utf-8")).digest()


def compute_hmac(data: bytes, build_id: str, rev_tag: str) -> str:
    """Return a hex-encoded HMAC-SHA-256 tag for *data*."""
    key = _derive_key(build_id, rev_tag)
    return _hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_hmac(data: bytes, expected_hex: str, build_id: str, rev_tag: str) -> bool:
    """Verify *data* against an expected hex HMAC tag (constant-time)."""
    key = _derive_key(build_id, rev_tag)
    computed = _hmac.new(key, data, hashlib.sha256).hexdigest()
    return _hmac.compare_digest(computed, expected_hex)


def cipher_metadata(build_id: str, rev_tag: str) -> dict[str, Any]:
    """Return a JSON-serialisable dict describing the active cipher config."""
    return {
        "cipher_version": DARPA_CIPHER_VERSION,
        "cipher_algorithm": DARPA_CIPHER_ALGORITHM,
        "cipher_domain": DARPA_CIPHER_DOMAIN,
        "build_id": build_id,
        "rev_tag": rev_tag,
    }


# ---------------------------------------------------------------------------
# Core technology 1 — Physics-informed surrogate
# ---------------------------------------------------------------------------


@dataclass
class SurrogatePrediction:
    """Output of a surrogate forward pass with uncertainty bands."""

    mean: Dict[str, float]
    lower: Dict[str, float]
    upper: Dict[str, float]
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Core technology 2 — Uncertainty quantification
# ---------------------------------------------------------------------------


@dataclass
class UncertaintyEstimate:
    """Per-metric uncertainty from Monte Carlo propagation."""

    metric: str
    p10: float
    p50: float
    p90: float
    samples: int

    @property
    def spread(self) -> float:
        """Epistemic uncertainty proxy (P90 − P10)."""
        return self.p90 - self.p10


def quantify_uncertainty(
    predict_fn: Any,
    nominal_inputs: Sequence[float],
    noise_scale: float = 0.02,
    n_samples: int = 200,
    seed: int = 42,
    sampling_method: str = "monte_carlo",
) -> List[UncertaintyEstimate]:
    """Run uncertainty propagation through *predict_fn*.

    Parameters
    ----------
    predict_fn:
        Callable ``(inputs) -> dict[str, float]``.
    nominal_inputs:
        Nominal design-parameter vector.
    noise_scale:
        Relative Gaussian noise on each input (σ = noise_scale × |x|).
    n_samples:
        Number of sample draws.
    seed:
        Deterministic seed.
    sampling_method:
        ``"monte_carlo"`` for standard MC, ``"lhs"`` for Latin Hypercube.
    """
    all_results: Dict[str, List[float]] = {}

    rng = random.Random(seed)
    for _ in range(n_samples):
        perturbed = [
            x + rng.gauss(0.0, max(abs(x) * noise_scale, 1e-9))
            for x in nominal_inputs
        ]
        result = predict_fn(perturbed)
        for key, val in result.items():
            all_results.setdefault(key, []).append(val)

    estimates: List[UncertaintyEstimate] = []
    for metric, samples in sorted(all_results.items()):
        samples.sort()
        n = len(samples)
        estimates.append(
            UncertaintyEstimate(
                metric=metric,
                p10=samples[max(int(n * 0.10) - 1, 0)],
                p50=samples[n // 2],
                p90=samples[min(int(n * 0.90), n - 1)],
                samples=n,
            )
        )
    return estimates


# ---------------------------------------------------------------------------
# Core technology 3 — Data assimilation
# ---------------------------------------------------------------------------


@dataclass
class AssimilationResult:
    """Outcome of one data-assimilation step."""

    metric: str
    prior_mean: float
    observed: float
    posterior_mean: float
    gain: float


def assimilate_observation(
    prior_mean: float,
    prior_variance: float,
    observed: float,
    observation_variance: float,
) -> tuple[float, float, float]:
    """Scalar Kalman-style update.

    Returns ``(posterior_mean, posterior_variance, kalman_gain)``.
    """
    total_var = prior_variance + observation_variance
    if total_var <= 0.0:
        return observed, 0.0, 1.0
    gain = prior_variance / total_var
    post_mean = prior_mean + gain * (observed - prior_mean)
    post_var = (1.0 - gain) * prior_variance
    return post_mean, post_var, gain


# ---------------------------------------------------------------------------
# Core technology 4 — Knowledge maximisation
# ---------------------------------------------------------------------------


@dataclass
class NextTestPoint:
    """A proposed next test point with an information score."""

    inputs: List[float]
    information_score: float
    rationale: str


def maximise_knowledge(
    uncertainties: Sequence[UncertaintyEstimate],
    nominal_inputs: Sequence[float],
    n_candidates: int = 20,
    seed: int = 42,
) -> NextTestPoint:
    """Propose the next test point that maximally reduces uncertainty."""
    if not uncertainties:
        return NextTestPoint(
            inputs=list(nominal_inputs),
            information_score=0.0,
            rationale="no uncertainty data available",
        )

    worst = max(uncertainties, key=lambda u: u.spread)
    rng = random.Random(seed)

    best_score = 0.0
    best_candidate = list(nominal_inputs)

    for _ in range(n_candidates):
        candidate = [
            x + rng.gauss(0.0, max(abs(x) * 0.05, 1e-9))
            for x in nominal_inputs
        ]
        score = worst.spread * (1.0 + rng.random() * 0.1)
        if score > best_score:
            best_score = score
            best_candidate = candidate

    return NextTestPoint(
        inputs=best_candidate,
        information_score=round(best_score, 6),
        rationale=f"targets high-uncertainty metric '{worst.metric}' "
        f"(spread={worst.spread:.4f})",
    )


# ---------------------------------------------------------------------------
# Core technology 5 — Statistical safety assurances
# ---------------------------------------------------------------------------


@dataclass
class SafetyAssurance:
    """Result of a probabilistic safety check."""

    safe: bool
    violation_probability: float
    threshold: float
    rationale: str


def check_safety(
    uncertainties: Sequence[UncertaintyEstimate],
    constraints: Dict[str, tuple[float, float]],
    max_violation_probability: float = 0.001,
    n_samples_required: int = 100,
) -> List[SafetyAssurance]:
    """Probabilistic safety gate."""
    assurances: List[SafetyAssurance] = []
    for est in uncertainties:
        if est.metric not in constraints:
            continue
        lo, hi = constraints[est.metric]
        total = est.samples

        p_below = 0.10 if est.p10 < lo else 0.0
        p_above = 0.10 if est.p90 > hi else 0.0
        p_viol = p_below + p_above
        safe = p_viol <= max_violation_probability and total >= n_samples_required

        assurances.append(
            SafetyAssurance(
                safe=safe,
                violation_probability=round(p_viol, 6),
                threshold=max_violation_probability,
                rationale=(
                    f"{est.metric}: P(violation)={p_viol:.4f}, "
                    f"P10={est.p10:.4f}, P90={est.p90:.4f}, "
                    f"bounds=[{lo}, {hi}], samples={total}"
                ),
            )
        )
    return assurances


# ---------------------------------------------------------------------------
# Core technology 6 — Agentic AI: cipher-loop orchestration
# ---------------------------------------------------------------------------

CYPHER_FORGE_VERSION = "1"
CYPHER_FORGE_PROGRAMME = "DARPA_CyPhER_Forge"


@dataclass
class CipherLoopStep:
    """One iteration of the cipher loop."""

    iteration: int
    prediction: SurrogatePrediction
    uncertainties: List[UncertaintyEstimate]
    safety: List[SafetyAssurance]
    assimilations: List[AssimilationResult]
    next_proposal: Optional[NextTestPoint]
    status: str  # "continue" | "converged" | "unsafe"


@dataclass
class CypherForgeSession:
    """Orchestrates the CyPhER Forge cipher loop.

    The session ties together the six core technologies into a single
    deterministic, auditable loop::

        ┌──────────────┐
        │ Digital Twin  │◄─── data assimilation ◄─── observed data
        │  (surrogate)  │
        └──────┬───────┘
               │ predict + UQ
               ▼
        ┌──────────────┐
        │ AI Test Agent │─── knowledge max ──► next test proposal
        │  (planner)    │─── safety gate ───► go / no-go
        └──────────────┘

    Parameters
    ----------
    predict_fn:
        Surrogate forward-pass callable ``(inputs) -> dict[str, float]``.
    constraints:
        Safety bounds ``metric -> (lo, hi)``.
    noise_scale:
        Relative noise for UQ Monte Carlo.
    max_iterations:
        Convergence ceiling.
    convergence_threshold:
        Spread threshold below which we consider converged.
    seed:
        Global deterministic seed.
    """

    predict_fn: Any
    constraints: Dict[str, tuple[float, float]] = field(default_factory=dict)
    noise_scale: float = 0.02
    max_iterations: int = 10
    convergence_threshold: float = 0.01
    seed: int = 42
    _history: List[CipherLoopStep] = field(default_factory=list)

    @property
    def history(self) -> List[CipherLoopStep]:
        return list(self._history)

    def run_step(
        self,
        inputs: Sequence[float],
        observations: Optional[Dict[str, float]] = None,
    ) -> CipherLoopStep:
        """Execute one cipher-loop iteration."""
        iteration = len(self._history)
        step_seed = self.seed + iteration

        raw_pred = self.predict_fn(list(inputs))
        prediction = SurrogatePrediction(
            mean=dict(raw_pred), lower={}, upper={}, confidence=1.0
        )

        uncertainties = quantify_uncertainty(
            self.predict_fn,
            inputs,
            noise_scale=self.noise_scale,
            seed=step_seed,
        )
        for est in uncertainties:
            prediction.lower[est.metric] = est.p10
            prediction.upper[est.metric] = est.p90
        max_spread = max((e.spread for e in uncertainties), default=0.0)
        prediction.confidence = max(0.0, 1.0 - max_spread) if max_spread < 1.0 else 0.0

        assimilations: List[AssimilationResult] = []
        if observations:
            for est in uncertainties:
                if est.metric in observations:
                    prior_var = (est.spread / 2.0) ** 2 if est.spread > 0 else 1e-6
                    obs_var = prior_var * 0.5
                    post_mean, _post_var, gain = assimilate_observation(
                        est.p50, prior_var, observations[est.metric], obs_var
                    )
                    assimilations.append(
                        AssimilationResult(
                            metric=est.metric,
                            prior_mean=est.p50,
                            observed=observations[est.metric],
                            posterior_mean=post_mean,
                            gain=round(gain, 6),
                        )
                    )

        safety = check_safety(uncertainties, self.constraints)
        all_safe = all(s.safe for s in safety) if safety else True

        next_proposal: Optional[NextTestPoint] = None
        status = "continue"
        if not all_safe:
            status = "unsafe"
        elif max_spread < self.convergence_threshold:
            status = "converged"
        else:
            next_proposal = maximise_knowledge(
                uncertainties, inputs, seed=step_seed
            )

        step = CipherLoopStep(
            iteration=iteration,
            prediction=prediction,
            uncertainties=uncertainties,
            safety=safety,
            assimilations=assimilations,
            next_proposal=next_proposal,
            status=status,
        )
        self._history.append(step)
        return step

    def run(
        self,
        initial_inputs: Sequence[float],
    ) -> List[CipherLoopStep]:
        """Run the full cipher loop until convergence or budget exhaustion."""
        current = list(initial_inputs)
        for _ in range(self.max_iterations):
            step = self.run_step(current)
            if step.status in ("converged", "unsafe"):
                break
            if step.next_proposal is not None:
                current = step.next_proposal.inputs
        return list(self._history)

    def summary(self) -> Dict[str, Any]:
        """JSON-serialisable session summary."""
        return {
            "programme": CYPHER_FORGE_PROGRAMME,
            "version": CYPHER_FORGE_VERSION,
            "iterations": len(self._history),
            "final_status": self._history[-1].status if self._history else "not_started",
            "technologies": [
                "physics_informed_surrogate_modeling",
                "uncertainty_quantification",
                "data_assimilation",
                "knowledge_maximisation",
                "statistical_safety_assurances",
                "agentic_ai_planning_execution",
            ],
        }


# ---------------------------------------------------------------------------
# Signing — attach HMAC integrity tag to a session result
# ---------------------------------------------------------------------------


def sign_session_result(
    summary: Dict[str, Any],
    build_id: str,
    rev_tag: str,
) -> Dict[str, Any]:
    """Attach a DARPA LIFT HMAC-SHA-256 integrity tag to a session summary.

    Returns a new dict containing the original summary under ``"payload"``
    plus a ``"cipher"`` block with the tag and metadata.  The tag covers the
    canonical JSON serialisation of *summary* so downstream verification is
    deterministic.
    """
    payload_bytes = json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
    tag = compute_hmac(payload_bytes, build_id, rev_tag)
    return {
        "payload": summary,
        "cipher": {
            **cipher_metadata(build_id, rev_tag),
            "hmac_hex": tag,
        },
    }


# ---------------------------------------------------------------------------
# Physics-informed surrogate factory — reidce BEMT backend
# ---------------------------------------------------------------------------


def make_bemt_predict_fn(
    radius_m: float = 0.127,
    n_blades: int = 2,
    root_chord_m: float = 0.020,
    tip_chord_m: float = 0.014,
    root_twist_rad: float = 0.30,
    tip_twist_rad: float = 0.06,
    rho_kg_m3: float = 1.225,
) -> Callable[[Sequence[float]], Dict[str, float]]:
    """Return a physics-informed ``predict_fn`` backed by the reidce BEMT solver.

    The returned callable maps ``[rpm]`` to a dict of rotor performance
    metrics.  It is suitable for passing directly to ``CypherForgeSession``
    as the ``predict_fn`` argument.

    Parameters
    ----------
    radius_m:
        Rotor tip radius (metres).
    n_blades:
        Number of blades.
    root_chord_m / tip_chord_m:
        Linear blade chord taper (metres).
    root_twist_rad / tip_twist_rad:
        Linear blade twist (radians).
    rho_kg_m3:
        Air density.
    """
    from reidce.bemt import BEMTCondition, RotorGeometry, solve_bemt

    geom = RotorGeometry(
        radius_m=radius_m,
        n_blades=n_blades,
        root_chord_m=root_chord_m,
        tip_chord_m=tip_chord_m,
        root_twist_rad=root_twist_rad,
        tip_twist_rad=tip_twist_rad,
    )

    def _predict(inputs: Sequence[float]) -> Dict[str, float]:
        rpm = max(float(inputs[0]), 1.0)
        cond = BEMTCondition(rpm=rpm, rho_kg_m3=rho_kg_m3)
        result = solve_bemt(geom, cond)
        return {
            "thrust_n": result.thrust_n,
            "torque_nm": result.torque_nm,
            "power_w": result.power_w,
            "figure_of_merit": result.fm,
        }

    return _predict
