# CAM Dev Order 7B: Translator Capability Registry Handoff

**Date:** 2026-05-13  
**Status:** Complete  
**Predecessor:** 7A (Translator Planning)

---

## Summary

Implemented the declarative translator capability registry defined in 7A architecture planning. The registry declares translator and postprocessor capabilities without executing any translations or generating any artifacts.

---

## Core Outcome

```
Translator capabilities are now introspectable.
No execution occurs.
```

The registry is declarative only — it describes what translators CAN do, not what they DO.

---

## Files Created

| File | Purpose |
|------|---------|
| `app/cam/translator_capability_registry.py` | Registry models, entries, helper functions |
| `app/routers/cam/translator_capability_router.py` | Introspection endpoints |
| `tests/cam/test_translator_capability_registry.py` | Registry and endpoint tests |

---

## Files Modified

| File | Change |
|------|--------|
| `app/router_registry/manifests/cam_manifest.py` | Added router registration |

---

## Registry Entries

### 7B Entries (validation_only, execution_disabled)

| ID | Category | Output | State | Notes |
|----|----------|--------|-------|-------|
| `dxf_r12` | translator | dxf | validation_only | Free tier DXF format |
| `dxf_r2000` | translator | dxf | validation_only | Paid tier DXF format |
| `gcode_grbl_placeholder` | postprocessor | gcode | execution_disabled | Placeholder only |

### MRP-3A Entries (governed_execution)

| ID | Category | Output | State | Notes |
|----|----------|--------|-------|-------|
| `body_outline_dxf_r12` | translator | dxf | governed_execution | Body outline R12 export |
| `body_outline_dxf_r2000` | translator | dxf | governed_execution | Body outline R2000 export |

---

## Model Structure

```python
class TranslatorCapability(BaseModel):
    # Identity
    translator_id: str
    translator_name: str
    translator_version: str
    
    # Classification
    translator_category: Literal["translator", "postprocessor"]
    output_class: Literal["dxf", "gcode", "svg", "toolpath"]
    output_format_version: Optional[str]
    
    # Lifecycle (7A architecture language + MRP-3A)
    execution_state: Literal[
        "validation_only",
        "execution_planned", 
        "execution_disabled",
        "execution_authorized_future",
        "governed_execution",  # MRP-3A: authorized for Export Object consumption
    ]
    maturity: Literal["placeholder", "candidate", "governed", "canonical"]
    
    # Operational flags (guards/tests/filtering)
    execution_supported: bool = False
    artifact_generation_supported: bool = False
    machine_output_supported: bool = False
    
    # Future authorization
    authorization_required: bool = True
    
    # Capability declarations
    supported_operations: List[str]
    supported_geometry_types: List[str]
    supported_units: List[str]
```

---

## Invariants Enforced

### Via Model Validator

| Invariant | Enforcement |
|-----------|-------------|
| `validation_only` → all flags false | ValidationError on violation |
| `execution_disabled` → execution_supported false | ValidationError on violation |
| `governed_execution` → execution_supported true | ValidationError on violation |
| `machine_output_supported` always false | ValidationError on violation |

### Via Tests

| Invariant | Test Class |
|-----------|------------|
| 7B entries have execution_supported=False | TestExecutionInvariants |
| 7B entries have artifact_generation_supported=False | TestExecutionInvariants |
| MRP-3A entries have execution_supported=True | TestMRP3AInvariants |
| MRP-3A entries have artifact_generation_supported=True | TestMRP3AInvariants |
| All entries have machine_output_supported=False | TestExecutionInvariants, TestMRP3AInvariants |
| No DXF/G-code tokens generated | TestNoExecutionTokens |
| Registry does not affect operation registry | TestRegistryIsolation |
| 7B entries require authorization | TestAuthorizationField |
| MRP-3A entries skip authorization (governed) | TestAuthorizationField |

---

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/cam/translators/capabilities` | List all capabilities |
| `GET /api/cam/translators/capabilities/summary` | Lightweight summary |
| `GET /api/cam/translators/capabilities/{id}` | Single capability |
| `GET /api/cam/translators/ids` | List all IDs |
| `GET /api/cam/translators/by-category/{cat}` | Filter by category |
| `GET /api/cam/translators/by-output/{class}` | Filter by output |
| `GET /api/cam/translators/for-operation/{op}` | Filter by operation |

---

## Registry Separation

```
┌─────────────────────────────────────────────────────────────────────┐
│               CAM_OPERATION_REGISTRY (Governance)                    │
│  Location: app/cam/cam_operation_registry.py                        │
│  Authority: Lifecycle, policy, promotion                            │
│  Entries: nut_slot, drilling                                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│            TRANSLATOR_CAPABILITY_REGISTRY (Execution)               │
│  Location: app/cam/translator_capability_registry.py                │
│  Authority: Execution capabilities (declarative in 7B)              │
│  Entries: dxf_r12, dxf_r2000, gcode_grbl_placeholder               │
└─────────────────────────────────────────────────────────────────────┘
```

These registries are separate and do not cross-reference in 7B.

---

## What 7B Does NOT Do

- No translator execution
- No postprocessor execution
- No DXF generation
- No G-code generation
- No artifact persistence
- No machine output
- No approval automation
- No imports from dxf_compat, ezdxf, or postprocessor utilities

**Declarative only. No execution.**

---

## Future Implementation Path

When execution is eventually implemented:

1. **8A**: Sandbox infrastructure
2. **8B**: DXF translator wrapper (around dxf_compat)
3. **8C**: Authorization token model
4. **8D**: Artifact persistence with provenance
5. **8E**: Postprocessor framework
6. **8F**: Controller-specific postprocessors
7. **8G**: Machine output packaging

Each step requires architecture review before implementation.

---

## Test Coverage

```bash
cd services/api
python -m pytest tests/cam/test_translator_capability_registry.py -v
```

Tests cover:
- Registry entry existence
- 7B invariant enforcement
- Model validation
- Helper function behavior
- Registry isolation
- No execution tokens
- All endpoints
- Authorization field

---

## Integration with Existing Systems

### Existing Validation Modules (unchanged)

| Module | Status |
|--------|--------|
| `dxf_translator_boundary.py` | Unchanged — validation gate |
| `postprocessor_boundary.py` | Unchanged — validation gate |
| `export_object_to_dxf_adapter.py` | Unchanged — compatibility adapter |
| `dxf_compat.py` | Unchanged — not imported by 7B |

### Existing Governance Modules (unchanged)

| Module | Status |
|--------|--------|
| `cam_operation_registry.py` | Unchanged — separate registry |
| `cam_lifecycle_policy_engine.py` | Unchanged |
| `cam_lifecycle_audit_ledger.py` | Unchanged |
| `cam_promotion_evidence.py` | Unchanged |

---

## Acceptance Criteria (Met)

- [x] Translator capability registry exists
- [x] DXF translators are declaratively represented
- [x] G-code/postprocessor placeholder is represented but disabled
- [x] Endpoints expose registry state
- [x] No artifact generation exists
- [x] No execution capability exists
- [x] Model validators enforce invariants
- [x] All CAM tests pass

---

*Translator Capability Registry Handoff — CAM 7B — 2026-05-13*
