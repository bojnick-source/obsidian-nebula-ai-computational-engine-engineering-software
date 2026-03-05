# Assembly Wrapper — Output Schema

```yaml
# MCP tool response envelope
tool_id: assembly
wrapper_version: "1.0.0"
trace_id: "<UUID v4>"
invocation_id: "<UUID v4>"
duration_s: <float>
degraded: false

output:
  assembly_status: "validated"   # "validated" | "issues_found" | "hard_failure"
  has_errors: false

  # Mass properties (Step 4)
  mass_props:
    total_mass_kg: 3.15
    mass_budget_kg: 3.5
    mass_margin_kg: 0.35
    over_budget: false
    center_of_mass_mm: [180.2, 0.0, -2.4]

  # Placement summary (Step 2)
  placements:
    - component_id: "C-001"
      name: "Fuselage"
      translation_mm: [0, 0, 0]
      rotation_deg: [0, 0, 0]
      mass_kg: 1.2

  # Interference (Step 3)
  interference_summary:
    interference_errors: 0       # hard failures
    clearance_warnings: 2        # 0.5–2.0 mm gaps
    issues:
      - type: "clearance_violation"
        components: ["C-002", "C-004"]
        severity: "warning"
        description: "C-002 ↔ C-004: 1.3 mm gap (required ≥ 2.0 mm)"
        details:
          min_gap_mm: 1.3
          required_mm: 2.0

  # Fastener validation (Step 5)
  fastener_errors: []    # validation errors (empty = all valid)

  # DFA tool access (Step 6)
  tool_access_summary:
    fasteners_checked: 12
    tool_access_errors: 0      # hard failures
    tool_access_warnings: 1    # blind assembly
    results:
      - interface_id: "IF-003"
        fastener_type: "M3_socket_head"
        issue_type: "visual_access_blocked"
        severity: "warning"
        description: "[VISUAL ACCESS BLOCKED] IF-003: blind assembly required"
        blind_assembly_required: true

  # Disassembly sequence (Step 7)
  disassembly:
    removal_order: ["C-007", "C-006", "C-004", "C-005", "C-002", "C-003", "C-001"]
    total_estimated_time_min: 18.5
    non_destructive_count: 7
    total_count: 7
    cycle_detected: false

  # Maintenance classification (Step 8)
  maintenance:
    L1_field_count: 3
    L2_depot_count: 3
    L3_factory_count: 1
    field_replaceable_fraction: 0.52
    serviceability_warnings: []
    classifications:
      - component_id: "C-007"
        name: "Canopy"
        level: "L1-field"
        reason: "Direct access, non-destructive, hand tools only"
        estimated_time_min: 1.0
        prerequisites: []

  # Vault paths written (Step 9)
  vault_paths:
    - "01-Projects/Aladdin-3B/assembly/assembly_model.md"
    - "01-Projects/Aladdin-3B/assembly/interference_report.md"
    - "01-Projects/Aladdin-3B/assembly/tool_access_report.md"
    - "01-Projects/Aladdin-3B/assembly/disassembly_sequence.md"
    - "01-Projects/Aladdin-3B/assembly/maintenance_access.md"

  # Error summary
  error_summary: []

# Error envelope (populated only if has_errors=true)
errors: []
```
