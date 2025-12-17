# Phase 32.0 — AI Design Lane Skeleton

**Status:** Ready for Implementation  
**Date:** December 1, 2025  
**Depends On:** Phase 30.0 (Art Studio Normalization), Phase 31.0 (Rosette Parametrics)

---

## 🎯 Overview

Phase 32.0 adds a new **AI Design Lane** to Art Studio for prompt-based artwork generation. This is a **skeleton implementation** that provides clean extension points for future AI integration without requiring external APIs yet.

### **Key Principles**
- ✅ **Zero Breakage**: Rosette/Relief/Adaptive lanes unchanged
- ✅ **Drop-in Compatible**: Works with Phase 30.0 and 31.0
- ✅ **No External Dependencies**: Stub implementation, safe for dev
- ✅ **Future-Ready**: Clean hooks for DALL·E, vectorization, pattern saving

### **What This Adds**
- New backend namespace: `/api/art/ai`
- New frontend route: `/art/ai`
- In-memory job store (no DB required)
- Structured prompts with constraints (width, height, style, target use)
- Job listing and retrieval endpoints

### **What This Doesn't Do (Yet)**
- ❌ No real AI image generation (stubbed)
- ❌ No vectorization (hook provided)
- ❌ No pattern/inlay saving (to be wired in later phase)

---

## 📦 Architecture

### **Backend Flow**
```
POST /api/art/ai/design
  ↓
AIDesignRequest (prompt, constraints)
  ↓
ai_design_service.create_ai_design_job()
  ↓
AIDesignJob (in-memory, UUID)
  ↓
Response: {job_id, status: "pending", ...}
```

### **Frontend Flow**
```
User enters prompt in /art/ai
  ↓
Submit to /api/art/ai/design
  ↓
Job appears in list
  ↓
(Future: Display image, offer vectorization, save to pattern library)
```

---

## 🔧 Implementation Steps

### **Step 1: Extend Art Models**

**File:** `services/api/app/models/art_models.py`

Add these models at the end of the file (after existing Rosette/Relief/Adaptive models):

```python
# services/api/app/models/art_models.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# ... existing Rosette/Relief/Adaptive models ...


# ---- AI Design Lane (Phase 32.0) ----

class AIDesignRequest(BaseModel):
    """Request to create an AI-generated design."""
    prompt: str = Field(
        ...,
        description="Text prompt describing the desired artwork (e.g. 'botanical inlay, vines, 40mm circle').",
    )
    target_use: str = Field(
        "inlay",
        description="Intended downstream use: 'inlay', 'rosette', or 'relief'.",
    )
    width_mm: float = Field(40.0, description="Target width in millimeters.")
    height_mm: float = Field(40.0, description="Target height in millimeters.")
    style_hint: Optional[str] = Field(
        None,
        description="Optional style hint: 'line-art', 'engraving', 'high-relief', etc.",
    )


class AIDesignJob(BaseModel):
    """AI design job with status and results."""
    job_id: str
    status: str  # "pending", "complete", "failed"
    prompt: str
    target_use: str
    width_mm: float
    height_mm: float
    style_hint: Optional[str] = None
    # For now we just store fake URLs; later you can wire real storage
    image_url: Optional[str] = None
    vector_svg_url: Optional[str] = None
    notes: Optional[str] = None


class AIDesignJobList(BaseModel):
    """List of AI design jobs."""
    jobs: List[AIDesignJob] = Field(default_factory=list)
```

---

### **Step 2: Create AI Design Service**

**File:** `services/api/app/services/ai_design_service.py` (NEW)

This service manages AI design jobs in-memory (no DB required for skeleton).

