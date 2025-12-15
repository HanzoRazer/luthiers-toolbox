# Instrument DXF Asset Mapping Guide

**Wave 17 - Instrument Geometry Integration**  
**Module:** DXF Registry & Loader (`dxf_registry.py`, `dxf_loader.py`)  
**Status:** Production Ready

---

## Overview

This guide documents the **DXF Asset Registry System**, which provides centralized mapping between logical instrument component IDs and physical DXF template files.

**What This System Does:**
- Maps logical IDs (e.g., `"strat_body_v1"`) to file paths
- Categorizes assets by type (body, neck, pickguard, etc.)
- Provides metadata (units, DXF version, notes)
- Resolves assets from `GuitarModelSpec` references

**What This System Does NOT Do:**
- Parse DXF file contents (use `ezdxf` library for that)
- Generate DXF files (use Neck Taper Suite or CAD software)
- Validate DXF geometry (future enhancement)

---

## Architecture

### System Components

```
instrument_geometry/
├── dxf_registry.py        # Central asset registry
├── dxf_loader.py          # Asset resolution and loading
├── model_spec.py          # GuitarModelSpec with body_outline_id
└── assets/                # Physical DXF files (not in repo yet)
    └── instrument_templates/
        ├── strat/
        │   ├── body_standard.dxf
        │   └── pickguard_sss.dxf
        ├── lp/
        │   ├── body_standard.dxf
        │   └── pickguard_lp.dxf
        └── acoustic/
            ├── dreadnought_body.dxf
            └── om_body.dxf
```

### Data Flow

```
GuitarModelSpec
    ↓ (body_outline_id = "strat_body_v1")
dxf_loader.get_body_dxf_asset_for_model()
    ↓ (lookup in registry)
dxf_registry.get_dxf_asset_by_id()
    ↓ (returns DXFAsset)
DXFAsset
    ↓ (provides file path)
dxf_loader.load_dxf_geometry_stub()
    ↓ (reads file if exists)
Geometry data (for CAM, rendering, etc.)
```

---

## DXF Asset Registry

### File: `dxf_registry.py`

#### DXFKind Enum

Categorizes assets by instrument component type:

```python
from enum import Enum

class DXFKind(str, Enum):
    BODY = "body"               # Guitar/bass body outline
    NECK = "neck"               # Neck blank outline
    PICKGUARD = "pickguard"     # Pickguard/scratchplate
    HEADSTOCK = "headstock"     # Headstock shape
    FRETBOARD = "fretboard"     # Fretboard blank (with fret slots)
    OTHER = "other"             # Miscellaneous (bridge plates, control cavities, etc.)
```

**Usage:**
```python
from instrument_geometry.dxf_registry import DXFKind

body_kind = DXFKind.BODY
print(body_kind.value)  # "body"
```

#### DXFAsset Dataclass

Represents a single registered DXF asset:

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DXFAsset:
    id: str                  # Logical ID (e.g., "strat_body_v1")
    kind: DXFKind            # Asset category
    path: Path               # Absolute path to DXF file
    units: str               # "mm" or "in"
    dxf_version: str         # "R12" (AC1009) or "R2000" (AC1015), etc.
    notes: str               # Human-readable description
```

**Example:**
```python
from pathlib import Path
from instrument_geometry.dxf_registry import DXFAsset, DXFKind

asset = DXFAsset(
    id="strat_body_v1",
    kind=DXFKind.BODY,
    path=Path("/path/to/assets/strat/body_standard.dxf"),
    units="mm",
    dxf_version="R12",
    notes="Fender Stratocaster body outline (standard routing)"
)
```

#### DXF_ASSETS Registry

Central dictionary mapping IDs to assets:

```python
from pathlib import Path

# Base path for templates (relative to this file)
ASSETS_DIR = Path(__file__).parent / "assets" / "instrument_templates"

