# Luthier's Tool Box - Coding Policy & Developer Handoff Guide

**Project:** CNC Guitar Lutherie CAD/CAM Toolbox  
**Repository:** `HanzoRazer/luthiers-toolbox`  
**Last Updated:** November 9, 2025

---

## Primary Technology Stack

### Core Languages

**Python 3.11+ (Backend) - ~60% of codebase**
- Modern async/await patterns (`asyncio`, `FastAPI`)
- Type hints required (`pydantic>=2.0.0` for schemas)
- Strict validation for geometry and CAM operations

**TypeScript/JavaScript (Frontend) - ~40% of codebase**
- Vue 3 Composition API (`<script setup>` syntax)
- Type safety enforced (`.ts` files, typed props/emits)
- ES modules with Vite bundling

**PowerShell (Automation) - Windows-first tooling**
- All test scripts have `.ps1` variants (e.g., `test_adaptive_l1.ps1`)
- Bash equivalents for CI/Linux compatibility

### Configuration Languages

- **JSON** - Post-processor configs (`services/api/app/data/posts/*.json`), geometry data
- **YAML** - Docker Compose, CI workflows (`.github/workflows/*.yml`)
- **Markdown** - Documentation (patch notes, integration guides)

---

## Python Coding Standards

### Style & Formatting

```python
#!/usr/bin/env python3
"""
Module for adaptive pocket toolpath generation.

Implements L.1 robust offsetting with pyclipper.
"""

# Imports: stdlib → third-party → local (sorted alphabetically)
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pyclipper
from shapely.geometry import Polygon

from ..cam.adaptive_core_l1 import plan_adaptive_l1
from ..schemas.cam_sim import SimIssue, SimIssuesSummary
from ..util.units import scale_geom_units
```

### Type Safety

```python
# Always use type hints (enforced by pydantic)
def plan_adaptive_l1(
    loops: List[Dict[str, Any]],
    tool_d: float,
    stepover: float,
    stepdown: float,
    margin: float,
    strategy: str,
    smoothing: float = 0.3
) -> List[Tuple[float, float]]:
    """
    Plan adaptive pocket toolpath with robust offsetting.
    
    Args:
        loops: Boundary loops (first=outer, rest=islands)
        tool_d: Tool diameter in mm
        stepover: Stepover as fraction of tool_d (0.3-0.7)
        stepdown: Z-axis depth per pass in mm
        margin: Clearance from boundary in mm
        strategy: "Spiral" (continuous) or "Lanes" (discrete)
        smoothing: Arc tolerance for rounded joins (0.05-1.0 mm)
        
    Returns:
        List of (x, y) toolpath points in mm
        
    Raises:
        ValueError: If tool_d <= 0 or stepover out of range
    """
    if tool_d <= 0:
        raise ValueError(f"Invalid tool diameter: {tool_d}")
    
    # ... implementation
    return path_points
```

### Async Patterns

```python
# Database operations MUST be async (if DB integration added)
async def fetch_geometry_from_db(workspace_id: str) -> Dict[str, Any]:
    async with get_db_session() as session:
        result = await session.execute(query)
        return result.scalar()

# File I/O can remain sync (not performance-critical)
def load_dxf_geometry(dxf_path: str) -> Dict[str, Any]:
    with open(dxf_path, "r") as f:
        # DXF parsing is CPU-bound, sync is fine
        return parse_dxf(f)
```

### Error Handling

```python
# Fail-safe: Default to conservative values on errors
try:
    smoothing = max(0.05, min(1.0, body.smoothing))
except Exception as e:
    logger.warning(f"Invalid smoothing value, using default: {e}")
    smoothing = 0.3  # Safe default

# Geometry validation MUST catch invalid input
if tool_d >= min_pocket_dimension:
    raise HTTPException(
        status_code=400,
        detail=f"Tool diameter ({tool_d}mm) too large for pocket"
    )
```

### Configuration Access

```python
# Environment-driven config (never hardcode paths)
from pathlib import Path
import os

# Use Path for cross-platform compatibility
DATA_DIR = Path(__file__).parent / "data"
POSTS_DIR = DATA_DIR / "posts"

# Environment variables for deployment settings
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Never commit secrets - use .env files
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # For Blueprint Lab
```

