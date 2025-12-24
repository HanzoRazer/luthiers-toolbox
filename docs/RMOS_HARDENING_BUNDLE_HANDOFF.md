# RMOS Hardening Bundle — Developer Handoff

**Document Version:** 1.0
**Created:** 2025-12-23
**Audited By:** Claude Code
**Target Bundles:** H1, H2, H3

---

## Executive Summary

This document provides implementation guidance for remaining gaps in the RMOS Hardening Bundle. An audit was performed against the bundle specifications, and **~85% of the work is already complete**. This handoff covers the remaining patches needed.

### Quick Reference: What Needs Patching

| Priority | Component | Effort | Files to Create/Modify |
|----------|-----------|--------|------------------------|
| **P1** | CI verify_store gate | 5 min | `.github/workflows/rmos_ci.yml` |
| **P2** | Advisory summaries schema | 30 min | `runs_v2/schemas_summaries.py` (NEW) |
| **P2** | Advisory summaries endpoint | 30 min | `workflow/sessions/routes.py` |
| **P3** | SVG text blob helper | 15 min | `runs_v2/attachments.py` |
| **P3** | Variant SHA in responses | 30 min | `runs_v2/advisory_blob_service.py` |
| **P3** | Repair/Index CLI | 1 hr | `runs_v2/cli_repair.py` (NEW) |

---

## Part 1: Already Implemented (Do Not Duplicate)

Before patching, understand what already exists to avoid duplication.

### H1 Components — Complete

| Component | Location | Notes |
|-----------|----------|-------|
| Request ID ContextVar | `app/util/request_context.py` | Includes `new_request_id()`, `require_request_id()`, `clear_request_id()` |
| RequestIdMiddleware | `app/main.py:47-76` | Honors `X-Request-Id` header, sets ContextVar |
| Logging filter | `app/util/logging_request_id.py` | Injects `%(request_id)s` into log records |
| RunArtifact provenance | `app/rmos/runs_v2/api_runs.py:187,228` | `request_id` stored in artifact meta |
| Engine compute_ms | `app/rmos/engines/base.py:50-56` | Required in `FeasibilityEngine` protocol |
| count_runs_filtered() | `app/rmos/runs_v2/store.py:857` | Efficient count without full deserialization |
| Pytest ContextVar cleanup | `tests/conftest.py:140-153` | `clear_request_id()` called before/after each test |

### H2 Components — Complete

| Component | Location | Notes |
|-----------|----------|-------|
| Split store | `app/rmos/runs_v2/store.py` | Date-partitioned: `{root}/{YYYY-MM-DD}/{run_id}.json` |
| Migration CLI | `app/rmos/runs_v2/cli_migrate.py` | Commands: `status`, `migrate`, `verify`, `rollback` |
| Cursor pagination | `app/rmos/runs_v2/store.py` | Base64-encoded cursor with `created_at_utc|run_id` |
| Cascade delete | `app/workflow/sessions/routes.py:125-171` | `force` and `cascade` query params |
| verify_store CLI | `app/rmos/runs_v2/verify_store.py` | Strict mode is default, `--no-strict` to disable |

### H3 Components — Complete

| Component | Location | Notes |
|-----------|----------|-------|
| Content-addressed attachments | `app/rmos/runs_v2/attachments.py` | SHA256-keyed, two-level directory sharding |
| `put_bytes_attachment()` | `attachments.py:47-92` | Deduplicates by content hash |
| `put_text_attachment()` | `attachments.py:95+` | Text variant of above |

---

## Part 2: Gap Patches Required

### Gap 1: CI verify_store Gate (H1)

**Priority:** P1 (Critical — prevents broken stores from merging)
**Effort:** 5 minutes
**File:** `.github/workflows/rmos_ci.yml`

#### Context

The `verify_store.py` CLI exists and works correctly. It just needs to be wired into CI so broken stores fail the build.

#### Implementation

Add this step **after** the pytest step (around line 62):

```yaml
      - name: Verify RMOS runs_v2 store integrity
        working-directory: services/api
        env:
          RMOS_RUNS_DIR: ${{ runner.temp }}/rmos_runs
        run: |
          echo "Verifying runs_v2 store integrity..."
          python -m app.rmos.runs_v2.verify_store
```

#### Why This Location

- The pytest step at line 55-61 already sets up `RMOS_RUNS_DIR`
- verify_store uses the same env var
- Runs after tests so we verify the post-test state

