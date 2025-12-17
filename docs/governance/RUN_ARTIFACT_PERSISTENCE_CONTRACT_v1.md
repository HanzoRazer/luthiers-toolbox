# Run Artifact Persistence Contract

**Document Type:** Canonical Governance Specification
**Version:** 1.0
**Effective Date:** December 17, 2025
**Status:** AUTHORITATIVE
**Precedence:** PRIMARY - All implementations MUST conform
**Dependency:** SERVER_SIDE_FEASIBILITY_ENFORCEMENT_CONTRACT_v1.md

---

## Governance Statement

This document establishes the **canonical contract** for run artifact persistence within the Luthier's ToolBox RMOS. Every toolpath generation attempt MUST create an immutable audit trail. Deviation from this contract is prohibited without formal amendment through the governance review process.

### Governing Principles

1. **Complete Capture** — Every request (OK, BLOCKED, ERROR) creates an artifact
2. **Immutable Storage** — Artifacts are write-once, never modified
3. **Hash Verification** — All outputs are SHA256 hashed for provenance
4. **Authoritative Feasibility** — Only server-computed feasibility is recorded
5. **Audit Trail Completeness** — Sufficient data to reconstruct any decision

### Subordinate Documents

All implementation documents, guides, and code related to run artifact storage are subordinate to this contract.

---

## Scope

| In Scope | Out of Scope |
|----------|--------------|
| Run artifact schema definition | UI display of artifacts |
| Persistence requirements | Query and filtering logic |
| Hash computation specifications | Retention and purge policies |
| Storage structure | Cross-system artifact federation |

---

## Artifact Creation Requirements (MANDATORY)

### When Artifacts MUST Be Created

| Outcome | Status Value | Required |
|---------|--------------|----------|
| Toolpath generation succeeded | `OK` | YES |
| Toolpath generation blocked by safety | `BLOCKED` | YES |
| Toolpath generation failed with exception | `ERROR` | YES |

**There are NO exceptions to this rule.**

---

## Run Artifact Schema Specification

### Core Schema

```python
class RunArtifact(BaseModel):
    """
    Complete record of a toolpath generation attempt.
    Created for EVERY request: OK, BLOCKED, or ERROR.
    """
    # Identity (REQUIRED)
    run_id: str                    # Unique identifier (UUID hex)
    created_at_utc: datetime       # UTC timestamp

    # Context (REQUIRED)
    mode: str                      # "saw", "router", etc.
    tool_id: str                   # Tool identifier

    # Outcome (REQUIRED)
    status: Literal["OK", "BLOCKED", "ERROR"]

    # Inputs (REQUIRED)
    request_summary: Dict[str, Any]  # Sanitized request (no client feasibility)

    # Authoritative Data (REQUIRED)
    feasibility: Dict[str, Any]      # Server-computed feasibility
    decision: RunDecision            # Safety decision

    # Verification (REQUIRED)
    hashes: Hashes                   # SHA256 hashes

    # Outputs (REQUIRED, may be empty)
    outputs: RunOutputs              # Generated artifacts

    # Metadata (OPTIONAL)
    meta: Dict[str, Any]             # Policy info, versions, etc.
```

### Hash Schema

```python
class Hashes(BaseModel):
    """SHA256 hashes for audit verification."""
    feasibility_sha256: str              # REQUIRED - always present
    toolpaths_sha256: Optional[str]      # Present if status=OK
    gcode_sha256: Optional[str]          # Present if G-code generated
    opplan_sha256: Optional[str]         # Present if opplan generated
```

### Decision Schema

```python
class RunDecision(BaseModel):
    """Safety decision extracted from feasibility."""
    risk_level: str                      # GREEN, YELLOW, RED, UNKNOWN
    score: Optional[float]               # Numeric score if available
    block_reason: Optional[str]          # Why blocked (if applicable)
    warnings: List[str]                  # Warning messages
    details: Dict[str, Any]              # Additional decision data
```

### Outputs Schema

