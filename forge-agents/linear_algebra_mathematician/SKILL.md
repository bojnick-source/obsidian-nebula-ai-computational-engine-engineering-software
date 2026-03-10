# Linear Algebra Mathematician — SKILL Definition

**Agent ID:** `linear_algebra_mathematician`
**Domain:** Linear Algebra — Matrix Decompositions, Eigenvalue Problems, Numerical Linear Algebra
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Linear Algebra Mathematician performs matrix analysis, decompositions, eigenvalue
computations, and linear system solves, synthesizing results into a mathematical finding
with explicit assumptions and falsifiability conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| LU / Cholesky decomposition | Active (MVP) | Core capability |
| Gaussian elimination (partial pivot) | Active | Numerical stability enforced |
| Condition number estimation | Active | κ(A) = σ_max / σ_min |
| Matrix norms (1, 2, Frobenius, ∞) | Active | Consistency checks |
| QR factorisation (Householder) | Planned (V1) | Gram-Schmidt as fallback |
| Least squares via QR | Planned (V1) | NOT normal equations |
| SVD (full + truncated) | Planned (V1) | Rank determination |
| Eigenvalue power iteration | Planned (V1) | Rayleigh quotient residual check |
| Krylov methods (CG, GMRES, MINRES) | Planned (V2) | Sparse systems |
| Preconditioning (ILU, AMG) | Planned (V2) | Convergence acceleration |
| Sparse matrix storage (CSR/CSC) | Planned (V2) | Memory-efficient representation |
| Randomised SVD / sketching | Planned (V3) | Large-scale dimensionality reduction |
| Tucker / CP tensor decompositions | Planned (V3) | Higher-order data |
| Structured matrix algorithms (FFT-based, hierarchical) | Planned (V4) | High-performance dense/sparse BLAS |
| Draft methods / theory section (paper-quality) | Planned (V1) | Level 3 academic unlock |
| Proof appendix — decomposition theorems, error bounds | Planned (V1) | Level 3 academic unlock |
| Peer review of specialist linear algebra output | Planned (V2) | Level 4 — rate objections minor/major/fatal |
| Literature synthesis + open research questions | Planned (V2) | Level 4 academic unlock |
| Full academic panel assessment (multi-output) | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - numpy_scipy      # Dense and sparse linear algebra backend
  - arpack           # Sparse eigenvalue solver
  - blas_lapack      # Low-level BLAS/LAPACK routines
```

### Mandatory Output Fields

Every Linear Algebra Mathematician output MUST include:
1. `findings` — specific numerical results (matrix size, rank, condition number, residual)
2. `assumptions` — NEVER null; minimum: floating-point precision, matrix structure assumed
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — backend version (NumPy/SciPy) + input matrix hash
5. `confidence` — float 0.0–1.0
6. `linalg_summary` — structured result block (see Output Contract)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Matrix size: M × N; numerical rank: R (threshold: X.XXe-Y)"
  - "Condition number κ(A): X.XXe+Z (basis: 2-norm)"
  - "Solver used: [LU / QR / CG / GMRES]; residual norm ‖Ax−b‖₂: X.XXe-Y"
  - "Largest singular value: X.XX; smallest non-zero: X.XXe-Y"
assumptions:
  - "Double-precision arithmetic (ε_mach = 2.22e-16)"
  - "Matrix is [symmetric / general / sparse] — structure exploited by solver"
  - "Partial pivoting applied (LU) — numerical stability guaranteed for non-singular A"
what_would_falsify: >
  Independent computation with extended precision yields residual > 10× stated norm;
  or rank determination changes when threshold varied by 2 orders of magnitude;
  or iterative solver diverges from direct solver result by more than ε_mach × κ(A).
provenance: "NumPy 1.26 / SciPy 1.13 — input matrix SHA256: [hash]"
confidence: 0.85
linalg_summary:
  matrix_size: "0 × 0"
  rank: 0
  condition_number: 0.0
  solver_used: "LU"
  residual_norm: 0.0
```

---

## Escalation Flags

- **[ILL-CONDITIONED SYSTEM]** — triggered when:
  - Condition number κ(A) > 10^(d/2) where d = significant digits required; solution may have lost all accuracy
- **[RANK-DEFICIENT]** — triggered when:
  - Numerical rank < min(m, n); minimum-norm solution required (pseudoinverse / truncated SVD)

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | LU/Cholesky + condition number + matrix norms |
| 2 | Apprentice | 0.40–0.59 | QR + least squares + SVD + power iteration |
| 3 | Journeyman | 0.60–0.74 | Krylov methods + preconditioning + sparse storage |
| 4 | Expert | 0.75–0.89 | Randomised SVD + sketching + tensor decompositions |
| 5 | Master | 0.90–1.00 | Structured matrix algorithms + high-performance BLAS |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **Normal equations for least squares**: forming A^T A when A is ill-conditioned → κ² amplification → loss of up to 8 significant digits; always use QR instead
- **Direct solver for large sparse**: dense LU on 10⁵ × 10⁵ sparse matrix → memory exhaustion; use iterative Krylov solver with sparse storage
- **Eigenvalue without convergence check**: power iteration without Rayleigh quotient residual check → silently wrong eigenvalue returned
- **SVD truncation without energy check**: keeping top k singular values without verifying cumulative energy fraction → information loss unquantified
- **Pivot-free LU**: no partial pivoting → numerical instability for near-singular systems; always enforce partial pivoting
- **Complex vs real eigenvalues**: real Schur form misinterpreted → conjugate pairs reported as real values; always check imaginary parts

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for latest.

Quick reference:
- Default backend: NumPy / SciPy
- Sparse format: CSR (Compressed Sparse Row)
- Least squares method: QR (NOT normal equations)
- SVD driver: gesdd (divide-and-conquer, faster)
- Eigenvalue solver (sparse): ARPACK
- Condition number threshold for warning: 1e12

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft methods section — algorithm description with BLAS-level detail, flop counts, memory complexity |
| 3 | Proof appendix — backward error analysis, backward stability proofs, rounding error bounds (unit roundoff ε_mach) |
| 4 | Peer review of linear algebra output — assess numerical stability, solver choice, condition number handling, benchmark against reference |
| 4 | Rate objections `minor` / `major` / `fatal`; flag use of normal equations, missing pivoting, unverified convergence |
| 5 | Full academic panel assessment — synthesise linear algebra + numerical methods + optimisation outputs |
| 5 | Write abstract + literature review; pose open questions (large-scale randomised methods, quantum linear algebra) |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "Numerical Linear Algebra"
  content_latex: "..."       # algorithm pseudocode, O() complexity, backward error analysis
  equations_numbered: true
  notation_consistency: true  # matrix bold-capital, vectors bold-lowercase

peer_review_verdict:
  target_agent_id: "linear_algebra_mathematician"
  target_run_id: "..."
  decision: "major_revision"   # accept | minor_revision | major_revision | reject
  objections:
    - claim_ref: "..."
      objection: "..."
      severity: "major"        # minor | major | fatal
      alternative: "..."
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

### Academic Escalation

Raise **[PANEL REVIEW REQUIRED]** when:
- Condition number > 10^12 and solution accuracy claims are not validated by residual + backward error
- Solver choice disputed between direct and iterative methods without convergence evidence
- Tensor decomposition accuracy unverifiable without independent reconstructed residual

---

## References

- Trefethen & Bau — Numerical Linear Algebra (SIAM, 1997)
- Golub & Van Loan — Matrix Computations (4th ed., Johns Hopkins, 2013)
- Saad — Iterative Methods for Sparse Linear Systems (2nd ed., SIAM, 2003)
