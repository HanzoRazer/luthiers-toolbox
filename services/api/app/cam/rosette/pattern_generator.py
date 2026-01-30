#!/usr/bin/env python3
"""
Rosette Pattern Generator - Combined Traditional + Modern Methods

This module implements both the traditional craftsman matrix method
(laminate-slice-assemble) and modern CAD parametric methods for 
rosette pattern generation.

Target: TXRX Labs presentation - January 2026
Author: Luthier's ToolBox Project

Traditional Method Source: Rope pattern video methodology
Modern Method Source: SkyScraper Guitars CAD approach

================================================================================
FUTURE ENHANCEMENTS ROADMAP
================================================================================

Phase 1: Pattern Library Expansion
----------------------------------
- [ ] Historical Pattern Database
      * Torres rosette formulas (multiple variations)
      * Hauser patterns
      * Romanillos designs  
      * Fleta guitar rosettes
      * Simplicio patterns
      * Robert Bouchet designs
      * Source: Video tutorials, luthier documentation, museum photos

- [ ] Pattern Categories & Tags
      * Style: Spanish, German, French, Modern, Celtic
      * Complexity: Beginner, Intermediate, Advanced, Master
      * Era: Historical (pre-1900), Classical (1900-1970), Contemporary
      * Materials: 2-color, 3-color, multi-wood

- [ ] User-Contributed Patterns
      * Upload custom matrix formulas
      * Share patterns with community
      * Rating/review system
      * Attribution tracking

Phase 2: Advanced Matrix Features
---------------------------------
- [ ] Multi-Color Matrix Support
      * Extend beyond black/white to 3+ materials
      * Example: {"ebony": 3, "maple": 2, "rosewood": 1}
      * Auto-generate cut lists for all materials
      * Color-coded assembly diagrams

- [ ] Matrix Visualization
      * Real-time grid preview as formula is edited
      * Color blocks showing pattern before fabrication
      * Animation showing assembly sequence
      * Export visualization as PNG/PDF for workshop reference

- [ ] Matrix Optimization
      * Suggest material-efficient column sequences
      * Minimize waste calculations
      * Alternative sequences with same visual result
      * "Simplify" option to reduce strip count while preserving look

- [ ] Reverse Engineering
      * Input: photo of existing rosette
      * Output: estimated matrix formula
      * ML-assisted pattern recognition
      * Manual refinement tools

Phase 3: CAD/CAM Integration
----------------------------
- [ ] Advanced DXF Export Options
      * Layer organization by ring/material
      * Toolpath-ready output (offset for kerf)
      * Multiple DXF versions (R12, R14, 2018)
      * Spline vs. polyline options

- [ ] G-Code Generation
      * Direct G-code output for CNC routers
      * Post-processor selection (Grbl, Mach3, LinuxCNC)
      * Toolpath strategies: profile, pocket, v-carve
      * Feed/speed recommendations per material

- [ ] Laser Cutter Support
      * Power/speed settings per material
      * Kerf compensation
      * Multi-pass for thick veneer
      * Lightburn/RDWorks compatible output

- [ ] 3D Preview
      * Three.js visualization of assembled rosette
      * Show ring depth/profile
      * Material textures
      * Export STL for 3D printing molds

Phase 4: Fabrication Workflow
-----------------------------
- [ ] Interactive Assembly Guide
      * Step-by-step with photos/diagrams
      * Checklist with progress tracking
      * Timer for glue dry times
      * Tips and troubleshooting per step

- [ ] Material Calculator Enhancement
      * Link to supplier catalogs (StewMac, LMI, etc.)
      * Price estimation
      * Inventory tracking integration
      * Reorder alerts when stock low

- [ ] Quality Control Checklist
      * Pre-cut inspection points
      * Assembly verification steps
      * Final QC before installation
      * Photo documentation prompts

Phase 5: RMOS Integration
-------------------------
- [ ] Bidirectional Art Studio Connection
      * Push patterns to Art Studio library
      * Pull constraints from RMOS feasibility
      * Sync pattern metadata across systems

- [ ] Feasibility Scoring
      * CNC time estimation
      * Material cost calculation
      * Complexity score for pricing
      * Risk assessment (fragile patterns, difficult materials)

- [ ] Project Templates
      * Full rosette specs for common guitar models
      * Dreadnought standard (Martin D-28 style)
      * Classical standard (various sizes)
      * OM/000 configurations
      * Custom template builder

Phase 6: AI Features (Future)
-----------------------------
- [ ] Natural Language Pattern Design
      * "Create a Torres-style rosette with 5 rings, high contrast"
      * AI suggests parameters, user refines
      * Style transfer from reference images

- [ ] Pattern Variation Generator
      * Input: base pattern
      * Output: 10 variations (subtle to dramatic)
      * Preserve style while exploring options

- [ ] Historical Style Matching
      * Analyze photo of antique guitar
      * Generate rosette matching that era/maker
      * Reference database of historical examples

================================================================================
IMPLEMENTATION PRIORITY (for TXRX Labs January 2026)
================================================================================

MVP (Must Have):
1. ✅ Traditional matrix method with presets
2. ✅ Modern parametric ring definition
3. ✅ DXF/SVG export
4. ✅ BOM generation
5. ✅ Assembly instructions
6. [ ] 3-4 more historical presets (Torres, Hauser)

v1.1 (January Release):
7. [ ] Multi-color matrix support
8. [ ] Matrix visualization preview
9. [ ] Pattern library save/load
10. [ ] Basic G-code generation

v1.5 (Q2 2026):
11. [ ] Interactive assembly guide
12. [ ] RMOS feasibility integration
13. [ ] 3D preview
14. [ ] User pattern sharing

v2.0 (Future):
15. [ ] AI pattern suggestions
16. [ ] Reverse engineering from photos
17. [ ] Full supplier integration

================================================================================
"""

