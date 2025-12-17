# Bidirectional Workflow System Analysis Report

**Repository:** Luthier's ToolBox
**Analysis Date:** December 15, 2025
**Document Type:** Technical Architecture Analysis with Recommendations

---

## Executive Summary

The Luthier's ToolBox implements a sophisticated **bidirectional workflow architecture** that enables data and control flow in both directions between design tools (Art Studio) and manufacturing systems (RMOS/CAM). This architecture represents a significant departure from traditional unidirectional CAM systems and provides unique capabilities for guitar luthiers.

### Key Findings

1. **Three-Mode Workflow System**: The system supports Design-First, Constraint-First, and AI-Assisted workflows
2. **Central RMOS Oracle**: All workflows funnel through the RMOS feasibility scoring system
3. **90+ API Routers**: Extensive but fragmented router ecosystem with dependency issues
4. **5-Domain Architecture**: Creative, CAM, Manufacturing Planning, Production Logging, and Future Engineering layers
5. **Risk-Graded Safety**: GREEN/YELLOW/RED classification system for manufacturing safety

### Critical Recommendation

**Consolidate the bidirectional flow into a unified state machine** with clear entry/exit points. The current architecture has the right concepts but suffers from fragmentation across too many router files.

---

## Part 1: System Architecture Breakdown

### 1.1 The Bidirectional Flow Model

```
                    BIDIRECTIONAL DATA FLOW

    +-----------------+                 +------------------+
    |                 |    Design       |                  |
    |   ART STUDIO    | ───────────────>|      RMOS        |
    |   (Creative)    |                 |  (Manufacturing  |
    |                 | <───────────────|     Oracle)      |
    |                 |   Constraints   |                  |
    +-----------------+                 +------------------+
            |                                   |
            |                                   |
            v                                   v
    +-----------------+                 +------------------+
    |                 |                 |                  |
    |   CAM ENGINE    |<----------------|    SAW LAB       |
    | (G-code/paths)  |  Toolpath Req   |  (Execution)     |
    |                 |                 |                  |
    +-----------------+                 +------------------+
```

### 1.2 Three Directional Workflow Modes

| Mode | Driver | Entry Point | RMOS Role | Best For |
|------|--------|-------------|-----------|----------|
| **Design-First** | Artist | Art Studio UI | Post-design validation | Creative exploration |
| **Constraint-First** | Operator | RMOS Constraints Panel | Pre-design filtering | Production workflows |
| **AI-Assisted** | AI Generator | Natural language prompt | Filter + rank candidates | Parameter optimization |

### 1.3 File Structure Reference

```
services/api/app/
├── workflow/
│   ├── __init__.py
│   └── directional_workflow.py      # Core workflow modes
│
├── rmos/                             # Manufacturing Oracle
│   ├── api_contracts.py             # Core types (RiskBucket, RmosContext)
│   ├── api_ai_routes.py             # AI search endpoints
│   ├── api_constraint_profiles.py   # Constraint management
│   ├── api_profile_history.py       # Profile versioning
│   ├── feasibility_scorer.py        # Score computation
│   ├── context_router.py            # Context management
│   └── api/
│       ├── constraint_search_routes.py
│       └── log_routes.py
│
├── routers/                          # 90+ API routers
│   ├── art_studio_rosette_router.py # Art Studio integration
│   ├── rmos_patterns_router.py      # Pattern management
│   ├── rmos_saw_ops_router.py       # Saw operations
│   ├── cam_*.py                     # CAM subsystem (15+ files)
│   ├── blueprint_*.py               # Blueprint system
│   └── ...
│
├── art_studio/
│   └── rosette_router.py            # Creative layer API
│
├── cam_core/
│   └── api/
│       └── saw_lab_router.py        # Saw execution
│
└── main.py                          # Router registration (33 active)
```

---

## Part 2: Annotated Schema Diagrams

