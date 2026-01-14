# CNC Saw Lab System Audit

**Version:** 1.0.0
**Date:** 2026-01-13
**Status:** ~75-80% Production-Ready

---

## Executive Summary

The CNC Saw Lab is a **substantially complete manufacturing subsystem** with robust safety validation, comprehensive RMOS integration, and excellent test coverage. The system provides blade management, safety calculations, G-code generation, telemetry ingestion, and learning-based parameter optimization. Core functionality is production-ready; remaining work focuses on UI polish and future path planning enhancements.

---

## 1. Architecture Overview

### Core Principle: Safety-First Manufacturing

The Saw Lab ensures that all cutting operations are:
- **Validated** via 5 safety calculators
- **Gated** via RMOS safety policy integration
- **Tracked** via immutable run artifacts
- **Optimized** via learning system feedback

```
┌─────────────────────────────────────────────────────────────────┐
│                      CNC Saw Lab Core                            │
├─────────────────────────────────────────────────────────────────┤
│  Blade Registry                                                  │
│  ├── CRUD Operations (7 endpoints)                               │
│  ├── PDF Import for bulk data                                    │
│  └── Validation per material                                     │
├─────────────────────────────────────────────────────────────────┤
│  Safety Calculators (5)                                          │
│  ├── Rim Speed (peripheral velocity)                             │
│  ├── Bite Load (chip per tooth)                                  │
│  ├── Heat Index (thermal risk)                                   │
│  ├── Deflection (depth vs diameter)                              │
│  └── Kickback (feed rate risk)                                   │
├─────────────────────────────────────────────────────────────────┤
│  G-Code Generation                                               │
│  ├── Multi-pass depth planning                                   │
│  ├── 3 operation types (slice, batch, contour)                   │
│  └── Feed rate conversion (IPM → mm/min)                         │
├─────────────────────────────────────────────────────────────────┤
│  RMOS Integration                                                │
│  ├── Safety Policy Gating                                        │
│  ├── CAM Guards (5 risk checks)                                  │
│  └── Decision Service (immutable history)                        │
├─────────────────────────────────────────────────────────────────┤
│  Learning System                                                 │
│  ├── Telemetry ingestion (3-factor risk)                         │
│  ├── Lane scale optimization                                     │
│  └── Automatic override application                              │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Separation

| Layer | Responsibility | NOT Responsible For |
|-------|----------------|---------------------|
| **Blade Registry** | Blade specs, validation, search | Cutting decisions |
| **Calculators** | Safety scoring, risk factors | Execution blocking |
| **G-Code Generator** | Toolpath emission, multi-pass | Safety decisions |
| **RMOS Integration** | Safety gating, decision history | Blade management |
| **Learning System** | Parameter optimization | Initial parameters |

---

## 2. Backend Structure

### Directory Layout

```
services/api/app/
├── saw_lab/                              # Core module (788 lines)
│   ├── __init__.py                       ✅ Module exports
│   ├── calculators/                      # 5 safety calculators
│   │   ├── saw_bite_load.py              ✅ 4,806 bytes
│   │   ├── saw_deflection.py             ✅ 4,027 bytes
│   │   ├── saw_heat.py                   ✅ 3,420 bytes
│   │   ├── saw_kickback.py               ✅ 5,233 bytes
│   │   └── saw_rimspeed.py               ✅ 4,619 bytes
│   └── saw_lab_toolpaths_from_decision_service.py  ✅ 142 lines
│
├── services/                             # Business logic (4,548 lines)
│   ├── saw_lab_service.py                ✅ Main facade
│   ├── saw_lab_decision_service.py       ✅ 208 lines
│   ├── saw_lab_batch_*.py                ✅ 10 batch workflow files
│   ├── saw_lab_execution_*.py            ✅ 4 execution files
│   ├── saw_lab_export_service.py         ✅ 169 lines
│   ├── saw_lab_gcode_emit_service.py     ✅ 222 lines
│   ├── saw_lab_learning_*.py             ✅ 4 learning files
│   ├── saw_lab_metrics_*.py              ✅ 4 metrics files
│   ├── saw_lab_compare_service.py        ✅ 272 lines
│   └── saw_lab_rollup_*.py               ✅ 3 rollup files
│
├── routers/                              # API routes (1,244 lines)
│   ├── saw_blade_router.py               ✅ 241 lines - CRUD
│   ├── saw_gcode_router.py               ✅ 132 lines - G-code
│   ├── saw_validate_router.py            ✅ 230 lines - Validation
│   ├── saw_telemetry_router.py           ✅ 498 lines - Telemetry
│   └── rmos_saw_ops_router.py            ✅ 143 lines - RMOS
│
├── cam_core/                             # CAM integration
│   ├── api/saw_lab_router.py             🟡 22 lines (placeholder)
│   ├── gcode/saw_gcode_generator.py      ✅ Comprehensive
│   └── saw_lab/                          # Blade registry (34KB)
│       ├── saw_blade_registry.py         ✅ 14,380 bytes
│       ├── saw_blade_validator.py        ✅ 20,062 bytes
│       ├── importers/
│       │   └── pdf_saw_blade_importer.py ✅ PDF parsing
│       ├── models.py                     ✅ Core models
│       ├── operations.py                 ✅ Operations
│       ├── queue.py                      ✅ Queue management
│       └── learning.py                   ✅ Learning integration
│
├── calculators/                          # Calculator adapters
│   ├── saw_bridge.py                     ✅ 4,948 bytes
│   └── saw/                              # RMOS adapters (18KB)
│       ├── bite_per_tooth_adapter.py     ✅ 2,570 bytes
│       ├── deflection_adapter.py         ✅ 3,898 bytes
│       ├── heat_adapter.py               ✅ 3,306 bytes
│       ├── kickback_adapter.py           ✅ 4,293 bytes
│       └── rim_speed_adapter.py          ✅ 2,731 bytes
│
├── rmos/                                 # RMOS integration
│   ├── policies/saw_safety_gate.py       ✅ 84 lines
│   ├── operations/saw_adapter.py         ✅ Adapter
│   └── saw_cam_guard.py                  ✅ 286 lines - 5 guards
│
├── cnc_production/schemas/
│   └── saw_lab_compat.py                 ✅ Compatibility layer
│
├── toolpath/
│   └── saw_engine.py                     ✅ Toolpath orchestration
│
└── _experimental/cnc_production/
    ├── joblog/saw_joblog_models.py       ✅ Job logging
    └── learn/saw_live_learn_dashboard.py ✅ Dashboard
