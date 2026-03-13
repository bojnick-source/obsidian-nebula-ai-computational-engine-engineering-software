/**
 * @file fea_linear.cpp
 * @brief Deterministic float64 FEA linear system solver implementation.
 *
 * See: forge-core/include/forge/solver/fea_linear.hpp
 */

#include "forge/solver/fea_linear.hpp"
#include "forge/common/result.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <numeric>

namespace forge::solver {

// ── HollowCircleSection ───────────────────────────────────────────────────────

double HollowCircleSection::moment_of_inertia() const noexcept {
    constexpr double kPi = 3.14159265358979323846;
    const double r_o = outer_diameter_m / 2.0;
    const double r_i = r_o - wall_thickness_m;
    return kPi * (r_o * r_o * r_o * r_o - r_i * r_i * r_i * r_i) / 4.0;
}

double HollowCircleSection::area() const noexcept {
    constexpr double kPi = 3.14159265358979323846;
    const double r_o = outer_diameter_m / 2.0;
    const double r_i = r_o - wall_thickness_m;
    return kPi * (r_o * r_o - r_i * r_i);
}

// ── Local stiffness matrix ────────────────────────────────────────────────────

std::array<double, 16>
build_local_stiffness(const BeamElementParams& elem) noexcept {
    const double L  = elem.length_m;
    const double EI = elem.elastic_modulus_pa * elem.moment_of_inertia_m4;
    const double L2 = L * L;
    const double L3 = L2 * L;

    // Row-major 4x4 matrix for DOFs [v1, θ1, v2, θ2]
    std::array<double, 16> k{};
    k[ 0] =  12.0 * EI / L3;   k[ 1] =   6.0 * EI / L2;
    k[ 2] = -12.0 * EI / L3;   k[ 3] =   6.0 * EI / L2;

    k[ 4] =   6.0 * EI / L2;   k[ 5] =   4.0 * EI / L;
    k[ 6] =  -6.0 * EI / L2;   k[ 7] =   2.0 * EI / L;

    k[ 8] = -12.0 * EI / L3;   k[ 9] =  -6.0 * EI / L2;
    k[10] =  12.0 * EI / L3;   k[11] =  -6.0 * EI / L2;

    k[12] =   6.0 * EI / L2;   k[13] =   2.0 * EI / L;
    k[14] =  -6.0 * EI / L2;   k[15] =   4.0 * EI / L;

    return k;
}

// ── Global stiffness assembly ─────────────────────────────────────────────────

forge::common::Result<DenseMatrix>
assemble_global_stiffness(std::span<const BeamElementParams> elements) {
    if (elements.empty()) {
        return forge::common::Result<DenseMatrix>::err({"ERR_EMPTY_MESH", "No elements provided"});
    }

    const std::size_t n_elem = elements.size();
    const std::size_t n_dof  = 2 * (n_elem + 1);

    DenseMatrix K(n_dof, n_dof);

    for (std::size_t i = 0; i < n_elem; ++i) {
        const auto k_local = build_local_stiffness(elements[i]);
        // Global DOF indices: [2i, 2i+1, 2i+2, 2i+3]
        const std::array<std::size_t, 4> dofs{2*i, 2*i+1, 2*i+2, 2*i+3};

        for (std::size_t a = 0; a < 4; ++a) {
            for (std::size_t b = 0; b < 4; ++b) {
                K.at(dofs[a], dofs[b]) += k_local[a * 4 + b];
            }
        }
    }

    return forge::common::Result<DenseMatrix>::ok(std::move(K));
}

// ── Boundary conditions ───────────────────────────────────────────────────────

void apply_penalty_bcs(
    DenseMatrix& K,
    std::vector<double>& F,
    std::span<const std::size_t> fixed_dofs,
    double penalty
) noexcept {
    for (const std::size_t dof : fixed_dofs) {
        if (dof >= K.rows) continue;
        for (std::size_t j = 0; j < K.cols; ++j) {
            K.at(dof, j) = 0.0;
            K.at(j, dof) = 0.0;
        }
        K.at(dof, dof) = penalty;
        if (dof < F.size()) F[dof] = 0.0;
    }
}

// ── Gaussian elimination with partial pivoting ────────────────────────────────

forge::common::Result<std::vector<double>>
gauss_eliminate(DenseMatrix K, std::vector<double> F) {
    const std::size_t n = K.rows;

    if (K.cols != n || F.size() != n) {
        return forge::common::Result<std::vector<double>>::err({
            "ERR_DIMENSION_MISMATCH",
            "K must be square and F must have the same length as K.rows"
        });
    }

    // Find the maximum absolute value of K for singularity detection threshold
    double max_k = 0.0;
    for (double v : K.data) max_k = std::max(max_k, std::abs(v));
    const double singular_threshold = 1.0e-14 * max_k;

    for (std::size_t col = 0; col < n; ++col) {
        // ── Partial pivoting ────────────────────────────────────────────────
        std::size_t max_row = col;
        double max_val = std::abs(K.at(col, col));
        for (std::size_t row = col + 1; row < n; ++row) {
            const double val = std::abs(K.at(row, col));
            if (val > max_val) {
                max_val = val;
                max_row = row;
            }
        }

        if (max_val < singular_threshold) {
            return forge::common::Result<std::vector<double>>::err({
                "ERR_SINGULAR_MATRIX",
                "Stiffness matrix is singular or near-singular — check BCs"
            });
        }

        // Swap rows
        if (max_row != col) {
            for (std::size_t j = 0; j < n; ++j) {
                std::swap(K.at(col, j), K.at(max_row, j));
            }
            std::swap(F[col], F[max_row]);
        }

        // ── Elimination ─────────────────────────────────────────────────────
        const double pivot = K.at(col, col);
        for (std::size_t row = col + 1; row < n; ++row) {
            const double factor = K.at(row, col) / pivot;
            K.at(row, col) = 0.0;
            for (std::size_t j = col + 1; j < n; ++j) {
                K.at(row, j) -= factor * K.at(col, j);
            }
            F[row] -= factor * F[col];
        }
    }

    // ── Back substitution ────────────────────────────────────────────────────
    std::vector<double> d(n, 0.0);
    for (std::ptrdiff_t row = static_cast<std::ptrdiff_t>(n) - 1; row >= 0; --row) {
        const std::size_t r = static_cast<std::size_t>(row);
        double sum = F[r];
        for (std::size_t j = r + 1; j < n; ++j) {
            sum -= K.at(r, j) * d[j];
        }
        d[r] = sum / K.at(r, r);
    }

    return forge::common::Result<std::vector<double>>::ok(std::move(d));
}

// ── Stress recovery ───────────────────────────────────────────────────────────

forge::common::Result<std::vector<ElementStressResult>>
recover_stresses(
    std::span<const BeamElementParams> elements,
    std::span<const double> displacements,
    double yield_strength_pa,
    double outer_diameter_m
) {
    const std::size_t n_elem = elements.size();
    const std::size_t expected_dof = 2 * (n_elem + 1);

    if (displacements.size() != expected_dof) {
        return forge::common::Result<std::vector<ElementStressResult>>::err({
            "ERR_DIMENSION_MISMATCH",
            "Displacement vector size does not match element count"
        });
    }

    const double c = outer_diameter_m / 2.0;  // extreme fibre distance
    std::vector<ElementStressResult> results;
    results.reserve(n_elem);

    for (std::size_t i = 0; i < n_elem; ++i) {
        const auto& elem = elements[i];
        const double d0 = displacements[2 * i];      // v1
        const double d1 = displacements[2 * i + 1];  // θ1
        const double d2 = displacements[2 * i + 2];  // v2
        const double d3 = displacements[2 * i + 3];  // θ2

        const double axial_strain  = (d2 - d0) / elem.length_m;
        const double axial_stress  = elem.elastic_modulus_pa * axial_strain;
        const double kappa         = (d3 - d1) / elem.length_m;
        const double bending_stress = elem.elastic_modulus_pa * c * kappa;

        const double von_mises = std::abs(axial_stress) + std::abs(bending_stress);
        const double sf = von_mises > 1.0e-12
                          ? yield_strength_pa / von_mises
                          : kInf;

        results.push_back({axial_stress, bending_stress, von_mises, sf});
    }

    return forge::common::Result<std::vector<ElementStressResult>>::ok(std::move(results));
}

// ── Convenience: full cantilever beam solve ────────────────────────────────────

forge::common::Result<CantileverResult>
solve_cantilever(
    const HollowCircleSection& section,
    double length_m,
    std::size_t n_elements,
    double elastic_modulus,
    double yield_strength,
    double tip_load_n
) {
    if (n_elements < 2) {
        return forge::common::Result<CantileverResult>::err({"ERR_INVALID_INPUT", "n_elements must be >= 2"});
    }
    if (length_m <= 0.0) {
        return forge::common::Result<CantileverResult>::err({"ERR_INVALID_INPUT", "length_m must be > 0"});
    }

    const double elem_len = length_m / static_cast<double>(n_elements);
    const double moi  = section.moment_of_inertia();

    std::vector<BeamElementParams> elems(n_elements, {elastic_modulus, moi, elem_len});

    // Assemble
    auto K_result = assemble_global_stiffness(elems);
    if (!K_result) return forge::common::Result<CantileverResult>::err(K_result.error());
    DenseMatrix K = std::move(K_result.value());

    const std::size_t n_dof = K.rows;
    std::vector<double> F(n_dof, 0.0);

    // Tip load at last node, transverse DOF
    F[n_dof - 2] = tip_load_n;

    // Fixed at node 0: DOFs 0 (v) and 1 (θ)
    std::array<std::size_t, 2> fixed{0, 1};
    apply_penalty_bcs(K, F, fixed);

    auto d_result = gauss_eliminate(std::move(K), std::move(F));
    if (!d_result) return forge::common::Result<CantileverResult>::err(d_result.error());

    const auto& d = d_result.value();

    auto stress_result = recover_stresses(elems, d, yield_strength, section.outer_diameter_m);
    if (!stress_result) return forge::common::Result<CantileverResult>::err(stress_result.error());

    const auto& stresses = stress_result.value();

    double max_disp = 0.0;
    for (std::size_t i = 0; i < d.size(); i += 2) {
        max_disp = std::max(max_disp, std::abs(d[i]));
    }

    double max_stress = 0.0;
    for (const auto& s : stresses) {
        max_stress = std::max(max_stress, s.von_mises_pa);
    }

    // Strain energy = 0.5 * d^T * K * d (K is already modified; approximate from stress)
    double strain_energy = 0.0;
    for (const auto& s : stresses) {
        strain_energy += 0.5 * s.von_mises_pa * s.von_mises_pa / elastic_modulus
                       * section.area() * elem_len;
    }

    return forge::common::Result<CantileverResult>::ok({
        d,
        stresses,
        max_disp,
        max_stress,
        strain_energy
    });
}

}  // namespace forge::solver