```python
# services/api/app/services/ai_design_service.py
"""
AI Design Lane service skeleton.

This is intentionally a stub:
- No real DALL·E / external calls yet.
- Jobs are stored in-memory only (per-process).
- Safe to run in dev without credentials.

Later, you can:
- Swap in a persistent store (SQLite, Redis, etc.).
- Wire in external AI image APIs and vectorizers.
"""

from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from app.models.art_models import AIDesignRequest, AIDesignJob, AIDesignJobList

# In-memory job store (per process)
_JOBS: Dict[str, AIDesignJob] = {}


def create_ai_design_job(req: AIDesignRequest) -> AIDesignJob:
    """
    Create a new AI design job from a prompt.
    
    NOTE: This is a stub implementation. No external AI calls are made.
    In a future phase, this function would:
    - Call DALL·E or similar API with req.prompt + constraints
    - Store the generated image URL or blob handle
    - Optionally trigger vectorization pipeline
    """
    job_id = f"ai-{uuid4().hex[:12]}"
    
    job = AIDesignJob(
        job_id=job_id,
        status="pending",
        prompt=req.prompt,
        target_use=req.target_use,
        width_mm=req.width_mm,
        height_mm=req.height_mm,
        style_hint=req.style_hint,
        image_url=None,
        vector_svg_url=None,
        notes="Stubbed AI design job. No external call wired yet.",
    )
    _JOBS[job_id] = job
    return job


def list_ai_design_jobs() -> AIDesignJobList:
    """List all AI design jobs in this process."""
    return AIDesignJobList(jobs=list(_JOBS.values()))


def get_ai_design_job(job_id: str) -> AIDesignJob | None:
    """Get a single AI design job by ID."""
    return _JOBS.get(job_id)


def delete_ai_design_job(job_id: str) -> bool:
    """
    Delete an AI design job.
    
    Returns True if job existed and was deleted, False otherwise.
    """
    if job_id in _JOBS:
        del _JOBS[job_id]
        return True
    return False
```

---

### **Step 3: Create AI Router**

**File:** `services/api/app/routers/art/ai_router.py` (NEW)

This router provides the `/api/art/ai` endpoints.

```python
# services/api/app/routers/art/ai_router.py
"""
AI Design lane router.

This router exposes a basic skeleton:
- POST /api/art/ai/design   → create stubbed AI job
- GET  /api/art/ai/jobs     → list in-memory jobs
- GET  /api/art/ai/jobs/{id} → retrieve job detail
- DELETE /api/art/ai/jobs/{id} → delete job (cleanup)

No real AI calls yet; safe for current design lane.
"""

from fastapi import APIRouter, HTTPException

from app.models.art_models import AIDesignRequest, AIDesignJobList, AIDesignJob
from app.services.ai_design_service import (
    create_ai_design_job,
    list_ai_design_jobs,
    get_ai_design_job,
    delete_ai_design_job,
)

router = APIRouter(tags=["art-ai"])


@router.post("/design", response_model=AIDesignJob)
async def create_design(req: AIDesignRequest) -> AIDesignJob:
    """
    Create a new AI design job from a prompt + constraints.

    NOTE: This is a stub. No external AI calls are made yet.
    
    Example request:
    {
      "prompt": "botanical inlay with vines and leaves, circular",
      "target_use": "inlay",
      "width_mm": 40.0,
      "height_mm": 40.0,
      "style_hint": "line-art"
    }
    """
    return create_ai_design_job(req)


@router.get("/jobs", response_model=AIDesignJobList)
async def list_jobs() -> AIDesignJobList:
    """
    List all AI design jobs in this process.
    
    Returns empty list if no jobs have been created yet.
    """
    return list_ai_design_jobs()


@router.get("/jobs/{job_id}", response_model=AIDesignJob)
async def get_job(job_id: str) -> AIDesignJob:
    """
    Get a single AI design job by ID.
    
    Returns 404 if job does not exist.
    """
    job = get_ai_design_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"AI job {job_id} not found")
    return job


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete an AI design job.
    
    Returns 404 if job does not exist.
    """
    deleted = delete_ai_design_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"AI job {job_id} not found")
    return {"status": "deleted", "job_id": job_id}
```

---

### **Step 4: Wire AI Router into Root Art Router**

**File:** `services/api/app/routers/art/root_art_router.py`

Add the AI router import and include it:

```python
# services/api/app/routers/art/root_art_router.py

from fastapi import APIRouter

from .rosette_router import router as rosette_router
from .relief_router import router as relief_router
from .adaptive_router import router as adaptive_router
from .ai_router import router as ai_router  # NEW

router = APIRouter(
    prefix="/api/art",
    tags=["art-studio"],
    responses={404: {"description": "Art lane not found"}},
)

# Existing lane mounts
router.include_router(rosette_router, prefix="/rosette")
router.include_router(relief_router, prefix="/relief")
router.include_router(adaptive_router, prefix="/adaptive")

# NEW lane: AI Design (Phase 32.0)
router.include_router(ai_router, prefix="/ai")


@router.get("/jobs")
async def list_all_art_jobs():
    """List jobs across all art lanes."""
    return {"message": "Cross-lane job listing not yet implemented"}


@router.get("/jobs/{job_id}")
async def get_art_job(job_id: str):
    """Get job detail from any art lane."""
    return {"message": f"Cross-lane job retrieval for {job_id} not yet implemented"}
```

