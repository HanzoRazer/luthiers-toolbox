# IBG Provenance Attachment Field Matrix

**Sprint:** MRP-6C  
**Status:** R1 RATIFICATION PREP  
**Date:** 2026-05-24  
**Parent:** `IBG_PROVENANCE_RATIFICATION_PACKET.md`

---

## Purpose

This matrix defines the exact fields required at the IBG DXF save boundary before export lifecycle promotion is allowed.

---

## Field Matrix

| Field | Required | Source | Authority Owner | Maps To | Failure If Missing |
|-------|----------|--------|-----------------|---------|-------------------|
| `provenance_record_id` | **Yes** | Auto-generated (`prov_{uuid}`) | System | Audit lineage | Save rejected: no lineage anchor |
| `source_artifact_id` | **Yes** | Upstream DXF/blueprint path | Pipeline | `DxfLifecycleContext.source_module` | Save rejected: origin unknown |
| `ibg_run_id` | **Yes** | Workflow execution ID | Pipeline | Audit lineage | Save rejected: session untraceable |
| `candidate_id` | **Yes** | `BodyEvidenceCandidate.candidate_id` | IBG runtime | Semantic traceability | Save rejected: candidate unlinked |
| `epistemic_status` | **Yes** | Pipeline stage determination | Crosswalk (ADR-0012) | Authority posture | Save rejected: authority undefined |
| `authority_state` | **Yes** | `AuthorityStateContainer.current_state` | IBG constitutional | `DxfLifecycleContext.authority_context` | Save rejected: governance state unknown |
| `confidence_type` | **Yes** | `ConfidenceDeclaration.confidence_type` | IBG constitutional | Non-authoritative metadata | Save rejected: confidence semantics unclear |
| `confidence_value` | No | `ConfidenceDeclaration.value` | IBG constitutional | Advisory metadata | Allowed: value is non-authoritative |
| `topology_integrity_score` | **Yes** | `ProvenanceRecord.topology_integrity_score` | IBG runtime | Gate threshold | Save rejected: quality unknown |
| `reconstruction_method` | **Yes** | `transformation_history[-1].stage` | IBG runtime | Algorithm lineage | Save rejected: method undocumented |
| `operator_review_status` | **Yes** | `ReviewEnforcement` state | IBG constitutional | Review gate | Save rejected: review state unknown |
| `operator_review_id` | Conditional | Human reviewer ID | Operator | Audit trail | Required if `operator_review_status == reviewed` |
| `export_intent` | **Yes** | Caller declaration | Caller | Purpose documentation | Save rejected: purpose unclear |
| `lifecycle_target` | **Yes** | Caller declaration | Governance | Matrix classification | Save rejected: target undefined |
| `geometry_hash` | No | Computed from output | System | Integrity verification | Allowed: optional integrity check |
| `created_at` | **Yes** | Save timestamp | System | Audit timeline | Save rejected: time unknown |
| `schema_version` | **Yes** | Fixed: `ibg_provenance.v1` | Governance | Contract versioning | Save rejected: schema undefined |

---

## Field Definitions

### Identity Fields

| Field | Type | Format | Example |
|-------|------|--------|---------|
| `provenance_record_id` | string | `prov_{uuid12}` | `prov_a1b2c3d4e5f6` |
| `source_artifact_id` | string | File path or URI | `/blueprints/cuatro_2026.dxf` |
| `ibg_run_id` | string | `ibg_run_{uuid12}` | `ibg_run_x1y2z3w4v5u6` |
| `candidate_id` | string | `bec_{uuid12}` | `bec_m1n2o3p4q5r6` |

### Authority Fields

| Field | Type | Values | Notes |
|-------|------|--------|-------|
| `epistemic_status` | enum | `OBSERVED`, `DERIVED`, `ESTIMATED`, `PREDICTED`, `HEURISTIC`, `OPERATOR_ANNOTATED`, `EXTERNALLY_SOURCED` | Per ADR-0012 |
| `authority_state` | enum | `canonical_geometry`, `derived_topology`, `semantic_interpretation`, `advisory_candidate`, `human_reviewed`, `approved_for_generation`, `sandbox_experimental`, `rejected`, `archived_superseded` | Per IBG constitutional |
| `confidence_type` | enum | `epistemic`, `statistical`, `heuristic`, `human_assessed` | Per ConfidenceDeclaration |

### Quality Fields

| Field | Type | Range | Threshold |
|-------|------|-------|-----------|
| `topology_integrity_score` | float | 0.0–1.0 | ≥0.7 for standard gate, ≥0.85 for strict |
| `confidence_value` | float | 0.0–1.0 | No threshold (non-authoritative) |

### Review Fields

| Field | Type | Values | Notes |
|-------|------|--------|-------|
| `operator_review_status` | enum | `pending`, `in_review`, `reviewed`, `bypassed` | `bypassed` triggers gate rejection |
| `operator_review_id` | string | `human:{id}` | Required when status is `reviewed` |

### Intent Fields

| Field | Type | Values | Notes |
|-------|------|--------|-------|
| `export_intent` | enum | `fabrication_prep`, `review_artifact`, `diagnostic_output`, `archive` | Determines downstream handling |
| `lifecycle_target` | enum | `COMPAT_ONLY`, `LIFECYCLE_GOVERNED` | Must match matrix disposition post-R2 |

