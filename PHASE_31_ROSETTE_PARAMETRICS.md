# Phase 31.0 — Rosette Parametrics + Pattern Library

**Status:** Ready for Implementation  
**Date:** December 1, 2025  
**Depends On:** Phase 30.0 Completion Patch  
**Target:** Transform Rosette from demo stubs to parametric pattern library

---

## 🎯 Overview

Phase 31.0 upgrades the Rosette lane from hardcoded demo patterns to a **parametric pattern library** with:

- **File-based pattern store** (no DB migration required)
- **CRUD API endpoints** for pattern management
- **Frontend pattern selector** with live preview
- **Backward compatible** with Phase 30.0 tests

### **What's New**

1. **Pattern Store** (`rosette_pattern_store.py`) - File-based JSON storage with default seed patterns
2. **Extended Router** (`rosette_router.py`) - Adds GET/POST/DELETE for patterns
3. **Enhanced Tests** (`test_art_routes.py`) - Pattern CRUD test coverage
4. **Parametric UI** (`ArtStudioRosette.vue`) - Pattern selector with live parameters

---

## 📦 Implementation

### **Step 1: Backend Pattern Store**

#### 1.1 Create `services/api/app/services/rosette_pattern_store.py`

```python
# services/api/app/services/rosette_pattern_store.py
"""
File-based store for Rosette patterns.

This is intentionally simple and local so it doesn't require DB migrations.
If you later want to move to SQLite, you can keep the same interface.

Storage location: services/api/app/data/rosette_patterns.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from app.models.art_models import RosettePattern

# Default storage location (adjust if you have a central data folder)
_PATTERNS_PATH = Path(__file__).resolve().parent.parent / "data" / "rosette_patterns.json"


def _ensure_storage_dir() -> None:
    """Ensure the data directory exists."""
    _PATTERNS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_raw() -> list[dict]:
    """
    Load raw pattern data from JSON file.
    
    Returns default seed patterns on first run.
    Returns empty list if file is corrupted.
    """
    _ensure_storage_dir()
    
    if not _PATTERNS_PATH.exists():
        # Seed with default patterns on first run
        defaults = [
            {
                "id": "classic",
                "name": "Classic Rosette",
                "rings": 3,
                "description": "Traditional multi-ring soundhole rosette.",
            },
            {
                "id": "herringbone",
                "name": "Herringbone",
                "rings": 4,
                "description": "Herringbone pattern with accent rings.",
            },
            {
                "id": "simple",
                "name": "Simple Border",
                "rings": 2,
                "description": "Minimal, clean border rosette.",
            },
            {
                "id": "complex",
                "name": "Complex Ornamental",
                "rings": 6,
                "description": "Multi-layered ornamental pattern for premium builds.",
            },
        ]
        _PATTERNS_PATH.write_text(json.dumps(defaults, indent=2), encoding="utf-8")
        return defaults

    try:
        data = json.loads(_PATTERNS_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        # If file is corrupted, return empty list instead of crashing
        return []

    return []


def _save_raw(patterns: list[dict]) -> None:
    """Save pattern data to JSON file."""
    _ensure_storage_dir()
    _PATTERNS_PATH.write_text(json.dumps(patterns, indent=2), encoding="utf-8")


def list_patterns() -> List[RosettePattern]:
    """
    List all available rosette patterns.
    
    Returns:
        List of RosettePattern objects
    """
    return [RosettePattern(**p) for p in _load_raw()]


def get_pattern(pattern_id: str) -> Optional[RosettePattern]:
    """
    Get a single pattern by ID.
    
    Args:
        pattern_id: Unique pattern identifier
        
    Returns:
        RosettePattern if found, None otherwise
    """
    for p in _load_raw():
        if p.get("id") == pattern_id:
            return RosettePattern(**p)
    return None


def upsert_pattern(pattern: RosettePattern) -> RosettePattern:
    """
    Create or update a pattern.
    
    If pattern.id exists, updates the existing pattern.
    If pattern.id is new, adds it to the library.
    
    Args:
        pattern: RosettePattern to save
        
    Returns:
        The saved RosettePattern
    """
    patterns = _load_raw()
    updated = False
    
    for idx, existing in enumerate(patterns):
        if existing.get("id") == pattern.id:
            patterns[idx] = pattern.model_dump()
            updated = True
            break
    
    if not updated:
        patterns.append(pattern.model_dump())
    
    _save_raw(patterns)
    return pattern


def delete_pattern(pattern_id: str) -> bool:
    """
    Delete a pattern from the library.
    
    Args:
        pattern_id: ID of pattern to delete
        
    Returns:
        True if deleted, False if not found
    """
    patterns = _load_raw()
    new_patterns = [p for p in patterns if p.get("id") != pattern_id]
    
    if len(new_patterns) == len(patterns):
        return False
    
    _save_raw(new_patterns)
    return True
```

