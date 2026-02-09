"""Rosette Pattern Generator — Combined Traditional + Modern Methods."""

from __future__ import annotations

import math
from typing import List, Dict, Optional, Any

# Re-export all public types for backward compatibility.
# Consumers that import from pattern_generator continue to work.
from .pattern_schemas import (  # noqa: F401
    PatternType,
    MaterialType,
    OutputFormat,
    MatrixFormula,
    StripCutList,
    AssemblyInstruction,
    TraditionalPatternResult,
    RingSpec,
    RosetteSpec,
    Point2D,
    PathSegment,
    ModernPatternResult,
)
from .presets import PRESET_MATRICES  # noqa: F401

# WP-3: Modern generator extracted to its own module
from .modern_pattern_generator import ModernPatternGenerator as ModernPatternGenerator  # noqa: F401

# ============================================================================
# TRADITIONAL METHOD GENERATOR
# ============================================================================

class TraditionalPatternGenerator:
    """Generator for traditional matrix-based rope patterns."""
    
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
# UNIFIED API - Combines Both Methods
# ============================================================================

class RosettePatternEngine:
    """Unified engine for rosette pattern generation."""
    
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
        """Generate pattern using traditional matrix method."""
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
        """Generate pattern using modern parametric method."""
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