```python
class RunOutputs(BaseModel):
    """Generated outputs (embedded or referenced)."""
    # Embedded outputs (for small payloads)
    gcode_text: Optional[str]            # Inline if <= 200KB
    opplan_json: Optional[Dict]          # Inline operation plan

    # File references (for large outputs)
    gcode_path: Optional[str]            # Path to G-code file
    opplan_path: Optional[str]           # Path to opplan file
    preview_svg_path: Optional[str]      # Path to preview SVG
```

---

## Hash Computation Specifications

### Stability Requirements

All hash computations MUST be deterministic and reproducible:

```python
def sha256_json(obj: Any) -> str:
    """
    MANDATORY: Stable JSON hash
    - Sort keys alphabetically
    - Use compact separators (",", ":")
    - Use ensure_ascii=False for Unicode
    """
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
```

### Hash Purposes

| Hash Field | Purpose | Verification Use Case |
|------------|---------|----------------------|
| `feasibility_sha256` | Prove which safety evaluation was used | "Was this the feasibility that authorized this G-code?" |
| `toolpaths_sha256` | Verify entire response payload | "Has the response been tampered with?" |
| `gcode_sha256` | Trace specific G-code to source | "Did this G-code file come from this run?" |
| `opplan_sha256` | Verify operation plan integrity | "Is this the original operation plan?" |

---

## Storage Structure Specification

### Directory Layout

```
{RMOS_RUNS_DIR}/
+-- {YYYY-MM-DD}/
    +-- {run_id}.json
    +-- {run_id}.json
    +-- ...
```

### Path Resolution

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Environment variable | `RMOS_RUNS_DIR=/data/runs/rmos` |
| 2 | Default | `services/api/data/runs/rmos` |

### File Naming

- Run ID: UUID hex (32 characters)
- Extension: `.json`
- Example: `a1b2c3d4e5f67890a1b2c3d4e5f67890.json`

---

## Artifact Content by Status

### OK Artifact

```json
{
  "run_id": "a1b2c3d4...",
  "created_at_utc": "2025-12-17T17:30:00Z",
  "mode": "saw",
  "tool_id": "saw:veneer_160",
  "status": "OK",
  "request_summary": {"blade": {...}, "material": "softwood"},
  "feasibility": {"risk_level": "GREEN", "score": 87.5, ...},
  "decision": {"risk_level": "GREEN", "score": 87.5, "warnings": []},
  "hashes": {
    "feasibility_sha256": "abc123...",
    "toolpaths_sha256": "def456...",
    "gcode_sha256": "789xyz...",
    "opplan_sha256": "..."
  },
  "outputs": {
    "gcode_text": "G90\nG21\n...",
    "opplan_json": {...}
  },
  "meta": {"dispatch": {"mode": "saw"}}
}
```

### BLOCKED Artifact

```json
{
  "run_id": "b2c3d4e5...",
  "created_at_utc": "2025-12-17T17:31:00Z",
  "mode": "saw",
  "tool_id": "saw:kerf_cut_v1",
  "status": "BLOCKED",
  "request_summary": {"blade": {...}},
  "feasibility": {"risk_level": "RED", "score": 25, ...},
  "decision": {
    "risk_level": "RED",
    "score": 25,
    "block_reason": "Rim speed exceeds safe threshold",
    "warnings": ["Excessive RPM for blade diameter"]
  },
  "hashes": {
    "feasibility_sha256": "blocked123...",
    "toolpaths_sha256": null,
    "gcode_sha256": null,
    "opplan_sha256": null
  },
  "outputs": {},
  "meta": {"policy": {"block_on_red": true}}
}
```

### ERROR Artifact

```json
{
  "run_id": "c3d4e5f6...",
  "created_at_utc": "2025-12-17T17:32:00Z",
  "mode": "saw",
  "tool_id": "saw:blade_v1",
  "status": "ERROR",
  "request_summary": {...},
  "feasibility": {...},
  "decision": {...},
  "hashes": {"feasibility_sha256": "error123..."},
  "outputs": {},
  "meta": {
    "exception": {
      "type": "ValueError",
      "message": "Invalid blade configuration"
    }
  }
}
```

---

## Data Flow Specification

