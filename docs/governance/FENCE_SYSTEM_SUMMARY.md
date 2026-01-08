# Fence System Implementation Summary

> **Completed**: 2026-01-08
> **Status**: Ready for deployment and CI integration

---

## What We Built

A comprehensive **architectural boundary enforcement system** (fence system) that prevents domain bleed and maintains clean separation between:

1. **External boundaries** (ToolBox ↔ Analyzer)
2. **Internal domains** (RMOS ↔ CAM)
3. **Operation lanes** (governed vs utility)
4. **AI sandbox** (advisory vs execution)
5. **Frontend** (SDK vs raw fetch)
6. **Artifact authority** (centralized validation)
7. **Legacy deprecation** (migration tracking)

---

## Files Created/Updated

### New Files

| File | Purpose | Lines |
|------|---------|-------|
| `FENCE_REGISTRY.json` | Machine-readable boundary definitions | 380 |
| `docs/governance/FENCE_ARCHITECTURE.md` | Complete fence documentation | 650 |
| `docs/governance/FENCE_SYSTEM_SUMMARY.md` | This summary | 150 |

### Updated Files

| File | Changes | Purpose |
|------|---------|---------|
| `.github/copilot-instructions.md` | Added fence references, updated critical rules, enhanced CLI commands | AI agent guidance |
| `Makefile` | Added `check-boundaries` target | Local development workflow |

---

## Key Components

### 1. FENCE_REGISTRY.json

**Schema**: `fence-registry-v1.json`

**Structure**:
```json
{
  "profiles": {
    "external_boundary": { ... },
    "rmos_cam_boundary": { ... },
    "operation_lane_boundary": { ... },
    "ai_sandbox_boundary": { ... },
    "saw_lab_encapsulation": { ... },
    "frontend_sdk_boundary": { ... },
    "artifact_authority": { ... },
    "legacy_deprecation": { ... }
  },
  "enforcement_order": [...],
  "ci_integration": {...},
  "exemption_process": {...}
}
```

**Features**:
- Forbidden import prefixes with rationale
- Alternative integration patterns
- CI script references
- Documentation links
- Enforcement order specification

### 2. FENCE_ARCHITECTURE.md

**Sections**:
- Philosophy (why fences matter)
- 8 detailed fence profiles with examples
- Enforcement stack (CI + pre-commit hooks)
- Integration patterns (artifact, HTTP, SDK)
- Exemption process
- Metrics & monitoring
- Quick reference card

**Usage Examples**:
- Correct vs incorrect patterns for each fence
- Visual diagrams of domain boundaries
- Command-line enforcement examples

### 3. Copilot Instructions Enhancement

**Added**:
- Critical Rule #11: Architectural Fences reference
- 7 boundary check commands in "Essential CLI Commands"
- Updated "Common Pitfalls" with fence-specific issues
- New reference to FENCE_REGISTRY.json and FENCE_ARCHITECTURE.md

### 4. Makefile Target

**Command**: `make check-boundaries`

**Runs**:
1. External boundary check (toolbox profile)
2. RMOS ↔ CAM domain boundary check
3. Operation lane compliance check
4. AI sandbox boundary checks (3 scripts)
5. Artifact authority check
6. CAM Intent schema validation
7. Legacy usage gate (frontend)

---

## Fence Profiles Overview

### Profile 1: External Boundary

**Prevents**: Cross-repo code dependencies (ToolBox → Analyzer)

**Enforces**: Artifact-based integration only

**Script**: `python -m app.ci.check_boundary_imports --profile toolbox`

**Status**: ✅ Already enforced in CI

---

### Profile 2: RMOS ↔ CAM Boundary

**Prevents**: 
- RMOS directly generating toolpaths
- CAM directly managing workflow state

**Enforces**: 
- RMOS uses CAM Intent envelope + HTTP
- CAM returns data structures, no orchestration