### 2.1 Core Data Contracts

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        RMOS API CONTRACTS                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐        ┌─────────────────────┐                │
│  │   RmosContext       │        │  RosetteParamSpec   │                │
│  ├─────────────────────┤        ├─────────────────────┤                │
│  │ material_id: str?   │        │ outer_diameter_mm   │                │
│  │ tool_id: str?       │◄──────►│ inner_diameter_mm   │                │
│  │ machine_profile_id  │        │ ring_count: int     │                │
│  │ use_shapely: bool   │        │ pattern_type: str   │                │
│  └─────────────────────┘        └─────────────────────┘                │
│            │                              │                             │
│            │                              │                             │
│            ▼                              ▼                             │
│  ┌─────────────────────────────────────────────────────┐               │
│  │        compute_feasibility_for_design()             │               │
│  │        ═══════════════════════════════════          │               │
│  │  INPUT:  design (RosetteParamSpec)                  │               │
│  │          ctx (RmosContext)                          │               │
│  │  OUTPUT: RmosFeasibilityResult                      │               │
│  └─────────────────────────────────────────────────────┘               │
│                          │                                              │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────┐               │
│  │     RmosFeasibilityResult                           │               │
│  ├─────────────────────────────────────────────────────┤               │
│  │ score: float (0-100)       # Overall feasibility    │               │
│  │ risk_bucket: RiskBucket    # GREEN/YELLOW/RED       │               │
│  │ warnings: List[str]        # Manufacturing warnings │               │
│  │ efficiency: float?         # Material efficiency %  │               │
│  │ estimated_cut_time_seconds # Machining time         │               │
│  │ calculator_results: Dict   # Individual calc output │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Directional Workflow Schema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DIRECTIONAL WORKFLOW TYPES                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  enum DirectionalMode:                                                  │
│    ├── design_first      # Artist-driven, post-validation              │
│    ├── constraint_first  # Manufacturing-driven, pre-filtering         │
│    └── ai_assisted       # AI-driven, feedback loop                    │
│                                                                         │
│  ┌─────────────────────┐        ┌─────────────────────┐                │
│  │  ModePreviewRequest │        │  ModePreviewResult  │                │
│  ├─────────────────────┤        ├─────────────────────┤                │
│  │ mode: DirectionalMode│───────►│ mode               │                │
│  │ tool_id: str?       │        │ constraints         │                │
│  │ material_id: str?   │        │ feasibility_score?  │                │
│  │ machine_profile: str?│        │ risk_level?        │                │
│  │ goal_speed: float   │        │ warnings: List[str] │                │
│  │ goal_quality: float │        │ recommendations:    │                │
│  │ goal_tool_life: float│        │   List[str]        │                │
│  └─────────────────────┘        └─────────────────────┘                │
│                                                                         │
│  ┌─────────────────────────────────────────────────────┐               │
│  │            ModeConstraints                          │               │
│  ├─────────────────────────────────────────────────────┤               │
│  │ mode: DirectionalMode                               │               │
│  │ hard_limits: Dict[str, Any]  # Cannot be exceeded   │               │
│  │   └── max_rpm, max_feed_mm_min, max_stepover_pct   │               │
│  │ soft_limits: Dict[str, Any]  # Warning thresholds   │               │
│  │   └── recommended_rpm, recommended_feed_mm_min     │               │
│  │ suggestions: List[str]       # UI guidance text     │               │
│  └─────────────────────────────────────────────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Risk Classification System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     RISK BUCKET CLASSIFICATION                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Score Range        Risk Bucket       Action                           │
│   ───────────        ───────────       ──────                           │
│   80-100             🟢 GREEN          Safe to proceed                  │
│   60-79              🟡 YELLOW         Review parameters                │
│   0-59               🔴 RED            Requires modification            │
│                                                                         │
│   Risk Factors Evaluated:                                               │
│   ┌────────────────────────────────────────────────────────┐           │
│   │ 1. Rim Speed       - RPM limits for outer ring radius  │           │
│   │ 2. Gantry Span     - Machine reach constraints         │           │
│   │ 3. Deflection      - Thin blade + long cut physics     │           │
│   │ 4. Kerf Ratio      - Blade width vs strip width        │           │
│   │ 5. Heat Generation - Feed rate vs material hardness    │           │
│   │ 6. Chipload        - Feed per tooth calculations       │           │
│   └────────────────────────────────────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Data Flow Sequences

### 3.1 Design-First Flow (Artist Mode)

