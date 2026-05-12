# CAM Dev Order 6I: Lifecycle Policy Engine Handoff

**Date:** 2026-05-11
**Status:** Complete
**Predecessor:** 6H (Capability Registry)

## Summary

Converts the capability registry from descriptive metadata into active lifecycle policy enforcement. The policy engine controls lifecycle stages BEFORE they run — it does not run disallowed stages and report violations afterward.

## Files Created

- `app/cam/cam_lifecycle_policy_engine.py` — Policy evaluation runtime
- `tests/cam/test_lifecycle_policy_engine.py` — Policy engine tests (32 tests)

## Files Modified

- `app/cam/export_lifecycle_orchestrator.py` — Integrated policy engine
- `tests/cam/test_export_lifecycle.py` — Updated error message assertions
- `tests/cam/test_drilling_export_lifecycle.py` — Updated error message assertions
- `tests/cam/test_operation_capability_registry.py` — Updated error message assertions

## Architecture

### Declaration vs Enforcement

| Component | Purpose |
|-----------|---------|
| Capability Registry (6H) | Declares what an operation claims |
| Policy Engine (6I) | Enforces what the lifecycle allows |

### LifecyclePolicyEvaluation Model

```python
LifecyclePolicyEvaluation(
    operation="nut_slot",
    allowed=True,
    lifecycle_gate="green",
    exportability_class="governed_export",
    maturity="canonical",
    policy_checks=["operation_registered: PASS", ...],
    blocking_issues=[],
    warnings=[],
    
    # Stage permissions
    preview_allowed=True,
    export_object_allowed=True,
    machine_validation_allowed=True,
    translator_validation_allowed=True,
    rmos_persistence_allowed=True,
    
    # Hard prohibitions (always false)
    machine_output_allowed=False,
    translator_execution_allowed=False,
)
```

### Orchestrator Flow (6I)

```
0. evaluate_lifecycle_policy()
1. If policy RED → return early with lifecycle-shaped report
2. Generate preview (if preview_allowed)
3. Build export object (if export_object_allowed and preview GREEN)
4. Run machine validation (if machine_validation_allowed)
5. Run translator validation (if translator_validation_allowed)
6. Aggregate lifecycle report
7. Persist to RMOS (if rmos_persistence_allowed and persist_to_rmos)
```

## Exportability Class Rules

| Class | preview | export_object | machine_val | translator_val | rmos |
|-------|---------|---------------|-------------|----------------|------|
| preview_only | ✓ | ✗ | ✗ | ✗ | ✗ |
| governed_export | ✓ | ✓ | ✓ | ✓ | ✓ |
| translator_ready | ✓ | ✓ | ✓ | ✓ | ✓ |
| machine_candidate | ✓ | ✓ | ✓ | ✓ | ✓ |

### Special Behavior

- **preview_only**: Returns YELLOW warning, blocks all stages except preview
- **machine_candidate**: Returns YELLOW warning "Operation is a machine-output candidate; execution remains prohibited"
- **experimental/candidate maturity**: Returns YELLOW warning

## Maturity Enforcement

| Maturity | Gate | Warning |
|----------|------|---------|
| canonical | GREEN | None |
| governed | GREEN | None |
| candidate | YELLOW | "Operation maturity is candidate" |
| experimental | YELLOW | "Operation maturity is experimental" |

## RMOS Eligibility Enforcement

If `persist_to_rmos=True` and operation does not support RMOS persistence:
- Policy returns RED
- Blocking issue: "Operation does not permit RMOS persistence"

## Safety Assertions

Always enforced:
- `machine_output_allowed = False`
- `translator_execution_allowed = False`

Even for canonical/machine_candidate/translator_ready operations.

## Policy Response in Lifecycle Report

```json
{
  "lifecycle_gate": "green",
  "export_ready": true,
  "policy_evaluation": {
    "allowed": true,
    "exportability_class": "governed_export",
    "maturity": "canonical",
    "preview_allowed": true,
    "export_object_allowed": true,
    "machine_validation_allowed": true,
    "translator_validation_allowed": true,
    "rmos_persistence_allowed": true,
    "machine_output_allowed": false,
    "translator_execution_allowed": false
  }
}
```

## Test Coverage

- 32 new policy engine tests
- 120 total CAM tests passing
- Tests cover:
  - Policy evaluation basics
  - Stage permissions
  - Safety assertions
  - Maturity enforcement
  - RMOS eligibility
  - Orchestrator integration
  - Helper functions
  - preview_only behavior (simulated)
  - machine_candidate behavior

## What 6I Does NOT Do

- No machine execution
- No G-code generation
- No DXF generation
- No translator execution
- No dynamic policy loading
- No external policy config
- No operation auto-promotion

## Guardrail

Policy engine controls lifecycle stages BEFORE they run. Do not run disallowed stages and then report violations afterward.

## Next Steps

Potential 6J work:
- Add preview_only operations to registry
- UI integration with policy evaluation
- Policy-based rate limiting
- Audit logging for policy decisions
