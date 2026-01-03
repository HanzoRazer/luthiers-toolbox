# AI Code Bundle Lock Points v1

> **Purpose**: Authoritative reference for AI-generated code bundles. This file provides concrete specifications to prevent API drift, type mismatches, and UI placement errors.
>
> **Auto-Generated**: 2026-01-07
> **Branch**: `feature/cnc-saw-labs`

---

## (A) Authoritative Router Mount Table

### Canonical Prefixes (Use These)

| Router | Prefix | Tags | Status |
|--------|--------|------|--------|
| `rmos_router` | `/api/rmos` | RMOS | ✅ Canonical |
| `rmos_ai_router` | `/api/rmos` | RMOS AI | ✅ Canonical |
| `rmos_profiles_router` | `/api/rmos` | RMOS Profiles | ✅ Canonical |
| `rmos_history_router` | `/api/rmos` | RMOS History | ✅ Canonical |
| `rmos_runs_router` | `/api/rmos` | RMOS, Runs | ✅ Canonical |
| `rmos_workflow_router` | `/api/rmos/workflow` | RMOS, Workflow | ✅ Canonical |
| `rmos_feasibility_router` | `/api/rmos` | RMOS, Feasibility | ✅ Canonical |
| `rmos_toolpaths_router` | `/api/rmos` | RMOS, Toolpaths | ✅ Canonical |
| `cam_router` | `/api/cam` | CAM Consolidated | ✅ Canonical (Wave 18) |
| `compare_router` | `/api/compare` | Compare Consolidated | ✅ Canonical (Wave 19) |
| `saw_batch_router` | `/api/saw/batch` | Saw Lab | ✅ Canonical (Operation Lane) |
| `art_patterns_router` | `/api/art` | Art Studio, Patterns | ✅ Canonical |
| `art_generators_router` | `/api/art` | Art Studio, Generators | ✅ Canonical |
| `art_preview_router` | `/api/art` | Art Studio, Preview | ✅ Canonical |
| `art_snapshots_router` | `/api/art` | Art Studio, Snapshots | ✅ Canonical |
| `tooling_router` | `/api/tooling` | Tooling | ✅ Canonical |
| `machines_router` | `/api/machines` | Machines | ✅ Canonical |
| `posts_router` | `/api/posts` | Post Processors | ✅ Canonical |
| `feeds_router` | `/api/feeds` | Feeds & Speeds | ✅ Canonical |

### OPERATION Lane Endpoints (G-code Producing)

These endpoints MUST use the governed workflow (spec → plan → approve → execute):

```python
# Reference Implementation: Saw Lab Batch
POST /api/saw/batch/spec        # Stage: SPEC
POST /api/saw/batch/plan        # Stage: PLAN  
POST /api/saw/batch/approve     # Stage: DECISION
POST /api/saw/batch/toolpaths   # Stage: EXECUTE
GET  /api/saw/batch/executions/{id}/gcode  # Stage: EXPORT

# RMOS Operations (generic adapter)
POST /api/rmos/operations/{tool_id}/execute
POST /api/rmos/operations/{tool_id}/plan
GET  /api/rmos/operations/{run_id}/export.zip
```

---

## (B) Canonical Enums & Schema Names

### TypeScript Enums (packages/client/src/api/rmosRuns.ts)

```typescript
// VARIANT STATUS - Advisory variant workflow states
export type VariantStatus = "NEW" | "REVIEWED" | "PROMOTED" | "REJECTED";

// RISK LEVEL - Feasibility gate decisions  
export type RiskLevel = "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | "ERROR";

// REJECTION REASON CODES - Operator rejection justification
export type RejectReasonCode =
  | "GEOMETRY_UNSAFE"
  | "TEXT_REQUIRES_OUTLINE"
  | "AESTHETIC"
  | "DUPLICATE"
  | "OTHER";

// DIFF SEVERITY - Run comparison results
export type DiffSeverity = "CRITICAL" | "WARNING" | "INFO" | "NONE";

// RISK BUCKET ID - Dashboard classification (sawLab.ts)
export type RiskBucketId = "unknown" | "green" | "yellow" | "orange" | "red";

// BULK PROMOTE DECISION - Gate verdict
export type BulkPromoteDecision = "ALLOW" | "BLOCK";
```