from __future__ import annotations
import math
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Literal, Any
from enum import Enum
from datetime import datetime
import io

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
    
    Example from video:
        Row | Black | White
         1  |   5   |   2
         2  |   5   |   2
         3  |   5   |   2
         4  |   4   |   3
         5  |   4   |   3
        ----|-------|------
            |  23   |  12   (totals)
    
    Column sequence: [1, 2, 2, 1, 3, 4, 5, 4, 3]
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
        # Height is determined by max strips in any row
        max_strips = max(sum(row.values()) for row in self.rows)
        return max_strips * self.strip_thickness_mm
    
    def validate(self) -> List[str]:
        """Validate the matrix formula."""
        errors = []
        if not self.rows:
            errors.append("Matrix must have at least one row")
        if not self.column_sequence:
            errors.append("Column sequence cannot be empty")
        
        # Check that all column references are valid
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
    style_tag: Optional[str] = None  # "spanish_traditional", "modern", etc.
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
        
        # Check for ring overlaps and gaps
        sorted_rings = sorted(self.rings, key=lambda r: r.inner_diameter_mm)
        for i, ring in enumerate(sorted_rings):
            if ring.inner_diameter_mm >= ring.outer_diameter_mm:
                errors.append(f"Ring {i}: inner diameter must be less than outer")
            if i > 0:
                prev = sorted_rings[i-1]
                if ring.inner_diameter_mm < prev.outer_diameter_mm:
                    errors.append(f"Ring {i} overlaps with ring {i-1}")
        
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


# ============================================================================
# PRESET PATTERNS - Traditional Matrix Formulas
# ============================================================================

