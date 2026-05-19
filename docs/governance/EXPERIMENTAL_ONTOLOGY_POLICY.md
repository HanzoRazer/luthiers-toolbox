# Experimental Ontology Policy

**Status:** DRAFT FOR GOVERNANCE RATIFICATION  
**Authority:** NOT CANONICAL UNTIL RATIFIED — NOT CI BLOCKING POLICY UNTIL WIRED  
**Date:** 2026-05-18  
**Purpose:** Containment rules for experimental systems  
**Constitutional Dependency:** REPOSITORY_CONSTITUTION.md §9

---

## 1. Authority Statement

This document defines how experimental systems are bounded.

```
DRAFT FOR GOVERNANCE RATIFICATION
NOT CANONICAL UNTIL RATIFIED
NOT CI BLOCKING POLICY UNTIL WIRED
```

---

## 2. Experimental Principle

```
Experimental systems may pressure-test ontology.
Experimental systems may not define ontology.
```

### What Experimental Means

Experimental systems are systems that:
- Explore semantic alternatives
- Generate evidence for governance consideration
- Operate in sandbox environments
- Have not been ratified for canonical status

### What Experimental Does Not Mean

| Not Experimental | Reason |
|------------------|--------|
| Unfinished | Completion status is not experimental status |
| Untested | Testing status is not experimental status |
| New | Age is not experimental status |
| Undocumented | Documentation status is not experimental status |

---

## 3. Experimental Containment Boundaries

### Experimental Systems May

| Permitted | Description |
|-----------|-------------|
| Pressure-test ontology | Explore whether current vocabulary is sufficient |
| Propose vocabulary | Through reconciliation workflow |
| Operate in sandbox | Within designated containment boundaries |
| Generate evidence | For governance consideration |
| Fail safely | Failures do not affect canonical systems |

### Experimental Systems May NOT

| Forbidden | Reason |
|-----------|--------|
| Define canonical ontology | Constitutional Invariant 3: Evidence is not ontology |
| Leak into canonical systems | Containment boundary violation |
| Self-promote to canonical | Ratification required (Constitutional Invariant 4) |
| Bypass review | Review is required for all semantic decisions |
| Claim authority through usage | Constitutional Invariant 8: Usage is not ratification |

---

## 4. Containment Mechanisms

### Namespace Isolation

Experimental systems must use isolated namespaces:

| Mechanism | Description |
|-----------|-------------|
| Prefix convention | `experimental_`, `sandbox_`, `staging_` |
| Directory isolation | Separate directory tree from canonical |
| Schema separation | Experimental schemas not mixed with canonical |
| Database isolation | Experimental data in separate tables/collections |

### Interface Boundaries

Experimental systems may not:

| Forbidden Interface | Reason |
|---------------------|--------|
| Export to canonical consumers | Containment leak |
| Accept canonical imports as authority | Backwards contamination |
| Register in canonical registries | Registry pollution |
| Appear in canonical documentation | Documentation confusion |

### Failure Isolation

Experimental system failures must not:

| Forbidden Impact | Reason |
|------------------|--------|
| Block canonical operations | Production stability |
| Corrupt canonical data | Data integrity |
| Trigger canonical alerts | Alert fatigue |
| Appear as canonical errors | Error confusion |

---

## 5. Experimental Lifecycle

### Stage 1: Sandbox Creation

| Field | Description |
|-------|-------------|
| Sandbox Name | Unique identifier |
| Sandbox Purpose | What is being explored |
| Sandbox Boundary | Where sandbox ends |
| Sandbox Owner | Who is responsible |
| Sandbox Duration | Expected lifetime (may be indefinite) |

### Stage 2: Experimental Operation

| Permitted Activity | Description |
|--------------------|-------------|
| Generate evidence | Create data for governance review |
| Test hypotheses | Validate semantic alternatives |
| Document findings | Record what was learned |
| Propose vocabulary | Submit to reconciliation workflow |

### Stage 3: Governance Review

Experimental findings are reviewed through:
- `ONTOLOGY_RECONCILIATION_WORKFLOW.md` for vocabulary proposals
- `GOVERNANCE_RATIFICATION_MODEL.md` for promotion requests

### Stage 4: Outcome