**Key Features:**
- ✅ Auto-creates `data/` directory if missing
- ✅ Seeds with 4 default patterns on first run
- ✅ Fail-soft on corrupted JSON (returns empty list)
- ✅ Compatible with future SQLite migration (same interface)

---

### **Step 2: Extend Rosette Router**

#### 2.1 Update `services/api/app/routers/art/rosette_router.py`

Replace the entire file with this extended version:

```python
# services/api/app/routers/art/rosette_router.py
"""
Rosette lane router - handles rosette pattern generation and previews.

Phase 31.0: Extended with pattern library CRUD operations.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from app.models.art_models import RosettePattern
from app.services.rosette_pattern_store import (
    list_patterns,
    get_pattern,
    upsert_pattern,
    delete_pattern,
)

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

    NOTE:
    - This endpoint still uses query params for compatibility with Phase 30 tests.
    - In a later phase, you can add a JSON-body variant using RosettePreviewRequest.
    
    Args:
        pattern_name: Pattern ID from pattern library
        diameter_mm: Rosette diameter in millimeters
        ring_count: Number of concentric rings (overrides pattern default)
        material: Wood material type
        resolution_dpi: Output resolution for raster exports
    
    Returns:
        Job response with SVG, DXF, and G-code summary
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


@router.get("/patterns", response_model=List[RosettePattern])
async def list_rosette_patterns():
    """
    List available rosette patterns/presets from the pattern library.
    
    Returns all patterns from the file-based store.
    Includes default seed patterns on first run.
    
    Returns:
        List of RosettePattern objects
    """
    return list_patterns()


@router.get("/patterns/{pattern_id}", response_model=RosettePattern)
async def get_rosette_pattern(pattern_id: str):
    """
    Get a single rosette pattern by ID.
    
    Args:
        pattern_id: Unique pattern identifier (e.g., "classic", "herringbone")
    
    Returns:
        RosettePattern object
        
    Raises:
        HTTPException 404 if pattern not found
    """
    pattern = get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(
            status_code=404,
            detail=f"Pattern '{pattern_id}' not found in library"
        )
    return pattern


@router.post("/patterns", response_model=RosettePattern)
async def create_or_update_rosette_pattern(pattern: RosettePattern):
    """
    Create or update a rosette pattern.

    - If pattern.id exists: updates existing pattern
    - If pattern.id is new: creates new pattern
    
    Args:
        pattern: RosettePattern to save
    
    Returns:
        The saved RosettePattern
    """
    saved = upsert_pattern(pattern)
    return saved


@router.delete("/patterns/{pattern_id}")
async def delete_rosette_pattern(pattern_id: str):
    """
    Delete a rosette pattern from the library.
    
    Args:
        pattern_id: ID of pattern to delete
    
    Returns:
        Confirmation message with deleted pattern ID
        
    Raises:
        HTTPException 404 if pattern not found
    """
    ok = delete_pattern(pattern_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Pattern '{pattern_id}' not found"
        )
    return {"status": "deleted", "pattern_id": pattern_id}
```

