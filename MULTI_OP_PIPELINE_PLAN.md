# Multi-Operation CAM Pipeline Extension Plan

**Date:** December 12, 2025  
**Status:** 📋 Planning Phase  
**Objective:** Extend `cam_pipeline_router.py` to orchestrate multiple CAM operations (drilling, pocketing, profiling, V-carve) in a single job

---

## 🎯 Executive Summary

**Current State:**
- ✅ Backend routers exist for all operation types (33 routers)
- ✅ Individual operations fully functional
- ⚠️ Pipeline limited to RosetteCam operations only
- ❌ No unified multi-operation sequencing

**Goal:**
Enable users to define jobs like:
```
Job: Guitar Body Cutout
  1. Drill mounting holes (3mm bit)
  2. Adaptive pocket cavity (6mm bit)
  3. Profile cut perimeter (3mm bit)
  → Single G-code file with tool changes
```

**Estimated Effort:** 16-24 hours (3-4 days)

---

## 📊 Current Architecture Analysis

### **Existing Pipeline Flow** (Rosette Only)

```python
# services/api/app/routers/cam_pipeline_router.py (line 23-26)
PipelineOp = Union[RosetteCamPipelineOp]
# Comment: "Later you can add more op types to this union:
#           - AdaptivePocket
#           - ReliefRoughing, etc."
```

**Current 5-Stage Pipeline:**
```
1. dxf_preflight    → Validate DXF geometry
2. adaptive_plan    → Plan pocket offsets
3. adaptive_plan_run → Generate toolpath moves
4. export_post      → Apply post-processor
5. simulate_gcode   → Validate output
```

**Limitation:** Hard-coded to adaptive pocketing only

### **Available Operation Backends**

| Operation | Router | Status | Endpoints |
|-----------|--------|--------|-----------|
| **Adaptive Pocketing** | `adaptive_router.py` | ✅ Production | `/plan`, `/gcode`, `/batch_export` |
| **Drilling** | `cam_drill_router.py` | ✅ Production | `/pattern`, `/export` |
| **Drill Patterns** | `cam_drill_pattern_router.py` | ✅ Production | `/grid`, `/circular`, `/linear` |
| **V-Carve** | `cam_vcarve_router.py` | ✅ Production | `/plan`, `/export` |
| **Relief Routing** | `cam_relief_router.py` | ✅ Production | `/roughing`, `/finishing` |
| **Profile Cutting** | Multiple routers | ⚠️ Scattered | Various endpoints |
| **Fret Slots** | `cam_fret_slots_export_router.py` | ✅ Production | `/export`, `/export_multi` |

**Assessment:** All building blocks exist, just need orchestration layer

---

## 🏗️ Proposed Architecture

### **Phase 1: Operation Type Schema (Week 1)**

**1.1 Create Operation Type Definitions**

**File:** `services/api/app/schemas/cam_pipeline_ops.py` (NEW)

```python
from pydantic import BaseModel, Field
from typing import Literal, Union, List
from enum import Enum

# ============================================================================
# Base Operation Interface
# ============================================================================

class BaseOperationInput(BaseModel):
    """Base class for all CAM operation inputs."""
    operation_type: str
    tool_id: str  # Reference to tool library
    feed_xy: float = Field(..., gt=0, description="Cutting feed rate (mm/min)")
    feed_z: float = Field(..., gt=0, description="Plunge feed rate (mm/min)")
    safe_z: float = Field(5.0, description="Safe retract height (mm)")
    
class BaseOperationResult(BaseModel):
    """Base class for all CAM operation results."""
    operation_type: str
    success: bool
    moves: List[dict]  # Toolpath moves
    stats: dict  # Length, time, volume, etc.
    warnings: List[str] = []
    errors: List[str] = []

# ============================================================================
# Drilling Operations
# ============================================================================

class DrillPoint(BaseModel):
    x: float
    y: float
    z_depth: float  # Absolute depth or relative?

class DrillingInput(BaseOperationInput):
    operation_type: Literal["Drilling"] = "Drilling"
    points: List[DrillPoint]
    peck_depth: float = Field(None, description="Peck drilling depth (mm)")
    dwell_time: float = Field(0.0, description="Dwell at bottom (seconds)")
    retract_mode: Literal["full", "incremental"] = "full"

class DrillingResult(BaseOperationResult):
    operation_type: Literal["Drilling"] = "Drilling"
    hole_count: int
    total_depth: float

# ============================================================================
# Adaptive Pocketing Operations
# ============================================================================

class AdaptivePocketInput(BaseOperationInput):
    operation_type: Literal["AdaptivePocket"] = "AdaptivePocket"
    boundary_loops: List[dict]  # List of point loops (outer + islands)
    stepover: float = Field(0.45, ge=0.1, le=0.8, description="Stepover ratio")
    stepdown: float = Field(1.5, gt=0, description="Depth per pass (mm)")
    margin: float = Field(0.5, ge=0, description="Boundary margin (mm)")
    strategy: Literal["Spiral", "Lanes"] = "Spiral"
    smoothing: float = Field(0.3, description="Arc tolerance (mm)")
    climb: bool = Field(True, description="Climb milling")

class AdaptivePocketResult(BaseOperationResult):
    operation_type: Literal["AdaptivePocket"] = "AdaptivePocket"
    area_cleared: float  # mm²
    volume_removed: float  # mm³
    ring_count: int

# ============================================================================
# Profile Routing Operations
# ============================================================================

class ProfileInput(BaseOperationInput):
    operation_type: Literal["Profile"] = "Profile"
    path_loops: List[dict]  # Paths to follow
    side: Literal["inside", "outside", "on"] = "outside"
    tabs: List[dict] = []  # Tab locations (x, y, width, height)
    lead_in: dict = None  # Lead-in arc/line config
    lead_out: dict = None  # Lead-out arc/line config
    stepdown: float = Field(1.5, gt=0)
    finish_allowance: float = Field(0.0, description="Roughing allowance (mm)")

class ProfileResult(BaseOperationResult):
    operation_type: Literal["Profile"] = "Profile"
    path_length: float  # mm
    tab_count: int

# ============================================================================
# V-Carve Operations
# ============================================================================

class VCarveInput(BaseOperationInput):
    operation_type: Literal["VCarve"] = "VCarve"
    geometry: List[dict]  # Paths to carve
    v_angle: float = Field(90.0, description="V-bit angle (degrees)")
    flat_depth: float = Field(None, description="Max depth (mm)")
    clearance_tool: str = Field(None, description="Clearance tool ID")

class VCarveResult(BaseOperationResult):
    operation_type: Literal["VCarve"] = "VCarve"
    max_depth: float
    carved_length: float

# ============================================================================
# Relief Routing Operations
# ============================================================================

class ReliefInput(BaseOperationInput):
    operation_type: Literal["Relief"] = "Relief"
    z_map: List[List[float]]  # 2D height map
    roughing_passes: int = Field(3, ge=1)
    finishing_pass: bool = Field(True)
    stepdown: float = Field(1.0, gt=0)

class ReliefResult(BaseOperationResult):
    operation_type: Literal["Relief"] = "Relief"
    max_relief_depth: float
    pass_count: int

# ============================================================================
# Pipeline Operation Union
# ============================================================================

PipelineOperationInput = Union[
    DrillingInput,
    AdaptivePocketInput,
    ProfileInput,
    VCarveInput,
    ReliefInput
]

PipelineOperationResult = Union[
    DrillingResult,
    AdaptivePocketResult,
    ProfileResult,
    VCarveResult,
    ReliefResult
]
```