```
+-----------------------------------------------------------------------------+
|                         RUN ARTIFACT CREATION FLOW                           |
+-----------------------------------------------------------------------------+
|                                                                             |
|   Request arrives at /api/rmos/toolpaths                                    |
|                      |                                                      |
|                      v                                                      |
|   +-------------------------------------+                                   |
|   |  Recompute feasibility (server)     |                                   |
|   |  Hash: feasibility_sha256           |                                   |
|   +------------------+------------------+                                   |
|                      |                                                      |
|          +-----------+-----------+                                          |
|          v           v           v                                          |
|      BLOCKED       SUCCESS      ERROR                                       |
|          |           |           |                                          |
|          v           v           v                                          |
|   +----------+ +----------+ +----------+                                    |
|   | Artifact | | Artifact | | Artifact |                                    |
|   | BLOCKED  | |    OK    | |  ERROR   |                                    |
|   |          | | +hashes  | | +except  |                                    |
|   +----+-----+ +----+-----+ +----+-----+                                    |
|        |            |            |                                          |
|        +------------+------------+                                          |
|                     |                                                       |
|                     v                                                       |
|   +-------------------------------------+                                   |
|   |  RunStore.write_artifact()          |                                   |
|   |  --> {RMOS_RUNS_DIR}/{date}/{id}.json|                                   |
|   +-------------------------------------+                                   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Request Summary Sanitization

Client feasibility MUST be stripped from request summaries:

```python
def summarize_request(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    MANDATORY: Strip client feasibility, truncate large payloads.
    """
    summary = {}
    for k in sorted(req.keys()):
        if k == "feasibility":
            continue  # NEVER store client feasibility
        # ... truncation logic for large values
    return summary
```

---

## API Response Requirements

### Success Response

```python
{
    # ... toolpath payload ...
    "_run_id": "a1b2c3d4...",
    "_run_artifact_path": "/data/runs/rmos/2025-12-17/a1b2c3d4.json",
    "_hashes": {
        "feasibility_sha256": "...",
        "toolpaths_sha256": "...",
        "gcode_sha256": "...",
        "opplan_sha256": "..."
    }
}
```

### Blocked Response (HTTP 409)

```python
{
    "detail": {
        "error": "SAFETY_BLOCKED",
        "message": "Toolpath generation blocked by server-side safety policy.",
        "run_id": "b2c3d4e5...",
        "run_artifact_path": "/data/runs/rmos/2025-12-17/b2c3d4e5.json",
        "decision": {...}
    }
}
```

---

## Compliance Verification

Implementations are compliant when:

- [ ] Every toolpath request creates an artifact (OK, BLOCKED, or ERROR)
- [ ] Artifacts contain all required fields per schema
- [ ] feasibility_sha256 is always computed and stored
- [ ] Client feasibility is never stored in request_summary
- [ ] Artifacts are written to date-partitioned directories
- [ ] Response includes run_id and hashes

---

## Test Requirements

All implementations MUST include tests proving:

1. **BLOCKED creates artifact** — Safety-blocked requests persist artifacts
2. **OK creates artifact with hashes** — Successful requests include all hashes
3. **ERROR creates artifact** — Exceptions still create artifacts
4. **Client feasibility stripped** — request_summary never contains feasibility key

---

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `RMOS_RUNS_DIR` | `services/api/data/runs/rmos` | Artifact storage root |

---

## Amendment Process

Changes to this contract require:
1. Formal proposal with justification
2. Data migration plan for existing artifacts
3. Version increment
4. Update to all subordinate implementations

---

## Summary

This contract ensures an **immutable manufacturing decision trail**:

| Outcome | What's Recorded |
|---------|-----------------|
| **BLOCKED** | Feasibility, decision, reason for block |
| **OK** | Feasibility, decision, all output hashes |
| **ERROR** | Feasibility, decision, exception details |

Every manufacturing decision is:
- **Traceable** — which feasibility led to which toolpath
- **Verifiable** — SHA256 hashes prove integrity
- **Auditable** — complete record of blocked vs. allowed
- **Debuggable** — exact reason for any block or error

---

## Document Control

| Field | Value |
|-------|-------|
| Document ID | GOV-RAP-001 |
| Classification | Internal - Engineering |
| Owner | RMOS Architecture Team |
| Last Review | December 17, 2025 |
| Next Review | March 17, 2026 |
