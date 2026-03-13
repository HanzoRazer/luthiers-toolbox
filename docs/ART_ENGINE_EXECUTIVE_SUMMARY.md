# Art Studio — Unified Art Generation Engine

## Executive Summary

The current Art Studio (`services/api/app/art_studio/`) has its decorative and machining concerns tangled across ~50 Python files. Decorative image/pattern generation (rosettes, inlays, marquetry) shares obvious geometry, material, export, and preset infrastructure — but each domain reimplements it independently.

Meanwhile, **bracing, relief, and v-carve are pure machining/cutting operations** — they belong to CAM, not to an art generation engine. Bracing computes structural section profiles and mass. Relief and v-carve parse SVG into polylines for CNC toolpath planning. None of them *generate* decorative imagery.

This document proposes a **Unified Art Generation Engine** scoped to the **4 decorative domains** (rosettes, fretboard inlays, headstock inlays, marquetry), extracting shared concerns into a single layer while preserving each domain's logic as pluggable **Art Modules**. Bracing, relief, and v-carve remain independent routers under Art Studio or migrate to CAM — they are not part of this engine.

---

## Current State

### Art Engine Scope — Decorative Image Generation (4 domains)

| Domain | Router | Maturity | Geometry Model | Exports | Presets |
|--------|--------|----------|----------------|---------|---------|
| **Rosettes** | `art_studio/api/` (9 files) | High | `RosetteParamSpec` → concentric rings | SVG, DXF, PNG, G-code, JSON | `PRESET_MATRICES` in generator registry |
| **Fretboard Inlays** | `inlay_router.py` | Medium | `InlayShape` → positioned polygons | DXF, G-code | `INLAY_PRESETS` dict |
| **Headstock Inlays** | `headstock_inlay_router.py` | Low (AI-prompt only) | None — text prompt output | AI prompt text | Style × design × material combinatorics |
| **Marquetry** | *(new)* | Not started | — | — | — |

### Out of Scope — Pure Machining/Cutting (stay as independent routers)

| Domain | Router | Why it's out | Where it belongs |
|--------|--------|-------------|------------------|
| **Bracing** | `bracing_router.py` | Structural section profiles, mass calculation, no decorative imagery | CAM / structural calculator |
| **Relief** | `relief_router.py` | SVG → polyline parsing for CNC depth carving, no image generation | CAM toolpath input |
| **V-Carve** | `vcarve_router.py` | SVG → polyline parsing for CNC engraving, no image generation | CAM toolpath input |

### Overlap Matrix (Engine-Scoped Domains Only)

| Shared Concern | Rosettes | Fretboard Inlays | Headstock Inlays | Marquetry (new) |
|----------------|:--------:|:----------------:|:----------------:|:---------------:|
| DXF R12 export | ✅ | ✅ | ❌ | ✅ |
| SVG preview | ✅ custom renderer | ❌ | ❌ | ✅ |
| G-code (via CAM bridge) | ✅ | ✅ | ❌ | ✅ |
| Material library | ✅ `wood_materials.py` | ❌ | ✅ `WOOD_DESCRIPTIONS` | ✅ |
| Preset system | ✅ registry | ✅ dict | ✅ enums | ✅ |
| Snapshot persistence | ✅ `DesignSnapshot` | ❌ | ❌ | ✅ |
| AI prompt generation | ❌ | ❌ | ✅ | ✅ |
| Positioned shapes | ✅ (annuli) | ✅ (polygons) | ❌ | ✅ (tiles/polygons) |

### Critical Finding: 7 Missing Abstractions (Decorative Domains)

1. **Base Art Spec** — `RosetteParamSpec` doesn't generalize; `InlayCalcInput` is completely separate
2. **Pattern Output Interface** — No shared "here are the shapes" envelope
3. **Manufacturing Intent** — No unified "design → CamIntent" bridge for decorative art
4. **Geometry Rendering Pipeline** — Preview rendering is hand-coded per domain
5. **Material Database** — Scattered across `wood_materials.py` (visual) and `WOOD_DESCRIPTIONS` (text)
6. **Unified DXF Exporter** — Two separate DXF writers for decorative art (`dxf_compat` wrapper in `inlay_calc.py`, rosette DXF in `dxf_compat`)
7. **Unified Snapshot Store** — Only rosettes have persistence; inlays and future marquetry have nothing

---

## Proposed Architecture — Unified Art Engine