DXF_ASSETS: Dict[str, DXFAsset] = {
    "strat_body_v1": DXFAsset(
        id="strat_body_v1",
        kind=DXFKind.BODY,
        path=ASSETS_DIR / "strat" / "body_standard.dxf",
        units="mm",
        dxf_version="R12",
        notes="Fender Stratocaster body outline (standard SSS routing)"
    ),
    "lp_body_v1": DXFAsset(
        id="lp_body_v1",
        kind=DXFKind.BODY,
        path=ASSETS_DIR / "lp" / "body_standard.dxf",
        units="mm",
        dxf_version="R12",
        notes="Gibson Les Paul body outline (standard)"
    ),
    "om_acoustic_body_v1": DXFAsset(
        id="om_acoustic_body_v1",
        kind=DXFKind.BODY,
        path=ASSETS_DIR / "acoustic" / "om_body.dxf",
        units="mm",
        dxf_version="R12",
        notes="Orchestra Model (OM) acoustic guitar body"
    ),
    "dreadnought_body_v1": DXFAsset(
        id="dreadnought_body_v1",
        kind=DXFKind.BODY,
        path=ASSETS_DIR / "acoustic" / "dreadnought_body.dxf",
        units="mm",
        dxf_version="R12",
        notes="Martin-style Dreadnought acoustic body"
    ),
}
```

#### Lookup Function

```python
def get_dxf_asset_by_id(asset_id: str) -> Optional[DXFAsset]:
    """
    Retrieve a DXF asset by its logical ID.
    
    Args:
        asset_id: Logical asset ID (e.g., "strat_body_v1")
        
    Returns:
        DXFAsset if found, None otherwise
    """
    return DXF_ASSETS.get(asset_id)
```

**Example:**
```python
from instrument_geometry.dxf_registry import get_dxf_asset_by_id

asset = get_dxf_asset_by_id("lp_body_v1")
if asset:
    print(f"Found: {asset.notes}")
    print(f"Path: {asset.path}")
else:
    print("Asset not found")
```

---

## DXF Loader System

### File: `dxf_loader.py`

#### Function: `get_body_dxf_asset_for_model()`

Resolves `GuitarModelSpec.body_outline_id` to a `DXFAsset`:

```python
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .model_spec import GuitarModelSpec

from .dxf_registry import get_dxf_asset_by_id, DXFAsset

def get_body_dxf_asset_for_model(model: "GuitarModelSpec") -> Optional[DXFAsset]:
    """
    Resolve the body outline DXF asset for a given guitar model.
    
    Args:
        model: GuitarModelSpec with body_outline_id field
        
    Returns:
        DXFAsset if model has body_outline_id and it exists in registry
        None if model.body_outline_id is None or asset not found
    """
    if not model.body_outline_id:
        return None
    return get_dxf_asset_by_id(model.body_outline_id)
```

**Example:**
```python
from instrument_geometry.model_spec import PRESET_MODELS
from instrument_geometry.dxf_loader import get_body_dxf_asset_for_model

strat_model = PRESET_MODELS["strat_25_5"]
asset = get_body_dxf_asset_for_model(strat_model)

if asset:
    print(f"Body template: {asset.path}")
else:
    print("No body template assigned")
```

#### Function: `read_dxf_bytes()`

Reads raw DXF file bytes:

```python
from pathlib import Path

def read_dxf_bytes(path: Path) -> bytes:
    """
    Read a DXF file as raw bytes.
    
    Args:
        path: Path to DXF file
        
    Returns:
        Raw file bytes
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read
    """
    with open(path, "rb") as f:
        return f.read()
```

#### Function: `load_dxf_geometry_stub()`

Skeleton for future full DXF parsing (uses `ezdxf` when available):

```python
from pathlib import Path
from typing import Dict, Any

def load_dxf_geometry_stub(asset: DXFAsset) -> Dict[str, Any]:
    """
    Load DXF geometry from an asset.
    
    This is currently a STUB that returns metadata only.
    Future implementation will use ezdxf to parse entities.
    
    Args:
        asset: DXFAsset to load
        
    Returns:
        Dictionary with keys:
            - success: bool
            - path: str (file path)
            - exists: bool (file exists on disk)
            - units: str (from asset metadata)
            - dxf_version: str (from asset metadata)
            - entities: List (empty for now, will be polylines/arcs later)
            - raw_bytes: bytes (if file exists)
    """
    exists = asset.path.exists()
    
    result = {
        "success": exists,
        "path": str(asset.path),
        "exists": exists,
        "units": asset.units,
        "dxf_version": asset.dxf_version,
        "entities": [],  # Future: parse with ezdxf
    }
    
    if exists:
        result["raw_bytes"] = read_dxf_bytes(asset.path)
    
    return result
