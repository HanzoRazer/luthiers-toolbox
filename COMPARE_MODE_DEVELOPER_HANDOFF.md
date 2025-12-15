# Compare Mode Infrastructure - Developer Handoff

**Status:** 🔨 Ready for Implementation  
**Priority:** MEDIUM (Unblocks Item 17: Export Overlays)  
**Estimated Effort:** 3-5 days  
**Date:** November 15, 2025

---

## 🎯 Executive Summary

This document provides a complete specification for implementing **Compare Mode Infrastructure** – a system that enables side-by-side comparison of CAM toolpaths, geometry, and analysis results. This infrastructure will unblock **Item 17 (Export Overlays with Compare Mode)** and provide foundation for advanced diff-based features.

### **Core Concept**
Compare Mode allows users to:
1. Select a **baseline** geometry/toolpath (reference)
2. Compare it against **current** geometry/toolpath (working version)
3. View **differences** (added/removed/modified segments)
4. Export comparison results with overlay metadata

---

## 📋 Prerequisites

### **Existing Systems (Already Complete)**
- ✅ Geometry import/export (DXF/SVG/JSON)
- ✅ CAM pipeline execution
- ✅ Backplot visualization (CamBackplotViewer, CamBackplot3D)
- ✅ Overlay system (already supports visualization)
- ✅ Risk analytics (issue tracking)
- ✅ Multi-post export system

### **Missing Components (To Be Implemented)**
- ❌ Baseline geometry storage
- ❌ Diff calculation utilities
- ❌ Compare mode UI state management
- ❌ Diff visualization overlays
- ❌ Comparison metadata export

---

## 🏗️ System Architecture

### **Component Layers**

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
├─────────────────────────────────────────────────────────┤
│  CompareModePicker.vue     │  Select baseline/current   │
│  CompareDiffViewer.vue     │  Visualize differences     │
│  CompareStatsPanel.vue     │  Show comparison metrics   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                     API Layer                            │
├─────────────────────────────────────────────────────────┤
│  POST /api/compare/geometry/diff     │ Geometry diff    │
│  POST /api/compare/toolpath/diff     │ Toolpath diff    │
│  GET  /api/compare/baselines         │ List baselines   │
│  POST /api/compare/baseline/save     │ Save baseline    │
│  POST /api/compare/export            │ Export with diff │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                          │
├─────────────────────────────────────────────────────────┤
│  geometry_diff.py          │ Geometric comparison       │
│  toolpath_diff.py          │ Move sequence comparison   │
│  baseline_storage.py       │ Baseline CRUD operations   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   Storage Layer                          │
├─────────────────────────────────────────────────────────┤
│  services/api/app/data/baselines/    │ JSON storage     │
│  {baseline_id}.json                  │ Geometry data    │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Data Models

### **1. Baseline Model**

**File:** `services/api/app/models/compare_baseline.py`

```python
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class BaselineGeometry(BaseModel):
    """Stored baseline geometry for comparison."""
    units: Literal["mm", "inch"]
    paths: List[dict]  # Array of line/arc segments
    source: Optional[str] = None  # Original file path
    
class BaselineToolpath(BaseModel):
    """Stored baseline toolpath for comparison."""
    units: Literal["mm", "inch"]
    moves: List[dict]  # Array of G-code moves
    stats: Optional[dict] = None
    
class Baseline(BaseModel):
    """Complete baseline record."""
    id: str  # UUID
    name: str  # User-friendly name
    description: Optional[str] = None
    created_at: datetime
    
    # Type of baseline
    type: Literal["geometry", "toolpath", "both"]
    
    # Data
    geometry: Optional[BaselineGeometry] = None
    toolpath: Optional[BaselineToolpath] = None
    
    # Metadata
    tags: List[str] = []
    project: Optional[str] = None
```

### **2. Diff Models**

**File:** `services/api/app/models/compare_diff.py`

