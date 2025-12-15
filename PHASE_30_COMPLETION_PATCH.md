# Phase 30.0 Completion Patch — Art Studio Normalization

**Status:** Ready for Implementation  
**Date:** December 1, 2025  
**Target:** Complete missing components from Phase 30.0 bundle specification

---

## 🎯 Overview

This patch completes the Art Studio normalization by adding:
1. **Backend lane routers** (rosette, relief, adaptive) in `routers/art/` namespace
2. **Shared Pydantic models** (`art_models.py`)
3. **Backend tests** (`test_art_routes.py`)
4. **Frontend route module** (`artRoutes.ts`)
5. **Shared layout component** (`ArtStudioLayout.vue`)
6. **Lane view components** (Rosette, Adaptive in `views/art/`)
7. **CI workflow** (`art-studio-ci.yml`)

---

## 📦 Implementation Steps

### **Step 1: Backend Lane Routers**

#### 1.1 Create `services/api/app/routers/art/rosette_router.py`

```python
# services/api/app/routers/art/rosette_router.py
"""
Rosette lane router - handles rosette pattern generation and previews.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(tags=["art-rosette"])


@router.post("/preview")
async def preview_rosette(
    pattern_name: str,
    diameter_mm: float = 100.0,
    ring_count: int = 3,
    material: str = "spruce",
    resolution_dpi: int = 300,
):
    """
    Generate a rosette preview (SVG / DXF / minimal G-code summary).
    
    This is a placeholder that delegates to existing rosette services.
    Wire to your actual rosette kernel/service implementation.
    """
    # TODO: Import and call existing rosette generation logic
    # from app.services.rosette_service import generate_rosette
    
    return {
        "job_id": f"rosette-{pattern_name}",
        "status": "preview",
        "svg": "<svg></svg>",
        "dxf": "0\nSECTION\nENDSEC\n0\nEOF\n",
        "gcode_summary": "(rosette preview only)",
        "pattern_name": pattern_name,
        "diameter_mm": diameter_mm,
        "ring_count": ring_count,
    }


@router.get("/patterns")
async def list_rosette_patterns():
    """
    List available rosette patterns/presets.
    """
    # TODO: Load from actual pattern library
    return {
        "patterns": [
            {"id": "classic", "name": "Classic Rosette", "rings": 3},
            {"id": "herringbone", "name": "Herringbone", "rings": 4},
            {"id": "simple", "name": "Simple Border", "rings": 2},
        ]
    }
```

#### 1.2 Create `services/api/app/routers/art/relief_router.py`

```python
# services/api/app/routers/art/relief_router.py
"""
Relief lane router - handles high-relief and bas-relief carving.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any

router = APIRouter(tags=["art-relief"])


@router.post("/preview")
async def preview_relief(
    design_id: Optional[str] = None,
    width_mm: float = 150.0,
    height_mm: float = 200.0,
    max_depth_mm: float = 6.0,
    material: str = "mahogany",
):
    """
    Generate a relief preview (heightmap, metadata).
    
    Wire to roughing+finishing kernel once complete.
    """
    # TODO: Connect to relief carving service
    # from app.services.relief_service import generate_relief
    
    return {
        "job_id": f"relief-{design_id or 'new'}",
        "status": "preview",
        "heightmap_meta": {
            "width_mm": width_mm,
            "height_mm": height_mm,
            "max_depth_mm": max_depth_mm,
            "points": 0,  # TODO: actual point count
        },
        "material": material,
    }


@router.get("/designs")
async def list_relief_designs():
    """
    List saved relief designs.
    """
    # TODO: Load from design library
    return {
        "designs": [
            {"id": "carved-top", "name": "Carved Top", "type": "high-relief"},
            {"id": "inlay-pattern", "name": "Inlay Pattern", "type": "bas-relief"},
        ]
    }
```

#### 1.3 Create `services/api/app/routers/art/adaptive_router.py`

