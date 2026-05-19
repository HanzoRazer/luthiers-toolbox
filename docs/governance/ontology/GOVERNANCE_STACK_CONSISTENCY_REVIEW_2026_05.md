# Governance Stack Consistency Review — May 2026

**Status:** CONSISTENCY VERIFICATION  
**Date:** 2026-05-17  
**Scope:** Ontology governance stack internal coherence  
**Track:** Instrument Knowledge Reconciliation (Sandbox)

---

## 1. Purpose

This review verifies internal semantic consistency across the ontology governance stack.

This is:

```
consistency verification
```

NOT:

```
semantic expansion
```

---

## 2. Documents Reviewed

| Document | Layer | Date |
|----------|-------|------|
| `INSTRUMENT_DATA_STORAGE_AUDIT.md` | Storage topology | 2026-05-15 |
| `INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` | Semantic discovery | 2026-05-15 |
| `PROMOTION_REVIEW_MANIFEST_V1.md` | Review governance | 2026-05-15 |
| `ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md` | Governance-state visibility | 2026-05-15 |
| `AUTHORITY_BOUNDARY_REGISTRY_V1.md` | Ownership visibility | 2026-05-16 |

Supporting documents also reviewed:

| Document | Purpose |
|----------|---------|
| `GOVERNANCE_AUTHORITY_HIERARCHY.md` | Repository tier model |
| `ontology_ci_policy.json` | CI enforcement policy |
| `ontology_drift_baseline_2026_05.json` | Accepted drift baseline |

---

## 3. Review Areas

| # | Area | Status |
|---|------|--------|
| 1 | Terminology consistency | FINDING |
| 2 | Status vocabulary collisions | FINDING |
| 3 | Escalation semantics | OK |
| 4 | Authority claims alignment | OK |
| 5 | Non-ownership clauses | OK |
| 6 | Tier semantics | CRITICAL FINDING |
| 7 | Provenance language | OK |
| 8 | Draft/ratification language | OK |
| 9 | Anti-pattern definitions | OK |
| 10 | Cross-references | DOCUMENTATION GAP |

---

## 4. Findings

### Finding 1: Tier Terminology Collision (CRITICAL)

**Location:** Repository-wide

**Issue:** Two different "Tier 1/2/3" models exist in the governance documentation.

#### Model A: Governance Authority Hierarchy

From `GOVERNANCE_AUTHORITY_HIERARCHY.md`:

| Tier | Name | Scope |
|------|------|-------|
| Tier 1 | Structural Invariants | Repository-wide code organization |
| Tier 2 | Domain Governance | Domain-specific (MRP, CAM, RMOS) |
| Tier 3 | Operational Policies | Runtime behavior |

#### Model B: Data Promotion Tiers

From `INSTRUMENT_DATA_STORAGE_AUDIT.md` and ontology documents:

| Tier | Name | Scope |
|------|------|-------|
| Tier 1 | Canonical | Governed, ratified data |
| Tier 2 | Curated | Reviewed, pending promotion |
| Tier 3 | Staging | Non-canonical evidence |

**Collision Risk:**

```
"Tier 1" in governance hierarchy ≠ "Tier 1" in data promotion
```

A reader could conflate:

- "Tier 1 Structural Invariants" (governance model)
- "Tier 1 Canonical" (data promotion model)

These are unrelated concepts sharing the same terminology.

**Severity:** CRITICAL — creates cross-document ambiguity

**Recommendation:** Disambiguate tier terminology:

| Model | Proposed Terminology |
|-------|---------------------|
| Governance Authority | "Authority Tier 1/2/3" or "Governance Level 1/2/3" |
| Data Promotion | "Data Tier 1/2/3" or "Promotion Stage 1/2/3" |

Alternatively, rename data promotion tiers to avoid "Tier" entirely:

| Current | Alternative |
|---------|-------------|
| Tier 1 | Canonical Stage |
| Tier 2 | Curated Stage |
| Tier 3 | Staging Stage |

**Impact on Existing Documents:**

- `INSTRUMENT_DATA_STORAGE_AUDIT.md` — uses "Tier 1/2/3" for data
- `INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` — uses "Tier 1/2/3" for data
- `PROMOTION_REVIEW_MANIFEST_V1.md` — uses "Tier 1/2/3" for data
- `AUTHORITY_BOUNDARY_REGISTRY_V1.md` — uses "Tier 1/2/3" for data
- `GOVERNANCE_AUTHORITY_HIERARCHY.md` — uses "Tier 1/2/3" for governance

**Action Required:** Governance decision on terminology normalization

---

