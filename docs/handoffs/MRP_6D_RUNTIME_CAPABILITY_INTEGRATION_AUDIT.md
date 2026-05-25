# MRP-6D: Runtime Capability Integration Audit

**Sprint:** MRP-6D  
**Status:** READY FOR EXECUTION  
**Date:** 2026-05-25  
**Predecessor:** MRP-5V (Runtime Capability Federation), MRP-6A (Post-Merge Verification)

---

## Executive Summary

This handoff defines the audit scope for verifying runtime capability integration across the governed runtime spine. The audit validates that capability resolution gates are properly wired, policy enforcement is consistent, and no capability bypass paths exist.

---

## Audit Scope

### In Scope

| Component | Location | Audit Focus |
|-----------|----------|-------------|
| CapabilityRegistry | `app/cam/runtime_capabilities/registry.py` | Registration integrity |
| CapabilityResolver | `app/cam/runtime_capabilities/resolution.py` | Resolution correctness |
| ExecutionPolicyFederation | `app/cam/runtime_capabilities/policies.py` | Policy enforcement |
| Source Adapters | `app/cam/runtime_capabilities/sources.py` | Registry wrapping |
| CertifiedRuntimeService | `app/cam/runtime_service/service.py` | Capability gate integration |
| Domain Registries | `app/cam/*_registry.py` | Source coverage |

### Out of Scope

| Component | Reason |
|-----------|--------|
| IBG provenance integration | Blocked on R1 ratification |
| Deep geometry compatibility | Future work (not MRP-5V) |
| Dynamic capability loading | Future work |
| CI manifest enforcement | Future work |

---

## Audit Checklist

### 1. Registry Integrity

| Check | Command | Expected |
|-------|---------|----------|
| No duplicate capability IDs | `audit_runtime_capabilities.py` | 0 duplicates |
| All namespaces populated | `audit_runtime_capabilities.py` | operation, translator, adapter present |
| Deterministic manifest | `generate_runtime_manifest.py --verify` | Hash matches |

```bash
python scripts/runtime_provenance/audit_runtime_capabilities.py
python scripts/runtime_provenance/generate_runtime_manifest.py --verify
```

### 2. Resolution Correctness

| Check | Test | Expected |
|-------|------|----------|
| Unknown capability rejected | `test_resolver_unknown_capability` | NOT_FOUND |
| Disabled capability rejected | `test_resolver_disabled_capability` | DISABLED |
| Replay-unsafe in replay mode | `test_resolver_replay_unsafe` | REPLAY_UNSAFE |
| Valid capability resolved | `test_resolver_valid_capability` | RESOLVED |

```bash
pytest services/api/tests/cam/test_runtime_capability_integration.py -v -k resolver
```

### 3. Policy Enforcement

| Policy | Enforced At | Test |
|--------|-------------|------|
| EnabledPolicy | Resolution | `test_policy_enabled` |
| DeterministicPolicy | Resolution | `test_policy_deterministic` |
| ReplaySafetyPolicy | Resolution | `test_policy_replay_safety` |
| CompatibilityTagsPolicy | Resolution | `test_policy_compatibility_tags` |
| RequiredTagsPolicy | Resolution | `test_policy_required_tags` |

```bash
pytest services/api/tests/cam/test_runtime_capability_integration.py -v -k policy
```

### 4. Service Integration

| Check | Location | Expected |
|-------|----------|----------|
| Capability gate present | `CertifiedRuntimeService.execute()` | Gate at step 4 |
| Capability rejection status | `ServiceExecutionStatus` | CAPABILITY_REJECTED exists |
| Resolution report in result | `CertifiedRuntimeResult` | capability_resolution_report field |

```bash
pytest services/api/tests/cam/test_runtime_capability_integration.py -v -k service
```

### 5. Source Adapter Coverage

| Source | Registry | Adapter |
|--------|----------|---------|
| CAM Operations | `cam_operation_registry.py` | `CamOperationCapabilitySource` |
| Translators | `translator_capability_registry.py` | `TranslatorCapabilitySource` |
| Runtime Adapters | `runtime_service/adapters.py` | `AdapterCapabilitySource` |

```bash
pytest services/api/tests/cam/test_runtime_capability_integration.py -v -k source
```

---

## Bypass Detection

### Known Bypass Paths (Must Not Exist)

| Bypass Attempt | Detection | Status |
|----------------|-----------|--------|
| Direct adapter call without resolution | Grep for `adapter.execute` without `resolver.resolve` | AUDIT |
| Capability ID not set (skips resolution) | Grep for `capability_id=None` | ALLOWED (backward compat) |
| Policy mutation | Policy classes immutable | VERIFY |
| Registry mutation after init | `registry._capabilities` not exposed | VERIFY |

### Detection Commands

```bash
# Find direct adapter calls
rg "adapter\.execute" services/api/app/cam/ --context 3

# Find capability_id=None patterns
rg "capability_id=None" services/api/app/cam/

# Verify policy immutability
rg "def __setattr__" services/api/app/cam/runtime_capabilities/policies.py
```

---

## Integration Points

### Upstream Dependencies

```
CertifiedTopology (MRP-5P)
    ↓
RuntimeAdmission (MRP-5M)
    ↓
CapabilityResolution (MRP-5V) ← AUDIT TARGET
    ↓
CertifiedRuntimeService (MRP-5QR)
```

### Downstream Consumers

| Consumer | Integration Point | Status |
|----------|-------------------|--------|
| DXF Export | `CertifiedRuntimeService.execute()` | INTEGRATED |
| Replay Bundle | `execute_replay_bundle.py` | INTEGRATED |
| Translation Pipeline | `translator_capability_registry` | INTEGRATED |