---

## TypeScript/Vue Coding Standards

### Component Structure

```vue
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import type { BackplotLoop, BackplotMove, SimIssue } from '@/types/cam';
import { planAdaptive, generateGcode } from '@/api/adaptive';

// Props with types
interface Props {
  loops: BackplotLoop[];
  toolDiameter: number;
  units?: 'mm' | 'inch';
}

const props = withDefaults(defineProps<Props>(), {
  units: 'mm'
});

// Emits with types
const emit = defineEmits<{
  'update:moves': [moves: BackplotMove[]];
  'error': [message: string];
}>();

// Reactive state
const moves = ref<BackplotMove[]>([]);
const isLoading = ref(false);

// Computed properties
const totalLength = computed(() =>
  moves.value.reduce((sum, m) => sum + (m.length ?? 0), 0)
);

// Watchers
watch(() => props.toolDiameter, (newDiam) => {
  if (newDiam <= 0) {
    emit('error', 'Tool diameter must be positive');
  }
});

// Lifecycle
onMounted(async () => {
  await loadInitialData();
});
</script>

<template>
  <div class="cam-viewer">
    <canvas ref="canvasRef" :width="800" :height="600" />
    <div class="stats">
      Length: {{ totalLength.toFixed(2) }} {{ props.units }}
    </div>
  </div>
</template>

<style scoped>
.cam-viewer {
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>
```

### API Client Pattern

```typescript
// packages/client/src/api/adaptive.ts
import { postJson, getJson } from './base';

const base = '/cam/pocket/adaptive';

export interface PlanIn {
  loops: Loop[];
  units: 'mm' | 'inch';
  tool_d: number;
  stepover?: number;
  strategy?: 'Spiral' | 'Lanes';
}

export interface PlanOut {
  moves: Move[];
  stats: {
    length_mm: number;
    time_s: number;
    area_mm2: number;
  };
}

// Type-safe API calls
export const planAdaptive = (payload: PlanIn) =>
  postJson<PlanOut>(`${base}/plan`, payload);

export const planAdaptiveFromDxf = (payload: PlanFromDxfIn) =>
  postJson<PlanFromDxfOut>(`${base}/plan_from_dxf`, payload);
```

---

## File Organization Rules

### Source Code Structure

```
services/api/app/
├── cam/                # CAM algorithms (adaptive, infill, helical)
│   ├── adaptive_core_l1.py
│   ├── adaptive_core_l2.py
│   ├── trochoid_l3.py
│   └── feedtime.py
├── routers/            # FastAPI endpoints
│   ├── adaptive_router.py
│   ├── pipeline_router.py
│   ├── machines_router.py
│   └── posts_router.py
├── schemas/            # Pydantic models
│   ├── cam_sim.py
│   └── geometry.py
├── services/           # Business logic
│   └── cam_sim_bridge.py
├── util/               # Utilities
│   ├── units.py        # mm ↔ inch conversion
│   └── exporters.py    # DXF/SVG/G-code export
├── data/               # Static configuration
│   └── posts/          # Post-processor JSON configs
└── main.py             # FastAPI app entrypoint
```

### Frontend Structure

```
packages/client/src/
├── api/                # TypeScript API clients
│   ├── adaptive.ts
│   ├── pipeline.ts
│   └── blueprint.ts
├── components/         # Reusable Vue components
│   ├── cam/
│   │   ├── CamBackplotViewer.vue
│   │   └── CamPipelineRunner.vue
│   └── GeometryOverlay.vue
├── views/              # Lab/page components
│   ├── AdaptiveKernelLab.vue
│   ├── PipelineLab.vue
│   ├── BlueprintLab.vue
│   └── art/            # Specialized art studio views
├── types/              # TypeScript type definitions
│   └── cam.ts
└── stores/             # State management (optional)
```

### Documentation Structure

```
docs/
├── ADAPTIVE_POCKETING_MODULE_L.md
├── PATCH_L1_ROBUST_OFFSETTING.md
├── PATCH_L2_TRUE_SPIRALIZER.md
├── INTEGRATION_COMPLETE_V16_1.md
└── BLUEPRINT_LAB_INTEGRATION_COMPLETE.md
```