#### Acceptance Criteria

- [ ] CI fails if `verify_store` exits non-zero
- [ ] CI passes on clean store
- [ ] Step appears in GitHub Actions logs

---

### Gap 2: Advisory Summaries Schema (H2)

**Priority:** P2 (Enables fast session views)
**Effort:** 30 minutes
**File:** `services/api/app/rmos/runs_v2/schemas_summaries.py` (NEW)

#### Context

The current `/{session_id}/runs` endpoint returns basic run info. The bundle spec calls for a richer "advisory summary" that includes decision fields (risk_level, score, block_reason) without loading full artifacts.

#### Implementation

Create new file:

```python
# services/api/app/rmos/runs_v2/schemas_summaries.py
"""
Advisory Summary Schemas for RMOS Runs.

Lightweight representations of run artifacts for fast list views.
Includes decision/risk fields without full payload.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RunAdvisorySummary(BaseModel):
    """
    Lightweight summary of a run artifact for list views.

    Includes governance-relevant fields without full payload.
    Used by workflow session views and advisory dashboards.
    """
    # Identity
    run_id: str
    created_at_utc: str

    # Status
    status: Optional[str] = None
    event_type: Optional[str] = None

    # Decision fields (from artifact.decision)
    risk_level: Optional[str] = Field(
        None,
        description="GREEN/YELLOW/RED/ERROR"
    )
    score: Optional[float] = Field(
        None,
        description="Feasibility score 0-100"
    )
    block_reason: Optional[str] = Field(
        None,
        description="If blocked, why"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )

    # Explanation fields (if AI explanation attached)
    explanation_status: Optional[str] = Field(
        None,
        description="pending/complete/failed"
    )
    explanation_summary: Optional[str] = Field(
        None,
        description="First ~200 chars of explanation"
    )

    # Provenance
    request_id: Optional[str] = None
    compute_ms: Optional[float] = None

    # Flexible metadata (for UI customization)
    meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_abc123def456",
                "created_at_utc": "2025-12-23T10:30:00Z",
                "status": "OK",
                "event_type": "feasibility_check",
                "risk_level": "GREEN",
                "score": 87.5,
                "block_reason": None,
                "warnings": ["High spindle speed for this material"],
                "request_id": "req_1234567890abcdef",
                "compute_ms": 45.2
            }
        }


class RunAdvisorySummaryPage(BaseModel):
    """Paginated response for advisory summaries."""
    items: List[RunAdvisorySummary]
    next_cursor: Optional[str] = None
    total: Optional[int] = Field(
        None,
        description="Total count (only if include_total=true)"
    )
```

#### Mapping Guide

When extracting from `RunArtifact`:

| Summary Field | Source Path in RunArtifact |
|---------------|---------------------------|
| `risk_level` | `artifact.decision.risk_level` |
| `score` | `artifact.decision.score` |
| `block_reason` | `artifact.decision.block_reason` |
| `warnings` | `artifact.decision.warnings` |
| `explanation_status` | `artifact.meta.get("explanation_status")` |
| `explanation_summary` | `artifact.meta.get("explanation_summary", "")[:200]` |
| `request_id` | `artifact.meta.get("request_id")` or `artifact.request_id` |
| `compute_ms` | `artifact.meta.get("compute_ms")` |

#### Acceptance Criteria

- [ ] Schema validates with Pydantic v2
- [ ] Example in schema is accurate
- [ ] Imported successfully in routes.py

---

### Gap 3: Advisory Summaries Endpoint (H2)

**Priority:** P2
**Effort:** 30 minutes
**File:** `services/api/app/workflow/sessions/routes.py`

#### Context

Modify the existing `/{session_id}/runs` endpoint to support a `view` parameter that switches between full artifacts and lightweight summaries.

#### Current Implementation (lines 202-257)

The endpoint currently returns a simplified dict with basic fields. We need to add `view=summary` support.

#### Implementation

**Step 1:** Add import at top of file:

```python
from app.rmos.runs_v2.schemas_summaries import RunAdvisorySummary, RunAdvisorySummaryPage
```

**Step 2:** Add helper function (before the endpoint):

