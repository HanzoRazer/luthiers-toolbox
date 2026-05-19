# Ontology Governance Observability Layer V1

**Status:** DRAFT FOR GOVERNANCE RECONCILIATION  
**Date:** 2026-05-15  
**Authority:** NOT CANONICAL — NOT ENFORCEMENT AUTHORITY — NOT CI BLOCKING POLICY  
**Scope:** Governance-state visibility only  
**Track:** Instrument Knowledge Reconciliation (Sandbox)

---

## 1. Authority Statement

This document defines governance observability semantics.

```
It does NOT redefine CI enforcement policy.
It does NOT create semantic authority.
It does NOT authorize canonical promotion.
It does NOT implement executable automation.
```

**Document classification:**

| Property | Value |
|----------|-------|
| Status | DRAFT FOR GOVERNANCE RECONCILIATION |
| Authority | PROPOSED — NOT RATIFIED |
| CI Policy | NOT CI BLOCKING POLICY |
| Enforcement | NOT ENFORCEMENT AUTHORITY |

The observability layer exists to make governance state visible and auditable. It does not create, modify, or arbitrate semantic truth.

---

## 2. Purpose and Scope

### Purpose

This document defines:

```
governance-state visibility
```

NOT:

```
governance-state execution
```

### What Observability Provides

| Capability | Description |
|------------|-------------|
| Inspection | View current ontology governance state |
| Auditability | Trace governance decisions over time |
| Attribution | Identify who made governance decisions |
| Correlation | Link related ontology findings |
| Escalation visibility | See when findings require governance attention |

### What Observability Does NOT Provide

| Non-Capability | Reason |
|----------------|--------|
| Semantic ratification | Requires governance committee |
| Automatic normalization | Would create runtime-local ontology |
| CI blocking decisions | Defined by `ontology_ci_policy.json` |
| Canonical promotion | Requires `PROMOTION_REVIEW_MANIFEST_V1` workflow |
| Conflict resolution | Requires human arbitration |

### Observability Supports

- Ontology review
- Semantic arbitration
- Migration planning
- Authority preservation
- Governance escalation

---

## 3. Drift Lifecycle States

Every ontology drift finding progresses through a governed lifecycle.

### State Definitions

| State | Meaning | Entry Condition | Exit Condition |
|-------|---------|-----------------|----------------|
| `DISCOVERED` | Finding newly detected | Initial detection | Baselined or reviewed |
| `BASELINED` | Accepted legacy drift | Added to baseline file | Cleanup or re-evaluation |
| `ACCEPTED_LEGACY` | Permanent accepted debt | Governance acceptance | Explicit removal |
| `UNDER_REVIEW` | Active governance review | Review initiated | Decision made |
| `NORMALIZATION_PROPOSED` | Fix proposed | Proposal submitted | Accepted or rejected |
| `RATIONALE_REQUIRED` | Missing justification | Governance request | Rationale provided |
| `READY_FOR_RATIFICATION` | Pending final approval | All criteria met | Ratified or returned |
| `RATIFIED` | Canonical governance decision | Governance committee approval | Superseded |
| `DEPRECATED` | Scheduled for removal | Deprecation decision | Removed |
| `QUARANTINED` | Isolated for review | Critical issue detected | Resolved or escalated |

### Allowed State Transitions