```
SEQUENCE: Design-First Workflow

┌─────────┐     ┌────────────────┐     ┌──────────────┐     ┌─────────┐
│  User   │     │   Art Studio   │     │     RMOS     │     │   CAM   │
└────┬────┘     └───────┬────────┘     └──────┬───────┘     └────┬────┘
     │                  │                     │                   │
     │ 1. Create Design │                     │                   │
     │─────────────────>│                     │                   │
     │                  │                     │                   │
     │                  │ 2. Call feasibility │                   │
     │                  │────────────────────>│                   │
     │                  │                     │                   │
     │                  │ 3. Return score     │                   │
     │                  │<────────────────────│                   │
     │                  │    + risk_bucket    │                   │
     │                  │    + warnings       │                   │
     │                  │                     │                   │
     │ 4. Show results  │                     │                   │
     │<─────────────────│                     │                   │
     │   (adjust if RED)│                     │                   │
     │                  │                     │                   │
     │ 5. Approve       │                     │                   │
     │─────────────────>│                     │                   │
     │                  │ 6. Generate toolpaths                   │
     │                  │────────────────────────────────────────>│
     │                  │                     │                   │
     │                  │                     │ 7. Return G-code  │
     │                  │<────────────────────────────────────────│
     │                  │                     │                   │
     │ 8. Export        │                     │                   │
     │<─────────────────│                     │                   │
     │                  │                     │                   │
```

### 3.2 Constraint-First Flow (Production Mode)

```
SEQUENCE: Constraint-First Workflow

┌──────────┐    ┌──────────────┐    ┌────────────────┐    ┌───────────┐
│ Operator │    │     RMOS     │    │   Art Studio   │    │    CAM    │
└────┬─────┘    └──────┬───────┘    └───────┬────────┘    └─────┬─────┘
     │                 │                    │                   │
     │ 1. Set constraints                   │                   │
     │────────────────>│                    │                   │
     │   (material,    │                    │                   │
     │    tool, limits)│                    │                   │
     │                 │                    │                   │
     │                 │ 2. Generate candidates                 │
     │                 │───────────────────>│                   │
     │                 │                    │                   │
     │                 │ 3. Return valid designs                │
     │                 │<───────────────────│                   │
     │                 │   (filtered by     │                   │
     │                 │    constraints)    │                   │
     │                 │                    │                   │
     │ 4. Present options                   │                   │
     │<────────────────│                    │                   │
     │                 │                    │                   │
     │ 5. Select design│                    │                   │
     │────────────────>│                    │                   │
     │                 │                    │                   │
     │                 │ 6. Generate toolpaths                  │
     │                 │───────────────────────────────────────>│
     │                 │                    │                   │
     │ 7. Execute      │                    │    8. Return code │
     │<────────────────────────────────────────────────────────│
     │                 │                    │                   │
```

### 3.3 AI-Assisted Flow (Generative Mode)

```
SEQUENCE: AI-Assisted Workflow

┌──────┐   ┌────────────┐   ┌──────────────┐   ┌────────────┐   ┌───────┐
│ User │   │  AI Engine │   │     RMOS     │   │ Art Studio │   │  CAM  │
└──┬───┘   └─────┬──────┘   └──────┬───────┘   └─────┬──────┘   └───┬───┘
   │             │                 │                 │               │
   │ 1. Prompt   │                 │                 │               │
   │────────────>│                 │                 │               │
   │ "Spanish    │                 │                 │               │
   │  style..."  │                 │                 │               │
   │             │                 │                 │               │
   │             │ 2. Generate 6 candidates         │               │
   │             │────────────────>│                 │               │
   │             │                 │                 │               │
   │             │                 │ 3. Score each   │               │
   │             │                 │    candidate    │               │
   │             │                 │                 │               │
   │             │ 4. Return ranked list            │               │
   │             │<────────────────│                 │               │
   │             │   (filter RED,  │                 │               │
   │             │    sort by score)                │               │
   │             │                 │                 │               │
   │ 5. Present sorted options     │                 │               │
   │<────────────│                 │                 │               │
   │  #1: 92 GREEN                 │                 │               │
   │  #2: 84 YELLOW                │                 │               │
   │  #3: 71 GREEN                 │                 │               │
   │             │                 │                 │               │
   │ 6. Select   │                 │                 │               │
   │────────────>│                 │                 │               │
   │             │                 │                 │               │
   │             │ 7. To Art Studio for tweaks      │               │
   │             │─────────────────────────────────>│               │
   │             │                 │                 │               │
   │             │                 │  8. Generate toolpaths         │
   │             │                 │─────────────────────────────────>│
   │             │                 │                 │               │
```

