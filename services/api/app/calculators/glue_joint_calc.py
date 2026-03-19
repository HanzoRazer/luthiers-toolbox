"""
Glue joint geometry calculator (CONSTRUCTION-005).

Acoustic guitar construction: neck joint, top/back plate joints,
bridge plate, brace gluing surfaces.

Glue surface requirements:
  hide_glue: min 500 mm² per joint, clamping 50–100 psi, open 3–5 min
  pva:       min 400 mm², clamping 20–50 psi, open 5–10 min
  epoxy:     min 300 mm², no clamping, open 5–60 min
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

# Joint type literals
JOINT_DOVETAIL = "dovetail"
JOINT_BOLT_ON = "bolt_on"
JOINT_MORTISE_TENON = "mortise_tenon"
JOINT_BUTT = "butt_joint"
JOINT_LAP = "lap_joint"

# Glue type literals
GLUE_HIDE = "hide_glue"
GLUE_PVA = "pva"
GLUE_EPOXY = "epoxy"

# Min glue surface (mm²) per glue type
MIN_SURFACE_MM2 = {
    GLUE_HIDE: 500.0,
    GLUE_PVA: 400.0,
    GLUE_EPOXY: 300.0,
}

# Clamping pressure (psi) — (min, max) for gate
CLAMPING_PSI = {
    GLUE_HIDE: (50.0, 100.0),
    GLUE_PVA: (20.0, 50.0),
    GLUE_EPOXY: (0.0, 0.0),  # not required
}

# Open time (minutes) and cure time (hours) — nominal
OPEN_TIME_MIN = {
    GLUE_HIDE: (3.0, 5.0),
    GLUE_PVA: (5.0, 10.0),
    GLUE_EPOXY: (5.0, 60.0),
}
CURE_TIME_HOURS = {
    GLUE_HIDE: 24.0,
    GLUE_PVA: 12.0,
    GLUE_EPOXY: 24.0,
}

# Neck joint type → nominal glue surface (mm²); bolt_on = 0
NECK_JOINT_SURFACE_MM2 = {
    JOINT_DOVETAIL: 800.0,
    JOINT_BOLT_ON: 0.0,
    JOINT_MORTISE_TENON: 600.0,
}


@dataclass
class GlueJointSpec:
    """Specification for a glue joint with surface, pressure, and timing."""
    joint_type: str  # dovetail | bolt_on | mortise_tenon | butt_joint | lap_joint
    glue_surface_mm2: float
    clamping_pressure_psi: float
    open_time_minutes: float
    cure_time_hours: float
    glue_type: str  # hide_glue | pva | epoxy
    gate: str  # GREEN | YELLOW | RED
    notes: List[str]


def _gate_for_surface(surface_mm2: float, glue_type: str) -> Tuple[str, List[str]]:
    """Return gate and notes for glue surface vs minimum."""
    notes: List[str] = []
    min_surf = MIN_SURFACE_MM2.get(glue_type, 400.0)
    if surface_mm2 <= 0:
        return "RED", ["No glue surface (e.g. bolt-on)."]
    if surface_mm2 >= min_surf:
        gate = "GREEN"
        notes.append(f"Glue surface {surface_mm2:.0f} mm² meets minimum {min_surf:.0f} mm² for {glue_type}.")
    elif surface_mm2 >= min_surf * 0.8:
        gate = "YELLOW"
        notes.append(f"Glue surface {surface_mm2:.0f} mm² is slightly below recommended {min_surf:.0f} mm².")
    else:
        gate = "RED"
        notes.append(f"Glue surface {surface_mm2:.0f} mm² is below minimum {min_surf:.0f} mm² for {glue_type}.")
    return gate, notes


def compute_neck_joint(
    joint_type: str,
    neck_heel_width_mm: float,
    neck_heel_length_mm: float,
    glue_type: str = "hide_glue",
) -> GlueJointSpec:
    """
    Compute glue joint spec for a neck joint.

    Dovetail: traditional ~800 mm² nominal; can estimate from heel width × length × factor.
    Mortise-tenon: ~600 mm² nominal.
    Bolt-on: no glue surface (mechanical); gate reflects that.
    """
    joint_type = joint_type.strip().lower().replace(" ", "_")
    glue_type = glue_type.strip().lower().replace(" ", "_")
    if glue_type not in (GLUE_HIDE, GLUE_PVA, GLUE_EPOXY):
        glue_type = GLUE_HIDE

    if joint_type == JOINT_BOLT_ON:
        surface_mm2 = 0.0
        clamping_psi = 0.0
        open_min = 0.0
        cure_hr = 0.0
        gate = "GREEN"
        notes = ["Bolt-on: no glue; mechanical attachment only."]
    else:
        notes = []
        # Estimate glue surface from heel dimensions
        if joint_type == JOINT_DOVETAIL:
            # Dovetail: both cheeks + end grain; approximate 2 × (width × depth) + end
            # depth ~ 30–40 mm typical; use 0.6 factor for effective glue area
            effective_depth_mm = min(neck_heel_length_mm * 0.7, 40.0)
            surface_mm2 = 2.0 * (neck_heel_width_mm * effective_depth_mm) * 0.6
            surface_mm2 = max(surface_mm2, NECK_JOINT_SURFACE_MM2[JOINT_DOVETAIL] * 0.9)
            notes.append("Dovetail: glue surface estimated from heel width × depth (both cheeks).")
        elif joint_type == JOINT_MORTISE_TENON:
            # Mortise-tenon: tenon faces; approximate width × length × 0.8
            surface_mm2 = neck_heel_width_mm * neck_heel_length_mm * 0.8
            surface_mm2 = max(surface_mm2, NECK_JOINT_SURFACE_MM2[JOINT_MORTISE_TENON] * 0.9)
            notes.append("Mortise-tenon: glue surface estimated from tenon footprint.")
        else:
            # Generic: width × length as proxy
            surface_mm2 = neck_heel_width_mm * neck_heel_length_mm * 0.5
            notes.append(f"Joint type {joint_type}: glue surface estimated from heel dimensions.")

        gate, gate_notes = _gate_for_surface(surface_mm2, glue_type)
        notes.extend(gate_notes)
        lo, hi = CLAMPING_PSI[glue_type]
        clamping_psi = (lo + hi) / 2 if (lo + hi) > 0 else 0.0
        open_lo, open_hi = OPEN_TIME_MIN[glue_type]
        open_min = (open_lo + open_hi) / 2
        cure_hr = CURE_TIME_HOURS[glue_type]

    return GlueJointSpec(
        joint_type=joint_type,
        glue_surface_mm2=round(surface_mm2, 1),
        clamping_pressure_psi=round(clamping_psi, 1),
        open_time_minutes=round(open_min, 1),
        cure_time_hours=round(cure_hr, 1),
        glue_type=glue_type,
        gate=gate,
        notes=notes,
    )


def compute_plate_joint(
    joint_type: str,
    length_mm: float,
    width_mm: float,
    glue_type: str = "hide_glue",
) -> GlueJointSpec:
    """
    Compute glue joint spec for plate joints (e.g. brace to top/back,
    plate to rim, bridge plate to top).

    joint_type: "butt_joint" | "lap_joint"
    length_mm: joint length (along brace or seam)
    width_mm: contact width (brace width or overlap)
    """
    joint_type = joint_type.strip().lower().replace(" ", "_")
    glue_type = glue_type.strip().lower().replace(" ", "_")
    if glue_type not in (GLUE_HIDE, GLUE_PVA, GLUE_EPOXY):
        glue_type = GLUE_HIDE

    if joint_type == JOINT_LAP:
        surface_mm2 = length_mm * width_mm
        notes = [f"Lap joint: glue area {length_mm:.0f} × {width_mm:.0f} mm."]
    else:
        # Butt joint: contact is typically length × width (edge to edge)
        surface_mm2 = length_mm * width_mm
        notes = [f"Butt joint: glue area {length_mm:.0f} × {width_mm:.0f} mm."]

    gate, gate_notes = _gate_for_surface(surface_mm2, glue_type)
    notes.extend(gate_notes)
    lo, hi = CLAMPING_PSI[glue_type]
    clamping_psi = (lo + hi) / 2 if (lo + hi) > 0 else 0.0
    open_lo, open_hi = OPEN_TIME_MIN[glue_type]
    open_min = (open_lo + open_hi) / 2
    cure_hr = CURE_TIME_HOURS[glue_type]

    return GlueJointSpec(
        joint_type=joint_type,
        glue_surface_mm2=round(surface_mm2, 1),
        clamping_pressure_psi=round(clamping_psi, 1),
        open_time_minutes=round(open_min, 1),
        cure_time_hours=round(cure_hr, 1),
        glue_type=glue_type,
        gate=gate,
        notes=notes,
    )
