# GOV-CONVERGE-007-A Dev Handoff - Legacy Canonical Creation Retirement

**Date:** 2026-07-04  
**Base:** `origin/main` at `bed827ab` (`docs(ci): close CI-RED-019 and CI-RED-003 in SPRINTS.md by current-main witness (#187)`)  
**Lane:** Governance / C2 canonical geometry authority migration safety net  
**Target:** `GOV-CONVERGE-007-A`  
**Status:** Dev-ready handoff. Do not treat this document as an implementation commit.

---

## 1. Goal

Retire the remaining normal path for creating canonical geometry without process-approval metadata.

PR #182 and #185 established the process-approved canonical authority model and guarded fabricated process metadata. The remaining safety-net gap is that the old canonical creation path is still a normal API and test fixture path:

- `POST /api/cam/geometry-authority/references/canonical`
- `create_canonical_geometry_reference(...)`

This work should make the process-approved path the only green-path creator for canonical geometry, while preserving the old factory only for explicit transition/legacy-warning tests.

---

## 2. Scope

### In Scope

1. Hard-retire or transition-fence the legacy HTTP endpoint:
   - `services/api/app/routers/cam/geometry_authority_router.py`
   - `POST /references/canonical`

2. Migrate normal tests in:
   - `services/api/tests/cam/test_geometry_authority_references.py`
   - away from `create_canonical_geometry_reference(...)`
   - toward the existing `_process_approved_canonical_reference(...)` helper or a new process-approved request helper.

3. Keep only explicit legacy-transition tests on the old factory:
   - `services/api/tests/cam/test_canonical_geometry_process_approval.py`
   - `services/api/tests/cam/test_canonical_geometry_process_boundaries.py`
   - any remaining legacy test cluster in `test_geometry_authority_references.py` should be named as such.

4. Update guidance strings/docstrings that still point users at the old factory/endpoint as if it were a normal path.

5. Add a per-PR CBSP21 manifest under:
   - `.cbsp21/patches/gov-converge-007a-legacy-canonical-retirement.json`

6. Update `SPRINTS.md` only if the PR actually closes part of GOV-CONVERGE-007. Do not close the whole item unless the restore trigger is fully met.

### Out of Scope

- Do not flip missing process-approval metadata from warning to RED.
- Do not implement persistent approval-record storage or registry authenticity lookup.
- Do not add the authorized approver allowlist / authorization anchor.
- Do not reopen C2 geometry-origin governance.
- Do not change solver, CAM, export, DXF/SVG/STEP, or IBG behavior.
- Do not rename `PROPOSED_*` constants unless the implementation naturally touches that module and the rename is low-risk.

---

## 3. Current Ground Truth

Verified on `origin/main`:

- `SPRINTS.md` keeps `GOV-CONVERGE-007` open and lists the first closure item as:
  - migrate or retire legacy `POST /api/cam/geometry-authority/references/canonical`.
- `services/api/app/routers/cam/geometry_authority_router.py` still imports `create_canonical_geometry_reference` and uses it in `create_canonical_reference`.
- The process-approved endpoint already exists:
  - `POST /api/cam/geometry-authority/references/canonical/process-approved`
- The generic `/references` endpoint already rejects fake process-approved canonical metadata.
- `services/api/app/cam/canonical_geometry_process_policy.py` records the C2 vocabulary as ratified on 2026-07-04:
  - `body-geometry-canonicalization`
  - `v1`
  - `c2-process-exclusive-canonical-authority-v1`
- Missing process-approval metadata is currently warning-only in `validate_geometry_authority_reference`.
- `test_geometry_authority_references.py` still has many normal-path uses of `create_canonical_geometry_reference`.

---

## 4. Decisions For This Work

### Decision 1 - Retire the legacy HTTP creator, do not remove the route

Recommended behavior:

- Keep `POST /api/cam/geometry-authority/references/canonical` mounted.
- Change it to return `410 Gone` with a clear message pointing to:
  - `/api/cam/geometry-authority/references/canonical/process-approved`

Why:

- A 410 is safer than a 404 because clients get a deliberate migration signal.
- Keeping the route avoids endpoint-count churn.
- It stops new legacy canonical refs at the API boundary.
- It does not require warning-to-RED yet.

### Decision 2 - Keep the legacy factory, but make it transition-only

Do not delete `create_canonical_geometry_reference(...)` in this pass.

Use it only in tests that explicitly assert transition behavior:

- legacy canonical refs warn, not RED;
- legacy refs lack process metadata;
- the strict RED flip remains deferred.

### Decision 3 - Process-approved helper is the green fixture path

Any test that simply needs "a valid canonical reference" should use:

- `_process_approved_canonical_reference(...)`, or
- a new helper returning process-approved request payloads for router tests.

### Decision 4 - Strict RED timing remains a human/governance decision

Do not make missing process metadata a blocking issue in this PR.

This PR can reduce the remaining blast radius enough to make a later strict-RED PR feasible, but it should not take that decision itself.

### Decision 5 - Authenticity remains unverified pending governance

Do not claim verified canonical authority. Process-approved refs still carry:

```text
authentication = unverified_pending_governance
```

The authorized-approver anchor is a later PR.

---

## 5. File-By-File Patch Plan

### 5.1 `services/api/app/routers/cam/geometry_authority_router.py`

Patch:

1. Remove the import of `create_canonical_geometry_reference` if no longer used.
2. Keep `CreateCanonicalReferenceRequest` only if the 410 endpoint still accepts a typed body. Prefer keeping it for OpenAPI compatibility unless tests prove simpler removal is safe.
3. Change `create_canonical_reference(...)` to raise:

```python
raise HTTPException(
    status_code=410,
    detail=(
        "Legacy canonical reference creation is retired under GOV-CONVERGE-007-A. "
        "Use /api/cam/geometry-authority/references/canonical/process-approved "
        "with a governed approval record."
    ),
)
```

4. Do not register a reference in this endpoint.
5. Leave the process-approved endpoint untouched except for small shared helper reuse if needed.

Acceptance:

- Legacy endpoint returns 410.
- No legacy canonical reference is registered through the API.
- Process-approved endpoint still returns 200 for valid requests.

### 5.2 `services/api/tests/cam/test_geometry_authority_references.py`

Patch:

1. Keep `_process_approved_canonical_reference(...)`.
2. Add helper:

```python
def _process_approved_canonical_payload(...):
    return {
        "owning_domain": "boe",
        "approval_record": {
            "canonical_process_id": PROPOSED_CANONICAL_PROCESS_ID,
            "canonical_process_version": PROPOSED_CANONICAL_PROCESS_VERSION,
            "approval_rule_id": PROPOSED_APPROVAL_RULE_ID,
            "source_geometry_id": "geo-router-source",
            "provenance_hash": "prov-router",
            "process_inputs_hash": "inputs-router",
            "approver_id": "human:router-test",
        },
        "description": "...",
    }
```

3. Convert normal reference/registry/CI-summary tests from `create_canonical_geometry_reference(...)` to `_process_approved_canonical_reference(...)`.
4. Convert router tests that currently call `/references/canonical` for setup to `/references/canonical/process-approved`.
5. Replace `test_create_canonical_reference` router expectation:
   - old: `200`
   - new: `410`
   - assert the response names the process-approved endpoint.
6. Keep at most one explicit test group for legacy factory behavior, named clearly, for example:

```python
class TestLegacyCanonicalTransition:
    ...
```

Acceptance:

- A grep should show `create_canonical_geometry_reference` in this file only in the explicit legacy transition cluster, or not at all if all legacy factory tests live in the two dedicated process files.

### 5.3 `services/api/tests/cam/test_canonical_geometry_process_approval.py`

Patch:

1. Keep `test_canonical_reference_without_process_approval_warns_in_transition_mode`.
2. Update the module docstring if needed:
   - C2 vocabulary is ratified, not proposed.
   - transition mode still warns, not RED.
3. Do not convert this legacy-warning test.

Acceptance:

- This file remains the primary proof that warning-only transition mode is intentionally preserved.