**No other backend changes required.** The AI router is now accessible at `/api/art/ai`.

---

### **Step 5: Backend Tests**

**File:** `services/api/app/tests/test_art_routes.py`

Append these tests to the existing file:

```python
# services/api/app/tests/test_art_routes.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ... existing tests for rosette/relief/adaptive/patterns ...


class TestAIDesignLane:
    """Tests for Phase 32.0 AI Design Lane."""
    
    def test_create_ai_job(self):
        """Test creating an AI design job with valid prompt."""
        resp = client.post(
            "/api/art/ai/design",
            json={
                "prompt": "botanical inlay, vines, circular rosette",
                "target_use": "inlay",
                "width_mm": 40.0,
                "height_mm": 40.0,
                "style_hint": "line-art",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"].startswith("ai-")
        assert data["status"] == "pending"
        assert data["prompt"] == "botanical inlay, vines, circular rosette"
        assert data["target_use"] == "inlay"
        assert data["width_mm"] == 40.0
        assert data["notes"]  # Should have stub message

    def test_create_ai_job_minimal(self):
        """Test creating AI job with minimal payload."""
        resp = client.post(
            "/api/art/ai/design",
            json={
                "prompt": "simple geometric pattern",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"].startswith("ai-")
        assert data["target_use"] == "inlay"  # default
        assert data["width_mm"] == 40.0  # default
        assert data["height_mm"] == 40.0  # default

    def test_list_ai_jobs(self):
        """Test listing AI design jobs."""
        resp = client.get("/api/art/ai/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)
        # May be empty or contain jobs from previous tests

    def test_get_ai_job(self):
        """Test retrieving a specific AI job."""
        # Create a job first
        create_resp = client.post(
            "/api/art/ai/design",
            json={"prompt": "test pattern for retrieval"},
        )
        job_id = create_resp.json()["job_id"]
        
        # Retrieve it
        resp = client.get(f"/api/art/ai/jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["prompt"] == "test pattern for retrieval"

    def test_get_ai_job_not_found(self):
        """Test retrieving non-existent job returns 404."""
        resp = client.get("/api/art/ai/jobs/does-not-exist")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_delete_ai_job(self):
        """Test deleting an AI design job."""
        # Create a job first
        create_resp = client.post(
            "/api/art/ai/design",
            json={"prompt": "test pattern for deletion"},
        )
        job_id = create_resp.json()["job_id"]
        
        # Delete it
        resp = client.delete(f"/api/art/ai/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"
        
        # Verify it's gone
        get_resp = client.get(f"/api/art/ai/jobs/{job_id}")
        assert get_resp.status_code == 404

    def test_delete_ai_job_not_found(self):
        """Test deleting non-existent job returns 404."""
        resp = client.delete("/api/art/ai/jobs/does-not-exist")
        assert resp.status_code == 404
```

**Run tests:**
```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
pytest app/tests/test_art_routes.py::TestAIDesignLane -v
```

---

### **Step 6: Frontend Route Integration**

**File:** `packages/client/src/router/artRoutes.ts`

Add AI route entry:

```typescript
// packages/client/src/router/artRoutes.ts

import type { RouteRecordRaw } from "vue-router";

export const artRoutes: RouteRecordRaw[] = [
  {
    path: "/art/rosette",
    name: "ArtStudioRosette",
    component: () => import("@/views/art/ArtStudioRosette.vue"),
  },
  {
    path: "/art/relief",
    name: "ArtStudioRelief",
    component: () => import("@/views/art/ArtStudioRelief.vue"),
  },
  {
    path: "/art/adaptive",
    name: "ArtStudioAdaptive",
    component: () => import("@/views/art/ArtStudioAdaptive.vue"),
  },
  {
    path: "/art/ai",
    name: "ArtStudioAI",
    component: () => import("@/views/art/ArtStudioAI.vue"), // NEW (Phase 32.0)
  },
];
```

