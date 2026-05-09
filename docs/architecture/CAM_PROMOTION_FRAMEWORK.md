# CAM Promotion Framework

**Date:** 2026-05-09  
**Status:** ACTIVE FRAMEWORK  
**Scope:** Candidate CAM module promotion to governed status

---

## Purpose

This document defines the formal process for promoting CAM modules from CANDIDATE status to GOVERNED status. The goal is to make promotion:

- Measurable
- Repeatable
- Auditable

---

## Promotion Pipeline

```
LIBRARY
  ↓
CANDIDATE
  ↓
GOVERNED PREVIEW
  ↓
GOVERNED EXPORT
  ↓
MACHINE OUTPUT
```

Each transition requires explicit approval and documented evidence.

---

## Module Categories

| Category | Definition | Examples |
|----------|------------|----------|
| **Geometry Generator** | Produces geometry only (points, paths) | polygon_offset, offset_geometry |
| **Preview Generator** | Safe visualization output (JSON, SVG) | nut_slot_cam preview |
| **Export Generator** | Serializable manufacturing output (DXF, G-code string) | fret_slots_cam, profile_toolpath |
| **Postprocessor** | Machine-specific translation | rmos/posts/grbl.py |
| **Simulation Tool** | Non-export analysis | util/gcode/simulator.py |
| **Utility Library** | Support logic only | util/gcode/lexer.py |

---

## Promotion Stages

### Stage 1: LIBRARY → CANDIDATE

**Criteria:**
- Code compiles and is importable
- Has a clear purpose/scope
- No obvious safety hazards

**Evidence:** Code exists and is referenced.

---

### Stage 2: CANDIDATE → GOVERNED PREVIEW

**Required:**

| Requirement | Description |
|-------------|-------------|
| Coordinate system documented | Origin, axes, Z-zero semantics |
| Input contract documented | Pydantic schema or dataclass |
| Output contract documented | Return type, structure |
| Tests exist | At least smoke tests |
| Preview visualization path | JSON or SVG output available |
| Safety gates | @safety_critical or explicit validation |
| Route provenance | Clear path from endpoint to generator |

**Evidence:** Documented in scorecard, tests passing.

---

### Stage 3: GOVERNED PREVIEW → GOVERNED EXPORT

**Additional requirements:**

| Requirement | Description |
|-------------|-------------|
| Export governance compliance | Follows CAM_EXPORT_GOVERNANCE_POLICY.md |
| Postprocessor separation | G-code generation via postprocessor interface |
| Machine profile abstraction | Not hardcoded to specific machine |
| Manual review path | User can preview before export |
| Safe-Z semantics | Explicit safe_z_mm parameter |
| Tool/stock validation | Validates tool vs material |

**Evidence:** Governance checklist complete, architecture review passed.

---

### Stage 4: GOVERNED EXPORT → MACHINE OUTPUT

**Additional requirements:**

| Requirement | Description |
|-------------|-------------|
| Machine validation | Envelope, feed, spindle checks |
| Execution governance | RMOS run tracking with run_id |
| Streaming safety | No direct machine connection |
| Operator confirmation | User acknowledgment required |
| Hardware isolation | Downloaded file, not streamed |
| Audit trail | Input hash, output hash, timestamps |

**Evidence:** Full governance audit, RMOS integration verified.

---

## Promotion Review Workflow

```
1. Self-Assessment
   ↓
   Developer evaluates module against scorecard
   ↓
2. Audit
   ↓
   Reviewer verifies evidence
   ↓
3. Tests
   ↓
   All relevant tests pass
   ↓
4. Preview Verification
   ↓
   Visual inspection of output
   ↓
5. Governance Review
   ↓
   Check against policy documents
   ↓
6. Promotion Approval
   ↓
   Update registry, add markers
```

---

## Forbidden Practices

### Silent Canonicalization

**FORBIDDEN:** Treating a module as canonical without formal promotion.

Evidence of violation:
- Module used in production without promotion record
- "It's been working fine" as justification
- No entry in cam_candidate_registry.json

### Premature Export

**FORBIDDEN:** Adding export capability without governance.

Evidence of violation:
- New G-code endpoint without RMOS tracking
- Download capability without preview gate
- Machine output without user confirmation

### Implicit Deprecation

**FORBIDDEN:** Hiding or disabling modules without audit.

Evidence of violation:
- Routes removed without documentation
- Modules moved to archive without registry update
- "Dead code" assumptions without verification

---

## Registry Management

### cam_candidate_registry.json

All CANDIDATE modules must have an entry:

```json
{
  "module": "fret_slots_cam",
  "status": "candidate",
  "category": "export_generator",
  "readiness_score": 72,
  "promotion_target": "governed_preview",
  "blocking_issues": ["coordinate docs missing"],
  "last_evaluated": "2026-05-09"
}
```

### Status Values

| Status | Meaning |
|--------|---------|
| `candidate` | Awaiting promotion |
| `governed_preview` | Preview-safe, no export |
| `governed_export` | Export-safe, no machine streaming |
| `machine_output` | Full governance, machine-ready |
| `quarantined` | Blocked pending governance review |
| `library` | Utility code, no promotion needed |

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_MODULE_READINESS_SCORECARD.md` | Scoring criteria |
| `CAM_PROMOTION_CHECKLIST.md` | Required evidence |
| `CAM_EXPORT_GOVERNANCE_POLICY.md` | Export safety gates |
| `CAM_MACHINE_OUTPUT_QUARANTINE_POLICY.md` | Quarantine rules |
| `CAM_COORDINATE_SYSTEM_GOVERNANCE.md` | Coordinate standards |

---

*Framework established: 2026-05-09*
