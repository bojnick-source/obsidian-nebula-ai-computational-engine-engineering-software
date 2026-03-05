# Assembly Wrapper — Input Schema

```yaml
# MCP tool invocation input
tool_id: assembly
wrapper_version: "1.0.0"
trace_id: "<UUID v4>"          # propagated from orchestrator
invocation_id: "<UUID v4>"     # unique per tool call

input:
  project: "<string>"           # project name (used for vault paths)
  mass_budget_kg: <float>       # optional; null = no budget check

  # Coordinate system override (optional; default: X=aft, Y=starboard, Z=up)
  coordinate_system:
    origin_description: "nose tip of fuselage"
    units: "mm"

  # Primary component (placed at origin)
  primary_component_id: "C-001"

  # Component list
  components:
    - id: "C-001"
      name: "Fuselage"
      mass_kg: 1.2
      stl_path: "/path/to/fuselage.stl"   # empty string if STL not yet available
    - id: "C-002"
      name: "Wing L"
      mass_kg: 0.4
      stl_path: "/path/to/wing_l.stl"
    # ... additional components

  # Interface records (IF-XXX from system-decomposition)
  interfaces:
    - id: "IF-001"
      component_ids: ["C-001", "C-002"]
      offset_mm: [0, -350, 0]           # translation from neighbour
      rotation_deg: [0, 0, 0]
      joint_type: "bolted"              # bolted | snap_fit | press_fit | adhesive | riveted
      fastener_type: "M4_socket_head"   # key into FASTENER_TOOL_MAP
      is_symmetric: false
    # ... additional interfaces

  # Fastener specs (one per interface with mechanical connection)
  fastener_specs:
    - interface_id: "IF-001"
      connection_description: "Wing L to fuselage"
      fastener_type: "M4_socket_head"
      quantity: 4
      material: "A2 stainless steel"
      torque_spec_nm: 3.0
      thread_engagement_mm: 14.0      # ≥ 3× diameter
      locking: "Loctite 243"
      position_mm: [0, -350, 0]       # global position of fastener group centroid
      axis: [0, 0, 1]                 # fastener insertion direction (unit vector)
    # ... additional fastener specs

  # Components that must be field-serviceable (L1 or L2)
  frequently_replaced:
    - "C-004"   # Motor L
    - "C-005"   # Motor R
    - "C-006"   # Battery

  # Feature flags
  run_tool_access: true    # false = skip swept-volume check (faster, less safe)
  clearance_required_mm: 2.0
```
