# Luthier's ToolBox — Developer Handoff Document

**Last Updated:** December 11, 2025  
**Status:** Active Development (Phase E)  
**Primary Language:** Python 3.10+  
**Framework:** FastAPI + Pydantic  
**Output Formats:** DXF (CAD), G-code (CNC)

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [Domain Glossary](#2-domain-glossary)
3. [Architecture Overview](#3-architecture-overview)
4. [Phase Progression (A → E)](#4-phase-progression-a--e)
5. [Directory Structure](#5-directory-structure)
6. [Key Files Reference](#6-key-files-reference)
7. [Current Technical Debt](#7-current-technical-debt)
8. [Environment Setup](#8-environment-setup)
9. [Testing Strategy](#9-testing-strategy)
10. [Prioritized Roadmap](#10-prioritized-roadmap)
11. [Common Tasks](#11-common-tasks)
12. [Contacts & Resources](#12-contacts--resources)

---

## 1. What Is This Project?

**Luthier's ToolBox** is a CAM (Computer-Aided Manufacturing) system for guitar builders. It generates:

- **DXF files** — 2D templates for laser cutters and CNC routers
- **G-code** — Machine instructions for CNC fret slot cutting

### The Problem It Solves

A luthier (guitar maker) building a custom instrument needs precise templates:
- Fret slot positions (mathematically derived from scale length)
- Body outlines
- Neck tapers
- Inlay patterns
- Rosette designs

Traditionally, luthiers either:
1. Buy pre-made templates (limited options)
2. Calculate by hand (error-prone, slow)
3. Use general CAD software (steep learning curve)

**Luthier's ToolBox** lets them input guitar specs → get ready-to-cut files.

### The "RMOS" Subsystem

RMOS = **Responsive Manufacturing Optimization System**

This is the "smart" layer that:
- Validates designs against machine capabilities
- Optimizes toolpaths for specific CNC routers
- Calculates feed rates based on material hardness
- Provides feasibility scoring before cutting

Think of it as: "Will this design actually work on my machine, and how should I cut it?"

---

## 2. Domain Glossary

| Term | Definition |
|------|------------|
| **Scale Length** | Distance from nut to bridge saddle (e.g., Fender = 648mm, Gibson = 628mm) |
| **Fret** | Metal wire pressed into slots on fretboard; pressing string against fret shortens vibrating length |
| **Fret Slot** | Thin kerf cut into fretboard where fret wire is inserted (typically 0.5-0.6mm wide, 2-3mm deep) |
| **Nut** | Slotted piece at headstock end that spaces strings; position 0 for fret calculations |
| **Fretboard/Fingerboard** | Wood surface where frets are installed; typically ebony, rosewood, or maple |
| **Fan Fret / Multiscale** | Frets at angles rather than perpendicular; bass strings get longer scale, treble shorter |
| **Perpendicular Fret** | In fan-fret designs, the one fret that's straight across (often 7th or 12th) |
| **Compound Radius** | Fretboard surface curves more at nut (easier chords) than at heel (easier bends) |
| **Rosette** | Decorative ring around soundhole on acoustic guitars |
| **Inlay** | Decorative material (pearl, abalone) set into wood |
| **Kerf** | Width of material removed by cutting tool |
| **Purfling** | Decorative/protective strips around body edge |
| **Rule of 18** | Historical approximation: each fret is 1/18th of remaining scale length (actual = 17.817) |
| **Equal Temperament** | Modern tuning system; fret spacing based on 12th root of 2 (≈1.05946) |

### Measurement Conventions

- All internal calculations use **millimeters**
- API accepts mm by default
- Scale lengths often referenced in inches historically:
  - 25.5" = 647.7mm (Fender)
  - 24.75" = 628.65mm (Gibson)
  - 25" = 635mm (PRS)

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│                           (main.py)                              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │ Routers  │ │ Routers  │ │ Routers  │
             │ (HTTP)   │ │ (HTTP)   │ │ (HTTP)   │
             └────┬─────┘ └────┬─────┘ └────┬─────┘
                  │            │            │
                  ▼            ▼            ▼
             ┌──────────────────────────────────┐
             │          Calculators             │
             │   (Pure math, no HTTP concerns)  │
             └──────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ instrument │  │    rmos    │  │    cam     │
       │ _geometry  │  │            │  │            │
       │            │  │ (context,  │  │ (toolpath, │
       │ (fret_math │  │ feasibility│  │  g-code,   │
       │  profiles) │  │  scoring)  │  │  preview)  │
       └────────────┘  └────────────┘  └────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │     Schemas      │
                    │   (Pydantic)     │
                    │                  │
                    │ Request/Response │
                    │    validation    │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │     Output       │
                    │                  │
                    │  • DXF files     │
                    │  • G-code        │
                    │  • JSON/API      │
                    └──────────────────┘
```

### Data Flow Example: Fret Slot Export

```
1. HTTP Request
   POST /api/cam/fret_slots/export
   {"scale_length_mm": 648, "fret_count": 22, "post_processor": "GRBL"}
        │
        ▼
2. Router (cam_fret_slots_export_router.py)
   - Validates request via Pydantic schema
   - Calls calculator
        │
        ▼
3. Calculator (fret_slots_export.py)
   - Calls fret_math.compute_fret_positions_mm()
   - Builds slot geometry
   - Generates G-code for post-processor
        │
        ▼
4. Geometry (fret_math.py)
   - Pure math: 12th root of 2, iterative positioning
   - Returns list of distances from nut
        │
        ▼
5. Response
   {"gcode": "G21 G90...", "slot_count": 22, "estimated_time_min": 4.5}
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI** | Async, auto-docs, Pydantic integration |
| **Calculators separate from routers** | Testable without HTTP; reusable |
| **Try-except imports in main.py** | Allow partial startup if modules missing (debt!) |
| **ezdxf library** | Robust DXF R12→R2018 support |
| **Post-processor templates** | Same geometry, different G-code dialects |

---

## 4. Phase Progression (A → E)

The project uses a phased implementation approach. Each phase builds on the previous.

### Phase A: Core Geometry ✅ COMPLETE

**Goal:** Calculate fret positions mathematically.

**Key Files:**
- `instrument_geometry/neck/fret_math.py`
- `instrument_geometry/neck/neck_profiles.py`

**Outputs:**
- List of fret positions in mm
- Support for standard and multiscale

**Formula:**
```
position[n] = scale_length × (1 - (1 / 2^(n/12)))
```

---

### Phase B: DXF Export ✅ COMPLETE

**Goal:** Generate 2D CAD files for laser cutting.

**Key Files:**
- `calculators/fret_slots_cam.py` (export_dxf_r12)
- Uses `ezdxf` library

**Outputs:**
- DXF R12 format (universal compatibility)
- LINE and POLYLINE entities
- Layers for different cut types

---

### Phase C: G-code Generation ✅ COMPLETE

**Goal:** Generate CNC machine instructions.

**Key Files:**
- `calculators/fret_slots_cam.py` (generate_gcode)
- `calculators/fret_slots_export.py` (multi-post-processor)

**Outputs:**
- G-code for 8 post-processors
- Feed/speed calculations
- Time estimates

**Supported Controllers:**
- GRBL, Mach3, Mach4, LinuxCNC, PathPilot, MASSO, Fanuc, Haas

---

### Phase D: RMOS Feasibility ✅ COMPLETE

**Goal:** Validate designs against machine capabilities.

**Key Files:**
- `rmos/context.py` — Manufacturing context (material, tool, machine)
- `rmos/feasibility_fusion.py` — Scoring algorithm
- `rmos/feasibility_router.py` — API endpoints

**Outputs:**
- Feasibility score (0-100)
- Risk factors
- Optimization suggestions

**Example Checks:**
- "Is slot depth achievable with this tool length?"
- "Will feed rate cause burning in ebony?"
- "Does machine have enough Z travel?"

---

### Phase E: CAM Preview & Export 🔄 IN PROGRESS

**Goal:** Unified preview + export pipeline with UI integration.

**Key Files:**
- `cam/cam_preview_router.py` — Preview endpoint
- `routers/cam_fret_slots_export_router.py` — Export endpoint
- `schemas/cam_fret_slots.py` — Request/response models

**Outputs:**
- Combined feasibility + toolpath preview
- Multi-format export (G-code + DXF)
- Downloadable files

**New in Phase E:**
- `FanFretPoint` dataclass with `is_perpendicular` field
- Multi-post-processor batch export
- Material-aware feed rate recommendations

---

### Future Phases (Not Started)

| Phase | Goal | Status |
|-------|------|--------|
| **F** | Art Studio (rosettes, inlays) | Routers exist, no implementation |
| **G** | SQLite pattern persistence | Documented, not implemented |
| **H** | Real-time WebSocket updates | Router stubbed |
| **I** | AI-assisted optimization | Placeholder routers only |

---

## 5. Directory Structure

```
luthiers-toolbox-main/
├── services/
│   └── api/
│       └── app/
│           ├── main.py                 # FastAPI app, router registration
│           │
│           ├── routers/                # HTTP endpoint handlers
│           │   ├── cam_fret_slots_export_router.py  ✅
│           │   ├── health_router.py                  ✅
│           │   ├── geometry_router.py                ✅
│           │   ├── feeds_router.py                   ✅
│           │   └── ... (30 working, 81 phantom)
│           │
│           ├── calculators/            # Pure business logic
│           │   ├── fret_slots_cam.py               ✅ Phase C
│           │   ├── fret_slots_export.py            ✅ Phase E
│           │   └── ...
│           │
│           ├── schemas/                # Pydantic models
│           │   ├── cam_fret_slots.py               ✅
│           │   └── ...
│           │
│           ├── instrument_geometry/    # Guitar math
│           │   ├── neck/
│           │   │   ├── fret_math.py                ✅ Core
│           │   │   └── neck_profiles.py            ✅
│           │   └── body/
│           │       └── fretboard_geometry.py       ✅
│           │
│           ├── rmos/                   # Manufacturing optimization
│           │   ├── context.py                      ✅ Created
│           │   ├── context_router.py               ✅ Created
│           │   ├── feasibility_fusion.py           ✅
│           │   ├── feasibility_router.py           ✅
│           │   └── ...
│           │
│           ├── cam/                    # CAM-specific logic
│           │   └── cam_preview_router.py           ✅ Phase E
│           │
│           └── art_studio/             # ❌ PHANTOM (not implemented)
│               ├── bracing_router.py   ❌
│               ├── rosette_router.py   ❌
│               └── ...
│
├── scripts/
│   └── audit_phantom_imports.py        ✅ Cleanup tool
│
├── ARCHITECTURE_DRIFT_DIAGNOSTIC.md    ✅ Technical debt report
├── ARCHITECTURE_PATCH_SUMMARY.md       ✅ Patch notes
└── DEVELOPER_HANDOFF.md                ✅ This document
```

---

## 6. Key Files Reference

### Must-Understand Files

| File | Lines | Purpose | Complexity |
|------|-------|---------|------------|
| `main.py` | ~1200 | App bootstrap, router registration | High (debt) |
| `fret_math.py` | ~350 | Core fret position calculations | Medium |
| `fret_slots_cam.py` | ~450 | G-code generation, DXF export | Medium |
| `fret_slots_export.py` | ~220 | Multi-post-processor export | Low |
| `context.py` | ~180 | Manufacturing context model | Low |
| `feasibility_fusion.py` | ~400 | RMOS scoring algorithm | High |

### The Fret Math

The heart of the system is in `fret_math.py`:

```python
def compute_fret_positions_mm(scale_length_mm: float, fret_count: int) -> List[float]:
    """
    Equal temperament fret spacing.
    
    Each fret divides remaining scale by 2^(1/12) ≈ 1.05946
    
    Fret 12 is exactly halfway (octave).
    Fret 24 is 3/4 of scale length (two octaves).
    """
    positions = []
    for fret in range(1, fret_count + 1):
        # Distance from nut
        pos = scale_length_mm * (1.0 - (1.0 / (SEMITONE_RATIO ** fret)))
        positions.append(pos)
    return positions
```

### The Context Model

`context.py` bundles manufacturing parameters:

```python
@dataclass
class RmosContext:
    materials: MaterialSpec    # Wood properties (density, hardness)
    tool: ToolSpec            # Cutter properties (diameter, flutes)
    machine: MachineSpec      # CNC limits (RPM, feed, travel)
    cut_type: CutType         # FRET_SLOT, INLAY, ROSETTE, etc.
    
    def get_recommended_feed_mmpm(self) -> float:
        """Material-aware feed rate calculation."""
        base_feed = 1500.0
        return base_feed * self.materials.chip_load_factor
```

---

## 7. Current Technical Debt

### Critical: 73% Phantom Import Rate

**Problem:** `main.py` has 111 try-import blocks. 81 of them (73%) reference files that don't exist.

**Symptom:** The API starts, but 73% of documented endpoints return 404.

**Root Cause:**
```python
# This pattern HIDES missing files instead of failing:
try:
    from .missing_module import router
except Exception:
    router = None  # Silently swallowed!

if router:  # Never true
    app.include_router(router)
```

**Solution:** Run `python scripts/audit_phantom_imports.py --clean`

---

### High: Specification Drift

**Problem:** Documentation describes features that were never implemented.

**Examples:**
- `FanFretPoint.is_perpendicular` — documented but missing (NOW FIXED)
- Phase E export pipeline — documented but missing (NOW FIXED)
- SQLite pattern stores — documented in N11.2, never built
- Art Studio module — 6 routers referenced, none exist

**Solution:** Treat uploaded specs as "target state," not "current state."

---

### Medium: No Test Coverage

**Problem:** No `tests/` directory with meaningful tests.

**Impact:** Refactoring is dangerous; regressions undetected.

**Solution:** Add tests incrementally (see Section 9).

---

### Low: Inconsistent Post-Processor Support

**Problem:** Some endpoints support all 8 post-processors, others only GRBL.

**Solution:** Standardize on the `PostProcessor` enum from `schemas/cam_fret_slots.py`.

---

## 8. Environment Setup

### Prerequisites

```bash
Python 3.10+
pip or poetry
```

### Installation

```bash
# Clone repository
git clone https://github.com/HanzoRazer/luthiers-toolbox.git
cd luthiers-toolbox

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)

# Install dependencies
cd services/api
pip install -r requirements.txt
```

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.100+ | Web framework |
| `uvicorn` | 0.23+ | ASGI server |
| `pydantic` | 2.0+ | Data validation |
| `ezdxf` | 1.0+ | DXF file generation |
| `numpy` | 1.24+ | Numerical calculations |

### Running Locally

```bash
cd services/api
uvicorn app.main:app --reload --port 8000

# API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

### Running Tests

```bash
cd services/api
pytest app/tests/ -v
```

---

## 9. Testing Strategy

### Current State

Minimal test coverage. Most validation is manual via Swagger UI.

### Recommended Test Structure

```
services/api/app/tests/
├── test_fret_math.py           # Unit: core calculations
├── test_fret_slots_export.py   # Unit: G-code generation
├── test_context.py             # Unit: RMOS context
├── test_feasibility.py         # Unit: scoring algorithm
├── test_api_export.py          # Integration: export endpoints
└── test_api_preview.py         # Integration: preview endpoints
```

### Priority Test Cases

1. **Fret Math Accuracy**
   ```python
   def test_fret_12_is_half_scale():
       positions = compute_fret_positions_mm(648.0, 12)
       assert abs(positions[11] - 324.0) < 0.01  # 12th fret at midpoint
   ```

2. **Post-Processor Output**
   ```python
   def test_grbl_header():
       response = export_fret_slots(FretSlotExportRequest(
           scale_length_mm=648,
           post_processor=PostProcessor.GRBL
       ))
       assert "G21" in response.gcode  # Metric mode
       assert "G90" in response.gcode  # Absolute positioning
   ```

3. **Feasibility Edge Cases**
   ```python
   def test_impossible_depth_rejected():
       # 10mm depth with 5mm tool should fail
       score = evaluate_feasibility(depth=10, tool_length=5)
       assert score < 50  # Low feasibility
   ```

---

## 10. Prioritized Roadmap

### Immediate (This Week)

| Task | Impact | Effort |
|------|--------|--------|
| ✅ Fix `context.py` missing | Unblocks CAM preview | Done |
| ✅ Add `FanFretPoint.is_perpendicular` | Completes Wave 19 | Done |
| ✅ Implement Phase E export | Core feature | Done |
| Run phantom import cleanup | Reduces confusion | 5 min |
| Add basic test suite | Prevents regressions | 2 hrs |

### Short-Term (This Month)

| Task | Impact | Effort |
|------|--------|--------|
| SQLite pattern persistence | Save/load designs | 1 day |
| Art Studio rosette generator | Popular feature request | 2 days |
| WebSocket progress updates | Better UX for long jobs | 1 day |
| Compound radius in exports | Accuracy improvement | 4 hrs |

### Medium-Term (Next Quarter)

| Task | Impact | Effort |
|------|--------|--------|
| Full test coverage (>80%) | Maintainability | 1 week |
| Inlay pattern generator | Expands use cases | 1 week |
| Machine profile database | User convenience | 3 days |
| Documentation site | Onboarding | 1 week |

### Long-Term (Future)

| Task | Impact | Effort |
|------|--------|---------|
| AI toolpath optimization | Differentiation | Research |
| Cloud job queue | Scalability | 2 weeks |
| Desktop app (Electron) | Offline use | 1 month |

---

## 11. Common Tasks

### Add a New Post-Processor

1. Add enum value in `schemas/cam_fret_slots.py`:
   ```python
   class PostProcessor(str, Enum):
       ...
       NEWCONTROLLER = "NewController"
   ```

2. Add template in `calculators/fret_slots_export.py`:
   ```python
   POST_TEMPLATES[PostProcessor.NEWCONTROLLER] = PostTemplate(
       name="NewController",
       header="...",
       footer="...",
   )
   ```

### Add a New Endpoint

1. Create router in `routers/`:
   ```python
   router = APIRouter(prefix="/api/new", tags=["New Feature"])
   
   @router.get("/endpoint")
   async def my_endpoint():
       return {"status": "ok"}
   ```

2. Register in `main.py`:
   ```python
   try:
       from .routers.new_router import router as new_router
   except Exception as e:
       new_router = None
   
   if new_router:
       app.include_router(new_router)
   ```

### Add a New Material

Edit `rmos/context_router.py`:
```python
MATERIAL_PRESETS["cocobolo"] = MaterialSpec(
    material_id="cocobolo",
    name="Cocobolo",
    density_kg_m3=1100.0,
    hardness_janka=2960.0,
    chip_load_factor=0.65,
    heat_sensitivity=1.4,
)
```

### Generate G-code via API

```bash
curl -X POST http://localhost:8000/api/cam/fret_slots/export \
  -H "Content-Type: application/json" \
  -d '{
    "scale_length_mm": 648.0,
    "fret_count": 22,
    "nut_width_mm": 42.0,
    "heel_width_mm": 56.0,
    "slot_depth_mm": 3.0,
    "post_processor": "GRBL"
  }' | jq .gcode
```

---

## 12. Contacts & Resources

### Repository

- **GitHub:** https://github.com/HanzoRazer/luthiers-toolbox
- **Primary Branch:** `main`

### External Resources

| Resource | URL |
|----------|-----|
| FastAPI Docs | https://fastapi.tiangolo.com |
| ezdxf Library | https://ezdxf.readthedocs.io |
| Fret Calculator Theory | https://www.liutaiomottola.com/formulae/fret.htm |
| G-code Reference | https://linuxcnc.org/docs/html/gcode.html |

### Guitar Building References

| Topic | Resource |
|-------|----------|
| Scale Length Theory | *Guitar Making: Tradition and Technology* (Cumpiano & Natelson) |
| Fret Math | *The Art of Tap Tuning* (Mottola) |
| CNC for Luthiers | https://www.lmii.com/knowledge-base |

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-11 | Claude | Initial handoff document |
| 2025-12-11 | Claude | Added Phase E export, FanFretPoint, context.py |

---

*This document should be updated whenever significant architectural changes are made.*