**What Changed:**
- ✅ Kept `/preview` signature (Phase 30 tests still pass)
- ✅ Upgraded `/patterns` to use real store
- ✅ Added CRUD endpoints: GET (by ID), POST (upsert), DELETE
- ✅ Added comprehensive docstrings and error handling

---

### **Step 3: Extend Backend Tests**

#### 3.1 Append to `services/api/app/tests/test_art_routes.py`

Add this new test class at the end of the file:

```python
# Add at end of services/api/app/tests/test_art_routes.py

from app.models.art_models import RosettePattern


class TestRosettePatterns:
    """Tests for Rosette pattern library endpoints (Phase 31.0)."""

    def test_list_patterns_returns_defaults(self):
        """Test that /patterns returns default seed patterns."""
        resp = client.get("/api/art/rosette/patterns")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check for default seed patterns
        ids = [p["id"] for p in data]
        assert "classic" in ids
        assert "herringbone" in ids
        assert "simple" in ids

    def test_get_pattern_by_id(self):
        """Test fetching a single pattern by ID."""
        resp = client.get("/api/art/rosette/patterns/classic")
        assert resp.status_code == 200
        pattern = resp.json()
        assert pattern["id"] == "classic"
        assert pattern["name"] == "Classic Rosette"
        assert pattern["rings"] == 3

    def test_get_pattern_not_found(self):
        """Test 404 response for non-existent pattern."""
        resp = client.get("/api/art/rosette/patterns/nonexistent")
        assert resp.status_code == 404

    def test_create_and_get_pattern(self):
        """Test creating a new pattern and retrieving it."""
        payload = {
            "id": "test-parametric",
            "name": "Test Parametric Rosette",
            "rings": 5,
            "description": "For unit tests",
        }
        
        # Create
        resp = client.post("/api/art/rosette/patterns", json=payload)
        assert resp.status_code == 200
        created = resp.json()
        assert created["id"] == "test-parametric"
        assert created["rings"] == 5
        assert created["name"] == "Test Parametric Rosette"

        # Fetch
        resp = client.get("/api/art/rosette/patterns/test-parametric")
        assert resp.status_code == 200
        fetched = resp.json()
        assert fetched["name"] == "Test Parametric Rosette"
        assert fetched["description"] == "For unit tests"

    def test_update_existing_pattern(self):
        """Test updating an existing pattern (upsert behavior)."""
        # Create initial pattern
        payload = {
            "id": "to-update",
            "name": "Original Name",
            "rings": 3,
            "description": "Original description",
        }
        resp = client.post("/api/art/rosette/patterns", json=payload)
        assert resp.status_code == 200

        # Update with new data
        updated_payload = {
            "id": "to-update",
            "name": "Updated Name",
            "rings": 5,
            "description": "Updated description",
        }
        resp = client.post("/api/art/rosette/patterns", json=updated_payload)
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["name"] == "Updated Name"
        assert updated["rings"] == 5

        # Verify update persisted
        resp = client.get("/api/art/rosette/patterns/to-update")
        assert resp.status_code == 200
        fetched = resp.json()
        assert fetched["name"] == "Updated Name"

    def test_delete_pattern(self):
        """Test deleting a pattern from the library."""
        # Ensure it exists
        resp = client.post(
            "/api/art/rosette/patterns",
            json={
                "id": "to-delete",
                "name": "Temp Pattern",
                "rings": 2,
                "description": "To be deleted",
            },
        )
        assert resp.status_code == 200

        # Delete
        resp = client.delete("/api/art/rosette/patterns/to-delete")
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "deleted"
        assert result["pattern_id"] == "to-delete"

        # Verify gone
        resp = client.get("/api/art/rosette/patterns/to-delete")
        assert resp.status_code == 404

    def test_delete_nonexistent_pattern(self):
        """Test 404 response when deleting non-existent pattern."""
        resp = client.delete("/api/art/rosette/patterns/does-not-exist")
        assert resp.status_code == 404

    def test_preview_with_pattern_library_integration(self):
        """Test preview endpoint works with pattern library patterns."""
        # Ensure pattern exists
        resp = client.get("/api/art/rosette/patterns/classic")
        assert resp.status_code == 200
        pattern = resp.json()

        # Generate preview using pattern
        resp = client.post(
            "/api/art/rosette/preview",
            params={
                "pattern_name": pattern["id"],
                "diameter_mm": 100,
                "ring_count": pattern["rings"],
            },
        )
        assert resp.status_code == 200
        preview = resp.json()
        assert preview["pattern_name"] == "classic"
        assert preview["ring_count"] == 3
```

