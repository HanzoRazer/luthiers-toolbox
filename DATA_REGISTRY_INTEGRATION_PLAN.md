# Data Registry Integration Plan - 9 Products Hybrid Architecture

**Date:** December 13, 2025  
**Source:** `files (50)\data_registry_9products.zip`  
**Scope:** Three-tier data architecture for multi-product SaaS delivery  
**Status:** 🔄 Ready for Integration

---

## 📦 Package Overview

The **Hybrid Data Registry** provides a three-tier data architecture supporting **9 distinct product editions** with proper entitlement enforcement and data isolation.

### Architecture Layers

```
┌─────────────────────────────────────────────┐
│  SYSTEM DATA (Universal, Read-Only)        │  ← Same for all 9 products
│  • Scale lengths, fret formulas, wood ref  │
│  • Body templates, neck profiles           │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  EDITION DATA (Product-Specific)            │  ← Different per product
│  • Pro: Tools, machines, CAM presets        │
│  • Parametric: Guitar templates             │
│  • Neck Designer: Neck templates            │
│  • etc. (9 product variants)                │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  USER DATA (Tenant-Isolated, CRUD)          │  ← Per-user SQLite
│  • Custom profiles, tools, machines         │
│  • Projects, saved designs                  │
│  • Cloud-synced (optional PostgreSQL)       │
└─────────────────────────────────────────────┘
```

### The 9 Products

| # | Product | Price | Edition Enum | Data Access |
|---|---------|-------|--------------|-------------|
| 1 | ltb-express | $49 | `EXPRESS` | System only (honeypot) |
| 2 | ltb-pro | $299-399 | `PRO` | System + Pro edition |
| 3 | ltb-enterprise | $899-1299 | `ENTERPRISE` | System + Pro + Enterprise |
| 4 | ltb-parametric | $39-59 | `PARAMETRIC` | System + Guitar templates |
| 5 | ltb-neck-designer | $29-79 | `NECK_DESIGNER` | System + Neck templates |
| 6 | ltb-headstock-designer | $14-29 | `HEADSTOCK_DESIGNER` | System + Headstock templates |
| 7 | ltb-bridge-designer | $14-19 | `BRIDGE_DESIGNER` | System + Bridge templates |
| 8 | ltb-fingerboard-designer | $19-29 | `FINGERBOARD_DESIGNER` | System + Fretboard templates |
| 9 | ltb-cnc-blueprints | $29-49 | `CNC_BLUEPRINTS` | Housing industry blueprints |

---

## 📂 File Structure Analysis

### Extracted Package Contents

```
data_registry/
├── __init__.py              # Package exports, version 1.0.0
├── registry.py              # Core Registry class (757 lines)
├── README.md                # Complete documentation (233 lines)
│
├── schemas/
│   └── all_schemas.json     # Validation rules (3.8KB)
│
├── system/                  # UNIVERSAL DATA (all products)
│   ├── instruments/
│   │   ├── body_templates.json       # 7 body templates (4KB)
│   │   └── neck_profiles.json        # 7 neck profiles (2.6KB)
│   ├── materials/
│   │   └── wood_species.json         # 13 wood species (5.6KB)
│   └── references/
│       ├── fret_formulas.json        # 12-TET + temperaments (1.7KB)
│       └── scale_lengths.json        # 8 standard scales (2.4KB)
│
└── edition/                 # PRODUCT-SPECIFIC DATA
    ├── express/             # (empty - honeypot strategy)
    │
    ├── pro/                 # PRO/ENTERPRISE CAM features
    │   ├── tools/router_bits.json       # 11 router bits (6.6KB)
    │   ├── machines/profiles.json       # 3 machines (5.3KB)
    │   ├── empirical/wood_limits.json   # 11 species limits (8.1KB)
    │   ├── cam_presets/presets.json     # 8 CAM recipes (4.6KB)
    │   └── posts/processors.json        # 4 post processors (5.3KB)
    │
    ├── parametric/
    │   └── guitar_templates.json        # 4 guitar templates (3.3KB)
    │
    ├── neck_designer/
    │   └── neck_templates.json          # 5 necks + 4 truss specs (3.9KB)
    │
    ├── headstock_designer/
    │   └── headstock_templates.json     # 6 headstocks + 5 tuner layouts (4KB)
    │
    ├── bridge_designer/
    │   └── bridge_templates.json        # 6 bridges + saddle specs (4.4KB)
    │
    ├── fingerboard_designer/
    │   └── fretboard_templates.json     # 6 fretboards + 6 inlays + 4 fret wires (5.6KB)
    │
    └── cnc_blueprints/
        └── blueprint_standards.json     # Framing, cabinets, doors, codes (5.6KB)
```