---

## Critical Safety Rules

### 1. Unit Consistency

```python
# ❌ WRONG - Mixed units
def plan_pocket(loops, tool_d_inch, stepover_mm):
    # Disaster waiting to happen

# ✅ CORRECT - All internal operations in mm
def plan_pocket(loops: List[Loop], tool_d: float, stepover: float, units: str = "mm"):
    """All dimensions in mm internally."""
    if units == "inch":
        tool_d = tool_d * 25.4  # Convert at boundary
    # ... process in mm
```

### 2. Geometry Validation

```python
# All geometry inputs MUST be validated
def validate_pocket_geometry(loops: List[Loop], tool_d: float) -> Tuple[bool, List[str]]:
    """
    Validate pocket is machinable with given tool.
    
    Returns:
        (valid: bool, errors: List[str])
    """
    errors = []
    
    if not loops:
        errors.append("No boundary loops provided")
    
    outer = loops[0]
    min_dimension = min(outer.width, outer.height)
    if tool_d >= min_dimension:
        errors.append(f"Tool ({tool_d}mm) too large for pocket ({min_dimension}mm)")
    
    return len(errors) == 0, errors
```

### 3. Post-Processor Safety

```python
# ❌ WRONG - Hardcoded G-code
gcode = "G0 Z5\nG1 X10 Y10 F1200\n"

# ✅ CORRECT - Post-processor aware
def generate_gcode(moves: List[Move], post_id: str) -> str:
    """Generate G-code with proper post-processor headers/footers."""
    post_config = load_post_config(post_id)  # From data/posts/{post_id}.json
    
    lines = []
    lines.extend(post_config["header"])  # Machine-specific setup
    
    for move in moves:
        lines.append(format_move(move, post_config["dialect"]))
    
    lines.extend(post_config["footer"])  # Safe shutdown
    
    return "\n".join(lines)
```

### 4. DXF Export Compatibility

```python
# ❌ WRONG - Modern DXF features
doc = ezdxf.new("R2018")
doc.modelspace().add_spline(...)

# ✅ CORRECT - R12 for maximum CAM compatibility
doc = ezdxf.new("R12")  # AC1009
msp = doc.modelspace()
msp.add_lwpolyline(points, dxfattribs={"closed": True})  # Closed paths only
```

---

## Naming Conventions

### Variables & Functions

**Python:** `snake_case` for everything (PEP 8)
```python
def plan_adaptive_pocket(loops, tool_diameter, stepover_ratio):
    path_points = []
    min_safe_radius = tool_diameter / 2 + margin
```

**TypeScript:** `camelCase` for variables/functions, `PascalCase` for types
```typescript
function planAdaptivePocket(loops: Loop[], toolDiameter: number): Move[] {
  const pathPoints: Point[] = [];
  const minSafeRadius = toolDiameter / 2 + margin;
}
```

### Files

**Python Modules:** `lowercase_with_underscores.py`
- `adaptive_core_l1.py`, `cam_sim_bridge.py`, `units.py`

**Vue Components:** `PascalCase.vue`
- `CamBackplotViewer.vue`, `AdaptiveKernelLab.vue`, `PipelineLab.vue`

**TypeScript Modules:** `camelCase.ts`
- `adaptive.ts`, `pipeline.ts`, `blueprint.ts`

**Configs:** Descriptive names with extensions
- `grbl.json`, `mach4.json`, `docker-compose.yml`

### Environment Variables

**Prefix:** None (simple project, not multi-tenant)

**Naming:** `UPPERCASE_WITH_UNDERSCORES`
```bash
API_HOST=localhost
API_PORT=8000
VITE_API_BASE_URL=http://localhost:8000
```

---

## Docker & Infrastructure

### Compose Files

```
docker-compose.yml                    # Main stack (API + Client + Proxy)
docker/
├── api/Dockerfile                    # FastAPI backend
├── client/Dockerfile                 # Vue 3 frontend
└── proxy/Dockerfile                  # Nginx reverse proxy
```