### Finding 2: Status Vocabulary Overlap (MINOR)

**Location:** Observability layer vs. Authority boundary registry

**Issue:** Both documents define status vocabularies with overlapping terms.

#### Observability Layer Drift Lifecycle States

```
DISCOVERED, BASELINED, ACCEPTED_LEGACY, UNDER_REVIEW,
NORMALIZATION_PROPOSED, RATIONALE_REQUIRED, READY_FOR_RATIFICATION,
RATIFIED, DEPRECATED, QUARANTINED
```

#### Authority Boundary Registry Status Values

```
DOCUMENTED, UNRESOLVED, UNDER_REVIEW, PROPOSED, RATIFIED, DEFERRED
```

**Overlapping Terms:**

| Term | Observability Meaning | Authority Boundary Meaning |
|------|----------------------|---------------------------|
| `UNDER_REVIEW` | Active governance review of drift finding | Boundary record under governance review |
| `RATIFIED` | Canonical governance decision made | Boundary record governance-approved |

**Assessment:**

The overlap is intentional but could cause confusion if a finding and a boundary record both have `UNDER_REVIEW` status — are they the same review?

**Severity:** MINOR — same semantic intent, but potential process confusion

**Recommendation:** Clarify in both documents that:

```
Drift lifecycle states track findings.
Boundary record states track ownership records.
These are parallel vocabularies for different governance objects.
```

No terminology change required if relationship is documented.

---

### Finding 3: Escalation Semantics (OK)

**Verification:**

| Document | Escalation Model |
|----------|------------------|
| Observability Layer | Severity escalation (advisory → warning → blocking → quarantine) |
| Authority Boundary Registry | Ownership dispute escalation (discovery → documentation → review → arbitration → ratification) |
| CI Policy | Automated severity escalation rules |

**Assessment:**

These describe different escalation types:

- Observability: finding severity
- Authority boundary: ownership disputes
- CI policy: automated enforcement

They do not contradict. The observability layer correctly defers to `ontology_ci_policy.json` for enforcement decisions.

**Status:** OK — complementary escalation models

---

### Finding 4: Authority Claims Alignment (OK)

**Verification:**

| Document | Authority Claim |
|----------|-----------------|
| Dimension Ontology | "semantic arbitration groundwork, NOT canonical repository truth" |
| Promotion Manifest | "records review, does not create truth" |
| Observability Layer | "NOT CANONICAL — NOT ENFORCEMENT AUTHORITY" |
| Authority Boundary Registry | "NOT CANONICAL — NOT ENFORCEMENT AUTHORITY" |

**Assessment:**

All documents consistently claim:

```
draft governance work
not canonical authority
not enforcement
```

No document claims authority beyond its stated scope.

**Status:** OK — authority claims aligned

---

### Finding 5: Non-Ownership Clauses (OK)

**Verification:**

| System | Must Not Own | Documented In |
|--------|--------------|---------------|
| Tier 3 Staging | canonical semantics, runtime authorization | Authority Boundary Registry |
| Tier 2 Review | canonical ratification, ontology mutation | Authority Boundary Registry |
| Observability | enforcement authority, semantic ratification | Authority Boundary Registry + Observability Layer |
| Ontology Drafts | automatic enforcement, runtime truth | Authority Boundary Registry |

**Assessment:**

Non-ownership clauses are explicit and consistent. No hidden authority inversion detected.

The key invariant is preserved:

```
consumption does not imply ownership
```

**Status:** OK — non-ownership boundaries clear

---

### Finding 6: Tier Semantics (CRITICAL)

See Finding 1. This is the same issue elevated to its own section due to severity.

**Status:** CRITICAL — requires governance terminology decision

---

### Finding 7: Provenance Language (OK)

**Verification:**

| Document | Provenance Focus |
|----------|------------------|
| Promotion Manifest | Review provenance (who reviewed, when, decision, confidence) |
| Observability Layer | Finding provenance (where detected, related contracts, history) |
| Authority Boundary Registry | Ownership provenance (who claims, conflicts, escalation authority) |

**Assessment:**

Each document defines provenance appropriate to its domain:

- Review provenance for promotion decisions
- Finding provenance for drift observations
- Ownership provenance for authority boundaries

These are complementary, not conflicting.

**Status:** OK — provenance language domain-appropriate

---

### Finding 8: Draft/Ratification Language (OK)

**Verification:**

All ontology governance documents use consistent header format:

```
Status: DRAFT FOR GOVERNANCE RECONCILIATION
Authority: PROPOSED — NOT RATIFIED (or equivalent)
```

