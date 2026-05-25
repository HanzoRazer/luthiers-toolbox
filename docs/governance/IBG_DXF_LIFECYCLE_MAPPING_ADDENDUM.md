# IBG DXF Lifecycle Mapping Addendum

**Sprint:** MRP-6C  
**Status:** R1 RATIFICATION PREP  
**Date:** 2026-05-24  
**Parent:** `IBG_PROVENANCE_RATIFICATION_PACKET.md`  
**Matrix Reference:** `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md`

---

## Purpose

This addendum defines the rules for when IBG DXF saves may transition from `BLOCKED_PROVENANCE` to `COMPAT_ONLY` or `LIFECYCLE_GOVERNED`.

---

## Current State

All five IBG DXF save points are classified:

```
BLOCKED_PROVENANCE
```

| Path | Lines | Risk Level |
|------|-------|------------|
| `body_contour_solver.py` | 777, 808 | BLOCKED |
| `arc_reconstructor.py` | 1116, 1279, 1303 | BLOCKED |

This classification must remain until R2 implementation completes.

---

## Transition Rules

### Rule 1: No Direct Jump to LIFECYCLE_GOVERNED

```
BLOCKED_PROVENANCE → LIFECYCLE_GOVERNED    FORBIDDEN
```

**Rationale:** LIFECYCLE_GOVERNED requires full export orchestrator integration, which depends on provenance attachment being ratified and wired first.

**Allowed path:**
```
BLOCKED_PROVENANCE → R1 → R2 → COMPAT_ONLY → (future) → LIFECYCLE_GOVERNED
```

### Rule 2: COMPAT_ONLY Requires Provenance Attachment

```
BLOCKED_PROVENANCE → COMPAT_ONLY
```

**Prerequisites:**
1. R1 ratification complete
2. R2 implementation complete
3. IBGProvenanceAttachment present at save boundary
4. All required fields populated
5. Validation passes
6. Matrix disposition updated via governance PR

### Rule 3: LIFECYCLE_GOVERNED Requires Orchestrator

```
COMPAT_ONLY → LIFECYCLE_GOVERNED
```

**Prerequisites:**
1. Export lifecycle orchestrator integration complete
2. Gate validation integrated
3. Full provenance chain wired
4. Governance PR with matrix update

### Rule 4: No Implicit Promotion

Matrix row transitions require:
- Explicit governance PR
- CI validation passing
- Handoff documentation
- No silent bulk updates

---

## Promotion Decision Matrix

| From | To | R1 Required | R2 Required | Orchestrator Required | Allowed |
|------|----|-----------|-----------|--------------------|---------|
| BLOCKED_PROVENANCE | COMPAT_ONLY | **Yes** | **Yes** | No | **Yes** |
| BLOCKED_PROVENANCE | LIFECYCLE_GOVERNED | Yes | Yes | **Yes** | **No** (skip) |
| COMPAT_ONLY | LIFECYCLE_GOVERNED | N/A | N/A | **Yes** | **Yes** |
| BLOCKED_PROVENANCE | DIRECT_SAVE_GAP | — | — | — | **No** (regression) |
| BLOCKED_PROVENANCE | R_AND_D_EXCLUDED | — | — | — | **No** (wrong direction) |

---

## Gate Integration Requirements

### For COMPAT_ONLY Transition

```python
# Required at IBG save boundary (post-R2)
def ibg_dxf_save(
    doc: ezdxf.Drawing,
    path: Path,
    attachment: IBGProvenanceAttachment,
    context: DxfLifecycleContext,
) -> None:
    # 1. Validate attachment
    errors = validate_ibg_attachment(attachment)
    if errors:
        raise IBGProvenanceValidationError(errors)
    
    # 2. Validate authority state
    if not can_export_dxf(attachment.authority_state):
        raise IBGAuthorityStateError(attachment.authority_state)
    
    # 3. Assert lifecycle context
    assert_dxf_lifecycle_context(context)
    
    # 4. Save with provenance
    doc.saveas(path)
    log_ibg_save(attachment, context, path)
```

### For LIFECYCLE_GOVERNED Transition

```python
# Additional requirements (future)
def ibg_dxf_save_governed(
    doc: ezdxf.Drawing,
    path: Path,
    attachment: IBGProvenanceAttachment,
    context: DxfLifecycleContext,
) -> None:
    # All COMPAT_ONLY requirements, plus:
    
    # 5. Orchestrator validation
    orchestrator_result = export_lifecycle_orchestrator.validate(context)
    if not orchestrator_result.is_valid:
        raise LifecycleOrchestratorError(orchestrator_result)
    
    # 6. Full gate chain
    gate_chain_result = run_full_gate_chain(attachment, context)
    if not gate_chain_result.passed:
        raise GateChainError(gate_chain_result)
    
    # 7. Provenance recording
    record_provenance(attachment, context, path)
    
    doc.saveas(path)
```