```
DISCOVERED
    → BASELINED (added to baseline)
    → UNDER_REVIEW (review initiated)
    → QUARANTINED (critical issue)

BASELINED
    → UNDER_REVIEW (cleanup initiated)
    → ACCEPTED_LEGACY (permanent acceptance)
    → DEPRECATED (scheduled removal)

ACCEPTED_LEGACY
    → UNDER_REVIEW (re-evaluation)
    → DEPRECATED (cleanup decision)

UNDER_REVIEW
    → NORMALIZATION_PROPOSED (fix proposed)
    → RATIONALE_REQUIRED (needs justification)
    → BASELINED (accepted as-is)
    → QUARANTINED (critical issue found)

NORMALIZATION_PROPOSED
    → READY_FOR_RATIFICATION (proposal approved)
    → UNDER_REVIEW (proposal rejected)
    → RATIONALE_REQUIRED (needs more justification)

RATIONALE_REQUIRED
    → UNDER_REVIEW (rationale provided)
    → QUARANTINED (cannot justify)

READY_FOR_RATIFICATION
    → RATIFIED (approved)
    → UNDER_REVIEW (returned for revision)

RATIFIED
    → DEPRECATED (superseded)

DEPRECATED
    → (removed from tracking)

QUARANTINED
    → UNDER_REVIEW (review resolved)
    → (escalated to governance committee)
```

### Forbidden State Transitions

| From | To | Reason |
|------|----|--------|
| DISCOVERED | RATIFIED | Cannot skip review |
| BASELINED | RATIFIED | Baseline is not ratification |
| QUARANTINED | RATIFIED | Must exit quarantine through review |
| Any | Any (silent) | All transitions require provenance |

---

## 4. Semantic Ownership Escalation Model

When semantic ambiguity is discovered, it follows an escalation path toward resolution.

### Escalation Flow

```
runtime ambiguity
    ↓
ontology conflict detected
    ↓
governance review initiated
    ↓
ontology draft created
    ↓
arbitration conducted
    ↓
ratification decision
    ↓
migration planning
```

### Escalation Stages

| Stage | Owner | Output |
|-------|-------|--------|
| Runtime ambiguity | Runtime consumer | Ambiguity report |
| Conflict detection | Observability layer | Conflict finding |
| Governance review | Governance team | Review decision |
| Ontology draft | Ontology author | Draft document |
| Arbitration | Governance committee | Resolution proposal |
| Ratification | Governance authority | Canonical decision |
| Migration planning | Implementation team | Migration plan |

### Explicitly Prohibited

```
runtime-local semantic ratification
```

No runtime system may:
- Define canonical meaning
- Resolve semantic conflicts silently
- Promote staging to canonical
- Create domain-local ontology
- Bypass governance review

---

## 5. Governance Signal Categories

### Category Definitions

| Category | Meaning | Severity Guidance | Escalation Condition |
|----------|---------|-------------------|---------------------|
| `AUTHORITY_CONFLICT` | Multiple systems claim ownership | Warning → Blocking | Cross-domain expansion |
| `ONTOLOGY_DRIFT` | Semantic meaning diverging | Advisory | New drift in non-legacy code |
| `TERM_COLLISION` | Same term, different meanings | Warning | Used across domains |
| `DOMAIN_BOUNDARY_AMBIGUITY` | Unclear which domain owns concept | Advisory | Affects runtime behavior |
| `PROVENANCE_GAP` | Missing origin/lineage | Warning | Canonical data affected |
| `NORMALIZATION_RISK` | Transformation may lose meaning | Warning | Irreversible transformation |
| `RUNTIME_AUTHORITY_EXPANSION` | Runtime claiming semantic authority | Blocking | Any occurrence |
| `UNREGISTERED_LIFECYCLE_TERM` | Term not in canonical registry | Warning | Used in governance context |
| `STAGING_PROMOTION_RISK` | Staging data treated as canonical | Blocking | Runtime consumption detected |

### Example Cases

#### AUTHORITY_CONFLICT

```
Finding: "morphology" ownership unclear
Semantic Registry: Geometry Layer / MRP
Authority Registry: Geometry Layer
Severity: Advisory (naming inconsistency, not true conflict)
```

#### ONTOLOGY_DRIFT

```
Finding: body_length_mm semantic disagreement
Source A: instrument_specs.py → 406mm (physical)
Source B: outlines.py → 458.8mm (bbox)
Severity: Advisory (documented in ontology baseline)
```

#### TERM_COLLISION