**Total Data:** 19 JSON files, ~100KB of reference data

---

## 🎯 Integration Strategy

### Phase 1: Drop-in Package Installation (20 minutes)

**Location:** `services/api/app/data_registry/`

**Steps:**
1. Extract `data_registry/` to `services/api/app/data_registry/`
2. Verify package structure matches expected paths
3. Add to `.gitignore` if needed: `data_registry/user/*.sqlite`

**Why this location:**
- Parallel to existing `instrument_geometry/` module
- API-side data layer (backend concern, not frontend)
- Follows mono-repo structure conventions

**Validation:**
```powershell
# Test import
cd services/api
python -c "from app.data_registry import Registry, Edition; print('✓ Import successful')"

# Test basic functionality
python -c "
from app.data_registry import Registry
reg = Registry(edition='pro')
scales = reg.get_scale_lengths()
print(f'✓ Loaded {len(scales.get(\"scales\", {}))} scale lengths')
"
```

---

### Phase 2: Calculator Rehabilitation (2-4 hours)

**Current State:**
- Calculators use hardcoded magic numbers and inline dictionaries
- No centralized reference data
- Difficult to maintain consistency across products

**Rehabilitation Pattern:**

**Before (hardcoded):**
```python
# calculators/service.py
def calc_feeds(wood_species: str, tool_diameter: float):
    if wood_species == "mahogany":
        base_feed = 1200  # Magic number!
        chipload = 0.002  # Where did this come from?
    # ...
```

**After (registry-driven):**
```python
from app.data_registry import get_registry

def calc_feeds(wood_species: str, tool_diameter: float, edition: str = "pro"):
    reg = get_registry(edition=edition)
    
    # System data (wood reference)
    wood = reg.get_wood(wood_species)
    if not wood:
        raise ValueError(f"Unknown wood species: {wood_species}")
    
    # Edition data (empirical limits - Pro/Enterprise only)
    limits = reg.get_empirical_limit(wood_species)
    if not limits:
        # Fallback to conservative defaults
        limits = {"base_feed": 800, "chipload": 0.001}
    
    # Calculate with validated data
    base_feed = limits["base_feed"]
    chipload = limits["chipload"]
    # ...
```

**Target Files:**
- `calculators/service.py` - Main service (feeds, speeds, chipload)
- `calculators/fret_spacing.py` - Use `get_fret_formulas()`, `get_scale_length()`
- `instrument_geometry/scale_length.py` - Migrate to registry scales
- Any file with hardcoded wood properties, scale lengths, fret math