### Health Checks

```yaml
# docker-compose.yml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Git Workflow

### Branch Strategy

- **`main`** - Production-ready code (protected)
- **Feature branches** - `feature/blueprint-lab`, `feature/adaptive-l3`
- **Patch branches** - `patch/l1-robust-offsetting`

### Commit Messages

```bash
feat(adaptive): add L.3 trochoidal insertion
fix(units): correct inch-to-mm conversion factor
docs(integration): add v16.1 complete summary
ci(tests): add adaptive pocket L.1 island tests
```

### Pre-Commit Checks

```powershell
# Run before committing
pytest services/api/app/tests/ -q    # Backend tests
cd packages/client && npm run build  # Frontend build test
ruff check services/api              # Python linting
```

---

## Testing Requirements

### Backend Tests

**Location:** `services/api/app/tests/`

**Coverage Target:** >70% for CAM algorithms

```python
# test_adaptive_l1.py
def test_plan_with_island():
    loops = [
        {"pts": [[0,0], [100,0], [100,60], [0,60]]},      # outer
        {"pts": [[30,15], [70,15], [70,45], [30,45]]}     # island
    ]
    
    path = plan_adaptive_l1(
        loops,
        tool_d=6.0,
        stepover=0.45,
        stepdown=1.5,
        margin=0.5,
        strategy="Spiral",
        smoothing=0.3
    )
    
    assert len(path) > 0
    assert no_island_collision(path, loops[1])
```

### Frontend Tests

**Location:** `packages/client/src/__tests__/`

**Coverage:** Component rendering, API contract validation

```typescript
// CamBackplotViewer.test.ts
import { mount } from '@vue/test-utils';
import CamBackplotViewer from '@/components/cam/CamBackplotViewer.vue';