---

## Part 4: Current Implementation Status

### 4.1 Working Components

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| `directional_workflow.py` | `services/api/app/workflow/` | **COMPLETE** | Three modes implemented |
| `api_contracts.py` | `services/api/app/rmos/` | **COMPLETE** | Core types defined |
| `api_ai_routes.py` | `services/api/app/rmos/` | **COMPLETE** | AI search endpoints |
| `api_constraint_profiles.py` | `services/api/app/rmos/` | **COMPLETE** | Profile management |
| Risk scoring | Multiple files | **COMPLETE** | GREEN/YELLOW/RED system |

### 4.2 Broken/Missing Components

| Component | Issue | Fix Required |
|-----------|-------|--------------|
| `feasibility_router.py` | Missing `rmos.context` module | Create context module |
| `cam_preview_router.py` | Missing `rmos.context` module | Create context module |
| `pipeline_router.py` | Missing `httpx` dependency | Install httpx |
| `blueprint_router.py` | Missing `analyzer` module | Create analyzer |
| `saw_blade_router.py` | Missing `cam_core` | Fix cam_core imports |

### 4.3 Router Fragmentation Analysis

```
ROUTER COUNT BY CATEGORY:
├── CAM Routers:         15 files  (cam_*.py)
├── RMOS Routers:         4 files  (rmos_*.py, api_*.py)
├── Blueprint Routers:    2 files  (blueprint_*.py)
├── Saw Lab Routers:      5 files  (saw_*.py)
├── Compare Routers:      4 files  (compare_*.py)
├── Generator Routers:    2 files  (body/neck_generator_router.py)
├── Other Routers:       58+ files
└── TOTAL:              ~90 router files

REGISTERED IN main.py:   33 routers (37%)
BROKEN/COMMENTED:         9 routers (10%)
ORPHANED:               ~48 routers (53%)
```

---

## Part 5: Recommendations for a More Robust System

### 5.1 Immediate Fixes (Week 1)

#### R1: Create Missing Context Module
```python
# services/api/app/rmos/context.py
from .api_contracts import RmosContext, RmosServices

def get_default_context() -> RmosContext:
    return RmosContext(
        material_id="default",
        tool_id="default",
        use_shapely_geometry=True
    )
```

#### R2: Fix Broken Imports
```bash
# Install missing dependency
pip install httpx

# Fix cam_core circular imports
# Move shared types to api_contracts.py
```

### 5.2 Short-Term Improvements (Weeks 2-4)

#### R3: Router Consolidation Strategy

**Merge related routers into domain modules:**

```
BEFORE (fragmented):
├── cam_adaptive_benchmark_router.py
├── cam_biarc_router.py
├── cam_compare_diff_router.py
├── cam_drill_pattern_router.py
├── cam_drill_router.py
├── cam_dxf_adaptive_router.py
├── cam_fret_slots_export_router.py
├── cam_fret_slots_router.py
├── cam_helical_v161_router.py
├── cam_learn_router.py
├── cam_logs_router.py
├── cam_metrics_router.py
├── cam_opt_router.py
├── cam_pipeline_preset_run_router.py
├── cam_pipeline_router.py
└── ... (15 more)

AFTER (consolidated):
├── cam/
│   ├── __init__.py
│   ├── core_router.py       # Merged: opt, logs, metrics, learn
│   ├── toolpath_router.py   # Merged: adaptive, biarc, helical
│   ├── drilling_router.py   # Merged: drill, drill_pattern
│   ├── export_router.py     # Merged: fret_slots_export, compare_diff
│   └── pipeline_router.py   # Merged: pipeline, preset_run
```

#### R4: Implement State Machine for Workflows