```

**Example:**
```python
from instrument_geometry.dxf_registry import get_dxf_asset_by_id
from instrument_geometry.dxf_loader import load_dxf_geometry_stub

asset = get_dxf_asset_by_id("strat_body_v1")
if asset:
    data = load_dxf_geometry_stub(asset)
    if data["success"]:
        print(f"Loaded {len(data['raw_bytes'])} bytes")
        print(f"Units: {data['units']}, Version: {data['dxf_version']}")
    else:
        print(f"File not found: {data['path']}")
```

---

## Integration with GuitarModelSpec

### Workflow Example

```python
from instrument_geometry.model_spec import PRESET_MODELS
from instrument_geometry.dxf_loader import get_body_dxf_asset_for_model, load_dxf_geometry_stub

# 1. Get preset model
lp_model = PRESET_MODELS["lp_24_75"]
print(f"Model: {lp_model.display_name}")
print(f"Body outline ID: {lp_model.body_outline_id}")

# 2. Resolve DXF asset
asset = get_body_dxf_asset_for_model(lp_model)
if not asset:
    print("No body template assigned to this model")
    exit(1)

print(f"Asset kind: {asset.kind.value}")
print(f"Asset path: {asset.path}")
print(f"Notes: {asset.notes}")

# 3. Load geometry (stub for now)
data = load_dxf_geometry_stub(asset)
if data["success"]:
    print(f"✅ Loaded DXF: {data['units']} units, {data['dxf_version']} format")
    # Future: access data["entities"] for polylines/arcs
else:
    print(f"⚠️ DXF file not found (placeholder path): {data['path']}")
    print("   → Add real DXF file to assets directory to enable loading")
```

---

## Adding New Assets

### Step 1: Place DXF File

Put the DXF file in the appropriate subdirectory:

```bash
# Example: Add Telecaster body
cp telecaster_body.dxf services/api/app/assets/instrument_templates/strat/tele_body.dxf
```

### Step 2: Register Asset

Edit `dxf_registry.py` and add entry to `DXF_ASSETS`:

```python
DXF_ASSETS["tele_body_v1"] = DXFAsset(
    id="tele_body_v1",
    kind=DXFKind.BODY,
    path=ASSETS_DIR / "strat" / "tele_body.dxf",
    units="mm",
    dxf_version="R12",
    notes="Fender Telecaster body outline (standard bridge routing)"
)
```

### Step 3: Create Model Preset (Optional)

Add to `model_spec.py`:

```python
TELE_25_5_MODEL = GuitarModelSpec(
    id="tele_25_5",
    display_name="Tele-style 25.5\"",
    scale_profile_id="fender_25_5",
    num_strings=6,
    strings=STANDARD_10_46_E_STANDARD,
    nut_spacing=StringSpacingSpec(num_strings=6, e_to_e_mm=35.0),
    bridge_spacing=StringSpacingSpec(num_strings=6, e_to_e_mm=52.0),
    neck_taper=NeckTaperSpec(nut_width_mm=42.0, heel_width_mm=56.0, taper_length_in=16.0),
    body_outline_id="tele_body_v1"  # ← Reference registry entry
)

PRESET_MODELS["tele_25_5"] = TELE_25_5_MODEL
```

### Step 4: Test Resolution

```python
from instrument_geometry.model_spec import PRESET_MODELS
from instrument_geometry.dxf_loader import get_body_dxf_asset_for_model, load_dxf_geometry_stub

model = PRESET_MODELS["tele_25_5"]
asset = get_body_dxf_asset_for_model(model)
assert asset is not None, "Asset not found"
assert asset.path.exists(), f"File not found: {asset.path}"