### 5.4 `services/api/tests/cam/test_canonical_geometry_process_boundaries.py`

Patch:

1. Keep the naked legacy canonical reference test if it explicitly proves the warning/transition boundary.
2. Rename test if needed so its purpose is obvious.
3. Do not use the legacy factory for ordinary setup.

Acceptance:

- Any legacy factory use is visibly negative/transition coverage.

### 5.5 `services/api/app/cam/geometry_authority_reference.py`

Patch:

1. Update `create_canonical_geometry_reference(...)` docstring:
   - replace "PROPOSED" with ratified status where appropriate.
   - state that runtime/API creation is retired.
   - state that the factory is retained only for compatibility and explicit transition tests.
2. Do not change model behavior in this pass unless tests require it.

Acceptance:

- The old factory no longer reads like a recommended path.

### 5.6 `services/api/app/cam/geometry_authority_validation.py`

Patch:

1. Update comments/docstrings from "PROPOSED" to ratified status where needed.
2. Preserve warning-not-RED behavior.
3. Do not move missing metadata into `blocking_issues`.

Acceptance:

- Existing transition-mode tests still prove warning-only behavior.

### 5.7 `services/api/app/cam/canonical_geometry_process_approval.py`

Patch:

Optional. Only touch if wording is confusing in nearby tests:

- The top-level module already records ratification.
- Avoid broad doc churn.

Acceptance:

- No behavior change.

### 5.8 `SPRINTS.md`

Patch only after implementation is complete.

Recommended update:

- In `GOV-CONVERGE-007`, mark item 1 as closed by the new PR:
  - legacy HTTP canonical creation retired with 410.
- Mark item 2 as partially or fully closed depending on the final grep result.
- Do not close item 3:
  - warning-to-RED timing still deferred.
- Do not close item 5:
  - persistent authenticity lookup still deferred.

Acceptance:

- `GOV-CONVERGE-007` remains OPEN unless every restore-trigger line is actually satisfied.

### 5.9 `.cbsp21/patches/gov-converge-007a-legacy-canonical-retirement.json`

Add a per-PR manifest.

Expected paths:

```json
{
  "paths_in_scope": [
    "services/api/app/cam/",
    "services/api/app/routers/cam/",
    "services/api/tests/cam/",
    "SPRINTS.md"
  ],
  "files_expected_to_change": [
    "services/api/app/routers/cam/geometry_authority_router.py",
    "services/api/app/cam/geometry_authority_reference.py",
    "services/api/app/cam/geometry_authority_validation.py",
    "services/api/tests/cam/test_geometry_authority_references.py",
    "services/api/tests/cam/test_canonical_geometry_process_approval.py",
    "services/api/tests/cam/test_canonical_geometry_process_boundaries.py",
    "SPRINTS.md"
  ]
}
```

Trim the expected list to actual touched files before opening the PR.

---

## 6. Utilities And Search Commands

Use these as witnesses during implementation.

### Legacy factory call-site audit

```powershell
rg -n "create_canonical_geometry_reference" services/api/app services/api/tests SPRINTS.md
```

Expected after patch:

- no production/router usage;
- test usage only in explicit legacy transition tests.

### Legacy endpoint audit

```powershell
rg -n "references/canonical|process-approved|CreateCanonicalReferenceRequest" services/api/app/routers/cam services/api/tests/cam
```

Expected after patch:

- legacy endpoint exists but returns 410;
- normal setup uses `/references/canonical/process-approved`.

### Focused tests

Run from `services/api`:

```powershell
py -3.11 -m pytest tests/cam/test_geometry_authority_references.py -q
py -3.11 -m pytest tests/cam/test_canonical_geometry_process_approval.py tests/cam/test_canonical_geometry_process_boundaries.py -q
```

### Wider API witness

If the focused tests pass:

```powershell
py -3.11 -m pytest tests/cam/test_geometry_authority_references.py tests/cam/test_canonical_geometry_process_approval.py tests/cam/test_canonical_geometry_process_boundaries.py -q
```

