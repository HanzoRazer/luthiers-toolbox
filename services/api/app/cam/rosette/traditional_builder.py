#!/usr/bin/env python3
"""Traditional Rosette Builder Interface"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import json

from .pattern_generator import (
    MatrixFormula,
    TraditionalPatternGenerator,
    TraditionalPatternResult,
    RosettePatternEngine,
    PRESET_MATRICES,
)
from .pattern_renderer import PatternRenderer, RenderConfig

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class WoodSpecies(str, Enum):
    """Common veneer species for rosette work."""
    # Dark woods
    EBONY = "ebony"
    ROSEWOOD = "rosewood"
    WALNUT = "walnut"
    WENGE = "wenge"

    # Light woods
    HOLLY = "holly"
    MAPLE = "maple"
    SPRUCE = "spruce"
    BOXWOOD = "boxwood"

    # Medium/colored woods
    MAHOGANY = "mahogany"
    CHERRY = "cherry"
    PADAUK = "padauk"
    PURPLEHEART = "purpleheart"

    # Dyed veneers
    DYED_BLACK = "dyed_black"
    DYED_RED = "dyed_red"
    DYED_GREEN = "dyed_green"
    DYED_BLUE = "dyed_blue"


@dataclass
class VeneerStock:
    """Represents veneer material in the shop."""
    species: str
    thickness_mm: float = 0.6
    available_length_mm: float = 300.0
    available_width_mm: float = 100.0
    notes: Optional[str] = None


@dataclass
class CutList:
    """
    Traditional cut list for the shop.

    Lists exactly what strips to cut from each veneer species.
    """
    species: str
    num_strips: int
    strip_width_mm: float
    strip_length_mm: float
    strip_thickness_mm: float

    @property
    def total_length_mm(self) -> float:
        """Total veneer length needed (with waste)."""
        return self.num_strips * self.strip_width_mm * 1.15  # 15% waste

    def __str__(self) -> str:
        return (
            f"{self.species.upper():12} "
            f"{self.num_strips:3}× strips @ "
            f"{self.strip_width_mm:.1f}mm wide × "
            f"{self.strip_length_mm:.0f}mm long"
        )


@dataclass
class StickDefinition:
    """
    Definition of one stick (glued strip assembly).

    In traditional method, each row of the matrix becomes one stick.
    """
    stick_number: int  # 1-indexed for craftsmen
    strips: List[Tuple[str, int]]  # [(species, count), ...]
    total_strips: int

    def __str__(self) -> str:
        parts = [f"{count}× {species}" for species, count in self.strips]
        return f"Stick {self.stick_number}: {', '.join(parts)} ({self.total_strips} total)"


@dataclass
class AssemblySequence:
    """
    The chip assembly sequence.

    This is the heart of the traditional method - the order in which
    chips from different sticks are arranged to create the pattern.
    """
    sequence: List[int]  # Stick numbers in assembly order
    description: str

    def __str__(self) -> str:
        seq_str = " - ".join(str(s) for s in self.sequence)
        return f"Assembly: {seq_str}"

    @property
    def pattern_width_chips(self) -> int:
        return len(self.sequence)


@dataclass
class TraditionalProject:
    """
    A complete traditional rosette project.

    Contains everything a craftsman needs:
    - Pattern name and history
    - Cut list for the shop
    - Stick definitions
    - Assembly sequence
    - Step-by-step instructions
    """
    name: str
    master_attribution: Optional[str]  # "Torres", "Hauser", etc.
    description: str

    # Materials
    cut_list: List[CutList]
    stick_definitions: List[StickDefinition]
    assembly_sequence: AssemblySequence

    # Dimensions
    strip_width_mm: float
    strip_thickness_mm: float
    chip_length_mm: float

    # Instructions
    instructions: List[str]

    # Metadata
    difficulty: str = "Intermediate"  # Beginner, Intermediate, Advanced, Master
    estimated_time_hours: float = 4.0
    notes: List[str] = field(default_factory=list)

    def print_project_sheet(self) -> str:
        """Generate a printable project sheet."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"ROSETTE PROJECT: {self.name}")
        if self.master_attribution:
            lines.append(f"Style: {self.master_attribution}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(self.description)
        lines.append("")

        lines.append("-" * 40)
        lines.append("MATERIALS - CUT LIST")
        lines.append("-" * 40)
        for item in self.cut_list:
            lines.append(f"  {item}")
        lines.append("")

        lines.append("-" * 40)
        lines.append("STICK DEFINITIONS")
        lines.append("-" * 40)
        for stick in self.stick_definitions:
            lines.append(f"  {stick}")
        lines.append("")

        lines.append("-" * 40)
        lines.append("ASSEMBLY SEQUENCE")
        lines.append("-" * 40)
        lines.append(f"  {self.assembly_sequence}")
        lines.append(f"  Pattern width: {self.assembly_sequence.pattern_width_chips} chips")
        lines.append("")

        lines.append("-" * 40)
        lines.append("ASSEMBLY INSTRUCTIONS")
        lines.append("-" * 40)
        for i, step in enumerate(self.instructions, 1):
            lines.append(f"  {i}. {step}")
        lines.append("")

        if self.notes:
            lines.append("-" * 40)
            lines.append("NOTES")
            lines.append("-" * 40)
            for note in self.notes:
                lines.append(f"  • {note}")

        lines.append("")
        lines.append(f"Difficulty: {self.difficulty}")
        lines.append(f"Estimated time: {self.estimated_time_hours:.1f} hours")
        lines.append("=" * 60)

        return "\n".join(lines)


class TraditionalBuilder:
    """
    Traditional rosette builder interface.

    Provides a craftsman-friendly way to work with rosette patterns,
    using terminology and workflow familiar to traditional luthiers.
    """

    def __init__(self):
        self.engine = RosettePatternEngine()
        self._renderer = None

    @property
    def renderer(self) -> PatternRenderer:
        """Lazy-load renderer (requires PIL)."""
        if self._renderer is None:
            self._renderer = PatternRenderer()
        return self._renderer

    def list_master_patterns(self) -> Dict[str, List[str]]:
        """
        List patterns organized by master luthier.

        Returns dict like:
        {
            "Torres": ["torres_simple_rope_4x7", "torres_diamond_7x9", ...],
            "Hauser": ["hauser_rope_6x11", ...],
            ...
        }
        """
        masters = {
            "Torres": [],
            "Hauser": [],
            "Romanillos": [],
            "Fleta": [],
            "Bouchet": [],
            "Simplicio": [],
            "Traditional": [],
            "Modern": [],
        }

        for key in PRESET_MATRICES.keys():
            if "torres" in key:
                masters["Torres"].append(key)
            elif "hauser" in key:
                masters["Hauser"].append(key)
            elif "romanillos" in key:
                masters["Romanillos"].append(key)
            elif "fleta" in key:
                masters["Fleta"].append(key)
            elif "bouchet" in key:
                masters["Bouchet"].append(key)
            elif "simplicio" in key:
                masters["Simplicio"].append(key)
            elif "modern" in key:
                masters["Modern"].append(key)
            else:
                masters["Traditional"].append(key)

        # Remove empty categories
        return {k: v for k, v in masters.items() if v}

    def get_pattern_info(self, pattern_id: str) -> Dict:
        """Get human-readable info about a pattern."""
        if pattern_id not in PRESET_MATRICES:
            raise ValueError(f"Unknown pattern: {pattern_id}")

        formula = PRESET_MATRICES[pattern_id]
        materials = list(formula.get_material_totals().keys())

        return {
            "id": pattern_id,
            "name": formula.name,
            "rows": formula.row_count,
            "columns": formula.column_count,
            "materials": materials,
            "strip_width_mm": formula.strip_width_mm,
            "strip_thickness_mm": formula.strip_thickness_mm,
            "chip_length_mm": formula.chip_length_mm,
            "notes": formula.notes,
        }

    def create_project(
        self,
        pattern_id: str,
        panel_length_mm: float = 300.0,
    ) -> TraditionalProject:
        """
        Create a complete traditional project from a pattern ID.

        This generates everything needed for the shop:
        - Cut list
        - Stick definitions
        - Assembly sequence
        - Step-by-step instructions
        """
        if pattern_id not in PRESET_MATRICES:
            raise ValueError(f"Unknown pattern: {pattern_id}")

        formula = PRESET_MATRICES[pattern_id]

        # Generate using the pattern generator
        generator = TraditionalPatternGenerator(formula)
        result = generator.generate(panel_length_mm=panel_length_mm)

        # Build cut list
        cut_list = []
        for item in result.cut_list:
            cut_list.append(CutList(
                species=item.material,
                num_strips=item.count,
                strip_width_mm=item.width_mm,
                strip_length_mm=item.length_mm,
                strip_thickness_mm=item.thickness_mm,
            ))

        # Build stick definitions
        stick_defs = []
        for i, row in enumerate(formula.rows, 1):
            strips = [(mat, count) for mat, count in row.items()]
            total = sum(count for _, count in strips)
            stick_defs.append(StickDefinition(
                stick_number=i,
                strips=strips,
                total_strips=total,
            ))

        # Assembly sequence
        assembly = AssemblySequence(
            sequence=list(formula.column_sequence),
            description=f"Arrange chips in this order to create the {formula.name} pattern",
        )

        # Build instructions
        instructions = [
            f"Cut strips {formula.strip_width_mm}mm wide from each veneer species",
            "Sort strips by species and count according to stick definitions",
        ]

        for stick in stick_defs:
            strip_desc = ", ".join(f"{count}× {species}" for species, count in stick.strips)
            instructions.append(f"Glue Stick {stick.stick_number}: {strip_desc}")

        instructions.extend([
            "Allow sticks to dry completely (minimum 2 hours, overnight preferred)",
            f"Slice each stick into chips approximately {formula.chip_length_mm}mm thick",
            f"Arrange chips according to sequence: {' - '.join(str(s) for s in formula.column_sequence)}",
            "Glue chips together to form the pattern laminate",
            "Allow laminate to dry, then sand smooth",
            "Slice laminate to desired ring width",
            "Bend carefully into rosette channel (steam if needed)",
        ])

        # Determine master attribution
        master = None
        for name in ["Torres", "Hauser", "Romanillos", "Fleta", "Bouchet", "Simplicio"]:
            if name.lower() in pattern_id.lower():
                master = name
                break

        # Determine difficulty
        total_strips = sum(item.num_strips for item in cut_list)
        if total_strips < 20:
            difficulty = "Beginner"
        elif total_strips < 40:
            difficulty = "Intermediate"
        elif total_strips < 60:
            difficulty = "Advanced"
        else:
            difficulty = "Master"

        return TraditionalProject(
            name=formula.name,
            master_attribution=master,
            description=formula.notes or f"Traditional {formula.name} rosette pattern",
            cut_list=cut_list,
            stick_definitions=stick_defs,
            assembly_sequence=assembly,
            strip_width_mm=formula.strip_width_mm,
            strip_thickness_mm=formula.strip_thickness_mm,
            chip_length_mm=formula.chip_length_mm,
            instructions=instructions,
            difficulty=difficulty,
            estimated_time_hours=2.0 + (total_strips * 0.05),
            notes=[
                "Work in a dust-free environment",
                "Use fresh, sharp blade for slicing chips",
                "Test fit in channel before final glue-up",
            ],
        )

    def render_pattern(
        self,
        pattern_id: str,
        as_ring: bool = False,
        num_repeats: int = 4,
    ) -> "Image.Image":
        """Render the actual pattern geometry."""
        return self.renderer.render_preset(
            pattern_id,
            as_ring=as_ring,
            num_repeats=num_repeats,
        )

    def save_project_sheet(
        self,
        project: TraditionalProject,
        output_path: str,
    ) -> str:
        """Save project sheet to text file."""
        with open(output_path, "w") as f:
            f.write(project.print_project_sheet())
        return output_path

    def create_custom_formula(
        self,
        name: str,
        rows: List[Dict[str, int]],
        column_sequence: List[int],
        strip_width_mm: float = 1.0,
        strip_thickness_mm: float = 0.6,
        chip_length_mm: float = 2.0,
        notes: Optional[str] = None,
    ) -> MatrixFormula:
        """Create a custom matrix formula."""
        formula = MatrixFormula(
            name=name,
            rows=rows,
            column_sequence=column_sequence,
            strip_width_mm=strip_width_mm,
            strip_thickness_mm=strip_thickness_mm,
            chip_length_mm=chip_length_mm,
            notes=notes,
        )

        # Validate
        errors = formula.validate()
        if errors:
            raise ValueError(f"Invalid formula: {'; '.join(errors)}")

        return formula


def demo():
    """Demonstrate traditional builder interface."""
    builder = TraditionalBuilder()

    print("=" * 60)
    print("TRADITIONAL ROSETTE BUILDER")
    print("For craftsmen who learned the old ways")
    print("=" * 60)

    # List patterns by master
    print("\nPatterns by Master Luthier:")
    for master, patterns in builder.list_master_patterns().items():
        print(f"\n  {master}:")
        for p in patterns[:3]:  # Show first 3
            info = builder.get_pattern_info(p)
            print(f"    • {info['name']} ({info['rows']}×{info['columns']})")

    # Create a project
    print("\n" + "=" * 60)
    project = builder.create_project("torres_diamond_7x9")
    print(project.print_project_sheet())

    return builder, project


if __name__ == "__main__":
    demo()
