"""
Rosette Pattern Schemas — Enums, dataclasses, and type definitions.

Extracted from pattern_generator.py during WP-3 God-Object Decomposition.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum


# ============================================================================
# ENUMS AND CONSTANTS
# ============================================================================

class PatternType(str, Enum):
    """Available pattern types for rosette rings."""
    ROPE = "rope"
    HERRINGBONE = "herringbone"
    CHECKERBOARD = "checkerboard"
    SOLID = "solid"
    CUSTOM_MATRIX = "custom_matrix"


class MaterialType(str, Enum):
    """Common veneer materials for rosettes."""
    BLACK = "black"      # Ebony, dyed veneer
    WHITE = "white"      # Maple, holly, spruce
    BROWN = "brown"      # Walnut, rosewood
    NATURAL = "natural"  # Unspecified wood tone


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    DXF = "dxf"
    SVG = "svg"
    BOM = "bom"          # Bill of materials only
    ASSEMBLY = "assembly" # Assembly instructions


# ============================================================================
# DATA CLASSES - Traditional Matrix Method
# ============================================================================

@dataclass
class MatrixFormula:
    """
    Traditional craftsman's matrix formula for rope patterns.

    Based on video methodology:
    - Each row defines how many strips of each material
    - Column sequence defines assembly order
    - Strips are glued into sticks, sliced into chips, assembled per matrix
    """
    name: str
    rows: List[Dict[str, int]]  # Each row: {"black": 5, "white": 2}
    column_sequence: List[int]   # Assembly order, 1-indexed row references
    strip_width_mm: float = 1.0
    strip_thickness_mm: float = 0.6
    chip_length_mm: float = 2.0  # Length when sliced
    notes: Optional[str] = None

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.column_sequence)

    def get_material_totals(self) -> Dict[str, int]:
        """Calculate total strips needed per material."""
        totals: Dict[str, int] = {}
        for row in self.rows:
            for material, count in row.items():
                totals[material] = totals.get(material, 0) + count
        return totals

    def get_pattern_width_mm(self) -> float:
        """Calculate total pattern width from column sequence."""
        return len(self.column_sequence) * self.strip_width_mm

    def get_pattern_height_mm(self) -> float:
        """Calculate pattern height from row count."""
        max_strips = max(sum(row.values()) for row in self.rows)
        return max_strips * self.strip_thickness_mm

    def validate(self) -> List[str]:
        """Validate the matrix formula."""
        errors = []
        if not self.rows:
            errors.append("Matrix must have at least one row")
        if not self.column_sequence:
            errors.append("Column sequence cannot be empty")

        for col_ref in self.column_sequence:
            if col_ref < 1 or col_ref > len(self.rows):
                errors.append(f"Column sequence references invalid row {col_ref}")

        return errors


@dataclass
class StripCutList:
    """Bill of materials for traditional method."""
    material: str
    count: int
    width_mm: float
    thickness_mm: float
    length_mm: float  # Length of veneer panel needed

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.length_mm * self.count

    @property
    def volume_mm3(self) -> float:
        return self.area_mm2 * self.thickness_mm


@dataclass
class AssemblyInstruction:
    """Step-by-step assembly instruction."""
    step: int
    action: str
    details: str
    materials: List[str]
    diagram_ref: Optional[str] = None


@dataclass
class TraditionalPatternResult:
    """Complete result from traditional matrix method."""
    formula: MatrixFormula
    cut_list: List[StripCutList]
    assembly_instructions: List[AssemblyInstruction]
    material_totals: Dict[str, int]
    pattern_dimensions: Dict[str, float]
    estimated_waste_percent: float = 15.0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": "traditional_matrix",
            "formula": asdict(self.formula),
            "cut_list": [asdict(c) for c in self.cut_list],
            "assembly_instructions": [asdict(a) for a in self.assembly_instructions],
            "material_totals": self.material_totals,
            "pattern_dimensions": self.pattern_dimensions,
            "estimated_waste_percent": self.estimated_waste_percent,
            "notes": self.notes,
        }


# ============================================================================
# DATA CLASSES - Modern Parametric Method
# ============================================================================

@dataclass
class RingSpec:
    """Specification for a single rosette ring."""
    ring_index: int          # 0 = innermost
    inner_diameter_mm: float
    outer_diameter_mm: float
    pattern_type: PatternType
    primary_color: str = "black"
    secondary_color: str = "white"
    tile_width_mm: float = 2.0
    tile_angle_deg: float = 45.0
    notes: Optional[str] = None

    @property
    def width_mm(self) -> float:
        return (self.outer_diameter_mm - self.inner_diameter_mm) / 2

    @property
    def circumference_mm(self) -> float:
        """Average circumference of the ring."""
        avg_diameter = (self.inner_diameter_mm + self.outer_diameter_mm) / 2
        return math.pi * avg_diameter


@dataclass
class RosetteSpec:
    """Complete rosette specification."""
    name: str
    rings: List[RingSpec]
    soundhole_diameter_mm: float = 100.0
    style_tag: Optional[str] = None
    notes: Optional[str] = None

    @property
    def outer_diameter_mm(self) -> float:
        if not self.rings:
            return self.soundhole_diameter_mm
        return max(r.outer_diameter_mm for r in self.rings)

    @property
    def inner_diameter_mm(self) -> float:
        if not self.rings:
            return self.soundhole_diameter_mm
        return min(r.inner_diameter_mm for r in self.rings)

    def validate(self) -> List[str]:
        """Validate rosette specification."""
        errors = []
        if not self.rings:
            errors.append("Rosette must have at least one ring")

        sorted_rings = sorted(self.rings, key=lambda r: r.inner_diameter_mm)
        for i, ring in enumerate(sorted_rings):
            if ring.inner_diameter_mm >= ring.outer_diameter_mm:
                errors.append(f"Ring {i}: inner diameter must be less than outer")
            if i > 0:
                prev = sorted_rings[i - 1]
                if ring.inner_diameter_mm < prev.outer_diameter_mm:
                    errors.append(f"Ring {i} overlaps with ring {i - 1}")

        return errors


@dataclass
class Point2D:
    """2D point for geometry."""
    x: float
    y: float

    def rotate(self, angle_rad: float, cx: float = 0, cy: float = 0) -> 'Point2D':
        """Rotate point around center."""
        dx = self.x - cx
        dy = self.y - cy
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return Point2D(
            cx + dx * cos_a - dy * sin_a,
            cy + dx * sin_a + dy * cos_a
        )


@dataclass
class PathSegment:
    """A path segment for DXF/SVG output."""
    points: List[Point2D]
    is_closed: bool = False
    layer: str = "0"
    color: str = "black"


@dataclass
class ModernPatternResult:
    """Complete result from modern parametric method."""
    spec: RosetteSpec
    paths: List[PathSegment]
    bom: Dict[str, float]  # material -> area in mm²
    estimated_cut_time_min: float
    dxf_content: Optional[str] = None
    svg_content: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": "modern_parametric",
            "spec": asdict(self.spec),
            "path_count": len(self.paths),
            "bom": self.bom,
            "estimated_cut_time_min": self.estimated_cut_time_min,
            "has_dxf": self.dxf_content is not None,
            "has_svg": self.svg_content is not None,
            "notes": self.notes,
        }