**1.2 Update Pipeline Request/Response Schemas**

**File:** `services/api/app/schemas/cam_pipeline.py` (MODIFY)

```python
from typing import List
from pydantic import BaseModel, Field
from .cam_pipeline_ops import PipelineOperationInput, PipelineOperationResult

class MultiOpPipelineRequest(BaseModel):
    """Request for multi-operation CAM pipeline."""
    operations: List[PipelineOperationInput]
    
    # Global settings
    units: Literal["mm", "inch"] = "mm"
    machine_id: str
    post_id: str
    
    # Tool library
    tools: List[dict] = Field(..., description="Tool definitions")
    
    # Material settings
    material_id: str = Field(None)
    stock_thickness: float = Field(None)
    
    # Export options
    merge_gcode: bool = Field(True, description="Merge into single G-code file")
    include_tool_changes: bool = Field(True)

class MultiOpPipelineResponse(BaseModel):
    """Response from multi-operation CAM pipeline."""
    success: bool
    operations: List[PipelineOperationResult]
    
    # Combined stats
    total_time_s: float
    total_length_mm: float
    tool_changes: int
    
    # G-code output
    gcode: str = Field(None, description="Merged G-code (if merge_gcode=True)")
    gcode_files: List[dict] = Field(None, description="Separate files per operation")
    
    # Warnings/errors
    warnings: List[str] = []
    errors: List[str] = []
```

---

### **Phase 2: Operation Handlers (Week 1-2)**

**2.1 Create Operation Handler Registry**

**File:** `services/api/app/services/cam_operation_handlers.py` (NEW)

