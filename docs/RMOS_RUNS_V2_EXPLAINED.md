# RMOS Runs v2 - Purpose and Architecture

**Date:** December 18, 2025
**Status:** Production (v2 is default)
**Contract:** `docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md`

---

## What Are Run Artifacts?

When the system processes a manufacturing request (toolpath generation, feasibility check, etc.), it creates a **run artifact** - a permanent, immutable record of:

- **What was requested** - Design parameters, tool selection, material
- **The feasibility evaluation** - Is this safe to manufacture?
- **The decision** - OK (proceed), BLOCKED (unsafe), or ERROR
- **Verification hashes** - SHA256 checksums for integrity
- **Generated outputs** - G-code, toolpaths, operation plans

Run artifacts are your **audit trail for manufacturing safety**. They answer:
> "Why did the system approve/reject this job on this date?"

---

## The Problem: v1 Was Non-Compliant

The original implementation (`runs/`) didn't follow the governance contract:

| Requirement | Contract Specifies | v1 Implementation | Risk |
|-------------|-------------------|-------------------|------|
| **Schema** | Pydantic `BaseModel` | Python `@dataclass` | Can't enforce required fields |
| **Storage** | One file per run, date-partitioned | Single `runs.json` file | Doesn't scale, corruption risk |
| **Immutability** | Write-once, never modify | Had `patch_run_meta()` | Audit trail could be altered |
| **Required Fields** | `feasibility_sha256`, `risk_level` | Optional | Missing critical safety data |
| **Thread Safety** | Per-file atomic writes | Global file lock | Contention under load |

### Why This Matters

1. **Safety Compliance** - Manufacturing decisions need tamper-proof records
2. **Audit Requirements** - Must prove what the system decided and why
3. **Legal Liability** - If a job causes damage, records must be trustworthy
4. **Scalability** - Single JSON file becomes a bottleneck

---

## The Solution: runs_v2

A new module built to governance specifications:

```
services/api/app/rmos/runs_v2/
├── schemas.py          # Pydantic models with REQUIRED fields
├── store.py            # Date-partitioned, immutable storage
├── hashing.py          # Deterministic SHA256 hashing
├── attachments.py      # Content-addressed file storage
├── diff.py             # Compare two run artifacts
├── compat.py           # v1 ↔ v2 format conversion
├── migration_utils.py  # Data migration tools
├── api_runs.py         # REST API (9 endpoints)
├── cli_migrate.py      # Command-line migration tool
└── __init__.py         # Package exports
```

---

## Key Design Decisions

### 1. Pydantic Schemas with Required Fields

```python
class Hashes(BaseModel):
    feasibility_sha256: str  # REQUIRED - can't be None or empty
    toolpaths_sha256: Optional[str] = None
    gcode_sha256: Optional[str] = None

class RunDecision(BaseModel):
    risk_level: str  # REQUIRED - GREEN, YELLOW, RED, UNKNOWN, ERROR
    score: Optional[float] = None
    block_reason: Optional[str] = None
```

If you try to create a run without `feasibility_sha256` or `risk_level`, Pydantic raises a validation error. The system cannot create incomplete records.

### 2. Date-Partitioned Storage

```
services/api/data/runs/rmos/
├── 2025-12-17/
│   ├── run_abc123def456.json
│   └── run_def456789abc.json
├── 2025-12-18/
│   └── run_ghi789jkl012.json
└── 2025-12-19/
    └── ...
```

Benefits:
- Fast queries by date range
- Easy backup/archival of old partitions
- No single-file bottleneck
- Filesystem naturally handles concurrent access

### 3. Strict Immutability

Once a run artifact is written, it **cannot be modified**. Period.

```python
def put(self, artifact: RunArtifact) -> None:
    path = self._path_for(artifact.run_id, artifact.created_at_utc)
    if path.exists():
        raise ValueError(f"Artifact {artifact.run_id} already exists. "
                        "Run artifacts are immutable per governance contract.")
    # ... atomic write via .tmp + os.replace()
```

**What about adding notes or explanations later?**

Use **append-only advisory links**:

```python
# Creates a SEPARATE file, doesn't touch the original
store.attach_advisory(
    run_id="run_abc123",
    advisory_id="adv_explanation_001",
    kind="explanation",
    engine_id="claude-3-5-sonnet"
)
```

This creates `run_abc123_advisory_adv_explanation_001.json` alongside the original, preserving immutability while allowing additional context.

### 4. Atomic Writes

All writes use the temp-file-then-rename pattern:

```python
tmp = path.with_suffix(".json.tmp")
tmp.write_text(artifact.model_dump_json(indent=2))
os.replace(tmp, path)  # Atomic on all platforms
```

If the process crashes mid-write, you get either the old file or the new file - never a corrupted partial file.

---

## API Endpoints (v2)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/runs` | List with filtering |
| POST | `/runs` | Create new artifact (immutable) |
| GET | `/runs/{id}` | Get full details |
| GET | `/runs/diff?a={id}&b={id}` | Compare two runs |
| POST | `/runs/{id}/attach-advisory` | Add advisory link |
| GET | `/runs/{id}/advisories` | List attached advisories |
| GET | `/runs/{id}/attachments` | List file attachments |
| GET | `/runs/{id}/attachments/{sha256}` | Download attachment |
| GET | `/runs/{id}/attachments/verify` | Verify integrity |

**Removed from v2:**
- `PATCH /runs/{id}/meta` - Violated immutability

---

## Feature Flag

The implementation is controlled by an environment variable:

```bash
# v2 is the DEFAULT (no env var needed)
# System uses governance-compliant implementation automatically

# To rollback to v1 (emergency only)
export RMOS_RUNS_V2_ENABLED=false
```

---

## Migration CLI

If v1 data exists, migrate it:

```bash
# Check current status
python -m rmos.runs_v2.cli_migrate status

# Dry-run (validate without writing)
python -m rmos.runs_v2.cli_migrate migrate --dry-run

# Run actual migration
python -m rmos.runs_v2.cli_migrate migrate

# Verify migration
python -m rmos.runs_v2.cli_migrate verify
```

---

## File Locations

| Purpose | Path |
|---------|------|
| v2 Code | `services/api/app/rmos/runs_v2/` |
| v1 Code (legacy) | `services/api/app/rmos/runs/` |
| v2 Data Store | `services/api/data/runs/rmos/` |
| v1 Data Store | `services/api/app/data/runs.json` |
| Governance Contract | `docs/governance/RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md` |
| Migration Plan | `docs/RMOS_RUNS_GOVERNANCE_MIGRATION_PLAN.md` |

---

## Summary

| Aspect | v1 (Legacy) | v2 (Current) |
|--------|-------------|--------------|
| Schema | Dataclass | Pydantic with validation |
| Storage | Single `runs.json` | Date-partitioned files |
| Immutability | Could modify | Write-once only |
| Required Fields | Optional | Enforced |
| Thread Safety | Global lock | Atomic per-file |
| Advisory | N/A | Append-only links |
| Compliance | ❌ Non-compliant | ✅ Governance-compliant |

---

*Document created: December 18, 2025*
