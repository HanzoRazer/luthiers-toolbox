# Deferred policy

Evidence resolution does not create a validation policy.

## Next order

`LTB-MVS-VALIDATION-POLICY-004` is the next separate order. It has to introduce one owner-approved `ValidationPolicyV1`, with a human owner and a source for every numeric field. The test helper `_policy()` in `test_physical_engineering_proposal_v1.py` remains a fixture. Its numbers, including `0.6` and `2.5`, do not become production thresholds because a stored thickness resolved.

This increment's harness test calls that fixture so the existing gate can run. The resolver module does not construct `ValidationPolicyV1`.

## Still blocked

`LTB-MVS-GUIDED-REVIEW-SLICE-002` stays blocked until both this resolver and the policy order exist. PR #454 recorded the stop and did not add a route. This increment also adds no route, client form, or browser write path.

## Not in this patch

- Scientific contradiction tolerances.
- Age-based expiry.
- Confidence scores.
- Ecosystem adoption of `ltb_stored_evidence_artifact` by Physical Engineering Mesh.
- `PEP-MESH-SEAM-003` geometry trust.
- Archtop comparator vocabulary: source-reported, drawing-derived, model-assumption, measured-specimen.
- `MAINT-DEFER-017` and `MAINT-DEFER-018`.
- CAM, DXF, G-code, or manufacturing admission.