```python
from typing import Dict, Callable
from ..schemas.cam_pipeline_ops import (
    PipelineOperationInput,
    PipelineOperationResult,
    DrillingInput, DrillingResult,
    AdaptivePocketInput, AdaptivePocketResult,
    ProfileInput, ProfileResult,
    VCarveInput, VCarveResult,
    ReliefInput, ReliefResult
)
from ..cam.adaptive_core_l2 import plan_adaptive_l2, to_toolpath
from ..cam.feedtime_l3 import jerk_aware_time

# ============================================================================
# Operation Handler Protocol
# ============================================================================

OperationHandler = Callable[[PipelineOperationInput], PipelineOperationResult]

# ============================================================================
# Drilling Handler
# ============================================================================

def handle_drilling(op: DrillingInput) -> DrillingResult:
    """Execute drilling operation."""
    moves = []
    total_depth = 0.0
    
    # For each drill point
    for point in op.points:
        # Rapid to safe Z
        moves.append({"code": "G0", "z": op.safe_z})
        
        # Rapid to XY position
        moves.append({"code": "G0", "x": point.x, "y": point.y})
        
        # Peck drilling if specified
        if op.peck_depth:
            current_z = 0.0
            while current_z > point.z_depth:
                peck_target = max(current_z - op.peck_depth, point.z_depth)
                moves.append({"code": "G1", "z": peck_target, "f": op.feed_z})
                if peck_target > point.z_depth:
                    moves.append({"code": "G0", "z": op.safe_z})  # Retract
                current_z = peck_target
        else:
            # Straight plunge
            moves.append({"code": "G1", "z": point.z_depth, "f": op.feed_z})
        
        # Dwell if specified
        if op.dwell_time > 0:
            moves.append({"code": "G4", "p": op.dwell_time})
        
        # Retract
        moves.append({"code": "G0", "z": op.safe_z})
        
        total_depth += abs(point.z_depth)
    
    # Calculate stats
    from ..cam.feedtime import estimate_time
    time_s = estimate_time(moves, op.feed_xy, op.feed_z, rapid_feed=3000)
    
    return DrillingResult(
        operation_type="Drilling",
        success=True,
        moves=moves,
        stats={
            "time_s": time_s,
            "hole_count": len(op.points),
            "total_depth_mm": total_depth
        },
        hole_count=len(op.points),
        total_depth=total_depth
    )

# ============================================================================
# Adaptive Pocketing Handler
# ============================================================================

def handle_adaptive_pocket(op: AdaptivePocketInput) -> AdaptivePocketResult:
    """Execute adaptive pocketing operation."""
    
    # Call existing adaptive pocketing engine (L.2)
    path_pts = plan_adaptive_l2(
        loops=op.boundary_loops,
        tool_d=0.0,  # Tool diameter from tool library lookup
        stepover=op.stepover,
        stepdown=op.stepdown,
        margin=op.margin,
        strategy=op.strategy,
        smoothing=op.smoothing
    )
    
    # Convert to toolpath moves
    moves = to_toolpath(
        path_pts=path_pts,
        z_rough=0.0,  # From operation context
        safe_z=op.safe_z,
        feed_xy=op.feed_xy,
        feed_z=op.feed_z,
        climb=op.climb
    )
    
    # Calculate stats
    from ..cam.stock_ops import polygon_area
    from ..cam.feedtime_l3 import jerk_aware_time
    
    area = sum(polygon_area(loop['pts']) for loop in op.boundary_loops if 'pts' in loop)
    time_s = jerk_aware_time(moves, machine_profile={})  # Machine from context
    
    return AdaptivePocketResult(
        operation_type="AdaptivePocket",
        success=True,
        moves=moves,
        stats={
            "time_s": time_s,
            "area_mm2": area,
            "volume_mm3": area * op.stepdown,
            "length_mm": sum(m.get('length', 0) for m in moves)
        },
        area_cleared=area,
        volume_removed=area * op.stepdown,
        ring_count=len(path_pts)
    )

# ============================================================================
# Profile Routing Handler
# ============================================================================

def handle_profile(op: ProfileInput) -> ProfileResult:
    """Execute profile routing operation."""
    # TODO: Implement profile routing logic
    # - Offset path by tool radius
    # - Add lead-in/lead-out
    # - Insert tabs
    # - Generate Z passes for stepdown
    
    return ProfileResult(
        operation_type="Profile",
        success=False,
        moves=[],
        stats={},
        path_length=0.0,
        tab_count=len(op.tabs),
        errors=["Profile routing not implemented yet"]
    )

# ============================================================================
# V-Carve Handler
# ============================================================================

def handle_vcarve(op: VCarveInput) -> VCarveResult:
    """Execute V-carve operation."""
    # TODO: Call existing V-carve router logic
    return VCarveResult(
        operation_type="VCarve",
        success=False,
        moves=[],
        stats={},
        max_depth=0.0,
        carved_length=0.0,
        errors=["V-carve not implemented yet"]
    )

# ============================================================================
# Relief Handler
# ============================================================================

def handle_relief(op: ReliefInput) -> ReliefResult:
    """Execute relief routing operation."""
    # TODO: Call existing relief router logic
    return ReliefResult(
        operation_type="Relief",
        success=False,
        moves=[],
        stats={},
        max_relief_depth=0.0,
        pass_count=0,
        errors=["Relief routing not implemented yet"]
    )

# ============================================================================
# Handler Registry
# ============================================================================

OPERATION_HANDLERS: Dict[str, OperationHandler] = {
    "Drilling": handle_drilling,
    "AdaptivePocket": handle_adaptive_pocket,
    "Profile": handle_profile,
    "VCarve": handle_vcarve,
    "Relief": handle_relief
}

def execute_operation(op: PipelineOperationInput) -> PipelineOperationResult:
    """Execute a single CAM operation."""
    handler = OPERATION_HANDLERS.get(op.operation_type)
    if not handler:
        raise ValueError(f"Unknown operation type: {op.operation_type}")
    return handler(op)
```

**2.2 Update Pipeline Router**

**File:** `services/api/app/routers/cam_pipeline_router.py` (MODIFY)