test('renders toolpath moves', () => {
  const wrapper = mount(CamBackplotViewer, {
    props: {
      moves: [
        { code: 'G0', x: 0, y: 0, z: 5 },
        { code: 'G1', x: 10, y: 10, z: -1.5 }
      ]
    }
  });
  
  expect(wrapper.find('canvas').exists()).toBe(true);
});
```

### Integration Tests

**PowerShell Scripts:**
```powershell
# test_adaptive_l1.ps1
$body = @{
  loops = @(
    @{pts = @(@(0,0), @(100,0), @(100,60), @(0,60))}
  )
  tool_d = 6.0
  stepover = 0.45
  strategy = "Spiral"
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod `
  -Uri "http://localhost:8000/cam/pocket/adaptive/plan" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"

Write-Host "✓ Path length: $($response.stats.length_mm) mm"
```

### CI Environment

**.github/workflows/adaptive_pocket.yml**
```yaml
name: Adaptive Pocket Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r services/api/requirements.txt
      - run: pytest services/api/app/tests/test_adaptive_*.py -v
```

---

## Documentation Standards

### Docstrings (Google Style)

```python
def inject_min_fillet(
    path: List[Tuple[float, float]],
    min_radius: float,
    arc_tol: float = 0.1
) -> List[Tuple[float, float]]:
    """
    Insert arc fillets at sharp corners in toolpath.
    
    Prevents sudden direction changes that cause machine jerking.
    
    Args:
        path: List of (x, y) coordinates in mm
        min_radius: Minimum corner radius to enforce (mm)
        arc_tol: Arc sampling tolerance (mm)
        
    Returns:
        Smoothed path with arc fillets inserted
        
    Raises:
        ValueError: If min_radius <= 0
        
    Example:
        >>> path = [(0, 0), (10, 0), (10, 10)]
        >>> smoothed = inject_min_fillet(path, min_radius=2.0)
        >>> len(smoothed) > len(path)  # Arcs add points
        True
    """
```

### Patch Notes Structure

```markdown
# Patch L.X: Feature Name

**Status:** ✅ Implemented  
**Date:** November 9, 2025  
**Module:** Adaptive Pocketing Engine

## Overview
Brief description of what changed and why.

## Implementation Details
- Key algorithms
- File changes
- API updates

## Usage Examples
Code snippets showing before/after

## Testing
How to validate the changes

## Migration Guide (if breaking)
Steps to upgrade existing code
```

---

## Key Dependencies & Versions

### Backend (Python)

```txt
# requirements.txt
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
ezdxf>=1.0.0           # DXF R12 export
shapely>=2.0.0         # Geometry operations
pyclipper>=1.3.0       # Robust polygon offsetting
numpy>=1.24.0          # Numerical operations
```

### Frontend (TypeScript/Vue)

```json
// package.json
{
  "dependencies": {
    "vue": "^3.4.0",
    "pinia": "^2.1.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0"
  }
}
```

---

## Handoff Checklist

### New Developer Onboarding

- [ ] **Python 3.11+** installed
- [ ] **Node.js 18+** installed
- [ ] **Virtual environment created:** `python -m venv .venv`
- [ ] **Backend dependencies:** `pip install -r services/api/requirements.txt`
- [ ] **Frontend dependencies:** `cd packages/client && npm install`
- [ ] **Environment configured:** Copy `.env.example` → `.env` (if needed)
- [ ] **Backend runs:** `uvicorn app.main:app --reload --port 8000` (from `services/api/`)
- [ ] **Frontend runs:** `npm run dev` (from `packages/client/`)
- [ ] **Tests pass:** `pytest services/api/app/tests/ -q`
- [ ] **Copilot instructions reviewed:** `.github/copilot-instructions.md`
- [ ] **Integration docs read:** `INTEGRATION_COMPLETE_V16_1.md`
- [ ] **Docker validated:** `docker compose up --build`

### Key Documentation to Read

1. **Architecture:** `.github/copilot-instructions.md` (project overview)
2. **Adaptive Pocketing:** `ADAPTIVE_POCKETING_MODULE_L.md` (CAM algorithms)
3. **Integration Summary:** `INTEGRATION_COMPLETE_V16_1.md` (current state)
4. **Blueprint Lab:** `BLUEPRINT_LAB_INTEGRATION_COMPLETE.md` (DXF workflow)
5. **Multi-Post Export:** `PATCH_K_EXPORT_COMPLETE.md` (G-code generation)

---

## Design Philosophy

This project prioritizes:

1. **CAM Compatibility** over visual fidelity
   - DXF exports are R12 format for legacy software support
   - Closed paths for toolpath generation
   - Millimeter precision matching CNC machinery

2. **Safety** over convenience
   - Geometry validation before CAM operations
   - Post-processor awareness prevents machine crashes
   - Unit conversion at API boundaries only

3. **Modularity** over monoliths
   - Routers are independent (machines, posts, pipeline, adaptive)
   - Components are reusable (CamBackplotViewer, CamPipelineRunner)
   - Algorithms are versioned (L.0, L.1, L.2, L.3)

4. **Documentation** over assumptions
   - Every patch has a detailed markdown summary
   - Integration guides include usage examples
   - API endpoints document expected inputs/outputs

---

## Quick Reference Commands

### Development

```powershell
# Start backend
cd services/api
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Start frontend
cd packages/client
npm run dev

# Run tests
pytest services/api/app/tests/ -v
npm run test  # Frontend (if configured)

# Lint/format
ruff check services/api
black services/api
```

### Docker

```powershell
# Full stack
docker compose up --build

# Individual services
docker compose up api
docker compose up client
docker compose up proxy

# Health checks
curl http://localhost:8000/health
curl http://localhost:8080/  # Client via proxy
```

### Testing Endpoints

```powershell
# Test adaptive pocket planning
Invoke-RestMethod `
  -Uri "http://localhost:8000/cam/pocket/adaptive/plan" `
  -Method POST `
  -Body (@{
    loops = @(@{pts = @(@(0,0), @(100,0), @(100,60), @(0,60))})
    tool_d = 6.0
    stepover = 0.45
    strategy = "Spiral"
  } | ConvertTo-Json -Depth 10) `
  -ContentType "application/json"

# Test machine profiles
curl http://localhost:8000/cam/machines

# Test post-processor configs
curl http://localhost:8000/cam/posts
```

---

**Status:** ✅ Coding Policy Complete  
**Last Updated:** November 9, 2025  
**Maintainer:** HanzoRazer