```python
def _extract_advisory_summary(artifact) -> RunAdvisorySummary:
    """
    Extract lightweight summary from a RunArtifact.

    Handles both Pydantic models and dicts.
    """
    # Normalize to dict
    if hasattr(artifact, "model_dump"):
        raw = artifact.model_dump()
    elif hasattr(artifact, "__dict__"):
        raw = artifact.__dict__
    else:
        raw = dict(artifact)

    decision = raw.get("decision") or {}
    meta = raw.get("meta") or {}

    # Extract explanation summary (truncate to 200 chars)
    explanation_full = meta.get("explanation_summary") or meta.get("explanation", "")
    explanation_summary = explanation_full[:200] if explanation_full else None

    return RunAdvisorySummary(
        run_id=raw.get("run_id"),
        created_at_utc=(
            raw.get("created_at_utc").isoformat()
            if hasattr(raw.get("created_at_utc"), "isoformat")
            else raw.get("created_at_utc")
        ),
        status=raw.get("status"),
        event_type=raw.get("event_type"),
        risk_level=decision.get("risk_level"),
        score=decision.get("score"),
        block_reason=decision.get("block_reason"),
        warnings=decision.get("warnings") or [],
        explanation_status=meta.get("explanation_status"),
        explanation_summary=explanation_summary,
        request_id=meta.get("request_id") or raw.get("request_id"),
        compute_ms=meta.get("compute_ms"),
        meta={k: v for k, v in meta.items() if k not in ("explanation", "explanation_summary")},
    )
```

**Step 3:** Modify endpoint signature (line 202-209):

```python
@router.get("/{session_id}/runs")
def list_runs_for_session(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    include_total: bool = Query(False, description="Include total count (may be slower)"),
    view: str = Query("default", description="Response format: 'default' or 'summary'"),
):
```

**Step 4:** Add summary branch in response logic (before the return statement):

```python
    # If summary view requested, extract lightweight summaries
    if view == "summary":
        summaries = [_extract_advisory_summary(r) for r in runs]
        response = {
            "session_id": session_id,
            "items": [s.model_dump() for s in summaries],
            "limit": limit,
            "offset": offset,
            "count": len(summaries),
        }
        if include_total and count_runs_v2 is not None:
            response["total"] = count_runs_v2(workflow_session_id=session_id, status=status)
        return response

    # Default view (existing logic continues below)
    return {
        "session_id": session_id,
        "runs": [
            # ... existing code ...
        ],
        ...
    }
```

#### Acceptance Criteria

- [ ] `GET /workflow-sessions/{id}/runs` returns existing format by default
- [ ] `GET /workflow-sessions/{id}/runs?view=summary` returns `RunAdvisorySummary` items
- [ ] Summary includes `risk_level`, `score`, `block_reason` when available
- [ ] `explanation_summary` is truncated to 200 chars
- [ ] Existing tests still pass

---

### Gap 4: SVG Text Blob Helper (H3)

**Priority:** P3
**Effort:** 15 minutes
**File:** `services/api/app/rmos/runs_v2/attachments.py`

#### Context

The attachments module has `put_text_attachment()` but needs a specialized SVG helper that:
1. Validates SVG content
2. Uses appropriate MIME type
3. Returns `variant_sha256` for deduplication tracking

#### Implementation

Add at end of `attachments.py`:

```python
def put_svg_attachment(
    svg_text: str,
    *,
    kind: str = "svg_variant",
    filename: str = "variant.svg",
    validate: bool = True,
) -> Tuple[RunAttachment, str, str]:
    """
    Store SVG text as a content-addressed attachment.

    Args:
        svg_text: SVG content (must start with '<svg' or '<?xml')
        kind: Attachment type (default: svg_variant)
        filename: Display filename
        validate: If True, perform basic SVG validation

    Returns:
        Tuple of (RunAttachment, storage_path, variant_sha256)

    Raises:
        ValueError: If validate=True and content doesn't look like SVG
    """
    if validate:
        stripped = svg_text.strip()
        if not (stripped.startswith("<svg") or stripped.startswith("<?xml")):
            raise ValueError("Content does not appear to be SVG (must start with <svg or <?xml)")
        if "</svg>" not in stripped:
            raise ValueError("Content does not appear to be valid SVG (missing </svg>)")

    # Compute SHA before storage for return value
    variant_sha256 = sha256_of_text(svg_text)

    # Store using existing text attachment logic
    attachment, path = put_text_attachment(
        text=svg_text,
        kind=kind,
        mime="image/svg+xml",
        filename=filename,
        ext=".svg",
    )

    return attachment, path, variant_sha256


def get_svg_by_sha(sha256: str) -> Optional[str]:
    """
    Retrieve SVG content by its SHA256 hash.

    Args:
        sha256: Content hash

    Returns:
        SVG text content, or None if not found
    """
    path = _path_for_sha(sha256, ".svg")
    if not path.exists():
        # Try without extension (some older attachments)
        path = _path_for_sha(sha256, "")
        if not path.exists():
            return None

    return path.read_text(encoding="utf-8")
```