```python
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from ..schemas.cam_pipeline import MultiOpPipelineRequest, MultiOpPipelineResponse
from ..schemas.cam_pipeline_ops import PipelineOperationResult
from ..services.cam_operation_handlers import execute_operation
from ..utils.post_presets import get_post_config

router = APIRouter(prefix="/api/cam/pipeline", tags=["cam_pipeline"])

@router.post("/run_multi", response_model=MultiOpPipelineResponse)
async def run_multi_operation_pipeline(req: MultiOpPipelineRequest):
    """
    Execute multi-operation CAM pipeline.
    
    Example request:
    {
      "operations": [
        {
          "operation_type": "Drilling",
          "tool_id": "drill_3mm",
          "points": [{"x": 10, "y": 10, "z_depth": -5}],
          "feed_xy": 800,
          "feed_z": 400
        },
        {
          "operation_type": "AdaptivePocket",
          "tool_id": "endmill_6mm",
          "boundary_loops": [{"pts": [[0,0], [50,0], [50,30], [0,30]]}],
          "stepover": 0.45,
          "stepdown": 1.5,
          "feed_xy": 1200,
          "feed_z": 600
        }
      ],
      "units": "mm",
      "machine_id": "router_1",
      "post_id": "GRBL"
    }
    """
    
    # Execute each operation
    results: List[PipelineOperationResult] = []
    all_moves = []
    total_time = 0.0
    total_length = 0.0
    current_tool = None
    tool_changes = 0
    
    for idx, op in enumerate(req.operations):
        try:
            # Check for tool change
            if current_tool and op.tool_id != current_tool:
                if req.include_tool_changes:
                    all_moves.append({
                        "code": "M6",
                        "tool": op.tool_id,
                        "comment": f"Tool change to {op.tool_id}"
                    })
                    tool_changes += 1
            current_tool = op.tool_id
            
            # Execute operation
            result = execute_operation(op)
            results.append(result)
            
            # Accumulate moves and stats
            if result.success:
                all_moves.extend(result.moves)
                total_time += result.stats.get('time_s', 0)
                total_length += result.stats.get('length_mm', 0)
            
        except Exception as e:
            results.append(PipelineOperationResult(
                operation_type=op.operation_type,
                success=False,
                moves=[],
                stats={},
                errors=[str(e)]
            ))
    
    # Generate G-code
    gcode = None
    if req.merge_gcode:
        from ..util.exporters import moves_to_gcode
        from ..utils.post_presets import get_post_config
        
        post_config = get_post_config(req.post_id)
        gcode = moves_to_gcode(
            moves=all_moves,
            post_config=post_config,
            units=req.units
        )
    
    return MultiOpPipelineResponse(
        success=all(r.success for r in results),
        operations=results,
        total_time_s=total_time,
        total_length_mm=total_length,
        tool_changes=tool_changes,
        gcode=gcode if req.merge_gcode else None,
        warnings=[],
        errors=[]
    )
```

---

### **Phase 3: G-code Merging & Tool Changes (Week 2)**

**3.1 Tool Change Logic**

**File:** `services/api/app/services/tool_change_manager.py` (NEW)

```python
from typing import List, Dict
from enum import Enum

class ToolChangeStrategy(str, Enum):
    MANUAL = "manual"  # M6 with pause
    AUTOMATIC = "automatic"  # M6 with ATC
    NONE = "none"  # No tool changes (error if multiple tools)

def insert_tool_change(
    moves: List[dict],
    from_tool: str,
    to_tool: str,
    strategy: ToolChangeStrategy,
    safe_z: float = 5.0
) -> List[dict]:
    """Insert tool change moves between operations."""
    
    tool_change_moves = []
    
    # 1. Retract to safe Z
    tool_change_moves.append({
        "code": "G0",
        "z": safe_z,
        "comment": "Retract for tool change"
    })
    
    # 2. Move to tool change position (machine-specific)
    tool_change_moves.append({
        "code": "G53",  # Machine coordinates
        "g0": True,
        "x": 0,
        "y": 0,
        "comment": "Move to tool change position"
    })
    
    # 3. Execute tool change
    if strategy == ToolChangeStrategy.MANUAL:
        tool_change_moves.extend([
            {"code": "M5", "comment": "Spindle off"},
            {"code": "M0", "comment": f"Manual tool change to {to_tool}"},
            {"code": "M6", "t": to_tool},
        ])
    elif strategy == ToolChangeStrategy.AUTOMATIC:
        tool_change_moves.extend([
            {"code": "M6", "t": to_tool, "comment": f"Automatic tool change to {to_tool}"}
        ])
    else:
        raise ValueError(f"Multiple tools required but strategy is {strategy}")
    
    # 4. Spindle restart
    tool_change_moves.append({
        "code": "M3",
        "s": 18000,  # TODO: Get from tool/operation
        "comment": "Spindle on"
    })
    
    # 5. Optional: Re-probe Z (machine-specific)
    # tool_change_moves.append({"code": "G38.2", "z": -10, "f": 100})
    
    return tool_change_moves

def optimize_tool_order(operations: List[dict]) -> List[dict]:
    """
    Reorder operations to minimize tool changes.
    
    Simple greedy algorithm:
    - Group operations by tool
    - Sort by Z depth (deepest first)
    """
    from collections import defaultdict
    
    by_tool = defaultdict(list)
    for op in operations:
        by_tool[op.tool_id].append(op)
    
    # Sort tools by total operation count (most used first)
    sorted_tools = sorted(by_tool.keys(), key=lambda t: len(by_tool[t]), reverse=True)
    
    optimized = []
    for tool in sorted_tools:
        # Sort operations by depth (deepest first for better chip evacuation)
        ops = sorted(by_tool[tool], key=lambda o: getattr(o, 'z_depth', 0))
        optimized.extend(ops)
    
    return optimized
```

**3.2 G-code Merging Utility**

**File:** `services/api/app/util/exporters.py` (MODIFY - add function)