**Test Coverage:**
- ✅ List patterns (default seeds)
- ✅ Get pattern by ID (success + 404)
- ✅ Create new pattern
- ✅ Update existing pattern (upsert)
- ✅ Delete pattern (success + 404)
- ✅ Preview integration with pattern library

---

### **Step 4: Frontend Pattern Selector**

#### 4.1 Update `packages/client/src/views/art/ArtStudioRosette.vue`

Replace the entire file with this parametric version:

```vue
<!-- packages/client/src/views/art/ArtStudioRosette.vue -->
<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import ArtStudioLayout from "./ArtStudioLayout.vue";

interface RosettePattern {
  id: string;
  name: string;
  rings: number;
  description?: string;
}

interface PreviewResult {
  job_id: string;
  status: string;
  svg?: string;
  dxf?: string;
  gcode_summary?: string;
  pattern_name: string;
  diameter_mm: number;
  ring_count: number;
}

const patterns = ref<RosettePattern[]>([]);
const selectedPatternId = ref<string | null>(null);
const diameter = ref(100);
const ringCount = ref(3);

const loadingPatterns = ref(false);
const previewResult = ref<PreviewResult | null>(null);
const previewLoading = ref(false);
const previewError = ref<string | null>(null);

const selectedPattern = computed(() =>
  patterns.value.find((p) => p.id === selectedPatternId.value) || null
);

onMounted(async () => {
  await loadPatterns();
});

async function loadPatterns() {
  loadingPatterns.value = true;
  try {
    const resp = await fetch("/api/art/rosette/patterns");
    if (!resp.ok) throw new Error(`Failed to load patterns: ${resp.status}`);
    const data = (await resp.json()) as RosettePattern[];
    patterns.value = data;
    
    // Auto-select first pattern if available
    if (data.length > 0 && !selectedPatternId.value) {
      selectedPatternId.value = data[0].id;
      ringCount.value = data[0].rings;
    }
  } catch (err: any) {
    console.error("Error loading patterns:", err);
    previewError.value = `Failed to load pattern library: ${err.message}`;
  } finally {
    loadingPatterns.value = false;
  }
}

async function generatePreview() {
  if (!selectedPattern.value) return;

  previewLoading.value = true;
  previewError.value = null;
  previewResult.value = null;

  const params = new URLSearchParams({
    pattern_name: selectedPattern.value.id,
    diameter_mm: String(diameter.value),
    ring_count: String(ringCount.value),
  });

  try {
    const resp = await fetch(`/api/art/rosette/preview?${params.toString()}`, {
      method: "POST",
    });
    if (!resp.ok) throw new Error(`Preview failed: ${resp.status}`);
    previewResult.value = await resp.json();
  } catch (err: any) {
    previewError.value = err?.message ?? "Unknown error";
  } finally {
    previewLoading.value = false;
  }
}

function onPatternChange(id: string) {
  const p = patterns.value.find((p) => p.id === id);
  selectedPatternId.value = id;
  if (p) {
    ringCount.value = p.rings;
  }
}
</script>

<template>
  <ArtStudioLayout>
    <section class="space-y-4">
      <h2 class="text-xl font-semibold">Rosette Designer</h2>
      <p class="text-sm opacity-80">
        Choose a pattern from the library and generate a parametric preview.
      </p>

      <!-- Pattern Library + Parameters -->
      <div class="border rounded-xl p-4 space-y-3 bg-white shadow-sm">
        <div>
          <label class="block text-sm font-medium mb-1">Pattern</label>
          <select
            v-model="selectedPatternId"
            class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-sky-500 focus:border-transparent"
            :disabled="loadingPatterns"
            @change="onPatternChange(($event.target as HTMLSelectElement).value)"
          >
            <option v-if="loadingPatterns" disabled>Loading patterns…</option>
            <option v-if="!loadingPatterns && patterns.length === 0" disabled>
              No patterns available
            </option>
            <option
              v-for="pattern in patterns"
              :key="pattern.id"
              :value="pattern.id"
            >
              {{ pattern.name }} ({{ pattern.rings }} rings)
            </option>
          </select>
          <p v-if="selectedPattern" class="mt-1 text-xs text-gray-600">
            {{ selectedPattern.description }}
          </p>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium mb-1">
              Diameter (mm)
            </label>
            <input
              v-model.number="diameter"
              type="number"
              class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              min="50"
              max="200"
              step="1"
            />
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">
              Ring Count
            </label>
            <input
              v-model.number="ringCount"
              type="number"
              class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              min="1"
              max="10"
              step="1"
            />
          </div>
        </div>

        <button
          @click="generatePreview"
          :disabled="previewLoading || !selectedPatternId"
          class="w-full px-4 py-2 bg-sky-500 text-white rounded hover:bg-sky-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="previewLoading">⏳ Generating Preview…</span>
          <span v-else>🎨 Generate Preview</span>
        </button>

        <p v-if="previewError" class="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
          ❌ {{ previewError }}
        </p>
      </div>

      <!-- Preview Area -->
      <div class="border rounded-xl p-4 min-h-[300px] bg-gray-50">
        <template v-if="previewResult">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold">Preview Summary</h3>
              <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                {{ previewResult.status }}
              </span>
            </div>
            
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div class="bg-white p-2 rounded border">
                <span class="text-gray-600">Pattern:</span>
                <span class="font-medium ml-1">{{ previewResult.pattern_name }}</span>
              </div>
              <div class="bg-white p-2 rounded border">
                <span class="text-gray-600">Diameter:</span>
                <span class="font-medium ml-1">{{ previewResult.diameter_mm }}mm</span>
              </div>
              <div class="bg-white p-2 rounded border">
                <span class="text-gray-600">Rings:</span>
                <span class="font-medium ml-1">{{ previewResult.ring_count }}</span>
              </div>
              <div class="bg-white p-2 rounded border">
                <span class="text-gray-600">Job ID:</span>
                <span class="font-mono text-xs ml-1">{{ previewResult.job_id }}</span>
              </div>
            </div>

            <details class="mt-3">
              <summary class="cursor-pointer text-sm font-medium text-sky-600 hover:text-sky-700">
                View Full Response
              </summary>
              <pre class="mt-2 text-xs bg-white p-3 rounded border overflow-x-auto">{{ JSON.stringify(previewResult, null, 2) }}</pre>
            </details>
          </div>
        </template>
        <template v-else>
          <div class="flex items-center justify-center h-full">
            <p class="text-sm text-center text-gray-500">
              Select a pattern and click
              <strong class="text-sky-600">Generate Preview</strong>
              to see your rosette design.
            </p>
          </div>
        </template>
      </div>
    </section>
  </ArtStudioLayout>
</template>

<style scoped>
/* Smooth transitions */
input:focus,
select:focus,
button:hover {
  transition: all 0.2s ease;
}

/* Preview card elevation */
.border.rounded-xl {
  transition: box-shadow 0.2s ease;
}

.border.rounded-xl:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
</style>
```