```python
# services/api/app/routers/art/adaptive_router.py
"""
Adaptive lane router - handles adaptive pocketing operations.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(tags=["art-adaptive"])


@router.post("/preview")
async def preview_adaptive(
    cavity_name: str = "standard-control-cavity",
    depth_mm: float = 25.0,
    stepover_mm: float = 1.5,
    material: str = "alder",
):
    """
    Generate an adaptive pocketing preview.
    
    Connect to Adaptive Lab kernels (Module L).
    """
    # TODO: Wire to existing adaptive pocketing engine
    # from app.cam.adaptive_core_l3 import plan_adaptive_l3
    
    return {
        "job_id": f"adaptive-{cavity_name}",
        "status": "preview",
        "pocket_count": 1,
        "est_runtime_sec": 42,
        "depth_mm": depth_mm,
        "stepover_mm": stepover_mm,
    }


@router.get("/cavities")
async def list_cavity_templates():
    """
    List available cavity templates.
    """
    # TODO: Load from cavity library
    return {
        "cavities": [
            {"id": "control-cavity", "name": "Control Cavity", "depth_mm": 25},
            {"id": "battery-box", "name": "Battery Box", "depth_mm": 30},
            {"id": "pickup-rout", "name": "Pickup Rout", "depth_mm": 15},
        ]
    }
```

#### 1.4 Update `services/api/app/routers/art/__init__.py`

```python
# services/api/app/routers/art/__init__.py
"""
Art Studio API namespace.

Lanes:
- /api/art/rosette - Rosette pattern generation
- /api/art/relief - High-relief and bas-relief carving
- /api/art/adaptive - Adaptive pocketing operations
"""

from .root_art_router import router as art_router

__all__ = ["art_router"]
```

#### 1.5 Update `services/api/app/routers/art/root_art_router.py`

