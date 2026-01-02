"""
Instrument Geometry: DXF Loader

Wave 17 - Instrument Geometry Integration

Resolves GuitarModelSpec.body_outline_id to actual DXF assets and provides
skeleton for future DXF parsing integration.

Usage:
    from instrument_geometry.dxf_loader import get_body_dxf_asset_for_model
    from instrument_geometry.model_spec import PRESET_MODELS
    
    model = PRESET_MODELS["strat_25_5"]
    asset = get_body_dxf_asset_for_model(model)
    if asset:
        data = load_dxf_geometry_stub(asset)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from .dxf_registry import DXFAsset, get_dxf_asset_by_id

if TYPE_CHECKING:
    from .model_spec import GuitarModelSpec


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------

def get_body_dxf_asset_for_model(model: "GuitarModelSpec") -> Optional[DXFAsset]:
    """
    Resolve the BODY DXF asset for a given GuitarModelSpec.

    Uses model.body_outline_id as a key into DXF_ASSETS.
    
    Args:
        model: GuitarModelSpec instance

    Returns:
        DXFAsset if model has body_outline_id and it's registered, None otherwise
        
    Example:
        >>> from instrument_geometry.model_spec import PRESET_MODELS
        >>> model = PRESET_MODELS["strat_25_5"]
        >>> asset = get_body_dxf_asset_for_model(model)
        >>> if asset:
        ...     print(asset.id)
        strat_body_v1
    """
    if not model.body_outline_id:
        return None
    return get_dxf_asset_by_id(model.body_outline_id)


# ---------------------------------------------------------------------------
# DXF loading skeleton
# ---------------------------------------------------------------------------

def read_dxf_bytes(path: Path) -> bytes:
    """
    Read the raw DXF bytes from disk.

    Args:
        path: Path to DXF file

    Returns:
        Raw file bytes

    Raises:
        FileNotFoundError: If the file does not exist
    """
    return path.read_bytes()


def load_dxf_geometry_stub(asset: DXFAsset) -> Any:
    """
    DXF geometry loader using the existing R12 parser.

    Responsibilities:
    - Open DXF file
    - Extract outlines (LWPOLYLINE / POLYLINE / LINE)
    - Convert to internal MLPath representation
    - Return geometry data + metadata

    Args:
        asset: DXFAsset to load

    Returns:
        Dict with:
        - asset_id: Asset identifier
        - kind: Asset kind (body, neck, etc.)
        - units: DXF units
        - paths: List of extracted geometry paths
        - path_count: Number of paths extracted
        - total_length_mm: Approximate total path length
        - bounds: Bounding box [min_x, min_y, max_x, max_y]
        - raw_bytes: Original DXF content (for pass-through)
        
    Example:
        >>> asset = get_dxf_asset_by_id("strat_body_v1")
        >>> if asset:
        ...     data = load_dxf_geometry_stub(asset)
        ...     print(data["path_count"])
        5
    """
    from io import StringIO
    from ..toolpath.dxf_io_legacy import read_dxf_to_mlpaths
    
    # Get absolute path (relative to this file's location)
    base_path = Path(__file__).parent.parent  # services/api/app/
    full_path = base_path / asset.path
    
    try:
        raw = read_dxf_bytes(full_path)
    except FileNotFoundError:
        # Return placeholder if file doesn't exist yet
        return {
            "asset_id": asset.id,
            "kind": asset.kind.value,
            "units": asset.units,
            "dxf_version": asset.dxf_version,
            "notes": asset.notes,
            "path": str(asset.path),
            "paths": [],
            "path_count": 0,
            "total_length_mm": 0.0,
            "bounds": [0.0, 0.0, 0.0, 0.0],
            "raw_bytes": b"",
            "placeholder": True,
        }
    
    # Parse DXF content to MLPaths using existing R12 parser
    try:
        content = raw.decode("utf-8", errors="replace")
        stream = StringIO(content)
        mlpaths = read_dxf_to_mlpaths(stream)
    except Exception:
        # If parsing fails, return raw bytes with empty geometry
        mlpaths = []
    
    # Extract geometry information from MLPaths
    paths = []
    total_length = 0.0
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    
    for path in mlpaths:
        path_points = path.points
        paths.append({
            "points": list(path_points),
            "is_closed": path.is_closed,
        })
        
        # Calculate path length and bounds
        for i, pt in enumerate(path_points):
            x, y = pt
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            
            if i > 0:
                prev_x, prev_y = path_points[i - 1]
                total_length += ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
    
    # Handle empty bounds
    if min_x == float("inf"):
        min_x = min_y = max_x = max_y = 0.0
    
    return {
        "asset_id": asset.id,
        "kind": asset.kind.value,
        "units": asset.units,
        "dxf_version": asset.dxf_version,
        "notes": asset.notes,
        "path": str(asset.path),
        "paths": paths,
        "path_count": len(paths),
        "total_length_mm": round(total_length, 2),
        "bounds": [min_x, min_y, max_x, max_y],
        "raw_bytes": raw,
        "placeholder": False,
    }


def load_dxf_geometry_by_path(file_path: str) -> dict:
    """
    Load DXF geometry directly from a file path.
    
    This is a convenience wrapper that reads a DXF file from disk and parses
    it using the R12 parser to extract geometry data.
    
    Args:
        file_path: Absolute or relative path to the DXF file.
        
    Returns:
        dict with keys:
          - path_count: Number of polyline paths
          - total_length_mm: Total length of all paths in mm
          - bounds: [min_x, min_y, max_x, max_y] bounding box
          - paths: List of path dicts with 'points' and 'is_closed'
          - placeholder: False (real data extracted)
          - source_file: The original file path
          
    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file cannot be parsed as DXF.
    """
    from pathlib import Path
    
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"DXF file not found: {file_path}")
    
    # Read raw bytes from file
    raw = path_obj.read_bytes()
    
    # Parse using R12 legacy parser
    try:
        mlpaths = read_dxf_to_mlpaths(raw)
    except Exception as e:
        raise ValueError(f"Failed to parse DXF file: {e}")
    
    # Extract paths and compute metrics
    paths = []
    total_length = 0.0
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    
    for mlpath in mlpaths:
        path_points = [(pt.x, pt.y) for pt in mlpath.points]
        is_closed = mlpath.closed if hasattr(mlpath, "closed") else False
        paths.append({
            "points": path_points,
            "is_closed": is_closed,
        })
        
        for i, pt in enumerate(path_points):
            x, y = pt
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            
            if i > 0:
                prev_x, prev_y = path_points[i - 1]
                total_length += ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
    
    # Handle empty bounds
    if min_x == float("inf"):
        min_x = min_y = max_x = max_y = 0.0
    
    return {
        "path_count": len(paths),
        "total_length_mm": round(total_length, 2),
        "bounds": [min_x, min_y, max_x, max_y],
        "paths": paths,
        "placeholder": False,
        "source_file": str(file_path),
    }
