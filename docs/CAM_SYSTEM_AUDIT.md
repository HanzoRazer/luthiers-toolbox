# CAM System Audit

**Version:** 1.0.0
**Date:** 2026-01-13
**Status:** ~62% Production-Ready
**Purpose:** Developer guide for completing CAM system gaps

---

## Executive Summary

The CAM (Computer-Aided Manufacturing) system is the **core manufacturing engine** of luthiers-toolbox. While the algorithmic foundation is solid (toolpath generation, G-code emission, post-processors), critical user-facing infrastructure is missing. This document provides **actionable developer guidance** with specific code locations, reference implementations, and integration patterns.

**Key Finding:** The gap is not algorithmic—it's infrastructure. The math works; the user experience doesn't.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  ├── cam_pipeline_router.py      - Unified pipeline runner      │
│  ├── cam/routers/rosette/        - Rosette CAM operations       │
│  ├── cam_roughing_router.py      - Rectangular roughing         │
│  └── cam_simulate_router.py      - G-code simulation            │
├─────────────────────────────────────────────────────────────────┤
│                    SERVICE LAYER                                 │
│  ├── art_jobs_store.py           - Job persistence (JSON)       │
│  ├── pipeline_ops_rosette.py     - Pipeline orchestration       │
│  └── cam_sim_bridge.py           - Simulation bridge            │
├─────────────────────────────────────────────────────────────────┤
│                    CORE COMPUTATION LAYER                        │
│  ├── cam_core/feeds_speeds/      - ❌ STUB (needs work)         │
│  ├── cam_core/tools/             - ⚠️ PARTIAL (registry works)  │
│  ├── cam/rosette/cnc/            - ✅ WORKING (safety, feeds)   │
│  └── cam/adaptive_core*.py       - ✅ WORKING (toolpaths)       │
├─────────────────────────────────────────────────────────────────┤
│                    DATA LAYER                                    │
│  ├── data/art_jobs.json          - Job storage                  │
│  ├── data/cam_core/tools.json    - Tool library                 │
│  └── data/posts/*.json           - Post-processor configs       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Gap Analysis Summary

| Gap | Location | Current State | Completeness | Priority | Hours |
|-----|----------|---------------|--------------|----------|-------|
| **Feeds & Speeds Calculator** | `cam_core/feeds_speeds/` | STUB | 5% | **HIGH** | 8h |
| **Material Database** | `cam_core/feeds_speeds/materials.py` | 2 materials | 20% | **HIGH** | 4h |
| **3D Visualization** | `CamBackplot3D.vue` | Working but basic | 85% | MEDIUM | 6h |
| **Job Persistence** | `art_jobs_store.py` | Working, needs status | 70% | MEDIUM | 4h |
| **Collision Detection** | `cnc_safety_validator.py` | Envelope only | 40% | **HIGH** | 6h |
| **Tool Importers** | `cam_core/tools/importers/` | All STUB | 0% | MEDIUM | 6h |

**Total Estimated Hours to MVP: ~50 hours**

---

## 3. Gap #1: Feeds & Speeds Calculator

### Current State: STUB (Returns Zeros)

**File:** `services/api/app/cam_core/feeds_speeds/calculator.py`

```python
# CURRENT IMPLEMENTATION (lines 1-20)
def calculate_feed_plan(tool: Dict[str, Any], material: str, strategy: str) -> Dict[str, Any]:
    """Return a placeholder feed plan structure."""
    return {
        "tool_id": tool.get("id"),
        "material": material,
        "strategy": strategy,
        "feed_xy": 0.0,      # ❌ NOT IMPLEMENTED
        "feed_z": 0.0,       # ❌ NOT IMPLEMENTED
        "rpm": 0.0,          # ❌ NOT IMPLEMENTED
        "notes": "Feeds & speeds calculator not implemented.",
    }
```

### Reference Implementation (Working Code)

**File:** `services/api/app/cam/rosette/cnc/cnc_materials.py` (lines 1-80)

```python
# THIS PATTERN WORKS - USE AS REFERENCE
from dataclasses import dataclass
from enum import Enum

class MaterialType(str, Enum):
    HARDWOOD = "hardwood"
    SOFTWOOD = "softwood"
    COMPOSITE = "composite"
    MDF = "mdf"
    PLYWOOD = "plywood"

@dataclass
class FeedRule:
    material: MaterialType
    feed_recommend_mm_per_min: float
    feed_max_mm_per_min: float
    spindle_rpm: int
    max_z_step_mm: float  # per-pass depth limit

_MATERIAL_FEED_RULES: Dict[MaterialType, FeedRule] = {
    MaterialType.HARDWOOD: FeedRule(
        material=MaterialType.HARDWOOD,
        feed_recommend_mm_per_min=800.0,
        feed_max_mm_per_min=1200.0,
        spindle_rpm=16000,
        max_z_step_mm=0.5,
    ),
    MaterialType.SOFTWOOD: FeedRule(
        material=MaterialType.SOFTWOOD,
        feed_recommend_mm_per_min=900.0,
        feed_max_mm_per_min=1300.0,
        spindle_rpm=17000,
        max_z_step_mm=0.6,
    ),
}
```

### Implementation Guide

**Step 1: Create Chipload Database**

Create new file: `services/api/app/cam_core/feeds_speeds/chipload_db.py`

```python
"""
Chipload database for feed/speed calculations.
Reference: Machinery's Handbook, tool manufacturer specs
"""
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

class ToolMaterial(str, Enum):
    HSS = "hss"           # High Speed Steel
    CARBIDE = "carbide"   # Solid Carbide
    COATED = "coated"     # Coated Carbide (TiN, TiAlN)

class WorkMaterial(str, Enum):
    HARDWOOD = "hardwood"
    SOFTWOOD = "softwood"
    MDF = "mdf"
    PLYWOOD = "plywood"
    ALUMINUM = "aluminum"
    ACRYLIC = "acrylic"
    BRASS = "brass"

@dataclass(frozen=True)
class ChiploadEntry:
    """Chipload per tooth (mm) for tool/material combination."""
    tool_material: ToolMaterial
    work_material: WorkMaterial
    diameter_min_mm: float
    diameter_max_mm: float
    chipload_min_mm: float
    chipload_max_mm: float
    chipload_recommend_mm: float
    surface_speed_m_min: float  # For RPM calculation
    notes: str = ""

# Chipload lookup table - expand as needed
CHIPLOAD_TABLE: list[ChiploadEntry] = [
    # Carbide in Hardwood
    ChiploadEntry(
        tool_material=ToolMaterial.CARBIDE,
        work_material=WorkMaterial.HARDWOOD,
        diameter_min_mm=3.0,
        diameter_max_mm=6.0,
        chipload_min_mm=0.05,
        chipload_max_mm=0.15,
        chipload_recommend_mm=0.08,
        surface_speed_m_min=300.0,
        notes="Conservative for hardwoods like maple, oak"
    ),
    ChiploadEntry(
        tool_material=ToolMaterial.CARBIDE,
        work_material=WorkMaterial.HARDWOOD,
        diameter_min_mm=6.0,
        diameter_max_mm=12.0,
        chipload_min_mm=0.08,
        chipload_max_mm=0.20,
        chipload_recommend_mm=0.12,
        surface_speed_m_min=350.0,
    ),
    # Carbide in Softwood
    ChiploadEntry(
        tool_material=ToolMaterial.CARBIDE,
        work_material=WorkMaterial.SOFTWOOD,
        diameter_min_mm=3.0,
        diameter_max_mm=6.0,
        chipload_min_mm=0.08,
        chipload_max_mm=0.20,
        chipload_recommend_mm=0.12,
        surface_speed_m_min=400.0,
    ),
    # Carbide in MDF
    ChiploadEntry(
        tool_material=ToolMaterial.CARBIDE,
        work_material=WorkMaterial.MDF,
        diameter_min_mm=3.0,
        diameter_max_mm=12.0,
        chipload_min_mm=0.10,
        chipload_max_mm=0.25,
        chipload_recommend_mm=0.15,
        surface_speed_m_min=500.0,
        notes="MDF dulls tools faster - use sharp bits"
    ),
    # Carbide in Aluminum
    ChiploadEntry(
        tool_material=ToolMaterial.CARBIDE,
        work_material=WorkMaterial.ALUMINUM,
        diameter_min_mm=3.0,
        diameter_max_mm=12.0,
        chipload_min_mm=0.02,
        chipload_max_mm=0.08,
        chipload_recommend_mm=0.04,
        surface_speed_m_min=250.0,
        notes="Use single-flute or O-flute for chip clearance"
    ),
]

def lookup_chipload(
    tool_material: ToolMaterial,
    work_material: WorkMaterial,
    diameter_mm: float,
) -> Optional[ChiploadEntry]:
    """Find chipload entry for tool/material/diameter combination."""
    for entry in CHIPLOAD_TABLE:
        if (entry.tool_material == tool_material and
            entry.work_material == work_material and
            entry.diameter_min_mm <= diameter_mm <= entry.diameter_max_mm):
            return entry
    return None
```

**Step 2: Implement Calculator Logic**

Replace `services/api/app/cam_core/feeds_speeds/calculator.py`:

```python
"""
Feeds & Speeds Calculator
Computes optimal cutting parameters based on tool, material, and machine limits.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
import math

from .chipload_db import lookup_chipload, ToolMaterial, WorkMaterial, ChiploadEntry


@dataclass
class FeedSpeedResult:
    """Calculated feed and speed parameters."""
    tool_id: str
    material: str
    strategy: str

    # Calculated values
    rpm: int
    feed_xy_mm_min: float
    feed_z_mm_min: float
    plunge_mm_min: float

    # Derived metrics
    chipload_mm: float
    surface_speed_m_min: float
    material_removal_rate_cm3_min: float

    # Validation
    warnings: list[str]
    is_valid: bool
    notes: str


def calculate_rpm(surface_speed_m_min: float, diameter_mm: float) -> int:
    """
    Calculate spindle RPM from surface speed and tool diameter.

    Formula: RPM = (Surface Speed × 1000) / (π × Diameter)
    """
    if diameter_mm <= 0:
        return 0
    rpm = (surface_speed_m_min * 1000) / (math.pi * diameter_mm)
    return int(round(rpm, -2))  # Round to nearest 100


def calculate_feed_rate(
    rpm: int,
    flute_count: int,
    chipload_mm: float,
) -> float:
    """
    Calculate feed rate from RPM, flute count, and chipload.

    Formula: Feed = RPM × Flutes × Chipload
    """
    return rpm * flute_count * chipload_mm


def calculate_feed_plan(
    tool: Dict[str, Any],
    material: str,
    strategy: str,
    machine_max_rpm: int = 24000,
    machine_max_feed_mm_min: float = 5000.0,
) -> FeedSpeedResult:
    """
    Calculate optimal feed and speed parameters.

    Args:
        tool: Tool definition with diameter_mm, flute_count, tool_material
        material: Work material name (hardwood, softwood, etc.)
        strategy: Cutting strategy (roughing, finishing, adaptive)
        machine_max_rpm: Machine spindle limit
        machine_max_feed_mm_min: Machine feed limit

    Returns:
        FeedSpeedResult with calculated parameters
    """
    warnings = []

    # Extract tool parameters
    tool_id = tool.get("id", "unknown")
    diameter_mm = tool.get("diameter_mm", 6.0)
    flute_count = tool.get("flute_count", 2)
    tool_material_str = tool.get("tool_material", "carbide")

    # Map to enums
    try:
        tool_material = ToolMaterial(tool_material_str.lower())
    except ValueError:
        tool_material = ToolMaterial.CARBIDE
        warnings.append(f"Unknown tool material '{tool_material_str}', defaulting to carbide")

    try:
        work_material = WorkMaterial(material.lower())
    except ValueError:
        work_material = WorkMaterial.HARDWOOD
        warnings.append(f"Unknown material '{material}', defaulting to hardwood")

    # Lookup chipload
    chipload_entry = lookup_chipload(tool_material, work_material, diameter_mm)

    if chipload_entry is None:
        # Fallback to conservative defaults
        warnings.append(f"No chipload data for {tool_material}/{work_material}/{diameter_mm}mm, using conservative defaults")
        chipload_mm = 0.05
        surface_speed_m_min = 200.0
    else:
        # Adjust chipload based on strategy
        if strategy == "roughing":
            chipload_mm = chipload_entry.chipload_recommend_mm * 1.0
        elif strategy == "finishing":
            chipload_mm = chipload_entry.chipload_recommend_mm * 0.5
        elif strategy == "adaptive":
            chipload_mm = chipload_entry.chipload_recommend_mm * 1.2
        else:
            chipload_mm = chipload_entry.chipload_recommend_mm

        surface_speed_m_min = chipload_entry.surface_speed_m_min

    # Calculate RPM
    rpm = calculate_rpm(surface_speed_m_min, diameter_mm)

    # Apply machine limits
    if rpm > machine_max_rpm:
        warnings.append(f"Calculated RPM {rpm} exceeds machine limit {machine_max_rpm}, clamping")
        rpm = machine_max_rpm

    # Calculate feed rate
    feed_xy_mm_min = calculate_feed_rate(rpm, flute_count, chipload_mm)

    # Apply machine feed limit
    if feed_xy_mm_min > machine_max_feed_mm_min:
        warnings.append(f"Calculated feed {feed_xy_mm_min:.0f} exceeds limit {machine_max_feed_mm_min:.0f}, clamping")
        feed_xy_mm_min = machine_max_feed_mm_min
        # Recalculate effective chipload
        chipload_mm = feed_xy_mm_min / (rpm * flute_count)

    # Z feed (typically 30-50% of XY feed)
    feed_z_mm_min = feed_xy_mm_min * 0.4
    plunge_mm_min = feed_xy_mm_min * 0.3

    # Calculate MRR (simplified)
    stepover_mm = diameter_mm * 0.4  # 40% stepover assumption
    stepdown_mm = diameter_mm * 0.5  # 50% depth assumption
    mrr_cm3_min = (feed_xy_mm_min * stepover_mm * stepdown_mm) / 1000.0

    is_valid = len([w for w in warnings if "exceeds" in w.lower()]) == 0

    return FeedSpeedResult(
        tool_id=tool_id,
        material=material,
        strategy=strategy,
        rpm=rpm,
        feed_xy_mm_min=round(feed_xy_mm_min, 1),
        feed_z_mm_min=round(feed_z_mm_min, 1),
        plunge_mm_min=round(plunge_mm_min, 1),
        chipload_mm=round(chipload_mm, 4),
        surface_speed_m_min=round(surface_speed_m_min, 1),
        material_removal_rate_cm3_min=round(mrr_cm3_min, 2),
        warnings=warnings,
        is_valid=is_valid,
        notes=chipload_entry.notes if chipload_entry else "",
    )
```

**Step 3: Add API Endpoint**

Add to `services/api/app/cam_core/cam_core_router.py`:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from .feeds_speeds.calculator import calculate_feed_plan, FeedSpeedResult

router = APIRouter(prefix="/cam-core", tags=["CAM Core"])


class FeedSpeedRequest(BaseModel):
    tool_id: str
    tool_diameter_mm: float = Field(..., gt=0)
    tool_flute_count: int = Field(default=2, ge=1)
    tool_material: str = Field(default="carbide")
    work_material: str = Field(..., description="hardwood, softwood, mdf, etc.")
    strategy: str = Field(default="roughing", description="roughing, finishing, adaptive")
    machine_max_rpm: int = Field(default=24000, gt=0)
    machine_max_feed_mm_min: float = Field(default=5000.0, gt=0)


class FeedSpeedResponse(BaseModel):
    tool_id: str
    material: str
    strategy: str
    rpm: int
    feed_xy_mm_min: float
    feed_z_mm_min: float
    plunge_mm_min: float
    chipload_mm: float
    surface_speed_m_min: float
    material_removal_rate_cm3_min: float
    warnings: List[str]
    is_valid: bool
    notes: str


@router.post("/feeds-speeds/calculate", response_model=FeedSpeedResponse)
def calculate_feeds_speeds(request: FeedSpeedRequest) -> FeedSpeedResponse:
    """
    Calculate optimal feed and speed parameters for a tool/material combination.

    Returns RPM, feed rates, chipload, and validation warnings.
    """
    tool = {
        "id": request.tool_id,
        "diameter_mm": request.tool_diameter_mm,
        "flute_count": request.tool_flute_count,
        "tool_material": request.tool_material,
    }

    result = calculate_feed_plan(
        tool=tool,
        material=request.work_material,
        strategy=request.strategy,
        machine_max_rpm=request.machine_max_rpm,
        machine_max_feed_mm_min=request.machine_max_feed_mm_min,
    )

    return FeedSpeedResponse(**result.__dict__)
```

**Step 4: Register Router in main.py**

Add to `services/api/app/main.py`:

```python
from .cam_core.cam_core_router import router as cam_core_router

# In router registration section:
app.include_router(cam_core_router)
```

---

## 4. Gap #2: Collision Detection

### Current State: Envelope Checking Only

**File:** `services/api/app/cam/rosette/cnc/cnc_safety_validator.py`

```python
# CURRENT: Only checks if points are inside machine envelope
def evaluate_cnc_safety(toolpaths, envelope, ...):
    # 1) Envelope checks - point inside bounds ✅
    # 2) Feed validation ✅
    # 3) Kerf drift validation ✅
    # ❌ NO tool-workpiece collision detection
    # ❌ NO tool-fixture collision detection
```

### Implementation Guide

**Step 1: Add Collision Detection Module**

Create: `services/api/app/cam/collision_detector.py`

```python
"""
Collision Detection for CAM Operations

Detects potential collisions between:
- Tool and workpiece (gouging)
- Tool and fixtures/clamps
- Tool at different Z-passes (stacking violations)
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum
import math


class CollisionType(str, Enum):
    GOUGE = "gouge"           # Tool cuts too deep
    FIXTURE = "fixture"       # Tool hits clamp/fixture
    RAPID_PLUNGE = "rapid_plunge"  # Rapid move into material
    Z_STACK = "z_stack"       # Multi-pass Z interference


@dataclass
class CollisionZone:
    """Represents a potential collision area."""
    collision_type: CollisionType
    x: float
    y: float
    z: float
    severity: str  # "warning", "error", "critical"
    description: str
    move_index: int
    suggested_fix: str = ""


@dataclass
class ToolGeometry:
    """Tool dimensions for collision checking."""
    diameter_mm: float
    flute_length_mm: float
    overall_length_mm: float
    shank_diameter_mm: float = 0.0

    @property
    def radius_mm(self) -> float:
        return self.diameter_mm / 2.0


@dataclass
class WorkpieceGeometry:
    """Workpiece bounds for collision checking."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_top: float      # Top surface Z
    z_bottom: float   # Bottom surface Z (stock bottom)


@dataclass
class FixtureZone:
    """Defines a fixture/clamp exclusion zone."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    name: str = "fixture"


@dataclass
class Move:
    """Represents a single toolpath move."""
    index: int
    x: float
    y: float
    z: float
    is_rapid: bool = False
    feed_rate: float = 0.0


def check_gouge(
    move: Move,
    tool: ToolGeometry,
    workpiece: WorkpieceGeometry,
    intended_depth: float,
    tolerance_mm: float = 0.1,
) -> Optional[CollisionZone]:
    """
    Check if tool gouges deeper than intended.

    Gouge occurs when:
    - Z is lower than intended cutting depth
    - Tool penetrates beyond programmed depth
    """
    if move.z < (workpiece.z_top - intended_depth - tolerance_mm):
        overcut = abs(move.z - (workpiece.z_top - intended_depth))
        return CollisionZone(
            collision_type=CollisionType.GOUGE,
            x=move.x,
            y=move.y,
            z=move.z,
            severity="critical" if overcut > 1.0 else "warning",
            description=f"Tool gouges {overcut:.2f}mm deeper than intended",
            move_index=move.index,
            suggested_fix=f"Adjust Z to {workpiece.z_top - intended_depth:.2f}mm",
        )
    return None


def check_fixture_collision(
    move: Move,
    tool: ToolGeometry,
    fixtures: List[FixtureZone],
) -> Optional[CollisionZone]:
    """
    Check if tool collides with fixture/clamp zones.

    Uses tool radius to check swept volume, not just center point.
    """
    tool_radius = tool.radius_mm

    for fixture in fixtures:
        # Check if tool swept volume intersects fixture
        tool_x_min = move.x - tool_radius
        tool_x_max = move.x + tool_radius
        tool_y_min = move.y - tool_radius
        tool_y_max = move.y + tool_radius

        x_overlap = (tool_x_min < fixture.x_max) and (tool_x_max > fixture.x_min)
        y_overlap = (tool_y_min < fixture.y_max) and (tool_y_max > fixture.y_min)
        z_overlap = (move.z < fixture.z_max) and (move.z > fixture.z_min)

        if x_overlap and y_overlap and z_overlap:
            return CollisionZone(
                collision_type=CollisionType.FIXTURE,
                x=move.x,
                y=move.y,
                z=move.z,
                severity="critical",
                description=f"Tool collides with fixture '{fixture.name}'",
                move_index=move.index,
                suggested_fix="Add fixture clearance or reposition clamp",
            )
    return None


def check_rapid_into_material(
    move: Move,
    prev_move: Optional[Move],
    workpiece: WorkpieceGeometry,
) -> Optional[CollisionZone]:
    """
    Check if rapid move plunges into material.

    Rapid moves should never go below stock top surface.
    """
    if not move.is_rapid:
        return None

    if move.z < workpiece.z_top:
        return CollisionZone(
            collision_type=CollisionType.RAPID_PLUNGE,
            x=move.x,
            y=move.y,
            z=move.z,
            severity="critical",
            description=f"Rapid move plunges {workpiece.z_top - move.z:.2f}mm into material",
            move_index=move.index,
            suggested_fix=f"Add safe retract to Z={workpiece.z_top + 5:.2f}mm before rapid",
        )
    return None


def detect_collisions(
    moves: List[Move],
    tool: ToolGeometry,
    workpiece: WorkpieceGeometry,
    fixtures: List[FixtureZone],
    intended_depth: float,
) -> List[CollisionZone]:
    """
    Run all collision checks on a toolpath.

    Returns list of collision zones sorted by severity.
    """
    collisions: List[CollisionZone] = []

    prev_move = None
    for move in moves:
        # Check gouge
        gouge = check_gouge(move, tool, workpiece, intended_depth)
        if gouge:
            collisions.append(gouge)

        # Check fixture collision
        fixture_hit = check_fixture_collision(move, tool, fixtures)
        if fixture_hit:
            collisions.append(fixture_hit)

        # Check rapid into material
        rapid_plunge = check_rapid_into_material(move, prev_move, workpiece)
        if rapid_plunge:
            collisions.append(rapid_plunge)

        prev_move = move

    # Sort by severity (critical first)
    severity_order = {"critical": 0, "error": 1, "warning": 2}
    collisions.sort(key=lambda c: severity_order.get(c.severity, 3))

    return collisions


# Example usage in router:
"""
@router.post("/validate-collisions")
def validate_collisions(request: CollisionCheckRequest):
    moves = [Move(**m) for m in request.moves]
    tool = ToolGeometry(**request.tool)
    workpiece = WorkpieceGeometry(**request.workpiece)
    fixtures = [FixtureZone(**f) for f in request.fixtures]

    collisions = detect_collisions(
        moves=moves,
        tool=tool,
        workpiece=workpiece,
        fixtures=fixtures,
        intended_depth=request.intended_depth,
    )

    return {
        "collision_count": len(collisions),
        "has_critical": any(c.severity == "critical" for c in collisions),
        "collisions": [asdict(c) for c in collisions],
    }
"""
```

**Step 2: Integrate with Safety Validator**

Update `services/api/app/cam/rosette/cnc/cnc_safety_validator.py`:

```python
from ...collision_detector import detect_collisions, Move, ToolGeometry, WorkpieceGeometry

def evaluate_cnc_safety(
    toolpaths: ToolpathPlan,
    envelope: MachineEnvelope,
    tool: Optional[ToolGeometry] = None,
    workpiece: Optional[WorkpieceGeometry] = None,
    fixtures: Optional[List[FixtureZone]] = None,
    intended_depth: float = 0.0,
    # ... existing params
) -> CNCSafetyDecision:
    """Extended safety validation with collision detection."""

    # Existing checks...

    # NEW: Collision detection
    if tool and workpiece:
        moves = [
            Move(index=i, x=seg.end_x, y=seg.end_y, z=seg.end_z, is_rapid=seg.is_rapid)
            for i, seg in enumerate(toolpaths.segments)
        ]

        collisions = detect_collisions(
            moves=moves,
            tool=tool,
            workpiece=workpiece,
            fixtures=fixtures or [],
            intended_depth=intended_depth,
        )

        for collision in collisions:
            if collision.severity == "critical":
                decision.is_safe = False
            decision.warnings.append(f"[{collision.collision_type}] {collision.description}")

    return decision
```

---

## 5. Gap #3: Job Persistence Enhancement

### Current State: Working but Basic

**File:** `services/api/app/services/art_jobs_store.py`

```python
# CURRENT: Simple job storage without status tracking
@dataclass
class ArtJob:
    id: str
    job_type: str
    created_at: float
    # ... basic fields
    # ❌ NO status field
    # ❌ NO execution history
    # ❌ NO checkpoint support
```

### Implementation Guide

**Step 1: Extend Job Model**

Update `services/api/app/services/art_jobs_store.py`:

```python
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Literal
from pathlib import Path
import json
import time
import uuid
import threading

JobStatus = Literal["pending", "queued", "running", "completed", "failed", "cancelled"]

@dataclass
class JobCheckpoint:
    """Intermediate state checkpoint."""
    checkpoint_id: str
    timestamp: float
    stage: str
    progress_percent: float
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobExecutionLog:
    """Execution event log entry."""
    timestamp: float
    level: str  # "info", "warning", "error"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CamJob:
    """Enhanced CAM job with full lifecycle tracking."""
    id: str
    job_type: str
    created_at: float

    # Status tracking
    status: JobStatus = "pending"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Configuration
    tool_id: Optional[str] = None
    material: Optional[str] = None
    post_preset: Optional[str] = None

    # Results
    gcode_lines: Optional[int] = None
    estimated_runtime_sec: Optional[float] = None
    output_file: Optional[str] = None

    # Execution tracking
    checkpoints: List[JobCheckpoint] = field(default_factory=list)
    execution_logs: List[JobExecutionLog] = field(default_factory=list)
    error_message: Optional[str] = None

    # Metadata
    meta: Dict[str, Any] = field(default_factory=dict)

    def add_checkpoint(self, stage: str, progress: float, data: Dict[str, Any] = None):
        """Add execution checkpoint."""
        self.checkpoints.append(JobCheckpoint(
            checkpoint_id=str(uuid.uuid4())[:8],
            timestamp=time.time(),
            stage=stage,
            progress_percent=progress,
            data=data or {},
        ))

    def log(self, level: str, message: str, details: Dict[str, Any] = None):
        """Add execution log entry."""
        self.execution_logs.append(JobExecutionLog(
            timestamp=time.time(),
            level=level,
            message=message,
            details=details or {},
        ))

    def start(self):
        """Mark job as started."""
        self.status = "running"
        self.started_at = time.time()
        self.log("info", "Job started")

    def complete(self, gcode_lines: int = None, runtime_sec: float = None):
        """Mark job as completed."""
        self.status = "completed"
        self.completed_at = time.time()
        self.gcode_lines = gcode_lines
        self.estimated_runtime_sec = runtime_sec
        self.log("info", f"Job completed: {gcode_lines} lines, {runtime_sec:.1f}s estimated")

    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = "failed"
        self.completed_at = time.time()
        self.error_message = error_message
        self.log("error", f"Job failed: {error_message}")


# Thread-safe storage
_lock = threading.Lock()
JOBS_PATH = Path("data/cam_jobs.json")


def _ensure_dir():
    JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_jobs() -> List[Dict[str, Any]]:
    _ensure_dir()
    if not JOBS_PATH.exists():
        return []
    with open(JOBS_PATH, "r") as f:
        return json.load(f)


def _save_jobs(jobs: List[Dict[str, Any]]):
    _ensure_dir()
    with open(JOBS_PATH, "w") as f:
        json.dump(jobs, f, indent=2, default=str)


def create_cam_job(
    job_type: str,
    tool_id: str = None,
    material: str = None,
    post_preset: str = None,
    meta: Dict[str, Any] = None,
) -> CamJob:
    """Create a new CAM job."""
    job = CamJob(
        id=str(uuid.uuid4()),
        job_type=job_type,
        created_at=time.time(),
        tool_id=tool_id,
        material=material,
        post_preset=post_preset,
        meta=meta or {},
    )

    with _lock:
        jobs = _load_jobs()
        jobs.append(asdict(job))
        _save_jobs(jobs)

    return job


def get_cam_job(job_id: str) -> Optional[CamJob]:
    """Retrieve a CAM job by ID."""
    with _lock:
        jobs = _load_jobs()

    for job_dict in jobs:
        if job_dict.get("id") == job_id:
            # Reconstruct nested dataclasses
            checkpoints = [JobCheckpoint(**cp) for cp in job_dict.get("checkpoints", [])]
            logs = [JobExecutionLog(**log) for log in job_dict.get("execution_logs", [])]
            job_dict["checkpoints"] = checkpoints
            job_dict["execution_logs"] = logs
            return CamJob(**job_dict)
    return None


def update_cam_job(job: CamJob) -> CamJob:
    """Update an existing CAM job."""
    with _lock:
        jobs = _load_jobs()
        for i, job_dict in enumerate(jobs):
            if job_dict.get("id") == job.id:
                jobs[i] = asdict(job)
                _save_jobs(jobs)
                return job
    raise ValueError(f"Job {job.id} not found")


def list_cam_jobs(
    status: Optional[JobStatus] = None,
    job_type: Optional[str] = None,
    limit: int = 50,
) -> List[CamJob]:
    """List CAM jobs with optional filtering."""
    with _lock:
        jobs = _load_jobs()

    result = []
    for job_dict in jobs:
        if status and job_dict.get("status") != status:
            continue
        if job_type and job_dict.get("job_type") != job_type:
            continue
        result.append(CamJob(**job_dict))

    # Sort by created_at descending
    result.sort(key=lambda j: j.created_at, reverse=True)
    return result[:limit]
```

---

## 6. Gap #4: Tool Library Importers

### Current State: All Stubs

**Files:** `services/api/app/cam_core/tools/importers/`

```python
# carbide_importer.py - STUB
def import_carbide_tool_library(payload):
    return {"tools": [], "presets": []}

# fusion_importer.py - STUB
def import_fusion_tool_library(payload):
    return {"tools": [], "presets": []}

# vectric_importer.py - STUB
def import_vectric_tool_library(payload):
    return {"tools": [], "presets": []}
```

### Implementation Guide

**Step 1: Implement Fusion 360 Importer**

Update `services/api/app/cam_core/tools/importers/fusion_importer.py`:

```python
"""
Fusion 360 Tool Library Importer

Parses Fusion 360's tool library JSON export format.
Export via: Manage > Tool Library > Export
"""
from typing import Dict, Any, List, Optional
import json

from ..models import RouterBitTool, SawBladeTool, DrillBitTool, ToolPreset


def import_fusion_tool_library(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Import tools from Fusion 360 JSON export.

    Fusion 360 format:
    {
        "version": 2,
        "tools": [
            {
                "guid": "...",
                "type": "flat end mill",
                "unit": "millimeters",
                "geometry": {
                    "DC": 6.0,          # Cutter diameter
                    "HAND": true,       # Right hand
                    "LB": 50.0,         # Body length
                    "LCF": 20.0,        # Flute length
                    "NOF": 2,           # Number of flutes
                    "OAL": 75.0,        # Overall length
                    "SFDM": 6.0,        # Shank diameter
                },
                "start-values": {
                    "presets": [
                        {
                            "name": "Hardwood Roughing",
                            "n": 18000,     # RPM
                            "f_n": 0.1,     # Feed per revolution
                            "f_z": 0.05,    # Feed per tooth
                        }
                    ]
                }
            }
        ]
    }
    """
    tools_out = []
    presets_out = []
    errors = []

    fusion_tools = payload.get("tools", [])
    unit_system = payload.get("unit", "millimeters")
    unit_multiplier = 1.0 if unit_system == "millimeters" else 25.4

    for idx, fusion_tool in enumerate(fusion_tools):
        try:
            tool_type = fusion_tool.get("type", "").lower()
            geometry = fusion_tool.get("geometry", {})
            guid = fusion_tool.get("guid", f"fusion_{idx}")

            # Extract geometry with unit conversion
            diameter = geometry.get("DC", 0) * unit_multiplier
            flute_count = geometry.get("NOF", 2)
            flute_length = geometry.get("LCF", 0) * unit_multiplier
            overall_length = geometry.get("OAL", 0) * unit_multiplier
            shank_diameter = geometry.get("SFDM", diameter) * unit_multiplier

            # Map Fusion tool type to our types
            if "mill" in tool_type or "end" in tool_type:
                tool = RouterBitTool(
                    id=guid,
                    name=fusion_tool.get("description", f"Fusion Tool {idx}"),
                    vendor=fusion_tool.get("vendor", "Unknown"),
                    source="fusion360",
                    diameter_mm=diameter,
                    flute_count=flute_count,
                    flute_length_mm=flute_length,
                    overall_length_mm=overall_length,
                )
            elif "drill" in tool_type:
                tool = DrillBitTool(
                    id=guid,
                    name=fusion_tool.get("description", f"Fusion Drill {idx}"),
                    vendor=fusion_tool.get("vendor", "Unknown"),
                    source="fusion360",
                    diameter_mm=diameter,
                    point_angle_deg=geometry.get("SIG", 118.0),
                    flute_count=flute_count,
                )
            else:
                # Default to router bit
                tool = RouterBitTool(
                    id=guid,
                    name=fusion_tool.get("description", f"Fusion Tool {idx}"),
                    source="fusion360",
                    diameter_mm=diameter,
                    flute_count=flute_count,
                )

            # Extract presets
            start_values = fusion_tool.get("start-values", {})
            fusion_presets = start_values.get("presets", [])

            for preset_data in fusion_presets:
                preset = ToolPreset(
                    id=f"{guid}_{preset_data.get('name', 'default')}".replace(" ", "_"),
                    name=preset_data.get("name", "Default"),
                    rpm=preset_data.get("n", 10000),
                    feed_mm_min=preset_data.get("n", 10000) * preset_data.get("f_z", 0.05) * flute_count,
                    f_z_mm_tooth=preset_data.get("f_z"),
                    f_n_mm_rev=preset_data.get("f_n"),
                )
                tool.presets.append(preset)

            tools_out.append(tool.dict())

        except Exception as e:
            errors.append(f"Tool {idx}: {str(e)}")

    return {
        "tools": tools_out,
        "presets": presets_out,
        "imported_count": len(tools_out),
        "errors": errors,
    }
```

---

## 7. Frontend Enhancement: 3D Visualization

### Current State: Working but Basic

**File:** `client/src/components/CamBackplot3D.vue` (240 lines)

The 3D visualization works but lacks:
- Multi-pass Z-layer visualization
- Tool geometry preview
- Collision zone highlighting

### Enhancement Guide

Add to `client/src/components/CamBackplot3D.vue`:

```typescript
// Add these imports
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

// Add collision zone visualization
function addCollisionZones(collisions: CollisionZone[]) {
  const collisionGroup = new THREE.Group()
  collisionGroup.name = 'collisions'

  for (const collision of collisions) {
    // Create sphere at collision point
    const geometry = new THREE.SphereGeometry(2, 16, 16)
    const material = new THREE.MeshBasicMaterial({
      color: collision.severity === 'critical' ? 0xff0000 : 0xffaa00,
      transparent: true,
      opacity: 0.6,
    })
    const sphere = new THREE.Mesh(geometry, material)
    sphere.position.set(collision.x, collision.y, collision.z)

    // Add pulsing animation
    sphere.userData.collision = collision

    collisionGroup.add(sphere)
  }

  scene.add(collisionGroup)
}

// Add tool geometry preview
function addToolPreview(tool: { diameter: number, length: number }, position: THREE.Vector3) {
  const geometry = new THREE.CylinderGeometry(
    tool.diameter / 2,
    tool.diameter / 2,
    tool.length,
    32
  )
  const material = new THREE.MeshPhongMaterial({
    color: 0x888888,
    transparent: true,
    opacity: 0.5,
  })
  const toolMesh = new THREE.Mesh(geometry, material)
  toolMesh.position.copy(position)
  toolMesh.rotation.x = Math.PI / 2  // Point down

  scene.add(toolMesh)
  return toolMesh
}

// Add multi-pass Z visualization
function visualizeZPasses(moves: Move[], passDepth: number) {
  const passes: Map<number, Move[]> = new Map()

  // Group moves by Z level
  for (const move of moves) {
    const zLevel = Math.round(move.z / passDepth) * passDepth
    if (!passes.has(zLevel)) {
      passes.set(zLevel, [])
    }
    passes.get(zLevel)!.push(move)
  }

  // Create colored layer for each pass
  const colors = [0x0066ff, 0x00ff66, 0xff6600, 0xff0066, 0x6600ff]
  let colorIdx = 0

  for (const [zLevel, passMoves] of passes) {
    const points = passMoves.map(m => new THREE.Vector3(m.x, m.y, m.z))
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({
      color: colors[colorIdx % colors.length],
      linewidth: 2,
    })
    const line = new THREE.Line(geometry, material)
    line.userData.zLevel = zLevel
    scene.add(line)
    colorIdx++
  }
}
```

---

## 8. Test Coverage

### Current Test Files

| Test File | Coverage | Status |
|-----------|----------|--------|
| `test_cam_pipeline_preset.py` | Pipeline presets | ✅ |
| `test_cam_rosette_intent.py` | Rosette intent | ✅ |
| `test_cam_sim_metrics.py` | Simulation metrics | ✅ |
| `test_cam_backplot_overlay.py` | Backplot overlay | ✅ |
| `test_feeds_speeds/` | Feeds & speeds | ❌ Missing |
| `test_collision_detection/` | Collision | ❌ Missing |
| `test_tool_importers/` | Tool import | ❌ Missing |

### Required Test Files

Create `services/api/tests/cam_core/test_feeds_speeds.py`:

```python
"""Tests for feeds & speeds calculator."""
import pytest
from app.cam_core.feeds_speeds.calculator import calculate_feed_plan, calculate_rpm
from app.cam_core.feeds_speeds.chipload_db import lookup_chipload, ToolMaterial, WorkMaterial


class TestRpmCalculation:
    def test_rpm_from_surface_speed(self):
        # 300 m/min surface speed, 6mm diameter
        rpm = calculate_rpm(surface_speed_m_min=300.0, diameter_mm=6.0)
        # Expected: (300 * 1000) / (π * 6) ≈ 15915
        assert 15900 <= rpm <= 16000

    def test_rpm_zero_diameter(self):
        rpm = calculate_rpm(surface_speed_m_min=300.0, diameter_mm=0)
        assert rpm == 0

    def test_rpm_small_diameter(self):
        rpm = calculate_rpm(surface_speed_m_min=300.0, diameter_mm=1.0)
        # Small diameter = very high RPM
        assert rpm > 90000


class TestChiploadLookup:
    def test_carbide_hardwood_6mm(self):
        entry = lookup_chipload(
            tool_material=ToolMaterial.CARBIDE,
            work_material=WorkMaterial.HARDWOOD,
            diameter_mm=6.0,
        )
        assert entry is not None
        assert entry.chipload_recommend_mm > 0

    def test_unknown_combination(self):
        entry = lookup_chipload(
            tool_material=ToolMaterial.HSS,
            work_material=WorkMaterial.BRASS,
            diameter_mm=100.0,
        )
        assert entry is None


class TestFeedPlanCalculation:
    def test_roughing_hardwood(self):
        tool = {
            "id": "test_tool",
            "diameter_mm": 6.0,
            "flute_count": 2,
            "tool_material": "carbide",
        }
        result = calculate_feed_plan(
            tool=tool,
            material="hardwood",
            strategy="roughing",
        )

        assert result.rpm > 0
        assert result.feed_xy_mm_min > 0
        assert result.chipload_mm > 0
        assert result.is_valid

    def test_machine_limit_clamping(self):
        tool = {
            "id": "test_tool",
            "diameter_mm": 25.0,  # Large tool
            "flute_count": 4,
            "tool_material": "carbide",
        }
        result = calculate_feed_plan(
            tool=tool,
            material="softwood",
            strategy="roughing",
            machine_max_rpm=10000,
            machine_max_feed_mm_min=2000.0,
        )

        assert result.rpm <= 10000
        assert result.feed_xy_mm_min <= 2000.0
        assert "clamping" in " ".join(result.warnings).lower()
```

---

## 9. Quick Reference: File Locations

### Core CAM Files

| Component | File Path | Lines | Status |
|-----------|-----------|-------|--------|
| **Feeds Calculator** | `services/api/app/cam_core/feeds_speeds/calculator.py` | 20 | ❌ STUB |
| **Chipload DB** | `services/api/app/cam_core/feeds_speeds/chipload_db.py` | - | ❌ Missing |
| **Materials** | `services/api/app/cam_core/feeds_speeds/materials.py` | 25 | ⚠️ Minimal |
| **Tool Models** | `services/api/app/cam_core/tools/models.py` | 90 | ✅ Complete |
| **Tool Registry** | `services/api/app/cam_core/tools/registry.py` | 100 | ✅ Complete |
| **Fusion Importer** | `services/api/app/cam_core/tools/importers/fusion_importer.py` | 6 | ❌ STUB |
| **Safety Validator** | `services/api/app/cam/rosette/cnc/cnc_safety_validator.py` | 150 | ⚠️ Partial |
| **Collision Detector** | `services/api/app/cam/collision_detector.py` | - | ❌ Missing |
| **Job Store** | `services/api/app/services/art_jobs_store.py` | 75 | ⚠️ Needs status |
| **CAM Core Router** | `services/api/app/cam_core/cam_core_router.py` | 8 | ❌ Dormant |

### Frontend CAM Files

| Component | File Path | Lines | Status |
|-----------|-----------|-------|--------|
| **2D Backplot** | `client/src/components/cam/CamBackplotViewer.vue` | 245 | ✅ Production |
| **3D Backplot** | `client/src/components/CamBackplot3D.vue` | 240 | ✅ Working |
| **Pipeline Runner** | `client/src/components/cam/CamPipelineRunner.vue` | - | ✅ Working |
| **CAM Types** | `client/src/types/cam.ts` | 200+ | ✅ Complete |

### Reference Implementations

| Pattern | File Path | Use For |
|---------|-----------|---------|
| **Material Feed Rules** | `services/api/app/cam/rosette/cnc/cnc_materials.py` | Feeds & speeds |
| **JSON Job Store** | `services/api/app/services/art_jobs_store.py` | Job persistence |
| **Tool Models** | `services/api/app/cam_core/tools/models.py` | Tool definitions |
| **Three.js 3D** | `client/src/components/CamBackplot3D.vue` | 3D visualization |

---

## 10. Implementation Checklist

### Phase 1: Critical Path (~25 hours)

- [ ] **Feeds & Speeds Calculator** (8h)
  - [ ] Create `chipload_db.py` with 10+ material/tool combinations
  - [ ] Implement `calculate_feed_plan()` with real calculations
  - [ ] Add RPM and feed rate validation
  - [ ] Create API endpoint in `cam_core_router.py`
  - [ ] Register router in `main.py`

- [ ] **Collision Detection** (6h)
  - [ ] Create `collision_detector.py` module
  - [ ] Implement gouge detection
  - [ ] Implement fixture collision
  - [ ] Implement rapid-into-material check
  - [ ] Integrate with `cnc_safety_validator.py`

- [ ] **Material Database Expansion** (4h)
  - [ ] Add 10+ material profiles
  - [ ] Include machinability ratings
  - [ ] Add thermal properties
  - [ ] Create material lookup API

- [ ] **Job Persistence Enhancement** (4h)
  - [ ] Add status tracking to `CamJob`
  - [ ] Implement checkpoints
  - [ ] Add execution logging
  - [ ] Create job list/filter API

- [ ] **Tests** (3h)
  - [ ] Feeds & speeds tests
  - [ ] Collision detection tests
  - [ ] Job persistence tests

### Phase 2: Enhancement (~15 hours)

- [ ] **Tool Library Importers** (6h)
  - [ ] Fusion 360 JSON parser
  - [ ] Carbide Create parser
  - [ ] Vectric CSV parser

- [ ] **3D Visualization Enhancement** (6h)
  - [ ] Multi-pass Z visualization
  - [ ] Collision zone highlighting
  - [ ] Tool geometry preview

- [ ] **Frontend Polish** (3h)
  - [ ] Job list view
  - [ ] Job detail view
  - [ ] Feed/speed calculator UI

### Phase 3: Polish (~10 hours)

- [ ] Documentation
- [ ] Additional tests
- [ ] Performance optimization
- [ ] Error handling improvements

---

## 11. Summary

**The CAM system is 62% complete. The remaining 38% is infrastructure, not algorithms.**

### What Works
- ✅ Toolpath generation (adaptive, roughing, drilling, v-carve)
- ✅ G-code emission with 5+ post-processors
- ✅ Basic safety validation (envelope, feed limits)
- ✅ 2D/3D visualization
- ✅ Tool model schemas
- ✅ JSON persistence patterns

### What's Missing
- ❌ Feeds & speeds calculator (returns zeros)
- ❌ Collision detection (envelope only)
- ❌ Material database (2 materials)
- ❌ Tool library importers (all stubs)
- ❌ Job status tracking

### Developer Action Items

1. **Start with `chipload_db.py`** - This unlocks the entire feeds & speeds system
2. **Use `cnc_materials.py` as reference** - Pattern already exists in rosette module
3. **Extend `art_jobs_store.py`** - Don't rewrite, just add status fields
4. **Register `cam_core_router.py`** - Router exists but isn't in main.py

**50 focused hours transforms this from working algorithms to a shippable product.**

---

*Document generated as part of luthiers-toolbox system audit.*
*Includes code examples, file paths, and implementation guidance for developers.*