**No changes to `router/index.ts` required** — it already spreads `artRoutes`.

---

### **Step 7: Update Art Studio Layout Navigation**

**File:** `packages/client/src/views/art/ArtStudioLayout.vue`

Add AI Designer link to navigation:

```vue
<!-- packages/client/src/views/art/ArtStudioLayout.vue -->
<template>
  <div class="p-6 flex flex-col gap-4">
    <header class="flex items-center justify-between flex-wrap gap-3">
      <h1 class="text-2xl font-bold">Art Studio</h1>
      <nav class="flex gap-3 text-sm">
        <RouterLink to="/art/rosette" class="hover:text-sky-500">
          Rosette
        </RouterLink>
        <RouterLink to="/art/relief" class="hover:text-sky-500">
          Relief
        </RouterLink>
        <RouterLink to="/art/adaptive" class="hover:text-sky-500">
          Adaptive
        </RouterLink>
        <RouterLink to="/art/ai" class="hover:text-sky-500">
          AI Designer
        </RouterLink>
      </nav>
    </header>

    <main>
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
// Shared layout for all Art Studio lanes
</script>
```

---

### **Step 8: Create AI Designer View**

**File:** `packages/client/src/views/art/ArtStudioAI.vue` (NEW)

This is the main UI for the AI Design Lane:

```vue
<!-- packages/client/src/views/art/ArtStudioAI.vue -->
<script setup lang="ts">
import { ref, onMounted } from "vue";
import ArtStudioLayout from "./ArtStudioLayout.vue";

interface AIDesignJob {
  job_id: string;
  status: string;
  prompt: string;
  target_use: string;
  width_mm: number;
  height_mm: number;
  style_hint?: string | null;
  image_url?: string | null;
  vector_svg_url?: string | null;
  notes?: string | null;
}

const prompt = ref("");
const targetUse = ref<"inlay" | "rosette" | "relief">("inlay");
const widthMm = ref(40);
const heightMm = ref(40);
const styleHint = ref("");

const submitting = ref(false);
const submitError = ref<string | null>(null);

const jobs = ref<AIDesignJob[]>([]);
const loadingJobs = ref(false);
const jobsError = ref<string | null>(null);

onMounted(() => {
  fetchJobs();
});

async function fetchJobs() {
  loadingJobs.value = true;
  jobsError.value = null;
  try {
    const resp = await fetch("/api/art/ai/jobs");
    if (!resp.ok) throw new Error(`Failed to fetch jobs: ${resp.status}`);
    const data = await resp.json();
    jobs.value = data.jobs ?? [];
  } catch (err: any) {
    console.error(err);
    jobsError.value = err?.message ?? "Failed to load AI jobs.";
  } finally {
    loadingJobs.value = false;
  }
}

async function submitPrompt() {
  if (!prompt.value.trim()) return;
  submitting.value = true;
  submitError.value = null;

  try {
    const resp = await fetch("/api/art/ai/design", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: prompt.value,
        target_use: targetUse.value,
        width_mm: widthMm.value,
        height_mm: heightMm.value,
        style_hint: styleHint.value || null,
      }),
    });
    if (!resp.ok) throw new Error(`Design request failed: ${resp.status}`);
    const job = (await resp.json()) as AIDesignJob;
    jobs.value.unshift(job);
    prompt.value = "";
  } catch (err: any) {
    console.error(err);
    submitError.value = err?.message ?? "Failed to create AI design job.";
  } finally {
    submitting.value = false;
  }
}

async function deleteJob(jobId: string) {
  try {
    const resp = await fetch(`/api/art/ai/jobs/${jobId}`, { method: "DELETE" });
    if (!resp.ok) throw new Error(`Failed to delete job: ${resp.status}`);
    jobs.value = jobs.value.filter((j) => j.job_id !== jobId);
  } catch (err: any) {
    console.error(err);
    alert(`Failed to delete job: ${err.message}`);
  }
}
</script>

<template>
  <ArtStudioLayout>
    <section class="space-y-4">
      <h2 class="text-xl font-semibold">AI Designer (Skeleton)</h2>
      <p class="text-sm opacity-80">
        Use AI-generated artwork as a starting point for inlays, rosettes, and
        reliefs. This lane is currently a stub: no external AI is wired yet,
        but the prompts and jobs are fully structured for future integration.
      </p>

      <!-- Prompt form -->
      <div class="border rounded-xl p-4 space-y-3 bg-white">
        <div>
          <label class="block text-sm font-medium mb-1">Prompt</label>
          <textarea
            v-model="prompt"
            class="w-full px-3 py-2 border rounded min-h-[80px]"
            placeholder="e.g. botanical inlay with vines and leaves, circular, fine line-art"
          />
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="block text-sm font-medium mb-1">Target Use</label>
            <select
              v-model="targetUse"
              class="w-full px-3 py-2 border rounded text-sm"
            >
              <option value="inlay">Inlay</option>
              <option value="rosette">Rosette</option>
              <option value="relief">Relief</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">Width (mm)</label>
            <input
              v-model.number="widthMm"
              type="number"
              class="w-full px-3 py-2 border rounded"
              min="10"
              max="400"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">Height (mm)</label>
            <input
              v-model.number="heightMm"
              type="number"
              class="w-full px-3 py-2 border rounded"
              min="10"
              max="400"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium mb-1">Style Hint (Optional)</label>
          <input
            v-model="styleHint"
            type="text"
            class="w-full px-3 py-2 border rounded"
            placeholder="line-art, engraving, high-relief, stipple, etc."
          />
        </div>

        <button
          @click="submitPrompt"
          :disabled="submitting || !prompt.trim()"
          class="w-full px-4 py-2 bg-sky-500 text-white rounded hover:bg-sky-600 disabled:opacity-50"
        >
          <span v-if="submitting">Submitting...</span>
          <span v-else>Submit AI Design Request</span>
        </button>

        <p v-if="submitError" class="mt-2 text-sm text-red-600">
          {{ submitError }}
        </p>
      </div>

      <!-- Jobs list -->
      <div class="border rounded-xl p-4 bg-gray-50 space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold">AI Jobs</h3>
          <button
            @click="fetchJobs"
            class="text-xs px-3 py-1 border rounded hover:bg-white"
            :disabled="loadingJobs"
          >
            <span v-if="loadingJobs">Refreshing…</span>
            <span v-else>Refresh</span>
          </button>
        </div>

        <p v-if="jobsError" class="text-sm text-red-600">
          {{ jobsError }}
        </p>

        <p v-else-if="!jobs.length" class="text-sm text-gray-500">
          No AI jobs yet. Submit a prompt to create the first job.
        </p>

        <ul v-else class="space-y-2">
          <li
            v-for="job in jobs"
            :key="job.job_id"
            class="p-2 rounded border bg-white text-xs flex flex-col gap-1"
          >
            <div class="flex justify-between items-center">
              <span class="font-mono text-[11px]">
                {{ job.job_id }}
              </span>
              <div class="flex items-center gap-2">
                <span
                  class="px-2 py-0.5 rounded-full text-[11px]"
                  :class="{
                    'bg-yellow-100 text-yellow-800': job.status === 'pending',
                    'bg-green-100 text-green-800': job.status === 'complete',
                    'bg-red-100 text-red-800': job.status === 'failed',
                  }"
                >
                  {{ job.status }}
                </span>
                <button
                  @click="deleteJob(job.job_id)"
                  class="px-2 py-0.5 text-red-600 hover:bg-red-50 rounded text-[11px]"
                  title="Delete job"
                >
                  ✕
                </button>
              </div>
            </div>
            <div class="text-gray-700">
              <strong>Use:</strong> {{ job.target_use }} |
              <strong>Size:</strong> {{ job.width_mm }}×{{ job.height_mm }} mm
            </div>
            <div class="text-gray-600">
              <strong>Prompt:</strong> {{ job.prompt }}
            </div>
            <div v-if="job.style_hint" class="text-gray-500">
              <strong>Style:</strong> {{ job.style_hint }}
            </div>
            <div v-if="job.notes" class="text-gray-400 italic">
              {{ job.notes }}
            </div>
          </li>
        </ul>
      </div>
    </section>
  </ArtStudioLayout>
</template>
```

---

## 🧪 Testing

### **Backend Tests**

```powershell
cd services/api
.\.venv\Scripts\Activate.ps1
pytest app/tests/test_art_routes.py::TestAIDesignLane -v
```

