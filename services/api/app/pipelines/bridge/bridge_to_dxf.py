"""
Bridge Saddle Compensation DXF Generator
Migrated from: server/pipelines/bridge/bridge_to_dxf.py
Status: Medium Priority Pipeline

Creates DXF drawings (R12-R18) from bridge saddle compensation JSON:
- SADDLE_LINE layer: Compensated saddle positions per string
- SLOT_RECTANGLE layer: Bridge slot rectangles
- NUT_REFERENCE layer: Nut reference line
- SCALE_REFERENCE layer: Scale length reference
- DIMENSIONS layer: String spacing and annotations

Dependencies: ezdxf
"""
import json
from pathlib import Path
from ...util.dxf_compat import (
    create_document, add_polyline, add_rectangle,
    validate_version, DxfVersion
)


def create_dxf(
    model: dict,
    output_path: str | Path,
    dxf_version: DxfVersion = 'R12'
) -> None:
    """
    Generate DXF from saddle compensation model.
    
    Args:
        model: Dictionary with keys:
            - scale_length_mm: Scale length in mm
            - nut_width_mm: Nut width
            - saddle_offset_mm: Base saddle offset from scale
            - strings: List of dicts with 'name', 'x_mm', 'y_compensation_mm'
        output_path: Where to write the DXF file
        dxf_version: DXF version R12-R18 (default R12 for CAM compatibility)
    """
    # Validate version (R12 is the genesis of Luthier's ToolBox)
    version = validate_version(dxf_version)
    doc = create_document(version)
    msp = doc.modelspace()

    # Define layers
    layers = [
        ('SADDLE_LINE', 1),       # Red - compensated saddle line
        ('SLOT_RECTANGLE', 3),   # Green - bridge slot
        ('NUT_REFERENCE', 5),    # Blue - nut reference
        ('SCALE_REFERENCE', 7),  # White - scale length ref
        ('DIMENSIONS', 8),       # Gray - annotations
    ]
    for layer_name, color in layers:
        doc.layers.add(name=layer_name, color=color)

    scale_length = model.get('scale_length_mm', 650.0)
    nut_width = model.get('nut_width_mm', 43.0)
    saddle_offset = model.get('saddle_offset_mm', 2.0)
    strings = model.get('strings', [])

    if not strings:
        # Default 6-string if not specified
        strings = [
            {'name': 'E6', 'x_mm': 0.0, 'y_compensation_mm': 2.5},
            {'name': 'A', 'x_mm': 7.5, 'y_compensation_mm': 2.0},
            {'name': 'D', 'x_mm': 15.0, 'y_compensation_mm': 1.8},
            {'name': 'G', 'x_mm': 22.5, 'y_compensation_mm': 1.5},
            {'name': 'B', 'x_mm': 30.0, 'y_compensation_mm': 1.2},
            {'name': 'E1', 'x_mm': 37.5, 'y_compensation_mm': 1.0},
        ]

    # Calculate bounding box
    x_min = min(s['x_mm'] for s in strings) - 5.0
    x_max = max(s['x_mm'] for s in strings) + 5.0
    
    # --- Nut reference line ---
    msp.add_line(
        (x_min, 0),
        (x_max, 0),
        dxfattribs={'layer': 'NUT_REFERENCE'}
    )

    # --- Scale length reference line ---
    msp.add_line(
        (x_min, scale_length),
        (x_max, scale_length),
        dxfattribs={'layer': 'SCALE_REFERENCE'}
    )

    # --- Saddle compensation points and line ---
    saddle_points = []
    for s in strings:
        x = s['x_mm']
        y_base = scale_length + saddle_offset
        y_comp = y_base + s['y_compensation_mm']
        saddle_points.append((x, y_comp))
        
        # Mark each saddle point
        msp.add_circle(
            (x, y_comp),
            radius=0.5,
            dxfattribs={'layer': 'SADDLE_LINE'}
        )
        
        # Add string label
        msp.add_text(
            s['name'],
            dxfattribs={
                'layer': 'DIMENSIONS',
                'height': 2.0,
                'insert': (x - 1, y_comp + 3),
            }
        )

    # Connect saddle points (version-aware: LINE for R12, LWPOLYLINE for R13+)
    if len(saddle_points) >= 2:
        add_polyline(msp, saddle_points, layer='SADDLE_LINE', closed=False, version=version)

    # --- Bridge slot rectangle ---
    slot_width = x_max - x_min + 6.0  # 3mm margin each side
    slot_height = 3.0  # Standard 3mm slot width
    slot_y = scale_length + saddle_offset - slot_height / 2
    
    # Draw slot rectangle (version-aware)
    add_rectangle(
        msp,
        x_min - 3, slot_y,
        x_max + 3, slot_y + slot_height,
        layer='SLOT_RECTANGLE',
        version=version
    )

    # --- Dimension annotations ---
    # Scale length dimension
    msp.add_text(
        f"Scale: {scale_length:.1f}mm",
        dxfattribs={
            'layer': 'DIMENSIONS',
            'height': 3.0,
            'insert': (x_max + 10, scale_length / 2),
        }
    )
    
    # Nut width dimension
    msp.add_text(
        f"Nut: {nut_width:.1f}mm",
        dxfattribs={
            'layer': 'DIMENSIONS',
            'height': 2.5,
            'insert': (x_max + 10, 5),
        }
    )

    # String spacing
    if len(strings) >= 2:
        first_x = strings[0]['x_mm']
        last_x = strings[-1]['x_mm']
        spacing = last_x - first_x
        msp.add_text(
            f"String Spread: {spacing:.1f}mm",
            dxfattribs={
                'layer': 'DIMENSIONS',
                'height': 2.5,
                'insert': (x_max + 10, scale_length + saddle_offset + 10),
            }
        )

    # Save DXF
    doc.saveas(str(output_path))
    print(f"DXF saved to: {output_path}")


def load_model(json_path: str | Path) -> dict:
    """Load saddle compensation model from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)


# CLI entry point
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bridge_to_dxf.py <model.json> [output.dxf]")
        print("\nExample JSON structure:")
        print(json.dumps({
            "scale_length_mm": 650.0,
            "nut_width_mm": 43.0,
            "saddle_offset_mm": 2.0,
            "strings": [
                {"name": "E6", "x_mm": 0.0, "y_compensation_mm": 2.5},
                {"name": "A", "x_mm": 7.5, "y_compensation_mm": 2.0},
            ]
        }, indent=2))
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    output_path = sys.argv[2] if len(sys.argv) > 2 else json_path.with_suffix('.dxf')
    
    model = load_model(json_path)
    create_dxf(model, output_path)
