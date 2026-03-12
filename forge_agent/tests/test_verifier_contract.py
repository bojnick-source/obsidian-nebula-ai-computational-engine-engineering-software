"""Tests for AgentOutputContract static validator and VerifierAgent."""

from forge_agent.agents.verifier import AgentOutputContract, ContractViolation


VALID_OUTPUT = {
    "model_choice": "Euler-Bernoulli beam theory is appropriate for L/h > 10",
    "equations": [r"$$\sigma = M \cdot c / I$$", r"$$I = b h^3 / 12$$"],
    "units": "SI: Pa, m, kg",
    "sanity_checks": [
        {"type": "limiting_case", "detail": "For zero load, σ = 0 ✓"},
        {"type": "dimensional", "detail": "[N·m · m / m⁴] = [Pa] ✓"},
    ],
    "calculation_path": "Step 1: compute I = 0.01 × 0.02³ / 12 = 6.67e-9 m⁴. Step 2: σ = 1000 × 0.01 / 6.67e-9 = 1.5 MPa.",
    "numerical_answer": "σ_max = 1.5 MPa",
    "assumptions": ["Small deflection", "Linear elastic material"],
}


class TestAgentOutputContract:
    def test_valid_output_no_violations(self):
        violations = AgentOutputContract.validate(VALID_OUTPUT)
        assert violations == []

    def test_missing_model_choice(self):
        bad = {**VALID_OUTPUT}
        del bad["model_choice"]
        violations = AgentOutputContract.validate(bad)
        fields = [v.field for v in violations]
        assert "model_choice" in fields

    def test_missing_equations(self):
        bad = {**VALID_OUTPUT, "equations": []}
        violations = AgentOutputContract.validate(bad)
        assert any(v.field == "equations" for v in violations)

    def test_missing_sanity_checks(self):
        bad = {**VALID_OUTPUT, "sanity_checks": []}
        violations = AgentOutputContract.validate(bad)
        assert any(v.field == "sanity_checks" for v in violations)

    def test_missing_units(self):
        bad = {**VALID_OUTPUT, "units": ""}
        violations = AgentOutputContract.validate(bad)
        assert any(v.field == "units" for v in violations)

    def test_missing_calculation_path(self):
        bad = {**VALID_OUTPUT}
        del bad["calculation_path"]
        violations = AgentOutputContract.validate(bad)
        assert any(v.field == "calculation_path" for v in violations)

    def test_equations_must_be_list(self):
        bad = {**VALID_OUTPUT, "equations": "$$\\sigma = M c / I$$"}
        violations = AgentOutputContract.validate(bad)
        assert any(v.field == "equations" for v in violations)

    def test_multiple_missing_fields(self):
        bad = {
            "model_choice": "",
            "equations": [],
            "units": "",
            "sanity_checks": None,
            "calculation_path": None,
        }
        violations = AgentOutputContract.validate(bad)
        assert len(violations) >= 4

    def test_violation_has_reason(self):
        bad = {**VALID_OUTPUT}
        del bad["model_choice"]
        violations = AgentOutputContract.validate(bad)
        for v in violations:
            assert isinstance(v, ContractViolation)
            assert v.reason
            assert v.field