### Metadata Fields

| Field | Type | Format | Notes |
|-------|------|--------|-------|
| `reconstruction_method` | string | Stage name | e.g., `TOPOLOGY_RECONSTRUCTION`, `GAP_CLOSURE` |
| `geometry_hash` | string | SHA-256 prefix (12 chars) | Optional integrity check |
| `created_at` | datetime | ISO 8601 | `2026-05-24T14:30:00Z` |
| `schema_version` | string | Semantic version | `ibg_provenance.v1` |

---

## Validation Rules

### Required Field Presence

```python
REQUIRED_FIELDS = {
    "provenance_record_id",
    "source_artifact_id",
    "ibg_run_id",
    "candidate_id",
    "epistemic_status",
    "authority_state",
    "confidence_type",
    "topology_integrity_score",
    "reconstruction_method",
    "operator_review_status",
    "export_intent",
    "lifecycle_target",
    "created_at",
    "schema_version",
}

def validate_required_fields(attachment: dict) -> List[str]:
    missing = REQUIRED_FIELDS - set(attachment.keys())
    return list(missing)
```

### Conditional Requirements

```python
def validate_conditional_fields(attachment: dict) -> List[str]:
    errors = []
    
    # operator_review_id required when reviewed
    if attachment.get("operator_review_status") == "reviewed":
        if not attachment.get("operator_review_id"):
            errors.append("operator_review_id required when status is reviewed")
        elif not attachment["operator_review_id"].startswith("human:"):
            errors.append("operator_review_id must start with 'human:'")
    
    return errors
```

### Threshold Validation

```python
def validate_thresholds(attachment: dict, gate_config: str = "standard") -> List[str]:
    errors = []
    
    score = attachment.get("topology_integrity_score", 0.0)
    threshold = 0.7 if gate_config == "standard" else 0.85
    
    if score < threshold:
        errors.append(f"topology_integrity_score {score} < {threshold} threshold")
    
    return errors
```

---

## Authority State Constraints

### States Allowing DXF Save (Post-R2)

| Authority State | May Save DXF? | Lifecycle Target |
|-----------------|---------------|------------------|
| `canonical_geometry` | No | — (input only) |
| `derived_topology` | No | — (intermediate) |
| `semantic_interpretation` | No | — (interpretation) |
| `advisory_candidate` | No | — (not reviewed) |
| `human_reviewed` | **Yes** | COMPAT_ONLY |
| `approved_for_generation` | **Yes** | LIFECYCLE_GOVERNED |
| `sandbox_experimental` | No | — (untrusted) |
| `rejected` | No | — (rejected) |
| `archived_superseded` | No | — (superseded) |

### Forbidden Transitions at Save Boundary

```
advisory_candidate → save     FORBIDDEN
sandbox_experimental → save   FORBIDDEN
rejected → save               FORBIDDEN
```

---

## Cross-Reference Mapping

### To DxfLifecycleContext

| IBG Attachment Field | DxfLifecycleContext Field | Transformation |
|---------------------|---------------------------|----------------|
| `ibg_run_id` + caller | `source_module` | Concatenate |
| (fixed) | `export_type` | `"dxf-create-save"` |
| (config) | `dxf_version` | From caller |
| (gate decision) | `lifecycle_status` | `"COMPAT_ONLY"` or `"LIFECYCLE_GOVERNED"` |
| (fixed) | `runtime_callable` | `"runtime_service"` |
| `authority_state` | `authority_context` | Map to string |
| (attachment present) | `provenance_status` | `"IBG_ATTACHED"` |

### To ProvenanceRecord (Canonical)

| IBG Attachment Field | Canonical Field | Notes |
|---------------------|-----------------|-------|
| `provenance_record_id` | `provenance_id` | Direct mapping |
| `epistemic_status` | (implied by) `provenance_type` | Derivation context |
| `created_at` | `provenance_timestamp` | Direct mapping |
| `ibg_run_id` | `provenance_agent` | Execution context |
| (all fields) | `provenance_payload` | IBG-specific payload |

---

## Failure Handling

### Missing Required Field

```
Action: Reject save
Log: "IBG save rejected: missing required field {field_name}"
State: No file written
Recovery: Caller must supply field
```

### Threshold Violation

```
Action: Reject save
Log: "IBG save rejected: {field_name} {value} below threshold {threshold}"
State: No file written
Recovery: Improve topology quality or use permissive gate (dev only)
```

### Authority State Violation

```
Action: Reject save
Log: "IBG save rejected: authority_state {state} does not permit DXF export"
State: No file written
Recovery: Complete human review, transition authority state
```

### Bypass Attempt

```
Action: Reject save, increment bypass counter
Log: "IBG save rejected: bypass attempt detected"
State: No file written, bypass_attempt_count++
Recovery: Constitutional violation; escalate to governance
```

---

## Schema Version Contract

| Version | Status | Notes |
|---------|--------|-------|
| `ibg_provenance.v1` | **Active** (pending R1) | Initial ratification target |

### Version Migration

Future versions must:
1. Maintain backward compatibility for required fields
2. Add new fields as optional first
3. Announce deprecations in governance release notes
4. Never remove required fields without major version bump

---

*IBG Provenance Attachment Field Matrix — MRP-6C — 2026-05-24*