### Key Interfaces

```typescript
// Advisory Variant Summary (rmosRuns.ts:180-220)
export interface AdvisoryVariantSummary {
  advisory_id: string;               // sha256 CAS key (required)
  created_at_utc?: string | null;
  risk_level?: RiskLevel | null;
  rating?: number | null;            // 1-5 scale
  notes?: string | null;
  status?: VariantStatus | null;
  promoted_candidate_id?: string | null;
  rejected?: boolean | null;
  has_preview?: boolean | null;
  // Rejection details (Undo Reject bundle)
  rejection_reason_code?: string | null;
  rejection_reason_detail?: string | null;
  rejection_operator_note?: string | null;
  rejected_at_utc?: string | null;
}

// Run Artifact Detail (rmosRuns.ts:35-65)
export interface RunArtifactDetail {
  run_id: string;                    // UUID (required)
  created_at_utc: string;            // ISO 8601
  workflow_session_id?: string | null;
  tool_id?: string | null;
  material_id?: string | null;
  machine_id?: string | null;
  workflow_mode?: string | null;
  event_type: string;                // e.g., "EXECUTE", "PLAN"
  status: string;                    // e.g., "OK", "BLOCKED"
  feasibility?: Record<string, any> | null;
  request_hash?: string | null;
  toolpaths_hash?: string | null;
  gcode_hash?: string | null;
  parent_run_id?: string | null;
  drift_detected?: boolean;
  drift_summary?: string | null;
  gate_decision?: string | null;
  engine_version?: string | null;
}

// Execute Operation Request (sdk/rmos/operations.ts)
export type ExecuteOperationRequest = {
  cam_intent_v1: CamIntentV1;        // Intent envelope
  feasibility: FeasibilityResult;    // Server feasibility result
  parent_plan_run_id?: string;       // Lineage link
  meta?: Record<string, unknown>;    // Custom metadata
};

// Feasibility Result
export type FeasibilityResult = {
  risk_level?: "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | string;
  risk?: string;
  score?: number;                    // 0.0-1.0
  warnings?: string[];
  block_reason?: string | null;
  details?: Record<string, unknown>;
};
```

### Python Enums (Backend)

```python
# Location: services/api/app/rmos/runs_v2/schemas.py (or equivalent)

class VariantStatus(str, Enum):
    NEW = "NEW"
    REVIEWED = "REVIEWED"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"

class RiskLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

class RejectReasonCode(str, Enum):
    GEOMETRY_UNSAFE = "GEOMETRY_UNSAFE"
    TEXT_REQUIRES_OUTLINE = "TEXT_REQUIRES_OUTLINE"
    AESTHETIC = "AESTHETIC"
    DUPLICATE = "DUPLICATE"
    OTHER = "OTHER"
```

---

## (C) UI Location Conventions

### Directory Structure