```

**Total Backend: 11,289 lines across 103 files**

---

## 3. Component Status

### Tier 1: Production-Ready

| Component | Location | Features |
|-----------|----------|----------|
| **Blade Registry** | `cam_core/saw_lab/` | CRUD, validation, PDF import, search |
| **Rim Speed Calculator** | `calculators/saw_rimspeed.py` | Peripheral velocity, material limits |
| **Bite Load Calculator** | `calculators/saw_bite_load.py` | Chip per tooth, optimal ranges |
| **Heat Calculator** | `calculators/saw_heat.py` | Thermal risk, dust factor |
| **Deflection Calculator** | `calculators/saw_deflection.py` | Depth vs diameter ratio |
| **Kickback Calculator** | `calculators/saw_kickback.py` | Feed rate risk, cut type |
| **G-Code Generator** | `cam_core/gcode/` | Multi-pass, 3 operation types |
| **Safety Validation** | `routers/saw_validate_router.py` | 5 validation endpoints |
| **Telemetry System** | `routers/saw_telemetry_router.py` | 3-factor real-time risk |
| **RMOS Safety Gate** | `rmos/policies/saw_safety_gate.py` | Policy integration |
| **CAM Guards** | `rmos/saw_cam_guard.py` | 5 risk checks |
| **Learning System** | `services/saw_lab_learning_*.py` | Override application |
| **Batch Workflows** | `services/saw_lab_batch_*.py` | Decision, execution, metrics |

### Tier 2: Functional with Minor Gaps

| Component | Status | Gap |
|-----------|--------|-----|
| **Decision Service** | 95% | Minor edge cases |
| **Metrics Rollup** | 95% | History depth limits |
| **Export Service** | 90% | Format options |

### Tier 3: Placeholder/Skeleton

| Component | Status | Notes |
|-----------|--------|-------|
| **CAM Core Router** | Placeholder | 22 lines, needs delegation |
| **Path Planner 2.1** | Skeleton | Future optimization work |

---

## 4. Five Core Safety Calculators

### 4.1 Rim Speed Calculator

**File:** `saw_lab/calculators/saw_rimspeed.py` (4,619 bytes)

**Formula:**
```
rim_speed_m/s = π × D(mm) × RPM / 60000
```

**Material-Specific Limits (Carbide-Tipped):**

| Material | Optimal Range | Warning | Critical |
|----------|---------------|---------|----------|
| Hardwood | 40-70 m/s | >70 m/s | >85 m/s |
| Softwood | 50-80 m/s | >80 m/s | >95 m/s |
| Aluminum | 20-40 m/s | >40 m/s | >50 m/s |
| Acrylic | 30-60 m/s | >60 m/s | >75 m/s |

**Scoring:**
- 100: Optimal range
- 80: Below optimal (too slow)
- 70: Upper limit warning
- 40: Exceeds safe range
- 10: Critically high

### 4.2 Bite Load Calculator

**File:** `saw_lab/calculators/saw_bite_load.py` (4,806 bytes)

**Formula:**
```
bite_load_mm = feed_rate_mm_min / (RPM × tooth_count)
```

**Optimal Ranges by Material:**

| Material | Min | Optimal | Max |
|----------|-----|---------|-----|
| Softwood | 0.05 | 0.08-0.12 | 0.15 mm/tooth |
| Hardwood | 0.03 | 0.05-0.08 | 0.10 mm/tooth |
| Plywood | 0.03 | 0.04-0.06 | 0.08 mm/tooth |
| MDF | 0.05 | 0.07-0.10 | 0.12 mm/tooth |

**Risk Factors:**
- Too low: Rubbing, heat buildup, premature dulling
- Too high: Chip overload, rough cut, kickback risk

### 4.3 Heat Index Calculator

**File:** `saw_lab/calculators/saw_heat.py` (3,420 bytes)

**Formula:**
```
heat_index = 100 × speed_factor × feed_factor × dust_factor
```

**Component Factors:**

| Factor | Low Risk | Medium | High Risk |
|--------|----------|--------|-----------|
| Rim Speed | 40-60 m/s | 60-75 m/s | >75 m/s |
| Feed Rate | Optimal bite | ±20% | ±40%+ |
| Dust Collection | Active | Partial | None |

**Thresholds:**
- Cut length >500mm: Heat warning
- Heat index >80: Cooling pause recommended
- Heat index >95: Stop and inspect blade

### 4.4 Deflection Calculator

**File:** `saw_lab/calculators/saw_deflection.py` (4,027 bytes)

**Rule of Thumb:**
```
max_safe_depth = 40% × blade_diameter
```

**Risk Factors:**

| Factor | Calculation | Threshold |
|--------|-------------|-----------|
| Depth Ratio | cut_depth / blade_diameter | >40% = warning |
| Kerf Ratio | blade_diameter / kerf | <50 = thin blade risk |
| Overhang | arbor_to_cut / blade_diameter | >60% = deflection risk |

**Scoring:**
- 100: Safe depth ratio
- 70: Approaching limit
- 40: Exceeds safe ratio
- 10: Critical deflection risk

### 4.5 Kickback Calculator

**File:** `saw_lab/calculators/saw_kickback.py` (5,233 bytes)

**Risk Factors (Weighted):**

| Factor | Weight | High Risk Condition |
|--------|--------|---------------------|
| Cut Type | 25% | Rip cuts highest |
| Blade Exposure | 20% | >2" above stock |
| Feed Rate | 20% | Too fast OR too slow |
| Bevel Angle | 15% | >30 degrees |
| Stock Thickness | 10% | <0.5" thin stock |
| Material Density | 10% | Hardwood, knotty wood |

**Risk Levels:**
- GREEN: Score ≥80, normal operation
- YELLOW: Score 50-79, caution advised
- RED: Score <50, operation blocked

---

## 5. API Endpoints

### Blade Registry (`/api/saw/blades`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/` | POST | ✅ | Create blade with auto-ID |
| `/` | GET | ✅ | List all blades |
| `/{blade_id}` | GET | ✅ | Get single blade |
| `/{blade_id}` | PUT | ✅ | Update blade fields |
| `/{blade_id}` | DELETE | ✅ | Soft delete blade |
| `/search` | POST | ✅ | Search with filters |
| `/stats` | GET | ✅ | Registry statistics |

