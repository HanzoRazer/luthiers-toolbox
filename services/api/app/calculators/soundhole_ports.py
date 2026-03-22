"""
soundhole_ports.py — Side port / F-hole geometry and Helmholtz helpers
====================================================================

DECOMP-002 Phase 3: extracted from soundhole_calc.py.

Uses core physics from soundhole_physics (PortSpec, multi-port Helmholtz).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List

from .soundhole_physics import (
    K0,
    GAMMA,
    PLATE_MASS_FACTOR,
    PortSpec,
    compute_helmholtz_multiport,
)

# ── Side port position taxonomy ───────────────────────────────────────────────

SIDE_PORT_POSITIONS: Dict[str, Dict] = {
    "upper_treble": {
        "label": "Upper treble bout",
        "radiation": (
            "Directed toward player's right ear and slightly upward. "
            "Strong monitor effect — the most common position for performer comfort. "
            "Minimal change to audience-facing projection."
        ),
        "coupling": "low",  # low coupling to monopole mode
        "f_H_shift": "+3–6 Hz",
        "structural": (
            "Clear of main X-brace intersection. Min 40mm from neck block. "
            "Check for transverse brace ends."
        ),
    },
    "upper_bass": {
        "label": "Upper bass bout",
        "radiation": (
            "Directed toward player's left arm and toward ceiling. "
            "Useful for balanced monitoring in small rooms. "
            "Common on OM + side port builds."
        ),
        "coupling": "low",
        "f_H_shift": "+3–6 Hz",
        "structural": (
            "Clear of neck block. Min 40mm. May intersect with upper transverse brace end."
        ),
    },
    "lower_treble": {
        "label": "Lower treble bout",
        "radiation": (
            "Directed toward floor and slightly sideways. "
            "Strong coupling to lower bout volume — larger Helmholtz shift. "
            "Used when f_H tuning is the primary goal rather than monitor sound."
        ),
        "coupling": "high",
        "f_H_shift": "+8–15 Hz",
        "structural": "Min 40mm from tail block. Clear of lower X-brace leg.",
    },
    "lower_bass": {
        "label": "Lower bass bout",
        "radiation": (
            "Directed toward floor on the bass side. "
            "Maximum coupling to body volume — largest Helmholtz shift of any side position. "
            "Stoll Guitars and others use this to raise f_H without changing top geometry."
        ),
        "coupling": "high",
        "f_H_shift": "+8–15 Hz",
        "structural": "Min 40mm from tail block. Clear of lower X-brace leg (bass side).",
    },
    "waist": {
        "label": "Waist (narrowest point)",
        "radiation": (
            "Exits at 90° to body centerline. "
            "Unusual position — limited by narrow rim depth at waist. "
            "Low coupling to both upper and lower bout modes."
        ),
        "coupling": "minimal",
        "f_H_shift": "+1–4 Hz",
        "structural": (
            "Waist rim typically only 70–80mm deep — may limit port diameter to <25mm. "
            "Avoid binding ledge and kerfing thickness."
        ),
    },
    "symmetric_pair": {
        "label": "Symmetric pair (both upper bouts)",
        "radiation": (
            "Exits toward both player ears simultaneously. "
            "Stereo-like monitor experience — both ears receive direct sound. "
            "Total area doubles vs single port, so Helmholtz shift is larger."
        ),
        "coupling": "low",
        "f_H_shift": "+6–12 Hz (doubled area)",
        "structural": (
            "Two ports, each min 40mm from neck block, min 30mm separation from each other."
        ),
    },
}


SIDE_PORT_TYPES: Dict[str, Dict] = {
    "round": {
        "label": "Round",
        "description": (
            "Standard circular hole. Simplest to cut — forstner bit or hole saw. "
            "Perimeter correction is minimal (P/√A = 3.54 for circle)."
        ),
        "perim_factor": 1.0,  # multiplier on circular perimeter
    },
    "oval": {
        "label": "Oval",
        "description": (
            "Elliptical opening. Slightly higher perimeter than round for same area, "
            "raising L_eff by ~5%. Cut with router jig or file from round pilot hole."
        ),
        "perim_factor": 1.15,
    },
    "slot": {
        "label": "Slot / rectangular",
        "description": (
            "Row of slots or single rectangular slot. High perimeter-to-area ratio — "
            "L_eff is significantly longer than round, lowering f_H for same area. "
            "Common on ukuleles. Cut with router or oscillating tool."
        ),
        "perim_factor": 2.2,  # typical for slot aspect ratio 3:1
    },
    "chambered": {
        "label": "Chambered (tubed)",
        "description": (
            "Port opens into an internal routed channel before exiting the rim. "
            "The channel length adds directly to L_eff, allowing deliberate tuning "
            "of port resonance independent of visible hole size. "
            "Rare — found on some custom instruments."
        ),
        "perim_factor": 1.0,  # tube length handled separately via tube_length_mm
    },
}


@dataclass
class SidePortSpec:
    """
    Extended specification for a side-of-body port.

    Extends basic PortSpec with position, type, and structural context
    that affects radiation pattern and structural validity checks.

    Attributes:
        area_m2:          Opening area (m²)
        perim_m:          Perimeter of the opening (m)
        thickness_m:      Rim thickness at the port (m) — typically 0.0023m (2.3mm)
        position:         Where on the rim the port sits (see SIDE_PORT_POSITIONS)
        port_type:        Shape/construction type (see SIDE_PORT_TYPES)
        tube_length_mm:   Added internal channel length for chambered ports (mm)
        label:            Display name
    """

    area_m2: float
    perim_m: float
    thickness_m: float = 0.0023
    position: str = "upper_bass"  # key from SIDE_PORT_POSITIONS
    port_type: str = "round"  # key from SIDE_PORT_TYPES
    tube_length_mm: float = 0.0  # for chambered ports
    label: str = "Side port"

    @classmethod
    def from_circle_mm(
        cls,
        diameter_mm: float,
        position: str = "upper_bass",
        port_type: str = "round",
        rim_thickness_mm: float = 2.3,
        tube_length_mm: float = 0.0,
        label: str = "Side port",
    ) -> "SidePortSpec":
        r = (diameter_mm / 2) / 1000.0
        # Apply perimeter factor from port type
        pf = SIDE_PORT_TYPES.get(port_type, {}).get("perim_factor", 1.0)
        return cls(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r * pf,
            thickness_m=rim_thickness_mm / 1000.0,
            position=position,
            port_type=port_type,
            tube_length_mm=tube_length_mm,
            label=label,
        )

    def to_port_spec(self, k0: float = K0, gamma: float = GAMMA) -> PortSpec:
        """
        Convert to PortSpec for Helmholtz calculation.
        Tube length adds directly to effective neck length.
        """
        # Effective thickness includes any added tube length
        effective_thickness_m = self.thickness_m + (self.tube_length_mm / 1000.0)
        return PortSpec(
            area_m2=self.area_m2,
            perim_m=self.perim_m,
            location="side",
            thickness_m=effective_thickness_m,
            label=self.label,
        )

    @property
    def position_info(self) -> Dict:
        return SIDE_PORT_POSITIONS.get(self.position, SIDE_PORT_POSITIONS["upper_bass"])

    @property
    def type_info(self) -> Dict:
        return SIDE_PORT_TYPES.get(self.port_type, SIDE_PORT_TYPES["round"])

    @property
    def diameter_equiv_mm(self) -> float:
        return 2 * math.sqrt(self.area_m2 / math.pi) * 1000.0


@dataclass
class SidePortResult:
    """Analysis result for a side port."""

    port: SidePortSpec
    f_H_shift_hz: float  # Predicted Helmholtz shift from this port
    radiation_description: str
    structural_clearance: str
    coupling_level: str  # "low" | "high" | "minimal"
    f_H_shift_label: str
    warnings: List[str]


def analyze_side_port(
    port: SidePortSpec,
    body_volume_m3: float,
    main_ports: List[Any],
    rim_depth_at_position_mm: float = 90.0,
    k0: float = K0,
    gamma: float = GAMMA,
) -> SidePortResult:
    """
    Analyze a single side port — Helmholtz contribution, radiation, structural check.

    Args:
        port:                     The SidePortSpec to analyze
        body_volume_m3:           Guitar body volume
        main_ports:               Top/main ports (for baseline f_H comparison)
        rim_depth_at_position_mm: Rim depth where port sits (constrains max diameter)
        k0, gamma:                Helmholtz constants

    Returns:
        SidePortResult with radiation description and structural guidance
    """
    warnings: List[str] = []
    pos_info = port.position_info

    # Baseline f_H (without this side port)
    if main_ports:
        f_base, _ = compute_helmholtz_multiport(body_volume_m3, main_ports, k0, gamma)
    else:
        f_base = 0.0

    # f_H with this port added
    all_ports = list(main_ports) + [port.to_port_spec(k0, gamma)]
    f_with, _ = compute_helmholtz_multiport(body_volume_m3, all_ports, k0, gamma)
    shift = f_with - f_base

    # Structural checks
    diam_mm = port.diameter_equiv_mm
    if diam_mm > rim_depth_at_position_mm * 0.75:
        warnings.append(
            f"Port diameter {diam_mm:.0f}mm exceeds 75% of rim depth {rim_depth_at_position_mm:.0f}mm "
            f"at this position — risk of structural weakness in the rim."
        )

    if port.position == "waist" and diam_mm > 25:
        warnings.append(
            f"Waist rim is narrow. Port diameter {diam_mm:.0f}mm may be too large — "
            "waist depth is typically 70–80mm. Keep ports here ≤25mm diameter."
        )

    if port.tube_length_mm > 0:
        warnings.append(
            f"Chambered port: {port.tube_length_mm:.0f}mm tube adds to L_eff. "
            "Route channel before installing kerfing. Verify internal clearance."
        )

    return SidePortResult(
        port=port,
        f_H_shift_hz=round(shift, 1),
        radiation_description=pos_info["radiation"],
        structural_clearance=pos_info["structural"],
        coupling_level=pos_info["coupling"],
        f_H_shift_label=pos_info["f_H_shift"],
        warnings=warnings,
    )


# ── Inverse solver ────────────────────────────────────────────────────────────


def solve_for_diameter_mm(
    target_f_hz: float,
    volume_m3: float,
    thickness_m: float = 0.0025,
    k0: float = K0,
    gamma: float = GAMMA,
    plate_mass_factor: float = PLATE_MASS_FACTOR,
    min_mm: float = 40.0,
    max_mm: float = 150.0,
) -> Dict:
    """
    Inverse Helmholtz solver — find the diameter needed to hit a target f_H.

    Since f ∝ √A and A = πr², and f is linear in √A, the analytical inverse is:

        A_needed = (f_target/PMF × 2π/c)² × V × L_eff

    But L_eff itself depends on r (via k × r_eq), making this implicit.
    We use a simple bisection search (converges in <20 iterations for ±0.01Hz).

    Args:
        target_f_hz:       Target assembled-instrument air resonance (Hz)
        volume_m3:         Body internal volume (m³)
        thickness_m:       Top plate thickness at hole (m)
        k0, gamma:         End-correction constants
        plate_mass_factor: Coupling correction (default 0.92)
        min_mm, max_mm:    Search bounds for diameter (mm)

    Returns:
        Dict with diameter_mm, achieved_f_hz, area_cm2, warnings
    """
    warnings: List[str] = []

    def predict(diam_mm: float) -> float:
        r = (diam_mm / 2) / 1000.0
        p = PortSpec(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r,
            location="top",
            thickness_m=thickness_m,
        )
        f, _ = compute_helmholtz_multiport(volume_m3, [p], k0, gamma, plate_mass_factor)
        return f

    # Bisection search
    lo, hi = min_mm, max_mm
    for _ in range(60):
        mid = (lo + hi) / 2.0
        f_mid = predict(mid)
        if f_mid < target_f_hz:
            lo = mid
        else:
            hi = mid
        if (hi - lo) < 0.01:
            break

    result_diam = (lo + hi) / 2.0
    achieved_f = predict(result_diam)

    if result_diam <= min_mm + 0.1:
        warnings.append(
            f"Target {target_f_hz:.0f} Hz requires diameter below {min_mm:.0f}mm — "
            "consider smaller body volume or thicker top."
        )
    elif result_diam >= max_mm - 0.1:
        warnings.append(
            f"Target {target_f_hz:.0f} Hz requires diameter above {max_mm:.0f}mm — "
            "consider larger body volume or thinner top."
        )

    r_mm = result_diam / 2.0
    return {
        "diameter_mm": round(result_diam, 1),
        "radius_mm": round(r_mm, 1),
        "achieved_f_hz": round(achieved_f, 1),
        "error_hz": round(achieved_f - target_f_hz, 2),
        "area_cm2": round(math.pi * (r_mm / 10.0) ** 2, 2),
        "warnings": warnings,
    }


def solve_for_diameter_with_side_port_mm(
    target_f_hz: float,
    volume_m3: float,
    side_port_diameter_mm: float,
    thickness_m: float = 0.0025,
    rim_thickness_m: float = 0.0023,
    k0: float = K0,
    gamma: float = GAMMA,
) -> Dict:
    """
    Inverse solver when a side port is already planned.
    Returns the main hole diameter needed to hit target f_H given the side port.
    """
    side_r = (side_port_diameter_mm / 2) / 1000.0
    side_port = PortSpec(
        area_m2=math.pi * side_r * side_r,
        perim_m=2 * math.pi * side_r,
        location="side",
        thickness_m=rim_thickness_m,
    )

    def predict_total(main_diam_mm: float) -> float:
        r = (main_diam_mm / 2) / 1000.0
        main_port = PortSpec(
            area_m2=math.pi * r * r,
            perim_m=2 * math.pi * r,
            location="top",
            thickness_m=thickness_m,
        )
        f, _ = compute_helmholtz_multiport(volume_m3, [main_port, side_port], k0, gamma)
        return f

    lo, hi = 40.0, 140.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if predict_total(mid) < target_f_hz:
            lo = mid
        else:
            hi = mid
        if (hi - lo) < 0.01:
            break

    result_diam = (lo + hi) / 2.0
    return {
        "main_diameter_mm": round(result_diam, 1),
        "side_port_diameter_mm": round(side_port_diameter_mm, 1),
        "achieved_f_hz": round(predict_total(result_diam), 1),
    }