```
Finding: "width_mm" ambiguous
Meaning A: lower_bout_width_mm
Meaning B: body_outline_bbox_width_mm
Severity: Warning (affects multiple consumers)
```

#### RUNTIME_AUTHORITY_EXPANSION

```
Finding: Runtime normalizing bbox → physical implicitly
Location: vectorizer attempting silent conversion
Severity: Blocking (forbidden normalization)
```

#### STAGING_PROMOTION_RISK

```
Finding: CAD generator reading morphology_harvest/outputs/
Risk: Staging evidence treated as canonical
Severity: Blocking (Tier 3 → production bypass)
```

---

## 6. Severity Interpretation Model

This document interprets governance observability semantics. **It does not redefine CI enforcement policy.**

### Canonical Severity Definitions

Per `ontology_ci_policy.json`:

| Severity | Exit Code | CI Behavior | Description |
|----------|-----------|-------------|-------------|
| `informational` | 0 | no_action | Reporting only |
| `advisory` | 0 | log_finding | Visible governance concern |
| `warning` | 0 | log_prominently | Likely future violation |
| `blocking` | 1 | fail_ci | Ontology integrity failure |
| `quarantine` | 2 | reserved | Forbidden semantic state (not activated) |

### Current Enforcement Phase

Per `ontology_ci_policy.json`:

```
enforcement_phase: 2
"Advisory and warnings active, blocking for authority violations only"
```

### Escalation Rules (from CI Policy)

**Advisory → Warning:**
- Term appears in new code (not legacy)
- Term appears in multiple locations
- Term used across domains

**Warning → Blocking:**
- Authority inversion detected
- Semantic corruption detected
- Ownership conflict detected
- Canonical mutation attempted

**Blocking → Quarantine:**
- Requires immediate isolation
- Requires cross-team review
- Requires governance committee decision

### Observability Severity vs. Enforcement Severity

```
observability severity ≠ automatic enforcement
```

Observability may identify findings at any severity level. CI enforcement behavior is determined solely by `ontology_ci_policy.json`.

---

## 7. Drift Baseline Lifecycle

### Drift Categories

| Category | Description | Baseline Behavior |
|----------|-------------|-------------------|
| Legacy drift | Present before baseline date | Advisory (accepted) |
| New drift | Introduced after baseline | Escalate per severity |
| Resolved drift | Fixed after baseline | Remove from baseline |
| Deprecated drift | Scheduled for removal | Track until removed |
| Superseded drift | Replaced by new decision | Archive reference |

### Current Baseline Summary

Per `ontology_drift_baseline_2026_05.json`:

| Category | Count | Status |
|----------|-------|--------|
| Duplicate enum values | 151 | Accepted |
| Cross-domain terms | 7 | Accepted with disambiguation |
| Missing registrations | 1 | Pending fix |
| Authority naming inconsistencies | 2 | Accepted pending normalization |
| Potential lifecycle issues | 26 | Mostly false positives |

### Baseline Rules

Per `ontology_drift_baseline_2026_05.json`:

```json
{
  "violations_in_baseline": "advisory",
  "new_violations": "escalate_per_severity",
  "update_frequency": "quarterly_or_after_major_cleanup"
}
```

### Baseline Entry Removal Conditions

| Condition | Action |
|-----------|--------|
| Finding resolved | Remove from baseline |
| Finding superseded | Archive reference, remove active entry |
| Finding escalated | Change severity, retain entry |
| Finding promoted to canonical | Remove from baseline, document in ratification |

### Normalization Impact on Baseline

When semantic normalization is proposed:

1. Finding transitions to `NORMALIZATION_PROPOSED`
2. Baseline entry retained until ratification
3. After ratification, baseline entry archived
4. New canonical definition takes precedence

---

## 8. Governance Provenance Requirements

Every observability finding MUST include provenance metadata.

### Required Provenance Fields