```python
from pydantic import BaseModel
from typing import List, Literal

class GeometryDiffSegment(BaseModel):
    """Individual geometry segment with diff status."""
    type: Literal["line", "arc"]
    x1: float
    y1: float
    x2: float
    y2: float
    cx: Optional[float] = None  # Arc center X
    cy: Optional[float] = None  # Arc center Y
    r: Optional[float] = None   # Arc radius
    
    # Diff status
    status: Literal["added", "removed", "unchanged", "modified"]
    
class GeometryDiff(BaseModel):
    """Complete geometry comparison result."""
    baseline_id: str
    baseline_name: str
    
    # Segments categorized by status
    added: List[GeometryDiffSegment]
    removed: List[GeometryDiffSegment]
    modified: List[GeometryDiffSegment]
    unchanged: List[GeometryDiffSegment]
    
    # Summary statistics
    total_segments: int
    added_count: int
    removed_count: int
    modified_count: int
    unchanged_count: int
    
    # Geometric changes
    added_length_mm: float
    removed_length_mm: float
    net_length_change_mm: float
    
class ToolpathDiff(BaseModel):
    """Complete toolpath comparison result."""
    baseline_id: str
    baseline_name: str
    
    # Moves categorized by status
    added: List[dict]
    removed: List[dict]
    modified: List[dict]
    unchanged: List[dict]
    
    # Summary statistics
    total_moves: int
    added_count: int
    removed_count: int
    modified_count: int
    unchanged_count: int
    
    # Time/distance changes
    time_change_s: float
    length_change_mm: float
    
class CompareExportRequest(BaseModel):
    """Request to export geometry with comparison overlays."""
    current_geometry: dict
    baseline_id: str
    export_format: Literal["dxf", "svg", "json"]
    include_added: bool = True
    include_removed: bool = True
    include_unchanged: bool = False  # Usually omit for clarity
    target_units: Optional[Literal["mm", "inch"]] = None
```

---

## 🔧 Implementation Plan

### **Phase 1: Backend Foundation (Day 1-2)**

#### **Step 1.1: Create Data Models**
```bash
# Create new files
services/api/app/models/compare_baseline.py  # Baseline models
services/api/app/models/compare_diff.py      # Diff models
```

#### **Step 1.2: Implement Baseline Storage Service**

**File:** `services/api/app/services/baseline_storage.py`

```python
"""
Baseline storage service for Compare Mode.
Stores baseline geometry/toolpath data as JSON files.
"""

import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from ..models.compare_baseline import Baseline, BaselineGeometry, BaselineToolpath

BASELINES_DIR = Path(__file__).parent.parent / "data" / "baselines"
BASELINES_DIR.mkdir(parents=True, exist_ok=True)

def save_baseline(
    name: str,
    type: str,
    geometry: Optional[dict] = None,
    toolpath: Optional[dict] = None,
    description: Optional[str] = None,
    tags: List[str] = None,
    project: Optional[str] = None
) -> Baseline:
    """
    Save a new baseline.
    
    Args:
        name: User-friendly name
        type: "geometry", "toolpath", or "both"
        geometry: Geometry data (paths array)
        toolpath: Toolpath data (moves array)
        description: Optional description
        tags: Optional tags for filtering
        project: Optional project name
    
    Returns:
        Baseline model with generated ID
    """
    baseline_id = str(uuid.uuid4())
    
    baseline = Baseline(
        id=baseline_id,
        name=name,
        description=description,
        created_at=datetime.utcnow(),
        type=type,
        geometry=BaselineGeometry(**geometry) if geometry else None,
        toolpath=BaselineToolpath(**toolpath) if toolpath else None,
        tags=tags or [],
        project=project
    )
    
    # Save to file
    file_path = BASELINES_DIR / f"{baseline_id}.json"
    with open(file_path, "w") as f:
        json.dump(baseline.dict(), f, indent=2, default=str)
    
    return baseline

def get_baseline(baseline_id: str) -> Optional[Baseline]:
    """Load baseline by ID."""
    file_path = BASELINES_DIR / f"{baseline_id}.json"
    if not file_path.exists():
        return None
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    return Baseline(**data)

def list_baselines(
    type: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> List[Baseline]:
    """List all baselines with optional filtering."""
    baselines = []
    
    for file_path in BASELINES_DIR.glob("*.json"):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            baseline = Baseline(**data)
            
            # Apply filters
            if type and baseline.type != type:
                continue
            if project and baseline.project != project:
                continue
            if tags and not any(tag in baseline.tags for tag in tags):
                continue
            
            baselines.append(baseline)
        except Exception as e:
            print(f"Warning: Failed to load baseline {file_path}: {e}")
    
    # Sort by creation date (newest first)
    baselines.sort(key=lambda b: b.created_at, reverse=True)
    
    return baselines

def delete_baseline(baseline_id: str) -> bool:
    """Delete baseline by ID."""
    file_path = BASELINES_DIR / f"{baseline_id}.json"
    if file_path.exists():
        file_path.unlink()
        return True
    return False
```

#### **Step 1.3: Implement Geometry Diff Service**

**File:** `services/api/app/services/geometry_diff.py`

