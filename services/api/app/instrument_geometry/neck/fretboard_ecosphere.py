"""
Fretboard Ecosphere — Canonical Pydantic-Validated Document for Fret Geometry

Sprint FRET-A Phase 1: Core schema definition

This module defines the canonical data structure for all fret geometry in the
Luthiers Toolbox. It replaces ad-hoc dataclasses with a validated, serializable
Pydantic model that serves as the single source of truth for:

- Standard and multiscale (fanned fret) configurations
- Perpendicular distance calculation (FretFind2D parity)
- Per-string scale lengths and intonation offsets
- Compound radius profiles
- Export to DXF, SVG, Scala files

Architecture position:
    Input params → FretboardEcosphere.compute() → Validated document
                                                      ↓
                                        [export_dxf(), export_svg(), export_scala()]

The FretboardEcosphere is immutable after computation. To modify parameters,
create a new instance via compute().
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pow as math_pow, atan2, pi
from typing import List, Optional, Dict, Any, Tuple

from pydantic import BaseModel, Field, field_validator, model_validator

from app.calculators.alternative_temperaments import (
    TemperamentSystem,
    resolve_temperament_ratios,
    compute_fret_positions_from_ratios_mm,
)


class ScaleType(str, Enum):
    """Type of scale length configuration."""
    STANDARD = "standard"
    MULTISCALE = "multiscale"


class TemperamentType(str, Enum):
    """Tuning temperament for fret calculation."""
    EQUAL_12 = "equal_12"
    EQUAL_19 = "equal_19"
    EQUAL_24 = "equal_24"
    EQUAL_31 = "equal_31"
    PYTHAGOREAN = "pythagorean"
    JUST_MAJOR = "just_major"
    MEANTONE_QUARTER = "meantone_quarter"


class FretPoint(BaseModel):
    """A single computed point on a fret line.

    For standard fretting, all strings share the same x position.
    For multiscale, x varies per string.
    """
    fret_number: int = Field(..., ge=0, description="Fret number (0 = nut)")
    string_index: int = Field(..., ge=0, description="String index (0 = bass)")
    x_mm: float = Field(..., description="Distance from nut along centerline")
    y_mm: float = Field(..., description="Position across fretboard (- = bass, + = treble)")

    class Config:
        frozen = True


class FretLine(BaseModel):
    """A complete fret line spanning all strings.

    For standard fretting: all points have same x_mm, different y_mm.
    For multiscale: points have varying x_mm (angled fret).
    """
    fret_number: int = Field(..., ge=0, description="Fret number (0 = nut)")
    points: List[FretPoint] = Field(default_factory=list)
    angle_rad: float = Field(0.0, description="Angle from perpendicular (radians)")
    is_perpendicular: bool = Field(True, description="True if fret is perpendicular to centerline")

    @property
    def bass_point(self) -> Optional[FretPoint]:
        """First point (bass side)."""
        return self.points[0] if self.points else None

    @property
    def treble_point(self) -> Optional[FretPoint]:
        """Last point (treble side)."""
        return self.points[-1] if self.points else None

    @property
    def center_x_mm(self) -> float:
        """Average x position (center of fret)."""
        if not self.points:
            return 0.0
        return sum(p.x_mm for p in self.points) / len(self.points)

    class Config:
        frozen = True


class StringPath(BaseModel):
    """Path of a single string from nut to bridge.

    Includes all intersection points with frets.
    """
    string_index: int = Field(..., ge=0)
    scale_length_mm: float = Field(..., gt=0)
    nut_position: Tuple[float, float] = Field(..., description="(x, y) at nut")
    bridge_position: Tuple[float, float] = Field(..., description="(x, y) at bridge")
    fret_intersections: List[Tuple[float, float]] = Field(
        default_factory=list,
        description="(x, y) points where string crosses each fret"
    )
    intonation_offset_mm: float = Field(0.0, description="Saddle compensation offset")

    @property
    def compensated_length_mm(self) -> float:
        """Effective scale length with intonation compensation."""
        return self.scale_length_mm + self.intonation_offset_mm

    class Config:
        frozen = True


class RadiusSpec(BaseModel):
    """Fretboard radius specification.

    Supports:
    - Single radius (nut_radius_mm == heel_radius_mm or heel is None)
    - Compound radius (linear interpolation from nut to heel)
    """
    nut_radius_mm: Optional[float] = Field(None, gt=0, description="Radius at nut (None = flat)")
    heel_radius_mm: Optional[float] = Field(None, gt=0, description="Radius at heel (None = same as nut)")

    @property
    def is_compound(self) -> bool:
        """True if radius varies along fretboard."""
        if self.nut_radius_mm is None:
            return False
        if self.heel_radius_mm is None:
            return False
        return abs(self.heel_radius_mm - self.nut_radius_mm) > 0.01

    @property
    def is_flat(self) -> bool:
        """True if fretboard has no radius (flat)."""
        return self.nut_radius_mm is None

    def radius_at_position(self, position_ratio: float) -> Optional[float]:
        """Get radius at a position (0.0 = nut, 1.0 = heel)."""
        if self.is_flat:
            return None
        if not self.is_compound:
            return self.nut_radius_mm
        t = max(0.0, min(1.0, position_ratio))
        return self.nut_radius_mm + (self.heel_radius_mm - self.nut_radius_mm) * t

    class Config:
        frozen = True


class FretboardInput(BaseModel):
    """Input parameters for fretboard geometry computation.

    This is the user-facing input model. Validation ensures parameters
    are physically plausible before computation.
    """
    # Scale configuration
    scale_type: ScaleType = Field(ScaleType.STANDARD)
    scale_length_mm: float = Field(648.0, gt=0, le=2000, description="Primary scale length (or treble for multiscale)")
    bass_scale_length_mm: Optional[float] = Field(None, gt=0, le=2000, description="Bass scale length (multiscale only)")

    # String configuration
    string_count: int = Field(6, ge=1, le=18)

    # Fret configuration
    fret_count: int = Field(22, ge=1, le=36)
    perpendicular_fret: int = Field(0, ge=0, description="Fret that is perpendicular (0 = nut, multiscale only)")
    temperament: TemperamentType = Field(TemperamentType.EQUAL_12)

    # Width configuration
    nut_width_mm: float = Field(42.0, gt=0, le=100)
    heel_width_mm: Optional[float] = Field(None, gt=0, le=150, description="Width at last fret (None = compute from taper)")
    edge_offset_mm: float = Field(3.0, ge=0, le=10, description="String setback from edge")

    # Radius configuration
    radius: RadiusSpec = Field(default_factory=lambda: RadiusSpec(nut_radius_mm=241.3))

    # Extension
    extension_mm: float = Field(0.0, ge=0, le=50, description="Length past last fret")

    # Intonation
    intonation_offsets_mm: Dict[int, float] = Field(
        default_factory=dict,
        description="Per-string saddle compensation {string_index: offset_mm}"
    )

    @field_validator('perpendicular_fret')
    @classmethod
    def validate_perpendicular_fret(cls, v: int, info) -> int:
        """Perpendicular fret must be within fret count."""
        fret_count = info.data.get('fret_count', 22)
        if v > fret_count:
            raise ValueError(f"perpendicular_fret ({v}) cannot exceed fret_count ({fret_count})")
        return v

    @model_validator(mode='after')
    def validate_multiscale(self) -> 'FretboardInput':
        """Validate multiscale configuration."""
        if self.scale_type == ScaleType.MULTISCALE:
            if self.bass_scale_length_mm is None:
                raise ValueError("bass_scale_length_mm required for multiscale")
            if self.bass_scale_length_mm < self.scale_length_mm:
                raise ValueError("bass_scale_length_mm should be >= treble scale_length_mm (convention)")
        return self

    class Config:
        frozen = True


class FretboardEcosphere(BaseModel):
    """Canonical fretboard geometry document.

    This is the computed, validated output. It contains all geometry data
    needed for visualization, export, and CAM operations.

    Create via FretboardEcosphere.compute(input) — do not construct directly.
    """
    # Input echo (for traceability)
    input_params: FretboardInput

    # Computed geometry
    fret_lines: List[FretLine] = Field(default_factory=list)
    string_paths: List[StringPath] = Field(default_factory=list)

    # Outline
    outline_points: List[Tuple[float, float]] = Field(
        default_factory=list,
        description="(x, y) points forming fretboard outline"
    )

    # Summary metrics
    total_length_mm: float = Field(0.0, description="Nut to end of extension")
    max_width_mm: float = Field(0.0, description="Width at widest point (heel)")
    max_fret_angle_deg: float = Field(0.0, description="Maximum fret angle (multiscale)")

    # Metadata
    version: str = Field("1.0.0", description="Schema version")

    class Config:
        frozen = True

    @classmethod
    def compute(cls, params: FretboardInput) -> 'FretboardEcosphere':
        """Compute fretboard geometry from input parameters.

        This is the primary factory method. All geometry is computed here
        and the resulting FretboardEcosphere is immutable.

        Args:
            params: Validated input parameters

        Returns:
            Fully computed FretboardEcosphere document
        """
        # Determine heel width
        heel_width = params.heel_width_mm
        if heel_width is None:
            # Default taper: ~14mm wider at heel for 22-fret standard scale
            heel_width = params.nut_width_mm + 14.0

        # Compute fret positions
        if params.scale_type == ScaleType.STANDARD:
            fret_lines = cls._compute_standard_frets(
                scale_length_mm=params.scale_length_mm,
                fret_count=params.fret_count,
                string_count=params.string_count,
                nut_width_mm=params.nut_width_mm,
                heel_width_mm=heel_width,
                temperament=params.temperament,
            )
        else:
            fret_lines = cls._compute_multiscale_frets(
                treble_scale_mm=params.scale_length_mm,
                bass_scale_mm=params.bass_scale_length_mm,
                fret_count=params.fret_count,
                string_count=params.string_count,
                nut_width_mm=params.nut_width_mm,
                heel_width_mm=heel_width,
                perpendicular_fret=params.perpendicular_fret,
                temperament=params.temperament,
            )

        # Compute string paths
        string_paths = cls._compute_string_paths(
            fret_lines=fret_lines,
            params=params,
            heel_width_mm=heel_width,
        )

        # Compute outline
        last_fret_x = fret_lines[-1].center_x_mm if fret_lines else 0.0
        total_length = last_fret_x + params.extension_mm

        half_nut = params.nut_width_mm / 2.0
        half_heel = heel_width / 2.0

        outline = [
            (0.0, -half_nut),           # Nut bass
            (total_length, -half_heel), # Heel bass
            (total_length, half_heel),  # Heel treble
            (0.0, half_nut),            # Nut treble
        ]

        # Compute max fret angle
        max_angle = 0.0
        for fl in fret_lines:
            if abs(fl.angle_rad) > abs(max_angle):
                max_angle = fl.angle_rad

        return cls(
            input_params=params,
            fret_lines=fret_lines,
            string_paths=string_paths,
            outline_points=outline,
            total_length_mm=total_length,
            max_width_mm=heel_width,
            max_fret_angle_deg=abs(max_angle) * 180.0 / pi,
        )

    @staticmethod
    def _temperament_type_to_system(temperament: TemperamentType) -> TemperamentSystem:
        """Map schema TemperamentType to kernel TemperamentSystem."""
        mapping = {
            TemperamentType.EQUAL_12: TemperamentSystem.EQUAL_12TET,
            TemperamentType.EQUAL_19: TemperamentSystem.EQUAL_19TET,
            TemperamentType.EQUAL_24: TemperamentSystem.EQUAL_24TET,
            TemperamentType.EQUAL_31: TemperamentSystem.EQUAL_31TET,
            TemperamentType.PYTHAGOREAN: TemperamentSystem.PYTHAGOREAN,
            TemperamentType.JUST_MAJOR: TemperamentSystem.JUST_MAJOR,
            TemperamentType.MEANTONE_QUARTER: TemperamentSystem.MEANTONE_QUARTER,
        }
        return mapping.get(temperament, TemperamentSystem.EQUAL_12TET)

    @classmethod
    def _compute_fret_positions_for_temperament(
        cls,
        scale_length_mm: float,
        fret_count: int,
        temperament: TemperamentType,
    ) -> List[float]:
        """Compute all fret positions using the kernel (delegated math).

        Returns positions for frets 1 through fret_count (0-indexed list).
        Fret 0 (nut) is always at position 0.0 and is not included.
        """
        system = cls._temperament_type_to_system(temperament)
        ratios = resolve_temperament_ratios(system, fret_count)
        return compute_fret_positions_from_ratios_mm(scale_length_mm, ratios)

    @staticmethod
    def _fret_position_12tet(scale_length_mm: float, fret_number: int) -> float:
        """Calculate fret position for 12-TET (legacy, kept for reference)."""
        if fret_number == 0:
            return 0.0
        return scale_length_mm * (1.0 - math_pow(2.0, -fret_number / 12.0))

    @classmethod
    def _compute_standard_frets(
        cls,
        scale_length_mm: float,
        fret_count: int,
        string_count: int,
        nut_width_mm: float,
        heel_width_mm: float,
        temperament: TemperamentType,
    ) -> List[FretLine]:
        """Compute fret lines for standard (non-multiscale) fretting.

        Delegates to kernel for temperament-aware fret position calculation.
        """
        fret_lines: List[FretLine] = []

        # Get all fret positions from kernel (frets 1 through fret_count)
        fret_positions = cls._compute_fret_positions_for_temperament(
            scale_length_mm, fret_count, temperament
        )
        # Prepend fret 0 (nut) at position 0.0
        all_positions = [0.0] + fret_positions
        last_fret_x = all_positions[-1] if all_positions else 0.0

        # Include fret 0 (nut)
        for fret_num in range(fret_count + 1):
            x_pos = all_positions[fret_num]

            # Calculate width at this fret position
            if last_fret_x > 0:
                t = x_pos / last_fret_x
            else:
                t = 0.0

            width_at_fret = nut_width_mm + (heel_width_mm - nut_width_mm) * t
            half_width = width_at_fret / 2.0

            # Create points for each string
            points: List[FretPoint] = []
            for string_idx in range(string_count):
                if string_count > 1:
                    y_pos = -half_width + (width_at_fret * string_idx / (string_count - 1))
                else:
                    y_pos = 0.0

                points.append(FretPoint(
                    fret_number=fret_num,
                    string_index=string_idx,
                    x_mm=x_pos,
                    y_mm=y_pos,
                ))

            fret_lines.append(FretLine(
                fret_number=fret_num,
                points=points,
                angle_rad=0.0,
                is_perpendicular=True,
            ))

        return fret_lines

    @classmethod
    def _compute_multiscale_frets(
        cls,
        treble_scale_mm: float,
        bass_scale_mm: float,
        fret_count: int,
        string_count: int,
        nut_width_mm: float,
        heel_width_mm: float,
        perpendicular_fret: int,
        temperament: TemperamentType,
    ) -> List[FretLine]:
        """Compute fret lines for multiscale (fanned fret) configuration.

        Delegates to kernel for temperament-aware fret position calculation.
        """
        fret_lines: List[FretLine] = []

        # Get all fret positions from kernel for both scales
        treble_positions = cls._compute_fret_positions_for_temperament(
            treble_scale_mm, fret_count, temperament
        )
        bass_positions = cls._compute_fret_positions_for_temperament(
            bass_scale_mm, fret_count, temperament
        )
        # Prepend fret 0 (nut) at position 0.0
        treble_all = [0.0] + treble_positions
        bass_all = [0.0] + bass_positions

        # Calculate where perpendicular fret should intersect
        perp_treble = treble_all[perpendicular_fret] if perpendicular_fret <= fret_count else treble_all[-1]
        perp_bass = bass_all[perpendicular_fret] if perpendicular_fret <= fret_count else bass_all[-1]
        perp_center = (perp_treble + perp_bass) / 2.0

        # Offset to make perpendicular fret straight
        treble_offset = perp_center - perp_treble
        bass_offset = perp_center - perp_bass

        # Calculate last fret average for taper reference
        last_fret_avg = (treble_all[-1] + bass_all[-1]) / 2.0 + (treble_offset + bass_offset) / 2.0

        for fret_num in range(fret_count + 1):
            treble_x = treble_all[fret_num] + treble_offset
            bass_x = bass_all[fret_num] + bass_offset

            # Average for taper calculation
            avg_x = (treble_x + bass_x) / 2.0

            t = avg_x / last_fret_avg if last_fret_avg > 0 else 0.0
            width_at_fret = nut_width_mm + (heel_width_mm - nut_width_mm) * t
            half_width = width_at_fret / 2.0

            # Calculate fret angle
            dx = treble_x - bass_x
            dy = width_at_fret
            angle_rad = atan2(dx, dy) if dy > 0 else 0.0
            is_perp = fret_num == perpendicular_fret or abs(dx) < 0.001

            # Create points for each string (interpolate x position)
            points: List[FretPoint] = []
            for string_idx in range(string_count):
                if string_count > 1:
                    s = string_idx / (string_count - 1)
                    x_pos = bass_x + (treble_x - bass_x) * s
                    y_pos = -half_width + (width_at_fret * s)
                else:
                    x_pos = (bass_x + treble_x) / 2.0
                    y_pos = 0.0

                points.append(FretPoint(
                    fret_number=fret_num,
                    string_index=string_idx,
                    x_mm=x_pos,
                    y_mm=y_pos,
                ))

            fret_lines.append(FretLine(
                fret_number=fret_num,
                points=points,
                angle_rad=angle_rad,
                is_perpendicular=is_perp,
            ))

        return fret_lines

    @classmethod
    def _compute_string_paths(
        cls,
        fret_lines: List[FretLine],
        params: FretboardInput,
        heel_width_mm: float,
    ) -> List[StringPath]:
        """Compute string paths from nut to bridge."""
        string_paths: List[StringPath] = []

        half_nut = params.nut_width_mm / 2.0
        half_heel = heel_width_mm / 2.0

        for string_idx in range(params.string_count):
            if params.string_count > 1:
                s = string_idx / (params.string_count - 1)
            else:
                s = 0.5

            # String spacing (with edge offset)
            usable_nut = params.nut_width_mm - 2 * params.edge_offset_mm
            usable_heel = heel_width_mm - 2 * params.edge_offset_mm

            y_nut = -half_nut + params.edge_offset_mm + usable_nut * s
            y_bridge = -half_heel + params.edge_offset_mm + usable_heel * s

            # Determine scale length for this string
            if params.scale_type == ScaleType.MULTISCALE:
                scale = params.bass_scale_length_mm + (
                    params.scale_length_mm - params.bass_scale_length_mm
                ) * s
            else:
                scale = params.scale_length_mm

            # Get intonation offset
            offset = params.intonation_offsets_mm.get(string_idx, 0.0)

            # Collect fret intersections
            intersections: List[Tuple[float, float]] = []
            for fl in fret_lines:
                if string_idx < len(fl.points):
                    pt = fl.points[string_idx]
                    intersections.append((pt.x_mm, pt.y_mm))

            string_paths.append(StringPath(
                string_index=string_idx,
                scale_length_mm=scale,
                nut_position=(0.0, y_nut),
                bridge_position=(scale + offset, y_bridge),
                fret_intersections=intersections,
                intonation_offset_mm=offset,
            ))

        return string_paths

    def get_fret_line(self, fret_number: int) -> Optional[FretLine]:
        """Get a specific fret line by number."""
        for fl in self.fret_lines:
            if fl.fret_number == fret_number:
                return fl
        return None

    def get_string_path(self, string_index: int) -> Optional[StringPath]:
        """Get a specific string path by index."""
        for sp in self.string_paths:
            if sp.string_index == string_index:
                return sp
        return None

    def perpendicular_distance(self, fret_number: int, string_index: int) -> float:
        """Calculate perpendicular distance from nut to fret for a specific string.

        This is the FretFind2D-compatible measurement: the shortest distance
        from the nut line to the fret point, perpendicular to the nut.

        For standard fretting, this equals the fret x position.
        For multiscale, this accounts for the angled fret.
        """
        fl = self.get_fret_line(fret_number)
        if fl is None or string_index >= len(fl.points):
            return 0.0

        pt = fl.points[string_index]
        # For perpendicular distance, we project onto the centerline (x-axis)
        # The nut is at x=0, so perpendicular distance is just x_mm
        return pt.x_mm

    def to_scala_intervals(self) -> List[float]:
        """Export fret ratios as Scala-compatible interval list.

        Returns cents values from nut to each fret, compatible with
        Scala .scl file format.
        """
        if not self.fret_lines:
            return []

        # Use centerline (average) positions
        intervals: List[float] = []
        scale = self.input_params.scale_length_mm

        for fl in self.fret_lines[1:]:  # Skip nut (fret 0)
            x = fl.center_x_mm
            if x <= 0 or x >= scale:
                continue
            # Ratio of remaining string length to original
            ratio = (scale - x) / scale
            # Convert to cents: 1200 * log2(original/remaining)
            if ratio > 0:
                import math
                cents = 1200.0 * math.log2(1.0 / ratio)
                intervals.append(round(cents, 3))

        return intervals


def build_ecosphere(req: FretboardInput) -> FretboardEcosphere:
    """Build the canonical fretboard ecosphere from validated input.

    Thin wrapper around FretboardEcosphere.compute() that exists to give
    consumers (router, CLI, tests, future Fusion add-in) a stable public
    function to depend on rather than the classmethod's internal name.

    Raises:
        ValueError: if downstream kernels reject the input (non-monotonic
            ratios, invalid scale length, etc.). Pydantic validation is
            already handled at the FretboardInput layer.
    """
    return FretboardEcosphere.compute(req)
