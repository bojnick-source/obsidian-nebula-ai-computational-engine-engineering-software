"""Fastener specification and tool database — Steps 5 & 6 setup.

Canonical tool geometry database and fastener→tool mapping.
Used by both the fastener spec validator and the DFA tool access checker.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ToolGeometry:
    """Physical dimensions of an assembly/disassembly tool."""
    name: str
    # Approach cylinder: clear volume along fastener axis for tool head
    approach_diameter_mm: float
    approach_length_mm: float
    # Swing volume: handle arc during operation
    swing_radius_mm: float
    swing_arc_deg: float
    # Hand envelope (hand-held tools; 0 = not hand-held)
    hand_clearance_diameter_mm: float
    hand_clearance_length_mm: float
    # Approach alignment tolerance
    max_approach_angle_off_axis_deg: float

    @property
    def swing_arc_rad(self) -> float:
        return math.radians(self.swing_arc_deg)


# ─────────────────────────────────────────────────────────────────────────────
# Canonical tool database
# Source: measured from real tools + manufacturer datasheets.
# ─────────────────────────────────────────────────────────────────────────────

TOOL_DATABASE: dict[str, ToolGeometry] = {
    "hex_key_1.5mm": ToolGeometry(
        name="1.5mm hex key (L-shaped)",
        approach_diameter_mm=5.0,
        approach_length_mm=12.0,
        swing_radius_mm=60.0,
        swing_arc_deg=60.0,
        hand_clearance_diameter_mm=28.0,
        hand_clearance_length_mm=90.0,
        max_approach_angle_off_axis_deg=15.0,
    ),
    "hex_key_2.0mm": ToolGeometry(
        name="2.0mm hex key (L-shaped)",
        approach_diameter_mm=6.0,
        approach_length_mm=15.0,
        swing_radius_mm=80.0,
        swing_arc_deg=60.0,
        hand_clearance_diameter_mm=30.0,
        hand_clearance_length_mm=100.0,
        max_approach_angle_off_axis_deg=15.0,
    ),
    "hex_key_2.5mm": ToolGeometry(
        name="2.5mm hex key (L-shaped)",
        approach_diameter_mm=7.0,
        approach_length_mm=16.0,
        swing_radius_mm=90.0,
        swing_arc_deg=60.0,
        hand_clearance_diameter_mm=32.0,
        hand_clearance_length_mm=105.0,
        max_approach_angle_off_axis_deg=15.0,
    ),
    "hex_key_3.0mm": ToolGeometry(
        name="3.0mm hex key (L-shaped)",
        approach_diameter_mm=8.0,
        approach_length_mm=18.0,
        swing_radius_mm=100.0,
        swing_arc_deg=60.0,
        hand_clearance_diameter_mm=35.0,
        hand_clearance_length_mm=110.0,
        max_approach_angle_off_axis_deg=15.0,
    ),
    "hex_key_4.0mm": ToolGeometry(
        name="4.0mm hex key (L-shaped)",
        approach_diameter_mm=10.0,
        approach_length_mm=20.0,
        swing_radius_mm=115.0,
        swing_arc_deg=60.0,
        hand_clearance_diameter_mm=38.0,
        hand_clearance_length_mm=120.0,
        max_approach_angle_off_axis_deg=15.0,
    ),
    "socket_ratchet_M3": ToolGeometry(
        name="1/4-drive ratchet + 5.5mm socket (M3)",
        approach_diameter_mm=14.0,
        approach_length_mm=25.0,
        swing_radius_mm=130.0,
        swing_arc_deg=15.0,
        hand_clearance_diameter_mm=40.0,
        hand_clearance_length_mm=180.0,
        max_approach_angle_off_axis_deg=5.0,
    ),
    "socket_ratchet_M4": ToolGeometry(
        name="1/4-drive ratchet + 7mm socket (M4)",
        approach_diameter_mm=16.0,
        approach_length_mm=27.0,
        swing_radius_mm=130.0,
        swing_arc_deg=15.0,
        hand_clearance_diameter_mm=40.0,
        hand_clearance_length_mm=180.0,
        max_approach_angle_off_axis_deg=5.0,
    ),
    "socket_ratchet_M5": ToolGeometry(
        name="3/8-drive ratchet + 8mm socket (M5)",
        approach_diameter_mm=18.0,
        approach_length_mm=30.0,
        swing_radius_mm=170.0,
        swing_arc_deg=12.0,
        hand_clearance_diameter_mm=45.0,
        hand_clearance_length_mm=200.0,
        max_approach_angle_off_axis_deg=5.0,
    ),
    "screwdriver_phillips_2": ToolGeometry(
        name="#2 Phillips screwdriver",
        approach_diameter_mm=8.0,
        approach_length_mm=20.0,
        swing_radius_mm=0.0,
        swing_arc_deg=360.0,
        hand_clearance_diameter_mm=35.0,
        hand_clearance_length_mm=200.0,
        max_approach_angle_off_axis_deg=3.0,
    ),
    "nutrunner_M3": ToolGeometry(
        name="Pneumatic nutrunner, M3 socket",
        approach_diameter_mm=28.0,
        approach_length_mm=60.0,
        swing_radius_mm=0.0,
        swing_arc_deg=0.0,
        hand_clearance_diameter_mm=0.0,
        hand_clearance_length_mm=0.0,
        max_approach_angle_off_axis_deg=2.0,
    ),
    "nutrunner_M5": ToolGeometry(
        name="Pneumatic nutrunner, M5 socket",
        approach_diameter_mm=38.0,
        approach_length_mm=75.0,
        swing_radius_mm=0.0,
        swing_arc_deg=0.0,
        hand_clearance_diameter_mm=0.0,
        hand_clearance_length_mm=0.0,
        max_approach_angle_off_axis_deg=2.0,
    ),
}

# Fastener type → candidate tools (any one that clears = pass)
FASTENER_TOOL_MAP: dict[str, list[str]] = {
    "M2_socket_head":   ["hex_key_1.5mm"],
    "M2.5_socket_head": ["hex_key_2.0mm"],
    "M3_socket_head":   ["hex_key_2.5mm", "nutrunner_M3"],
    "M4_socket_head":   ["hex_key_3.0mm", "socket_ratchet_M4"],
    "M5_socket_head":   ["hex_key_4.0mm", "socket_ratchet_M5", "nutrunner_M5"],
    "M3_hex_head":      ["socket_ratchet_M3", "nutrunner_M3"],
    "M4_hex_head":      ["socket_ratchet_M4"],
    "M5_hex_head":      ["socket_ratchet_M5", "nutrunner_M5"],
    "M3_phillips":      ["screwdriver_phillips_2"],
    "M4_phillips":      ["screwdriver_phillips_2"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Fastener spec validator
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FastenerSpec:
    interface_id: str
    connection_description: str
    fastener_type: str           # key into FASTENER_TOOL_MAP
    quantity: int
    material: str
    torque_spec_nm: float
    thread_engagement_mm: float
    locking: str
    position_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    parent_components: list[str] | None = None

    def validate(self) -> list[str]:
        """Return list of validation errors (empty = valid)."""
        errors: list[str] = []
        if self.fastener_type not in FASTENER_TOOL_MAP:
            errors.append(
                f"{self.interface_id}: unknown fastener type '{self.fastener_type}'"
            )
        # Min 3× diameter thread engagement (d in mm from type name)
        try:
            d_str = self.fastener_type.split("_")[0].lstrip("M")
            d_mm = float(d_str)
            if self.thread_engagement_mm < 3 * d_mm:
                errors.append(
                    f"{self.interface_id}: thread engagement {self.thread_engagement_mm} mm "
                    f"< 3×d = {3*d_mm} mm (minimum for shear)"
                )
        except (ValueError, IndexError):
            pass
        return errors
