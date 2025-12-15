"""
Instrument Geometry: DXF Asset Registry

Wave 17 - Instrument Geometry Integration

Central registry mapping logical IDs to physical DXF file paths.
Does NOT parse DXF - only tracks metadata and locations.

Usage:
    from instrument_geometry.dxf_registry import get_dxf_asset_by_id
    
    asset = get_dxf_asset_by_id("strat_body_v1")
    if asset:
        print(asset.path)  # Path to DXF file
        print(asset.units)  # "mm" or "in"
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


class DXFKind(str, Enum):
    """
    DXF asset kind classification.
    
    Used to categorize what geometry type the DXF contains.
    """
    BODY = "body"
    NECK = "neck"
    PICKGUARD = "pickguard"
    HEADSTOCK = "headstock"
    FRETBOARD = "fretboard"
    OTHER = "other"


@dataclass
class DXFAsset:
    """
    Describes a single DXF asset on disk.

    This does NOT parse the DXF – it only captures where it is and how
    it should be interpreted.

    Attributes:
        id: Logical ID (e.g. "strat_body_v1", "lp_body_v1")
        kind: What this geometry represents (BODY, NECK, etc.)
        path: Repo-relative path to the DXF file
        units: Drawing units in the DXF ("mm" or "in")
        dxf_version: Nominal DXF version (e.g. "R12", "R14", "R18")
        notes: Free-form notes (e.g. "outline only", "includes centerlines")
    """
    id: str
    kind: DXFKind
    path: Path
    units: str = "mm"
    dxf_version: str = "R12"
    notes: str = ""


# ---------------------------------------------------------------------------
# Central registry of known instrument DXF assets
# ---------------------------------------------------------------------------

# Note: Paths are relative to services/api/app/
# Adjust these IDs and paths to match your actual DXF locations.
DXF_ASSETS: Dict[str, DXFAsset] = {
    # Strat-style body outline
    "strat_body_v1": DXFAsset(
        id="strat_body_v1",
        kind=DXFKind.BODY,
        path=Path("assets/instrument_templates/strat/strat_body_v1.dxf"),
        units="mm",
        dxf_version="R12",
        notes="Strat-style body outline, R12-safe export.",
    ),

    # LP-style body outline
    "lp_body_v1": DXFAsset(
        id="lp_body_v1",
        kind=DXFKind.BODY,
        path=Path("assets/instrument_templates/lp/lp_body_v1.dxf"),
        units="mm",
        dxf_version="R12",
        notes="LP-style body outline. Includes centerline.",
    ),

    # Example acoustic outline
    "om_acoustic_body_v1": DXFAsset(
        id="om_acoustic_body_v1",
        kind=DXFKind.BODY,
        path=Path("assets/instrument_templates/acoustic/om_body_v1.dxf"),
        units="mm",
        dxf_version="R14",
        notes="OM acoustic body. Soundhole & centerline in file.",
    ),
    
    # Dreadnought acoustic outline
    "dreadnought_body_v1": DXFAsset(
        id="dreadnought_body_v1",
        kind=DXFKind.BODY,
        path=Path("assets/instrument_templates/acoustic/dreadnought_body_v1.dxf"),
        units="mm",
        dxf_version="R12",
        notes="Dreadnought acoustic body outline.",
    ),
}


def get_dxf_asset_by_id(asset_id: str) -> Optional[DXFAsset]:
    """
    Look up a DXFAsset by its logical ID.

    Args:
        asset_id: Logical ID (e.g. "strat_body_v1")

    Returns:
        DXFAsset if found, None otherwise
        
    Example:
        >>> asset = get_dxf_asset_by_id("strat_body_v1")
        >>> if asset:
        ...     print(asset.path)
        assets/instrument_templates/strat/strat_body_v1.dxf
    """
    return DXF_ASSETS.get(asset_id)