**Expected Output:**
```
test_art_routes.py::TestAIDesignLane::test_create_ai_job PASSED
test_art_routes.py::TestAIDesignLane::test_create_ai_job_minimal PASSED
test_art_routes.py::TestAIDesignLane::test_list_ai_jobs PASSED
test_art_routes.py::TestAIDesignLane::test_get_ai_job PASSED
test_art_routes.py::TestAIDesignLane::test_get_ai_job_not_found PASSED
test_art_routes.py::TestAIDesignLane::test_delete_ai_job PASSED
test_art_routes.py::TestAIDesignLane::test_delete_ai_job_not_found PASSED

================================= 7 passed =================================
```

### **Frontend Manual Test**

```powershell
cd packages/client
npm run dev
```

**Test Steps:**
1. Navigate to `http://localhost:5173/art/ai`
2. Verify AI Designer navigation link appears in Art Studio header
3. Enter prompt: "botanical inlay with vines and leaves, circular"
4. Set constraints: Target Use = Inlay, Width = 40mm, Height = 40mm
5. Add style hint: "line-art"
6. Click "Submit AI Design Request"
7. Verify job appears in jobs list with status "pending"
8. Verify stub message in job notes
9. Click delete button on job
10. Verify job removed from list

### **API Smoke Test**

```powershell
# Start API
cd services/api
uvicorn app.main:app --reload --port 8000

# Test create AI job
curl -X POST http://localhost:8000/api/art/ai/design `
  -H "Content-Type: application/json" `
  -d '{
    "prompt": "geometric pattern for rosette",
    "target_use": "rosette",
    "width_mm": 60.0,
    "height_mm": 60.0,
    "style_hint": "line-art"
  }'

# Expected response:
# {
#   "job_id": "ai-abc123def456",
#   "status": "pending",
#   "prompt": "geometric pattern for rosette",
#   "target_use": "rosette",
#   "width_mm": 60.0,
#   "height_mm": 60.0,
#   "style_hint": "line-art",
#   "image_url": null,
#   "vector_svg_url": null,
#   "notes": "Stubbed AI design job. No external call wired yet."
# }

# Test list jobs
curl http://localhost:8000/api/art/ai/jobs

# Test get specific job
curl http://localhost:8000/api/art/ai/jobs/ai-abc123def456

# Test delete job
curl -X DELETE http://localhost:8000/api/art/ai/jobs/ai-abc123def456
```

---

## 🔌 Integration Points

### **Backward Compatibility**

**Phase 30.0 (Art Studio Normalization):**
- ✅ AI router mounts under existing `/api/art` namespace
- ✅ Uses shared `ArtStudioLayout.vue`
- ✅ Follows same route pattern (`/art/<lane>`)
- ✅ No changes to rosette/relief/adaptive routers

**Phase 31.0 (Rosette Parametrics):**
- ✅ AI lane does not depend on pattern store
- ✅ Pattern store does not depend on AI lane
- ✅ Future integration possible via "Save as pattern" button

### **Future Integration Hooks**

**Phase 33.0 (Potential — AI Image Generation):**
```python
# In ai_design_service.py
async def create_ai_design_job(req: AIDesignRequest) -> AIDesignJob:
    job_id = f"ai-{uuid4().hex[:12]}"
    
    # Call DALL·E or similar API
    image_url = await generate_image_from_prompt(
        prompt=req.prompt,
        size=(req.width_mm, req.height_mm),
        style=req.style_hint
    )
    
    job = AIDesignJob(
        job_id=job_id,
        status="complete",
        prompt=req.prompt,
        image_url=image_url,  # Real URL now
        notes="AI image generated successfully."
    )
    _JOBS[job_id] = job
    return job
```

**Phase 34.0 (Potential — Vectorization):**
```python
# Add /vectorize endpoint to ai_router.py
@router.post("/jobs/{job_id}/vectorize")
async def vectorize_job(job_id: str):
    job = get_ai_design_job(job_id)
    if not job or not job.image_url:
        raise HTTPException(404, "Job not found or no image")
    
    # Call vectorization service
    vector_svg_url = await vectorize_image(job.image_url)
    
    job.vector_svg_url = vector_svg_url
    return job
```