| Field | Required | Description |
|-------|----------|-------------|
| `finding_id` | YES | Unique identifier |
| `finding_type` | YES | Category from Section 5 |
| `source_location` | YES | File/line where finding detected |
| `source_term` | YES | The term or field in question |
| `ontology_reference` | CONDITIONAL | Link to ontology document if exists |
| `related_contracts` | CONDITIONAL | Affected contracts |
| `related_runtime` | CONDITIONAL | Affected runtime systems |
| `review_status` | YES | Current lifecycle state |
| `review_history` | YES | State transition log |
| `escalation_history` | CONDITIONAL | Escalation events if any |
| `provenance_timestamp` | YES | When finding was recorded |

### Provenance Preservation Rule

```
preservation of unresolved ambiguity
```

Findings with unresolved semantic conflicts MUST retain:
- All conflicting values
- All source locations
- All proposed interpretations
- Reasoning for non-resolution

Forbidden:
- Silently choosing one interpretation
- Dropping conflicting sources
- Averaging conflicting values
- Marking unresolved as resolved

---

## 9. Quarantine Philosophy

### Conceptual Meaning

```
QUARANTINED = reserved governance isolation state
```

Quarantine is NOT:
- Automatic CI behavior (exit code 2 is reserved, not activated)
- Permanent deletion
- Automatic rollback
- Runtime enforcement

Quarantine IS:
- Governance-initiated isolation
- Explicit review requirement
- Temporary holding state
- Cross-team coordination trigger

### Candidate Quarantine Targets

The following repository entities MAY be candidates for quarantine (conceptual, not operational):

| Target Type | Example | Quarantine Reason |
|-------------|---------|-------------------|
| Ontology drafts | Conflicting field definition | Requires arbitration |
| Semantic registries | Authority collision | Requires ownership decision |
| Migration branches | Breaking semantic change | Requires review |
| Staging datasets | Promoted without review | Tier violation |
| Generated evidence | Low confidence extraction | Quality concern |
| Conflicting contracts | Incompatible versions | Integration risk |
| Runtime plugins | Authority inversion detected | Governance violation |
| Unresolved adapters | Semantic translation unclear | Migration risk |

### Quarantine vs. Blocking

| Property | Blocking | Quarantine |
|----------|----------|------------|
| CI behavior | Fail immediately | Reserved (not implemented) |
| Scope | Single finding | Entire entity |
| Duration | Until fixed | Until governance decision |
| Resolution | Developer fix | Governance committee |
| Automation | Automatic | Manual only |

### Who May Trigger Quarantine

Quarantine authority is NOT yet defined. Candidates:
- Governance committee
- Domain owners (for their domain)
- Repository maintainers

### Quarantine vs. Migration Freeze

Quarantine does NOT automatically imply migration freeze. However:
- Quarantined ontology drafts SHOULD NOT be used for migration planning
- Quarantined contracts SHOULD NOT be implemented
- Quarantined staging SHOULD NOT be promoted

---

## 10. Relationship to Existing Governance Documents

### Positioned As

```
governance coordination infrastructure
```

NOT:

```
semantic authority
```

### Document Relationships

| Document | Relationship | This Layer's Role |
|----------|--------------|-------------------|
| `INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` | Ontology definition | Observes field semantics |
| `PROMOTION_REVIEW_MANIFEST_V1.md` | Promotion governance | Observes review decisions |
| `ONTOLOGY_DRIFT_BASELINE_2026_05.md` | Accepted drift record | Sources baseline state |
| `ontology_drift_baseline_2026_05.json` | Machine-readable baseline | Queries baseline entries |
| `ontology_ci_policy.json` | CI enforcement policy | Defers to for severity |
| `GOVERNANCE_AUTHORITY_HIERARCHY.md` | Tier authority model | Observes tier boundaries |

### Authority Hierarchy

```
ontology_ci_policy.json          ← Defines enforcement
    ↑
ontology_drift_baseline.json     ← Defines accepted state
    ↑
ONTOLOGY_DRIFT_BASELINE.md       ← Documents baseline
    ↑
THIS DOCUMENT                    ← Defines observability
    ↑
Future: Observability tooling    ← Implements visibility
```