### G-Code Generation (`/api/saw_gcode`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/generate` | POST | ✅ | Multi-pass G-code generation |

**Features:**
- 3 operation types: slice, batch, contour
- Multi-pass depth control (DOC per pass)
- Feed rate conversion (IPM → mm/min)
- Safe entry/exit moves
- Path length and depth statistics

### Safety Validation (`/api/saw/validate`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/operation` | POST | ✅ | Full operation validation |
| `/contour` | POST | ✅ | Radius-only validation |
| `/doc` | POST | ✅ | Depth of cut validation |
| `/feeds` | POST | ✅ | RPM/feed validation |
| `/limits` | GET | ✅ | Get safety limits |

### Telemetry (`/api/saw/telemetry`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/ingest` | POST | ✅ | Live risk scoring |
| `/runs` | GET | ✅ | List run records |
| `/runs` | POST | ✅ | Create run record |
| `/runs/{id}` | PUT | ✅ | Update run status |

**Risk Scoring Model:**
```
risk_score = (spindle_load × 0.40) + (vibration × 0.30) + (sound × 0.30)
```

### RMOS Integration (`/api/rmos/saw-ops`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/slice/preview` | POST | ✅ | Slice preview with geometry |
| `/pipeline/handoff` | POST | ✅ | Pattern handoff to CAM |