**UI Features:**
- ✅ Pattern selector (dropdown) with auto-load from API
- ✅ Auto-populates ring count when pattern changes
- ✅ Live diameter and ring count parameters
- ✅ Loading states and error handling
- ✅ Formatted preview display with collapsible JSON
- ✅ Smooth transitions and hover effects

---

## 🧪 Testing Guide

### **Backend Tests**

```powershell
# Navigate to API directory
cd services/api

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run all Art Studio tests
pytest app/tests/test_art_routes.py -v

# Run only Phase 31 pattern tests
pytest app/tests/test_art_routes.py::TestRosettePatterns -v

# Check coverage
pytest app/tests/test_art_routes.py --cov=app/routers/art --cov=app/services/rosette_pattern_store --cov-report=term
```

**Expected Output:**
```
test_art_routes.py::TestRosettePatterns::test_list_patterns_returns_defaults PASSED
test_art_routes.py::TestRosettePatterns::test_get_pattern_by_id PASSED
test_art_routes.py::TestRosettePatterns::test_get_pattern_not_found PASSED
test_art_routes.py::TestRosettePatterns::test_create_and_get_pattern PASSED
test_art_routes.py::TestRosettePatterns::test_update_existing_pattern PASSED
test_art_routes.py::TestRosettePatterns::test_delete_pattern PASSED
test_art_routes.py::TestRosettePatterns::test_delete_nonexistent_pattern PASSED
test_art_routes.py::TestRosettePatterns::test_preview_with_pattern_library_integration PASSED

========== 8 passed in 0.42s ==========
```