If local environment allows, run the normal API slice used by this lane. If it fails for an unrelated known environment issue, report the exact failure and let CI be the final witness.

### CBSP21 gates

Use the per-PR manifest. From repo root:

```powershell
py -3.11 scripts/ci/check_cbsp21_patch_input.py --base origin/main --head HEAD
$files = git diff --name-only origin/main...HEAD
py -3.11 scripts/ci/check_cbsp21_gate.py --changed-files $files
```

Use the three-dot diff. The gates are base-sensitive.

---

## 7. Test Cases To Add Or Update

### Router behavior

1. `test_legacy_canonical_endpoint_is_retired`
   - POST `/api/cam/geometry-authority/references/canonical`
   - expect `410`
   - response mentions process-approved endpoint
   - no reference is registered as a side effect

2. `test_create_process_approved_canonical_reference`
   - stays `200`
   - proves process metadata is present
   - proves authentication remains `unverified_pending_governance`

3. `test_list_references`
   - setup with process-approved endpoint or helper
   - list still includes canonical refs

4. `test_validate_reference`
   - setup with process-approved endpoint or helper
   - validation remains green/yellow as expected

5. `test_get_ci_summary`
   - setup with process-approved endpoint or helper
   - CI summary does not rely on legacy factory/endpoint

### Factory / validation behavior

6. `test_canonical_reference_without_process_approval_warns_in_transition_mode`
   - keep or strengthen
   - proves strict RED has not been pulled forward

7. `test_legacy_factory_is_transition_only`
   - optional naming wrapper
   - asserts warning wording names process-approved factory

8. `test_process_approved_reference_remains_hash_bound_to_approval_record`
   - already likely covered; keep green if touched.

### Audit / regression

9. Add a grep-style guard only if the repo already has a suitable pattern.
   - Avoid adding a brittle custom scan unless needed.
   - A focused test can assert the route returns 410; that is the main protection.

---

## 8. Rollout Order

1. Start from fresh `origin/main`.
2. Confirm open PRs are not touching the same files. As of this handoff, only PR #188 and #189 are open and they are performance branches.
3. Add the CBSP21 per-PR manifest.
4. Patch the router to retire the legacy endpoint with 410.
5. Migrate router tests to process-approved setup.
6. Migrate non-router normal tests to process-approved helper.
7. Isolate any remaining legacy factory tests into explicit transition/negative clusters.
8. Update docstrings/comments only where they would otherwise mislead a developer into using the legacy path.
9. Run focused tests.
10. Run CBSP21 gates with `origin/main...HEAD`.
11. Update `SPRINTS.md` with only the closure actually earned.
12. Push PR and hold merge until CI is green.

---

## 9. Stop-And-Ask Conditions

Stop and ask before proceeding if any of these appear:

1. A real production/client path still depends on `POST /references/canonical` returning `200`.
2. Tests force the missing-process-metadata warning to become RED.
3. Any implementation needs an authorized approver allowlist or persistent approval-record lookup.
4. Removing or changing the route would require an endpoint-count ratchet bump.
5. A proposed fix touches solver/CAM/export/IBG behavior.
6. CI failures indicate C2 process-approved refs are not accepted by registry/validation consumers.

---

## 10. Done Definition

This target is done when:

- Legacy API canonical creation no longer creates canonical refs.
- Process-approved API creation remains green.
- Normal green-path tests use process-approved references.
- Remaining legacy factory usage is explicit transition/negative coverage.
- Missing process-approval metadata still warns, not RED.
- `SPRINTS.md` records the partial GOV-CONVERGE-007 closure without closing the whole item prematurely.
- CBSP21 gates and focused tests pass.

---

## 11. Follow-Up After GOV-CONVERGE-007-A

If this lands cleanly, the next GOV-CONVERGE-007 items are:

1. Decide warning-to-RED timing for missing process metadata.
2. Scope PR-2 authorized approver anchor / allowlist.
3. Scope persistent approval-record authenticity lookup.
4. Optionally rename `PROPOSED_*` identifiers now that vocabulary is ratified.