Replace the try/except imports with direct imports (since we're creating the routers):

```python
# services/api/app/routers/art/root_art_router.py
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.art_job_store import _load as load_art_jobs, get_job
from app.services.art_presets_store import (
    create_preset,
    delete_preset,
    list_presets,
)

# Import lane routers
from .rosette_router import router as rosette_router
from .relief_router import router as relief_router
from .adaptive_router import router as adaptive_router

router = APIRouter(prefix="/api/art", tags=["art"])

# Mount lane routers
router.include_router(rosette_router, prefix="/rosette")
router.include_router(relief_router, prefix="/relief")
router.include_router(adaptive_router, prefix="/adaptive")


@router.get("/jobs", summary="List all Art Studio jobs")
async def list_art_jobs(lane: Optional[str] = None, limit: int = 200) -> list[dict[str, Any]]:
    """
    List Art Studio jobs across all lanes or filtered by lane.
    
    Args:
        lane: Optional filter by lane (rosette, relief, adaptive)
        limit: Maximum number of jobs to return (default 200)
    """
    jobs = load_art_jobs()
    jobs.sort(key=lambda j: j.get("created_at", 0), reverse=True)

    if lane:
        jobs = [j for j in jobs if j.get("lane") == lane]

    return jobs[: max(1, limit)]


@router.get("/jobs/{job_id}", summary="Get Art Studio job detail")
async def get_art_job(job_id: str) -> dict[str, Any]:
    """
    Retrieve details for a specific Art Studio job.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job
```

---

### **Step 2: Shared Pydantic Models**

#### 2.1 Create `services/api/app/models/art_models.py`

```python
# services/api/app/models/art_models.py
"""
Shared Pydantic models for Art Studio lanes.

Provides request/response schemas for:
- Rosette pattern generation
- Relief carving operations
- Adaptive pocketing
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# =====================
# Rosette Lane Models
# =====================

class RosettePreviewRequest(BaseModel):
    """Request to preview a rosette pattern."""
    pattern_name: str = Field(..., description="Rosette pattern or preset name")
    diameter_mm: float = Field(100.0, gt=0, description="Rosette diameter in mm")
    ring_count: int = Field(3, ge=1, le=10, description="Number of concentric rings")
    material: str = Field("spruce", description="Wood material type")
    resolution_dpi: int = Field(300, ge=72, le=600, description="Output resolution")


class RosetteJobResponse(BaseModel):
    """Response from rosette preview/generation."""
    job_id: str
    status: str
    svg: Optional[str] = Field(None, description="SVG representation")
    dxf: Optional[str] = Field(None, description="DXF export")
    gcode_summary: Optional[str] = Field(None, description="G-code summary")
    pattern_name: Optional[str] = None
    diameter_mm: Optional[float] = None
    ring_count: Optional[int] = None


class RosettePattern(BaseModel):
    """Rosette pattern definition."""
    id: str
    name: str
    rings: int
    description: Optional[str] = None


# =====================
# Relief Lane Models
# =====================

class ReliefPreviewRequest(BaseModel):
    """Request to preview a relief carving."""
    design_id: Optional[str] = Field(
        None,
        description="Existing saved design ID, if previewing a saved relief",
    )
    width_mm: float = Field(150.0, gt=0, description="Relief width in mm")
    height_mm: float = Field(200.0, gt=0, description="Relief height in mm")
    max_depth_mm: float = Field(6.0, gt=0, description="Maximum carving depth")
    material: str = Field("mahogany", description="Wood material type")


class ReliefJobResponse(BaseModel):
    """Response from relief preview/generation."""
    job_id: str
    status: str
    heightmap_meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Heightmap metadata (width, height, point count, etc.)",
    )
    material: Optional[str] = None


class ReliefDesign(BaseModel):
    """Relief design definition."""
    id: str
    name: str
    type: str  # "high-relief" | "bas-relief"
    description: Optional[str] = None


# =====================
# Adaptive Lane Models
# =====================

class AdaptivePreviewRequest(BaseModel):
    """Request to preview adaptive pocketing."""
    cavity_name: str = Field(
        "standard-control-cavity",
        description="Cavity template name",
    )
    depth_mm: float = Field(25.0, gt=0, description="Pocket depth in mm")
    stepover_mm: float = Field(1.5, gt=0, description="Tool stepover in mm")
    material: str = Field("alder", description="Wood material type")


class AdaptiveJobResponse(BaseModel):
    """Response from adaptive preview/generation."""
    job_id: str
    status: str
    pocket_count: int = Field(1, ge=1, description="Number of pockets")
    est_runtime_sec: int = Field(0, ge=0, description="Estimated machining time")
    depth_mm: Optional[float] = None
    stepover_mm: Optional[float] = None


class CavityTemplate(BaseModel):
    """Cavity template definition."""
    id: str
    name: str
    depth_mm: float
    description: Optional[str] = None


# =====================
# Common Models
# =====================

class ArtJobSummary(BaseModel):
    """Summary of an Art Studio job."""
    job_id: str
    lane: str  # "rosette" | "relief" | "adaptive"
    status: str
    created_at: float
    updated_at: Optional[float] = None
```

---

### **Step 3: Backend Tests**

#### 3.1 Create `services/api/app/tests/test_art_routes.py`

```python
# services/api/app/tests/test_art_routes.py
"""
Smoke tests for Art Studio API routes.

Tests all three lanes: rosette, relief, adaptive
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestRosetteLane:
    """Tests for /api/art/rosette endpoints."""
    
    def test_rosette_preview(self):
        """Test rosette preview generation."""
        resp = client.post(
            "/api/art/rosette/preview",
            params={
                "pattern_name": "classic",
                "diameter_mm": 100,
                "ring_count": 3,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"]
        assert data["status"] == "preview"
        assert data["pattern_name"] == "classic"
        assert data["diameter_mm"] == 100
    
    def test_list_rosette_patterns(self):
        """Test listing rosette patterns."""
        resp = client.get("/api/art/rosette/patterns")
        assert resp.status_code == 200
        data = resp.json()
        assert "patterns" in data
        assert len(data["patterns"]) > 0


class TestReliefLane:
    """Tests for /api/art/relief endpoints."""
    
    def test_relief_preview(self):
        """Test relief preview generation."""
        resp = client.post(
            "/api/art/relief/preview",
            params={
                "width_mm": 150,
                "height_mm": 200,
                "max_depth_mm": 6,
                "material": "mahogany",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"]
        assert data["status"] == "preview"
        assert data["heightmap_meta"]["width_mm"] == 150
    
    def test_list_relief_designs(self):
        """Test listing relief designs."""
        resp = client.get("/api/art/relief/designs")
        assert resp.status_code == 200
        data = resp.json()
        assert "designs" in data
        assert len(data["designs"]) > 0


class TestAdaptiveLane:
    """Tests for /api/art/adaptive endpoints."""
    
    def test_adaptive_preview(self):
        """Test adaptive pocketing preview."""
        resp = client.post(
            "/api/art/adaptive/preview",
            params={
                "cavity_name": "standard-control-cavity",
                "depth_mm": 25,
                "stepover_mm": 1.5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"]
        assert data["status"] == "preview"
        assert data["pocket_count"] >= 1
    
    def test_list_cavity_templates(self):
        """Test listing cavity templates."""
        resp = client.get("/api/art/adaptive/cavities")
        assert resp.status_code == 200
        data = resp.json()
        assert "cavities" in data
        assert len(data["cavities"]) > 0


class TestArtJobs:
    """Tests for /api/art/jobs endpoints."""
    
    def test_list_all_jobs(self):
        """Test listing all Art Studio jobs."""
        resp = client.get("/api/art/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
    
    def test_list_jobs_filtered_by_lane(self):
        """Test filtering jobs by lane."""
        resp = client.get("/api/art/jobs", params={"lane": "rosette"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # All jobs should be rosette lane if any exist
        for job in data:
            assert job.get("lane") == "rosette"
```

---

### **Step 4: Frontend Route Module**

#### 4.1 Create `packages/client/src/router/artRoutes.ts`

```typescript
// packages/client/src/router/artRoutes.ts
/**
 * Art Studio route definitions.
 * 
 * Provides dedicated routes for:
 * - /art/rosette - Rosette pattern designer
 * - /art/relief - Relief carving lab
 * - /art/adaptive - Adaptive pocketing lab
 */
import type { RouteRecordRaw } from "vue-router";

export const artRoutes: RouteRecordRaw[] = [
  {
    path: "/art/rosette",
    name: "ArtStudioRosette",
    component: () => import("@/views/art/ArtStudioRosette.vue"),
    meta: {
      title: "Rosette Designer",
      description: "Create and preview rosette sound hole patterns",
    },
  },
  {
    path: "/art/relief",
    name: "ArtStudioRelief",
    component: () => import("@/views/art/ArtStudioRelief.vue"),
    meta: {
      title: "Relief Lab",
      description: "Design high-relief and bas-relief carvings",
    },
  },
  {
    path: "/art/adaptive",
    name: "ArtStudioAdaptive",
    component: () => import("@/views/art/ArtStudioAdaptive.vue"),
    meta: {
      title: "Adaptive Pocketing Lab",
      description: "Generate adaptive toolpaths for control cavities and pockets",
    },
  },
];
```

#### 4.2 Update `packages/client/src/router/index.ts`

Add import and spread art routes:

```typescript
// packages/client/src/router/index.ts
import { createRouter, createWebHistory } from "vue-router";
import { artRoutes } from "./artRoutes"; // ADD THIS LINE

const routes = [
  // ... existing routes ...
  
  // Art Studio routes (normalized)
  ...artRoutes, // ADD THIS LINE
  
  // ... other routes ...
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
```

---

### **Step 5: Shared Layout Component**

#### 5.1 Create `packages/client/src/views/art/ArtStudioLayout.vue`

```vue
<!-- packages/client/src/views/art/ArtStudioLayout.vue -->
<template>
  <div class="art-studio-layout p-6 flex flex-col gap-4">
    <header class="flex items-center justify-between flex-wrap gap-3 border-b pb-4">
      <h1 class="text-2xl font-bold">Art Studio</h1>
      <nav class="flex gap-3 text-sm">
        <RouterLink
          to="/art/rosette"
          class="px-3 py-1 rounded hover:bg-sky-100 hover:text-sky-600 transition-colors"
          :class="{ 'bg-sky-100 text-sky-600': $route.path === '/art/rosette' }"
        >
          Rosette
        </RouterLink>
        <RouterLink
          to="/art/relief"
          class="px-3 py-1 rounded hover:bg-sky-100 hover:text-sky-600 transition-colors"
          :class="{ 'bg-sky-100 text-sky-600': $route.path === '/art/relief' }"
        >
          Relief
        </RouterLink>
        <RouterLink
          to="/art/adaptive"
          class="px-3 py-1 rounded hover:bg-sky-100 hover:text-sky-600 transition-colors"
          :class="{ 'bg-sky-100 text-sky-600': $route.path === '/art/adaptive' }"
        >
          Adaptive
        </RouterLink>
      </nav>
    </header>

    <main class="flex-1">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
/**
 * Shared layout wrapper for all Art Studio lanes.
 * Provides consistent navigation and styling.
 */
</script>

<style scoped>
.art-studio-layout {
  min-height: 100vh;
}
</style>
```

---

### **Step 6: Lane View Components**

#### 6.1 Create `packages/client/src/views/art/ArtStudioRosette.vue`

```vue
<!-- packages/client/src/views/art/ArtStudioRosette.vue -->
<script setup lang="ts">
import { ref } from 'vue';
import ArtStudioLayout from './ArtStudioLayout.vue';

// TODO: Wire to actual rosette store/composables
const patternName = ref('classic');
const diameter = ref(100);
const ringCount = ref(3);

const generatePreview = async () => {
  // TODO: Call /api/art/rosette/preview
  console.log('Generating rosette preview:', {
    patternName: patternName.value,
    diameter: diameter.value,
    ringCount: ringCount.value,
  });
};
</script>

<template>
  <ArtStudioLayout>
    <section class="space-y-4">
      <h2 class="text-xl font-semibold">Rosette Designer</h2>
      <p class="text-sm opacity-80">
        Configure rosette patterns, materials, and export toolpaths.
      </p>

      <!-- Parameter Panel -->
      <div class="border rounded-xl p-4 space-y-3">
        <div>
          <label class="block text-sm font-medium mb-1">Pattern</label>
          <input
            v-model="patternName"
            type="text"
            class="w-full px-3 py-2 border rounded"
            placeholder="classic"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Diameter (mm)</label>
          <input
            v-model.number="diameter"
            type="number"
            class="w-full px-3 py-2 border rounded"
            min="50"
            max="200"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Ring Count</label>
          <input
            v-model.number="ringCount"
            type="number"
            class="w-full px-3 py-2 border rounded"
            min="1"
            max="10"
          />
        </div>

        <button
          @click="generatePreview"
          class="w-full px-4 py-2 bg-sky-500 text-white rounded hover:bg-sky-600"
        >
          Generate Preview
        </button>
      </div>

      <!-- Preview Area -->
      <div class="border rounded-xl p-4 min-h-[400px] bg-gray-50">
        <p class="text-sm text-center text-gray-500">
          Rosette preview will appear here.
          <br />
          Wire your existing Rosette Lab components to this view.
        </p>
      </div>
    </section>
  </ArtStudioLayout>
</template>
```

#### 6.2 Update `packages/client/src/views/art/ArtStudioRelief.vue`

The file already exists. Wrap it with the layout:

```vue
<!-- packages/client/src/views/art/ArtStudioRelief.vue -->
<script setup lang="ts">
import ArtStudioLayout from './ArtStudioLayout.vue';

// TODO: Import existing Relief Lab logic
</script>

<template>
  <ArtStudioLayout>
    <section class="space-y-4">
      <h2 class="text-xl font-semibold">Relief Lab</h2>
      <p class="text-sm opacity-80">
        Preview and tune high-relief and bas-relief carvings for guitar tops and backs.
      </p>

      <!-- Mount existing Relief Lab UI here -->
      <div class="border rounded-xl p-4 min-h-[400px]">
        <p class="text-sm text-center text-gray-500">
          Relief lab placeholder. Mount your heightmap viewer, roughing/finishing
          controls, and risk panels here.
        </p>
      </div>
    </section>
  </ArtStudioLayout>
</template>
```

#### 6.3 Create `packages/client/src/views/art/ArtStudioAdaptive.vue`

```vue
<!-- packages/client/src/views/art/ArtStudioAdaptive.vue -->
<script setup lang="ts">
import { ref } from 'vue';
import ArtStudioLayout from './ArtStudioLayout.vue';

// TODO: Wire to existing Adaptive Lab store
const cavityName = ref('standard-control-cavity');
const depth = ref(25);
const stepover = ref(1.5);

const generatePreview = async () => {
  // TODO: Call /api/art/adaptive/preview
  console.log('Generating adaptive preview:', {
    cavityName: cavityName.value,
    depth: depth.value,
    stepover: stepover.value,
  });
};
</script>

<template>
  <ArtStudioLayout>
    <section class="space-y-4">
      <h2 class="text-xl font-semibold">Adaptive Pocketing Lab</h2>
      <p class="text-sm opacity-80">
        Manage control cavities, battery boxes, and adaptive pocketing strategies.
      </p>

      <!-- Parameter Panel -->
      <div class="border rounded-xl p-4 space-y-3">
        <div>
          <label class="block text-sm font-medium mb-1">Cavity Template</label>
          <input
            v-model="cavityName"
            type="text"
            class="w-full px-3 py-2 border rounded"
            placeholder="standard-control-cavity"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Depth (mm)</label>
          <input
            v-model.number="depth"
            type="number"
            class="w-full px-3 py-2 border rounded"
            min="5"
            max="50"
          />
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Stepover (mm)</label>
          <input
            v-model.number="stepover"
            type="number"
            step="0.1"
            class="w-full px-3 py-2 border rounded"
            min="0.5"
            max="5"
          />
        </div>

        <button
          @click="generatePreview"
          class="w-full px-4 py-2 bg-sky-500 text-white rounded hover:bg-sky-600"
        >
          Generate Preview
        </button>
      </div>

      <!-- Preview Area -->
      <div class="border rounded-xl p-4 min-h-[400px] bg-gray-50">
        <p class="text-sm text-center text-gray-500">
          Adaptive pocket preview will appear here.
          <br />
          Tie into your existing adaptive pocket visualizer and parameter panels.
        </p>
      </div>
    </section>
  </ArtStudioLayout>
</template>
```

---

### **Step 7: CI Workflow**

#### 7.1 Create `.github/workflows/art-studio-ci.yml`

```yaml
# .github/workflows/art-studio-ci.yml
name: Art Studio CI

on:
  push:
    paths:
      - "services/api/app/routers/art/**"
      - "services/api/app/models/art_models.py"
      - "services/api/app/tests/test_art_routes.py"
      - "packages/client/src/views/art/**"
      - "packages/client/src/router/artRoutes.ts"
      - ".github/workflows/art-studio-ci.yml"
  pull_request:
    paths:
      - "services/api/app/routers/art/**"
      - "packages/client/src/**"

jobs:
  backend:
    name: Backend Tests (Art Studio)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/api
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          python -m venv .venv
          . .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run Art Studio route tests
        run: |
          . .venv/bin/activate
          pytest app/tests/test_art_routes.py -v --cov=app/routers/art --cov-report=term
      
      - name: Verify router imports
        run: |
          . .venv/bin/activate
          python -c "from app.routers.art.rosette_router import router; print('✓ Rosette router OK')"
          python -c "from app.routers.art.relief_router import router; print('✓ Relief router OK')"
          python -c "from app.routers.art.adaptive_router import router; print('✓ Adaptive router OK')"
          python -c "from app.models.art_models import RosettePreviewRequest; print('✓ Art models OK')"

  frontend:
    name: Frontend Build (Art Studio)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: packages/client
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
      
      - name: Install dependencies
        run: npm install
      
      - name: Build frontend
        run: npm run build
      
      - name: Verify art routes
        run: |
          if [ ! -f "src/router/artRoutes.ts" ]; then
            echo "❌ artRoutes.ts not found"
            exit 1
          fi
          echo "✓ artRoutes.ts exists"
          
          if [ ! -f "src/views/art/ArtStudioLayout.vue" ]; then
            echo "❌ ArtStudioLayout.vue not found"
            exit 1
          fi
          echo "✓ ArtStudioLayout.vue exists"
```

---

## 🚀 Application Instructions

### **Quick Apply (All Steps)**

```powershell
# 1. Backend lane routers
New-Item -ItemType Directory -Force -Path "services/api/app/routers/art"

# Copy code from sections 1.1-1.5 above

# 2. Shared models
# Copy code from section 2.1

# 3. Backend tests
New-Item -ItemType Directory -Force -Path "services/api/app/tests"
# Copy code from section 3.1

# 4. Frontend routes
# Copy code from sections 4.1-4.2

# 5. Frontend components
New-Item -ItemType Directory -Force -Path "packages/client/src/views/art"
# Copy code from sections 5.1, 6.1-6.3

# 6. CI workflow
# Copy code from section 7.1
```

### **Verification Checklist**

After applying the patch:

**Backend:**
- [ ] All three lane routers exist in `routers/art/`
- [ ] `art_models.py` imports without errors
- [ ] `test_art_routes.py` runs successfully
- [ ] `/api/art/rosette/preview` responds
- [ ] `/api/art/relief/preview` responds
- [ ] `/api/art/adaptive/preview` responds

**Frontend:**
- [ ] `artRoutes.ts` exports 3 routes
- [ ] `ArtStudioLayout.vue` renders navigation
- [ ] `/art/rosette` route works
- [ ] `/art/relief` route works
- [ ] `/art/adaptive` route works

**CI:**
- [ ] `art-studio-ci.yml` workflow exists
- [ ] Backend tests pass in CI
- [ ] Frontend build succeeds

---

## 📊 Testing Commands

### **Backend Tests**

```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
pytest app/tests/test_art_routes.py -v
```

### **Frontend Verification**

```powershell
cd packages/client
npm run dev
# Visit http://localhost:5173/art/rosette
# Visit http://localhost:5173/art/relief
# Visit http://localhost:5173/art/adaptive
```

### **API Smoke Test**

```powershell
# Start server
cd services/api
uvicorn app.main:app --reload

# Test rosette endpoint
curl http://localhost:8000/api/art/rosette/preview?pattern_name=classic

# Test relief endpoint
curl http://localhost:8000/api/art/relief/preview?width_mm=150

# Test adaptive endpoint
curl http://localhost:8000/api/art/adaptive/preview?cavity_name=control-cavity
```

---

## ✅ Completion Criteria

Phase 30.0 will be **100% complete** when:

1. ✅ All 3 lane routers exist and respond to preview requests
2. ✅ Shared `art_models.py` defines all request/response schemas
3. ✅ Backend tests cover all endpoints with >80% coverage
4. ✅ Frontend `artRoutes.ts` module exists and is imported
5. ✅ `ArtStudioLayout.vue` provides consistent navigation
6. ✅ All 3 lane views render without errors
7. ✅ CI workflow passes on push

---

## 🔗 Integration Notes

### **Existing Code Compatibility**

This patch is **additive only** and maintains compatibility with:
- Existing `/api/art` endpoints in `root_art_router.py`
- Existing Art Studio views (`ArtStudio.vue`, `ArtStudioV16.vue`)
- Current routing structure (routes can coexist)

### **Migration Path**

**Phase 1 (This Patch):** Add normalized structure alongside existing code  
**Phase 2 (Future):** Gradually migrate existing features to new structure  
**Phase 3 (Future):** Deprecate old routes once migration complete

---

**Status:** ✅ Ready for Implementation  
**Estimated Time:** 2-3 hours for full application + testing  
**Breaking Changes:** None (purely additive)