### **Frontend Manual Testing**

```powershell
# Navigate to client directory
cd packages/client

# Start dev server
npm run dev
```

**Test Checklist:**
- [ ] Navigate to `http://localhost:5173/art/rosette`
- [ ] Verify pattern dropdown loads 4+ default patterns
- [ ] Select "Classic Rosette" - ring count should auto-populate to 3
- [ ] Change diameter to 120mm
- [ ] Click "Generate Preview" - should see formatted results
- [ ] Select "Herringbone" - ring count should change to 4
- [ ] Verify error handling (stop backend, try preview)

### **API Smoke Tests**

```powershell
# Start backend
cd services/api
uvicorn app.main:app --reload --port 8000

# In another terminal:

# List patterns
curl http://localhost:8000/api/art/rosette/patterns

# Get specific pattern
curl http://localhost:8000/api/art/rosette/patterns/classic

# Create new pattern
curl -X POST http://localhost:8000/api/art/rosette/patterns `
  -H "Content-Type: application/json" `
  -d '{"id":"test","name":"Test Pattern","rings":3,"description":"Test"}'

# Generate preview
curl -X POST "http://localhost:8000/api/art/rosette/preview?pattern_name=classic&diameter_mm=100&ring_count=3"

# Delete pattern
curl -X DELETE http://localhost:8000/api/art/rosette/patterns/test
```

---

## 🔗 Integration with Phase 30.0

### **Backward Compatibility**

✅ **All Phase 30 tests still pass:**
- `/preview` endpoint unchanged
- `/patterns` upgraded from static to dynamic (same response format)
- No breaking changes to route structure

✅ **Clean extension pattern:**
- Phase 30 router → Phase 31 adds CRUD endpoints
- Phase 30 tests → Phase 31 adds pattern library tests
- Phase 30 UI → Phase 31 upgrades to parametric selector

### **File Dependencies**

```
Phase 30.0 Files (Required):
✓ services/api/app/routers/art/__init__.py
✓ services/api/app/routers/art/root_art_router.py
✓ services/api/app/models/art_models.py
✓ services/api/app/tests/test_art_routes.py
✓ packages/client/src/views/art/ArtStudioLayout.vue
✓ packages/client/src/router/artRoutes.ts

Phase 31.0 Files (New):
+ services/api/app/services/rosette_pattern_store.py
+ services/api/app/data/rosette_patterns.json (auto-created)

Phase 31.0 Files (Modified):
~ services/api/app/routers/art/rosette_router.py (extended)
~ services/api/app/tests/test_art_routes.py (tests added)
~ packages/client/src/views/art/ArtStudioRosette.vue (upgraded)
```

---

## 📊 Verification Checklist