```python
def moves_to_gcode(
    moves: List[dict],
    post_config: dict,
    units: str = "mm"
) -> str:
    """
    Convert moves list to G-code with post-processor headers/footers.
    
    Args:
        moves: List of move dictionaries with 'code', 'x', 'y', 'z', 'f', etc.
        post_config: Post-processor configuration (header, footer, arc_mode, etc.)
        units: 'mm' or 'inch'
    
    Returns:
        Complete G-code program as string
    """
    lines = []
    
    # Header
    if units == "mm":
        lines.append("G21  ; Metric units")
    else:
        lines.append("G20  ; Imperial units")
    
    lines.append("G90  ; Absolute positioning")
    lines.append("G17  ; XY plane")
    
    # Post-processor header
    if 'header' in post_config:
        lines.extend(post_config['header'])
    
    # Convert moves to G-code
    for move in moves:
        line = move.get('code', 'G1')
        
        if 'x' in move:
            line += f" X{move['x']:.4f}"
        if 'y' in move:
            line += f" Y{move['y']:.4f}"
        if 'z' in move:
            line += f" Z{move['z']:.4f}"
        if 'f' in move:
            line += f" F{move['f']:.1f}"
        if 'i' in move:
            line += f" I{move['i']:.4f}"
        if 'j' in move:
            line += f" J{move['j']:.4f}"
        if 's' in move:
            line += f" S{move['s']}"
        if 't' in move:
            line += f" T{move['t']}"
        if 'p' in move:
            line += f" P{move['p']}"
        
        if 'comment' in move:
            line += f"  ; {move['comment']}"
        
        lines.append(line)
    
    # Post-processor footer
    if 'footer' in post_config:
        lines.extend(post_config['footer'])
    
    return '\n'.join(lines)
```

---

### **Phase 4: Frontend Integration (Week 2-3)**

**4.1 Update CamPipelineRunner.vue**

**File:** `packages/client/src/components/cam/CamPipelineRunner.vue` (MODIFY)

Add multi-operation builder UI:

```vue
<template>
  <div class="multi-op-pipeline">
    <!-- Existing DXF upload -->
    <section class="dxf-upload">
      <input type="file" accept=".dxf" @change="handleDxfUpload" />
    </section>
    
    <!-- NEW: Operation Builder -->
    <section class="operation-builder">
      <h3>CAM Operations</h3>
      
      <!-- Operation List -->
      <div v-for="(op, idx) in operations" :key="idx" class="operation-card">
        <div class="op-header">
          <span class="op-number">{{ idx + 1 }}</span>
          <select v-model="op.operation_type" @change="updateOpDefaults(op)">
            <option value="Drilling">Drilling</option>
            <option value="AdaptivePocket">Adaptive Pocket</option>
            <option value="Profile">Profile Routing</option>
            <option value="VCarve">V-Carve</option>
            <option value="Relief">Relief</option>
          </select>
          <button @click="removeOperation(idx)">Remove</button>
          <button @click="moveOperation(idx, -1)" :disabled="idx === 0">↑</button>
          <button @click="moveOperation(idx, 1)" :disabled="idx === operations.length - 1">↓</button>
        </div>
        
        <!-- Operation-Specific Parameters -->
        <div class="op-params">
          <!-- Drilling -->
          <template v-if="op.operation_type === 'Drilling'">
            <label>Tool: <select v-model="op.tool_id" :options="drillTools"></select></label>
            <label>Peck Depth (mm): <input type="number" v-model.number="op.peck_depth" step="0.1"></label>
            <label>Dwell (s): <input type="number" v-model.number="op.dwell_time" step="0.1"></label>
            <div class="drill-points">
              <h4>Drill Points (extracted from DXF circles/points)</h4>
              <ul>
                <li v-for="(pt, i) in op.points" :key="i">
                  X: {{ pt.x.toFixed(2) }}, Y: {{ pt.y.toFixed(2) }}, Depth: {{ pt.z_depth.toFixed(2) }}
                </li>
              </ul>
            </div>
          </template>
          
          <!-- Adaptive Pocket -->
          <template v-if="op.operation_type === 'AdaptivePocket'">
            <label>Tool: <select v-model="op.tool_id" :options="endmillTools"></select></label>
            <label>Stepover (%): <input type="number" v-model.number="op.stepover" min="10" max="80" step="5"></label>
            <label>Stepdown (mm): <input type="number" v-model.number="op.stepdown" step="0.1"></label>
            <label>Margin (mm): <input type="number" v-model.number="op.margin" step="0.1"></label>
            <label>Strategy:
              <select v-model="op.strategy">
                <option value="Spiral">Spiral</option>
                <option value="Lanes">Lanes</option>
              </select>
            </label>
            <label>Climb: <input type="checkbox" v-model="op.climb"></label>
          </template>
          
          <!-- Profile -->
          <template v-if="op.operation_type === 'Profile'">
            <label>Tool: <select v-model="op.tool_id" :options="endmillTools"></select></label>
            <label>Side:
              <select v-model="op.side">
                <option value="inside">Inside</option>
                <option value="outside">Outside</option>
                <option value="on">On Path</option>
              </select>
            </label>
            <label>Stepdown (mm): <input type="number" v-model.number="op.stepdown" step="0.1"></label>
            <label>Tabs: <input type="number" v-model.number="op.tab_count" min="0" max="10"></label>
          </template>
        </div>
        
        <!-- Common Feed/Speed -->
        <div class="feed-speed">
          <label>Feed XY (mm/min): <input type="number" v-model.number="op.feed_xy" step="100"></label>
          <label>Feed Z (mm/min): <input type="number" v-model.number="op.feed_z" step="50"></label>
          <label>Safe Z (mm): <input type="number" v-model.number="op.safe_z" step="0.5"></label>
        </div>
      </div>
      
      <!-- Add Operation Button -->
      <button @click="addOperation" class="add-op-btn">+ Add Operation</button>
    </section>
    
    <!-- Tool Change Settings -->
    <section class="tool-settings">
      <h3>Tool Management</h3>
      <label>Tool Change Strategy:
        <select v-model="toolChangeStrategy">
          <option value="manual">Manual (M0 pause)</option>
          <option value="automatic">Automatic (ATC)</option>
          <option value="none">None (single tool only)</option>
        </select>
      </label>
      <label>Optimize Tool Order: <input type="checkbox" v-model="optimizeToolOrder"></label>
      <label>Merge G-code: <input type="checkbox" v-model="mergeGcode"></label>
    </section>
    
    <!-- Run Pipeline Button -->
    <button @click="runMultiOpPipeline" :disabled="!canRunPipeline" class="run-btn">
      Run Multi-Operation Pipeline
    </button>
    
    <!-- Results Display -->
    <section v-if="pipelineResult" class="results">
      <h3>Pipeline Results</h3>
      
      <!-- Per-Operation Results -->
      <div v-for="(opResult, idx) in pipelineResult.operations" :key="idx" class="op-result">
        <h4>{{ idx + 1 }}. {{ opResult.operation_type }}</h4>
        <div class="status" :class="{ success: opResult.success, error: !opResult.success }">
          {{ opResult.success ? '✓ Success' : '✗ Failed' }}
        </div>
        <div class="op-stats">
          <span>Time: {{ opResult.stats.time_s?.toFixed(1) }}s</span>
          <span>Length: {{ opResult.stats.length_mm?.toFixed(1) }}mm</span>
          <span v-if="opResult.stats.hole_count">Holes: {{ opResult.stats.hole_count }}</span>
          <span v-if="opResult.stats.area_mm2">Area: {{ opResult.stats.area_mm2?.toFixed(0) }}mm²</span>
        </div>
        <div v-if="opResult.warnings.length" class="warnings">
          <strong>Warnings:</strong>
          <ul>
            <li v-for="(w, i) in opResult.warnings" :key="i">{{ w }}</li>
          </ul>
        </div>
        <div v-if="opResult.errors.length" class="errors">
          <strong>Errors:</strong>
          <ul>
            <li v-for="(e, i) in opResult.errors" :key="i">{{ e }}</li>
          </ul>
        </div>
      </div>
      
      <!-- Combined Stats -->
      <div class="combined-stats">
        <h4>Total Stats</h4>
        <p>Total Time: {{ pipelineResult.total_time_s?.toFixed(1) }}s ({{ (pipelineResult.total_time_s / 60).toFixed(1) }}min)</p>
        <p>Total Length: {{ pipelineResult.total_length_mm?.toFixed(1) }}mm</p>
        <p>Tool Changes: {{ pipelineResult.tool_changes }}</p>
      </div>
      
      <!-- G-code Download -->
      <div v-if="pipelineResult.gcode" class="gcode-download">
        <button @click="downloadGcode">Download G-code</button>
        <pre class="gcode-preview">{{ pipelineResult.gcode.slice(0, 500) }}...</pre>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// ============================================================================
// State
// ============================================================================

interface Operation {
  operation_type: 'Drilling' | 'AdaptivePocket' | 'Profile' | 'VCarve' | 'Relief'
  tool_id: string
  feed_xy: number
  feed_z: number
  safe_z: number
  [key: string]: any  // Operation-specific params
}

const operations = ref<Operation[]>([])
const toolChangeStrategy = ref<'manual' | 'automatic' | 'none'>('manual')
const optimizeToolOrder = ref(false)
const mergeGcode = ref(true)
const pipelineResult = ref<any>(null)

const drillTools = ref([
  { value: 'drill_3mm', label: '3mm Drill' },
  { value: 'drill_6mm', label: '6mm Drill' }
])

const endmillTools = ref([
  { value: 'endmill_3mm', label: '3mm End Mill' },
  { value: 'endmill_6mm', label: '6mm End Mill' },
  { value: 'endmill_12mm', label: '12mm End Mill' }
])

const canRunPipeline = computed(() => operations.value.length > 0)

// ============================================================================
// Operation Management
// ============================================================================

function addOperation() {
  operations.value.push({
    operation_type: 'Drilling',
    tool_id: 'drill_3mm',
    feed_xy: 800,
    feed_z: 400,
    safe_z: 5.0,
    points: []  // Will be populated from DXF
  })
}

function removeOperation(idx: number) {
  operations.value.splice(idx, 1)
}

function moveOperation(idx: number, direction: number) {
  const newIdx = idx + direction
  if (newIdx >= 0 && newIdx < operations.value.length) {
    const temp = operations.value[idx]
    operations.value[idx] = operations.value[newIdx]
    operations.value[newIdx] = temp
  }
}

function updateOpDefaults(op: Operation) {
  // Set operation-specific defaults when type changes
  if (op.operation_type === 'Drilling') {
    op.peck_depth = 2.0
    op.dwell_time = 0.5
    op.points = []  // Extract from DXF
  } else if (op.operation_type === 'AdaptivePocket') {
    op.stepover = 0.45
    op.stepdown = 1.5
    op.margin = 0.5
    op.strategy = 'Spiral'
    op.climb = true
    op.boundary_loops = []  // Extract from DXF
  } else if (op.operation_type === 'Profile') {
    op.side = 'outside'
    op.stepdown = 1.5
    op.tab_count = 3
    op.path_loops = []  // Extract from DXF
  }
}

// ============================================================================
// Pipeline Execution
// ============================================================================

async function runMultiOpPipeline() {
  const body = {
    operations: operations.value,
    units: 'mm',
    machine_id: 'router_1',  // From global settings
    post_id: 'GRBL',  // From global settings
    tools: [
      { id: 'drill_3mm', diameter: 3.0, type: 'drill' },
      { id: 'endmill_6mm', diameter: 6.0, type: 'endmill' }
    ],
    merge_gcode: mergeGcode.value,
    include_tool_changes: toolChangeStrategy.value !== 'none'
  }
  
  const response = await fetch('/api/cam/pipeline/run_multi', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  
  pipelineResult.value = await response.json()
}

function downloadGcode() {
  const blob = new Blob([pipelineResult.value.gcode], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'multi_op_job.nc'
  a.click()
  URL.revokeObjectURL(url)
}

// ============================================================================
// DXF Parsing (extract geometry for operations)
// ============================================================================

async function handleDxfUpload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  
  // Parse DXF and extract:
  // - Circles → drilling points
  // - Closed polylines → pocket boundaries
  // - Open polylines → profile paths
  
  // TODO: Implement DXF parsing
  console.log('DXF uploaded:', file.name)
}
</script>

<style scoped>
.operation-card {
  border: 1px solid #ccc;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}

.op-header {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.op-number {
  font-weight: bold;
  font-size: 1.2rem;
}

.status.success {
  color: green;
}

.status.error {
  color: red;
}

.gcode-preview {
  background: #f5f5f5;
  padding: 1rem;
  overflow-x: auto;
  max-height: 200px;
}
</style>
```