#### Acceptance Criteria

- [ ] `put_svg_attachment()` validates SVG content
- [ ] Returns `variant_sha256` for tracking
- [ ] `get_svg_by_sha()` retrieves stored SVG
- [ ] Deduplication works (same SVG = same SHA = single file)

---

### Gap 5: Variant SHA in Prompt→SVG Responses (H3)

**Priority:** P3
**Effort:** 30 minutes
**File:** `services/api/app/rmos/runs_v2/advisory_blob_service.py`

#### Context

When generating SVG variants from prompts, the response should include:
- `variant_sha256`: Content hash for deduplication/caching
- `variant_seed`: Random seed used (if applicable) for reproducibility

#### Implementation Guide

**Step 1:** Find the function that generates/returns SVG content (look for `generate_svg` or similar).

**Step 2:** Modify the response to include:

```python
from .attachments import put_svg_attachment

# In your SVG generation function:
def generate_advisory_svg(prompt: str, seed: Optional[int] = None, ...):
    # ... existing SVG generation logic ...
    svg_content = "..."  # generated SVG

    # Store and get SHA
    attachment, path, variant_sha256 = put_svg_attachment(
        svg_text=svg_content,
        kind="advisory_svg",
        filename=f"advisory_{variant_sha256[:8]}.svg",
    )

    return {
        "svg": svg_content,
        "variant_sha256": variant_sha256,
        "variant_seed": seed,
        "attachment": attachment.model_dump(),
        # ... other fields ...
    }
```

**Step 3:** Update response schema if one exists to include new fields.

#### Acceptance Criteria

- [ ] SVG generation response includes `variant_sha256`
- [ ] SVG generation response includes `variant_seed` (if seeded generation)
- [ ] Same prompt + seed produces same `variant_sha256`
- [ ] SVG is stored via `put_svg_attachment()` for deduplication

---

### Gap 6: Repair/Index CLI (H3)

**Priority:** P3
**Effort:** 1 hour
**File:** `services/api/app/rmos/runs_v2/cli_repair.py` (NEW)

#### Context

The bundle calls for a repair CLI that can:
1. Rebuild index from partition files
2. Detect orphaned artifacts (in filesystem but not index)
3. Detect missing artifacts (in index but not filesystem)
4. Optionally repair drift

#### Implementation

