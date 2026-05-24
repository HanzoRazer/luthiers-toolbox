# IBG Provenance Attachment Specification

**Date:** 2026-05-24  
**Status:** DRAFT — Ratification Substrate (NOT Runtime Implementation)  
**Sprint:** Governed Interoperability Normalization  
**Authority:** Documentation authority only — requires R1 ratification for implementation  
**Cross-reference:** [`CANONICAL_PROVENANCE_MODEL.md`](CANONICAL_PROVENANCE_MODEL.md), [`IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md`](IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md), [`CROSS_REPO_AUTHORITY_CROSSWALK.md`](CROSS_REPO_AUTHORITY_CROSSWALK.md)

---

## Purpose

This specification defines the provenance attachment schema for the 5 IBG DXF save points currently in `BLOCKED_PROVENANCE` status. It provides the ratification substrate for Phase R1 governance review.

**Constitutional boundary:** This is documentation-only drafting authority. Runtime implementation requires explicit R1 ratification.

---

## Blocked Save Points (Reference)

Per `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md`:

| File | Lines | Current Status |
|------|-------|----------------|
| `instrument_geometry/body/ibg/body_contour_solver.py` | 777, 808 | `BLOCKED_PROVENANCE` |
| `instrument_geometry/body/ibg/arc_reconstructor.py` | 1116, 1279, 1303 | `BLOCKED_PROVENANCE` |

These use `DxfWriter` (compat-governed) but must NOT receive lifecycle promotion until provenance attachment is ratified and wired.

---

## Provenance Attachment Schema

### 1. Required Fields at DXF Export Boundary

Every IBG DXF export must carry:

```python
@dataclass
class IBGExportProvenanceAttachment:
    """
    Required provenance attachment for IBG DXF exports.
    
    Constitutional invariants:
        - execution_authorized is ALWAYS False
        - review_required is ALWAYS True
        - epistemic_status defaults to PREDICTED until ratified
    """
    # Source lineage (REQUIRED)
    source_artifact_id: str          # Original input DXF/image path
    derivation_chain: List[str]      # Full ancestry IDs
    
    # Transformation context (REQUIRED)
    transformation_stage: str        # TransformationStage enum value
    transformation_method: str       # Function that produced this output
    transformation_params: Dict[str, Any]  # Parameters used
    
    # Authority declaration (REQUIRED)
    authority_state: str             # AuthorityState enum value
    epistemic_status: str            # EpistemicStatus enum value (default: PREDICTED)
    
    # Confidence envelope (REQUIRED for cross-repo interop)
    confidence_envelope: Optional[Dict[str, Any]]  # ConfidenceEnvelopeV1 serialized
    
    # Constitutional guards (FIXED — cannot be overridden)
    execution_authorized: Literal[False] = False
    review_required: Literal[True] = True
    runtime_authoritative: Literal[False] = False
    
    # Integrity
    provenance_hash: str             # SHA-256 hash of lineage chain
    attachment_timestamp: datetime
```

### 2. Epistemic Status Defaults

Until R1 ratification, all IBG exports carry:

```text
epistemic_status: PREDICTED
authority_state: SANDBOX_EXPERIMENTAL or ADVISORY_CANDIDATE
```

Post-R1 ratification may promote to:

```text
epistemic_status: DERIVED (if provenance chain complete)
authority_state: SEMANTIC_INTERPRETATION (pending human review)
```

Never allowed for IBG exports without explicit human review:

```text
epistemic_status: OBSERVED (measurement authority)
authority_state: CANONICAL_GEOMETRY (source authority)
authority_state: APPROVED_FOR_GENERATION (execution authority)
```

### 3. Cross-Repo Interoperability Fields

For ConfidenceEnvelopeV1 attachment:

```python
envelope_schema = {
    "envelope_version": "v1",
    "domain": "interpretive",        # IBG outputs are interpretive, not measurement
    "source_system": "luthiers_toolbox",
    "semantic_scope": str,           # What this export represents
    "confidence_type": str,          # ConfidenceType enum value
    "confidence_value": float,       # 0.0-1.0
    "epistemic_status": "predicted", # Default for IBG
    "evidence_basis": str,           # What evidence supports this
    "review_required": True,         # Constitutional invariant
    "non_implications": List[str],   # What this does NOT imply
    "runtime_authoritative": False,  # Constitutional invariant
    "execution_authorized": False,   # Constitutional invariant
}
```

### 4. DxfLifecycleContext Integration

The provenance attachment maps to existing `DxfLifecycleContext`:

```python
@dataclass
class DxfLifecycleContext:
    # Existing fields
    lifecycle_class: str             # BLOCKED_PROVENANCE → COMPAT_ONLY (post-ratification)
    
    # Provenance attachment (new)
    ibg_provenance: Optional[IBGExportProvenanceAttachment] = None
    
    # Validation
    def has_valid_provenance(self) -> bool:
        """Check if provenance attachment is complete and valid."""
        if self.lifecycle_class == "BLOCKED_PROVENANCE":
            return False  # Blocked until ratification
        if self.ibg_provenance is None:
            return False
        return (
            self.ibg_provenance.source_artifact_id is not None
            and len(self.ibg_provenance.derivation_chain) > 0
            and self.ibg_provenance.provenance_hash is not None
        )
```

---

## Mapping: ProvenanceRecord → DxfLifecycleContext

Conversion from runtime `ProvenanceRecord` to export attachment:

```python
def create_ibg_export_attachment(
    provenance: ProvenanceRecord,
    confidence: ConfidenceDeclaration,
    authority: AuthorityStateContainer,
) -> IBGExportProvenanceAttachment:
    """
    Create provenance attachment for IBG DXF export.
    
    This function will be implemented post-R1 ratification.
    Current status: specification only.
    """
    envelope = ConfidenceEnvelopeV1.from_confidence_declaration(
        declaration=confidence,
        domain=SemanticDomain.INTERPRETIVE,
        epistemic_status=EpistemicStatus.PREDICTED,
    )
    
    return IBGExportProvenanceAttachment(
        source_artifact_id=provenance.source_artifact,
        derivation_chain=provenance.derivation_chain,
        transformation_stage=provenance.get_last_transformation().stage.value,
        transformation_method=provenance.get_last_transformation().method,
        transformation_params=provenance.get_last_transformation().params,
        authority_state=authority.current_state.value,
        epistemic_status=EpistemicStatus.PREDICTED.value,
        confidence_envelope=envelope.to_dict(),
        provenance_hash=provenance.compute_provenance_hash(),
        attachment_timestamp=datetime.now(timezone.utc),
    )
```

---

## Validation Rules

### Pre-export validation (fail-closed)

```python
def validate_ibg_export_provenance(attachment: IBGExportProvenanceAttachment) -> bool:
    """
    Validate provenance attachment before allowing DXF export.
    
    Returns False (blocks export) if:
        - execution_authorized is not False
        - review_required is not True
        - derivation_chain is empty
        - provenance_hash is missing
        - authority_state indicates production authority without review
    """
    # Constitutional invariants
    if attachment.execution_authorized is not False:
        return False
    if attachment.review_required is not True:
        return False
    if attachment.runtime_authoritative is not False:
        return False
    
    # Lineage completeness
    if not attachment.source_artifact_id:
        return False
    if not attachment.derivation_chain:
        return False
    if not attachment.provenance_hash:
        return False
    
    # Authority sanity
    forbidden_states = {
        "canonical_geometry",
        "approved_for_generation",
    }
    if attachment.authority_state in forbidden_states:
        return False
    
    return True
```

---

## Implementation Phases (Post-Ratification)

### Phase R2 (after R1 ratification)

1. Wire IBG saves through `create_ibg_export_attachment`
2. Add validation at `DxfWriter.save` boundary
3. Reclassify matrix rows from `BLOCKED_PROVENANCE` → `COMPAT_ONLY`

### Phase R3 (optional)

1. Cross-repo review package integration
2. ConfidenceEnvelopeV1 propagation to CAM downstream

---

## What This Specification Does NOT Authorize

| Action | Reason |
|--------|--------|
| Runtime implementation before R1 | Documentation authority only |
| Promotion to `LIFECYCLE_GOVERNED` | Requires full orchestrator adoption |
| Execution authority claims | Constitutional invariant |
| Production spine integration | `R_AND_D_EXCLUDED` separation until graduated |
| Automatic approval based on confidence | Authority laundering prevention |

---

## Ratification Checklist (for R1 session)

- [ ] Schema fields reviewed by governance owner
- [ ] Constitutional invariants verified (execution_authorized, review_required)
- [ ] Cross-repo compatibility validated against tap_tone ADR-0012
- [ ] Epistemic status defaults agreed
- [ ] Validation rules approved
- [ ] Implementation timeline established
- [ ] Test coverage requirements defined

---

*Specification version: 2026-05-24*  
*Next update: R1 ratification session outcome*