**Total: 21 endpoints, ~95% functional**

---

## 6. RMOS Integration

### Safety Policy Gate

**File:** `rmos/policies/saw_safety_gate.py` (84 lines)

**Features:**
- Normalizes saw-specific field names (risk_bucket → risk_level)
- Integrates with SafetyPolicy framework
- Returns SafetyDecision with risk levels
- Blocks execution for RED/UNKNOWN risk levels

**Decision Flow:**
```
SawOperation → 5 Calculators → Risk Scores → Safety Gate → Allow/Block
```

### CAM Guard System

**File:** `rmos/saw_cam_guard.py` (286 lines)

**Integrated Guards:**

| Guard | Check | Threshold |
|-------|-------|-----------|
| Rim Speed | Peripheral velocity | 4,000-5,000 m/min max |
| Bite Per Tooth | Chip load | 0.01-0.25mm range |
| Heat Buildup | Cut length risk | 500mm threshold |
| Deflection | Depth/diameter ratio | 40% limit |
| Kickback | Feed rate risk | 5,000 mm/min, material-dependent |

**Risk Result Format:**
```python
RiskResult(
    value: float,           # Calculated value
    message: RmosMessage    # WARNING/ERROR/INFO
)
```

### Decision Service

**File:** `services/saw_lab_decision_service.py` (208 lines)

**Features:**
- Creates decision artifacts
- Records operator approval
- Integrates with runs_v2 store
- Immutable run history
- Forensic preservation (even validation failures)

---

## 7. Learning System

### Architecture

```
Telemetry → Risk Scoring → Lane Scale Delta → Override Application
    │            │               │                    │
  Live       3-factor         ±0.05/-0.10         Automatic
  Data       weighted          updates              when enabled
```

### Service Files