| Outcome | Description |
|---------|-------------|
| Promotion | Experimental system ratified for canonical status |
| Continuation | Experimental system continues exploration |
| Termination | Experimental system decommissioned |
| Absorption | Experimental system absorbed into existing canonical |

---

## 6. Promotion Process

### Promotion Requirements

| Requirement | Description |
|-------------|-------------|
| Evidence documented | What was learned in sandbox |
| Vocabulary proposed | Terms to add to canonical vocabulary |
| Authority requested | What ownership is sought |
| Constitutional compliance | No invariant violations |
| Ratification approval | Explicit human acceptance |

### Promotion Constraints

```
Promotion requires ratification.
Promotion is not automatic.
Promotion is not implied by successful operation.
Promotion is not implied by widespread sandbox adoption.
```

---

## 7. High-Risk Experimental Systems

The following categories require additional containment:

| Category | Risk | Additional Containment |
|----------|------|------------------------|
| Evidence extraction | May be mistaken for ontology | Explicit `evidence_only` flag |
| Geometry processing | May leak into CAM pipeline | Output validation gate |
| Vocabulary exploration | May create shadow vocabulary | Namespace audit |
| Authority testing | May imply authority grants | Authority boundary check |

### Sandbox Example: IBG (Instrument Body Geometry)

The IBG morphology system is a sandbox example demonstrating experimental containment:

| Aspect | IBG Status |
|--------|------------|
| Namespace | `instrument_geometry/body/ibg/` — isolated directory |
| Evidence generation | Morphology extraction produces evidence, not ontology |
| Vocabulary | Proposes terms like `morphology_category`, not yet canonical |
| Authority | No authority over canonical body definitions |
| Promotion path | Through `EXPERIMENTAL_PROMOTION` ratification |

IBG extraction failures (documented in `MORPHOLOGY_FAILURE_TAXONOMY.md`) demonstrate why evidence systems cannot be ontology authorities — extraction instability means evidence quality varies, which is acceptable for evidence but unacceptable for ontology.

---

## 8. Experimental Registry

### Registry Format

```yaml
sandbox_id: EXP-2026-0001
sandbox_name: ibg_morphology_harvest
sandbox_purpose: Extract body morphology evidence from blueprints
sandbox_boundary: services/api/app/instrument_geometry/body/ibg/
sandbox_owner: IBG Sprint Team
sandbox_created: 2026-05-17
sandbox_duration: Indefinite
sandbox_status: ACTIVE
promotion_status: NOT_REQUESTED
evidence_flag: true
authority_claim: NONE
vocabulary_proposals:
  - morphology_category
  - body_grid_cell
  - contour_zone
```

### Registry Location

Experimental registrations are stored in `docs/governance/experimental/` directory.

---

## 9. Containment Violations

### Violation Types

| Violation | Description |
|-----------|-------------|
| Namespace leak | Experimental code outside sandbox boundary |
| Data leak | Experimental data in canonical storage |
| Registry leak | Experimental system in canonical registry |
| Authority leak | Experimental system claiming canonical authority |
| Vocabulary leak | Experimental terms used as canonical |

### Violation Response

| Response | Description |
|----------|-------------|
| Identify leak | Locate violation source |
| Contain leak | Prevent further spread |
| Remediate | Remove leaked content from canonical |
| Document | Record violation for governance review |
| Prevent | Add containment check to prevent recurrence |

---

## 10. Open Experimental Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should experimental systems have time-limited containment? | Forces promotion or termination |
| 2 | Should experimental systems have resource limits? | Prevents unbounded growth |
| 3 | Should experimental violations block CI? | Enforcement strength |
| 4 | Should multiple sandboxes be permitted for same domain? | Exploration breadth vs. confusion |
| 5 | Should experimental systems require periodic review? | Prevents zombie sandboxes |

---

## Related Documents

- `REPOSITORY_CONSTITUTION.md` — Constitutional authority
- `GOVERNANCE_RATIFICATION_MODEL.md` — Promotion ratification
- `SEMANTIC_FREEZE_POLICY.md` — Freeze discipline
- `ONTOLOGY_RECONCILIATION_WORKFLOW.md` — Vocabulary proposal workflow
- `MORPHOLOGY_FAILURE_TAXONOMY.md` — Evidence extraction instability example

---

*Experimental Ontology Policy — DRAFT FOR GOVERNANCE RATIFICATION*