---

### **Phase 5: Testing & Validation (Week 3)**

**5.1 Create Test Script**

**File:** `test_multi_op_pipeline.ps1` (NEW)

```powershell
# Multi-Operation CAM Pipeline Test Suite

Write-Host "=== Multi-Operation CAM Pipeline Tests ===" -ForegroundColor Cyan

# Ensure server is running
$serverRunning = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 2
    $serverRunning = $true
} catch {
    Write-Host "✗ Server not running on localhost:8000" -ForegroundColor Red
    Write-Host "  Start server: cd services/api; python -m uvicorn app.main:app --reload" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Server running" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Test 1: Drilling Only
# ============================================================================

Write-Host "Test 1: Drilling Operation" -ForegroundColor Cyan

$body1 = @{
    operations = @(
        @{
            operation_type = "Drilling"
            tool_id = "drill_3mm"
            points = @(
                @{ x = 10.0; y = 10.0; z_depth = -5.0 },
                @{ x = 40.0; y = 10.0; z_depth = -5.0 },
                @{ x = 40.0; y = 40.0; z_depth = -5.0 },
                @{ x = 10.0; y = 40.0; z_depth = -5.0 }
            )
            peck_depth = 2.0
            dwell_time = 0.5
            feed_xy = 800
            feed_z = 400
            safe_z = 5.0
        }
    )
    units = "mm"
    machine_id = "router_1"
    post_id = "GRBL"
    tools = @(
        @{ id = "drill_3mm"; diameter = 3.0; type = "drill" }
    )
    merge_gcode = $true
    include_tool_changes = $false
} | ConvertTo-Json -Depth 10

try {
    $result1 = Invoke-RestMethod -Uri "http://localhost:8000/api/cam/pipeline/run_multi" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $body1
    
    if ($result1.success) {
        Write-Host "  ✓ Drilling pipeline succeeded" -ForegroundColor Green
        Write-Host "    Holes: $($result1.operations[0].hole_count)" -ForegroundColor Gray
        Write-Host "    Time: $($result1.total_time_s.ToString('F1'))s" -ForegroundColor Gray
        Write-Host "    G-code lines: $(($result1.gcode -split "`n").Count)" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Drilling pipeline failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

Write-Host ""

# ============================================================================
# Test 2: Adaptive Pocket Only
# ============================================================================

Write-Host "Test 2: Adaptive Pocket Operation" -ForegroundColor Cyan

$body2 = @{
    operations = @(
        @{
            operation_type = "AdaptivePocket"
            tool_id = "endmill_6mm"
            boundary_loops = @(
                @{ pts = @(@(0,0), @(50,0), @(50,30), @(0,30)) }
            )
            stepover = 0.45
            stepdown = 1.5
            margin = 0.5
            strategy = "Spiral"
            smoothing = 0.3
            climb = $true
            feed_xy = 1200
            feed_z = 600
            safe_z = 5.0
        }
    )
    units = "mm"
    machine_id = "router_1"
    post_id = "GRBL"
    tools = @(
        @{ id = "endmill_6mm"; diameter = 6.0; type = "endmill" }
    )
    merge_gcode = $true
} | ConvertTo-Json -Depth 10