```
art_studio/
├── engine/                    # THE UNIFIED LAYER
│   ├── __init__.py
│   ├── protocol.py            # ArtSpec protocol + ArtResult envelope
│   ├── registry.py            # Domain-agnostic generator registry
│   ├── geometry.py            # Shared geometry IR (intermediate representation)
│   ├── materials.py           # Unified material catalog
│   ├── presets.py             # Universal preset system
│   ├── snapshot.py            # Domain-agnostic snapshot persistence
│   └── export/
│       ├── __init__.py
│       ├── dxf.py             # Single DXF R12 exporter
│       ├── svg.py             # Single SVG renderer
│       └── manufacturing.py   # Design → CamIntent bridge
│
├── modules/                   # DOMAIN-SPECIFIC PLUG-INS
│   ├── __init__.py
│   ├── rosette/               # Existing rosette logic (refactored)
│   │   ├── spec.py            # RosetteArtSpec (implements ArtSpec)
│   │   ├── generator.py       # Ring generators
│   │   └── renderer.py        # Ring-specific SVG
│   ├── inlay/                 # Fretboard + headstock inlays
│   │   ├── spec.py            # InlayArtSpec (implements ArtSpec)
│   │   ├── calculator.py      # Fret position math
│   │   └── shapes.py          # Shape generators (dot, diamond, block, crown...)
│   └── marquetry/             # NEW — overlaps with inlays but free-form
│       ├── spec.py            # MarquetryArtSpec
│       └── tessellation.py    # Tile/pattern fill algorithms
│
├── api/                       # ROUTERS (thin — delegate to engine)
│   ├── unified_router.py      # POST /generate, /preview, /export
│   └── domain_routers.py      # Domain-specific convenience endpoints
│
├── svg/                       # EXISTING — AI-powered SVG generation
│   ├── generator.py           # Prompt → image → vectorize → SVG
│   └── styles.py              # Style prompt suffixes
│
└── schemas/                   # EXISTING — kept for backward compat
```

---

## Core Schemas

### 1. `ArtSpec` — The Universal Design Protocol

Every art domain produces an `ArtSpec`. This is the single interface the engine cares about.

```python
# art_studio/engine/protocol.py
"""
Unified Art Specification Protocol.

Every art module implements ArtSpec. The engine never knows
which domain it's working with — it only sees ArtSpec.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Protocol, runtime_checkable
from pydantic import BaseModel, Field
from datetime import datetime

from .geometry import GeometryCollection


# ── Domain Enum ──────────────────────────────────────────────────────

ArtDomain = Literal[
    "rosette",
    "inlay",
    "marquetry",
]


# ── Protocol ─────────────────────────────────────────────────────────

@runtime_checkable
class ArtSpec(Protocol):
    """
    What every art module must produce.

    The engine calls .to_geometry() to get domain-agnostic shapes,
    then feeds those shapes to exporters (DXF, SVG, G-code bridge).
    """

    @property
    def domain(self) -> ArtDomain:
        """Which art domain this spec belongs to."""
        ...

    @property
    def bounds_mm(self) -> BoundingBox:
        """Axis-aligned bounding box of the entire design."""
        ...

    def to_geometry(self) -> GeometryCollection:
        """
        Convert domain-specific parameters into engine-neutral geometry.

        This is the key abstraction: rosettes produce concentric arcs,
        inlays produce positioned polygons, marquetry produces tile grids —
        but they all return GeometryCollection.
        """
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-safe dict for snapshot persistence."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArtSpec":
        """Deserialize from snapshot."""
        ...


# ── Bounding Box ─────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Axis-aligned bounding box. All values in mm."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    @property
    def center(self) -> tuple[float, float]:
        return ((self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2)


# ── Art Result Envelope ──────────────────────────────────────────────

class ArtResult(BaseModel):
    """
    Universal output envelope from any art generation operation.

    Every endpoint returns this. Consumers never need to know which
    domain produced it.
    """

    domain: ArtDomain
    spec_data: Dict[str, Any] = Field(
        description="Serialized ArtSpec (domain-specific parameters)"
    )
    geometry: GeometryCollection = Field(
        description="Engine-neutral geometry ready for export"
    )
    bounds_mm: BoundingBox
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**What this solves:** Every decorative domain currently has its own output shape (`RosetteParamSpec`, `InlayCalcResult`). `ArtResult` wraps any of them into a single envelope that downstream code (exporters, persistence, UI) can consume uniformly.

---

### 2. `GeometryCollection` — Shared Intermediate Representation

```python
# art_studio/engine/geometry.py
"""
Domain-agnostic geometry primitives.

These are the building blocks that every art domain converts its
design into. Exporters (DXF, SVG, G-code bridge) consume only these.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class ShapeType(str, Enum):
    """Primitive geometry types the engine understands."""
    CIRCLE = "circle"
    ARC = "arc"
    POLYGON = "polygon"         # Closed polyline (any shape)
    POLYLINE = "polyline"       # Open polyline
    ANNULUS = "annulus"          # Ring (rosettes)
    RECTANGLE = "rectangle"     # Axis-aligned rect (block inlays, marquetry tiles)
    ELLIPSE = "ellipse"


Point2D = Tuple[float, float]


class Shape(BaseModel):
    """
    A single geometric primitive with metadata.

    Every shape carries enough information for any exporter to render it:
    - Geometry: type-specific fields (center, radius, vertices, etc.)
    - Metadata: layer name, material ref, depth, and domain tag
    """

    shape_type: ShapeType
    layer: str = Field(
        default="ART_OUTLINE",
        description="DXF layer / SVG group for this shape"
    )

    # ── Circle / Arc / Annulus ───────────────────────────────────────
    center: Optional[Point2D] = None
    radius: Optional[float] = None          # circle, arc
    inner_radius: Optional[float] = None    # annulus
    outer_radius: Optional[float] = None    # annulus
    start_angle_deg: Optional[float] = None # arc
    end_angle_deg: Optional[float] = None   # arc

    # ── Polygon / Polyline ───────────────────────────────────────────
    vertices: Optional[List[Point2D]] = None

    # ── Rectangle ────────────────────────────────────────────────────
    origin: Optional[Point2D] = None   # bottom-left corner
    width: Optional[float] = None
    height: Optional[float] = None
    rotation_deg: float = 0.0

    # ── Ellipse ──────────────────────────────────────────────────────
    rx: Optional[float] = None
    ry: Optional[float] = None

    # ── Manufacturing metadata ───────────────────────────────────────
    depth_mm: Optional[float] = Field(
        default=None,
        description="Cut/pocket depth for CNC operations"
    )
    material_id: Optional[str] = Field(
        default=None,
        description="Reference to material catalog entry"
    )
    domain_tag: Optional[str] = Field(
        default=None,
        description="Which art domain produced this shape"
    )


class GeometryCollection(BaseModel):
    """
    An ordered collection of Shape primitives.

    This is the universal intermediate representation.
    Exporters iterate over shapes and emit format-specific output.
    """

    shapes: List[Shape] = Field(default_factory=list)
    units: str = Field(default="mm", description="Always mm internally")

    def by_layer(self, layer: str) -> List[Shape]:
        """Filter shapes by DXF layer name."""
        return [s for s in self.shapes if s.layer == layer]

    def by_type(self, shape_type: ShapeType) -> List[Shape]:
        """Filter shapes by primitive type."""
        return [s for s in self.shapes if s.shape_type == shape_type]

    @property
    def layers(self) -> set[str]:
        """All unique layer names in this collection."""
        return {s.layer for s in self.shapes}
```

**What this solves:** Currently rosettes emit `RingParam` (annuli) and inlays emit `InlayShape` (positioned polygons) with no shared vocabulary. `GeometryCollection` is the single language that all decorative domains translate into before export.

---

### 3. Domain-Agnostic Generator Registry

```python
# art_studio/engine/registry.py
"""
Universal generator registry.