This layer observes state defined by higher-authority documents. It does not define that state.

---

## 11. Example Governance Findings

### Example A: Physical vs. Bounding Box Ambiguity

```
Finding ID: DRIFT-2026-05-001
Category: ONTOLOGY_DRIFT
Lifecycle State: BASELINED

Source Term: body_length_mm
Source Locations:
  - instrument_specs.py:63 → 406mm (Stratocaster)
  - body_outlines.py:34 → 458.8mm (Stratocaster)

Conflict Description:
  instrument_specs.py interprets body_length_mm as physical measurement
  body_outlines.py interprets height_mm as bounding box extent
  52.8mm variance is not measurement error — different conventions

Ontology Reference: INSTRUMENT_DIMENSION_ONTOLOGY_V1.md, Field 1

Severity: Advisory (documented in baseline)
Escalation: None (accepted legacy drift)
Resolution Status: UNRESOLVED — requires ontology ratification
```

### Example B: Width Field Semantic Ambiguity

```
Finding ID: DRIFT-2026-05-002
Category: TERM_COLLISION
Lifecycle State: UNDER_REVIEW

Source Term: width_mm
Source Locations:
  - body_templates.json:15 → 318mm (Stratocaster)
  - body_outlines.py:34 → 322.3mm (Stratocaster)

Conflict Description:
  "width_mm" could mean lower_bout_width_mm OR bbox_width_mm
  Field name does not disambiguate measurement convention

Ontology Reference: INSTRUMENT_DIMENSION_ONTOLOGY_V1.md, Fields 2 & 5

Severity: Warning (affects multiple consumers)
Escalation Condition: If used in new CAM code
Resolution Status: NORMALIZATION_PROPOSED — separate fields for bbox vs physical
```

### Example C: Runtime Implicit Normalization (Hypothetical)

```
Finding ID: RUNTIME-2026-05-001
Category: RUNTIME_AUTHORITY_EXPANSION
Lifecycle State: QUARANTINED

Source Location: vectorizer_phase3.py:hypothetical

Violation Description:
  Runtime attempting to normalize bbox measurements to physical
  without ontology reference or provenance

Forbidden Action: bbox → physical (implicit)
Reference: INSTRUMENT_DIMENSION_ONTOLOGY_V1.md, Allowed Derivations

Severity: Blocking (authority inversion)
Escalation: Immediate governance review required
Resolution Status: QUARANTINED — requires governance decision
```

### Example D: Staging Promotion Without Review (Hypothetical)

```
Finding ID: STAGING-2026-05-001
Category: STAGING_PROMOTION_RISK
Lifecycle State: DISCOVERED

Source Location: hypothetical_generator.py

Violation Description:
  Generator reading from morphology_harvest/outputs/ directly
  Tier 3 evidence consumed without Tier 2 review

Forbidden Action: Staging → Runtime bypass
Reference: PROMOTION_REVIEW_MANIFEST_V1.md, Tier Model

Severity: Blocking (tier boundary violation)
Escalation: Requires code review and refactoring
Resolution Status: DISCOVERED — pending review
```

---

## 12. Forbidden Governance Anti-Patterns

The following patterns are explicitly prohibited:

### Anti-Pattern 1: Silent Semantic Normalization

```
FORBIDDEN: Converting bbox → physical without provenance
REASON: Loses measurement convention, creates semantic corruption
```

### Anti-Pattern 2: Runtime-Local Ontology Creation

```
FORBIDDEN: Runtime defining canonical field meanings
REASON: Ontology authority belongs to governance, not runtime
```

### Anti-Pattern 3: Staging → Canonical Promotion Without Review

```
FORBIDDEN: Consuming Tier 3 evidence in production
REASON: Bypasses PROMOTION_REVIEW_MANIFEST_V1 workflow
```

