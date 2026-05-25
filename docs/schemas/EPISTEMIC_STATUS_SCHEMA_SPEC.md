# Epistemic Status Schema Specification

**Status:** SCHEMA SPEC ONLY — not broadly implemented  
**Date:** 2026-05-24  
**Constitutional Source:** tap_tone_pi ADR-0012  
**Cross-Reference:** [`docs/handoffs/imports/constitutional_stabilization_do_77_82/ADR-0012-epistemic-status-taxonomy.md`](../handoffs/imports/constitutional_stabilization_do_77_82/ADR-0012-epistemic-status-taxonomy.md)

---

## Purpose

This document specifies the optional `epistemic_status` field for luthiers-toolbox artifacts. The field aligns with tap_tone_pi ADR-0012 (Epistemic Status Taxonomy).

**Implementation scope:** Schema specification only. Broad implementation is deferred until cross-repo data flow creates pressure.

**Exception:** IBG candidate/review artifacts include this field as part of the confidence vocabulary migration.

---

## Field Definition

### epistemic_status

| Property | Value |
|----------|-------|
| Type | `string` |
| Required | No (optional) |
| Default | `"heuristic"` for advisory outputs |

### Allowed Values

| Value | Authority Level | Description |
|-------|-----------------|-------------|
| `observed` | Measurement-authoritative | Directly captured from physical sensor |
| `derived` | Computationally authoritative | Mathematical transform of observed data |
| `estimated` | Approximation only | Inferential approximation |
| `predicted` | Model-dependent | Model-generated future/inferred state |
| `heuristic` | No authority | Advisory/non-authoritative guidance |
| `operator_annotated` | Operator authority only | Human judgment or annotation |
| `externally_sourced` | External authority | Imported from outside the system |

### Constitutional Constraints

From ADR-0012:

1. **Status cannot elevate through combination** — the result takes the lowest authority status of any input
2. **HEURISTIC cannot return upward** — once heuristic, always heuristic for that derivation chain
3. **Only physical capture creates OBSERVED** — no system path may upgrade to observed
4. **Forbidden transitions** — `predicted → observed`, `estimated → derived`, `any → canonical/validated/approved`

---

## Schema Location

When implemented, the field appears in:

```json
{
  "epistemic_status": "heuristic",
  "_epistemic_status_reason": "Candidate ranking score — sorting relevance only"
}
```

### IBG Candidate Artifacts (Implemented)

```json
{
  "candidate_id": "bec_...",
  "candidate_rank": 0.85,
  "epistemic_status": "heuristic",
  "_rank_is_heuristic": true,
  "confidence": {
    "value": 0.85,
    "confidence_type": "heuristic",
    "interpretation": "Candidate ranking score..."
  }
}
```

---

## Non-Implications (Constitutional)

High `epistemic_status` does NOT imply:

| Does NOT Imply | Reason |
|----------------|--------|
| Correctness | Epistemic status describes origin, not truth |
| Approval | Status does not authorize downstream use |
| Execution authority | No epistemic status authorizes machine action |
| Review bypass | Human review may still be required |
| IBG memory eligibility | Requires explicit governance ratification |

---

## Cross-Repo Alignment

### tap_tone_pi ADR-0012 Mapping

| tap_tone_pi | luthiers-toolbox |
|-------------|------------------|
| `OBSERVED` | `observed` |
| `DERIVED` | `derived` |
| `ESTIMATED` | `estimated` |
| `PREDICTED` | `predicted` |
| `HEURISTIC` | `heuristic` |
| `OPERATOR-ANNOTATED` | `operator_annotated` |
| `EXTERNALLY-SOURCED` | `externally_sourced` |

### CAM Authority Block Alignment

CAM authority blocks use `execution_authority_claim: false`. Epistemic status is orthogonal — it describes data origin, not execution permission.

---

## Implementation Guidance

### When to Add

Add `epistemic_status` to artifacts when:

1. Touching IBG candidate/review artifacts (already implemented)
2. Creating cross-repo data exports
3. Building historical learning systems
4. Implementing provenance chain tracking

### When NOT to Add

Do not add `epistemic_status` for:

1. Internal computational intermediates
2. Test fixtures
3. R&D sandbox outputs (already excluded)
4. UI state (not persisted artifacts)

---

## Future Work

| Item | Status | Notes |
|------|--------|-------|
| Broad implementation | Deferred | Wait for cross-repo integration pressure |
| Validation in export paths | Deferred | Requires IBG R1 ratification first |
| Historical learning governance | Deferred | Wait for implementation need |

---

**Spec Version:** 1.0.0  
**Owner:** luthiers-toolbox governance