```python
# services/api/app/workflow/state_machine.py
from enum import Enum, auto
from typing import Optional
from pydantic import BaseModel

class WorkflowState(str, Enum):
    IDLE = "idle"
    DESIGNING = "designing"
    VALIDATING = "validating"
    CONSTRAINED = "constrained"
    AI_GENERATING = "ai_generating"
    AI_SELECTING = "ai_selecting"
    APPROVED = "approved"
    GENERATING_TOOLPATHS = "generating_toolpaths"
    READY_FOR_CAM = "ready_for_cam"
    EXECUTING = "executing"
    COMPLETE = "complete"
    ERROR = "error"

class WorkflowTransition(BaseModel):
    from_state: WorkflowState
    to_state: WorkflowState
    trigger: str
    guard: Optional[str] = None

# Define valid transitions
TRANSITIONS = [
    WorkflowTransition(from_state=WorkflowState.IDLE, to_state=WorkflowState.DESIGNING, trigger="start_design"),
    WorkflowTransition(from_state=WorkflowState.IDLE, to_state=WorkflowState.CONSTRAINED, trigger="set_constraints"),
    WorkflowTransition(from_state=WorkflowState.IDLE, to_state=WorkflowState.AI_GENERATING, trigger="ai_prompt"),
    WorkflowTransition(from_state=WorkflowState.DESIGNING, to_state=WorkflowState.VALIDATING, trigger="validate"),
    WorkflowTransition(from_state=WorkflowState.VALIDATING, to_state=WorkflowState.DESIGNING, trigger="adjust", guard="risk_bucket != GREEN"),
    WorkflowTransition(from_state=WorkflowState.VALIDATING, to_state=WorkflowState.APPROVED, trigger="approve", guard="risk_bucket != RED"),
    WorkflowTransition(from_state=WorkflowState.CONSTRAINED, to_state=WorkflowState.DESIGNING, trigger="select_design"),
    WorkflowTransition(from_state=WorkflowState.AI_GENERATING, to_state=WorkflowState.AI_SELECTING, trigger="candidates_ready"),
    WorkflowTransition(from_state=WorkflowState.AI_SELECTING, to_state=WorkflowState.DESIGNING, trigger="select_candidate"),
    WorkflowTransition(from_state=WorkflowState.APPROVED, to_state=WorkflowState.GENERATING_TOOLPATHS, trigger="generate"),
    WorkflowTransition(from_state=WorkflowState.GENERATING_TOOLPATHS, to_state=WorkflowState.READY_FOR_CAM, trigger="toolpaths_ready"),
    WorkflowTransition(from_state=WorkflowState.READY_FOR_CAM, to_state=WorkflowState.EXECUTING, trigger="execute"),
    WorkflowTransition(from_state=WorkflowState.EXECUTING, to_state=WorkflowState.COMPLETE, trigger="done"),
]
```

### 5.3 Medium-Term Architecture (Months 1-2)

#### R5: Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EVENT BUS ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│     │ Art Studio  │     │    RMOS     │     │  CAM Engine │           │
│     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘           │
│            │                   │                   │                   │
│            │ DesignChanged     │ FeasibilityScored │ ToolpathGenerated │
│            │                   │                   │                   │
│            ▼                   ▼                   ▼                   │
│     ┌──────────────────────────────────────────────────────────┐       │
│     │                    EVENT BUS                              │       │
│     │  Events: DesignChanged, ConstraintsSet, FeasibilityScored │       │
│     │         AIPromptReceived, CandidatesGenerated, etc.      │       │
│     └──────────────────────────────────────────────────────────┘       │
│            │                   │                   │                   │
│            ▼                   ▼                   ▼                   │
│     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│     │  WebSocket  │     │  Job Logger │     │  Analytics  │           │
│     │  Notifier   │     │             │     │   Engine    │           │
│     └─────────────┘     └─────────────┘     └─────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### R6: Unified API Gateway

```python
# services/api/app/gateway/unified_router.py
from fastapi import APIRouter, Depends
from .workflow.state_machine import WorkflowStateMachine
from .rmos.api_contracts import compute_feasibility_for_design

gateway = APIRouter(prefix="/api/v2")

@gateway.post("/workflow/start")
async def start_workflow(mode: DirectionalMode):
    """Unified entry point for all workflow modes"""
    pass

@gateway.post("/workflow/transition/{action}")
async def transition(action: str, state_machine: WorkflowStateMachine = Depends()):
    """Execute state machine transition"""
    pass

@gateway.get("/workflow/state")
async def get_state(state_machine: WorkflowStateMachine = Depends()):
    """Get current workflow state and available actions"""
    pass
```

