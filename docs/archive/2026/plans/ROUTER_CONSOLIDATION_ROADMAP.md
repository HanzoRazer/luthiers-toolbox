# Router Consolidation Roadmap

**Current State**: 143 router files, 565 route decorators
**Target**: <100 router files, <600 route decorators
**Gate**: `ci/router_count_gate.py` enforces ratchet baseline

## Consolidation Candidates

### Tier 1: Low-Risk Merges (6 → 1 each)

#### saw_lab Execution Lifecycle
Merge into `execution_lifecycle_router.py`:
- `execution_abort_router.py` (1 route, 71 lines)
- `execution_complete_router.py` (1 route, ~150 lines)
- `execution_confirmation_router.py` (2 routes, 120 lines)
- `execution_metrics_router.py` (1 route, 47 lines)
- `execution_start_from_toolpaths_router.py` (1 route, ~100 lines)
- `execution_status_router.py` (1 route, 67 lines)

**Savings**: 5 files, ~555 lines total (well under 500 limit)

#### saw_lab Toolpaths Operations
Merge into `toolpaths_operations_router.py`:
- `toolpaths_download_router.py` (1 route)
- `toolpaths_lint_router.py` (1 route)
- `toolpaths_lookup_router.py` (2 routes)
- `toolpaths_validate_router.py` (1 route)

**Savings**: 3 files

#### saw_lab Metrics Lookup
Merge into `metrics_lookup_consolidated_router.py`:
- `metrics_lookup_router.py` (1 route)
- `metrics_latest_by_execution_router.py` (1 route)
- `latest_batch_chain_router.py` (1 route)

**Savings**: 2 files

### Tier 2: Medium-Risk Merges

#### app/routers CAM Pipeline
- `cam_pipeline_router.py` (1 route)
- `cam_pipeline_preset_run_router.py` (1 route)
- `pipeline_router.py` (1 route)

Could consolidate into `pipeline_consolidated_router.py`

#### app/routers Machines/Posts
Already have consolidated versions:
- `machines_consolidated_router.py` ← deprecate `machines_router.py`
- `posts_consolidated_router.py` ← deprecate `posts_router.py`

### Tier 3: Requires Analysis

These directories have many small routers but need endpoint usage analysis:
- `app/routers/probe/` (6 files)
- `app/routers/cam/guitar/` (5 files)
- `app/routers/adaptive/` (4 files)
- `app/rmos/acoustics/` (4 files)

## Consolidation Process

1. **Create consolidated router** with all routes from source files
2. **Update `__init_router__.py`** to import from consolidated file
3. **Keep old files** with deprecation warnings + re-exports
4. **Run tests** to verify no breakage
5. **After 2 weeks**, delete deprecated files
6. **Update baseline** with `python ci/router_count_gate.py --update`

## Do NOT Consolidate

- Health/metrics routers (system endpoints)
- Domain aggregate routers (`__init_router__.py` files)
- Routers with different auth requirements
- Routers that are explicitly versioned (v1, v2)

## Tracking

| Consolidation | Files Reduced | Status |
|--------------|---------------|--------|
| saw_lab execution lifecycle | 5 | Planned |
| saw_lab toolpaths | 3 | Planned |
| saw_lab metrics | 2 | Planned |
| CAM pipeline | 2 | Planned |
| machines/posts deprecation | 2 | Planned |
| **Total** | **14** | - |

Expected outcome: 143 - 14 = **129 router files** (still above 100 target)

Additional consolidation needed for <100 target.
