"""
Rosette DXF Generator (Minimal)
Migrated from: server/pipelines/rosette/rosette_to_dxf.py
Status: Medium Priority Pipeline

Generates minimal DXF with soundhole and channel outline circles.
Uses raw DXF format for simplicity and zero dependencies.

For production use with complex rosettes, consider ezdxf-based version.
"""
from typing import Optional


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


def generate_rosette_dxf(
    soundhole_r: float,
    channel_inner_r: float,
    channel_outer_r: float,
    center_x: float = 0.0,
    center_y: float = 0.0,
    purfling_rings: Optional[list] = None,
) -> str:
    """
    Generate DXF content for rosette outline.
    
    Args:
        soundhole_r: Soundhole radius (mm)
        channel_inner_r: Inner edge of rosette channel (mm)
        channel_outer_r: Outer edge of rosette channel (mm)
        center_x: Center X coordinate
        center_y: Center Y coordinate
        purfling_rings: Optional list of additional ring radii (mm)
    
    Returns:
        DXF file content as string
    """
    dxf = header()
    
    # Soundhole circle
    dxf += circle(center_x, center_y, soundhole_r, "SOUNDHOLE")
    
    # Channel inner edge
    dxf += circle(center_x, center_y, channel_inner_r, "CHANNEL_INNER")
    
    # Channel outer edge
    dxf += circle(center_x, center_y, channel_outer_r, "CHANNEL_OUTER")
    
    # Optional purfling rings
    if purfling_rings:
        for i, r in enumerate(purfling_rings):
            dxf += circle(center_x, center_y, r, f"PURFLING_{i+1}")
    
    dxf += footer()
    return dxf


def save_rosette_dxf(
    output_path: str,
    soundhole_r: float,
    channel_inner_r: float,
    channel_outer_r: float,
    **kwargs
) -> None:
    """
    Generate and save rosette DXF file.
    
    Args:
        output_path: Where to write the DXF
        soundhole_r: Soundhole radius (mm)
        channel_inner_r: Inner channel radius (mm)
        channel_outer_r: Outer channel radius (mm)
        **kwargs: Additional args passed to generate_rosette_dxf
    """
    dxf_content = generate_rosette_dxf(
        soundhole_r=soundhole_r,
        channel_inner_r=channel_inner_r,
        channel_outer_r=channel_outer_r,
        **kwargs
    )
    
    with open(output_path, 'w') as f:
        f.write(dxf_content)
    
    print(f"Wrote: {output_path}")
    print(f"  Soundhole: R={soundhole_r}mm")
    print(f"  Channel: {channel_inner_r}-{channel_outer_r}mm")


# CLI entry point
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python rosette_to_dxf.py <soundhole_r> <channel_inner_r> <channel_outer_r> [output.dxf]")
        print("\nExample:")
        print("  python rosette_to_dxf.py 50 52 62 rosette.dxf")
        sys.exit(1)
    
    soundhole_r = float(sys.argv[1])
    channel_inner_r = float(sys.argv[2])
    channel_outer_r = float(sys.argv[3])
    output_path = sys.argv[4] if len(sys.argv) > 4 else "rosette.dxf"
    
    save_rosette_dxf(output_path, soundhole_r, channel_inner_r, channel_outer_r)