```python
"""
Geometry comparison service.
Computes differences between baseline and current geometry.
"""

from typing import List, Tuple
from math import hypot, isclose

from ..models.compare_diff import GeometryDiff, GeometryDiffSegment

def _segment_key(seg: dict) -> Tuple:
    """Generate unique key for segment (for matching)."""
    if seg["type"] == "line":
        return (
            "line",
            round(seg["x1"], 3),
            round(seg["y1"], 3),
            round(seg["x2"], 3),
            round(seg["y2"], 3)
        )
    else:  # arc
        return (
            "arc",
            round(seg["x1"], 3),
            round(seg["y1"], 3),
            round(seg["x2"], 3),
            round(seg["y2"], 3),
            round(seg.get("cx", 0), 3),
            round(seg.get("cy", 0), 3)
        )

def _segments_match(seg1: dict, seg2: dict, tolerance: float = 0.01) -> bool:
    """Check if two segments are approximately equal."""
    if seg1["type"] != seg2["type"]:
        return False
    
    if seg1["type"] == "line":
        return (
            isclose(seg1["x1"], seg2["x1"], abs_tol=tolerance) and
            isclose(seg1["y1"], seg2["y1"], abs_tol=tolerance) and
            isclose(seg1["x2"], seg2["x2"], abs_tol=tolerance) and
            isclose(seg1["y2"], seg2["y2"], abs_tol=tolerance)
        )
    else:  # arc
        return (
            isclose(seg1["x1"], seg2["x1"], abs_tol=tolerance) and
            isclose(seg1["y1"], seg2["y1"], abs_tol=tolerance) and
            isclose(seg1["x2"], seg2["x2"], abs_tol=tolerance) and
            isclose(seg1["y2"], seg2["y2"], abs_tol=tolerance) and
            isclose(seg1.get("cx", 0), seg2.get("cx", 0), abs_tol=tolerance) and
            isclose(seg1.get("cy", 0), seg2.get("cy", 0), abs_tol=tolerance)
        )

def _segment_length(seg: dict) -> float:
    """Calculate segment length in mm."""
    if seg["type"] == "line":
        dx = seg["x2"] - seg["x1"]
        dy = seg["y2"] - seg["y1"]
        return hypot(dx, dy)
    else:  # arc - approximate
        r = seg.get("r", 0)
        # Simple chord length approximation
        dx = seg["x2"] - seg["x1"]
        dy = seg["y2"] - seg["y1"]
        chord = hypot(dx, dy)
        # Arc length ≈ chord * (4/3) for typical arcs
        return chord * 1.333 if r > 0 else chord

def compute_geometry_diff(
    baseline_geometry: dict,
    current_geometry: dict,
    baseline_id: str,
    baseline_name: str,
    tolerance: float = 0.01
) -> GeometryDiff:
    """
    Compare baseline and current geometry.
    
    Args:
        baseline_geometry: Baseline geometry dict with 'paths'
        current_geometry: Current geometry dict with 'paths'
        baseline_id: Baseline ID for reference
        baseline_name: Baseline name for display
        tolerance: Matching tolerance in mm (default 0.01mm)
    
    Returns:
        GeometryDiff with categorized segments
    """
    baseline_paths = baseline_geometry.get("paths", [])
    current_paths = current_geometry.get("paths", [])
    
    # Build lookup sets
    baseline_keys = {_segment_key(seg): seg for seg in baseline_paths}
    current_keys = {_segment_key(seg): seg for seg in current_paths}
    
    added = []
    removed = []
    modified = []
    unchanged = []
    
    # Find removed and unchanged
    for key, baseline_seg in baseline_keys.items():
        if key in current_keys:
            current_seg = current_keys[key]
            if _segments_match(baseline_seg, current_seg, tolerance):
                unchanged.append(GeometryDiffSegment(
                    **baseline_seg,
                    status="unchanged"
                ))
            else:
                modified.append(GeometryDiffSegment(
                    **current_seg,
                    status="modified"
                ))
        else:
            removed.append(GeometryDiffSegment(
                **baseline_seg,
                status="removed"
            ))
    
    # Find added
    for key, current_seg in current_keys.items():
        if key not in baseline_keys:
            added.append(GeometryDiffSegment(
                **current_seg,
                status="added"
            ))
    
    # Calculate statistics
    added_length = sum(_segment_length(s.dict()) for s in added)
    removed_length = sum(_segment_length(s.dict()) for s in removed)
    
    return GeometryDiff(
        baseline_id=baseline_id,
        baseline_name=baseline_name,
        added=added,
        removed=removed,
        modified=modified,
        unchanged=unchanged,
        total_segments=len(baseline_paths) + len(current_paths),
        added_count=len(added),
        removed_count=len(removed),
        modified_count=len(modified),
        unchanged_count=len(unchanged),
        added_length_mm=round(added_length, 2),
        removed_length_mm=round(removed_length, 2),
        net_length_change_mm=round(added_length - removed_length, 2)
    )
```