**Script**: `python -m app.ci.check_domain_boundaries --profile rmos_cam`

**Status**: ⚠️ Script needs creation (template provided in FENCE_ARCHITECTURE.md)

---

### Profile 3: Operation Lane Boundary

**Prevents**: Machine-executing endpoints without governance

**Enforces**:
- OPERATION lane: artifacts + feasibility + audit trail
- UTILITY lane: stateless, no artifact storage

**Script**: `python -m app.ci.check_operation_lane_compliance`

**Status**: ✅ Already enforced for `/api/saw/batch/*`

---

### Profile 4: AI Sandbox Boundary

**Prevents**: AI directly controlling production workflows

**Enforces**:
- AI returns advisories, not commands
- No workflow state mutations
- No artifact creation

**Scripts**:
- `python ci/ai_sandbox/check_ai_import_boundaries.py`
- `python ci/ai_sandbox/check_ai_forbidden_calls.py`
- `python ci/ai_sandbox/check_ai_write_paths.py`

**Status**: ✅ Already enforced in CI

---

### Profile 5: Saw Lab Encapsulation

**Prevents**: Saw Lab depending on RMOS/CAM internals

**Enforces**:
- Self-contained with own stage sequence
- Uses CAM Intent + HTTP (no direct imports)
- Reference implementation for OPERATION lane

**Script**: `python -m app.ci.check_saw_lab_encapsulation`

**Status**: ⚠️ Script needs creation (Saw Lab already follows pattern)

---

### Profile 6: Frontend SDK Boundary

**Prevents**: Raw fetch() calls in components

**Enforces**: Typed SDK helpers from `@/sdk/endpoints`

**Script**: `python scripts/ci/check_frontend_sdk_usage.py`

**Status**: ⚠️ Script needs creation (pattern documented)

---

### Profile 7: Artifact Authority

**Prevents**: Direct `RunArtifact()` construction bypassing validation

**Enforces**: Only `store.py` can create artifacts via `validate_and_persist()`

**Scripts**:
- `python ci/rmos/check_no_direct_runartifact.py`
- `python ci/ai_sandbox/check_rmos_completeness_guard.py`

**Status**: ✅ Already enforced in CI

---

### Profile 8: Legacy Deprecation

**Prevents**: Legacy endpoint usage growing unbounded

**Enforces**: Budget-based migration (current: 8/10 usages)

**Script**: `python -m app.ci.legacy_usage_gate --roots packages/client/src --budget 10`

**Status**: ✅ Already enforced in CI

---

## Integration Patterns

### Pattern 1: Artifact Contract

**Use**: Domain A consumes Domain B's output without code dependency

**Example**: ToolBox → Analyzer measurements

```
Producer writes JSON → Consumer reads JSON
SHA256 integrity      Schema validation
Manifest for discovery No Python imports
```

### Pattern 2: HTTP API Contract

**Use**: Domain A invokes Domain B's behavior

**Example**: RMOS → CAM toolpath generation

```
Client constructs intent → Server validates
POST /api/cam/roughing   Generates toolpaths
Parse result             Returns JSON
Persist artifact         No state mutation
```

### Pattern 3: SDK Adapter

**Use**: Frontend needs type-safe API access

**Example**: Component → CAM endpoint

```
Call typed helper         SDK constructs request
Await typed response      Parses headers
ApiError with context     Handles request-ID
```

---

## Enforcement Status

| Profile | CI Script Exists | CI Workflow | Blocking | Status |
|---------|-----------------|-------------|----------|--------|
| External boundary | ✅ Yes | `architecture_scan.yml` | ✅ Yes | Active |
| RMOS ↔ CAM | ⚠️ Template | `domain_boundaries.yml` | ⚠️ TBD | Needs script |
| Operation lane | ✅ Yes | `domain_boundaries.yml` | ✅ Yes | Active |
| AI sandbox | ✅ Yes (3) | `ai_sandbox_enforcement.yml` | ✅ Yes | Active |
| Saw Lab | ⚠️ Template | N/A | ⚠️ TBD | Needs script |
| Frontend SDK | ⚠️ Template | N/A | ⚠️ TBD | Needs script |
| Artifact authority | ✅ Yes (2) | `artifact_linkage_gate.yml` | ✅ Yes | Active |
| Legacy deprecation | ✅ Yes | `legacy_endpoint_usage_gate.yml` | ⚠️ Warning | Active |