data = load_dxf_geometry_stub(asset)
assert data["success"], "Failed to load DXF"
print(f"✅ Telecaster asset loaded: {len(data['raw_bytes'])} bytes")
```

---

## Asset Categories & Use Cases

### Body Outlines (`DXFKind.BODY`)

**Purpose:** External body shape for routing/cutting

**Typical Contents:**
- Single closed polyline defining perimeter
- May include control cavity outlines
- May include pickup routing shapes

**CAM Workflows:**
- Profile cut (router table or CNC)
- Pocket mill for cavities
- 3D relief carving for tops

**Examples:**
- Strat, Tele, Les Paul, SG, Flying V
- Acoustic dreadnought, OM, grand concert
- Bass bodies (Precision, Jazz, Thunderbird)

### Neck Blanks (`DXFKind.NECK`)

**Purpose:** Neck blank outline (generated by Neck Taper Suite)

**Typical Contents:**
- Closed polyline with width taper from nut to heel
- May include headstock transition
- May include heel tenon shape

**CAM Workflows:**
- Band saw rough cut
- CNC profile for accurate taper
- Carving jigs for back profile

### Pickguards (`DXFKind.PICKGUARD`)

**Purpose:** Scratchplate shape and screw holes

**Typical Contents:**
- Outer perimeter (closed polyline)
- Screw hole positions (small circles)
- Pickup cutouts (rectangles or polygons)

**CAM Workflows:**
- Laser cut (acrylic/wood/metal)
- CNC mill (thin plastic/wood)
- Manual routing with template

### Headstocks (`DXFKind.HEADSTOCK`)

**Purpose:** Headstock shape (Fender 6-in-line, Gibson 3+3, etc.)

**Typical Contents:**
- Outer perimeter
- String hole positions
- Truss rod access hole
- Logo engraving outline (optional)

**CAM Workflows:**
- CNC carving for volute
- Laser engraving for logos
- Drill press for tuner holes

### Fretboards (`DXFKind.FRETBOARD`)

**Purpose:** Fretboard blank with fret slot positions

**Typical Contents:**
- Rectangle perimeter (width × length)
- Fret slot centerlines (width-spanning lines)
- Radius reference arcs (for sanding)

**CAM Workflows:**
- Fret slot saw (indexed cuts)
- CNC milling for compound radius
- Inlay routing (position markers)

### Other (`DXFKind.OTHER`)

**Purpose:** Miscellaneous components

**Examples:**
- Bridge plate (acoustic guitars)
- Control cavity cover
- Truss rod cover
- Binding strips
- Inlay patterns

---

## File Organization Best Practices

### Directory Structure

```
assets/instrument_templates/
├── strat/
│   ├── body_standard.dxf           # SSS routing
│   ├── body_hss.dxf                # HSS routing variant
│   ├── pickguard_sss_8hole.dxf
│   └── pickguard_hss_11hole.dxf
├── lp/
│   ├── body_standard.dxf
│   ├── body_custom_shop.dxf        # Weight relief variant
│   └── pickguard_lp.dxf
├── tele/
│   ├── body_standard.dxf
│   ├── body_thinline.dxf
│   └── pickguard_tele_8hole.dxf
├── acoustic/
│   ├── dreadnought_body.dxf
│   ├── om_body.dxf
│   ├── grand_concert_body.dxf
│   ├── dreadnought_bracing.dxf
│   └── om_bracing.dxf
└── bass/
    ├── precision_body.dxf
    ├── jazz_body.dxf
    └── precision_pickguard.dxf