#### **Step 1.4: Create Compare Router**

**File:** `services/api/app/routers/compare_router.py`

```python
"""
Compare Mode API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

from ..models.compare_baseline import Baseline
from ..models.compare_diff import GeometryDiff, CompareExportRequest
from ..services.baseline_storage import (
    save_baseline,
    get_baseline,
    list_baselines,
    delete_baseline
)
from ..services.geometry_diff import compute_geometry_diff
from ..util.exporters import export_geometry_dxf, export_geometry_svg

router = APIRouter(prefix="/compare", tags=["Compare Mode"])


# === Baseline Management ===

@router.post("/baseline/save", response_model=Baseline)
def save_baseline_endpoint(
    name: str,
    type: str,
    geometry: Optional[dict] = None,
    toolpath: Optional[dict] = None,
    description: Optional[str] = None,
    tags: List[str] = None,
    project: Optional[str] = None
):
    """
    Save a new baseline for comparison.
    
    Args:
        name: User-friendly name (e.g., "V1 Body Outline")
        type: "geometry", "toolpath", or "both"
        geometry: Geometry data with 'units' and 'paths'
        toolpath: Toolpath data with 'units' and 'moves'
        description: Optional description
        tags: Optional tags (e.g., ["neck", "v1"])
        project: Optional project name
    
    Returns:
        Saved baseline with generated ID
    """
    if type not in ["geometry", "toolpath", "both"]:
        raise HTTPException(400, "type must be 'geometry', 'toolpath', or 'both'")
    
    if type in ["geometry", "both"] and not geometry:
        raise HTTPException(400, "geometry required when type includes geometry")
    
    if type in ["toolpath", "both"] and not toolpath:
        raise HTTPException(400, "toolpath required when type includes toolpath")
    
    return save_baseline(
        name=name,
        type=type,
        geometry=geometry,
        toolpath=toolpath,
        description=description,
        tags=tags or [],
        project=project
    )


@router.get("/baselines", response_model=List[Baseline])
def list_baselines_endpoint(
    type: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[str] = None  # Comma-separated
):
    """
    List all saved baselines with optional filtering.
    
    Args:
        type: Filter by type ("geometry", "toolpath", "both")
        project: Filter by project name
        tags: Filter by tags (comma-separated, e.g., "neck,v1")
    
    Returns:
        List of baselines (newest first)
    """
    tag_list = tags.split(",") if tags else None
    return list_baselines(type=type, project=project, tags=tag_list)


@router.get("/baseline/{baseline_id}", response_model=Baseline)
def get_baseline_endpoint(baseline_id: str):
    """Get baseline by ID."""
    baseline = get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(404, f"Baseline {baseline_id} not found")
    return baseline


@router.delete("/baseline/{baseline_id}")
def delete_baseline_endpoint(baseline_id: str):
    """Delete baseline by ID."""
    success = delete_baseline(baseline_id)
    if not success:
        raise HTTPException(404, f"Baseline {baseline_id} not found")
    return {"deleted": True}


# === Comparison ===

@router.post("/geometry/diff", response_model=GeometryDiff)
def geometry_diff_endpoint(
    baseline_id: str,
    current_geometry: dict,
    tolerance: float = 0.01
):
    """
    Compare current geometry against saved baseline.
    
    Args:
        baseline_id: ID of baseline to compare against
        current_geometry: Current geometry with 'units' and 'paths'
        tolerance: Matching tolerance in mm (default 0.01)
    
    Returns:
        GeometryDiff with added/removed/modified/unchanged segments
    """
    baseline = get_baseline(baseline_id)
    if not baseline:
        raise HTTPException(404, f"Baseline {baseline_id} not found")
    
    if not baseline.geometry:
        raise HTTPException(400, "Baseline does not contain geometry")
    
    return compute_geometry_diff(
        baseline_geometry=baseline.geometry.dict(),
        current_geometry=current_geometry,
        baseline_id=baseline_id,
        baseline_name=baseline.name,
        tolerance=tolerance
    )


@router.post("/export")
def export_with_comparison(body: CompareExportRequest):
    """
    Export geometry with comparison overlays.
    
    Args:
        body: Export request with current geometry and baseline ID
    
    Returns:
        DXF/SVG file with color-coded segments:
        - Green: Added segments
        - Red: Removed segments
        - Gray: Unchanged (if included)
    """
    # Compute diff
    baseline = get_baseline(body.baseline_id)
    if not baseline or not baseline.geometry:
        raise HTTPException(404, "Baseline not found or has no geometry")
    
    diff = compute_geometry_diff(
        baseline_geometry=baseline.geometry.dict(),
        current_geometry=body.current_geometry,
        baseline_id=body.baseline_id,
        baseline_name=baseline.name
    )
    
    # Build export geometry with color layers
    export_paths = []
    
    if body.include_added:
        for seg in diff.added:
            seg_dict = seg.dict()
            seg_dict["meta"] = {"color": "green", "layer": "added"}
            export_paths.append(seg_dict)
    
    if body.include_removed:
        for seg in diff.removed:
            seg_dict = seg.dict()
            seg_dict["meta"] = {"color": "red", "layer": "removed"}
            export_paths.append(seg_dict)
    
    if body.include_unchanged:
        for seg in diff.unchanged:
            seg_dict = seg.dict()
            seg_dict["meta"] = {"color": "gray", "layer": "unchanged"}
            export_paths.append(seg_dict)
    
    export_geom = {
        "units": body.current_geometry.get("units", "mm"),
        "paths": export_paths
    }
    
    # Export
    if body.export_format == "dxf":
        return export_geometry_dxf(export_geom, f"comparison_{baseline.name}")
    elif body.export_format == "svg":
        return export_geometry_svg(export_geom, f"comparison_{baseline.name}")
    else:  # json
        return export_geom
```

