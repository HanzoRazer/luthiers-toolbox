# RMOS Runs Governance Compliance Migration Plan

**Date:** December 18, 2025
**Status:** Approved - Implementation In Progress
**Contract Reference:** `docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md`

---

## Executive Summary

This plan migrates the RMOS Runs implementation from a non-compliant dataclass/single-file architecture to a governance-compliant Pydantic/date-partitioned architecture.

**Estimated Duration:** 2-3 weeks (phased approach)

**User Decisions:**
- Immutability: **Strict** - Remove `patch_run_meta()` entirely, use append-only advisory links

---

## Table of Contents

1. [Compliance Gap Summary](#compliance-gap-summary)
2. [Migration Strategy](#migration-strategy)
3. [Phase 0: Preparation](#phase-0-preparation)
4. [Phase 1: Schema Migration](#phase-1-schema-migration)
5. [Phase 2: Storage Layer](#phase-2-storage-layer)
6. [Phase 3: Data Migration](#phase-3-data-migration)
7. [Phase 4: API Router](#phase-4-api-router)
8. [Phase 5: Dependent Files](#phase-5-dependent-files)
9. [Phase 6: Cleanup](#phase-6-cleanup)
10. [Critical Files](#critical-files)
11. [Testing Requirements](#testing-requirements)
12. [Rollback Plan](#rollback-plan)

---

## Compliance Gap Summary

| Requirement | Current | Contract | Status |
|-------------|---------|----------|--------|
| Schema Type | `@dataclass` | `BaseModel` (Pydantic) | NON-COMPLIANT |
| Storage | Single `runs.json` | `{YYYY-MM-DD}/{run_id}.json` | NON-COMPLIANT |
| Immutability | `patch_run_meta()` modifies | Write-once | NON-COMPLIANT |
| `feasibility_sha256` | Optional | REQUIRED | NON-COMPLIANT |
| `risk_level` | Optional | REQUIRED | NON-COMPLIANT |
| Thread Safety | Global Lock | Per-file atomic | PARTIAL |
| Advisory Integration | Schema only | Full implementation | PARTIAL |

---

## Migration Strategy

### Dual-Write with Feature Flag

Create `runs_v2/` module alongside existing `runs/`, controlled by `RMOS_RUNS_V2_ENABLED` flag.

**Rationale:**
- 6 dependent files with production usage
- Complex data migration from single-file to partitioned
- Need to preserve attachments, diff, filtering, verification
- Rollback capability required at each phase

---

## Phase 0: Preparation

**Duration:** 1-2 days

### Tasks

1. Create new directory structure
2. Add feature flag `RMOS_RUNS_V2_ENABLED` (default: `false`)
3. Create module scaffolding

### Directory Structure

```
services/api/app/rmos/runs_v2/
├── __init__.py          # Package exports
├── schemas.py           # Pydantic models
├── store.py             # Date-partitioned storage
├── hashing.py           # Deterministic hashing
├── attachments.py       # Content-addressed storage
├── diff.py              # Run comparison
├── api_runs.py          # FastAPI router
├── compat.py            # v1 -> v2 conversion
└── migration_utils.py   # Data migration tools
```

### Rollback

Delete `runs_v2/` directory, remove feature flag.

---

## Phase 1: Schema Migration

**Duration:** 2-3 days

### File: `services/api/app/rmos/runs_v2/schemas.py`

### Key Changes

#### Hashes Model (Required Fields)
```python
class Hashes(BaseModel):
    feasibility_sha256: str  # REQUIRED (was Optional)
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None
    opplan_sha256: Optional[str] = None
```

#### RunDecision Model (Required Fields)
```python
class RunDecision(BaseModel):
    risk_level: str  # REQUIRED (was Optional)
    score: Optional[float] = None
    block_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
```

#### RunArtifact Model
```python
class RunArtifact(BaseModel):
    # Identity (REQUIRED)
    run_id: str
    created_at_utc: datetime

    # Context (REQUIRED)
    mode: str
    tool_id: str

    # Outcome (REQUIRED)
    status: Literal["OK", "BLOCKED", "ERROR"]

    # Inputs (REQUIRED)
    request_summary: Dict[str, Any]

    # Authoritative Data (REQUIRED)
    feasibility: Dict[str, Any]
    decision: RunDecision
    hashes: Hashes

    # Outputs
    outputs: RunOutputs = Field(default_factory=RunOutputs)

    # Advisory (append-only)
    advisory_inputs: List[AdvisoryInputRef] = Field(default_factory=list)

    # Legacy fields for backward compat
    attachments: Optional[List[RunAttachment]] = None
```

### Validation

- [ ] Pydantic rejects missing `feasibility_sha256`
- [ ] Pydantic rejects missing/empty `risk_level`
- [ ] Round-trip serialization preserves all fields

---

## Phase 2: Storage Layer

**Duration:** 2-3 days

### File: `services/api/app/rmos/runs_v2/store.py`

### Key Implementation

```python
class RunStoreV2:
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)

    def _date_partition(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d")

    def _path_for(self, run_id: str, created_at: datetime) -> Path:
        partition = self._date_partition(created_at)
        return self.root / partition / f"{run_id}.json"

    def put(self, artifact: RunArtifact) -> None:
        """Write-once. Raises if exists (immutability)."""
        path = self._path_for(artifact.run_id, artifact.created_at_utc)
        if path.exists():
            raise ValueError(f"Artifact {artifact.run_id} exists (immutable)")

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp, path)  # Atomic write

    def get(self, run_id: str) -> Optional[RunArtifact]:
        """Search across date partitions for run_id."""
        for partition in sorted(self.root.iterdir(), reverse=True):
            if partition.is_dir():
                path = partition / f"{run_id}.json"
                if path.exists():
                    return RunArtifact.model_validate_json(path.read_text())
        return None

    def attach_advisory(self, run_id: str, ref: AdvisoryInputRef) -> str:
        """
        Append-only advisory link (preserves immutability).

        Creates separate link file: {run_id}_advisory_{advisory_id}.json
        """
        # Implementation preserves original artifact immutability
```

### Storage Structure

```
{RMOS_RUNS_DIR}/
├── 2025-12-17/
│   ├── run_abc123def456.json
│   ├── run_abc123def456_advisory_adv_001.json  # Advisory link
│   └── run_def456789abc.json
├── 2025-12-18/
│   └── run_ghi789jkl012.json
└── _index.json (optional, for fast lookups)
```

### Validation

- [ ] Date partitions created automatically
- [ ] Duplicate write raises exception
- [ ] Atomic writes (no partial files)
- [ ] Advisory links don't modify original

---

## Phase 3: Data Migration

**Duration:** 1-2 days

### File: `services/api/app/rmos/runs_v2/migration_utils.py`

### Tasks

1. Backup existing `runs.json`
2. Convert each v1 artifact to v2 format
3. Write to date-partitioned structure
4. Validate migration counts

### Field Mapping

| v1 Field | v2 Field |
|----------|----------|
| `request_hash` | `hashes.feasibility_sha256` |
| `toolpaths_hash` | `hashes.toolpaths_sha256` |
| `gcode_hash` | `hashes.gcode_sha256` |
| `decision.risk_level` (if missing) | `"UNKNOWN"` |
| `attachments` | `attachments` (preserved) |

### Migration Script

```python
def migrate_v1_to_v2(
    v1_path: str = "services/api/app/data/runs.json",
    v2_root: str = "services/api/data/runs/rmos"
) -> MigrationReport:
    """
    One-time migration from v1 single-file to v2 date-partitioned.
    """
    # 1. Backup
    backup_path = backup_v1_store(v1_path)

    # 2. Load v1 data
    v1_data = json.load(open(v1_path))

    # 3. Convert and write
    store_v2 = RunStoreV2(v2_root)
    for run_id, raw in v1_data.items():
        artifact_v2 = convert_v1_to_v2(raw)
        store_v2.put(artifact_v2)

    return MigrationReport(...)
```

### Validation

- [ ] All v1 artifacts converted
- [ ] No data loss
- [ ] Dates correctly partitioned
- [ ] Backup created

---

## Phase 4: API Router

**Duration:** 2-3 days

### File: `services/api/app/rmos/runs_v2/api_runs.py`

### Endpoints

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| GET | `/runs` | List with filtering | Preserve |
| GET | `/runs/{run_id}` | Get artifact | Preserve |
| POST | `/runs` | Create artifact | Preserve |
| GET | `/runs/diff` | Compare runs | Preserve |
| GET | `/runs/{run_id}/attachments` | List attachments | Preserve |
| GET | `/runs/{run_id}/attachments/{sha256}` | Download | Preserve |
| GET | `/runs/{run_id}/attachments/verify` | Verify integrity | Preserve |
| POST | `/runs/{run_id}/attach-advisory` | Attach advisory | **NEW** |
| GET | `/runs/{run_id}/advisories` | List advisories | **NEW** |
| POST | `/runs/{run_id}/suggest-and-attach` | Generate explanation | **NEW** |
| ~~PATCH~~ | ~~`/runs/{run_id}/meta`~~ | ~~Update metadata~~ | **REMOVED** |

### Removed Endpoints (Strict Immutability)

```python
# REMOVED per user decision - strict immutability
# @router.patch("/{run_id}/meta")
# def patch_meta(...):
#     """REMOVED: Run artifacts are immutable."""
```

### Validation

- [ ] All preserved endpoints work
- [ ] New advisory endpoints work
- [ ] Removed endpoints return appropriate error

---

## Phase 5: Dependent Files

**Duration:** 1-2 days

### Files to Update (6 total)

#### 1. `services/api/app/main.py` (line 247)

```python
# Conditional import based on feature flag
import os
if os.getenv("RMOS_RUNS_V2_ENABLED", "false").lower() == "true":
    from .rmos.runs_v2.api_runs import router as rmos_runs_router
else:
    from .rmos.runs.api_runs import router as rmos_runs_router
```

#### 2. `services/api/app/rmos/__init__.py` (lines 91-100)

```python
# Conditional re-exports
if os.getenv("RMOS_RUNS_V2_ENABLED", "false").lower() == "true":
    from .runs_v2 import (
        RunArtifact,
        RunDecision,
        Hashes,
        # ... v2 exports
    )
else:
    from .runs import (
        # ... v1 exports
    )
```

#### 3. `services/api/app/rmos/rosette_rmos_adapter.py`

- Update schema imports
- Use v2 store when enabled

#### 4. `services/api/app/rmos/api/rmos_toolpaths_router.py`

- Update imports
- Ensure required fields populated

### Validation

- [ ] Feature flag switches behavior
- [ ] No import errors in either mode
- [ ] End-to-end workflows work

---

## Phase 6: Cleanup

**Duration:** 1 day

### Tasks

1. Set `RMOS_RUNS_V2_ENABLED=true` as default
2. Rename modules:
   - `runs/` → `runs_legacy/`
   - `runs_v2/` → `runs/`
3. Remove feature flag conditionals
4. Update all imports to canonical paths
5. Update documentation

### Validation

- [ ] v2 works without feature flag
- [ ] No references to `runs_legacy/`
- [ ] All tests pass

---

## Critical Files

| File | Lines | Purpose |
|------|-------|---------|
| `services/api/app/rmos/runs/schemas.py` | 141 | Source: dataclass schemas |
| `services/api/app/rmos/runs/store.py` | 196 | Source: single-file store |
| `services/api/app/rmos/runs/api_runs.py` | 374 | Source: API endpoints |
| `docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md` | 431 | Contract: compliance requirements |
| `docs/Runs_Advisory_Integration/schemas.py` | 73 | Template: Pydantic models |
| `docs/Runs_Advisory_Integration/store.py` | 115 | Template: per-file storage |
| `docs/Runs_Advisory_Integration/router.py` | 243 | Template: advisory endpoints |

---

## Features Summary

### Features to Preserve

- [x] Content-addressed attachments (`attachments.py`)
- [x] Run diffing with severity (`diff.py`)
- [x] Multi-field filtering (`list_runs_filtered`)
- [x] SHA256 verification (`verify_run_attachments`)
- [x] Thread safety (via `filelock` for per-file)

### Features to Add

- [ ] Date-partitioned storage
- [ ] Pydantic validation with required fields
- [ ] Immutable artifacts (write-once)
- [ ] `attach_advisory()` - append-only pattern
- [ ] `suggest-and-attach` - explanation generation
- [ ] Advisory listing endpoint

### Features Removed

- [x] `patch_run_meta()` - violates immutability
- [x] `PATCH /runs/{id}/meta` endpoint - violates immutability

---

## Testing Requirements

### Unit Tests

- [ ] Pydantic validation rejects missing required fields
- [ ] `feasibility_sha256` cannot be None or empty
- [ ] `risk_level` cannot be None or empty
- [ ] Serialization/deserialization round-trips

### Integration Tests

- [ ] Date partitions created correctly
- [ ] Duplicate write raises exception (immutability)
- [ ] Advisory links created without modifying original
- [ ] API backward compatibility maintained

### Migration Tests

- [ ] All v1 artifacts converted to v2
- [ ] Field mapping correct
- [ ] Attachments preserved
- [ ] Backup created before migration

### Chaos Tests

- [ ] Thread safety under concurrent access
- [ ] Atomic writes survive process crash

---

## Rollback Plan

### Phase-by-Phase Rollback

| Phase | Rollback Action |
|-------|-----------------|
| 0-5 | Set `RMOS_RUNS_V2_ENABLED=false` |
| 6 | Restore `runs_legacy/` → `runs/` |

### Data Rollback

1. Stop API server
2. Restore `runs.json` from backup
3. Set `RMOS_RUNS_V2_ENABLED=false`
4. Restart API server

---

## Timeline Summary

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Preparation | 1-2 days | 1-2 days |
| Phase 1: Schema Migration | 2-3 days | 3-5 days |
| Phase 2: Storage Layer | 2-3 days | 5-8 days |
| Phase 3: Data Migration | 1-2 days | 6-10 days |
| Phase 4: API Router | 2-3 days | 8-13 days |
| Phase 5: Dependent Files | 1-2 days | 9-15 days |
| Phase 6: Cleanup | 1 day | 10-16 days |

**Total Estimated Duration: 2-3 weeks**

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | PLAN-RMOS-RUNS-MIG-001 |
| Classification | Internal - Engineering |
| Owner | RMOS Architecture Team |
| Created | December 18, 2025 |
| Status | Approved - Implementation In Progress |

---

*Document generated: December 18, 2025*