| Service | Lines | Purpose |
|---------|-------|---------|
| `saw_lab_learning_hook_config.py` | 161 | Hook configuration |
| `saw_lab_operator_feedback_learning_hook.py` | 161 | Feedback ingestion |
| `saw_lab_learning_apply_service.py` | 141 | Apply learned overrides |
| `saw_lab_learned_overrides_resolver.py` | 161 | Override resolution |

### Lane Scale Dynamics

| Condition | Delta | Effect |
|-----------|-------|--------|
| Successful cut, low risk | +0.05 | Increase confidence |
| Successful cut, medium risk | +0.02 | Slight increase |
| Warning triggered | -0.05 | Reduce confidence |
| Failure/abort | -0.10 | Significant reduction |

### Enablement

```python
# Environment flag
SAW_LAB_APPLY_ACCEPTED_OVERRIDES=true  # Enable auto-application
```

---

## 8. Frontend Components

### Vue Components

| Component | Lines | Status | Functionality |
|-----------|-------|--------|---------------|
| SawBatchPanel.vue | 814 | ✅ Working | Batch operation planning |
| SawContourPanel.vue | 1,014 | ✅ Working | Contour path planning |
| SawSlicePanel.vue | 775 | ✅ Working | Slice operation setup |
| SawLabShell.vue | 22 | ✅ Working | Container/routing |
| SawLabDiffPanel.vue | 16 | ⚠️ Stub | Diff visualization |
| SawLabQueuePanel.vue | 16 | ⚠️ Stub | Queue management |

**Total Frontend: 2,657 lines**

### API Client

**File:** `client/src/api/sawLab.ts` (317 lines)

| Feature | Status |
|---------|--------|
| Blade CRUD | ✅ Complete |
| Validation calls | ✅ Complete |
| G-code generation | ✅ Complete |
| Telemetry ingestion | ✅ Complete |
| Risk/dashboard types | ✅ Complete |
| JobLog types | ✅ Complete |

---

## 9. Test Coverage

### Test Statistics

- **132 test files**
- **11,030 lines of test code**
- **Excellent coverage for core functionality**

### Test Categories

| Category | Files | Status |
|----------|-------|--------|
| Safety Gate | 1 | ✅ 52 lines |
| Calculator Adapters | 1 | ✅ Complete |
| Bridge Integration | 1 | ✅ Complete |
| Batch Workflows | 20+ | ✅ Comprehensive |
| Execution Flow | 4+ | ✅ Well-tested |
| Learning System | 4+ | ✅ Enable/disable tested |
| Rollup Mechanics | 3+ | ✅ Tested |
| Metrics | 4+ | ✅ Tested |

### Key Test Files

```
services/api/tests/
├── rmos/test_saw_safety_gate.py           # 52 lines
├── calculators/test_saw_adapters.py       # Adapter testing
├── test_saw_bridge_profiles_integration.py # Integration
├── test_saw_batch_*.py                    # 10+ batch tests
├── test_saw_execution_*.py                # 4+ execution tests
├── test_saw_learning_*.py                 # 4+ learning tests
├── test_saw_rollup_*.py                   # 3+ rollup tests
└── test_saw_metrics_*.py                  # 4+ metrics tests
```

---

## 10. Data Models

### Core Models

```python
class SawContext:
    kerf: float              # Blade kerf width
    stock_thickness: float   # Material thickness
    feed_rate: float         # Feed rate mm/min
    rpm: int                 # Spindle speed

class SawDesign:
    operation_type: str      # slice, batch, contour
    cut_depth: float         # Depth of cut
    passes: int              # Number of passes
    geometry: List[Point]    # Cut path

class SawCalculatorResult:
    score: int               # 0-100
    risk_bucket: str         # GREEN/YELLOW/RED
    warnings: List[str]      # Warning messages
    metadata: Dict           # Calculator-specific

class SawBladeSpec:
    blade_id: str
    vendor: str
    model: str
    diameter_mm: float
    kerf_mm: float
    tooth_count: int
    tooth_geometry: str
    materials: List[str]     # Supported materials
```

### Compatibility Layer

**File:** `cnc_production/schemas/saw_lab_compat.py`