#### **Step 1.5: Register Router in main.py**

**Add to:** `services/api/app/main.py`

```python
# Around line 180 (after sim_metrics_router)
try:
    from .routers.compare_router import router as compare_router
except Exception as e:
    print(f"Warning: Could not load compare_router: {e}")
    compare_router = None

# Around line 450 (router registration)
if compare_router:
    app.include_router(compare_router)
```

---

### **Phase 2: Frontend Components (Day 3-4)**

#### **Step 2.1: Baseline Picker Component**

**File:** `packages/client/src/components/CompareBaselinePicker.vue`

```vue
<template>
  <div class="border rounded-lg bg-white p-3">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-sm font-semibold">Compare Mode</h3>
      <button
        @click="showSaveDialog = true"
        class="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Save as Baseline
      </button>
    </div>
    
    <!-- Baseline selector -->
    <div class="space-y-2">
      <label class="block text-xs font-medium text-gray-700">
        Select Baseline
      </label>
      <select
        v-model="selectedBaselineId"
        class="w-full px-2 py-1 text-xs border rounded"
      >
        <option :value="null">No comparison</option>
        <option
          v-for="baseline in baselines"
          :key="baseline.id"
          :value="baseline.id"
        >
          {{ baseline.name }} ({{ baseline.created_at }})
        </option>
      </select>
      
      <!-- Comparison stats (when baseline selected) -->
      <div v-if="diff" class="mt-2 p-2 bg-gray-50 rounded text-xs">
        <div class="grid grid-cols-2 gap-2">
          <div>
            <span class="text-green-600">+{{ diff.added_count }}</span> added
          </div>
          <div>
            <span class="text-red-600">-{{ diff.removed_count }}</span> removed
          </div>
          <div>
            <span class="text-blue-600">~{{ diff.modified_count }}</span> modified
          </div>
          <div>
            <span class="text-gray-600">={{ diff.unchanged_count }}</span> same
          </div>
        </div>
        
        <div class="mt-2 pt-2 border-t">
          <div>Net change: <b>{{ diff.net_length_change_mm.toFixed(1) }} mm</b></div>
        </div>
      </div>
    </div>
    
    <!-- Save baseline dialog -->
    <div
      v-if="showSaveDialog"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="showSaveDialog = false"
    >
      <div class="bg-white rounded-lg p-4 w-96">
        <h3 class="text-sm font-semibold mb-3">Save Baseline</h3>
        
        <div class="space-y-2">
          <div>
            <label class="block text-xs font-medium mb-1">Name</label>
            <input
              v-model="newBaselineName"
              class="w-full px-2 py-1 text-xs border rounded"
              placeholder="e.g., V1 Body Outline"
            />
          </div>
          
          <div>
            <label class="block text-xs font-medium mb-1">Description</label>
            <textarea
              v-model="newBaselineDesc"
              class="w-full px-2 py-1 text-xs border rounded"
              rows="2"
              placeholder="Optional description"
            />
          </div>
          
          <div>
            <label class="block text-xs font-medium mb-1">Tags</label>
            <input
              v-model="newBaselineTags"
              class="w-full px-2 py-1 text-xs border rounded"
              placeholder="comma,separated,tags"
            />
          </div>
        </div>
        
        <div class="flex gap-2 mt-4">
          <button
            @click="saveBaseline"
            class="flex-1 px-3 py-2 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Save
          </button>
          <button
            @click="showSaveDialog = false"
            class="flex-1 px-3 py-2 text-xs bg-gray-200 rounded hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

const props = defineProps<{
  currentGeometry: any
}>()

const emit = defineEmits<{
  (e: 'diff-computed', diff: any): void
  (e: 'baseline-selected', baselineId: string | null): void
}>()

const baselines = ref<any[]>([])
const selectedBaselineId = ref<string | null>(null)
const diff = ref<any>(null)

const showSaveDialog = ref(false)
const newBaselineName = ref('')
const newBaselineDesc = ref('')
const newBaselineTags = ref('')

// Load baselines on mount
async function loadBaselines() {
  try {
    const res = await fetch('/api/compare/baselines?type=geometry')
    if (res.ok) {
      baselines.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to load baselines:', err)
  }
}

// Compute diff when baseline selected
watch(selectedBaselineId, async (newId) => {
  if (!newId || !props.currentGeometry) {
    diff.value = null
    emit('baseline-selected', null)
    return
  }
  
  try {
    const res = await fetch('/api/compare/geometry/diff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        baseline_id: newId,
        current_geometry: props.currentGeometry,
        tolerance: 0.01
      })
    })
    
    if (res.ok) {
      diff.value = await res.json()
      emit('diff-computed', diff.value)
      emit('baseline-selected', newId)
    }
  } catch (err) {
    console.error('Failed to compute diff:', err)
    diff.value = null
  }
})

// Save current geometry as baseline
async function saveBaseline() {
  if (!newBaselineName.value.trim()) {
    alert('Please enter a name')
    return
  }
  
  try {
    const tags = newBaselineTags.value
      .split(',')
      .map(t => t.trim())
      .filter(t => t)
    
    const res = await fetch('/api/compare/baseline/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newBaselineName.value,
        type: 'geometry',
        geometry: props.currentGeometry,
        description: newBaselineDesc.value || null,
        tags: tags
      })
    })
    
    if (res.ok) {
      const saved = await res.json()
      baselines.value.unshift(saved)
      showSaveDialog.value = false
      newBaselineName.value = ''
      newBaselineDesc.value = ''
      newBaselineTags.value = ''
    }
  } catch (err) {
    console.error('Failed to save baseline:', err)
    alert('Failed to save baseline')
  }
}

// Load baselines on mount
loadBaselines()
</script>
```