| Document | Header Language |
|----------|-----------------|
| Dimension Ontology | "DRAFT FOR GOVERNANCE RECONCILIATION" / "PROPOSED — NOT RATIFIED" |
| Promotion Manifest | "DRAFT FOR GOVERNANCE RECONCILIATION" / "PROPOSED — NOT RATIFIED" |
| Observability Layer | "DRAFT FOR GOVERNANCE RECONCILIATION" / "NOT CANONICAL — NOT ENFORCEMENT AUTHORITY — NOT CI BLOCKING POLICY" |
| Authority Boundary Registry | "DRAFT FOR GOVERNANCE RECONCILIATION" / "NOT CANONICAL — NOT ENFORCEMENT AUTHORITY" |

**Assessment:**

Observability layer adds "NOT CI BLOCKING POLICY" which is specific to its scope — it could be confused with CI policy. This is appropriate differentiation, not inconsistency.

**Status:** OK — draft language consistent with appropriate variation

---

### Finding 9: Anti-Pattern Definitions (OK)

**Verification:**

Anti-patterns across documents:

| Document | Key Prohibitions |
|----------|------------------|
| Dimension Ontology | bbox → physical implicit, averaging conflicting values |
| Promotion Manifest | bbox → physical implicit, dropping sources, silent coercion |
| Observability Layer | silent normalization, runtime-local ontology, staging bypass, CI mutation, implicit escalation, usage-frequency ratification, cross-domain coercion |
| Authority Boundary Registry | implicit expansion, runtime-local ownership, persistence-as-canonical, consumer-as-ratification, convenience-as-authority, observability-as-authority |

**Assessment:**

Anti-patterns are complementary and reinforcing:

- Dimension ontology prohibits measurement conflation
- Promotion manifest prohibits review shortcuts
- Observability layer prohibits visibility-to-authority drift
- Authority boundary registry prohibits ownership assumption

The overlap (e.g., "runtime-local ontology" appears in multiple docs) is intentional reinforcement.

**Status:** OK — anti-patterns consistent and mutually reinforcing

---

### Finding 10: Cross-Reference Gaps (DOCUMENTATION)

**Issue:** Documents created earlier do not reference documents created later.

#### Reference Matrix

| Document | References To | Missing References |
|----------|---------------|-------------------|
| Storage Audit (earliest) | Harvest docs, REPO_DATA_AUDIT | Dimension Ontology, Promotion Manifest, Observability, Authority Boundary |
| Dimension Ontology | Storage Audit, harvest docs | Promotion Manifest, Observability, Authority Boundary |
| Promotion Manifest | Storage Audit, Dimension Ontology, Authority Hierarchy | Observability, Authority Boundary |
| Observability Layer | Most documents | Authority Boundary (created after) |
| Authority Boundary Registry | All preceding documents | N/A (most recent) |

**Assessment:**

This is expected during sequential document creation. The authority boundary registry has the most complete references because it was created last.

**Severity:** DOCUMENTATION — not semantic inconsistency

**Recommendation:** Add back-references to earlier documents:

1. `INSTRUMENT_DATA_STORAGE_AUDIT.md` — add "Related Ontology Documents" section
2. `INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` — reference Promotion Manifest and Observability Layer
3. `PROMOTION_REVIEW_MANIFEST_V1.md` — reference Observability Layer and Authority Boundary
4. `ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md` — reference Authority Boundary Registry

**Action:** Documentation update, no semantic change required

---

## 5. Cross-Document Narrative Inheritance Drift Check

**Purpose:** Verify that wording from one governance layer does not implicitly redefine another layer's scope.

### Check 1: Observability → Enforcement Drift

**Question:** Does observability layer language imply enforcement authority?

**Finding:** No. Document explicitly states:

```
observability severity ≠ automatic enforcement
```

and defers to `ontology_ci_policy.json` for enforcement decisions.

**Status:** No drift detected

### Check 2: Authority Boundary → Ontology Authority Drift

**Question:** Does authority boundary registry language imply ontology ratification authority?

**Finding:** No. Document explicitly states:

```
Documented authority visibility is not the same as semantic authority.
```

**Status:** No drift detected

### Check 3: Promotion Manifest → Canonical Creation Drift

**Question:** Does promotion manifest language imply tier 2 creates canonical truth?

**Finding:** No. Document explicitly states:

```
PromotionReviewManifestV1 records review. It does not create truth.
```

**Status:** No drift detected

### Check 4: Dimension Ontology → Field Authority Drift

**Question:** Does dimension ontology language imply field definitions are canonical?

**Finding:** No. Every field section ends with:

```
UNRESOLVED — requires canonical ratification
```