```python
class SawRunCompat:
    """Handles legacy and canonical run formats"""
    run_id: str
    meta: SawRunMetaCompat
    samples: List[TelemetrySampleCompat]
```

---

## 11. Identified Gaps

### Gap 1: Frontend Stubs

**Issue:** SawLabDiffPanel and SawLabQueuePanel are 16-line stubs
**Impact:** No diff visualization or queue management UI
**Effort:** 25 hours
**Priority:** LOW

### Gap 2: CAM Core Router

**Issue:** `cam_core/api/saw_lab_router.py` is 22-line placeholder
**Impact:** Should delegate to saw_lab_service facade
**Effort:** 15 hours
**Priority:** MEDIUM

### Gap 3: Path Planner 2.1

**Issue:** Current path planner is skeleton with fallback segmentation
**Impact:** No advanced path optimization
**Effort:** 40 hours (future work)
**Priority:** FUTURE

### Gap 4: Documentation

**Issue:** Missing operator guide and troubleshooting docs
**Impact:** Onboarding friction
**Effort:** 15 hours
**Priority:** LOW

### Gap 5: Edge Cases

**Issue:** PDF importer error handling, complex contour validation
**Impact:** Robustness for unusual inputs
**Effort:** 20 hours
**Priority:** VERY LOW

---

## 12. Path to Full Completion

### Phase 1: To 90% (~75 hours)

| Task | Hours | Priority |
|------|-------|----------|
| Frontend stubs (DiffPanel, QueuePanel) | 25 | LOW |
| CAM core router implementation | 15 | MEDIUM |
| Documentation (operator guide) | 15 | LOW |
| Edge case handling | 20 | VERY LOW |

### Phase 2: To 95% (~120 hours)

| Task | Hours | Priority |
|------|-------|----------|
| Above items | 75 | |
| Telemetry anomaly handling | 20 | LOW |
| Advanced path planning | 15 | LOW |
| Performance optimization | 10 | LOW |

### Phase 3: To 98% (~185 hours)

| Task | Hours | Priority |
|------|-------|----------|
| Above items | 120 | |
| Path Planner 2.1 (future) | 40 | FUTURE |
| Advanced blade selection UI | 15 | LOW |
| Performance tuning | 10 | LOW |

---

## 13. Summary

**The CNC Saw Lab is 75-80% production-ready with excellent core functionality.**

### What Works

- ✅ Complete blade registry with CRUD, validation, PDF import
- ✅ Five robust safety calculators (rim speed, bite, heat, deflection, kickback)
- ✅ Multi-pass G-code generation with 3 operation types
- ✅ Full RMOS safety policy integration with 5 CAM guards
- ✅ Real-time telemetry with 3-factor risk scoring
- ✅ Learning system with automatic override application
- ✅ Comprehensive batch workflow support
- ✅ Excellent test coverage (11,030 lines, 132 files)
- ✅ Production-ready frontend for batch, contour, and slice operations

### What's Missing

- ⚠️ Frontend stubs (DiffPanel, QueuePanel)
- ⚠️ CAM core router delegation
- ⚠️ Path Planner 2.1 (future optimization)
- ⚠️ Operator documentation

### Comparison to Other Systems

| Aspect | Saw Lab | Blueprint | Art Studio | RMOS | CAM |
|--------|---------|-----------|------------|------|-----|
| Core Algorithms | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete | ✅ Complete |
| API Endpoints | ✅ 95% | ✅ 93% | ✅ 90% | ✅ 95% | ⚠️ 65% |
| Test Coverage | ✅ Excellent | ⚠️ Partial | ✅ Good | ⚠️ 20% | ⚠️ Gaps |
| RMOS Integration | ✅ Complete | ⚠️ Planned | ✅ Complete | N/A | ⚠️ Stubs |
| Hours to MVP | ~75h | ~24h | ~30h | ~48h | ~50h |

**The Saw Lab is mature and production-ready for operator use. It represents one of the most complete subsystems in the repository, with the strongest test coverage and safety infrastructure.**

---

*Document generated as part of luthiers-toolbox system audit.*