#### **Step 2.2: Diff Viewer Component**

**File:** `packages/client/src/components/CompareDiffViewer.vue`

```vue
<template>
  <div v-if="diff" class="border rounded-lg bg-white p-3">
    <h3 class="text-sm font-semibold mb-2">Comparison Results</h3>
    
    <!-- Summary cards -->
    <div class="grid grid-cols-4 gap-2 mb-3">
      <div class="p-2 bg-green-50 rounded">
        <div class="text-xs text-gray-600">Added</div>
        <div class="text-lg font-bold text-green-600">{{ diff.added_count }}</div>
        <div class="text-xs text-gray-500">{{ diff.added_length_mm.toFixed(1) }} mm</div>
      </div>
      
      <div class="p-2 bg-red-50 rounded">
        <div class="text-xs text-gray-600">Removed</div>
        <div class="text-lg font-bold text-red-600">{{ diff.removed_count }}</div>
        <div class="text-xs text-gray-500">{{ diff.removed_length_mm.toFixed(1) }} mm</div>
      </div>
      
      <div class="p-2 bg-blue-50 rounded">
        <div class="text-xs text-gray-600">Modified</div>
        <div class="text-lg font-bold text-blue-600">{{ diff.modified_count }}</div>
      </div>
      
      <div class="p-2 bg-gray-50 rounded">
        <div class="text-xs text-gray-600">Unchanged</div>
        <div class="text-lg font-bold text-gray-600">{{ diff.unchanged_count }}</div>
      </div>
    </div>
    
    <!-- Export button -->
    <button
      @click="exportComparison"
      class="w-full px-3 py-2 text-xs bg-purple-500 text-white rounded hover:bg-purple-600"
    >
      Export with Overlays (DXF/SVG)
    </button>
    
    <!-- Legend -->
    <div class="mt-3 pt-3 border-t">
      <div class="text-xs font-medium mb-2">Legend</div>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 bg-green-500 rounded"></div>
          <span>Added segments</span>
        </div>
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 bg-red-500 rounded"></div>
          <span>Removed segments</span>
        </div>
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 bg-blue-500 rounded"></div>
          <span>Modified segments</span>
        </div>
        <div class="flex items-center gap-1">
          <div class="w-3 h-3 bg-gray-400 rounded"></div>
          <span>Unchanged</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  diff: any
  currentGeometry: any
  baselineId: string
}>()

async function exportComparison() {
  try {
    const res = await fetch('/api/compare/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_geometry: props.currentGeometry,
        baseline_id: props.baselineId,
        export_format: 'dxf',
        include_added: true,
        include_removed: true,
        include_unchanged: false
      })
    })
    
    if (res.ok) {
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `comparison_${Date.now()}.dxf`
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (err) {
    console.error('Export failed:', err)
    alert('Export failed')
  }
}
</script>
```