try {
    $result2 = Invoke-RestMethod -Uri "http://localhost:8000/api/cam/pipeline/run_multi" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $body2
    
    if ($result2.success) {
        Write-Host "  ✓ Adaptive pocket pipeline succeeded" -ForegroundColor Green
        Write-Host "    Area: $($result2.operations[0].area_cleared.ToString('F0'))mm²" -ForegroundColor Gray
        Write-Host "    Volume: $($result2.operations[0].volume_removed.ToString('F0'))mm³" -ForegroundColor Gray
        Write-Host "    Time: $($result2.total_time_s.ToString('F1'))s" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Adaptive pocket failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

Write-Host ""

# ============================================================================
# Test 3: Multi-Operation (Drill + Pocket)
# ============================================================================

Write-Host "Test 3: Multi-Operation (Drill + Pocket)" -ForegroundColor Cyan

$body3 = @{
    operations = @(
        @{
            operation_type = "Drilling"
            tool_id = "drill_3mm"
            points = @(
                @{ x = 5.0; y = 5.0; z_depth = -8.0 }
            )
            feed_xy = 800
            feed_z = 400
            safe_z = 5.0
        },
        @{
            operation_type = "AdaptivePocket"
            tool_id = "endmill_6mm"
            boundary_loops = @(
                @{ pts = @(@(10,10), @(60,10), @(60,40), @(10,40)) }
            )
            stepover = 0.45
            stepdown = 1.5
            feed_xy = 1200
            feed_z = 600
            safe_z = 5.0
        }
    )
    units = "mm"
    machine_id = "router_1"
    post_id = "GRBL"
    tools = @(
        @{ id = "drill_3mm"; diameter = 3.0; type = "drill" },
        @{ id = "endmill_6mm"; diameter = 6.0; type = "endmill" }
    )
    merge_gcode = $true
    include_tool_changes = $true
} | ConvertTo-Json -Depth 10

try {
    $result3 = Invoke-RestMethod -Uri "http://localhost:8000/api/cam/pipeline/run_multi" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $body3
    
    if ($result3.success) {
        Write-Host "  ✓ Multi-operation pipeline succeeded" -ForegroundColor Green
        Write-Host "    Operations completed: $($result3.operations.Count)" -ForegroundColor Gray
        Write-Host "    Tool changes: $($result3.tool_changes)" -ForegroundColor Gray
        Write-Host "    Total time: $($result3.total_time_s.ToString('F1'))s" -ForegroundColor Gray
        
        # Check for M6 (tool change) in G-code
        if ($result3.gcode -match "M6") {
            Write-Host "    ✓ Tool change found in G-code" -ForegroundColor Green
        } else {
            Write-Host "    ✗ Tool change NOT found in G-code" -ForegroundColor Red
        }
    } else {
        Write-Host "  ✗ Multi-operation pipeline failed" -ForegroundColor Red
    }
} catch {
    Write-Host "  ✗ Request failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== All Tests Complete ===" -ForegroundColor Cyan
```

**5.2 Integration Test Checklist**

- [ ] Single drilling operation works
- [ ] Single adaptive pocket works
- [ ] Multi-operation drill + pocket works
- [ ] Tool changes inserted correctly (M6)
- [ ] G-code merging produces valid output
- [ ] Post-processor headers/footers applied
- [ ] Stats aggregation correct (time, length, tool changes)
- [ ] Error handling (invalid operation type)
- [ ] Operation ordering preserved
- [ ] Tool optimization reduces changes

---

## 📅 Implementation Timeline

### **Week 1: Backend Foundation**
- **Days 1-2:** Create operation type schemas (`cam_pipeline_ops.py`)
- **Days 3-4:** Implement operation handlers (`cam_operation_handlers.py`)
- **Day 5:** Update pipeline router with `/run_multi` endpoint

### **Week 2: G-code & Tool Management**
- **Days 1-2:** Tool change logic (`tool_change_manager.py`)
- **Day 3:** G-code merging utility (`moves_to_gcode`)
- **Days 4-5:** Test backend with PowerShell scripts

### **Week 3: Frontend & Testing**
- **Days 1-3:** Update `CamPipelineRunner.vue` with multi-op UI
- **Days 4-5:** E2E testing, bug fixes, documentation

### **Week 4: Polish & Deployment** (Optional)
- **Days 1-2:** Profile routing implementation
- **Day 3:** V-carve integration
- **Days 4-5:** User documentation, example jobs

---

## 🎯 Success Criteria

**Must Have (MVP):**
- ✅ Drilling + Adaptive Pocket in single job
- ✅ Tool change support (manual M6)
- ✅ G-code merging with post-processor
- ✅ Per-operation stats + combined stats
- ✅ Error handling and validation

**Should Have (V1):**
- ✅ Profile routing support
- ✅ Tool order optimization
- ✅ Operation reordering UI
- ✅ DXF geometry extraction (circles → drill points, polylines → pockets)

**Nice to Have (V2):**
- V-carve operations
- Relief routing
- CAM strategy recommendations
- Job templates/presets
- Multi-file export (one per operation)

---

## 🚧 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **G-code incompatibility** | High | Extensive post-processor testing across all 6 controllers |
| **Tool change errors** | Medium | Add simulation validation, require manual verification |
| **Operation sequencing bugs** | Medium | Unit tests for each operation handler |
| **DXF parsing complexity** | Low | Start with manual operation definition, add auto-extraction later |
| **Performance (large jobs)** | Low | Add progress updates, async processing if needed |

---

## 📚 Related Documentation

- [CAM Engine Analysis](./CAM_ENGINE_ANALYSIS_COMPLETE.md)
- [Adaptive Pocketing Module L](./ADAPTIVE_POCKETING_MODULE_L.md)
- [Post-Processor System](./HELICAL_POST_PRESETS.md)
- [CamPipelineRunner Component](./packages/client/src/components/cam/CamPipelineRunner.vue)

---

## 🔗 Next Steps

1. **Review Plan:** User approval of architecture and timeline
2. **Kickoff Phase 1:** Create operation schemas
3. **Implement Handlers:** Start with drilling and adaptive pocket
4. **Test Backend:** PowerShell test suite
5. **Frontend Integration:** Update Vue component
6. **E2E Testing:** Full workflow validation
7. **Documentation:** User guide + API reference

---

**Status:** 📋 **READY FOR REVIEW**  
**Estimated Completion:** 3-4 weeks (16-24 hours development time)  
**Dependencies:** Existing CAM routers, post-processor system, Vue component

**Recommendation:** Start with Phase 1 (operation schemas) to validate architecture before full implementation.