or equivalent non-authority language.

**Status:** No drift detected

### Check 5: Storage Audit → Migration Authority Drift

**Question:** Does storage audit language imply migration authority?

**Finding:** Document explicitly states:

```
Do NOT Do (Prohibited):
- Delete instrument_specs.py
- Merge all data immediately
- Make harvest outputs canonical
```

**Status:** No drift detected

### Overall Narrative Drift Assessment

```
No cross-document narrative inheritance drift detected.
```

Each document maintains its stated scope boundaries.

---

## 6. Summary of Consistency Status

| Area | Status | Action Required |
|------|--------|-----------------|
| Terminology | FINDING | Governance decision on tier disambiguation |
| Status vocabularies | MINOR | Document parallel vocabulary relationship |
| Escalation semantics | OK | None |
| Authority claims | OK | None |
| Non-ownership clauses | OK | None |
| Tier semantics | CRITICAL | Same as terminology finding |
| Provenance language | OK | None |
| Draft/ratification language | OK | None |
| Anti-pattern definitions | OK | None |
| Cross-references | DOCUMENTATION | Add back-references |
| Narrative drift | OK | None |

---

## 7. Required Actions

### Governance Decision Required

**Issue:** Tier 1/2/3 terminology collision

**Options:**

| Option | Description | Impact |
|--------|-------------|--------|
| A | Rename governance tiers to "Authority Level 1/2/3" | Modify GOVERNANCE_AUTHORITY_HIERARCHY.md |
| B | Rename data promotion tiers to "Data Stage 1/2/3" | Modify 4 ontology documents |
| C | Add disambiguation prefix to all tier references | Modify all documents with tier references |
| D | Document collision as known ambiguity | Add clarification to both tier models |

**Recommendation:** Option D for V1 (document the collision), with Option B for future versions (rename data tiers to "stages").

Rationale: GOVERNANCE_AUTHORITY_HIERARCHY.md is reconciled and referenced by CLAUDE.md. Changing its terminology has wider impact. Data promotion tiers are new (created this sprint) and can adopt "stage" terminology more easily.

### Documentation Updates (No Governance Decision)

Add back-references to earlier documents pointing to later documents in the governance stack.

**Files to update:**

1. `INSTRUMENT_DATA_STORAGE_AUDIT.md`
2. `INSTRUMENT_DIMENSION_ONTOLOGY_V1.md`
3. `PROMOTION_REVIEW_MANIFEST_V1.md`
4. `ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md`

---

## 8. Governance Stack Coherence Assessment

### Stack Structure

```
INSTRUMENT_DATA_STORAGE_AUDIT.md
        │
        ▼ (identifies fragmentation)
INSTRUMENT_DIMENSION_ONTOLOGY_V1.md
        │
        ▼ (documents field semantics)
PROMOTION_REVIEW_MANIFEST_V1.md
        │
        ▼ (governs tier transition)
ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md
        │
        ▼ (provides visibility)
AUTHORITY_BOUNDARY_REGISTRY_V1.md
        │
        ▼ (formalizes ownership)
```

### Coherence Verdict

The governance stack is **internally coherent** with one critical terminology issue (tier collision) and minor documentation gaps.

The key governance invariant is maintained across all documents:

```
visibility ≠ authority
consumption ≠ ownership
draft ≠ canonical
```

### Recommendation

The governance stack is ready for:

1. Terminology decision (tier disambiguation)
2. Back-reference updates
3. Governance review cycle

The governance stack is NOT ready for:

- New ontology domain expansion
- CI enforcement integration
- Runtime coupling
- Migration execution

---

## 9. Document Lifecycle

| Phase | Status | Date |
|-------|--------|------|
| Consistency review | COMPLETE | 2026-05-17 |
| Terminology decision | DOCUMENTED | 2026-05-17 |
| Back-reference updates | COMPLETE | 2026-05-17 |

**Resolution:** Tier terminology collision documented in affected files. Data promotion tiers will be renamed to "stages" in future revision cycle. Back-references added to all governance stack documents.

---

## 10. Related Documents

- `docs/governance/ontology/INSTRUMENT_DIMENSION_ONTOLOGY_V1.md`
- `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md`
- `docs/governance/ontology/ONTOLOGY_GOVERNANCE_OBSERVABILITY_LAYER_V1.md`
- `docs/governance/ontology/AUTHORITY_BOUNDARY_REGISTRY_V1.md`
- `docs/governance/INSTRUMENT_DATA_STORAGE_AUDIT.md`
- `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md`

---

*Governance Stack Consistency Review — 2026-05-17*