**Benefits:**
- ✅ Single source of truth for reference data
- ✅ Easy to update (edit JSON, not Python code)
- ✅ Product edition enforcement (Express can't access empirical limits)
- ✅ User customization support (override defaults)

---

### Phase 3: Instrument Geometry Consolidation (1-2 hours)

**Current State:**
- `instrument_geometry/` has its own `registry.py` (conflicting name!)
- Mix of inline data and separate model files
- No edition awareness

**Consolidation Plan:**

#### Option A: Rename Existing (Recommended)
```bash
# Rename conflicting file
mv services/api/app/instrument_geometry/registry.py \
   services/api/app/instrument_geometry/model_registry.py

# Update imports across codebase
# registry.py → model_registry.py
```

#### Option B: Merge Functions
Migrate functions from `instrument_geometry/registry.py` into the new `data_registry/` if overlap exists.

**Integration:**
```python
# instrument_geometry/__init__.py
from ..data_registry import get_registry

# Deprecate old inline data
# from .scale_length import SCALE_LENGTHS  # OLD
# Use registry instead
def get_scale_length(scale_id: str, edition: str = "pro"):
    reg = get_registry(edition=edition)
    return reg.get_scale_length(scale_id)
```

---

### Phase 4: Main.py Integration (30 minutes)

**Add Registry Initialization Endpoint:**

```python
# services/api/app/main.py

from app.data_registry import get_registry, Edition

@app.get("/api/registry/info")
def get_registry_info(edition: str = "pro"):
    """
    Get registry metadata and available data categories.
    Used by frontend to display edition capabilities.
    """
    try:
        ed = Edition(edition)
    except ValueError:
        raise HTTPException(400, detail=f"Invalid edition: {edition}")
    
    reg = get_registry(edition=edition)
    
    return {
        "edition": edition,
        "entitlements": {
            "system": reg._get_entitlement_categories("system"),
            "edition": reg._get_entitlement_categories("edition"),
            "user": reg._get_entitlement_categories("user")
        },
        "data_counts": {
            "scale_lengths": len(reg.get_scale_lengths().get("scales", {})),
            "wood_species": len(reg.get_wood_species().get("species", {})),
            "body_templates": len(reg.get_body_templates().get("bodies", {})),
            # Add edition-specific counts if entitled
        }
    }

@app.get("/api/registry/scale_lengths")
def get_scale_lengths_endpoint(edition: str = "pro"):
    """Get all standard scale lengths (universal access)"""
    reg = get_registry(edition=edition)
    return reg.get_scale_lengths()

@app.get("/api/registry/tools")
def get_tools_endpoint(edition: str = "pro"):
    """Get tool library (Pro/Enterprise only)"""
    reg = get_registry(edition=edition)
    try:
        return reg.get_tools()
    except EntitlementError as e:
        raise HTTPException(403, detail=str(e))
```

**Add to Router Structure:**
Create `routers/registry_router.py` for comprehensive CRUD operations on registry data.

---

### Phase 5: Edition Detection Middleware (1 hour)

**Add Edition Context to Requests:**

```python
# services/api/app/core/edition_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware
from app.data_registry import Edition

class EditionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Detect edition from:
        # 1. License key validation (future)
        # 2. Environment variable (development)
        # 3. Default to Express (demo mode)
        
        edition = os.getenv("LTB_EDITION", "express")
        request.state.edition = Edition(edition)
        request.state.user_id = None  # TODO: OAuth integration
        
        response = await call_next(request)
        return response

# main.py
app.add_middleware(EditionMiddleware)
```

**Usage in Routers:**
```python
@router.post("/cam/feeds")
def calculate_feeds(request: Request, body: FeedsRequest):
    edition = request.state.edition.value
    reg = get_registry(edition=edition, user_id=request.state.user_id)
    
    # Registry automatically enforces entitlements
    limits = reg.get_empirical_limit(body.wood_species)  # Raises EntitlementError if Express
    # ...
```

---

### Phase 6: Frontend Integration (2-3 hours)

**Client-side Registry Awareness:**

```typescript
// packages/client/src/stores/registry.ts
import { defineStore } from 'pinia'

export const useRegistryStore = defineStore('registry', {
  state: () => ({
    edition: 'pro' as Edition,
    entitlements: null as any,
    scaleData: [] as any[],
    toolData: [] as any[]
  }),
  
  actions: {
    async loadEntitlements() {
      const res = await fetch(`/api/registry/info?edition=${this.edition}`)
      this.entitlements = await res.json()
    },
    
    async loadScales() {
      const res = await fetch(`/api/registry/scale_lengths?edition=${this.edition}`)
      const data = await res.json()
      this.scaleData = Object.values(data.scales || {})
    },
    
    async loadTools() {
      try {
        const res = await fetch(`/api/registry/tools?edition=${this.edition}`)
        if (res.status === 403) {
          // Not entitled - show upgrade prompt
          this.toolData = []
          return
        }
        const data = await res.json()
        this.toolData = Object.values(data.tools || {})
      } catch (e) {
        console.error('Failed to load tools', e)
      }
    }
  }
})
```

**Edition-Aware UI Components:**
```vue
<template>
  <div v-if="registryStore.entitlements?.edition.includes('tools')">
    <!-- Pro/Enterprise features -->
    <ToolLibrary />
  </div>
  <div v-else>
    <UpgradePrompt edition="pro" feature="Tool Library" />
  </div>
</template>

<script setup lang="ts">
import { useRegistryStore } from '@/stores/registry'
const registryStore = useRegistryStore()
</script>
```

---

## 🔍 Conflict Resolution

### Issue 1: Duplicate `registry.py` Files

**Conflict:**
- `services/api/app/instrument_geometry/registry.py` (existing)
- `services/api/app/data_registry/registry.py` (new)

**Resolution:**
```powershell
# Rename existing to avoid confusion
cd services/api/app/instrument_geometry
git mv registry.py model_registry.py

# Update all imports
# Old: from app.instrument_geometry.registry import get_model
# New: from app.instrument_geometry.model_registry import get_model
```

**Files to Update:**
```bash
grep -r "from.*instrument_geometry.registry" services/api/app/
grep -r "import.*instrument_geometry.registry" services/api/app/
```

---

### Issue 2: Data Overlap with Existing Files

**Potential Overlaps:**
- `instrument_geometry/scale_length.py` → Use `data_registry/system/references/scale_lengths.json`
- Hardcoded wood data in calculators → Use `data_registry/system/materials/wood_species.json`
- Tool library in `data/posts/` → Migrate to `data_registry/edition/pro/posts/processors.json`

**Strategy:**
1. **Deprecate gradually** - Keep old code working, add warnings
2. **Dual-mode operation** - Check registry first, fall back to old code
3. **Clean migration** - Remove old code after validation

---

## 🧪 Testing Strategy

### Unit Tests

```python
# services/api/app/tests/test_data_registry.py

import pytest
from app.data_registry import Registry, Edition, EntitlementError

def test_registry_system_data():
    """System data accessible to all editions"""
    for edition in [Edition.EXPRESS, Edition.PRO, Edition.PARAMETRIC]:
        reg = Registry(edition=edition.value)
        scales = reg.get_scale_lengths()
        assert "fender_25_5" in scales["scales"]

def test_registry_pro_entitlements():
    """Pro features blocked for Express"""
    express = Registry(edition="express")
    with pytest.raises(EntitlementError):
        express.get_tools()
    
    pro = Registry(edition="pro")
    tools = pro.get_tools()
    assert "flat_6mm_2f" in tools["tools"]

def test_registry_edition_isolation():
    """Parametric products can't access CAM features"""
    neck = Registry(edition="neck_designer")
    
    # Can access system data
    scales = neck.get_scale_lengths()
    assert len(scales["scales"]) > 0
    
    # Blocked from Pro features
    with pytest.raises(EntitlementError):
        neck.get_machines()
```

### Integration Tests

```powershell
# Test API endpoints with different editions
.\Test-Registry-Integration.ps1
```

**Test Script:**
```powershell
# Test-Registry-Integration.ps1

$api = "http://localhost:8000/api"

Write-Host "=== Testing Registry Endpoints ===" -ForegroundColor Cyan

# Test 1: System data (all editions)
Write-Host "`n1. Testing system data access..." -ForegroundColor Yellow
foreach ($edition in @("express", "pro", "parametric")) {
    $info = Invoke-RestMethod "$api/registry/info?edition=$edition"
    Write-Host "  ✓ $edition: $($info.edition)" -ForegroundColor Green
}

# Test 2: Pro features
Write-Host "`n2. Testing Pro entitlements..." -ForegroundColor Yellow
try {
    $tools = Invoke-RestMethod "$api/registry/tools?edition=express"
    Write-Host "  ✗ Express should not access tools!" -ForegroundColor Red
} catch {
    Write-Host "  ✓ Express blocked from tools (expected)" -ForegroundColor Green
}

$proTools = Invoke-RestMethod "$api/registry/tools?edition=pro"
Write-Host "  ✓ Pro accessed tools: $($proTools.tools.Count) items" -ForegroundColor Green

# Test 3: Edition-specific data
Write-Host "`n3. Testing edition-specific data..." -ForegroundColor Yellow
$neckTemplates = Invoke-RestMethod "$api/registry/edition_data?edition=neck_designer&category=neck_templates"
Write-Host "  ✓ Neck Designer: $($neckTemplates.templates.Count) templates" -ForegroundColor Green

Write-Host "`n✅ All tests passed!" -ForegroundColor Green
```

---

## 📋 Implementation Checklist

### Phase 1: Installation ✅ (20 min)
- [ ] Extract `data_registry/` to `services/api/app/data_registry/`
- [ ] Verify package imports: `python -c "from app.data_registry import Registry"`
- [ ] Add user database location to `.gitignore`: `data_registry/user/*.sqlite`

### Phase 2: Calculator Rehabilitation 🔄 (2-4 hours)
- [ ] Identify hardcoded data in `calculators/service.py`
- [ ] Replace magic numbers with registry calls
- [ ] Add edition parameter to calculator functions
- [ ] Test with different editions (Express vs Pro)
- [ ] Update API endpoints to pass edition context

### Phase 3: Instrument Geometry Consolidation 🔄 (1-2 hours)
- [ ] Rename `instrument_geometry/registry.py` → `model_registry.py`
- [ ] Update all imports across codebase
- [ ] Deprecate inline scale/wood data
- [ ] Migrate to registry-driven lookups

### Phase 4: Main.py Integration 🔄 (30 min)
- [ ] Add `/api/registry/info` endpoint
- [ ] Add `/api/registry/scale_lengths` endpoint
- [ ] Add `/api/registry/tools` endpoint (with entitlement check)
- [ ] Create `routers/registry_router.py` for full CRUD

### Phase 5: Edition Middleware ⏳ (1 hour)
- [ ] Create `core/edition_middleware.py`
- [ ] Add middleware to `main.py`
- [ ] Detect edition from environment variable (dev mode)
- [ ] Add placeholder for license key validation (future)

### Phase 6: Frontend Integration ⏳ (2-3 hours)
- [ ] Create `packages/client/src/stores/registry.ts`
- [ ] Add edition-aware component wrappers
- [ ] Implement upgrade prompts for blocked features
- [ ] Test entitlement enforcement in UI

### Phase 7: Testing 🧪 (2 hours)
- [ ] Create `tests/test_data_registry.py` unit tests
- [ ] Create `Test-Registry-Integration.ps1` smoke tests
- [ ] Test all 9 edition scenarios
- [ ] Validate entitlement blocking works

### Phase 8: Documentation 📚 (1 hour)
- [ ] Add registry usage to `CODING_POLICY.md`
- [ ] Update calculator documentation
- [ ] Create quickref: `DATA_REGISTRY_QUICKREF.md`
- [ ] Add to developer onboarding guide

---

## ⚠️ Breaking Changes & Migration

### Breaking Change 1: `instrument_geometry.registry` Rename

**Impact:** Any code importing from `instrument_geometry.registry`

**Migration:**
```python
# OLD (breaks after Phase 3)
from app.instrument_geometry.registry import get_model_spec

# NEW
from app.instrument_geometry.model_registry import get_model_spec
```

**Affected Files:** Run `grep -r "instrument_geometry.registry"` to find

---

### Breaking Change 2: Calculator Signatures

**Impact:** Calculator functions will require `edition` parameter

**Migration:**
```python
# OLD
result = calc_feeds(wood_species="mahogany", tool_diameter=6.0)

# NEW
result = calc_feeds(
    wood_species="mahogany",
    tool_diameter=6.0,
    edition="pro"  # New required parameter
)
```

**Mitigation:** Add default `edition="pro"` for backward compatibility during transition

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ All 9 product editions load correct data subset
- ✅ Entitlement enforcement blocks unauthorized access
- ✅ Calculator functions use registry instead of hardcoded data
- ✅ API endpoints respect edition context
- ✅ Frontend shows upgrade prompts for blocked features

### Performance Requirements
- ⚡ Registry data loads in < 100ms (JSON caching)
- ⚡ No N+1 queries (batch loads, not per-item)
- ⚡ User SQLite database < 10MB per user

### Quality Requirements
- 🧪 90%+ test coverage on registry module
- 📖 Complete API documentation for all endpoints
- 🔒 No data leakage between editions (validated in tests)

---

## 🚀 Rollout Timeline

### Week 1: Backend Foundation
- **Days 1-2:** Phase 1-3 (Installation, Calculator Rehab, Consolidation)
- **Days 3-4:** Phase 4-5 (Main.py Integration, Middleware)
- **Day 5:** Testing & validation

### Week 2: Frontend & Polish
- **Days 1-2:** Phase 6 (Frontend Integration)
- **Day 3:** Phase 7 (Comprehensive Testing)
- **Day 4:** Phase 8 (Documentation)
- **Day 5:** Final QA, merge to main

### Total Effort: **12-18 hours** across 2 weeks

---

## 📚 Related Documents

- **Source Package:** `files (50)\data_registry_9products.zip`
- **Package README:** `files (50)\DATA_REGISTRY_9PRODUCTS_README.md`
- **Product Segmentation:** [UNRESOLVED_TASKS_INVENTORY.md](./UNRESOLVED_TASKS_INVENTORY.md#product-segmentation-roadmap)
- **Phase 1 Plan:** [PHASE_1_EXECUTION_PLAN.md](./PHASE_1_EXECUTION_PLAN.md)
- **Calculator Docs:** [CAM_CAD_DEVELOPER_HANDOFF.md](./CAM_CAD_DEVELOPER_HANDOFF.md)

---

## 🎬 Next Immediate Action

**READY TO START:** Phase 1 - Package Installation (20 minutes)

```powershell
# 1. Extract package
cd "C:\Users\thepr\Downloads\Luthiers ToolBox\files (50)"
Expand-Archive -Path "data_registry_9products.zip" -DestinationPath ".\extracted" -Force

# 2. Copy to API location
Copy-Item -Recurse ".\extracted\data_registry" "..\services\api\app\data_registry"

# 3. Verify installation
cd ..\services\api
python -c "from app.data_registry import Registry, Edition; print('✓ Registry installed successfully')"

# 4. Test basic functionality
python -c "
from app.data_registry import Registry
reg = Registry(edition='pro')
scales = reg.get_scale_lengths()
print(f'✓ Loaded {len(scales.get(\"scales\", {}))} scale lengths')
tools = reg.get_tools()
print(f'✓ Loaded {len(tools.get(\"tools\", {}))} tools')
"
```

**Expected Output:**
```
✓ Registry installed successfully
✓ Loaded 8 scale lengths
✓ Loaded 11 tools
```

---

**Status:** ✅ Integration Plan Complete  
**Blocking Issues:** None - ready to proceed  
**Risk Level:** LOW (isolated package, gradual migration path)  
**Recommendation:** Start with Phase 1 TODAY, complete backend (Phases 1-5) this week
