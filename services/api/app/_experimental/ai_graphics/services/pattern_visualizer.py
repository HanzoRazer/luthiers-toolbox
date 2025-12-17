#!/usr/bin/env python3
"""
Spanish Mosaic Rosette Pattern Visualizer

Shows the ACTUAL physical construction:
- Each cell is a 1mm wood strip
- Strips stack vertically per row formula
- Sticks are sliced into chips
- Chips arranged per column sequence

This is TEACHING software - shows how to build it.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class PatternDimensions:
    """Physical dimensions of the assembled pattern."""
    strip_width_mm: float      # Width of each veneer strip
    strip_thickness_mm: float  # Thickness of veneer
    chip_length_mm: float      # Length when sliced (becomes width in pattern)
    
    row_count: int
    column_count: int
    max_strips_per_row: int
    
    @property
    def pattern_height_mm(self) -> float:
        """Height = max strips in any row × strip thickness"""
        return self.max_strips_per_row * self.strip_thickness_mm
    
    @property
    def pattern_width_mm(self) -> float:
        """Width = number of columns × chip length"""
        return self.column_count * self.chip_length_mm
    
    def __str__(self) -> str:
        return (
            f"Pattern: {self.pattern_width_mm:.1f}mm × {self.pattern_height_mm:.1f}mm\n"
            f"  {self.column_count} chips @ {self.chip_length_mm}mm = {self.pattern_width_mm:.1f}mm wide\n"
            f"  {self.max_strips_per_row} strips @ {self.strip_thickness_mm}mm = {self.pattern_height_mm:.1f}mm tall"
        )


def calculate_dimensions(formula: Dict) -> PatternDimensions:
    """Calculate physical dimensions from formula."""
    rows = formula.get('rows', [])
    col_seq = formula.get('column_sequence', [])
    
    max_strips = max(sum(row.values()) for row in rows) if rows else 0
    
    return PatternDimensions(
        strip_width_mm=formula.get('strip_width_mm', 1.0),
        strip_thickness_mm=formula.get('strip_thickness_mm', 0.6),
        chip_length_mm=formula.get('chip_length_mm', 1.6),
        row_count=len(rows),
        column_count=len(col_seq),
        max_strips_per_row=max_strips,
    )


def build_chip_grid(formula: Dict) -> List[List[str]]:
    """
    Build the actual chip grid showing material at each position.
    
    Returns 2D grid where:
    - Outer list = columns (left to right)
    - Inner list = strips in that column (bottom to top)
    - Values are material names ('black', 'white', etc.)
    """
    rows = formula.get('rows', [])
    col_seq = formula.get('column_sequence', [])
    
    grid = []
    
    for col_idx in col_seq:
        # col_idx is 1-indexed row reference
        row_formula = rows[col_idx - 1]  # Convert to 0-indexed
        
        # Build this column's strip stack (bottom to top)
        column_strips = []
        
        # Stack materials in consistent order for alignment
        for material in ['black', 'brown', 'white', 'natural']:
            count = row_formula.get(material, 0)
            column_strips.extend([material] * count)
        
        grid.append(column_strips)
    
    return grid


def render_ascii_pattern(formula: Dict, show_grid: bool = True) -> str:
    """
    Render the pattern as ASCII art showing actual chip arrangement.
    """
    grid = build_chip_grid(formula)
    dims = calculate_dimensions(formula)
    col_seq = formula.get('column_sequence', [])
    
    # Material symbols
    symbols = {
        'black': '███',
        'white': '░░░',
        'brown': '▓▓▓',
        'natural': '···',
    }
    
    lines = []
    lines.append("=" * 60)
    lines.append("ASSEMBLED PATTERN - What You'll See When Done")
    lines.append("=" * 60)
    lines.append(f"\n{dims}\n")
    
    # Column headers (row references)
    header = "     "
    for ref in col_seq:
        header += f" R{ref} "
    lines.append(header)
    
    # Find max height (strips) across all columns
    max_height = max(len(col) for col in grid)
    
    # Top border
    border = "    ┌" + "───┬" * (len(grid) - 1) + "───┐"
    lines.append(border)
    
    # Render rows from top to bottom
    for row_idx in range(max_height - 1, -1, -1):
        row_str = "    │"
        for col in grid:
            if row_idx < len(col):
                material = col[row_idx]
                row_str += symbols.get(material, '???') + "│"
            else:
                row_str += "   │"  # Empty cell (padding)
        lines.append(row_str)
    
    # Bottom border
    border = "    └" + "───┴" * (len(grid) - 1) + "───┘"
    lines.append(border)
    
    # Legend
    lines.append("\n    Legend: ███=black  ░░░=white  ▓▓▓=brown")
    lines.append(f"    Scale: Each cell ≈ {dims.chip_length_mm}mm × {dims.strip_thickness_mm}mm")
    
    return "\n".join(lines)


def render_assembly_guide(formula: Dict) -> str:
    """
    Generate step-by-step assembly instructions with visuals.
    This TEACHES the user how to build the pattern.
    """
    rows = formula.get('rows', [])
    col_seq = formula.get('column_sequence', [])
    dims = calculate_dimensions(formula)
    name = formula.get('name', 'Pattern')
    
    symbols = {'black': '█', 'white': '░', 'brown': '▓', 'natural': '·'}
    
    lines = []
    lines.append("=" * 70)
    lines.append(f"ASSEMBLY GUIDE: {name}")
    lines.append("=" * 70)
    lines.append(f"\nFinal size: {dims.pattern_width_mm:.1f}mm wide × {dims.pattern_height_mm:.1f}mm tall")
    lines.append("(This is TINY - about the size of your fingernail)\n")
    
    # =========================================================================
    # STEP 1: Materials needed
    # =========================================================================
    lines.append("─" * 70)
    lines.append("STEP 1: PREPARE VENEER STRIPS")
    lines.append("─" * 70)
    
    # Calculate totals
    totals = {}
    for row in rows:
        for mat, count in row.items():
            totals[mat] = totals.get(mat, 0) + count
    
    lines.append(f"\nCut strips {dims.strip_width_mm}mm wide × 300mm long:\n")
    for mat, count in totals.items():
        lines.append(f"  • {mat.upper()}: {count} strips (cut {int(count * 1.15)} for waste)")
    
    # =========================================================================
    # STEP 2: Build sticks
    # =========================================================================
    lines.append("\n" + "─" * 70)
    lines.append("STEP 2: GLUE STRIPS INTO STICKS (one stick per row)")
    lines.append("─" * 70)
    
    for i, row in enumerate(rows, 1):
        lines.append(f"\n  STICK #{i} (Row {i}):")
        
        # Show strip stack
        strip_line = "    Stack (bottom to top): "
        stack_vis = "    "
        
        stack = []
        for mat in ['black', 'brown', 'white', 'natural']:
            count = row.get(mat, 0)
            if count > 0:
                stack.append(f"{count}× {mat}")
                stack_vis += symbols.get(mat, '?') * count
        
        lines.append(strip_line + " + ".join(stack))
        lines.append(f"    Visual: [{stack_vis}] ({sum(row.values())} strips tall)")
    
    lines.append("\n  ⚠️  Let glue dry COMPLETELY before slicing (24 hours)")
    
    # =========================================================================
    # STEP 3: Slice into chips
    # =========================================================================
    lines.append("\n" + "─" * 70)
    lines.append("STEP 3: SLICE STICKS INTO CHIPS")
    lines.append("─" * 70)
    lines.append(f"\n  Cut each stick into chips {dims.chip_length_mm}mm thick")
    lines.append("  Use a fine-tooth saw or veneer saw")
    lines.append("  You'll need these chips:\n")
    
    # Count how many chips needed from each stick
    chip_counts = {}
    for ref in col_seq:
        chip_counts[ref] = chip_counts.get(ref, 0) + 1
    
    for stick_num, count in sorted(chip_counts.items()):
        lines.append(f"    Stick #{stick_num}: cut {count} chips")
    
    # =========================================================================
    # STEP 4: Arrange per sequence
    # =========================================================================
    lines.append("\n" + "─" * 70)
    lines.append("STEP 4: ARRANGE CHIPS IN SEQUENCE")
    lines.append("─" * 70)
    lines.append(f"\n  Column sequence (left to right):\n")
    
    seq_str = "    "
    for i, ref in enumerate(col_seq):
        seq_str += f"[{ref}]"
        if i < len(col_seq) - 1:
            seq_str += "─"
    lines.append(seq_str)
    
    lines.append("\n    ↑ Each number = which stick's chip to place")
    lines.append("\n  Lay chips flat, edges touching, in this exact order.")
    lines.append("  Apply thin glue between chips. Clamp lightly.")
    
    # =========================================================================
    # STEP 5: Final result
    # =========================================================================
    lines.append("\n" + "─" * 70)
    lines.append("STEP 5: FINAL PATTERN STRIP")
    lines.append("─" * 70)
    
    # Show the actual pattern
    lines.append("\n" + render_ascii_pattern(formula, show_grid=False))
    
    lines.append("\n" + "─" * 70)
    lines.append("NEXT: Slice this strip into segments to wrap around your rosette channel")
    lines.append("─" * 70)
    
    return "\n".join(lines)


def render_svg_pattern(formula: Dict, scale: float = 10.0) -> str:
    """
    Render pattern as SVG showing actual chip colors.
    
    Args:
        formula: Matrix formula dict
        scale: Pixels per mm (10 = 10px per mm)
    
    Returns:
        SVG string
    """
    grid = build_chip_grid(formula)
    dims = calculate_dimensions(formula)
    col_seq = formula.get('column_sequence', [])
    name = formula.get('name', 'Pattern')
    
    # Colors for materials
    colors = {
        'black': '#1a1a1a',
        'white': '#f5f0e6',
        'brown': '#8b4513',
        'natural': '#deb887',
    }
    
    # Calculate SVG dimensions
    max_height = max(len(col) for col in grid)
    
    chip_w = dims.chip_length_mm * scale
    strip_h = dims.strip_thickness_mm * scale
    
    svg_width = len(grid) * chip_w + 40  # margins
    svg_height = max_height * strip_h + 80  # margins + labels
    
    # Start SVG
    svg = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg"',
        f'     viewBox="0 0 {svg_width} {svg_height}"',
        f'     width="{svg_width}px" height="{svg_height}px">',
        f'  <title>{name}</title>',
        f'  <desc>Spanish mosaic rosette pattern - {dims.pattern_width_mm:.1f}mm × {dims.pattern_height_mm:.1f}mm</desc>',
        f'',
        f'  <!-- Background -->',
        f'  <rect width="100%" height="100%" fill="#f8f8f8"/>',
        f'',
        f'  <!-- Title -->',
        f'  <text x="{svg_width/2}" y="20" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">{name}</text>',
        f'  <text x="{svg_width/2}" y="38" text-anchor="middle" font-family="Arial" font-size="11" fill="#666">',
        f'    {dims.pattern_width_mm:.1f}mm × {dims.pattern_height_mm:.1f}mm (actual size)',
        f'  </text>',
        f'',
        f'  <!-- Pattern grid -->',
        f'  <g transform="translate(20, 50)">',
    ]
    
    # Draw chips
    for col_idx, column in enumerate(grid):
        x = col_idx * chip_w
        
        for strip_idx, material in enumerate(column):
            # Y from bottom (flip coordinate)
            y = (max_height - strip_idx - 1) * strip_h
            
            color = colors.get(material, '#cccccc')
            
            svg.append(
                f'    <rect x="{x}" y="{y}" width="{chip_w}" height="{strip_h}" '
                f'fill="{color}" stroke="#333" stroke-width="0.5"/>'
            )
    
    # Column labels (row references)
    svg.append(f'')
    svg.append(f'    <!-- Column labels -->')
    for col_idx, ref in enumerate(col_seq):
        x = col_idx * chip_w + chip_w / 2
        y = max_height * strip_h + 15
        svg.append(
            f'    <text x="{x}" y="{y}" text-anchor="middle" '
            f'font-family="Arial" font-size="9" fill="#666">R{ref}</text>'
        )
    
    svg.append(f'  </g>')
    
    # Legend
    legend_y = svg_height - 20
    svg.append(f'')
    svg.append(f'  <!-- Legend -->')
    svg.append(f'  <g transform="translate(20, {legend_y})">')
    
    x = 0
    for mat, color in colors.items():
        if any(mat in row for row in formula.get('rows', [])):
            svg.append(f'    <rect x="{x}" y="-8" width="12" height="12" fill="{color}" stroke="#333" stroke-width="0.5"/>')
            svg.append(f'    <text x="{x + 16}" y="2" font-family="Arial" font-size="10">{mat}</text>')
            x += 60
    
    svg.append(f'  </g>')
    svg.append(f'</svg>')
    
    return '\n'.join(svg)


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demo the visualizer with a Torres pattern."""
    
    formula = {
        'name': 'Torres Diamond Pattern',
        'rows': [
            {'black': 1, 'white': 5},
            {'black': 2, 'white': 4},
            {'black': 3, 'white': 3},
            {'black': 4, 'white': 2},
            {'black': 3, 'white': 3},
            {'black': 2, 'white': 4},
            {'black': 1, 'white': 5},
        ],
        'column_sequence': [1, 2, 3, 4, 5, 6, 7, 6, 5],
        'strip_width_mm': 0.7,
        'strip_thickness_mm': 0.6,
        'chip_length_mm': 1.6,
    }
    
    # Show ASCII pattern
    print(render_ascii_pattern(formula))
    
    # Show assembly guide
    print("\n\n")
    print(render_assembly_guide(formula))
    
    # Generate SVG
    svg = render_svg_pattern(formula, scale=15)
    with open('pattern_preview.svg', 'w') as f:
        f.write(svg)
    print("\n\n✅ Saved: pattern_preview.svg")
    
    return formula


if __name__ == "__main__":
    demo()