```
packages/client/src/
├── views/                    # Route-level pages (1 per route)
│   ├── RmosRunsView.vue      # /rmos/runs
│   ├── SawLabView.vue        # /saw-lab
│   ├── ArtStudioIndex.vue    # /art-studio
│   ├── ArtStudioRosette.vue  # /art-studio/rosette
│   ├── CompareView.vue       # /compare
│   └── ...
├── components/               # Reusable UI elements
│   ├── rmos/                 # RMOS domain components
│   │   ├── RmosRunCard.vue
│   │   ├── RmosRunDiff.vue
│   │   └── RmosOperationE2EPanel.vue
│   ├── saw_lab/              # Saw Lab domain components
│   │   ├── SawBatchSpec.vue
│   │   ├── SawBatchPlan.vue
│   │   └── SawJobLogForm.vue
│   ├── artstudio/            # Art Studio domain components
│   │   ├── RosettePreview.vue
│   │   └── PatternGenerator.vue
│   ├── cam/                  # CAM domain components
│   │   ├── ToolpathPreview.vue
│   │   └── RiskIndicator.vue
│   └── common/               # Cross-domain shared
│       ├── DataTable.vue
│       └── LoadingSpinner.vue
├── sdk/                      # Typed API clients
│   ├── endpoints/            # H8.3 typed helpers
│   │   ├── cam/
│   │   │   ├── roughing.ts
│   │   │   └── types.ts
│   │   └── index.ts
│   ├── rmos/                 # RMOS domain SDK
│   │   ├── index.ts
│   │   ├── runs.ts
│   │   ├── operations.ts
│   │   ├── workflow.ts
│   │   └── runs_attachments.ts
│   └── core/
│       ├── apiFetch.ts       # Simple transport
│       ├── apiFetchRaw.ts    # H8.3 raw transport
│       └── errors.ts
├── api/                      # Legacy API clients (migrate to sdk/)
│   ├── rmosRuns.ts           # ⚠️ Being migrated to sdk/rmos/
│   ├── sawLab.ts
│   └── ...
└── stores/                   # Pinia stores
    ├── useRmosRunsStore.ts
    └── useSawLabStore.ts
```

### Placement Rules

| Component Type | Location | Example |
|---------------|----------|---------|
| Route page | `views/` | `RmosRunsView.vue` |
| Domain component | `components/{domain}/` | `components/rmos/RmosRunCard.vue` |
| Cross-domain component | `components/common/` | `components/common/DataTable.vue` |
| Typed API helper | `sdk/endpoints/{domain}/` | `sdk/endpoints/cam/roughing.ts` |
| Domain SDK | `sdk/rmos/` | `sdk/rmos/operations.ts` |
| Pinia store | `stores/` | `stores/useRmosRunsStore.ts` |

### Naming Conventions

```typescript
// Views: {Domain}View.vue or {Domain}{SubDomain}View.vue
RmosRunsView.vue
SawLabView.vue
ArtStudioRosetteView.vue

// Components: {Domain}{Thing}.vue
RmosRunCard.vue
SawBatchPlan.vue
ArtStudioPreview.vue

// SDK: lowercase with domain prefix
sdk/rmos/runs.ts
sdk/endpoints/cam/roughing.ts

// Stores: use{Domain}{Resource}Store.ts
useRmosRunsStore.ts
useSawLabStore.ts
```

---

## (D) Deprecation "Red List"

### Legacy Routers (tags=["Legacy"])

These routers have "Legacy" tag and emit deprecation headers. **DO NOT USE for new code.**

| Legacy Prefix | Canonical Replacement | Router Name |
|--------------|----------------------|-------------|
| `/api/cam/vcarve` | `/api/cam/toolpath/vcarve` | `cam_vcarve_router` |
| `/api/cam/relief` | `/api/cam/relief` (proxy) | `cam_relief_router` |
| `/api/cam/svg` | `/api/cam/export` | `cam_svg_router` |
| `/api/cam/helical` | `/api/cam/toolpath/helical` | `cam_helical_router` |
| `/api/rosette` | `/api/art/rosette` | `rosette_pattern_router` |
| `/api/art-studio/rosette` | `/api/art/rosette` | `art_studio_rosette_router` |
| `/api/cam/fret_slots` | `/api/cam/fret_slots` (proxy) | `cam_fret_slots_router` |
| `/api/cam/drill*` | `/api/cam/drilling/pattern` | `cam_drill_pattern_router` |
| `/api/cam/roughing/*` | `/api/cam/toolpath/roughing` | `cam_roughing_router` |
| `/api/compare` (old) | `/api/compare` (Wave 19) | `legacy_compare_router` |
| `/api/compare/lab` (old) | `/api/compare/lab` (Wave 19) | `compare_lab_router` |
| `/api/cam/drilling` (old) | `/api/cam/drilling` (Wave 18) | `drilling_router` |
| `/api/cam/risk` (old) | `/api/cam/risk` (Wave 18) | `cam_risk_router` |
| `/api/cam/biarc` | `/api/cam/toolpath/biarc` | `cam_biarc_router` |
| `/api/cam/fret_slots` (export) | `/api/cam/fret_slots` (proxy) | `cam_fret_slots_export_router` |
| `/api/cam/jobs` | `/api/cam/risk` | `cam_risk_aggregate_router` |
| `/api/compare` (risk agg) | `/api/compare/risk` | `compare_risk_aggregate_router` |
| `/api/compare` (bucket) | `/api/compare/risk` | `compare_risk_bucket_detail_router` |
| `/api/compare` (export) | `/api/compare/risk` | `compare_risk_bucket_export_router` |

