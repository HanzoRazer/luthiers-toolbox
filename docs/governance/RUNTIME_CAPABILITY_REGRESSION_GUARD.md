# Runtime Capability Regression Guard

**Sprint**: MRP-5X  
**Status**: ACTIVE  
**Date**: 2026-05-23

## Purpose

This document describes the runtime capability regression guard — a focused test suite that protects the MRP-5V capability gate from silent bypass regressions.

## What This Guard Protects

The regression guard enforces these invariants:

| Invariant | Test | Failure Mode Prevented |
|-----------|------|------------------------|
| Unknown capability rejected | `test_resolver_rejects_unknown_capability` | Silent pass-through of unregistered capabilities |
| Disabled capability rejected | `test_resolver_rejects_disabled_capability` | Bypass of capability enable/disable controls |
| Replay-unsafe rejected in replay mode | `test_resolver_rejects_replay_unsafe_in_replay_mode` | Non-deterministic replay execution |
| Replay-unsafe allowed in normal mode | `test_replay_unsafe_allowed_in_normal_mode` | Over-restriction in normal execution |
| Duplicate capability ID rejected | `test_duplicate_id_raises_at_registration` | ID collision causing unpredictable resolution |
| Manifest stable across calls | `test_manifest_identical_across_calls` | Non-deterministic capability inventory |
| Policy ordering deterministic | `test_capability_list_is_sorted` | Non-deterministic policy evaluation |
| Resolver returns metadata only | `test_resolution_result_has_no_callable` | Capability resolution returning executables |
| Source registries not mutated | `test_source_capabilities_unchanged_after_federation` | Federation corrupting domain registries |
| Service requires capability resolution | `test_service_rejects_when_capability_resolution_fails` | Service bypassing capability gate |

## What This Guard Does NOT Protect

| Area | Reason | Covered By |
|------|--------|------------|
| Geometry correctness | Domain-specific, not runtime invariant | Domain test suites |
| CAM output correctness | Domain-specific, not runtime invariant | CAM integration tests |
| DXF format parity | Separate lifecycle concern | DXF lifecycle guards |
| Full behavioral execution | Integration-level concern | `test_runtime_spine_full_verification.py` |
| Governance timeouts | Infrastructure concern | Infrastructure monitoring |
| Policy semantic correctness | Policy design concern | Policy unit tests |

## Test File Location

```
services/api/tests/cam/test_runtime_capability_regression_guard.py
```

## How to Run

```bash
# Quick regression check
pytest services/api/tests/cam/test_runtime_capability_regression_guard.py -q

# Verbose output
pytest services/api/tests/cam/test_runtime_capability_regression_guard.py -v

# With coverage
pytest services/api/tests/cam/test_runtime_capability_regression_guard.py --cov=app.cam.runtime_capabilities
```

## How to Intentionally Update Expectations

If a capability contract change is intentional:

1. **Verify the change is authorized** — Check that the change follows governance policy
2. **Update the test** — Modify the assertion to match new expected behavior
3. **Document the change** — Add a note in the commit message explaining why
4. **Do not delete tests** — If an invariant no longer applies, mark it skip with reason

Example:

```python
@pytest.mark.skip(reason="MRP-6X: Capability IDs now support hierarchical format")
def test_capability_list_is_sorted(self):
    ...
```

## Known Pre-Existing Runtime Spine Mismatches

| Mismatch | Status | Notes |
|----------|--------|-------|
| MRP-5U not completed | OBSERVATION | MRP-5V implemented missing functionality |
| Service/replay namespaces empty | FOLLOW_UP | Namespaces exist but not populated |
| Dynamic capability loading | FOLLOW_UP | All capabilities statically registered |

## Relationship to MRP-5X Release Verification

```
test_runtime_capability_regression_guard.py
    |
    |-- Focused invariant tests (11 tests)
    |-- Guards capability bypass regressions
    |-- Does NOT duplicate integration tests
    |
    v
test_runtime_spine_full_verification.py
    |
    |-- End-to-end verification (19 tests)
    |-- Full spine path validation
    |-- Release boundary checks
    |
    v
MRP_5X_RUNTIME_SPINE_RELEASE_VERIFICATION.md
    |
    |-- Release readiness document
    |-- Status classifications (PASS/OBSERVATION/FOLLOW_UP/REQUIRED_FIX)
    |-- Commit readiness recommendation
```

## Governance Classification

This guard is classified as:

- **Protection level**: STABILIZED
- **Change policy**: Changes require regression verification
- **Ownership**: Runtime spine maintainers

## Expansion Lane Boundaries

The regression guard should remain focused on capability resolution invariants. Future expansion lanes:

| Lane | In Scope | Out of Scope |
|------|----------|--------------|
| Capability resolution | Yes | — |
| Policy enforcement | Yes | Policy semantic design |
| Registry integrity | Yes | Domain registry internals |
| Manifest determinism | Yes | Manifest content semantics |
| Service integration | Gate enforcement only | Full service behavior |

Do not expand this guard into full behavioral testing. That belongs in `test_runtime_spine_full_verification.py`.