**Phase 35.0 (Potential — Save to Pattern Library):**
```vue
<!-- In ArtStudioAI.vue -->
<button @click="saveAsPattern(job)" v-if="job.vector_svg_url">
  Save as Rosette Pattern
</button>

<script>
async function saveAsPattern(job: AIDesignJob) {
  await fetch("/api/art/rosette/patterns", {
    method: "POST",
    body: JSON.stringify({
      name: `AI Generated: ${job.prompt.substring(0, 30)}`,
      svg_data: job.vector_svg_url,
      source: "ai-generated"
    })
  });
}
</script>
```

---

## 📋 Checklist

### **Backend**
- [ ] Add AI models to `art_models.py`
- [ ] Create `services/ai_design_service.py`
- [ ] Create `routers/art/ai_router.py`
- [ ] Wire AI router into `root_art_router.py`
- [ ] Append AI tests to `tests/test_art_routes.py`
- [ ] Run pytest: `pytest app/tests/test_art_routes.py::TestAIDesignLane -v`

### **Frontend**
- [ ] Add AI route to `router/artRoutes.ts`
- [ ] Add AI nav link to `ArtStudioLayout.vue`
- [ ] Create `views/art/ArtStudioAI.vue`
- [ ] Run dev server: `npm run dev`
- [ ] Test prompt submission at `/art/ai`
- [ ] Test job listing refresh
- [ ] Test job deletion

### **Documentation**
- [ ] Update `DEVELOPER_HANDOFF_N16_COMPLETE.md` (add Phase 32.0 status)
- [ ] Update `AGENTS.md` if AI design patterns emerge
- [ ] Create `AI_DESIGN_QUICKREF.md` once real AI wired

---

## 🚀 Next Steps

### **Immediate (Post-Phase 32.0):**
1. Test all Art Studio lanes still work (rosette, relief, adaptive)
2. Verify Phase 31.0 pattern library unaffected
3. Run full CI suite

### **Phase 33.0 (Future — Real AI Integration):**
- Wire DALL·E API (requires OpenAI key)
- Add image storage (S3 or local filesystem)
- Implement progress tracking (WebSocket or polling)
- Add image preview in frontend
- Cost estimation per prompt

### **Phase 34.0 (Future — Vectorization Pipeline):**
- Add `/vectorize` endpoint
- Integrate potrace or similar library
- SVG optimization and cleanup
- Preview vectorized output

### **Phase 35.0 (Future — Pattern/Inlay Saving):**
- "Save as Rosette Pattern" button
- "Save as Inlay Template" button
- Integration with Phase 31.0 pattern store
- Metadata tagging (ai-generated, prompt, timestamp)

---

## 🐛 Troubleshooting

### **Issue:** AI router not found (404)
**Solution:** 
- Verify `ai_router.py` created in `routers/art/`
- Check `root_art_router.py` has `from .ai_router import router as ai_router`
- Check `router.include_router(ai_router, prefix="/ai")` present
- Restart API server: `uvicorn app.main:app --reload`

### **Issue:** Frontend route not working
**Solution:**
- Check `artRoutes.ts` has AI entry
- Check `ArtStudioAI.vue` created in `views/art/`
- Check router import: `npm run dev` should show no errors
- Navigate directly: `http://localhost:5173/art/ai`

### **Issue:** Jobs disappear after server restart
**Solution:**
- This is expected behavior (in-memory storage)
- For persistence, implement Phase 33.0 with database or file storage
- Temporary workaround: Use localStorage in frontend to cache jobs

### **Issue:** Tests fail with "module not found"
**Solution:**
- Check `services/ai_design_service.py` exists
- Check `routers/art/ai_router.py` exists
- Restart pytest with `-v` flag for detailed errors

---

## 📚 See Also

- [Phase 30.0: Art Studio Normalization](./PHASE_30_COMPLETION_PATCH.md)
- [Phase 31.0: Rosette Parametrics](./PHASE_31_ROSETTE_PARAMETRICS.md)
- [Developer Handoff Document](./docs/DEVELOPER_HANDOFF_N16_COMPLETE.md)
- [AGENTS.md](./AGENTS.md) — AI agent coding rules

---

**Status:** ✅ Phase 32.0 Complete and Ready for Implementation  
**Backward Compatible:** Yes (drop-in addition to Phase 30.0 and 31.0)  
**Next Iteration:** Phase 33.0 (Real AI image generation with DALL·E)  
**Integration Points:** Pattern library (Phase 31.0), Vectorization pipeline (Phase 34.0)