```

### Naming Convention

**Format:** `{component}_{variant}_{detail}.dxf`

**Examples:**
- `body_standard.dxf` - Default variant
- `body_hss.dxf` - HSS routing variant
- `pickguard_sss_8hole.dxf` - SSS with 8 screw holes
- `neck_22fret_42mm.dxf` - 22-fret neck, 42mm nut

### Metadata in Filenames

**Avoid:** Encoding too much metadata in filename
```
❌ stratocaster_body_alder_sss_routing_11holes_648mm_scale.dxf  # Too verbose
✅ body_standard.dxf  # Simple, metadata in registry
```

**Use Registry for Details:**
```python
DXFAsset(
    id="strat_body_v1",
    # ... other fields ...
    notes="Stratocaster body: SSS routing, 11 screw holes, standard contours"
)
```

---

## Future Enhancements

### Planned Features (Wave 18+)

**1. DXF Validation**
```python
def validate_dxf_asset(asset: DXFAsset) -> ValidationResult:
    """
    Validate DXF file integrity and geometry.
    
    Checks:
    - File exists and is readable
    - Valid DXF format (header, entities, EOF)
    - Closed polylines (for body/neck outlines)
    - No self-intersections
    - Units match metadata
    """
    pass
```

**2. Full `ezdxf` Integration**
```python
def load_dxf_geometry(asset: DXFAsset) -> GeometryData:
    """
    Parse DXF file and extract geometric entities.
    
    Returns:
    - Polylines as List[Point]
    - Arcs as Arc objects
    - Circles as Circle objects
    - Layers and colors
    """
    import ezdxf
    doc = ezdxf.readfile(asset.path)
    # ... parse entities ...
```

**3. Asset Version Management**
```python
DXFAsset(
    id="strat_body_v2",  # v2 = updated variant
    replaces="strat_body_v1",  # Deprecation tracking
    version="2.0",
    changelog="Updated pickup routing for humbucker compatibility"
)
```

**4. Multi-Resolution Assets**
```python
DXFAsset(
    id="lp_body_v1_hires",
    resolution="high",  # high/medium/low
    point_count=500,    # Number of polyline vertices
    file_size_kb=250
)
```

**5. Asset Previews (SVG Thumbnails)**
```python
DXFAsset(
    id="tele_body_v1",
    preview_svg=ASSETS_DIR / "tele" / "body_preview.svg",
    thumbnail_png=ASSETS_DIR / "tele" / "body_thumb.png"
)
```

---

## API Integration

### FastAPI Endpoint (Future)

```python
from fastapi import APIRouter, HTTPException
from instrument_geometry.dxf_registry import get_dxf_asset_by_id, DXF_ASSETS
from instrument_geometry.dxf_loader import load_dxf_geometry_stub

router = APIRouter(prefix="/api/instrument/assets", tags=["DXF Assets"])

@router.get("/list")
def list_dxf_assets():
    """List all registered DXF assets."""
    return {
        "assets": [
            {
                "id": asset.id,
                "kind": asset.kind.value,
                "notes": asset.notes,
                "units": asset.units,
                "exists": asset.path.exists()
            }
            for asset in DXF_ASSETS.values()
        ]
    }

@router.get("/{asset_id}")
def get_dxf_asset(asset_id: str):
    """Get metadata for a specific asset."""
    asset = get_dxf_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(404, f"Asset not found: {asset_id}")
    
    return {
        "id": asset.id,
        "kind": asset.kind.value,
        "path": str(asset.path),
        "units": asset.units,
        "dxf_version": asset.dxf_version,
        "notes": asset.notes,
        "exists": asset.path.exists()
    }

@router.get("/{asset_id}/download")
def download_dxf_asset(asset_id: str):
    """Download DXF file."""
    asset = get_dxf_asset_by_id(asset_id)
    if not asset:
        raise HTTPException(404, f"Asset not found: {asset_id}")
    if not asset.path.exists():
        raise HTTPException(404, f"File not found: {asset.path}")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        asset.path,
        media_type="application/dxf",
        filename=f"{asset.id}.dxf"
    )
```

---

## See Also

- [Neck Taper Theory Guide](./Neck_Taper_Theory.md) - Neck profile generation
- [Neck Taper DXF Export Guide](./Neck_Taper_DXF_Export.md) - DXF format details
- [GuitarModelSpec Documentation](../GUITAR_MODEL_INVENTORY_REPORT.md) - Model specification system
- [Wave 17 Integration Summary](../../docs/wave17_integration_summary.md) - Overall architecture

---

**Last Updated:** December 8, 2025  
**Author:** Luthier's Tool Box Development Team  
**Version:** 1.0 (Wave 17)