---

## Test Coverage Requirements

### Minimum Coverage

| Category | Required Tests | Current |
|----------|----------------|---------|
| Registry | 7 | 7 |
| Resolution | 6 | 6 |
| Policy | 5 | 4 |
| Source adapters | 5 | 5 |
| Service integration | 3 | 2 |
| **Total** | **26** | **24** |

### Gap Analysis

| Missing Test | Priority |
|--------------|----------|
| `test_policy_required_tags_rejection` | P1 |
| `test_service_capability_rejection_audit_trail` | P1 |

---

## Audit Artifacts

### Required Outputs

| Artifact | Location | Purpose |
|----------|----------|---------|
| Capability manifest | `reports/runtime/capability_manifest.json` | Deterministic inventory |
| Audit report | `reports/runtime/capability_audit.json` | Findings summary |
| Coverage report | `reports/runtime/capability_coverage.html` | Test coverage |

### Generation Commands

```bash
# Generate manifest
python scripts/runtime_provenance/generate_runtime_manifest.py \
    --output reports/runtime/capability_manifest.json

# Generate audit report
python scripts/runtime_provenance/audit_runtime_capabilities.py \
    --json --output reports/runtime/capability_audit.json

# Generate coverage
pytest services/api/tests/cam/test_runtime_capability_integration.py \
    --cov=services/api/app/cam/runtime_capabilities \
    --cov-report=html:reports/runtime/capability_coverage
```

---

## Acceptance Criteria

### Pass Criteria

| Criterion | Threshold |
|-----------|-----------|
| All existing tests pass | 42/42 |
| No duplicate capability IDs | 0 |
| Manifest deterministic | Hash stable |
| No bypass paths detected | 0 |
| Policy enforcement verified | 5/5 policies |
| Service integration verified | Gate present |

### Fail Criteria (Blocking)

| Finding | Severity |
|---------|----------|
| Bypass path exists | BLOCKING |
| Policy not enforced | BLOCKING |
| Duplicate capability ID | BLOCKING |
| Non-deterministic manifest | BLOCKING |
| Service gate missing | BLOCKING |

### Fail Criteria (Non-Blocking)

| Finding | Severity |
|---------|----------|
| Test coverage gap | WARNING |
| Missing namespace population | WARNING |
| Audit script error | WARNING |

---

## Execution Plan

### Phase 1: Automated Verification (30 min)

```bash
# Run all capability tests
pytest services/api/tests/cam/test_runtime_capability_integration.py -v

# Run audit scripts
python scripts/runtime_provenance/audit_runtime_capabilities.py
python scripts/runtime_provenance/audit_runtime_spine.py

# Generate manifest
python scripts/runtime_provenance/generate_runtime_manifest.py --verify
```

### Phase 2: Bypass Detection (20 min)

```bash
# Search for bypass patterns
rg "adapter\.execute" services/api/app/cam/ --context 3
rg "\.resolve\(" services/api/app/cam/runtime_service/

# Verify policy immutability
rg "class.*Policy" services/api/app/cam/runtime_capabilities/policies.py -A 5
```

### Phase 3: Integration Verification (20 min)

```bash
# Run service demo
python scripts/runtime_provenance/run_certified_runtime_service_demo.py

# Verify capability gate in service
rg "capability_resolution" services/api/app/cam/runtime_service/service.py
```

### Phase 4: Documentation (10 min)

- Update audit report with findings
- Document any gaps or issues
- Create remediation tickets if needed

---

## Known Issues

### From MRP-5V

| Issue | Status | Impact |
|-------|--------|--------|
| MRP-5U not completed | DOCUMENTED | MRP-5V absorbed scope |
| Deep geometry compatibility | NOT IMPLEMENTED | Tag-based only |
| Service/replay namespaces empty | NOT POPULATED | Future work |
| Dynamic capability loading | NOT IMPLEMENTED | Static registration |

### Potential Findings

| Finding | Likelihood | Remediation |
|---------|------------|-------------|
| Missing test coverage | MEDIUM | Add tests |
| Stale source adapter | LOW | Update adapter |
| Policy ordering issue | LOW | Reorder policies |

---

## Rollback Plan

If audit reveals blocking issues:

1. Do NOT revert runtime capability code
2. Add bypass flag with governance guard
3. Document issue in blocking findings
4. Create remediation sprint (MRP-6E)

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `MRP_5V_RUNTIME_CAPABILITY_FEDERATION.md` | Implementation details |
| `MRP_5X_RUNTIME_SPINE_RELEASE_VERIFICATION.md` | Release verification |
| `MRP_6A_POST_MERGE_RUNTIME_SPINE_VERIFICATION.md` | Post-merge status |
| `RUNTIME_BOUNDARY_INVENTORY.md` | Boundary inventory |

---

## Audit Scripts Reference

| Script | Purpose |
|--------|---------|
| `audit_runtime_capabilities.py` | Capability registry audit |
| `audit_runtime_service_boundary.py` | Service boundary audit |
| `audit_runtime_spine.py` | Full spine audit |
| `generate_runtime_manifest.py` | Manifest generation |
| `verify_runtime_spine_release.py` | Release verification |

---

## Definition of Done

- [ ] All 42 existing tests pass
- [ ] Audit scripts complete without errors
- [ ] No bypass paths detected
- [ ] Manifest is deterministic
- [ ] Policy enforcement verified (5/5)
- [ ] Service integration verified
- [ ] Coverage gaps documented
- [ ] Audit report generated
- [ ] Handoff updated with findings

---

*MRP-6D: Runtime Capability Integration Audit — 2026-05-25*
