# CAM Dev Order 7C: Translator Policy Integration Handoff

**Date:** 2026-05-13  
**Status:** Complete  
**Predecessor:** 7B (Translator Capability Registry)

---

## Summary

Integrated the translator capability registry from 7B into the DXF translator validation flow. Validation is now registry-gated: unknown translators, wrong-category translators (postprocessors), and wrong-output-class translators fail RED before compatibility checks run.

---

## Core Outcome

```
Translator validation is now registry-aware.
Unknown or invalid translators fail fast with clear diagnostics.
No execution occurs.
```

The registry is the source of truth for translator validity.

---

## Files Modified

| File | Change |
|------|--------|
| `app/cam/export_object_to_dxf_adapter.py` | Added registry-gated validation |

---

## Files Created

| File | Purpose |
|------|---------|
| `tests/cam/test_translator_policy_integration.py` | Registry integration tests |
| `docs/handoffs/CAM_7C_TRANSLATOR_POLICY_INTEGRATION_HANDOFF.md` | This handoff |

---

## Validation Flow (7C)

```
DXF Translator Validation Request
         │
         ▼
┌─────────────────────────────────┐
│ 1. Registry Validation (7C)    │
│    - Translator exists?        │
│    - Category == translator?   │
│    - Output class == dxf?      │
│    - Execution state valid?    │
└─────────────────────────────────┘
         │
    FAIL ├──────────────────────────────► RED (fail fast)
         │
    PASS │
         ▼
┌─────────────────────────────────┐
│ 2. Unit Compatibility          │
│ 3. Geometry Support            │
│ 4. Feature Support             │
└─────────────────────────────────┘
         │
         ▼
    GREEN / YELLOW / RED
```

---

## Registry Validation Checks

| Check | Failure Message |
|-------|-----------------|
| Translator not found | "Unknown translator: 'X' not found in capability registry" |
| Category mismatch | "Translator 'X' is a postprocessor, not a DXF translator" |
| Output class mismatch | "Translator 'X' output class 'gcode' is incompatible with DXF validation" |
| Execution disabled | "Translator 'X' is disabled and cannot be used for validation" |

---

## Integration with Lifecycle

The lifecycle orchestrator calls `evaluate_dxf_translator_compatibility()` at Step 5. With 7C, the registry validation happens automatically:

```
Lifecycle Step 5: Translator Validation
         │
         ▼
evaluate_dxf_translator_compatibility()
         │
         ├── Registry validation (7C) ─► RED if failed
         │
         └── Compatibility checks ─► GREEN/YELLOW/RED
```

No changes to `export_lifecycle_orchestrator.py` were needed — the integration is transparent.

---

## Diagnostic Examples

### Unknown Translator

```json
{
  "gate": "red",
  "compatible": false,
  "blocking_issues": [
    "Unknown translator: 'my_custom_translator' not found in capability registry"
  ]
}
```

### G-code Postprocessor Used for DXF

```json
{
  "gate": "red",
  "compatible": false,
  "blocking_issues": [
    "Translator 'gcode_grbl_placeholder' is a postprocessor, not a DXF translator",
    "Translator 'gcode_grbl_placeholder' output class 'gcode' is incompatible with DXF validation",
    "Translator 'gcode_grbl_placeholder' is disabled and cannot be used for validation"
  ]
}
```

---

## What 7C Does NOT Do

- No translator execution
- No postprocessor execution
- No DXF generation
- No G-code generation
- No artifact generation
- No machine output
- No approval automation
- No registry mutation

**Validation only. No execution.**

---

## Test Coverage

```bash
cd services/api
python -m pytest tests/cam/test_translator_policy_integration.py -v
```

Tests cover:
- Registry validation for known DXF translators
- Unknown translator rejection
- Postprocessor rejection for DXF validation
- Output class validation
- Execution state validation
- Safety assertions (no DXF/G-code tokens)
- Endpoint behavior
- Registry isolation

---

## Acceptance Criteria (Met)

- [x] Translator validation checks registry capability
- [x] Unknown translators fail RED
- [x] Placeholder G-code translator cannot pass DXF validation
- [x] Existing lifecycle validation still works for DXF translators
- [x] No artifacts are generated
- [x] No DXF is generated
- [x] No G-code is generated
- [x] Clear diagnostic messages for architectural violations

---

*Translator Policy Integration Handoff — CAM 7C — 2026-05-13*