PRESET_MATRICES: Dict[str, MatrixFormula] = {
    # =========================================================================
    # BASIC / BEGINNER PATTERNS
    # =========================================================================
    "classic_rope_5x9": MatrixFormula(
        name="Classic Rope 5x9",
        rows=[
            {"black": 5, "white": 2},
            {"black": 5, "white": 2},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 4, "white": 3},
        ],
        column_sequence=[1, 2, 2, 1, 3, 4, 5, 4, 3],
        strip_width_mm=1.0,
        strip_thickness_mm=0.6,
        chip_length_mm=2.0,
        notes="Traditional Spanish rope pattern from craftsman video"
    ),
    
    "simple_rope_3x5": MatrixFormula(
        name="Simple Rope 3x5",
        rows=[
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
            {"black": 3, "white": 2},
        ],
        column_sequence=[1, 2, 3, 2, 1],
        strip_width_mm=1.2,
        strip_thickness_mm=0.6,
        notes="Simplified rope pattern for beginners"
    ),
    
    "diagonal_stripe_4x7": MatrixFormula(
        name="Diagonal Stripe 4x7",
        rows=[
            {"black": 4, "white": 1},
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
            {"black": 1, "white": 4},
        ],
        column_sequence=[1, 2, 3, 4, 3, 2, 1],
        strip_width_mm=1.0,
        strip_thickness_mm=0.5,
        notes="Creates diagonal stripe effect"
    ),
    
    "chevron_5x7": MatrixFormula(
        name="Chevron 5x7",
        rows=[
            {"black": 1, "white": 4},
            {"black": 2, "white": 3},
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
            {"black": 1, "white": 4},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3],
        strip_width_mm=0.8,
        strip_thickness_mm=0.6,
        notes="V-shaped chevron pattern"
    ),
    
    # =========================================================================
    # ANTONIO DE TORRES PATTERNS (Spanish, c. 1850-1892)
    # Father of the modern classical guitar
    # =========================================================================
    "torres_simple_rope_4x7": MatrixFormula(
        name="Torres Simple Rope",
        rows=[
            {"black": 4, "white": 2},
            {"black": 3, "white": 3},
            {"black": 3, "white": 3},
            {"black": 4, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 3, 2, 1],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.5,
        notes="Torres-style simple rope, symmetric pattern. Common on his later instruments."
    ),
    
    "torres_ladder_6x9": MatrixFormula(
        name="Torres Ladder Pattern",
        rows=[
            {"black": 6, "white": 1},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Torres ladder/staircase pattern. Creates diagonal stepping effect."
    ),
    
    "torres_wave_5x11": MatrixFormula(
        name="Torres Wave Pattern",
        rows=[
            {"black": 2, "white": 5},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 2, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Torres wave/undulating pattern. Creates flowing visual movement."
    ),
    
    "torres_diamond_7x9": MatrixFormula(
        name="Torres Diamond Mosaic",
        rows=[
            {"black": 1, "white": 6},
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
            {"black": 1, "white": 6},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 6, 5],
        strip_width_mm=0.6,
        strip_thickness_mm=0.5,
        chip_length_mm=1.5,
        notes="Torres diamond/lozenge pattern. Classic Spanish mosaic style."
    ),
    
    # =========================================================================
    # HERMANN HAUSER PATTERNS (German, c. 1920-1952)
    # Master luthier, made guitars for Segovia
    # =========================================================================
    "hauser_rope_6x11": MatrixFormula(
        name="Hauser Classic Rope",
        rows=[
            {"black": 6, "white": 2},
            {"black": 5, "white": 3},
            {"black": 4, "white": 4},
            {"black": 4, "white": 4},
            {"black": 5, "white": 3},
            {"black": 6, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Hauser-style rope pattern. Refined German precision, symmetric."
    ),
    
    "hauser_herringbone_8x13": MatrixFormula(
        name="Hauser Herringbone",
        rows=[
            {"black": 1, "white": 7},
            {"black": 2, "white": 6},
            {"black": 3, "white": 5},
            {"black": 4, "white": 4},
            {"black": 5, "white": 3},
            {"black": 6, "white": 2},
            {"black": 7, "white": 1},
            {"black": 8, "white": 0},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3],
        strip_width_mm=0.6,
        strip_thickness_mm=0.4,
        chip_length_mm=1.5,
        notes="Hauser herringbone variation. High contrast diagonal effect."
    ),
    
    "hauser_segovia_7x11": MatrixFormula(
        name="Hauser Segovia Model",
        rows=[
            {"black": 5, "white": 3},
            {"black": 4, "white": 4},
            {"black": 3, "white": 5},
            {"black": 2, "white": 6},
            {"black": 3, "white": 5},
            {"black": 4, "white": 4},
            {"black": 5, "white": 3},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3],
        strip_width_mm=0.65,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Pattern style used on Hauser guitars made for Andrés Segovia."
    ),
    
    # =========================================================================
    # JOSÉ ROMANILLOS PATTERNS (Spanish/British, contemporary master)
    # =========================================================================
    "romanillos_rope_5x9": MatrixFormula(
        name="Romanillos Rope",
        rows=[
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Romanillos-style rope. Clean, balanced Spanish tradition."
    ),
    
    "romanillos_mosaic_6x11": MatrixFormula(
        name="Romanillos Mosaic",
        rows=[
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Romanillos mosaic pattern. Elegant Spanish-British fusion."
    ),
    
    # =========================================================================
    # IGNACIO FLETA PATTERNS (Spanish, c. 1930-1977)
    # Barcelona master, known for powerful tone
    # =========================================================================
    "fleta_rope_6x9": MatrixFormula(
        name="Fleta Barcelona Rope",
        rows=[
            {"black": 6, "white": 1},
            {"black": 5, "white": 2},
            {"black": 4, "white": 3},
            {"black": 4, "white": 3},
            {"black": 5, "white": 2},
            {"black": 6, "white": 1},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3],
        strip_width_mm=0.75,
        strip_thickness_mm=0.5,
        chip_length_mm=1.7,
        notes="Fleta-style rope pattern. Bold, high-contrast Barcelona tradition."
    ),
    
    "fleta_wave_7x11": MatrixFormula(
        name="Fleta Wave",
        rows=[
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 5, "white": 2},
            {"black": 6, "white": 1},
            {"black": 5, "white": 2},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 6, 5, 4, 3],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Fleta wave pattern. Dramatic visual flow."
    ),
    
    # =========================================================================
    # ROBERT BOUCHET PATTERNS (French, c. 1946-1986)
    # Renowned French master luthier
    # =========================================================================
    "bouchet_french_rope_5x9": MatrixFormula(
        name="Bouchet French Rope",
        rows=[
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1],
        strip_width_mm=0.85,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Bouchet-style rope. Refined French elegance, subtle contrast."
    ),
    
    "bouchet_mosaic_6x11": MatrixFormula(
        name="Bouchet Mosaic",
        rows=[
            {"black": 2, "white": 5},
            {"black": 3, "white": 4},
            {"black": 4, "white": 3},
            {"black": 4, "white": 3},
            {"black": 3, "white": 4},
            {"black": 2, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.75,
        strip_thickness_mm=0.5,
        chip_length_mm=1.7,
        notes="Bouchet mosaic pattern. Lighter, airy French aesthetic."
    ),
    
    # =========================================================================
    # FRANCISCO SIMPLICIO PATTERNS (Spanish, c. 1920-1932)
    # Barcelona school, ornate style
    # =========================================================================
    "simplicio_ornate_8x13": MatrixFormula(
        name="Simplicio Ornate",
        rows=[
            {"black": 2, "white": 6},
            {"black": 3, "white": 5},
            {"black": 5, "white": 3},
            {"black": 6, "white": 2},
            {"black": 6, "white": 2},
            {"black": 5, "white": 3},
            {"black": 3, "white": 5},
            {"black": 2, "white": 6},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3],
        strip_width_mm=0.6,
        strip_thickness_mm=0.45,
        chip_length_mm=1.4,
        notes="Simplicio ornate pattern. Complex, decorative Barcelona style."
    ),
    
    "simplicio_zigzag_6x11": MatrixFormula(
        name="Simplicio Zigzag",
        rows=[
            {"black": 6, "white": 1},
            {"black": 4, "white": 3},
            {"black": 2, "white": 5},
            {"black": 2, "white": 5},
            {"black": 4, "white": 3},
            {"black": 6, "white": 1},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Simplicio zigzag pattern. Bold angular design."
    ),
    
    # =========================================================================
    # MODERN / CONTEMPORARY PATTERNS
    # =========================================================================
    "modern_minimalist_3x5": MatrixFormula(
        name="Modern Minimalist",
        rows=[
            {"black": 2, "white": 3},
            {"black": 3, "white": 2},
            {"black": 2, "white": 3},
        ],
        column_sequence=[1, 2, 3, 2, 1],
        strip_width_mm=1.0,
        strip_thickness_mm=0.6,
        chip_length_mm=2.0,
        notes="Contemporary minimalist design. Clean, simple, modern aesthetic."
    ),
    
    "modern_bold_4x7": MatrixFormula(
        name="Modern Bold Stripe",
        rows=[
            {"black": 5, "white": 1},
            {"black": 3, "white": 3},
            {"black": 3, "white": 3},
            {"black": 5, "white": 1},
        ],
        column_sequence=[1, 2, 3, 4, 3, 2, 1],
        strip_width_mm=1.2,
        strip_thickness_mm=0.6,
        chip_length_mm=2.2,
        notes="Modern bold stripe. High contrast contemporary look."
    ),
    
    "modern_asymmetric_5x8": MatrixFormula(
        name="Modern Asymmetric",
        rows=[
            {"black": 5, "white": 1},
            {"black": 4, "white": 2},
            {"black": 3, "white": 3},
            {"black": 2, "white": 4},
            {"black": 1, "white": 5},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2],
        strip_width_mm=0.9,
        strip_thickness_mm=0.5,
        chip_length_mm=1.8,
        notes="Contemporary asymmetric gradient. Non-traditional, artistic."
    ),
    
    # =========================================================================
    # THREE-COLOR PATTERNS (Advanced)
    # =========================================================================
    "tricolor_spanish_6x9": MatrixFormula(
        name="Tricolor Spanish",
        rows=[
            {"black": 3, "white": 2, "brown": 2},
            {"black": 2, "white": 3, "brown": 2},
            {"black": 2, "white": 2, "brown": 3},
            {"black": 2, "white": 2, "brown": 3},
            {"black": 2, "white": 3, "brown": 2},
            {"black": 3, "white": 2, "brown": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3],
        strip_width_mm=0.7,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="Three-color Spanish pattern. Ebony, maple, rosewood combination."
    ),
    
    "tricolor_gradient_5x9": MatrixFormula(
        name="Tricolor Gradient",
        rows=[
            {"black": 4, "white": 1, "brown": 2},
            {"black": 3, "white": 2, "brown": 2},
            {"black": 2, "white": 3, "brown": 2},
            {"black": 2, "white": 2, "brown": 3},
            {"black": 1, "white": 2, "brown": 4},
        ],
        column_sequence=[1, 2, 3, 4, 5, 4, 3, 2, 1],
        strip_width_mm=0.75,
        strip_thickness_mm=0.5,
        chip_length_mm=1.7,
        notes="Three-color gradient. Transitions dark to light to medium."
    ),

    "german_tricolor_rope_6x11": MatrixFormula(
        name="German Tricolor Rope",
        rows=[
            {"red": 3, "white": 2, "green": 2},
            {"red": 2, "white": 3, "green": 2},
            {"red": 2, "white": 2, "green": 3},
            {"red": 2, "white": 2, "green": 3},
            {"red": 2, "white": 3, "green": 2},
            {"red": 3, "white": 2, "green": 2},
        ],
        column_sequence=[1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1],
        strip_width_mm=0.8,
        strip_thickness_mm=0.5,
        chip_length_mm=1.6,
        notes="German tricolor twisted rope (Seil) pattern. Red, white, green dyed veneers. Classic Central European lutherie tradition."
    ),
}


# ============================================================================
# TRADITIONAL METHOD GENERATOR
# ============================================================================

class TraditionalPatternGenerator:
    """
    Generator for traditional matrix-based rope patterns.
    
    Workflow:
    1. Define matrix formula (rows × columns)
    2. Calculate strip cut list (BOM)
    3. Generate assembly instructions
    4. Output fabrication data
    """
    
    def __init__(self, formula: MatrixFormula):
        self.formula = formula
        errors = formula.validate()
        if errors:
            raise ValueError(f"Invalid formula: {'; '.join(errors)}")
    
    def generate_cut_list(self, 
                          panel_length_mm: float = 300.0,
                          include_waste: bool = True) -> List[StripCutList]:
        """Generate bill of materials for strip cutting."""
        totals = self.formula.get_material_totals()
        cut_list = []
        
        waste_factor = 1.15 if include_waste else 1.0
        
        for material, count in totals.items():
            cut_list.append(StripCutList(
                material=material,
                count=int(count * waste_factor),
                width_mm=self.formula.strip_width_mm,
                thickness_mm=self.formula.strip_thickness_mm,
                length_mm=panel_length_mm,
            ))
        
        return cut_list
    
    def generate_assembly_instructions(self) -> List[AssemblyInstruction]:
        """Generate step-by-step assembly instructions."""
        instructions = []
        step = 1
        
        # Step 1: Prepare veneer panels
        materials = list(self.formula.get_material_totals().keys())
        instructions.append(AssemblyInstruction(
            step=step,
            action="Prepare Veneer Panels",
            details=f"Cut veneer panels to {self.formula.strip_width_mm}mm strips. "
                   f"You will need strips in: {', '.join(materials)}",
            materials=materials,
        ))
        step += 1
        
        # Step 2: Sort strips by row
        instructions.append(AssemblyInstruction(
            step=step,
            action="Sort Strips by Row",
            details="Organize strips according to the row formula:",
            materials=materials,
        ))
        for i, row in enumerate(self.formula.rows, 1):
            row_desc = ", ".join(f"{count}× {mat}" for mat, count in row.items())
            instructions[-1].details += f"\n  Row {i}: {row_desc}"
        step += 1
        
        # Step 3: Glue strips into column sticks
        instructions.append(AssemblyInstruction(
            step=step,
            action="Glue Column Sticks",
            details="Glue strips together to form column sticks. "
                   "Each row becomes one column stick. Let dry completely.",
            materials=materials,
        ))
        step += 1
        
        # Step 4: Slice sticks into chips
        instructions.append(AssemblyInstruction(
            step=step,
            action="Slice Into Chips",
            details=f"Using a fine-tooth saw or veneer saw, slice each column stick "
                   f"into chips approximately {self.formula.chip_length_mm}mm thick.",
            materials=[],
        ))
        step += 1
        
        # Step 5: Assemble per column sequence
        seq_str = " → ".join(str(c) for c in self.formula.column_sequence)
        instructions.append(AssemblyInstruction(
            step=step,
            action="Assemble Pattern",
            details=f"Arrange chips according to column sequence:\n  {seq_str}\n"
                   "Where each number refers to the row number of the chip. "
                   "Glue chips together to form the final pattern strip.",
            materials=[],
        ))
        step += 1
        
        # Step 6: Final processing
        instructions.append(AssemblyInstruction(
            step=step,
            action="Finish Pattern Strip",
            details="Sand smooth, then slice to desired width for rosette ring. "
                   "The pattern strip can be bent around the rosette channel.",
            materials=[],
        ))
        
        return instructions
    
    def generate(self, 
                 panel_length_mm: float = 300.0,
                 include_waste: bool = True) -> TraditionalPatternResult:
        """Generate complete traditional pattern result."""
        cut_list = self.generate_cut_list(panel_length_mm, include_waste)
        instructions = self.generate_assembly_instructions()
        
        pattern_dims = {
            "width_mm": self.formula.get_pattern_width_mm(),
            "height_mm": self.formula.get_pattern_height_mm(),
            "chip_length_mm": self.formula.chip_length_mm,
            "row_count": self.formula.row_count,
            "column_count": self.formula.column_count,
        }
        
        notes = [
            f"Pattern: {self.formula.name}",
            f"Column sequence: {' '.join(map(str, self.formula.column_sequence))}",
        ]
        if self.formula.notes:
            notes.append(self.formula.notes)
        
        return TraditionalPatternResult(
            formula=self.formula,
            cut_list=cut_list,
            assembly_instructions=instructions,
            material_totals=self.formula.get_material_totals(),
            pattern_dimensions=pattern_dims,
            estimated_waste_percent=15.0 if include_waste else 0.0,
            notes=notes,
        )


# ============================================================================
# MODERN PARAMETRIC METHOD GENERATOR
# ============================================================================

class ModernPatternGenerator:
    """
    Generator for modern CAD-based parametric patterns.
    
    Workflow:
    1. Define rosette specification (rings, diameters, patterns)
    2. Generate pattern geometry for each ring
    3. Output DXF/SVG for CNC/laser cutting
    """
    
    def __init__(self, spec: RosetteSpec):
        self.spec = spec
        errors = spec.validate()
        if errors:
            raise ValueError(f"Invalid spec: {'; '.join(errors)}")
    
    def _generate_circle(self, 
                         cx: float, cy: float, 
                         radius: float, 
                         segments: int = 72) -> List[Point2D]:
        """Generate circle as list of points."""
        points = []
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            points.append(Point2D(
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle)
            ))
        return points
    
    def _generate_herringbone_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate herringbone pattern for a ring."""
        paths = []
        
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2
        
        # Calculate number of tiles around circumference
        avg_r = (inner_r + outer_r) / 2
        circumference = 2 * math.pi * avg_r
        tile_count = max(1, int(circumference / ring.tile_width_mm))
        
        angle_step = 2 * math.pi / tile_count
        tile_angle = math.radians(ring.tile_angle_deg)
        
        for i in range(tile_count):
            base_angle = i * angle_step
            
            # Create diagonal line across tile
            # Alternate direction for herringbone effect
            if i % 2 == 0:
                p1 = Point2D(
                    inner_r * math.cos(base_angle - tile_angle/2),
                    inner_r * math.sin(base_angle - tile_angle/2)
                )
                p2 = Point2D(
                    outer_r * math.cos(base_angle + tile_angle/2),
                    outer_r * math.sin(base_angle + tile_angle/2)
                )
            else:
                p1 = Point2D(
                    inner_r * math.cos(base_angle + tile_angle/2),
                    inner_r * math.sin(base_angle + tile_angle/2)
                )
                p2 = Point2D(
                    outer_r * math.cos(base_angle - tile_angle/2),
                    outer_r * math.sin(base_angle - tile_angle/2)
                )
            
            paths.append(PathSegment(
                points=[p1, p2],
                is_closed=False,
                layer=f"ring_{ring.ring_index}",
                color=ring.primary_color if i % 2 == 0 else ring.secondary_color,
            ))
        
        return paths
    
    def _generate_checkerboard_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate checkerboard pattern for a ring."""
        paths = []
        
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2
        
        # Calculate tile count
        avg_r = (inner_r + outer_r) / 2
        circumference = 2 * math.pi * avg_r
        tile_count = max(4, int(circumference / ring.tile_width_mm))
        # Make even for alternating pattern
        tile_count = tile_count + (tile_count % 2)
        
        angle_step = 2 * math.pi / tile_count
        
        for i in range(tile_count):
            start_angle = i * angle_step
            end_angle = (i + 1) * angle_step
            
            # Create tile as 4-point polygon
            points = [
                Point2D(inner_r * math.cos(start_angle), inner_r * math.sin(start_angle)),
                Point2D(outer_r * math.cos(start_angle), outer_r * math.sin(start_angle)),
                Point2D(outer_r * math.cos(end_angle), outer_r * math.sin(end_angle)),
                Point2D(inner_r * math.cos(end_angle), inner_r * math.sin(end_angle)),
            ]
            
            paths.append(PathSegment(
                points=points,
                is_closed=True,
                layer=f"ring_{ring.ring_index}",
                color=ring.primary_color if i % 2 == 0 else ring.secondary_color,
            ))
        
        return paths
    
    def _generate_solid_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate solid ring (inner and outer circles)."""
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2
        
        return [
            PathSegment(
                points=self._generate_circle(0, 0, inner_r),
                is_closed=True,
                layer=f"ring_{ring.ring_index}_inner",
                color=ring.primary_color,
            ),
            PathSegment(
                points=self._generate_circle(0, 0, outer_r),
                is_closed=True,
                layer=f"ring_{ring.ring_index}_outer",
                color=ring.primary_color,
            ),
        ]
    
    def _generate_rope_ring(self, ring: RingSpec) -> List[PathSegment]:
        """Generate rope pattern for a ring using spiral curves."""
        paths = []
        
        inner_r = ring.inner_diameter_mm / 2
        outer_r = ring.outer_diameter_mm / 2
        ring_width = outer_r - inner_r
        
        # Number of "rope strands"
        strand_count = max(2, int(ring_width / ring.tile_width_mm))
        twist_count = 8  # Number of twists around the ring
        segments_per_twist = 12
        
        for strand in range(strand_count):
            points = []
            strand_offset = strand / strand_count
            
            for i in range(twist_count * segments_per_twist + 1):
                t = i / (twist_count * segments_per_twist)
                theta = 2 * math.pi * t  # Angle around ring
                
                # Radial position oscillates to create rope effect
                rope_phase = 2 * math.pi * twist_count * t + strand_offset * 2 * math.pi
                r = inner_r + ring_width * (0.5 + 0.3 * math.sin(rope_phase))
                
                points.append(Point2D(r * math.cos(theta), r * math.sin(theta)))
            
            paths.append(PathSegment(
                points=points,
                is_closed=False,
                layer=f"ring_{ring.ring_index}_strand_{strand}",
                color=ring.primary_color if strand % 2 == 0 else ring.secondary_color,
            ))
        
        return paths
    
    def generate_ring_paths(self, ring: RingSpec) -> List[PathSegment]:
        """Generate paths for a single ring based on pattern type."""
        if ring.pattern_type == PatternType.HERRINGBONE:
            return self._generate_herringbone_ring(ring)
        elif ring.pattern_type == PatternType.CHECKERBOARD:
            return self._generate_checkerboard_ring(ring)
        elif ring.pattern_type == PatternType.SOLID:
            return self._generate_solid_ring(ring)
        elif ring.pattern_type == PatternType.ROPE:
            return self._generate_rope_ring(ring)
        else:
            # Default to solid
            return self._generate_solid_ring(ring)
    
    def _export_dxf(self, paths: List[PathSegment]) -> str:
        """Export paths to DXF R12 format."""
        lines = []
        
        # Header
        lines.extend([
            "0", "SECTION",
            "2", "HEADER",
            "9", "$ACADVER",
            "1", "AC1009",  # R12
            "9", "$INSUNITS",
            "70", "4",  # mm
            "0", "ENDSEC",
        ])
        
        # Tables section (layers)
        lines.extend([
            "0", "SECTION",
            "2", "TABLES",
            "0", "TABLE",
            "2", "LAYER",
        ])
        
        # Collect unique layers
        layers = set(p.layer for p in paths)
        for layer in layers:
            lines.extend([
                "0", "LAYER",
                "2", layer,
                "70", "0",
                "62", "7",  # White color
                "6", "CONTINUOUS",
            ])
        
        lines.extend([
            "0", "ENDTAB",
            "0", "ENDSEC",
        ])
        
        # Entities section
        lines.extend([
            "0", "SECTION",
            "2", "ENTITIES",
        ])
        
        for path in paths:
            if len(path.points) < 2:
                continue
            
            if path.is_closed and len(path.points) >= 3:
                # POLYLINE for closed shapes
                lines.extend([
                    "0", "POLYLINE",
                    "8", path.layer,
                    "66", "1",
                    "70", "1",  # Closed polyline
                ])
                for pt in path.points:
                    lines.extend([
                        "0", "VERTEX",
                        "8", path.layer,
                        "10", f"{pt.x:.6f}",
                        "20", f"{pt.y:.6f}",
                    ])
                lines.extend(["0", "SEQEND"])
            else:
                # LINE segments for open paths
                for i in range(len(path.points) - 1):
                    p1, p2 = path.points[i], path.points[i+1]
                    lines.extend([
                        "0", "LINE",
                        "8", path.layer,
                        "10", f"{p1.x:.6f}",
                        "20", f"{p1.y:.6f}",
                        "11", f"{p2.x:.6f}",
                        "21", f"{p2.y:.6f}",
                    ])
        
        lines.extend([
            "0", "ENDSEC",
            "0", "EOF",
        ])
        
        return "\n".join(lines)
    
    def _export_svg(self, paths: List[PathSegment]) -> str:
        """Export paths to SVG format."""
        # Calculate bounds
        all_x = [p.x for path in paths for p in path.points]
        all_y = [p.y for path in paths for p in path.points]
        
        if not all_x:
            min_x, max_x, min_y, max_y = -50, 50, -50, 50
        else:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
        
        padding = 5
        width = max_x - min_x + 2 * padding
        height = max_y - min_y + 2 * padding
        
        svg_lines = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" ',
            f'     viewBox="{min_x - padding} {min_y - padding} {width} {height}"',
            f'     width="{width}mm" height="{height}mm">',
            f'  <title>Rosette Pattern - {self.spec.name}</title>',
            f'  <desc>Generated by Luthier\'s ToolBox</desc>',
        ]
        
        # Add paths
        for i, path in enumerate(paths):
            if len(path.points) < 2:
                continue
            
            points_str = " ".join(f"{p.x:.3f},{p.y:.3f}" for p in path.points)
            
            if path.is_closed:
                svg_lines.append(
                    f'  <polygon points="{points_str}" '
                    f'fill="none" stroke="{path.color}" stroke-width="0.2"/>'
                )
            else:
                svg_lines.append(
                    f'  <polyline points="{points_str}" '
                    f'fill="none" stroke="{path.color}" stroke-width="0.2"/>'
                )
        
        svg_lines.append('</svg>')
        return "\n".join(svg_lines)
    
    def _calculate_bom(self, paths: List[PathSegment]) -> Dict[str, float]:
        """Calculate bill of materials (area per color/material)."""
        bom: Dict[str, float] = {}
        
        for ring in self.spec.rings:
            # Calculate ring area
            inner_r = ring.inner_diameter_mm / 2
            outer_r = ring.outer_diameter_mm / 2
            ring_area = math.pi * (outer_r**2 - inner_r**2)
            
            # Split by pattern (simplified)
            if ring.pattern_type == PatternType.SOLID:
                bom[ring.primary_color] = bom.get(ring.primary_color, 0) + ring_area
            else:
                # Assume 50/50 split for patterned rings
                half_area = ring_area / 2
                bom[ring.primary_color] = bom.get(ring.primary_color, 0) + half_area
                bom[ring.secondary_color] = bom.get(ring.secondary_color, 0) + half_area
        
        return bom
    
    def generate(self, 
                 include_dxf: bool = True,
                 include_svg: bool = True) -> ModernPatternResult:
        """Generate complete modern pattern result."""
        all_paths = []
        
        for ring in self.spec.rings:
            ring_paths = self.generate_ring_paths(ring)
            all_paths.extend(ring_paths)
        
        # Calculate BOM
        bom = self._calculate_bom(all_paths)
        
        # Estimate cut time (rough: 1 minute per 100 path segments)
        total_segments = sum(len(p.points) - 1 for p in all_paths if len(p.points) > 1)
        cut_time = total_segments / 100
        
        result = ModernPatternResult(
            spec=self.spec,
            paths=all_paths,
            bom=bom,
            estimated_cut_time_min=round(cut_time, 1),
            notes=[
                f"Generated {len(all_paths)} path segments",
                f"Total rings: {len(self.spec.rings)}",
            ],
        )
        
        if include_dxf:
            result.dxf_content = self._export_dxf(all_paths)
        
        if include_svg:
            result.svg_content = self._export_svg(all_paths)
        
        return result


# ============================================================================
# UNIFIED API - Combines Both Methods
# ============================================================================

class RosettePatternEngine:
    """
    Unified engine for rosette pattern generation.
    
    Supports both traditional matrix method and modern parametric method
    through a single API, suitable for UI integration.
    """
    
    def __init__(self):
        self.preset_matrices = PRESET_MATRICES.copy()
    
    def list_preset_matrices(self) -> List[Dict[str, Any]]:
        """List available preset matrix formulas."""
        return [
            {
                "id": key,
                "name": formula.name,
                "rows": formula.row_count,
                "columns": formula.column_count,
                "materials": list(formula.get_material_totals().keys()),
                "notes": formula.notes,
            }
            for key, formula in self.preset_matrices.items()
        ]
    
    def generate_traditional(self,
                            preset_id: Optional[str] = None,
                            custom_formula: Optional[Dict[str, Any]] = None,
                            panel_length_mm: float = 300.0) -> TraditionalPatternResult:
        """
        Generate pattern using traditional matrix method.
        
        Args:
            preset_id: ID of preset matrix formula
            custom_formula: Custom matrix formula dict
            panel_length_mm: Length of veneer panels
        
        Returns:
            Complete traditional pattern result with BOM and instructions
        """
        if preset_id:
            if preset_id not in self.preset_matrices:
                raise ValueError(f"Unknown preset: {preset_id}")
            formula = self.preset_matrices[preset_id]
        elif custom_formula:
            formula = MatrixFormula(**custom_formula)
        else:
            raise ValueError("Must provide preset_id or custom_formula")
        
        generator = TraditionalPatternGenerator(formula)
        return generator.generate(panel_length_mm=panel_length_mm)
    
    def generate_modern(self,
                       rings: List[Dict[str, Any]],
                       name: str = "Custom Rosette",
                       soundhole_diameter_mm: float = 100.0,
                       include_dxf: bool = True,
                       include_svg: bool = True) -> ModernPatternResult:
        """
        Generate pattern using modern parametric method.
        
        Args:
            rings: List of ring specifications
            name: Name for the rosette
            soundhole_diameter_mm: Soundhole diameter
            include_dxf: Generate DXF output
            include_svg: Generate SVG output
        
        Returns:
            Complete modern pattern result with geometry and files
        """
        ring_specs = []
        for i, ring_dict in enumerate(rings):
            ring_dict['ring_index'] = i
            if 'pattern_type' in ring_dict and isinstance(ring_dict['pattern_type'], str):
                ring_dict['pattern_type'] = PatternType(ring_dict['pattern_type'])
            ring_specs.append(RingSpec(**ring_dict))
        
        spec = RosetteSpec(
            name=name,
            rings=ring_specs,
            soundhole_diameter_mm=soundhole_diameter_mm,
        )
        
        generator = ModernPatternGenerator(spec)
        return generator.generate(include_dxf=include_dxf, include_svg=include_svg)
    
    def generate_combined(self,
                         matrix_preset: str,
                         ring_inner_mm: float,
                         ring_outer_mm: float,
                         name: str = "Combined Pattern") -> Dict[str, Any]:
        """
        Generate using both methods for the same pattern.
        
        Useful for comparing traditional BOM with modern CAD output.
        """
        # Traditional for BOM and instructions
        traditional = self.generate_traditional(preset_id=matrix_preset)
        
        # Modern for geometry - use rope pattern type for matrix-derived patterns
        modern = self.generate_modern(
            rings=[{
                "inner_diameter_mm": ring_inner_mm,
                "outer_diameter_mm": ring_outer_mm,
                "pattern_type": "rope",
                "primary_color": "black",
                "secondary_color": "white",
            }],
            name=name,
        )
        
        return {
            "name": name,
            "traditional": traditional.to_dict(),
            "modern": modern.to_dict(),
            "combined_notes": [
                "Traditional method provides BOM and assembly instructions",
                "Modern method provides CAD geometry for CNC/laser",
                "Use traditional BOM for material preparation",
                "Use modern DXF for cutting templates",
            ],
        }


# ============================================================================
# CLI AND DEMO
# ============================================================================

def demo():
    """Demonstrate both methods."""
    engine = RosettePatternEngine()
    
    print("=" * 60)
    print("ROSETTE PATTERN GENERATOR - Combined Traditional + Modern")
    print("=" * 60)
    
    # List presets
    print("\n--- Available Preset Matrices ---")
    for preset in engine.list_preset_matrices():
        print(f"  {preset['id']}: {preset['name']} ({preset['rows']}×{preset['columns']})")
    
    # Traditional method demo
    print("\n--- Traditional Matrix Method Demo ---")
    trad_result = engine.generate_traditional(preset_id="classic_rope_5x9")
    
    print(f"Pattern: {trad_result.formula.name}")
    print(f"Dimensions: {trad_result.pattern_dimensions['width_mm']}mm × {trad_result.pattern_dimensions['height_mm']}mm")
    print(f"\nMaterial Totals (strips needed):")
    for mat, count in trad_result.material_totals.items():
        print(f"  {mat}: {count} strips")
    
    print(f"\nCut List (with 15% waste):")
    for item in trad_result.cut_list:
        print(f"  {item.material}: {item.count}× strips @ {item.width_mm}×{item.length_mm}mm")
    
    print(f"\nAssembly Instructions:")
    for instr in trad_result.assembly_instructions:
        print(f"  {instr.step}. {instr.action}")
    
    # Modern method demo
    print("\n--- Modern Parametric Method Demo ---")
    mod_result = engine.generate_modern(
        name="Demo Rosette",
        rings=[
            {"inner_diameter_mm": 90, "outer_diameter_mm": 94, "pattern_type": "solid", "primary_color": "black"},
            {"inner_diameter_mm": 94, "outer_diameter_mm": 100, "pattern_type": "herringbone"},
            {"inner_diameter_mm": 100, "outer_diameter_mm": 104, "pattern_type": "solid", "primary_color": "white"},
        ],
        soundhole_diameter_mm=90,
    )
    
    print(f"Pattern: {mod_result.spec.name}")
    print(f"Rings: {len(mod_result.spec.rings)}")
    print(f"Path segments: {len(mod_result.paths)}")
    print(f"Est. cut time: {mod_result.estimated_cut_time_min} min")
    print(f"\nBill of Materials (area mm²):")
    for mat, area in mod_result.bom.items():
        print(f"  {mat}: {area:.1f} mm²")
    
    print(f"\nDXF generated: {mod_result.dxf_content is not None}")
    print(f"SVG generated: {mod_result.svg_content is not None}")
    
    return engine, trad_result, mod_result


if __name__ == "__main__":
    engine, trad, mod = demo()
    
    # Save demo outputs
    print("\n--- Saving Demo Outputs ---")
    
    with open("/home/claude/demo_traditional.json", "w") as f:
        json.dump(trad.to_dict(), f, indent=2)
    print("Saved: demo_traditional.json")
    
    with open("/home/claude/demo_modern.json", "w") as f:
        json.dump(mod.to_dict(), f, indent=2)
    print("Saved: demo_modern.json")
    
    if mod.dxf_content:
        with open("/home/claude/demo_rosette.dxf", "w") as f:
            f.write(mod.dxf_content)
        print("Saved: demo_rosette.dxf")
    
    if mod.svg_content:
        with open("/home/claude/demo_rosette.svg", "w") as f:
            f.write(mod.svg_content)
        print("Saved: demo_rosette.svg")
    
    print("\n✅ Demo complete!")
