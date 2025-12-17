# Run Artifact Index + Query API Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 17, 2025
**Status:** AUTHORITATIVE
**Precedence:** PRIMARY - All implementations MUST conform
**Dependency:** RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

---

## Governance Statement

This document establishes the **canonical contract** for querying and retrieving Run Artifacts within the Luthier's ToolBox RMOS. All query endpoints MUST conform to the specifications herein. Deviation from this contract is prohibited without formal amendment through the governance review process.

### Governing Principles

1. **Complete Queryability** — All persisted artifacts MUST be retrievable via API
2. **Consistent Filtering** — Filter parameters work identically across all queries
3. **Secure Access** — Path traversal attacks MUST be rejected
4. **Pagination Support** — Large result sets MUST be paginated
5. **Audit Download** — Any artifact MUST be downloadable as JSON

### Subordinate Documents

All implementation documents, guides, and code related to artifact querying are subordinate to this contract.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Query endpoint specifications | Artifact creation logic |
| Filter parameter definitions | UI components for display |
| Pagination contract | Retention and purge policies |
| Security requirements | Cross-system federation |

---

## API Endpoints Specification

### Endpoint Summary

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/rmos/runs` | List artifacts with filters + pagination |
| `GET` | `/api/rmos/runs/{run_id}` | Fetch single artifact |
| `GET` | `/api/rmos/runs/{run_id}/download` | Download artifact as JSON file |

---

## List Endpoint Contract

### `GET /api/rmos/runs`

#### Query Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `status` | string | `OK`, `BLOCKED`, `ERROR` | Filter by run outcome |
| `mode` | string | `saw`, `router`, etc. | Filter by processing mode |
| `tool_id_prefix` | string | e.g., `saw:` | Filter by tool_id prefix |
| `risk_level` | string | `GREEN`, `YELLOW`, `RED`, `UNKNOWN` | Filter by safety decision |
| `date_from` | string | `YYYY-MM-DD` | Runs on or after this date |
| `date_to` | string | `YYYY-MM-DD` | Runs on or before this date |
| `limit` | integer | 1-200 (default: 50) | Max results per page |
| `cursor` | string | opaque | Pagination cursor |

#### Response Schema

```json
{
  "items": [
    {
      "run_id": "string",
      "created_at_utc": "string (ISO 8601)",
      "status": "OK | BLOCKED | ERROR",
      "mode": "string",
      "tool_id": "string",
      "risk_level": "GREEN | YELLOW | RED | UNKNOWN",
      "score": "number | null",
      "feasibility_sha256": "string",
      "toolpaths_sha256": "string | null",
      "artifact_path": "string"
    }
  ],
  "next_cursor": "string | null",
  "runs_dir": "string"
}
```

#### Pagination Contract

- Cursor format: `{YYYY-MM-DD}|{filename.json}` (opaque to client)
- Results ordered newest-first by default
- `next_cursor` is `null` when no more results exist
- Cursor MUST be passed unchanged to continue pagination

---

## Single Artifact Endpoint Contract

### `GET /api/rmos/runs/{run_id}`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string | UUID hex identifier |

#### Response Schema

Full `RunArtifact` object as defined in RUN_ARTIFACT_PERSISTENCE_CONTRACT_v1.md

#### Error Responses

| Status | Condition | Response |
|--------|-----------|----------|
| 404 | Run not found | `{"error": "RUN_NOT_FOUND", "run_id": "..."}` |

---

## Download Endpoint Contract

### `GET /api/rmos/runs/{run_id}/download`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string | UUID hex identifier |

#### Response

- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="{run_id}.json"`
- Body: Raw artifact JSON file

#### Error Responses

| Status | Condition | Response |
|--------|-----------|----------|
| 404 | Run not found | `{"error": "RUN_NOT_FOUND", "run_id": "..."}` |

---

## Security Requirements (MANDATORY)

### Path Traversal Prevention

```python
def find_artifact_path(self, run_id: str) -> Optional[Path]:
    """
    MANDATORY: Reject path traversal attempts.
    """
    if not run_id or any(c in run_id for c in ("/", "\\", "..")):
        return None  # Reject suspicious input
    # ... rest of lookup
```

