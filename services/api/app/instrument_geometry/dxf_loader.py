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
    Skeleton for a future DXF geometry loader.

    Eventual responsibilities (when wired to ezdxf or your existing
    R12-converter):

    - Open DXF
    - Extract outlines (LWPOLYLINE / POLYLINE / LINE)
    - Convert to your internal GeometryEngine / MLPath representation

    For now, we just return raw bytes + metadata so the wiring
    can be verified.

    Args:
        asset: DXFAsset to load

    Returns:
        Dict with metadata and raw_bytes
        
    Example:
        >>> asset = get_dxf_asset_by_id("strat_body_v1")
        >>> if asset:
        ...     data = load_dxf_geometry_stub(asset)
        ...     print(data["asset_id"])
        strat_body_v1
    """
    # Get absolute path (relative to this file's location)
    base_path = Path(__file__).parent.parent  # services/api/app/
    full_path = base_path / asset.path
    
    try:
        raw = read_dxf_bytes(full_path)
    except FileNotFoundError:
        # Placeholder: return empty bytes if file doesn't exist yet
        raw = b""
    
    return {
        "asset_id": asset.id,
        "kind": asset.kind.value,
        "units": asset.units,
        "dxf_version": asset.dxf_version,
        "notes": asset.notes,
        "path": str(asset.path),
        "raw_bytes": raw,
        "placeholder": len(raw) == 0,  # True if no actual file exists
    }