```python
#!/usr/bin/env python3
"""
RMOS Runs Store Repair CLI

Commands:
    status    - Report index/artifact health
    rebuild   - Rebuild index from partition files
    orphans   - List artifacts not in index
    repair    - Fix index/artifact drift

Usage:
    python -m app.rmos.runs_v2.cli_repair status
    python -m app.rmos.runs_v2.cli_repair rebuild --dry-run
    python -m app.rmos.runs_v2.cli_repair repair --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any

from .store import RunStoreV2, _get_store_root
from .verify_store import verify


def cmd_status(args: argparse.Namespace) -> int:
    """Report current store health."""
    print("=" * 60)
    print("RMOS Runs Store Health Report")
    print("=" * 60)

    ok, report = verify(strict_deserialize=not args.quick)

    print(f"\nStore root: {report['store_root']}")
    print(f"Index exists: {'Yes' if report['index_exists'] else 'No'}")
    print(f"Indexed runs: {report['indexed_runs']}")

    # Count orphans
    store = RunStoreV2()
    orphans = _find_orphan_artifacts(store)
    print(f"Orphan artifacts: {len(orphans)}")

    print(f"\nMissing artifacts: {len(report['missing_artifacts'])}")
    print(f"Partition mismatches: {len(report['partition_mismatches'])}")
    print(f"Deserialize failures: {len(report['deserialize_failures'])}")

    health = "HEALTHY" if (ok and len(orphans) == 0) else "NEEDS_ATTENTION"
    print(f"\nOverall: {health}")
    print("=" * 60)

    return 0 if health == "HEALTHY" else 1


def cmd_rebuild(args: argparse.Namespace) -> int:
    """Rebuild index from partition artifacts."""
    store = RunStoreV2()

    print("=" * 60)
    print("RMOS Runs Index Rebuild")
    print("=" * 60)
    print(f"\nStore root: {store.root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    if args.dry_run:
        # Just count what would be indexed
        count = 0
        for partition_dir in store.root.iterdir():
            if partition_dir.is_dir() and not partition_dir.name.startswith("_"):
                count += len(list(partition_dir.glob("*.json")))
        print(f"\nWould index {count} artifacts")
        return 0

    count = store.rebuild_index()
    print(f"\nRebuilt index with {count} artifacts")
    print("=" * 60)
    return 0


def cmd_orphans(args: argparse.Namespace) -> int:
    """List orphan artifacts (not in index)."""
    store = RunStoreV2()
    orphans = _find_orphan_artifacts(store)

    print("=" * 60)
    print("RMOS Orphan Artifacts")
    print("=" * 60)
    print(f"\nFound {len(orphans)} orphan(s)")

    for path in orphans[:50]:
        print(f"  - {path.relative_to(store.root)}")

    if len(orphans) > 50:
        print(f"  ... and {len(orphans) - 50} more")

    if orphans and args.delete:
        if not args.yes:
            confirm = input("\nDelete orphans? [y/N]: ")
            if confirm.lower() != "y":
                print("Cancelled.")
                return 1

        deleted = 0
        for path in orphans:
            try:
                path.unlink()
                deleted += 1
            except Exception as e:
                print(f"  Failed to delete {path}: {e}")
        print(f"\nDeleted {deleted} orphan(s)")

    print("=" * 60)
    return 0


def cmd_repair(args: argparse.Namespace) -> int:
    """Repair index/artifact drift."""
    store = RunStoreV2()

    print("=" * 60)
    print("RMOS Runs Store Repair")
    print("=" * 60)
    print(f"\nStore root: {store.root}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")

    # Step 1: Rebuild index to capture all artifacts
    print("\n[Step 1] Rebuilding index from partitions...")
    if not args.dry_run:
        count = store.rebuild_index()
        print(f"  Indexed {count} artifacts")
    else:
        print("  (skipped in dry-run)")

    # Step 2: Verify after rebuild
    print("\n[Step 2] Verifying store integrity...")
    ok, report = verify(strict_deserialize=True)

    if report["missing_artifacts"]:
        print(f"  WARNING: {len(report['missing_artifacts'])} artifacts still missing")
        print("  (these are in index but files don't exist)")

        if args.remove_missing and not args.dry_run:
            # Remove missing entries from index
            index = store._read_index()
            for run_id in report["missing_artifacts"]:
                index.pop(run_id, None)
            store._write_index(index)
            print(f"  Removed {len(report['missing_artifacts'])} missing entries from index")

    # Step 3: Handle orphans
    orphans = _find_orphan_artifacts(store)
    if orphans:
        print(f"\n[Step 3] Found {len(orphans)} orphan artifacts")
        if args.index_orphans and not args.dry_run:
            # Re-run rebuild to pick them up
            store.rebuild_index()
            print("  Re-indexed to capture orphans")

    print("\n" + "=" * 60)
    print("Repair complete. Run 'status' to verify.")
    print("=" * 60)
    return 0


def _find_orphan_artifacts(store: RunStoreV2) -> List[Path]:
    """Find artifacts not referenced in index."""
    index = store._read_index()
    indexed_ids: Set[str] = set(index.keys())

    orphans: List[Path] = []
    for partition_dir in store.root.iterdir():
        if not partition_dir.is_dir() or partition_dir.name.startswith("_"):
            continue

        for artifact_file in partition_dir.glob("*.json"):
            run_id = artifact_file.stem
            if run_id not in indexed_ids:
                orphans.append(artifact_file)

    return orphans


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RMOS Runs Store Repair CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # status
    status_p = subparsers.add_parser("status", help="Report store health")
    status_p.add_argument("--quick", action="store_true", help="Skip deserialization checks")
    status_p.set_defaults(func=cmd_status)

    # rebuild
    rebuild_p = subparsers.add_parser("rebuild", help="Rebuild index from artifacts")
    rebuild_p.add_argument("--dry-run", action="store_true", help="Show what would be done")
    rebuild_p.set_defaults(func=cmd_rebuild)

    # orphans
    orphans_p = subparsers.add_parser("orphans", help="List orphan artifacts")
    orphans_p.add_argument("--delete", action="store_true", help="Delete orphans")
    orphans_p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    orphans_p.set_defaults(func=cmd_orphans)

    # repair
    repair_p = subparsers.add_parser("repair", help="Repair store drift")
    repair_p.add_argument("--dry-run", action="store_true", help="Show what would be done")
    repair_p.add_argument("--remove-missing", action="store_true", help="Remove missing entries from index")
    repair_p.add_argument("--index-orphans", action="store_true", help="Add orphans to index")
    repair_p.set_defaults(func=cmd_repair)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

#### Acceptance Criteria

- [ ] `python -m app.rmos.runs_v2.cli_repair status` shows health report
- [ ] `python -m app.rmos.runs_v2.cli_repair rebuild --dry-run` shows what would be indexed
- [ ] `python -m app.rmos.runs_v2.cli_repair orphans` lists unindexed artifacts
- [ ] `python -m app.rmos.runs_v2.cli_repair repair --dry-run` shows repair plan
- [ ] All commands exit with appropriate codes (0=healthy, 1+=issues)

---

## Part 3: Testing Guide

### Running Existing Tests

```bash
cd services/api