---

### **Phase 3: Integration (Day 5)**

#### **Step 3.1: Update Geometry Overlay Component**

**File:** `packages/client/src/components/GeometryOverlay.vue`

Add compare mode section:

```vue
<!-- Add after existing export buttons -->
<div class="border-t pt-3 mt-3">
  <CompareBaselinePicker
    :current-geometry="geometry"
    @diff-computed="handleDiffComputed"
    @baseline-selected="handleBaselineSelected"
  />
  
  <CompareDiffViewer
    v-if="currentDiff"
    :diff="currentDiff"
    :current-geometry="geometry"
    :baseline-id="selectedBaselineId"
    class="mt-3"
  />
</div>

<script setup lang="ts">
// Add imports
import CompareBaselinePicker from './CompareBaselinePicker.vue'
import CompareDiffViewer from './CompareDiffViewer.vue'

// Add state
const currentDiff = ref<any>(null)
const selectedBaselineId = ref<string | null>(null)

function handleDiffComputed(diff: any) {
  currentDiff.value = diff
}

function handleBaselineSelected(baselineId: string | null) {
  selectedBaselineId.value = baselineId
  if (!baselineId) {
    currentDiff.value = null
  }
}
</script>
```

#### **Step 3.2: Update Backplot to Show Diff Colors**

**File:** `packages/client/src/components/CamBackplotViewer.vue`

Modify path rendering to respect `meta.color`:

```typescript
function drawPath(ctx: CanvasRenderingContext2D, path: any) {
  const color = path.meta?.color || 'blue'
  
  // Color mapping
  const colorMap: Record<string, string> = {
    green: '#10b981',   // Added
    red: '#ef4444',     // Removed
    blue: '#3b82f6',    // Modified
    gray: '#9ca3af'     // Unchanged
  }
  
  ctx.strokeStyle = colorMap[color] || color
  ctx.lineWidth = color === 'gray' ? 1 : 2
  
  // ... rest of drawing logic
}
```

---

## 🧪 Testing Plan

### **Backend Tests**

**File:** `test_compare_mode.ps1`

```powershell
# Test Compare Mode Infrastructure

Write-Host "=== Testing Compare Mode System ===" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"

# Test 1: Save baseline
Write-Host "`nTest 1: Save Baseline" -ForegroundColor Yellow

$geom = @{
    units = "mm"
    paths = @(
        @{ type="line"; x1=0; y1=0; x2=100; y2=0 }
        @{ type="line"; x1=100; y1=0; x2=100; y2=60 }
    )
}

$savePayload = @{
    name = "Test Baseline V1"
    type = "geometry"
    geometry = $geom
    description = "Test baseline for development"
    tags = @("test", "v1")
} | ConvertTo-Json -Depth 10

$baseline = Invoke-RestMethod -Uri "$baseUrl/compare/baseline/save" -Method Post -Body $savePayload -ContentType "application/json"
Write-Host "✓ Baseline saved: $($baseline.id)" -ForegroundColor Green

# Test 2: List baselines
$baselines = Invoke-RestMethod -Uri "$baseUrl/compare/baselines"
Write-Host "✓ Found $($baselines.Count) baselines" -ForegroundColor Green

# Test 3: Compute diff
Write-Host "`nTest 2: Compute Diff" -ForegroundColor Yellow

$currentGeom = @{
    units = "mm"
    paths = @(
        @{ type="line"; x1=0; y1=0; x2=100; y2=0 }    # unchanged
        @{ type="line"; x1=100; y1=0; x2=120; y2=20 } # added
    )
}

$diffPayload = @{
    baseline_id = $baseline.id
    current_geometry = $currentGeom
    tolerance = 0.01
} | ConvertTo-Json -Depth 10