### Scheduled for Removal (Smart Guitar Backend API.md)

| Router | Lines | Prefix | Status |
|--------|-------|--------|--------|
| `archtop_router.py` | 307 | `/cam/archtop` | 🔴 DEPRECATE |
| `om_router.py` | 517 | `/cam/om` | 🔴 DEPRECATE |
| `stratocaster_router.py` | 430 | `/cam/stratocaster` | 🔴 DEPRECATE |
| `smart_guitar_router.py` | 357 | `/cam/smart-guitar` | 🔴 DEPRECATE |
| `temperament_router.py` | 297 | `/temperaments` | 🔴 DEPRECATE |

**Reason**: Replaced by unified `parametric_guitar_router` at `/api/guitar/parametric`.

### Deprecation Headers

When calling legacy endpoints, these headers are emitted:

```http
Deprecation: true
Sunset: 2025-12-31
X-Deprecated-Lane: cam_roughing_router
Link: </api/cam/toolpath/roughing>; rel="successor-version"
```

---

## Quick Reference Card

### For New CAM Endpoints
```typescript
// ✅ CORRECT
import { cam } from "@/sdk/endpoints";
const { gcode, summary } = await cam.roughingGcode(payload);

// ❌ WRONG - raw fetch to legacy path
const res = await fetch("/api/cam/roughing/gcode", ...);
```

### For RMOS Operations
```typescript
// ✅ CORRECT
import { rmos } from "@/sdk";
const result = await rmos.operations.executeOperation("saw_v1", {
  cam_intent_v1: intent,
  feasibility: { risk_level: "GREEN" },
});

// ❌ WRONG - calling UTILITY lane directly
const res = await fetch("/api/rmos/workflow/sessions/.../toolpaths/request", ...);
```

### For New Components
```
✅ CORRECT placement:
  - View page: packages/client/src/views/NewFeatureView.vue
  - Domain component: packages/client/src/components/domain/NewComponent.vue
  - SDK helper: packages/client/src/sdk/endpoints/domain/newHelper.ts

❌ WRONG:
  - Random location: packages/client/src/NewComponent.vue
  - Legacy API: packages/client/src/api/newApi.ts (use sdk/ instead)
```

---

## File References

| Document | Path | Purpose |
|----------|------|---------|
| Endpoint Truth JSON | `services/api/app/data/endpoint_truth.json` | Machine-readable CI source |
| Router Map | `ROUTER_MAP.md` | Wave-by-wave router reference |
| Endpoint Truth Map | `docs/ENDPOINT_TRUTH_MAP.md` | Complete API surface |
| Boundary Rules | `docs/BOUNDARY_RULES.md` | Import restrictions |
| SDK README | `packages/client/src/sdk/endpoints/README.md` | H8.3 SDK patterns |
| Copilot Instructions | `.github/copilot-instructions.md` | AI agent quickstart |

---

*This document is the authoritative reference for AI code bundle generation. When in doubt, this file wins over cached assumptions.*
