# Phase 0 — policy and resolver ownership

Checked: 2026-10-22. Tree: `origin/main` `8a2f33cb8f2bd869963ae38c23d08fdd2e950722`. Worktree clean. Open pull requests: none.

Search:

```bash
rg -n "run_beginner_proposal|validate_proposal|ValidationPolicyV1|EvidenceResolver|evidence_resolver|advisory_allowed|evidence_required" services/api packages/client
```

## Answers

| Question | Answer |
| --- | --- |
| Production-owned evidence resolver | None. The protocol `EvidenceResolver` lives in `services/api/app/physical_engineering/evidence.py`. The only implementation is `InMemoryEvidenceResolver`. Its stored type, `StoredEvidenceArtifact`, says it exists for deterministic tests and is not a database record. No other class implements `resolve(self, ref: EvidenceRef)`. |
| Approved production `ValidationPolicyV1` | None. The only call site is `_policy()` in `services/api/tests/physical_engineering/test_physical_engineering_proposal_v1.py`. `policy.py` states that its numeric fields are Phase I test thresholds with no production engineering authority, and that the gate supplies no numeric defaults. `docs/physical_engineering/PEP-V1-HARDEN-001.md` repeats that. |
| Physical-engineering router | None. `services/api/app/physical_engineering/` has no router. The package is not mounted from `app/main.py`. `PEP-V1-HARDEN-001.md` says the gate is not mounted on a route. |
| Guided or MVS client surface | None for this workflow. `packages/client` has no physical-engineering review route. `components/guided/GuidedWorkflow.vue` is a generic step shell. Its production user in tree is `components/guided/workflows/DxfToGcodeWorkflow.vue`, a DXF-to-G-code flow. That is not an MVS host. |
| Request or run identifier utility | Not selected. This slice does not add a route, so no identifier helper was reused. |
| Standard API error envelope | Not selected. This slice does not add a route. |
| Evidence references resolvable without persistence changes | No. A resolver needs stored artifact bytes and metadata. The repository has fixture bytes inside tests and calculator functions such as `plate_modal_frequency`. A calculator estimate is not a stored evidence artifact, and promoting the test store into a route would invent the measurements. |

## Stop conditions that fired

- No production-approved validation policy exists.
- No production evidence resolver exists.
- A route would need a friendly or default policy, which this order forbids.
- Evidence would have to be represented with fixture or calculated stand-ins.
- The visible guided UI home is a CAM workflow, unrelated to this MVS slice.

These also stayed true: no other open PR owns the surface; the browser was not given a way to submit thresholds; the client was not taught `validate_proposal()` semantics.

## What was not changed

`beginner_proposal_harness.py`, `tools/grounding_agent`, the proposal gate, headstock files, `MAINT-DEFER-017`, and `MAINT-DEFER-018`.

## Smallest next prerequisite

One later order, before any review endpoint, must land both of these as production-owned dependencies:

1. An owner-approved `ValidationPolicyV1` construction, with its own identity and provenance. The test helper's thresholds are not that policy.
2. A production `EvidenceResolver` that reads stored evidence artifacts and recomputes their digests. `InMemoryEvidenceResolver` can back tests of that resolver. It cannot be the production dependency.

Until both exist, `POST /api/physical-engineering/beginner-proposal/review` stays unbuilt.