### **Backend**
- [ ] `rosette_pattern_store.py` imports without errors
- [ ] `rosette_router.py` imports store functions
- [ ] `/api/art/rosette/patterns` returns 4 default patterns
- [ ] `/api/art/rosette/patterns/classic` returns pattern details
- [ ] POST to `/api/art/rosette/patterns` creates new pattern
- [ ] DELETE to `/api/art/rosette/patterns/{id}` removes pattern
- [ ] All 8 new tests pass in `TestRosettePatterns`

### **Frontend**
- [ ] `/art/rosette` route renders without errors
- [ ] Pattern dropdown populates from API
- [ ] Selecting pattern updates ring count automatically
- [ ] Generate Preview button calls `/preview` with correct params
- [ ] Preview results display in formatted card
- [ ] Error states show user-friendly messages

### **Integration**
- [ ] Phase 30 tests still pass (backward compatibility)
- [ ] CI workflow passes without modification
- [ ] Pattern data persists across server restarts
- [ ] Multiple patterns can be created/deleted

---

## 🚀 Deployment Instructions

### **Quick Apply (All Steps)**

```powershell
# 1. Create pattern store
New-Item -ItemType File -Force -Path "services/api/app/services/rosette_pattern_store.py"
# Paste code from Step 1.1

# 2. Update rosette router
# Replace services/api/app/routers/art/rosette_router.py with code from Step 2.1

# 3. Extend tests
# Append code from Step 3.1 to services/api/app/tests/test_art_routes.py

# 4. Update frontend
# Replace packages/client/src/views/art/ArtStudioRosette.vue with code from Step 4.1

# 5. Test backend
cd services/api
pytest app/tests/test_art_routes.py::TestRosettePatterns -v

# 6. Test frontend
cd packages/client
npm run dev
# Visit http://localhost:5173/art/rosette
```

### **Git Workflow**

```bash
# Create feature branch
git checkout -b feature/phase-31-rosette-parametrics

# Add changes
git add services/api/app/services/rosette_pattern_store.py
git add services/api/app/routers/art/rosette_router.py
git add services/api/app/tests/test_art_routes.py
git add packages/client/src/views/art/ArtStudioRosette.vue

# Commit
git commit -m "Phase 31.0: Add Rosette parametric pattern library

- Add file-based pattern store with default seed patterns
- Extend rosette router with CRUD endpoints
- Add 8 new pattern library tests
- Upgrade UI with pattern selector and live preview
- Maintains backward compatibility with Phase 30.0"

# Push
git push origin feature/phase-31-rosette-parametrics
```

---

## 📝 Next Steps (Phase 32.0+)

### **Suggested Future Enhancements:**

1. **Pattern Import/Export**
   - Export pattern library as JSON file
   - Import patterns from external files
   - Share patterns between installations

2. **Advanced Parametrics**
   - Ring width ratios
   - Color/material per ring
   - Custom inlay patterns

3. **Real SVG Generation**
   - Replace placeholder SVG with actual rosette rendering
   - Interactive SVG preview with zoom/pan
   - Export high-res PNG/PDF

4. **Relief + Adaptive Pattern Libraries**
   - Mirror pattern store pattern for other lanes
   - Cross-lane pattern sharing
   - Unified pattern management UI

---

## ✅ Completion Criteria

Phase 31.0 is **100% complete** when:

1. ✅ Pattern store file exists and auto-seeds defaults
2. ✅ All 4 CRUD endpoints respond correctly
3. ✅ 8 new tests pass in `TestRosettePatterns`
4. ✅ Frontend loads patterns from API
5. ✅ Pattern selector updates parameters automatically
6. ✅ Preview generation uses selected pattern
7. ✅ Phase 30 tests remain passing (backward compatibility)
8. ✅ CI workflow passes without modification

---

**Status:** ✅ Ready for Implementation  
**Estimated Time:** 1-2 hours for full application + testing  
**Breaking Changes:** None (purely additive, backward compatible)  
**Dependencies:** Phase 30.0 Completion Patch must be applied first