### Input Validation

| Input | Validation |
|-------|------------|
| `run_id` | MUST NOT contain `/`, `\`, or `..` |
| `limit` | MUST be clamped to 1-200 range |
| `date_from`/`date_to` | MUST be valid `YYYY-MM-DD` format |

---

## Index Item Schema

### Lightweight Index Entry

```python
@dataclass(frozen=True)
class RunIndexItem:
    """Lightweight index entry for listing runs."""
    run_id: str
    created_at_utc: str
    status: str              # OK | BLOCKED | ERROR
    mode: str
    tool_id: str
    risk_level: str          # GREEN | YELLOW | RED | UNKNOWN
    score: Optional[float]
    feasibility_sha256: str
    toolpaths_sha256: Optional[str]
    artifact_path: str
```

### Quick Parse Requirements

- Index entries MUST be parseable without full model validation
- Corrupt JSON files MUST be skipped (return `None`)
- Parse failures MUST NOT crash the index scan

---

## Filter Behavior Specification

### Status Filter

| Value | Matches |
|-------|---------|
| `OK` | Successful toolpath generations |
| `BLOCKED` | Safety-blocked requests |
| `ERROR` | Exception during processing |

### Risk Level Filter

| Value | Matches |
|-------|---------|
| `GREEN` | Safe to proceed |
| `YELLOW` | Proceed with caution |
| `RED` | Blocked by policy |
| `UNKNOWN` | Unable to compute |

### Date Range Filters

- `date_from`: Inclusive (matches runs on or after)
- `date_to`: Inclusive (matches runs on or before)
- Both filters use artifact `created_at_utc` date portion

---

## Implementation Architecture

### File Structure

```
services/api/app/rmos/
+-- runs/
|   +-- index.py        # Scan + filter + pagination
|   +-- store.py        # Read methods (find_artifact_path, read_artifact)
+-- api/
    +-- rmos_runs_router.py  # Query endpoints
```

### Store Methods Contract

```python
class RunStore:
    def find_artifact_path(self, run_id: str) -> Optional[Path]:
        """Find artifact file by run_id. Returns None if not found."""

    def read_artifact(self, run_id: str) -> Optional[RunArtifact]:
        """Load and validate artifact. Returns None if not found."""
```

---

## Compliance Verification

Implementations are compliant when:

- [ ] All three endpoints are implemented and functional
- [ ] Filter parameters work as specified
- [ ] Pagination returns correct cursor and respects limit
- [ ] Path traversal attempts are rejected (return 404, not file)
- [ ] Download endpoint streams file with correct headers
- [ ] 404 errors include `run_id` in response

---

## Test Requirements

All implementations MUST include tests proving:

1. **Index returns items** — Created artifacts appear in index
2. **Filters work** — Status, mode, risk_level filters return correct subset
3. **Pagination works** — Cursor continues from correct position
4. **404 for missing** — Non-existent run_id returns 404
5. **Download streams JSON** — File response has correct content-type

---

## Usage Examples

### List Recent Runs

```bash
# Get 10 most recent runs
curl "http://localhost:8000/api/rmos/runs?limit=10"

# Filter by status
curl "http://localhost:8000/api/rmos/runs?status=BLOCKED"

# Filter by risk level
curl "http://localhost:8000/api/rmos/runs?risk_level=RED"

# Combine filters
curl "http://localhost:8000/api/rmos/runs?status=BLOCKED&risk_level=RED&mode=saw"
```

### Pagination

```bash
# First page
curl "http://localhost:8000/api/rmos/runs?limit=20"
# Response: {"items": [...], "next_cursor": "2025-12-17|abc123.json"}

# Next page
curl "http://localhost:8000/api/rmos/runs?limit=20&cursor=2025-12-17|abc123.json"
```

---

## Amendment Process

Changes to this contract require:
1. Formal proposal with justification
2. API versioning consideration
3. Backward compatibility analysis
4. Update to all subordinate implementations

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | GOV-RAQA-001 |
| Classification | Internal - Engineering |
| Owner | RMOS Architecture Team |
| Last Review | December 17, 2025 |
| Next Review | March 17, 2026 |
