"""
DXF Compatibility Layer - R12 through R18 Support
The genesis of Luthier's ToolBox: R12 doesn't support LWPOLYLINE.

This module provides version-aware DXF entity creation:
- R12: Uses LINE segments for polylines (maximum CAM compatibility)
- R13+: Can use LWPOLYLINE for closed paths

Supported versions: R12, R13, R14, R2000 (R15), R2004 (R16), R2007 (R17), R2010 (R18)
"""
from typing import List, Tuple, Literal, Optional
import ezdxf
from ezdxf.document import Drawing
from ezdxf.layouts import Modelspace

# Valid DXF versions (R12 through R18)
DXF_VERSIONS = {
    'R12': 'AC1009',    # AutoCAD R12 - the genesis
    'R13': 'AC1012',    # AutoCAD R13  
    'R14': 'AC1014',    # AutoCAD R14
    'R2000': 'AC1015',  # AutoCAD 2000 (R15)
    'R2004': 'AC1018',  # AutoCAD 2004 (R16)
    'R2007': 'AC1021',  # AutoCAD 2007 (R17)
    'R2010': 'AC1024',  # AutoCAD 2010 (R18)
}

# Versions that support LWPOLYLINE
LWPOLYLINE_VERSIONS = {'R13', 'R14', 'R2000', 'R2004', 'R2007', 'R2010'}

DxfVersion = Literal['R12', 'R13', 'R14', 'R2000', 'R2004', 'R2007', 'R2010']


def validate_version(version: str) -> DxfVersion:
    """
    Validate and normalize DXF version string.
    
    Args:
        version: Version string (R12, R13, R14, R2000, R2004, R2007, R2010)
                 Also accepts R15-R18 as aliases
    
    Returns:
        Normalized version string
        
    Raises:
        ValueError: If version not in R12-R18 range
    """
    # Normalize aliases
    aliases = {
        'R15': 'R2000',
        'R16': 'R2004', 
        'R17': 'R2007',
        'R18': 'R2010',
    }
    normalized = aliases.get(version.upper(), version.upper())
    
    if normalized not in DXF_VERSIONS:
        valid = ', '.join(sorted(DXF_VERSIONS.keys()))
        raise ValueError(f"Invalid DXF version '{version}'. Valid: {valid}")
    
    return normalized


def supports_lwpolyline(version: DxfVersion) -> bool:
    """Check if version supports LWPOLYLINE entity."""
    return version in LWPOLYLINE_VERSIONS


def create_document(version: DxfVersion = 'R12', setup: bool = False) -> Drawing:
    """
    Create a new DXF document with the specified version.
    
    Args:
        version: DXF version (R12-R18, default R12 for CAM compatibility)
        setup: Whether to setup default resources (only for R13+)
    
    Returns:
        ezdxf Drawing object
    """
    validated = validate_version(version)
    # R12 doesn't support setup=True
    if validated == 'R12':
        return ezdxf.new(validated)
    return ezdxf.new(validated, setup=setup)


def add_polyline(
    msp: Modelspace,
    points: List[Tuple[float, float]],
    layer: str = '0',
    closed: bool = False,
    version: DxfVersion = 'R12'
) -> None:
    """
    Add a polyline using version-appropriate entity.
    
    For R12: Uses LINE segments (the genesis approach)
    For R13+: Uses LWPOLYLINE
    
    Args:
        msp: Modelspace to add entities to
        points: List of (x, y) coordinate tuples
        layer: Layer name
        closed: Whether to close the polyline
        version: DXF version being used
    """
    if len(points) < 2:
        return
        
    validated = validate_version(version)
    
    if supports_lwpolyline(validated):
        # R13+ can use LWPOLYLINE
        msp.add_lwpolyline(
            points,
            dxfattribs={'layer': layer},
            close=closed
        )
    else:
        # R12: Use LINE segments (the genesis of Luthier's ToolBox)
        n = len(points)
        end = n if closed else n - 1
        for i in range(end):
            msp.add_line(
                points[i],
                points[(i + 1) % n],
                dxfattribs={'layer': layer}
            )


def add_rectangle(
    msp: Modelspace,
    x1: float, y1: float,
    x2: float, y2: float,
    layer: str = '0',
    version: DxfVersion = 'R12'
) -> None:
    """
    Add a rectangle using version-appropriate entity.
    
    Args:
        msp: Modelspace to add entities to
        x1, y1: Bottom-left corner
        x2, y2: Top-right corner
        layer: Layer name
        version: DXF version being used
    """
    corners = [
        (x1, y1),
        (x2, y1),
        (x2, y2),
        (x1, y2),
    ]
    add_polyline(msp, corners, layer=layer, closed=True, version=version)


def get_version_info(version: DxfVersion) -> dict:
    """
    Get information about a DXF version.
    
    Returns:
        Dict with version details
    """
    validated = validate_version(version)
    return {
        'version': validated,
        'ac_code': DXF_VERSIONS[validated],
        'supports_lwpolyline': supports_lwpolyline(validated),
        'supports_units': validated != 'R12',
        'is_genesis': validated == 'R12',
    }