Replaces the rosette-only registry (services/generators/registry.py)
with a domain-aware version. Same pattern, wider type signature.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .protocol import ArtDomain, ArtResult, ArtSpec


# ── Generator function signature ─────────────────────────────────────
# Takes domain-specific params dict, returns an ArtSpec for that domain.
GeneratorFn = Callable[[Dict[str, Any]], ArtSpec]


@dataclass
class GeneratorEntry:
    """Metadata about a registered generator."""
    key: str                        # e.g. "rosette.basic_rings@1"
    domain: ArtDomain
    fn: GeneratorFn
    name: str
    description: str = ""
    param_hints: Dict[str, Any] = field(default_factory=dict)
    version: int = 1


# ── Registry singleton ───────────────────────────────────────────────
_REGISTRY: Dict[str, GeneratorEntry] = {}


def register_generator(
    key: str,
    domain: ArtDomain,
    fn: GeneratorFn,
    name: str,
    description: str = "",
    param_hints: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register a generator function.

    Keys are namespaced: 'rosette.mosaic_band@1', 'inlay.dot_standard@1'.
    Raises ValueError on duplicate key.
    """
    if key in _REGISTRY:
        raise ValueError(f"Generator already registered: {key}")
    _REGISTRY[key] = GeneratorEntry(
        key=key,
        domain=domain,
        fn=fn,
        name=name,
        description=description,
        param_hints=param_hints or {},
    )


def get_generator(key: str) -> GeneratorEntry:
    """Look up a generator by key. Raises KeyError if not found."""
    if key not in _REGISTRY:
        raise KeyError(f"Unknown generator: {key}. Available: {list(_REGISTRY)}")
    return _REGISTRY[key]


def list_generators(domain: Optional[ArtDomain] = None) -> List[GeneratorEntry]:
    """
    List generators, optionally filtered by domain.

    list_generators()              → all generators
    list_generators("rosette")     → rosette generators only
    list_generators("inlay")       → inlay generators only
    """
    entries = list(_REGISTRY.values())
    if domain is not None:
        entries = [e for e in entries if e.domain == domain]
    return entries


def generate(key: str, params: Dict[str, Any]) -> ArtResult:
    """
    Run a generator and wrap its output in an ArtResult envelope.

    This is the main entry point for all art generation:
        result = generate("rosette.mosaic_band@1", {"ring_count": 5, ...})
        result = generate("inlay.dot_standard@1", {"scale_length_mm": 648, ...})

    Returns ArtResult with geometry ready for any exporter.
    """
    entry = get_generator(key)
    spec: ArtSpec = entry.fn(params)
    geometry = spec.to_geometry()

    return ArtResult(
        domain=entry.domain,
        spec_data=spec.to_dict(),
        geometry=geometry,
        bounds_mm=spec.bounds_mm,
    )
```

**What this solves:** The current `registry.py` only accepts `(outer_mm, inner_mm, params) → RosetteParamSpec`. The new registry accepts any domain's params and returns a universal `ArtResult`.

---

### 4. Unified Material Catalog

```python
# art_studio/engine/materials.py
"""
Unified material catalog for decorative art domains.

Merges:
  - cam/rosette/prototypes/wood_materials.py (14 visual wood entries)
  - cam/headstock/inlay_prompts.py WOOD_DESCRIPTIONS (20+ text entries)
  - inlay material types (mother-of-pearl, abalone, bone)

Single source of truth for material properties used in decorative art.
Bracing density values stay in bracing_calc.py (structural, not decorative).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class MaterialCategory(str, Enum):
    """Top-level material classification."""
    TONEWOOD = "tonewood"      # Spruce, cedar, mahogany...
    HARDWOOD = "hardwood"      # Ebony, rosewood, maple...
    EXOTIC = "exotic"          # Koa, ziricote, ovangkol...
    SHELL = "shell"            # Abalone, MOP, paua
    SYNTHETIC = "synthetic"    # Corian, Richlite, carbon fiber
    METAL = "metal"            # Gold leaf, brass, nickel silver
    BONE = "bone"              # Bone, ivory alternatives


@dataclass(frozen=True)
class Material:
    """
    A single material with properties needed across all art domains.

    Rosettes need: base/grain/accent colors, tight/figure/iridescent flags
    Inlays need: visual description for AI prompts, contrast rating
    Marquetry needs: colors + prompt descriptions for tile patterns
    All domains need: id, name, category
    """
    id: str
    name: str
    category: MaterialCategory

    # ── Visual properties (rosette preview, UI rendering) ────────────
    base_color: str = "#808080"         # Hex color
    grain_color: str = "#707070"
    accent_color: str = "#909090"
    highlight_color: str = "#a0a0a0"
    tight_grain: bool = False
    figured: bool = False
    iridescent: bool = False

    # ── Physical properties (informational, for CAM handoff) ────────
    density_kg_m3: Optional[float] = None
    janka_hardness: Optional[int] = None

    # ── AI prompt description (headstock inlays, marquetry) ──────────
    prompt_description: str = ""


# ── Catalog ──────────────────────────────────────────────────────────

_CATALOG: Dict[str, Material] = {}


def register_material(material: Material) -> None:
    """Add a material to the global catalog."""
    _CATALOG[material.id] = material


def get_material(material_id: str) -> Material:
    """Look up material by ID. Raises KeyError if not found."""
    if material_id not in _CATALOG:
        raise KeyError(f"Unknown material: {material_id}")
    return _CATALOG[material_id]


def list_materials(
    category: Optional[MaterialCategory] = None,
) -> List[Material]:
    """List materials, optionally filtered by category."""
    mats = list(_CATALOG.values())
    if category is not None:
        mats = [m for m in mats if m.category == category]
    return mats


def _bootstrap_catalog() -> None:
    """
    Register built-in materials (called once at import time).

    Merges decorative-art material definitions:
    - wood_materials.py visual entries (rosette ring previews)
    - WOOD_DESCRIPTIONS text entries (AI prompt generation)
    - inlay/shell materials (mother-of-pearl, abalone, bone)
    """
    _builtins = [
        Material(
            id="ebony", name="Ebony", category=MaterialCategory.HARDWOOD,
            base_color="#1a1008", grain_color="#0d0804",
            accent_color="#221408", highlight_color="#2a1c10",
            tight_grain=True, density_kg_m3=1100.0, janka_hardness=3220,
            prompt_description="jet black ebony with tight, barely visible grain",
        ),
        Material(
            id="maple", name="Maple", category=MaterialCategory.HARDWOOD,
            base_color="#f2e8c8", grain_color="#d8c898",
            accent_color="#f8f0d8", highlight_color="#fff8e8",
            tight_grain=True, density_kg_m3=650.0, janka_hardness=1450,
            prompt_description="creamy white maple with subtle flame figure",
        ),
        Material(
            id="rosewood", name="Rosewood", category=MaterialCategory.HARDWOOD,
            base_color="#4a1e10", grain_color="#3a1408",
            accent_color="#5a2818", highlight_color="#6a3020",
            density_kg_m3=870.0, janka_hardness=2790,
            prompt_description="deep chocolate brown rosewood with darker streaks",
        ),
        Material(
            id="abalone", name="Abalone", category=MaterialCategory.SHELL,
            base_color="#609070", grain_color="#408060",
            accent_color="#80b090", highlight_color="#80b898",
            figured=True, iridescent=True,
            prompt_description="iridescent abalone shell with blue-green-pink shimmer",
        ),
        Material(
            id="mother_of_pearl", name="Mother-of-Pearl",
            category=MaterialCategory.SHELL,
            base_color="#e8f0f8", grain_color="#c0d8f0",
            accent_color="#f0f8ff", highlight_color="#f0f8ff",
            figured=True, iridescent=True,
            prompt_description="lustrous white mother of pearl with rainbow highlights",
        ),
        Material(
            id="spruce", name="Spruce", category=MaterialCategory.TONEWOOD,
            base_color="#e8d8a0", grain_color="#c0a850",
            accent_color="#f0e0b0", highlight_color="#f8f0c0",
            tight_grain=True, density_kg_m3=420.0, janka_hardness=510,
            prompt_description="light tan spruce with gentle grain lines",
        ),
        # ... (remaining 20+ materials follow same pattern)
    ]
    for mat in _builtins:
        register_material(mat)


_bootstrap_catalog()
```

**What this solves:** Material data for decorative art is scattered across 2+ files with incompatible formats (visual dicts in `wood_materials.py`, text descriptions in `inlay_prompts.py`). This gives every decorative domain a single `get_material("ebony")` call that returns colors for rendering and prompt text for AI generation.

---

### 5. Unified DXF Exporter

```python
# art_studio/engine/export/dxf.py
"""
Single DXF R12 exporter for all decorative art domains.

Replaces:
  - calculators/inlay_calc.py generate_inlay_dxf_string()
  - calculators/inlay_calc.py _generate_basic_r12_dxf()
  - util/dxf_compat.py (still used internally, but wrapped)

Bracing DXF export stays in bracing_router.py (structural, not decorative).

Input: GeometryCollection
Output: DXF string (R12 AC1009)
"""
from __future__ import annotations

from io import StringIO
from typing import Optional

from ..geometry import GeometryCollection, Shape, ShapeType
from ...util.dxf_compat import (
    create_document,
    add_polyline,
    validate_version,
    DxfVersion,
)


def export_dxf(
    geometry: GeometryCollection,
    version: str = "R12",
    title: str = "Art Studio Export",
) -> str:
    """
    Export a GeometryCollection to DXF string.

    This is the ONE DXF exporter for the entire art engine.
    Domain-specific routers call: export_dxf(result.geometry)

    Args:
        geometry: Shapes to export.
        version: DXF version string (default R12 per project rules).
        title: Embedded title comment.

    Returns:
        DXF document as string.
    """
    ver = validate_version(version)
    doc = create_document(ver)
    msp = doc.modelspace()

    # Create layers from geometry
    seen_layers: set[str] = set()
    for shape in geometry.shapes:
        if shape.layer not in seen_layers:
            doc.layers.add(shape.layer, color=_layer_color(shape.layer))
            seen_layers.add(shape.layer)

    # Emit each shape
    for shape in geometry.shapes:
        _emit_shape(msp, shape, ver)

    stream = StringIO()
    doc.write(stream)
    return stream.getvalue()


def _emit_shape(msp, shape: Shape, version: DxfVersion) -> None:
    """Render a single Shape to DXF modelspace."""
    attribs = {"layer": shape.layer}

    if shape.shape_type == ShapeType.CIRCLE:
        msp.add_circle(
            center=shape.center,
            radius=shape.radius,
            dxfattribs=attribs,
        )

    elif shape.shape_type == ShapeType.ANNULUS:
        # Two concentric circles
        msp.add_circle(center=shape.center, radius=shape.inner_radius, dxfattribs=attribs)
        msp.add_circle(center=shape.center, radius=shape.outer_radius, dxfattribs=attribs)

    elif shape.shape_type in (ShapeType.POLYGON, ShapeType.POLYLINE):
        closed = shape.shape_type == ShapeType.POLYGON
        add_polyline(
            msp, shape.vertices, layer=shape.layer,
            closed=closed, version=version,
        )

    elif shape.shape_type == ShapeType.RECTANGLE:
        x, y = shape.origin
        pts = [
            (x, y), (x + shape.width, y),
            (x + shape.width, y + shape.height), (x, y + shape.height),
        ]
        add_polyline(msp, pts, layer=shape.layer, closed=True, version=version)

    elif shape.shape_type == ShapeType.ARC:
        msp.add_arc(
            center=shape.center,
            radius=shape.radius,
            start_angle=shape.start_angle_deg,
            end_angle=shape.end_angle_deg,
            dxfattribs=attribs,
        )


def _layer_color(layer_name: str) -> int:
    """Assign DXF color index by layer convention."""
    colors = {
        "ART_OUTLINE": 5,      # Blue
        "ART_CENTER": 1,       # Red
        "ART_FILL": 3,         # Green
        "ART_GUIDE": 8,        # Gray
        "INLAY_OUTLINE": 5,
        "INLAY_CENTER": 1,
    }
    return colors.get(layer_name, 7)  # Default white
```

**What this solves:** The two decorative-art DXF writers collapse into one. Any decorative domain that can produce a `GeometryCollection` gets free DXF export. Bracing keeps its own DXF writer since it's a structural concern.

---

### 6. Unified Snapshot Persistence

```python
# art_studio/engine/snapshot.py
"""
Domain-agnostic design snapshot persistence.

Replaces:
  - services/snapshot_store.py (rosette-only)
  - services/rosette_snapshot_store.py (rosette-specific)

Any ArtResult can be saved and restored.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .protocol import ArtDomain, ArtResult, BoundingBox


class ArtSnapshot(BaseModel):
    """
    Persisted state of any art design.

    Replaces DesignSnapshot (which was rosette-only).
    """
    snapshot_id: str
    domain: ArtDomain
    name: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(default=None, max_length=4000)
    tags: List[str] = Field(default_factory=list)

    # The design itself — serialized ArtSpec
    spec_data: Dict[str, Any] = Field(
        description="JSON-safe serialization of domain-specific ArtSpec"
    )

    # Cached geometry bounds (avoids re-computing on load)
    bounds_mm: Optional[BoundingBox] = None

    # Context references (machine, tool preset, material preset)
    context_refs: Dict[str, str] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Fingerprint for deduplication
    content_hash: Optional[str] = None
```

---

### 7. Manufacturing Bridge — Design → CAM

```python
# art_studio/engine/export/manufacturing.py
"""
Bridge from Art Studio designs to CAM execution.

Art Studio is ORNAMENT AUTHORITY (design + preview).
CAM is MACHINE AUTHORITY (toolpaths + G-code).

This bridge creates a CamIntent from an ArtResult,
respecting the RMOS boundary (Art Studio never calls CAM directly).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from ..protocol import ArtDomain, ArtResult


class ManufacturingHint(BaseModel):
    """
    Domain-specific manufacturing metadata attached to an ArtResult.

    The CAM system reads these hints when planning toolpaths.
    Art Studio produces them; CAM consumes them.
    """
    pocket_depth_mm: Optional[float] = None
    tool_diameter_suggestion_mm: Optional[float] = None
    stepover_fraction: Optional[float] = None
    operation_type: Optional[str] = Field(
        default=None,
        description="Suggested CAM operation: pocket, profile, vcarve, engrave"
    )
    notes: str = ""


def to_cam_intent(result: ArtResult, hints: ManufacturingHint) -> Dict[str, Any]:
    """
    Package an ArtResult into a CamIntentV1-compatible payload.

    This is the ONLY way Art Studio crosses the CAM boundary:
    art design → JSON artifact → CAM picks it up.

    Returns a dict ready to POST to /api/cam/... endpoints.
    """
    shapes_for_cam = []
    for shape in result.geometry.shapes:
        shapes_for_cam.append({
            "type": shape.shape_type.value,
            "vertices": shape.vertices,
            "center": shape.center,
            "radius": shape.radius,
            "depth_mm": hints.pocket_depth_mm or shape.depth_mm,
            "layer": shape.layer,
        })

    return {
        "source": "art_studio",
        "domain": result.domain,
        "geometry": shapes_for_cam,
        "bounds_mm": result.bounds_mm.model_dump(),
        "manufacturing_hints": hints.model_dump(),
    }
```

**What this solves:** Currently `_inlay_gcode_addon.py` directly imports CAM adaptive pocketing functions. The manufacturing bridge provides a clean JSON handoff that respects the CAM/Art Studio boundary fence.

---

## Domain Module Examples

### Rosette Module — Adapting Existing Code

```python
# art_studio/modules/rosette/spec.py
"""
Rosette domain module — wraps existing RosetteParamSpec
into the unified ArtSpec protocol.
"""
from __future__ import annotations

from typing import Any, Dict
from ...engine.protocol import ArtDomain, ArtSpec, BoundingBox
from ...engine.geometry import GeometryCollection, Shape, ShapeType
from ...schemas.rosette_params import RosetteParamSpec, RingParam


class RosetteArtSpec:
    """
    ArtSpec implementation for rosettes.

    Wraps the existing RosetteParamSpec (preserved as-is)
    and adds to_geometry() conversion.
    """

    def __init__(self, params: RosetteParamSpec):
        self._params = params

    @property
    def domain(self) -> ArtDomain:
        return "rosette"

    @property
    def bounds_mm(self) -> BoundingBox:
        r = self._params.outer_diameter_mm / 2
        return BoundingBox(min_x=-r, max_x=r, min_y=-r, max_y=r)

    def to_geometry(self) -> GeometryCollection:
        """Convert concentric rings to annulus shapes."""
        shapes = []
        inner_r = self._params.inner_diameter_mm / 2
        cursor = inner_r

        for ring in self._params.ring_params:
            outer = cursor + ring.width_mm
            shapes.append(Shape(
                shape_type=ShapeType.ANNULUS,
                center=(0.0, 0.0),
                inner_radius=cursor,
                outer_radius=outer,
                layer=f"RING_{ring.ring_index}",
                domain_tag="rosette",
            ))
            cursor = outer

        return GeometryCollection(shapes=shapes)

    def to_dict(self) -> Dict[str, Any]:
        return self._params.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RosetteArtSpec":
        return cls(RosetteParamSpec(**data))
```

### Inlay Module — Adapting Existing Code

```python
# art_studio/modules/inlay/spec.py
"""
Inlay domain module — wraps existing InlayCalcResult
into the unified ArtSpec protocol.
"""
from __future__ import annotations

from typing import Any, Dict
from ...engine.protocol import ArtDomain, ArtSpec, BoundingBox
from ...engine.geometry import GeometryCollection, Shape, ShapeType
from ...calculators.inlay_calc import (
    InlayCalcInput,
    InlayCalcResult,
    InlayShape,
    InlayPatternType,
    calculate_fretboard_inlays,
)


class InlayArtSpec:
    """
    ArtSpec implementation for fretboard and headstock inlays.

    Wraps InlayCalcInput → InlayCalcResult pipeline, exposing
    shapes as GeometryCollection.
    """

    def __init__(self, calc_input: InlayCalcInput):
        self._input = calc_input
        self._result: InlayCalcResult = calculate_fretboard_inlays(calc_input)

    @property
    def domain(self) -> ArtDomain:
        return "inlay"

    @property
    def bounds_mm(self) -> BoundingBox:
        b = self._result.bounds_mm
        return BoundingBox(
            min_x=b["min_x"], max_x=b["max_x"],
            min_y=b["min_y"], max_y=b["max_y"],
        )

    def to_geometry(self) -> GeometryCollection:
        """Convert InlayShapes to engine geometry."""
        shapes = []
        for inlay_shape in self._result.shapes:
            if inlay_shape.pattern_type == InlayPatternType.DOT:
                shapes.append(Shape(
                    shape_type=ShapeType.CIRCLE,
                    center=(inlay_shape.x_mm, inlay_shape.y_mm),
                    radius=inlay_shape.width_mm / 2,
                    depth_mm=inlay_shape.depth_mm,
                    layer="INLAY_OUTLINE",
                    domain_tag="inlay",
                ))
            elif inlay_shape.vertices:
                pts = [
                    (inlay_shape.x_mm + vx, inlay_shape.y_mm + vy)
                    for vx, vy in inlay_shape.vertices
                ]
                shapes.append(Shape(
                    shape_type=ShapeType.POLYGON,
                    vertices=pts,
                    depth_mm=inlay_shape.depth_mm,
                    layer="INLAY_OUTLINE",
                    domain_tag="inlay",
                ))
        return GeometryCollection(shapes=shapes)

    def to_dict(self) -> Dict[str, Any]:
        return self._input.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InlayArtSpec":
        return cls(InlayCalcInput(**data))
```

---

## Unified API Endpoints

```python
# art_studio/api/unified_router.py
"""
Unified Art Engine Router.

Single set of endpoints that work for ANY art domain.
Domain-specific convenience routes are thin wrappers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..engine.protocol import ArtDomain, ArtResult
from ..engine.registry import generate, list_generators
from ..engine.export.dxf import export_dxf


router = APIRouter(prefix="/art-studio/engine", tags=["Art Engine"])


class GenerateRequest(BaseModel):
    """Universal generate request — works for any art domain."""
    generator_key: str = Field(
        ..., description="Namespaced key, e.g. 'rosette.mosaic_band@1'"
    )
    params: Dict[str, Any] = Field(default_factory=dict)


@router.post("/generate", response_model=ArtResult)
def unified_generate(req: GenerateRequest) -> ArtResult:
    """
    Generate art for any domain.

    Examples:
        {"generator_key": "rosette.basic_rings@1",
         "params": {"outer_diameter_mm": 110, "inner_diameter_mm": 90, "ring_count": 5}}

        {"generator_key": "inlay.dot_standard@1",
         "params": {"scale_length_mm": 648, "pattern_type": "dot"}}

        {"generator_key": "bracing.x_brace@1",
         "params": {"width_mm": 12, "height_mm": 8, "length_mm": 280}}
    """
    return generate(req.generator_key, req.params)


@router.post("/export/dxf")
def unified_dxf_export(req: GenerateRequest):
    """Generate art + export as DXF R12 in one call."""
    result = generate(req.generator_key, req.params)
    dxf_string = export_dxf(result.geometry)
    return {"dxf": dxf_string, "domain": result.domain}


@router.get("/generators")
def list_all_generators(domain: Optional[ArtDomain] = None):
    """List available generators, optionally filtered by domain."""
    entries = list_generators(domain)
    return {
        "generators": [
            {
                "key": e.key,
                "domain": e.domain,
                "name": e.name,
                "description": e.description,
                "param_hints": e.param_hints,
            }
            for e in entries
        ]
    }
```

---

## Function Reference

| Function | Location | Purpose |
|----------|----------|---------|
| `generate(key, params) → ArtResult` | `engine/registry.py` | Main entry point — run any generator, return universal result |
| `register_generator(key, domain, fn, ...)` | `engine/registry.py` | Register a new generator (called at module import) |
| `list_generators(domain?) → [GeneratorEntry]` | `engine/registry.py` | Discover available generators for a domain |
| `export_dxf(geometry, version?) → str` | `engine/export/dxf.py` | Convert GeometryCollection to DXF R12 string |
| `to_cam_intent(result, hints) → dict` | `engine/export/manufacturing.py` | Bridge design → CAM intent (JSON, respects boundary) |
| `get_material(id) → Material` | `engine/materials.py` | Look up material by ID for any domain |
| `list_materials(category?) → [Material]` | `engine/materials.py` | List available materials |
| `spec.to_geometry() → GeometryCollection` | Each `modules/*/spec.py` | Convert domain spec to engine-neutral geometry |
| `spec.to_dict() → dict` | Each `modules/*/spec.py` | Serialize for snapshot persistence |
| `ArtSpec.from_dict(data) → ArtSpec` | Each `modules/*/spec.py` | Restore from snapshot |
| `render_preview_svg(geometry) → str` | `engine/export/svg.py` | Render GeometryCollection to SVG preview string |

---

## Migration Path

### Phase 1 — Foundation (No Breaking Changes)
1. Create `art_studio/engine/` with `protocol.py`, `geometry.py`, `materials.py`
2. Implement `RosetteArtSpec` and `InlayArtSpec` as adapters over existing code
3. Create `engine/export/dxf.py` wrapping existing `dxf_compat` utility
4. Add `engine/registry.py` (new) alongside existing `services/generators/registry.py`
5. **Existing routers continue to work unchanged**

### Phase 2 — Wire Unified Endpoints
1. Add `api/unified_router.py` with `/art-studio/engine/generate` endpoint
2. Register existing rosette generators (`basic_rings`, `mosaic_band`) in new registry
3. Register inlay presets as generators
4. **Old domain-specific routers still work — dual-path**

### Phase 3 — Snapshot Migration
1. Create `engine/snapshot.py` with `ArtSnapshot` model
2. Write migration for existing `DesignSnapshot` → `ArtSnapshot`
3. All domains store snapshots through uniform API

### Phase 4 — Marquetry Domain
1. Add `modules/marquetry/` (inherits inlay shapes + adds tessellation/tile-fill algorithms)
2. Register marquetry generators (herringbone, checkerboard, custom tile patterns)
3. Gets free DXF export, snapshot persistence, and material references from the engine

### Phase 5 — Consolidate & Deprecate
1. Mark old domain-specific routers as deprecated (keep alive for frontend compat)
2. Migrate frontend SDK to use unified `/art-studio/engine/*` endpoints
3. Remove old DXF generation code from `inlay_calc.py`
4. Merge `services/generators/registry.py` into `engine/registry.py`

---

## Boundary Rules (Enforced)

| Boundary | Rule |
|----------|------|
| Art Studio → CAM | JSON artifact only (`to_cam_intent()`). No direct import of `app.cam.*` inside `art_studio/engine/` or `art_studio/modules/` |
| CAM → Art Studio | Never. CAM reads JSON artifacts, doesn't import art modules |
| Engine → Modules | Engine imports module specs via protocol only (duck typing / `ArtSpec`) |
| Modules → Engine | Modules import `engine.geometry`, `engine.protocol`, `engine.materials` |
| Routers → Engine | Routers call `engine.registry.generate()` and exporters. Never call module internals |
| `_inlay_gcode_addon.py` | Moves to CAM or uses `to_cam_intent()` bridge. No more direct CAM imports in Art Studio |

---

## What This Enables

| Capability | Before | After |
|------------|--------|-------|
| Add new art domain | Create router + models + DXF writer + presets | Implement `ArtSpec`, register generator |
| DXF export | Rewrite per domain (3 implementations) | `export_dxf(result.geometry)` |
| SVG preview | Rewrite per domain (2 custom renderers) | `render_preview_svg(result.geometry)` |
| Material lookup | Check 3 files, different formats | `get_material("ebony")` |
| Save/load designs | Rosettes only | Any domain — `ArtSnapshot` |
| Design → CNC | Hardcoded per-domain bridges | `to_cam_intent(result, hints)` |
| List available generators | Rosettes only | `list_generators("inlay")` |
| Marquetry support | Not possible without new plumbing | Implement `MarquetryArtSpec` and register |

---

## What Stays Outside the Engine

| Domain | Current Location | Status |
|--------|-----------------|--------|
| **Bracing** | `bracing_router.py` + `calculators/bracing_calc.py` | Stays as-is. Structural calculation, not decorative art. Has its own DXF export, presets, and section profile math. |
| **Relief** | `relief_router.py` + `svg_ingest_service.py` | Stays as-is. SVG→polyline parsing for CNC depth carving. May migrate to CAM. |
| **V-Carve** | `vcarve_router.py` + `svg_ingest_service.py` | Stays as-is. SVG→polyline parsing for CNC engraving. May migrate to CAM. |

These three share `svg_ingest_service.py` for SVG parsing, which is a utility concern — not art generation. That service can remain a shared utility without being part of the art engine.