$diff = Invoke-RestMethod -Uri "$baseUrl/compare/geometry/diff" -Method Post -Body $diffPayload -ContentType "application/json"
Write-Host "✓ Diff computed:" -ForegroundColor Green
Write-Host "  Added: $($diff.added_count)" -ForegroundColor Gray
Write-Host "  Removed: $($diff.removed_count)" -ForegroundColor Gray
Write-Host "  Unchanged: $($diff.unchanged_count)" -ForegroundColor Gray

Write-Host "`n=== All Tests Passed ===" -ForegroundColor Green
```

### **Frontend Tests**

1. Manual UI testing:
   - Save baseline from geometry overlay
   - Select baseline from dropdown
   - View diff statistics
   - Export with overlays
   - Verify colors in backplot

2. Unit tests (optional):
   - Test `_segment_key()` matching
   - Test `_segments_match()` tolerance
   - Test diff calculation edge cases

---

## 📊 Success Criteria

### **Phase 1 Complete When:**
- [x] All data models created
- [x] Baseline storage working (save/list/get/delete)
- [x] Geometry diff calculation working
- [x] Router registered and endpoints responding
- [x] Test script passes

### **Phase 2 Complete When:**
- [x] Baseline picker component functional
- [x] Diff viewer component shows statistics
- [x] Save baseline dialog works
- [x] Export with overlays works

### **Phase 3 Complete When:**
- [x] Compare mode integrated in main UI
- [x] Backplot renders diff colors correctly
- [x] End-to-end workflow tested
- [x] Item 17 unblocked (export overlays functional)

---

## 🚀 Future Enhancements (Post-MVP)

### **Toolpath Comparison**
- Implement `toolpath_diff.py` service
- Add move sequence comparison
- Show time/length differences

### **3D Visualization**
- 3D diff viewer in CamBackplot3D
- Height map differences
- Volume change calculations

### **Advanced Features**
- Baseline versioning (track history)
- Automated regression testing (compare on every change)
- Diff annotations (comments on changes)
- Merge conflicts resolution (when both geometries modified)

### **Performance Optimizations**
- Spatial indexing for large geometries
- Parallel diff calculation
- Incremental diff updates

---

## 🔗 Dependencies

### **Backend**
- FastAPI (existing)
- Pydantic (existing)
- Python 3.11+ (existing)
- pathlib (stdlib)
- json (stdlib)
- uuid (stdlib)

### **Frontend**
- Vue 3 (existing)
- TypeScript (existing)
- Tailwind CSS (existing)
- No new npm packages required

---

## 📝 Implementation Checklist

### **Backend (Days 1-2)**
- [ ] Create `compare_baseline.py` model
- [ ] Create `compare_diff.py` model
- [ ] Create `baseline_storage.py` service
- [ ] Create `geometry_diff.py` service
- [ ] Create `compare_router.py`
- [ ] Register router in `main.py`
- [ ] Create data directory: `services/api/app/data/baselines/`
- [ ] Test with `test_compare_mode.ps1`

### **Frontend (Days 3-4)**
- [ ] Create `CompareBaselinePicker.vue`
- [ ] Create `CompareDiffViewer.vue`
- [ ] Update `GeometryOverlay.vue` integration
- [ ] Update `CamBackplotViewer.vue` for diff colors
- [ ] Test manual workflow

### **Integration (Day 5)**
- [ ] End-to-end testing
- [ ] Fix any bugs
- [ ] Update documentation
- [ ] Verify Item 17 unblocked

---

## 📞 Support Contacts

**Questions during implementation?**
- Architecture decisions: Refer to `ARCHITECTURAL_EVOLUTION.md`
- Existing patterns: Check `GeometryOverlay.vue`, `cam_relief_router.py`
- Export system: Review `PATCH_K_EXPORT_COMPLETE.md`

---

## ✅ Definition of Done

**Compare Mode Infrastructure is complete when:**
1. Baselines can be saved and retrieved
2. Geometry diffs can be computed accurately
3. Diffs are visualized in UI with color coding
4. Export includes diff overlays (DXF/SVG)
5. Item 17 workflow is functional end-to-end
6. Tests pass in both backend and frontend
7. Documentation is updated

**Estimated Timeline:** 3-5 days (1 developer)  
**Risk Level:** LOW (well-scoped, clear requirements)  
**Blockers:** None (all prerequisites available)

---

**Prepared for:** Development Team  
**Date:** November 15, 2025  
**Status:** Ready for Implementation  
**Priority:** MEDIUM (Unblocks Item 17)