### 5.4 Long-Term Vision (Months 3-6)

#### R7: Plugin Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PLUGIN ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   CORE KERNEL                                                           │
│   ├── State Machine Engine                                              │
│   ├── Event Bus                                                         │
│   ├── RMOS Feasibility Oracle                                           │
│   └── Data Registry                                                     │
│                                                                         │
│   PLUGIN SLOTS                                                          │
│   ├── [Design Plugin]      → Art Studio, Blueprint Import               │
│   ├── [Constraint Plugin]  → Material Library, Machine Profiles         │
│   ├── [AI Plugin]          → Parameter Suggester, Style Transfer        │
│   ├── [CAM Plugin]         → G-code Generator, Toolpath Optimizer       │
│   ├── [Execution Plugin]   → Saw Lab, Router Lab, Multi-axis            │
│   └── [Analytics Plugin]   → Job Logger, Yield Tracker, Compare Mode    │
│                                                                         │
│   PLUGIN API                                                            │
│   ├── register_plugin(slot, implementation)                             │
│   ├── emit_event(event_type, payload)                                   │
│   ├── subscribe_event(event_type, handler)                              │
│   └── get_current_state() → WorkflowState                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 6: Priority Action Items

### Priority 1: Critical (This Week)

| # | Task | Owner | Files Affected |
|---|------|-------|----------------|
| 1.1 | Create `rmos/context.py` module | Backend | 1 new file |
| 1.2 | Install `httpx` dependency | DevOps | requirements.txt |
| 1.3 | Fix `cam_core` circular imports | Backend | 3-5 files |

### Priority 2: High (Weeks 2-3)

| # | Task | Owner | Files Affected |
|---|------|-------|----------------|
| 2.1 | Implement WorkflowStateMachine | Backend | 2 new files |
| 2.2 | Consolidate CAM routers | Backend | 15 files → 5 files |
| 2.3 | Add WebSocket for real-time updates | Backend | 2 new files |

### Priority 3: Medium (Weeks 4-6)

| # | Task | Owner | Files Affected |
|---|------|-------|----------------|
| 3.1 | Implement Event Bus | Backend | 3 new files |
| 3.2 | Create Unified API Gateway | Backend | 1 new file |
| 3.3 | Add workflow visualization UI | Frontend | 2 Vue components |

---

## Part 7: Key Reference Files

### For Developers Starting Work

1. **Start Here**: `services/api/app/workflow/directional_workflow.py` - Core workflow logic
2. **API Types**: `services/api/app/rmos/api_contracts.py` - All Pydantic models
3. **Router Entry**: `services/api/app/main.py` - Active router list
4. **Architecture**: `projects/rmos/ARCHITECTURE.md` - Full 5-domain design

### For Understanding the Business Logic

1. **Bidirectional Concept**: `The_ Game_Changer_Insight_Bi-Directional_Work_FLow.md`
2. **Workflow Spec**: `RMOS_Directional_Workflow_2_0.md`
3. **Risk System**: `projects/rmos/ARCHITECTURE.md` - Section 7

### For Debugging

1. **Broken Imports**: See `main.py` header comments for list
2. **Dependency Graph**: Run `pip install pipdeptree && pipdeptree`
3. **Router Status**: `grep -r "router as" services/api/app/main.py`

---

## Conclusion

The Luthier's ToolBox bidirectional workflow system is architecturally sound but suffers from implementation fragmentation. The three-mode workflow (Design-First, Constraint-First, AI-Assisted) with RMOS as the central oracle is a powerful and unique approach.

**Immediate priorities:**
1. Fix broken dependencies to restore all 9 disabled routers
2. Implement a formal state machine to replace ad-hoc state management
3. Consolidate the 90+ routers into domain-organized modules

**The bidirectional flow is your competitive advantage** - no other CAM system enables constraint-driven design generation. Focus consolidation efforts on making this flow robust rather than adding new features.

---

*Report generated by AI analysis of repository structure, documentation, and source code.*
