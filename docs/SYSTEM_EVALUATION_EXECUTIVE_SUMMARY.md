# Luthier's ToolBox - System Evaluation Executive Summary

> **Purpose**: Comprehensive technical evaluation for re-review after system changes  
> **Version**: 1.0.0 | **Date**: December 20, 2025  
> **Scope**: Full-stack CAD/CAM system for CNC guitar lutherie

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [Schema Reference](#schema-reference)
5. [Observability & Testing](#observability--testing)
6. [Edge Cases & Failure Modes](#edge-cases--failure-modes)
7. [Operational Risks](#operational-risks)
8. [Graceful Degradation Patterns](#graceful-degradation-patterns)
9. [TODO / Technical Debt](#todo--technical-debt)
10. [Re-Review Checklist](#re-review-checklist)

---

## Executive Summary

### System Identity
**Luthier's ToolBox** is a production CAD/CAM system for CNC guitar manufacturing, providing:
- **Design tools**: Bridge calculator, rosette designer, fretboard geometry
- **CAM engines**: Adaptive pocketing, helical ramping, multi-post G-code generation
- **Manufacturing orchestration**: RMOS (Rosette Manufacturing OS) with governance-compliant workflows

### Architecture Summary
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LUTHIER'S TOOLBOX                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────────────────────────────────────────┐     │
│  │   CLIENT    │    │                     API                         │     │
│  │  Vue 3 +    │◄──►│  FastAPI (Python 3.11+)                         │     │
│  │  Vite       │    │  ├── 102+ Working Routers (33 core)             │     │
│  │  Pinia      │    │  ├── RMOS Feasibility Engine                    │     │
│  └─────────────┘    │  ├── Multi-Post CAM Export                      │     │
│                     │  └── SQLite Persistence                         │     │
│                     └───────────────────────────────────────────────────┘   │
│                                        │                                    │
│                     ┌──────────────────┴──────────────────┐                 │
│                     │        STORAGE LAYER                 │                 │
│                     │  ├── SQLite (rmos.db)               │                 │
│                     │  ├── Date-Partitioned Runs (JSON)   │                 │
│                     │  └── Post Configs (JSON)            │                 │
│                     └─────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Metrics
| Metric | Value | Notes |
|--------|-------|-------|
| Working Routers | 102 | 9 broken (dependency stubs) |
| Core Modules | 33 | Direct imports in main.py |
| CI Workflows | 24 | GitHub Actions |
| Test Coverage | Medium | Unit + Integration tests |
| Schema Version | 2 | N11.1 SQLite migrations |

### Critical Health Indicators

| Component | Status | Risk Level |
|-----------|--------|------------|
| Request ID Middleware | ✅ Healthy | 🟢 LOW |
| RMOS Feasibility Engine | ⚠️ Stub Scorers | 🟡 MEDIUM |
| runs_v2 Persistence | ✅ Governance-compliant | 🟢 LOW |
| Multi-Post Export | ✅ Production-ready | 🟢 LOW |
| Adaptive Pocketing | ✅ L.1/L.2 engines | 🟢 LOW |
| Broken Routers | ❌ 9 broken | 🔴 HIGH |

---

## Architecture Overview

### 1. Entry Point: `main.py`

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MIDDLEWARE STACK (order matters!)                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. RequestIdMiddleware  (correlation, audit trail)         │ │
│  │    ├── Accept X-Request-Id header                          │ │
│  │    ├── Generate req_{uuid} if missing                      │ │
│  │    └── Echo back in response headers                       │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │ 2. CORSMiddleware (allow_origins=["*"])                    │ │
│  │    ⚠️ WARNING: Permissive CORS - tighten for production    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ROUTER REGISTRATION (16 waves)                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Wave 1-6:   Core CAM, RMOS, Geometry, Machine Config       │ │
│  │ Wave 7-10:  Calculators, Presets, Compare Lab              │ │
│  │ Wave 11-13: Analytics, Polygon Offset, Art Studio          │ │
│  │ Wave 14-16: Vision Engine, RMOS Runs, Governance           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  CONDITIONAL ROUTERS (try/except ImportError)                   │
│  ├── ai_cam_router (experimental)                               │
│  ├── vision_router (experimental)                               │
│  ├── joblog_router (cnc_production)                             │
│  └── analytics_router (analytics module)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Strengths:**
- Clean wave-based organization with comments
- Conditional imports prevent startup failures
- Request ID middleware enables distributed tracing
- Health endpoints provide router inventory

**Weaknesses:**
- 9 broken routers (documented but not fixed)
- Some routers have prefix overlap potential
- No rate limiting middleware
- CORS allows all origins

### 2. RMOS Subsystem Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RMOS (Rosette Manufacturing OS)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐     ┌────────────────────┐     ┌─────────────────┐    │
│  │  FEASIBILITY    │────►│  TOOLPATHS         │────►│  RUNS_V2        │    │
│  │  ├─ compute_*   │     │  ├─ dispatch_*     │     │  ├─ RunArtifact │    │
│  │  ├─ resolve_mode│     │  ├─ should_block   │     │  ├─ RunStoreV2  │    │
│  │  └─ STUB scorers│     │  └─ persist_run    │     │  └─ Hashing     │    │
│  └─────────────────┘     └────────────────────┘     └─────────────────┘    │
│           │                        │                         │              │
│           ▼                        ▼                         ▼              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   GOVERNANCE CONTRACTS                               │   │
│  │  ├─ SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md              │   │
│  │  ├─ RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md                         │   │
│  │  └─ Client feasibility ALWAYS ignored, server recomputes            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Governance Invariants (CRITICAL):**
1. Client-provided feasibility is **ALWAYS stripped** and recomputed server-side
2. RED/UNKNOWN risk levels result in HTTP 409 (blocked)
3. **EVERY** request creates a run artifact (OK, BLOCKED, or ERROR)
4. All outputs are SHA256 hashed for provenance

**Code Example - Feasibility Enforcement:**
```python
# services/api/app/rmos/api/rmos_toolpaths_router.py
def rmos_toolpaths(req: Dict[str, Any]) -> Dict[str, Any]:
    # 1. NEVER trust client feasibility
    feasibility = compute_feasibility_internal(tool_id=tool_id, req=req)
    
    # 2. Block if policy requires
    if should_block(mode=mode, risk_level=risk_level):
        artifact = RunArtifact(status="BLOCKED", ...)
        persist_run(artifact)
        raise HTTPException(status_code=409, detail={"error": "SAFETY_BLOCKED"})
    
    # 3. Generate toolpaths + persist OK artifact
    toolpaths_payload = dispatch_toolpaths(mode=mode, req=req)
    artifact = RunArtifact(status="OK", ...)
    persist_run(artifact)
    return toolpaths_payload
```

### 3. Storage Layer

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STORAGE ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SQLite Database (rmos.db)                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Tables:                                                             │   │
│  │  ├─ patterns (rosette designs, geometry_json)                       │   │
│  │  ├─ strip_families (material configurations)                        │   │
│  │  ├─ joblogs (manufacturing run records)                             │   │
│  │  └─ schema_version (migration tracking, v2)                         │   │
│  │                                                                      │   │
│  │  Features:                                                           │   │
│  │  ├─ Connection pooling with context managers                        │   │
│  │  ├─ Transaction rollback on errors                                  │   │
│  │  ├─ Auto-migration for new columns (N11.1)                          │   │
│  │  └─ Singleton instance (get_rmos_db())                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Date-Partitioned Runs (JSON files)                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  data/runs/rmos/                                                     │   │
│  │  ├── 2025-12-17/                                                     │   │
│  │  │   ├── run_abc123def456.json                                       │   │
│  │  │   └── run_abc123def456_advisory_adv001.json  (append-only links) │   │
│  │  └── 2025-12-18/                                                     │   │
│  │      └── run_ghi789jkl012.json                                       │   │
│  │                                                                      │   │
│  │  IMMUTABILITY CONTRACT:                                              │   │
│  │  ├─ Artifacts are write-once (ValueError if exists)                 │   │
│  │  ├─ Atomic writes via .tmp + os.replace()                           │   │
│  │  └─ Advisory links preserve immutability                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Post-Processor Configs (JSON files)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  data/posts/                                                         │   │
│  │  ├── grbl.json      { "header": [...], "footer": [...] }            │   │
│  │  ├── mach4.json                                                      │   │
│  │  ├── linuxcnc.json                                                   │   │
│  │  ├── pathpilot.json                                                  │   │
│  │  └── masso.json                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. CAM Export Flow (Multi-Post)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-POST CAM EXPORT FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CLIENT                                                                     │
│  ┌──────────────────┐                                                       │
│  │ POST /geometry/  │                                                       │
│  │ export_bundle_   │─────────────────────────────────────────────────┐    │
│  │ multi            │                                                  │    │
│  │                  │     Request:                                     │    │
│  │ {                │     {                                            │    │
│  │   geometry,      │       "geometry": { "units": "mm", "paths": []}, │    │
│  │   gcode,         │       "gcode": "G90\nG1 X60...",                  │    │
│  │   post_ids,      │       "post_ids": ["GRBL", "Mach4"],             │    │
│  │   target_units   │       "target_units": "inch"                     │    │
│  │ }                │     }                                            │    │
│  └──────────────────┘                                                  │    │
│                                                                        ▼    │
│  API SERVER                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  1. VALIDATION                                                        │  │
│  │     ├─ File size < 10MB                                              │  │
│  │     ├─ Segments < 100,000                                            │  │
│  │     ├─ Coordinates < 10,000                                          │  │
│  │     └─ Supported file extensions                                     │  │
│  │                                                                       │  │
│  │  2. UNIT CONVERSION (scale_geom_units)                                │  │
│  │     ├─ Internal: always mm                                           │  │
│  │     ├─ MM_PER_IN = 25.4 (NIST definition)                            │  │
│  │     └─ Scale at API boundaries only                                  │  │
│  │                                                                       │  │
│  │  3. POST-PROCESSOR APPLICATION                                        │  │
│  │     for post_id in post_ids:                                          │  │
│  │       ├─ Load data/posts/{post_id}.json                              │  │
│  │       ├─ Prepend header lines                                        │  │
│  │       ├─ Add G21/G20 units command                                   │  │
│  │       ├─ Inject metadata comment                                     │  │
│  │       └─ Append footer lines                                         │  │
│  │                                                                       │  │
│  │  4. BUNDLE CREATION                                                   │  │
│  │     ├─ DXF R12 export (export_dxf)                                   │  │
│  │     ├─ SVG export (export_svg)                                       │  │
│  │     └─ N × .nc files (one per post)                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                        │    │
│                                                                        ▼    │
│  RESPONSE                                                                   │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  StreamingResponse (application/zip)                                │    │
│  │  ├── {job_name}.dxf                                                 │    │
│  │  ├── {job_name}.svg                                                 │    │
│  │  ├── {job_name}_GRBL.nc                                             │    │
│  │  └── {job_name}_Mach4.nc                                            │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. RMOS Workflow State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW STATE TRANSITIONS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                      ┌──────────────────────────────────────────┐           │
│                      │                 DRAFT                    │           │
│                      │  ├─ set_design → DRAFT                   │           │
│                      │  └─ set_context → CONTEXT_READY          │           │
│                      └──────────────────┬───────────────────────┘           │
│                                         │                                   │
│                                         ▼                                   │
│                      ┌──────────────────────────────────────────┐           │
│                      │           CONTEXT_READY                  │           │
│                      │  └─ request_feasibility →                │           │
│                      │         FEASIBILITY_REQUESTED            │           │
│                      └──────────────────┬───────────────────────┘           │
│                                         │                                   │
│                                         ▼                                   │
│                      ┌──────────────────────────────────────────┐           │
│                      │       FEASIBILITY_REQUESTED              │           │
│                      │  └─ store_feasibility →                  │           │
│                      │         FEASIBILITY_READY                │           │
│                      └──────────────────┬───────────────────────┘           │
│                                         │                                   │
│                    ┌────────────────────┼────────────────────┐              │
│                    │                    │                    │              │
│                    ▼                    ▼                    ▼              │
│  ┌─────────────────────┐  ┌────────────────────┐  ┌─────────────────────┐  │
│  │ DESIGN_REVISION_    │  │     APPROVED       │  │     REJECTED        │  │
│  │ REQUIRED            │  │ └─ request_toolpaths│  │ └─ archive →        │  │
│  │ └─ set_design →     │  │    → TOOLPATHS_    │  │       ARCHIVED      │  │
│  │     CONTEXT_READY   │  │      REQUESTED     │  │                     │  │
│  └─────────────────────┘  └─────────┬──────────┘  └─────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│                      ┌──────────────────────────────────────────┐           │
│                      │        TOOLPATHS_REQUESTED               │           │
│                      │  └─ store_toolpaths → TOOLPATHS_READY    │           │
│                      └──────────────────┬───────────────────────┘           │
│                                         │                                   │
│                                         ▼                                   │
│                      ┌──────────────────────────────────────────┐           │
│                      │          TOOLPATHS_READY                 │           │
│                      │  └─ archive → ARCHIVED                   │           │
│                      └──────────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Transition Enforcement:**
```python
# Illegal transitions raise WorkflowTransitionError
def _assert_can(session: WorkflowSession, action: str) -> WorkflowState:
    key = (session.state, action)
    if key not in _ALLOWED:
        raise WorkflowTransitionError(f"Illegal transition: {session.state} --{action}--> ?")
    return _ALLOWED[key]
```

---

## Schema Reference

### 1. RunArtifact (Governance-Compliant)

```python
# services/api/app/rmos/runs_v2/schemas.py

class RunArtifact(BaseModel):
    """
    IMMUTABLE: Once created, artifacts are never modified.
    Created for EVERY request: OK, BLOCKED, or ERROR.
    """
    
    # Identity (REQUIRED)
    run_id: str                          # "run_{uuid.hex}"
    created_at_utc: datetime
    
    # Provenance (OPTIONAL)
    request_id: Optional[str]            # X-Request-Id correlation
    
    # Context (REQUIRED)
    mode: str                            # "saw", "rosette", "cam"
    tool_id: str
    
    # Outcome (REQUIRED)
    status: Literal["OK", "BLOCKED", "ERROR"]
    
    # Inputs (REQUIRED)
    request_summary: Dict[str, Any]      # Redacted request (no client feasibility)
    
    # Authoritative Data (REQUIRED)
    feasibility: Dict[str, Any]          # Server-computed
    decision: RunDecision                # risk_level, score, warnings
    
    # Verification (REQUIRED)
    hashes: Hashes                       # SHA256 for integrity
    
    # Outputs
    outputs: RunOutputs                  # gcode_text, opplan_json, paths

class Hashes(BaseModel):
    feasibility_sha256: str              # REQUIRED per governance
    toolpaths_sha256: Optional[str]
    gcode_sha256: Optional[str]
    opplan_sha256: Optional[str]

class RunDecision(BaseModel):
    risk_level: str                      # GREEN, YELLOW, RED, UNKNOWN, ERROR
    score: Optional[float]               # 0-100
    block_reason: Optional[str]
    warnings: List[str]
```

### 2. SQLite Schema (RMOS Database)

```sql
-- Schema Version: 2 (N11.1)

CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    ring_count INTEGER NOT NULL,
    geometry_json TEXT NOT NULL,
    strip_family_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT,
    pattern_type TEXT NOT NULL DEFAULT 'generic',  -- N11.1 addition
    rosette_geometry TEXT                          -- N11.1 addition
);

CREATE TABLE strip_families (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    strip_width_mm REAL NOT NULL,
    strip_thickness_mm REAL NOT NULL,
    material_type TEXT NOT NULL,
    strips_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT
);

CREATE TABLE joblogs (
    id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    pattern_id TEXT REFERENCES patterns(id),
    strip_family_id TEXT REFERENCES strip_families(id),
    status TEXT NOT NULL DEFAULT 'pending',
    start_time TEXT,
    end_time TEXT,
    duration_seconds REAL,
    parameters_json TEXT NOT NULL,
    results_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX idx_patterns_name ON patterns(name);
CREATE INDEX idx_patterns_strip_family ON patterns(strip_family_id);
CREATE INDEX idx_patterns_pattern_type ON patterns(pattern_type);
CREATE INDEX idx_joblogs_status ON joblogs(status);
CREATE INDEX idx_joblogs_created ON joblogs(created_at DESC);
```

### 3. Post-Processor Configuration

```json
// data/posts/grbl.json
{
  "header": [
    "G90",              // Absolute positioning
    "G21",              // Millimeters
    "G94",              // Feed per minute
    "F1000",            // Default feed rate
    "(post GRBL)"       // Comment
  ],
  "footer": [
    "M5",               // Spindle stop
    "M30"               // Program end
  ]
}
```

### 4. CAD Exception Hierarchy

```
CadEngineError (base)
├── DxfValidationError   (coordinate bounds, entity limits)
├── DxfExportError       (ezdxf write failures)
├── OffsetEngineError    (buffer computation)
│   └── OffsetEngineNotAvailable (Shapely missing)
└── GeometryError        (self-intersection, degenerate)
```

---

## Observability & Testing

### 1. Logging Infrastructure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LOGGING ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOG FORMAT                                                                 │
│  "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"        │
│                                                                             │
│  Example:                                                                   │
│  2025-12-20 10:30:45 INFO [req_abc123def456] app.rmos.toolpaths: ...       │
│                                                                             │
│  COMPONENTS                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RequestIdMiddleware                                                 │   │
│  │  ├─ Accepts X-Request-Id from client                                │   │
│  │  ├─ Generates req_{uuid} if missing                                 │   │
│  │  ├─ Sets ContextVar for deep access                                 │   │
│  │  └─ Echoes back in X-Request-Id response header                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  RequestIdFilter (logging.Filter)                                    │   │
│  │  └─ Injects request_id into all log records                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ContextVar (request_context.py)                                     │   │
│  │  ├─ get_request_id() - access anywhere in call stack                │   │
│  │  └─ set_request_id() - middleware sets at start, clears at end      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LOGGING USAGE                                                              │
│  ├─ logger = logging.getLogger(__name__)                                   │
│  ├─ logger.info("Processing...", extra={"request_id": rid})                │
│  └─ logger.warning("Fallback used: {}")                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Health Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | Basic liveness | `{"status": "healthy", "version": "2.0.0-clean"}` |
| `GET /api/health` | Detailed inventory | Router counts, broken/working status |
| `GET /api/system/health` | Extended diagnostics | Path checks, dependency versions, queue/cache status |

### 3. CI/CD Workflows

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CI WORKFLOW INVENTORY                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CORE API                                                                   │
│  ├─ api_pytest.yml         Unit tests (pytest)                             │
│  ├─ api_health_check.yml   Health endpoint verification                    │
│  ├─ api_tests.yml          Integration tests                               │
│  └─ server-env-check.yml   Environment validation                          │
│                                                                             │
│  RMOS                                                                       │
│  ├─ rmos_ci.yml            Smoke tests via rmos_ci_test.py                 │
│  └─ rmos_migration.yml     Database migration tests                        │
│                                                                             │
│  CAM                                                                        │
│  ├─ cam_essentials.yml     Core CAM operations                             │
│  ├─ cam_gcode_smoke.yml    G-code generation                               │
│  ├─ adaptive_pocket.yml    Pocketing engine                                │
│  └─ helical_badges.yml     Helical ramping (badge generation)              │
│                                                                             │
│  CLIENT                                                                     │
│  ├─ client_lint_build.yml  Lint + build (Vite)                             │
│  └─ client_smoke.yml       Component smoke tests                           │
│                                                                             │
│  GEOMETRY                                                                   │
│  ├─ geometry_parity.yml    Design vs toolpath accuracy                     │
│  └─ api_dxf_tests.yml      DXF R12 roundtrip                               │
│                                                                             │
│  COMPARE LAB                                                                │
│  ├─ comparelab-tests.yml   State machine tests                             │
│  └─ comparelab-golden.yml  Golden file regression                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4. Test Structure

```
services/api/app/tests/
├── test_dxf_r12_roundtrip.py     # DXF export/import cycle
├── test_dxf_security_patch.py    # Security validation
├── test_e2e_workflow_integration.py
├── test_fan_fret_perpendicular.py
├── test_tool_library_phase1.py
├── rmos/
│   └── test_rosette_patterns_router.py
├── calculators/                   # Calculator unit tests
└── ai_graphics/                   # Vision engine tests
```

---

## Edge Cases & Failure Modes

### 1. Input Validation Edge Cases

| Edge Case | Location | Handling |
|-----------|----------|----------|
| Empty geometry paths | `geometry_router.py` | Return empty result, no crash |
| Coordinates > 10,000 | `geometry_router.py` | HTTPException 400 |
| File > 10MB | `geometry_router.py` | HTTPException 413 |
| Invalid DXF format | `dxf_engine.py` | DxfValidationError → 400 |
| Self-intersecting polygon | `offset_engine.py` | OffsetEngineError → 500 |
| Missing tool_id | `rmos_toolpaths_router.py` | HTTPException 400 "MISSING_TOOL_ID" |
| Unknown post processor | `_load_posts()` | Log warning, use empty config |

### 2. Concurrency Edge Cases

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Simultaneous artifact writes | Data corruption | Atomic writes via .tmp + os.replace() |
| Duplicate run_id | Collision | UUID generation + exists check |
| Database connection exhaustion | Deadlock | Context manager with auto-close |
| SQLite concurrent writes | Lock contention | Single-writer model (SQLite default) |

### 3. Resource Exhaustion

| Resource | Limit | Protection |
|----------|-------|------------|
| Memory | MAX_SEGMENTS = 100,000 | Validation before processing |
| Disk | Run partitions | Date-based cleanup (manual) |
| CPU | CAM computation | Async timeout (cam/async_timeout.py) |
| Network | CORS origins | Permissive (⚠️ tighten for prod) |

---

## Operational Risks

### 🔴 HIGH RISK

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| 9 broken routers | Partial functionality | Certain | Fix dependency stubs |
| RMOS scorers are stubs | Feasibility inaccurate | Certain | Wire real calculators |
| No rate limiting | DoS vulnerability | Medium | Add middleware |
| Permissive CORS | Security exposure | Low | Restrict origins |
| No auth middleware | Unauthorized access | Medium | Add JWT/OAuth |

### 🟡 MEDIUM RISK

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SQLite single-writer | Scale limitation | Medium | Migrate to PostgreSQL |
| Date partition cleanup | Disk exhaustion | Low | Add retention policy |
| Advisory links unbounded | Storage growth | Low | Add pagination/limits |
| Import fallback chains | Silent degradation | Medium | Improve logging |

### 🟢 LOW RISK

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Schema migration | Data loss | Low | Version tracking + backups |
| Post config malformed | Missing headers | Low | Graceful fallback |
| Request ID collision | Audit gap | Very Low | UUID sufficient |

---

## Graceful Degradation Patterns

### 1. Router Import Fallbacks

```python
# main.py - Pattern for optional routers
try:
    from .routers.ai_cam_router import router as ai_cam_router
except ImportError as e:
    print(f"Warning: AI-CAM router not available: {e}")
    ai_cam_router = None

# Later...
if ai_cam_router:
    app.include_router(ai_cam_router, prefix="/api", tags=["AI-CAM"])
```

**Strength:** Server starts even with missing dependencies  
**Weakness:** Silent degradation - users may not know features are unavailable

### 2. Post Processor Fallbacks

```python
# geometry_router.py - _load_posts()
try:
    with open(os.path.join(posts_dir, f), "r", encoding="utf-8") as fh:
        out[f[:-5]] = json.load(fh)
except json.JSONDecodeError as e:
    # Log but don't crash if one post file is malformed
    print(f"Warning: Failed to load post {f}: {e}")
```

**Strength:** Partial post configs don't crash entire system  
**Weakness:** Warning only printed to stdout, not logged properly

### 3. Toolpath Fallback Chains

```python
# rmos/toolpaths.py - Multiple fallback layers
try:
    from ..saw_lab.saw_toolpath_generator import generate_saw_toolpaths
except ImportError:
    logger.warning(f"saw_lab import failed, using fallback: {e}")
    # Fallback to stub generator
    def generate_saw_toolpaths(...): return {"toolpaths": [], "gcode": ""}
```

### 4. Database Auto-Migration

```python
# core/rmos_db.py - Column migration
cursor.execute("PRAGMA table_info(patterns)")
columns = {row[1] for row in cursor.fetchall()}

if 'pattern_type' not in columns:
    logger.info("Migrating: Adding pattern_type column")
    cursor.execute("""
        ALTER TABLE patterns 
        ADD COLUMN pattern_type TEXT NOT NULL DEFAULT 'generic'
    """)
```

**Strength:** Automatic schema evolution  
**Weakness:** No down-migration path

### 5. Error Artifact Persistence

```python
# rmos/api/rmos_toolpaths_router.py
except Exception as e:
    # ERROR artifact - still persisted for audit
    artifact = RunArtifact(
        status="ERROR",
        errors=[f"{type(e).__name__}: {str(e)}"],
        ...
    )
    persist_run(artifact)  # Always persist, even on error
    raise HTTPException(status_code=500, detail={...})
```

**Strength:** Complete audit trail even for failures  
**Weakness:** Error artifacts may accumulate

---

## TODO / Technical Debt

### 🔴 Critical (Blocking Production)

| Item | Location | Impact |
|------|----------|--------|
| Wire SAW feasibility scorer | `rmos_feasibility_router.py:97` | Risk assessment inaccurate |
| Wire rosette feasibility scorer | `rmos_feasibility_router.py:146` | Risk assessment inaccurate |
| Wire toolpath generators | `rmos_toolpaths_router.py:216` | Using stubs |
| Fix 9 broken routers | `main.py` header | Missing functionality |

### 🟡 Important (Technical Debt)

| Item | Location | Impact |
|------|----------|--------|
| Replace DXF stub with LWPOLYLINE | `toolpath/dxf_exporter.py:133` | R14/R18 compatibility |
| Compute string spacings | `rmos/context.py:282-283` | Fretboard calculations |
| Implement compare engine | `util/compare_automation_helpers.py:89` | Compare Lab incomplete |
| Real storage lookup | `util/compare_automation_helpers.py:41` | Baseline retrieval |

### 🟢 Nice-to-Have

| Item | Location | Impact |
|------|----------|--------|
| Saw blade RPM limits | `cam_core/saw_lab/saw_blade_validator.py:293` | Enhanced validation |
| Real DXF parsing | `rmos/context_adapter.py:273` | Blueprint import |
| Learned overrides wiring | `_experimental/cnc_production/learn:80` | ML integration |

### Code Locations (grep `TODO:|FIXME:`)

```bash
# Find all TODOs
grep -r "TODO:" services/api/app/ --include="*.py" | wc -l
# Result: 15+ active TODOs
```

---

## Re-Review Checklist

Use this checklist after making system changes:

### Architecture

- [ ] **Router Registration**: All new routers added to `main.py` with appropriate wave?
- [ ] **Import Guards**: New dependencies wrapped in `try/except ImportError`?
- [ ] **Prefix Conflicts**: No overlapping route prefixes?
- [ ] **Health Endpoint**: Router counts updated in `/api/health`?

### RMOS Governance

- [ ] **Feasibility Enforcement**: Server-side recompute before toolpaths?
- [ ] **Artifact Persistence**: Every request creates artifact (OK/BLOCKED/ERROR)?
- [ ] **Hash Verification**: All outputs have SHA256 hashes?
- [ ] **Risk Blocking**: RED/UNKNOWN blocks with HTTP 409?

### Storage

- [ ] **Schema Migration**: `schema_version` table updated?
- [ ] **Run Immutability**: No modification of existing artifacts?
- [ ] **Atomic Writes**: Using .tmp + os.replace() pattern?
- [ ] **Advisory Links**: Append-only, not modifying parent?

### Observability

- [ ] **Request ID**: All logs include `[request_id]`?
- [ ] **Error Logging**: Exceptions logged before re-raising?
- [ ] **Fallback Warnings**: `logger.warning()` for degraded modes?

### Testing

- [ ] **Unit Tests**: New code has pytest coverage?
- [ ] **CI Workflow**: Appropriate workflow triggered on changes?
- [ ] **Integration Tests**: E2E scenarios covered?

### Security

- [ ] **Input Validation**: Bounds checking for coordinates/sizes?
- [ ] **Path Sanitization**: Filename stems cleaned?
- [ ] **CORS Configuration**: Origins appropriate for environment?

### Performance

- [ ] **Resource Limits**: MAX_SEGMENTS, MAX_FILE_SIZE respected?
- [ ] **Connection Pooling**: Database connections properly closed?
- [ ] **Async Operations**: Long-running tasks don't block?

---

## Appendix: Quick Reference Commands

```bash
# Start API server
cd services/api && uvicorn app.main:app --reload --port 8000

# Run pytest
cd services/api && pytest app/tests/ -v

# Run RMOS CI
cd services/api && python ../../scripts/rmos_ci_test.py

# Check health
curl -s http://localhost:8000/api/health | jq .

# List broken routers
grep "BROKEN ROUTERS" services/api/app/main.py -A 10

# Find TODOs
grep -rn "TODO:" services/api/app/ --include="*.py"

# Check schema version
sqlite3 services/api/data/rmos.db "SELECT * FROM schema_version;"

# Count run artifacts
find services/api/data/runs/rmos -name "*.json" | wc -l
```

---

*Document generated: December 20, 2025*  
*Next review recommended: After any Wave 17+ additions or governance contract changes*
