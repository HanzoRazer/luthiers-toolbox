# Contracts Changelog

Every change to a `contracts/*.schema.json` or its `.schema.sha256` must be recorded here,
naming each affected contract. Enforced by
`scripts/ci/check_contracts_governance.py` (`CHANGELOG_REQUIRED` /
`CHANGELOG_MISSING_MENTIONS`).

Newest first.

---

## 2026-08-19 — MESH-MAT-001 material evidence research surface

Three new research-only contracts. None of them carries CAM, manufacturing, or QA
authority: each pins `research_only` to `true` and is explicitly separate from
`qa_core` and `cam_policy`.

### Added

- **`material_evidence`** — specimen material evidence envelope. Normalized SI units,
  ADR-0012 epistemic vocabulary, provenance references.
- **`material_prediction`** — orthotropic plate prediction sidecar. `epistemic_status`
  is fixed at `predicted`.
- **`prediction_residual`** — measured-vs-predicted modal residual sidecar.

### Notes on the shape of these three

- `material_evidence` encodes the provenance requirement **conditionally**: an
  evidence value whose `epistemic_status` is `observed` or `derived` must carry
  `source_artifact_id` or `source_hash`. This is a runtime rule in the importer, and
  expressing it in the schema keeps the two from disagreeing — a schema-valid payload
  should never fail at import. `source_artifact_id` / `source_hash` also carry
  `minLength: 1`, because the importer treats an empty string as absent.
- `material_evidence.research_only` is `const: true` rather than
  `default: true`. The importer rejects `false`; the schema now says the same thing.
- `material_prediction` and `prediction_residual` are `additionalProperties: false` at
  the top level, so undeclared fields cannot drift into a published sidecar. Extend
  them by changing the contract, not by adding keys in passing.
- `prediction_residual` residual entries carry `match_basis`
  (`mode_indices` | `nearest_frequency`), which tells a consumer whether a pairing came
  from explicit mode labels or from a frequency-proximity guess. It is absent when
  there is no pairing at all.