**Legend**:
- ✅ Fully implemented and enforced
- ⚠️ Template/pattern provided, script needs creation
- ❌ Not started

---

## Next Steps

### Phase 1: Documentation (Complete)
- ✅ Create FENCE_REGISTRY.json
- ✅ Create FENCE_ARCHITECTURE.md
- ✅ Update copilot-instructions.md
- ✅ Add Makefile target

### Phase 2: Complete Enforcement Scripts
- ⚠️ Create `check_domain_boundaries.py --profile rmos_cam`
- ⚠️ Create `check_saw_lab_encapsulation.py`
- ⚠️ Create `check_frontend_sdk_usage.py`

### Phase 3: CI Workflow Integration
- Add `domain_boundaries.yml` workflow
- Update existing workflows to reference FENCE_REGISTRY.json
- Add fence health metrics to CI dashboard

### Phase 4: Pre-Commit Hooks
- Create `scripts/git-hooks/check-boundaries.sh`
- Document installation in README

---

## Usage

### Local Development

**Check all fences before commit**:
```bash
make check-boundaries
```

**Check specific fence**:
```bash
cd services/api
python -m app.ci.check_boundary_imports --profile toolbox
```

### CI Pipeline

All active fences run automatically on PR creation. Blocking fences prevent merge if violated.

### New Code

**Before importing across domains**:
1. Check FENCE_REGISTRY.json for allowed imports
2. If forbidden, use artifact contract or HTTP API
3. Document integration pattern in code comments
4. Run `make check-boundaries` locally

---

## Metrics

**Tracked**:
- Boundary violations per month
- Legacy endpoint usage count
- Artifact authority violations
- AI sandbox escape attempts

**Dashboard**: `reports/boundary_health.json` (generated by CI)

---

## References

| Document | Path |
|----------|------|
| **Fence Registry** | [FENCE_REGISTRY.json](../../FENCE_REGISTRY.json) |
| **Fence Documentation** | [FENCE_ARCHITECTURE.md](FENCE_ARCHITECTURE.md) |
| **AI Agent Guide** | [.github/copilot-instructions.md](../../.github/copilot-instructions.md) |
| **External Boundaries** | [BOUNDARY_RULES.md](../BOUNDARY_RULES.md) |
| **Operation Governance** | [OPERATION_EXECUTION_GOVERNANCE_v1.md](../OPERATION_EXECUTION_GOVERNANCE_v1.md) |
| **Saw Lab Guide** | [CNC_SAW_LAB_DEVELOPER_GUIDE.md](../CNC_SAW_LAB_DEVELOPER_GUIDE.md) |
| **Endpoint Truth Map** | [ENDPOINT_TRUTH_MAP.md](../ENDPOINT_TRUTH_MAP.md) |
| **SDK Patterns** | [packages/client/src/sdk/endpoints/README.md](../../packages/client/src/sdk/endpoints/README.md) |

---

## Success Criteria

✅ **Complete** when:
1. FENCE_REGISTRY.json defines all boundaries
2. FENCE_ARCHITECTURE.md documents patterns
3. All 8 fence profiles have enforcement scripts
4. CI blocks merges on fence violations
5. `make check-boundaries` runs locally
6. AI agents reference FENCE_REGISTRY.json
7. Legacy usage budget reaches 0

---

**Last Updated**: 2026-01-08  
**Maintainer**: Architecture Team  
**Review Cycle**: Quarterly
