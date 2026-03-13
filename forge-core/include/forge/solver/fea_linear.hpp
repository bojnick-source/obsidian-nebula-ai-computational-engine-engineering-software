#pragma once

/**
 * @file fea_linear.hpp
 * @brief Deterministic float64 FEA linear system solver.
 *
 * Implements:
 *   - Gaussian elimination with partial pivoting (double precision)
 *   - Euler-Bernoulli 4x4 local stiffness matrix
 *   - Stiffness assembly for 1-D beam meshes
 *   - Penalty-method boundary condition application
 *
 * Design policy (FORGE polyglot accuracy layer):
 *   - All arithmetic is double (float64) — no float promotion, no implicit narrowing.
 *   - Error conditions are returned as forge::common::Result<T> — no exceptions.
 *   - Pure functions are marked [[nodiscard]].
 *   - No static mutable state (thread-safe).
 *
 * Python counterpart: forge-solver/src/forge_solver/fea.py
 */

#include "forge/common/result.hpp"

#include <array>
#include <cstddef>
#include <span>
#include <vector>

namespace forge::solver {

// ── Types ────────────────────────────────────────────────────────────────────

/// Dynamic dense matrix stored in row-major order.
struct DenseMatrix {
    std::size_t rows{0};
    std::size_t cols{0};
    std::vector<double> data;  ///< data[row * cols + col]

    DenseMatrix() = default;
    DenseMatrix(std::size_t r, std::size_t c)
        : rows(r), cols(c), data(r * c, 0.0) {}

    [[nodiscard]] double& at(std::size_t r, std::size_t c) noexcept {
        return data[r * cols + c];
    }
    [[nodiscard]] double at(std::size_t r, std::size_t c) const noexcept {
        return data[r * cols + c];
    }
};

/// Parameters for a single Euler-Bernoulli beam element.
struct BeamElementParams {
    double elastic_modulus_pa;       ///< Young's modulus [Pa]
    double moment_of_inertia_m4;     ///< Second moment of area [m⁴]
    double length_m;                 ///< Element length [m]
};

/// Hollow circular cross-section dimensions.
struct HollowCircleSection {
    double outer_diameter_m;
    double wall_thickness_m;

    /// Compute moment of inertia I = π(R⁴ - r⁴)/4.
    [[nodiscard]] double moment_of_inertia() const noexcept;
    /// Compute cross-sectional area A = π(R² - r²).
    [[nodiscard]] double area() const noexcept;
};

// ── Stiffness helpers ─────────────────────────────────────────────────────────

/**
 * @brief Build the 4×4 local stiffness matrix for one Euler-Bernoulli element.
 *
 * DOF ordering: [v1, θ1, v2, θ2] (transverse + rotation at each node).
 *
 * @param elem  Element geometric and material parameters.
 * @return      Symmetric 4×4 matrix as a flat row-major array.
 */
[[nodiscard]] std::array<double, 16>
build_local_stiffness(const BeamElementParams& elem) noexcept;

/**
 * @brief Assemble global stiffness matrix from n_elements beam elements.
 *
 * @param elements  Vector of element parameters (length = n_elements).
 * @return          (2*(n_elements+1)) × (2*(n_elements+1)) global K matrix,
 *                  or an error if inputs are invalid.
 */
[[nodiscard]] forge::common::Result<DenseMatrix>
assemble_global_stiffness(std::span<const BeamElementParams> elements);

// ── Boundary conditions ───────────────────────────────────────────────────────

/**
 * @brief Apply fixed DOF constraints via penalty method (modifies K and F in place).
 *
 * Sets K[dof,dof] = penalty, K[dof,*] = 0, K[*,dof] = 0, F[dof] = 0
 * for each dof in fixed_dofs.
 *
 * @param K          Global stiffness matrix (modified in place).
 * @param F          Force vector (modified in place).
 * @param fixed_dofs Zero-based DOF indices to constrain.
 * @param penalty    Penalty stiffness (default 1e20 — much larger than structural K).
 */
void apply_penalty_bcs(
    DenseMatrix& K,
    std::vector<double>& F,
    std::span<const std::size_t> fixed_dofs,
    double penalty = 1.0e20
) noexcept;

// ── Linear solver ─────────────────────────────────────────────────────────────

/**
 * @brief Solve K·d = F using Gaussian elimination with partial pivoting.
 *
 * Operates on a copy of K to avoid modifying the caller's stiffness matrix.
 * All arithmetic is double precision (float64).
 *
 * @param K  n×n coefficient matrix (square, must match size of F).
 * @param F  Right-hand side force vector of length n.
 * @return   Displacement vector d of length n, or an error if K is singular
 *           (pivot < 1e-14 * max|K|).
 */
[[nodiscard]] forge::common::Result<std::vector<double>>
gauss_eliminate(DenseMatrix K, std::vector<double> F);

// ── Stress recovery ────────────────────────────────────────────────────────────

struct ElementStressResult {
    double axial_stress_pa;
    double bending_stress_pa;
    double von_mises_pa;
    double safety_factor;   ///< yield / von_mises (kInf if stress == 0)
};

static constexpr double kInf = 1.0e300;

/**
 * @brief Recover stresses for all elements from the displacement vector.
 *
 * @param elements          Element parameters.
 * @param displacements     Global displacement vector (size = 2*(n+1)).
 * @param yield_strength_pa Material yield strength [Pa].
 * @param outer_diameter_m  Extreme fibre distance = D/2 for hollow circle.
 * @return Vector of element stress results (length = n_elements),
 *         or error if dimensions mismatch.
 */
[[nodiscard]] forge::common::Result<std::vector<ElementStressResult>>
recover_stresses(
    std::span<const BeamElementParams> elements,
    std::span<const double> displacements,
    double yield_strength_pa,
    double outer_diameter_m
);

// ── Convenience: full cantilever beam solve ────────────────────────────────────

struct CantileverResult {
    std::vector<double> displacements;
    std::vector<ElementStressResult> stresses;
    double max_displacement_m;
    double max_stress_pa;
    double strain_energy_j;
};

/**
 * @brief Solve a tip-loaded cantilever beam end-to-end.
 *
 * Fixed at node 0 (DOFs 0, 1). Tip load applied at last node (DOF 2*n).
 *
 * @param section           Cross-section geometry.
 * @param length_m          Total beam length [m].
 * @param n_elements        Number of elements (>= 2).
 * @param elastic_modulus   Young's modulus [Pa].
 * @param yield_strength    Yield strength [Pa].
 * @param tip_load_n        Transverse tip load [N].
 * @return CantileverResult, or error on invalid inputs or singular K.
 */
[[nodiscard]] forge::common::Result<CantileverResult>
solve_cantilever(
    const HollowCircleSection& section,
    double length_m,
    std::size_t n_elements,
    double elastic_modulus,
    double yield_strength,
    double tip_load_n
);

}  // namespace forge::solver
