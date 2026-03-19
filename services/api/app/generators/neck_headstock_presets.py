"""
Neck & Headstock Presets — Tool configs, dimensions dataclass, factory presets.

Split from neck_headstock_config.py during decomposition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..schemas.instrument_project import InstrumentProjectData

from .cam_utils import _require_cam_ready, _require_spec


# =============================================================================
# TOOL CONFIGURATION
# =============================================================================

@dataclass
class NeckToolConfig:
    """Tool configuration for neck operations."""
    number: int
    name: str
    diameter_in: float
    rpm: int
    feed_ipm: float
    plunge_ipm: float
    stepdown_in: float

    @property
    def diameter_mm(self) -> float:
        return self.diameter_in * 25.4


# Neck-specific tool library (smaller tools for precision work)
NECK_TOOLS: Dict[int, NeckToolConfig] = {
    1: NeckToolConfig(1, "1/4\" Ball End", 0.250, 18000, 100, 20, 0.10),
    2: NeckToolConfig(2, "1/8\" Flat End", 0.125, 20000, 60, 15, 0.05),
    3: NeckToolConfig(3, "1/4\" Flat End", 0.250, 18000, 80, 18, 0.08),
    4: NeckToolConfig(4, "3/8\" Ball End", 0.375, 16000, 120, 25, 0.12),
    5: NeckToolConfig(5, "1/16\" Flat End", 0.0625, 24000, 30, 10, 0.02),
    10: NeckToolConfig(10, "11/32\" Drill", 0.344, 2000, 10, 5, 0.05),  # Tuner holes
}


# =============================================================================
# DIMENSIONS
# =============================================================================

@dataclass
class NeckDimensions:
    """Neck blank and finished dimensions."""
    # Blank dimensions
    blank_length_in: float = 26.0      # Includes headstock + heel
    blank_width_in: float = 3.5        # Wide enough for headstock
    blank_thickness_in: float = 1.0    # Before carving

    # Finished dimensions
    nut_width_in: float = 1.6875       # 1-11/16" standard
    heel_width_in: float = 2.25        # At body joint
    depth_at_1st_in: float = 0.82      # Neck depth at 1st fret
    depth_at_12th_in: float = 0.92     # Neck depth at 12th fret

    # Scale
    scale_length_in: float = 25.5

    # Headstock
    headstock_angle_deg: float = 14.0  # Gibson style
    headstock_thickness_in: float = 0.55
    headstock_length_in: float = 7.5

    # Truss rod
    truss_rod_width_in: float = 0.25
    truss_rod_depth_in: float = 0.375
    truss_rod_length_in: float = 18.0  # From nut

    @classmethod
    def from_project(
        cls,
        project: "InstrumentProjectData",
    ) -> "NeckDimensions":
        """
        Create NeckDimensions from InstrumentProjectData (GEN-3).

        Reads spec and neck_state from the project to build dimensions.
        Requires project to be CAM-ready (not DRAFT status).

        Args:
            project: InstrumentProjectData with spec and neck_state

        Returns:
            Configured NeckDimensions instance

        Raises:
            ValueError: If project is not CAM-ready or missing required data

        Example:
            >>> dims = NeckDimensions.from_project(project)
        """
        _require_cam_ready(project)
        _require_spec(project)

        # Convert mm to inches
        scale_length_in = project.spec.scale_length_mm / 25.4
        nut_width_in = project.spec.nut_width_mm / 25.4
        heel_width_in = project.spec.heel_width_mm / 25.4

        # Get headstock angle from neck_state if available
        headstock_angle = 0.0
        headstock_type = "flat"
        depth_at_1st = 0.82
        depth_at_12th = 0.92

        if project.neck_state:
            headstock_angle = project.neck_state.headstock_angle_deg
            headstock_type = project.neck_state.headstock_type
            if project.neck_state.thickness_at_1st_mm:
                depth_at_1st = project.neck_state.thickness_at_1st_mm / 25.4
            if project.neck_state.thickness_at_12th_mm:
                depth_at_12th = project.neck_state.thickness_at_12th_mm / 25.4

        return cls(
            scale_length_in=scale_length_in,
            nut_width_in=nut_width_in,
            heel_width_in=heel_width_in,
            depth_at_1st_in=depth_at_1st,
            depth_at_12th_in=depth_at_12th,
            headstock_angle_deg=headstock_angle,
        )


# =============================================================================
# PRESETS
# =============================================================================

NECK_PRESETS: Dict[str, NeckDimensions] = {
    "gibson_50s": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.86,
        depth_at_12th_in=0.96,
        scale_length_in=24.75,
        headstock_angle_deg=17.0,
    ),
    "gibson_60s": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.80,
        depth_at_12th_in=0.90,
        scale_length_in=24.75,
        headstock_angle_deg=17.0,
    ),
    "fender_vintage": NeckDimensions(
        nut_width_in=1.625,
        depth_at_1st_in=0.82,
        depth_at_12th_in=0.92,
        scale_length_in=25.5,
        headstock_angle_deg=0.0,  # Flat headstock
        headstock_length_in=7.0,
        headstock_thickness_in=0.55,
    ),
    "fender_modern": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.78,
        depth_at_12th_in=0.88,
        scale_length_in=25.5,
        headstock_angle_deg=0.0,
        headstock_length_in=7.0,
        headstock_thickness_in=0.55,
    ),
    "prs": NeckDimensions(
        nut_width_in=1.6875,
        depth_at_1st_in=0.83,
        depth_at_12th_in=0.90,
        scale_length_in=25.0,
        headstock_angle_deg=10.0,
    ),
    "classical": NeckDimensions(
        nut_width_in=2.0,
        depth_at_1st_in=0.85,
        depth_at_12th_in=0.95,
        scale_length_in=25.6,  # 650mm
        headstock_angle_deg=15.0,
        blank_width_in=4.0,  # Wider for slotted
    ),
    "strat_24fret": NeckDimensions(
        # 24-fret Stratocaster - extended fretboard, modern compound radius
        # Resolves GAP-02: No 24-fret Stratocaster preset
        nut_width_in=1.6875,       # 1-11/16" modern width
        depth_at_1st_in=0.78,      # Slim modern profile
        depth_at_12th_in=0.88,
        scale_length_in=25.5,      # Fender 648mm scale
        headstock_angle_deg=0.0,   # Flat Fender headstock
        headstock_length_in=7.0,
        headstock_thickness_in=0.55,
        blank_length_in=27.0,      # Longer blank for 24 frets
    ),
    "martin_om": NeckDimensions(
        # Martin OM (Orchestra Model) acoustic neck
        # Resolves OM-GAP-06: Martin headstock + neck preset
        nut_width_in=1.75,         # 44.5mm standard Martin width
        depth_at_1st_in=0.84,      # Medium C profile
        depth_at_12th_in=0.94,
        scale_length_in=25.4,      # 645mm Martin OM scale
        headstock_angle_deg=15.0,  # Martin slotted angle
        headstock_length_in=7.5,
        headstock_thickness_in=0.55,
        blank_width_in=4.0,        # Wider for slotted headstock
    ),
    "benedetto_archtop": NeckDimensions(
        # Benedetto archtop neck (17", La Venezia style)
        # Resolves BEN-GAP-06: Benedetto headstock + neck preset
        nut_width_in=1.6875,       # 1-11/16" jazz width
        depth_at_1st_in=0.85,      # Full C profile for jazz
        depth_at_12th_in=0.95,
        scale_length_in=25.0,      # 635mm Benedetto scale
        headstock_angle_deg=14.0,  # Archtop headstock angle
        headstock_length_in=6.9,
        headstock_thickness_in=0.58,
    ),
}
