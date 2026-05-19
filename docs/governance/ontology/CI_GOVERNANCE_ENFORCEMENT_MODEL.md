# CI Governance Enforcement Model

**Status:** Authoritative  
**Date:** 2026-05-16  
**Sprint:** MRP-5K

---

## Purpose

This document defines the enforcement model for ontology governance checks in the repository CI pipeline. It establishes severity classifications, enforcement tiers, and progressive escalation phases.

---

## Core Principle

```
Governance enforcement exists to expose reality,
not manufacture artificial compliance.
```

Visible truthful governance is preferred over fake cleanliness.

---

## Severity Classifications

| Severity | Exit Code | CI Behavior | Purpose |
|----------|-----------|-------------|---------|
| informational | 0 | No action | Reporting only |
| advisory | 0 | Log finding | Visible governance concern |
| warning | 0 | Log prominently | Likely future violation |
| blocking | 1 | Fail CI | Ontology integrity failure |
| quarantine | 2 | Reserved | Forbidden semantic state |

### Informational

Pure reporting. No governance concern. Used for statistics and trends.

### Advisory

Visible governance concern that does not require immediate action. Includes:
- Historical semantic duplication
- Legacy drift patterns
- Future reconciliation opportunities

### Warning

Likely future violation that should be addressed but does not block. Includes:
- Deprecated lifecycle aliases in use
- Undocumented runtime classifications
- Inconsistent experimental terminology
- Mixed semantic_only/prototype usage

### Blocking

Ontology integrity failure that must be addressed before merge. Includes:
- Downstream authority redefining upstream authority
- Translator claiming geometry authority
- Runtime mutating canonical semantic ownership
- Duplicate canonical owner assignment
- Invalid authority chain cycles

### Quarantine (Reserved)

Forbidden semantic state requiring isolation before merge. Reserved for future activation. Includes:
- Experimental subsystem redefining canonical ontology
- Runtime claiming ontology ownership
- Adaptive system mutating authoritative semantics

---

## Enforcement Tiers

Ontology checks integrate with the existing governance tier system:

| Tier | Runtime | Ontology Checks |
|------|---------|-----------------|
| precommit | <2s | Not included (too slow) |
| ci | <30s | Authority chain audit |
| nightly | >30s | Full drift detection, lifecycle validation |

### CI Tier Checks

- `audit_authority_chains.py` — blocking for authority violations
- `validate_lifecycle_terms.py` — warning only

### Nightly Tier Checks

- `detect_semantic_drift.py` — advisory only
- Full baseline comparison

---

## Progressive Enforcement Phases

### Phase 1 — Advisory Only (Current)

All ontology findings reported as advisory. No CI blocking except clear authority violations.

### Phase 2 — Warnings

Lifecycle vocabulary issues become warnings. Still no blocking except authority violations.

### Phase 3 — Selected Blocking

Critical lifecycle violations become blocking:
- Use of quarantined terms
- Direct canonical term redefinition
- Forbidden alias usage

### Phase 4 — Full Enforcement

All ontology violations enforced at appropriate severity. Requires:
- Complete baseline cleanup
- All legacy drift addressed
- Full vocabulary normalization

**MRP-5K implements Phase 1–2 only.**

---

## Enforcement Policy Registry

Machine-readable enforcement policy: `ontology_ci_policy.json`

Structure:
```json
{
  "checks": {
    "audit_authority_chains": {
      "severity": "blocking",
      "tier": "ci"
    }
  }
}
```

---

## Exit Code Semantics

| Check Result | Exit Code | CI Effect |
|--------------|-----------|-----------|
| All pass | 0 | Success |
| Advisory only | 0 | Success with findings |
| Warnings only | 0 | Success with warnings |
| Any blocking | 1 | Failure |
| Any quarantine | 2 | Reserved (not activated) |

---

## Escalation Criteria

### Advisory → Warning

Term or pattern appears in:
- New code (not legacy)
- Multiple locations
- Cross-domain usage

### Warning → Blocking

Violation represents:
- Authority inversion
- Semantic corruption
- Ownership conflict
- Canonical mutation

### Blocking → Quarantine

Violation requires:
- Immediate isolation
- Cross-team review
- Governance committee decision

---

## Baseline Management

Current accepted drift is captured in:
- `ONTOLOGY_DRIFT_BASELINE_2026_05.md` — human record
- `ontology_drift_baseline_2026_05.json` — machine comparison

Baseline violations are:
- **Not blocking** — legacy drift is accepted
- **Visible** — reported as advisory
- **Tracked** — counted for trend analysis

New violations (not in baseline) may escalate to warning or blocking based on severity.

---

## Reporting Output

### Standard Output

```
ONTOLOGY GOVERNANCE REPORT
──────────────────────────
Authority Violations: 0
Lifecycle Warnings: 26
Semantic Drift Findings: 91
Blocking Failures: 0
Advisory Findings: 91
```

### JSON Output

```json
{
  "authority_violations": 0,
  "lifecycle_warnings": 26,
  "drift_findings": 91,
  "blocking": 0,
  "advisory": 91,
  "exit_code": 0
}
```

---

## Integration Points

### check_all.py

Ontology checks register in GOVERNANCE_CHECKS:
```python
("scripts/governance/audit_authority_chains.py", "Authority chain audit", True, EnforcementTier.CI),
("scripts/governance/validate_lifecycle_terms.py", "Lifecycle vocabulary", False, EnforcementTier.CI),
("scripts/governance/detect_semantic_drift.py", "Semantic drift detection", False, EnforcementTier.NIGHTLY),
```

### Pre-commit (Future)

Fast ontology checks may be added to pre-commit tier when execution time permits.

---

## Related Documents

- `ontology_ci_policy.json` — machine-readable policy
- `ONTOLOGY_DRIFT_BASELINE_2026_05.md` — current baseline
- `GOVERNANCE_CLASSIFICATION_MODEL.md` — classification model
- `LIFECYCLE_VOCABULARY_STANDARD.md` — lifecycle vocabulary