### Anti-Pattern 4: Ontology Mutation Through CI Tooling

```
FORBIDDEN: CI scripts modifying semantic definitions
REASON: CI observes and reports, does not define
```

### Anti-Pattern 5: Implicit Authority Escalation

```
FORBIDDEN: Observability findings becoming enforcement
REASON: Observability ≠ Authority
```

### Anti-Pattern 6: Auto-Ratification Through Usage Frequency

```
FORBIDDEN: "This term is used everywhere, so it's canonical"
REASON: Usage frequency ≠ Governance ratification
```

### Anti-Pattern 7: Cross-Domain Semantic Coercion

```
FORBIDDEN: Domain A redefining Domain B's vocabulary
REASON: Domain boundaries must be preserved
```

---

## 13. Open Governance Questions

The following questions require governance decision:

| # | Question | Impact | Proposed Owner |
|---|----------|--------|----------------|
| 1 | Should accepted drift expire automatically? | Baseline lifecycle | Governance committee |
| 2 | Who owns quarantine authority? | Quarantine workflow | Governance committee |
| 3 | Can drift baselines be versioned independently? | Baseline management | Observability maintainers |
| 4 | When should advisory findings escalate to warning? | Escalation policy | CI policy owner |
| 5 | Should ontology observability integrate with RMOS governance? | Cross-domain | RMOS + Ontology owners |
| 6 | How are cross-domain ontology disputes arbitrated? | Conflict resolution | Governance committee |
| 7 | What is the maximum time a finding can remain UNDER_REVIEW? | Review SLAs | Governance committee |
| 8 | Should observability findings be visible in developer tooling? | Developer experience | Tooling team |
| 9 | How do observability findings propagate to downstream repos? | Multi-repo governance | Architecture team |
| 10 | Can runtime systems query observability state? | Runtime integration | Runtime + Observability owners |

---

## 14. Document Lifecycle

| Phase | Status | Date |
|-------|--------|------|
| Initial draft | COMPLETE | 2026-05-15 |
| Governance review | PENDING | — |
| Ratification | PENDING | — |
| Executable implementation | BLOCKED | — |

---

## 15. Related Documents

### Governance Stack Documents

- `docs/governance/ontology/INSTRUMENT_DIMENSION_ONTOLOGY_V1.md` — Field semantic definitions
- `docs/governance/ontology/PROMOTION_REVIEW_MANIFEST_V1.md` — Tier 3→2 review governance
- `docs/governance/ontology/AUTHORITY_BOUNDARY_REGISTRY_V1.md` — Ownership boundaries
- `docs/governance/ontology/GOVERNANCE_STACK_CONSISTENCY_REVIEW_2026_05.md` — Stack consistency verification

### Baseline Documents

- `docs/governance/ontology/ONTOLOGY_DRIFT_BASELINE_2026_05.md`
- `docs/governance/ontology/ontology_drift_baseline_2026_05.json`

### Policy Documents

- `docs/governance/ontology/ontology_ci_policy.json`
- `docs/governance/GOVERNANCE_AUTHORITY_HIERARCHY.md`

### Audit Documents

- `docs/governance/INSTRUMENT_DATA_STORAGE_AUDIT.md`
- `docs/governance/MORPHOLOGY_HARVEST_STORAGE_AUTHORITY.md`

---

## 16. Terminology Note

**Data Promotion Tiers vs. Governance Authority Tiers**

This document references "Tier 1/2/3" for data promotion stages (Canonical/Curated/Staging). This is distinct from `GOVERNANCE_AUTHORITY_HIERARCHY.md` which uses "Tier 1/2/3" for governance authority strata (Structural Invariants/Domain Governance/Operational Policies). These are separate semantic systems.

---

## Final Rule

```
Observability records governance state.
It does not create semantic authority.
```

```
visibility ≠ authority
```

---

*Ontology Governance Observability Layer V1 — DRAFT FOR GOVERNANCE RECONCILIATION*