# Run all RMOS tests
python -m pytest tests/test_rmos*.py -v

# Run specific test files
python -m pytest tests/test_runs_v2_split_store.py -v
python -m pytest tests/test_runs_filter_by_batch_label.py -v

# Run with coverage
python -m pytest tests/ --cov=app/rmos --cov-report=html
```

### Testing Your Patches

#### Gap 1: CI Gate
```bash
# Simulate CI locally
cd services/api
python -m app.rmos.runs_v2.verify_store
echo $?  # Should be 0 on healthy store
```

#### Gap 2: Advisory Summaries
```bash
# Start server
uvicorn app.main:app --reload

# Test endpoint
curl "http://localhost:8000/api/workflow-sessions/{session_id}/runs?view=summary"
```

#### Gap 4-5: SVG Helpers
```python
# In Python REPL
from app.rmos.runs_v2.attachments import put_svg_attachment, get_svg_by_sha

svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle r="10"/></svg>'
att, path, sha = put_svg_attachment(svg)
print(f"Stored at: {path}, SHA: {sha}")

retrieved = get_svg_by_sha(sha)
assert retrieved == svg
```

#### Gap 6: Repair CLI
```bash
python -m app.rmos.runs_v2.cli_repair status
python -m app.rmos.runs_v2.cli_repair rebuild --dry-run
python -m app.rmos.runs_v2.cli_repair orphans
```

---

## Part 4: Code Style & Conventions

### Imports
```python
# Standard library first
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party
from pydantic import BaseModel, Field

# Local imports (relative preferred within package)
from .store import RunStoreV2
from .schemas import RunArtifact
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)

# Use structured logging
logger.info("run_created run_id=%s request_id=%s", run_id, request_id)
```

### Error Handling
```python
# Use specific exceptions
from fastapi import HTTPException

raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "run_id": run_id})
```

### Type Hints
```python
# Always use type hints
def process(data: Dict[str, Any], *, strict: bool = True) -> Optional[str]:
    ...
```

---

## Part 5: File Checklist

### Files to Create
- [ ] `services/api/app/rmos/runs_v2/schemas_summaries.py`
- [ ] `services/api/app/rmos/runs_v2/cli_repair.py`

### Files to Modify
- [ ] `.github/workflows/rmos_ci.yml` — Add verify step
- [ ] `services/api/app/workflow/sessions/routes.py` — Add view=summary
- [ ] `services/api/app/rmos/runs_v2/attachments.py` — Add SVG helpers
- [ ] `services/api/app/rmos/runs_v2/advisory_blob_service.py` — Add variant_sha256

### Files Already Modified (Reference Only)
- `services/api/app/util/request_context.py` — Helper functions added
- `services/api/tests/conftest.py` — Uses `clear_request_id()`

---

## Appendix: Bundle Source Reference

The original bundle specifications are in:
```
C:\Users\thepr\Downloads\luthiers-toolbox\RMOS Hardening Bundle H1.txt
```

This contains H1, H2, and H3 bundle specs with full code examples.
