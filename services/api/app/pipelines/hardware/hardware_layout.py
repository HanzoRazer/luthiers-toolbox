"""
Hardware Cavity DXF Generator
Migrated from: server/pipelines/hardware/hardware_layout.py
Status: Medium Priority Pipeline

Generates DXF drawings for hardware mounting cavities:
- Tuner holes (circles)
- Control cavities (rectangles)
- Pickup routes (rectangles)
- Bridge mounts (rectangles)

Note: Uses raw DXF output format for simplicity.
For production use, consider migrating to ezdxf.
"""
import json
from pathlib import Path
from typing import List, Dict, Any


def circle(x: float, y: float, r: float, layer: str = "0") -> str:
    """Generate DXF CIRCLE entity."""
    return f"""0
CIRCLE
8
{layer}
10
{x:.4f}
20
{y:.4f}
40
{r:.4f}
"""


def rectangle(x: float, y: float, w: float, h: float, layer: str = "0") -> str:
    """Generate DXF LWPOLYLINE rectangle entity."""
    # Rectangle corners
    x1, y1 = x, y
    x2, y2 = x + w, y + h
    
    return f"""0
LWPOLYLINE
8
{layer}
90
4
70
1
10
{x1:.4f}
20
{y1:.4f}
10
{x2:.4f}
20
{y1:.4f}
10
{x2:.4f}
20
{y2:.4f}
10
{x1:.4f}
20
{y2:.4f}
"""


def header() -> str:
    """DXF R12 header."""
    return """0
SECTION
2
HEADER
9
$ACADVER
1
AC1009
9
$INSUNITS
70
4
0
ENDSEC
0
SECTION
2
ENTITIES
"""


def footer() -> str:
    """DXF footer."""
    return """0
ENDSEC
0
EOF
"""


def generate_dxf(hardware_items: List[Dict[str, Any]]) -> str:
    """
    Generate DXF content from hardware layout specification.
    
    Args:
        hardware_items: List of hardware items with structure:
            {
                "type": "circle" | "rectangle",
                "x": float,  # Center X for circle, corner X for rectangle
                "y": float,  # Center Y for circle, corner Y for rectangle
                "r": float,  # Radius (circle only)
                "w": float,  # Width (rectangle only)
                "h": float,  # Height (rectangle only)
                "layer": str  # Optional layer name
            }
    
    Returns:
        DXF file content as string
    """
    dxf = header()
    
    for item in hardware_items:
        layer = item.get('layer', '0')
        item_type = item.get('type', 'circle')
        
        if item_type == 'circle':
            dxf += circle(
                item['x'],
                item['y'],
                item['r'],
                layer
            )
        elif item_type == 'rectangle':
            dxf += rectangle(
                item['x'],
                item['y'],
                item['w'],
                item['h'],
                layer
            )
    
    dxf += footer()
    return dxf


def run(inp_path: str | Path, out_dir: str | Path) -> Path:
    """
    Process hardware layout JSON and generate DXF.
    
    Args:
        inp_path: Path to JSON file with hardware specifications
        out_dir: Output directory for DXF file
    
    Returns:
        Path to generated DXF file
    """
    inp_path = Path(inp_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load hardware spec
    with open(inp_path, 'r') as f:
        spec = json.load(f)
    
    hardware_items = spec.get('hardware', [])
    
    # Generate DXF
    dxf_content = generate_dxf(hardware_items)
    
    # Write output
    out_path = out_dir / f"{inp_path.stem}_hardware.dxf"
    with open(out_path, 'w') as f:
        f.write(dxf_content)
    
    print(f"Generated: {out_path}")
    print(f"  Items: {len(hardware_items)}")
    
    return out_path


# CLI entry point
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python hardware_layout.py <spec.json> <output_dir>")
        print("\nExample JSON structure:")
        print(json.dumps({
            "hardware": [
                {"type": "circle", "x": 0, "y": 0, "r": 5, "layer": "TUNERS"},
                {"type": "rectangle", "x": 10, "y": 10, "w": 50, "h": 30, "layer": "CAVITIES"}
            ]
        }, indent=2))
        sys.exit(1)
    
    run(sys.argv[1], sys.argv[2])