---

## Matrix Update Protocol

When transitioning IBG rows:

### Step 1: PR Preparation

```markdown
## Matrix Update: IBG Provenance Paths

**Paths affected:**
- body_contour_solver.py:777
- body_contour_solver.py:808
- arc_reconstructor.py:1116
- arc_reconstructor.py:1279
- arc_reconstructor.py:1303

**Transition:** BLOCKED_PROVENANCE → COMPAT_ONLY

**Prerequisites verified:**
- [ ] R1 ratification complete (link to record)
- [ ] R2 implementation complete (link to PR)
- [ ] IBGProvenanceAttachment present at all paths
- [ ] All required fields populated
- [ ] Validation tests passing
- [ ] Handoff documentation created
```

### Step 2: Matrix Row Updates

Update `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` Section 3:

```diff
- | `body_contour_solver.py:777` | dxf-create-save | DxfWriter | Y | Y | N | BLOCKED | runtime_service | BLOCKED | BLOCKED_PROVENANCE | blocked_provenance | BLOCKED_PROVENANCE |
+ | `body_contour_solver.py:777` | dxf-create-save | DxfWriter | Y | Y | GUARD | IBG_ATTACHED | runtime_service | LOW-MEDIUM | COMPAT_ONLY | guarded_r2 | GUARD_ADDED |
```

### Step 3: CI Validation

Matrix validator must pass:
```bash
python scripts/governance/validate_export_lifecycle_matrix.py
```

### Step 4: Governance PR Merge

Requires governance review approval.

---

## Timeline Alignment

| Phase | Matrix State | Save Allowed |
|-------|--------------|--------------|
| Pre-R1 | BLOCKED_PROVENANCE | **No** |
| R1 Complete | BLOCKED_PROVENANCE | **No** (ratification only) |
| R2 In Progress | BLOCKED_PROVENANCE | **No** |
| R2 Complete | COMPAT_ONLY | **Yes** (with attachment) |
| Future Orchestrator | LIFECYCLE_GOVERNED | **Yes** (fully governed) |

---

## Forbidden Actions Before R2

| Action | Why Forbidden |
|--------|---------------|
| Remove BLOCKED_PROVENANCE classification | Violates fail-closed posture |
| Add lifecycle guards implying legitimacy | False confidence in governance story |
| Treat rank_score as export approval | Authority laundering |
| Skip provenance attachment validation | Violates gate requirements |
| Bulk-promote matrix rows | No implicit promotion allowed |

---

## Validation Requirements

### R2 Acceptance Tests

```python
def test_ibg_save_rejected_without_attachment():
    """IBG DXF save fails without provenance attachment."""
    with pytest.raises(IBGProvenanceRequiredError):
        ibg_dxf_save(doc, path, attachment=None, context=context)

def test_ibg_save_rejected_with_invalid_authority():
    """IBG DXF save fails with non-reviewed authority state."""
    attachment = create_attachment(authority_state="advisory_candidate")
    with pytest.raises(IBGAuthorityStateError):
        ibg_dxf_save(doc, path, attachment, context)

def test_ibg_save_allowed_with_valid_attachment():
    """IBG DXF save succeeds with valid provenance attachment."""
    attachment = create_valid_attachment()
    ibg_dxf_save(doc, path, attachment, context)
    assert path.exists()

def test_matrix_rows_remain_blocked_until_r2():
    """All 5 IBG paths remain BLOCKED_PROVENANCE."""
    matrix = load_lifecycle_matrix()
    ibg_paths = [
        "body_contour_solver.py:777",
        "body_contour_solver.py:808",
        "arc_reconstructor.py:1116",
        "arc_reconstructor.py:1279",
        "arc_reconstructor.py:1303",
    ]
    for path in ibg_paths:
        assert matrix[path].lifecycle_status == "BLOCKED_PROVENANCE"
```

---

## Related Documents

| Document | Role |
|----------|------|
| `EXPORT_LIFECYCLE_CLASSIFICATION_MATRIX.md` | Source matrix |
| `IBG_PROVENANCE_RATIFICATION_PACKET.md` | Ratification material |
| `IBG_PROVENANCE_ATTACHMENT_FIELD_MATRIX.md` | Field requirements |
| `IBG_BLOCKED_PROVENANCE_RATIFICATION_TIMELINE.md` | Chronology |
| `DXF_SAVE_LIFECYCLE_GUARD_PLAN.md` | Guard implementation |

---

*IBG DXF Lifecycle Mapping Addendum — MRP-6C — 2026-05-24*
