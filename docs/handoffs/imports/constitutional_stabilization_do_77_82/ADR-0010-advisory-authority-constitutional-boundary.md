# ADR-0010: Advisory Authority Constitutional Boundary

**Status:** Accepted  
**Date:** 2026-05-23  
**Supersedes:** None  
**Extends:** ADR-0009 (Advisory Boundary — Measurement vs Decision Support)  
**Enforcement:** Constitutional doctrine; runtime enforcement unchanged

---

## Context

ADR-0009 established the runtime separation between MEASUREMENT and DECISION SUPPORT instrument classes. This separation is CI-enforced and has proven effective at preventing advisory logic from contaminating measurement artifacts.

However, runtime separation alone does not address:

1. **Authority semantics** — what kinds of claims are constitutionally legitimate within DECISION SUPPORT systems?
2. **Operator sovereignty** — how do we prevent advisory systems from acquiring implicit authority over human judgment?
3. **Semantic leakage** — how do we prevent advisory language from creating accidental canonization?

This ADR establishes the constitutional framework for advisory authority that governs all DECISION SUPPORT systems, including but not limited to:

- `AnalyzerGuidanceEngine` (AGE)
- `WolfAdvisor`
- Future ML-based advisory systems
- Optimization assistants
- Review and flagging systems

---

## Decision

### 1. Orthogonal Authority Domains

Advisory authority is NOT hierarchical. The following domains are constitutionally orthogonal:

| Domain | Constitutional Definition | Example Systems |
|--------|---------------------------|-----------------|
| **Measurement** | Authority over captured observational records | Waveform capture, FFT pipelines, calibration traces |
| **Advisory** | Authority to prioritize operator attention | AGE directives, wolf-tone flags, drift alerts |
| **Interpretive** | Authority to frame semantic context | Narrative generators, pattern labelers |
| **Operator** | Final human judgment authority | UI decisions, workflow choices, acceptance/rejection |

No domain may assume, inherit, or simulate the authority of another domain.

### 2. Runtime Enforcement Continuity

The current runtime enforcement model remains unchanged:

```
INSTRUMENT CLASS: MEASUREMENT
INSTRUMENT CLASS: DECISION SUPPORT
```

The four-domain model is constitutional analysis, not runtime taxonomy. Future Dev Orders may refine enforcement classes, but ADR-0010 does not mandate immediate CI changes.

### 3. Advisory Authority Boundaries

DECISION SUPPORT systems (Advisory, Interpretive) are constitutionally bounded as follows:

#### 3.1 May Do

- Highlight attention-worthy patterns
- Flag sparse, inconsistent, or anomalous data
- Suggest areas for operator review
- Provide contextual framing for measurements
- Emit `AttentionDirectiveV1` to display layers
- Fall back silently when external services are unavailable

#### 3.2 May NOT Do

- Establish measurement truth
- Validate or invalidate acoustic properties
- Canonize interpretations as authoritative
- Override, bypass, or pre-empt operator judgment
- Persist advisory outputs as measurement artifacts
- Appear in `viewer_pack_v1` exports
- Modify measurement data or session files

### 4. Operator Sovereignty

Operator authority is constitutionally supreme over advisory authority.

The operator:
- May accept advisory guidance
- May reject advisory guidance
- May reinterpret advisory guidance
- May ignore advisory guidance entirely

No DECISION SUPPORT system may:
- Require operator acknowledgment to proceed
- Block workflows pending advisory acceptance
- Escalate advisory confidence into implicit authority
- Record operator rejection as error or anomaly

### 5. Forbidden Vocabulary

DECISION SUPPORT modules MUST NOT use language that implies measurement authority, validation, or canonization.

#### Forbidden in Advisory/Interpretive Systems

| Forbidden | Reason |
|-----------|--------|
| `confirmed` | Implies validation authority |
| `verified` | Implies truth authority |
| `diagnosed` | Implies causal authority |
| `resolved` | Implies remediation authority |
| `proven` | Implies epistemic authority |
| `certified` | Implies institutional authority |
| `validated` | Implies correctness authority |
| `optimal` | Implies design authority |
| `correct` | Implies truth authority |
| `approved` | Implies acceptance authority |
| `canonical` | Implies reference authority |
| `best` | Implies ranking authority |
| `fixed` | Implies remediation authority |

#### Allowed Vocabulary

| Allowed | Usage |
|---------|-------|
| `observed` | Factual occurrence |
| `flagged` | Attention marker |
| `suggested for review` | Advisory guidance |
| `attention recommended` | Priority indicator |
| `possible anomaly` | Uncertainty-qualified observation |
| `potential drift` | Uncertainty-qualified pattern |
| `may indicate` | Hedged interpretation |
| `appears to correlate` | Observational association |

### 6. Semantic Authority Leakage Prevention

Even with runtime isolation, semantic authority can leak through:

1. **UI language** — advisory cards using authoritative vocabulary
2. **Confidence inflation** — high confidence scores read as validation
3. **Recommendation laundering** — advisory output treated as canonical by downstream systems
4. **Implicit approval** — lack of advisory flag interpreted as validation

DECISION SUPPORT systems must actively prevent these leakage patterns through:

- Explicit uncertainty qualification
- Clear advisory-vs-measurement labeling
- Operator sovereignty reminders in UI
- Non-authoritative visual styling (no green checkmarks, no "approved" badges)

### 7. Presentation-Layer Authority Leakage

UI styling, labels, badges, colors, confidence displays, and layout can imply authority even when runtime boundaries are correct.

#### Risk Categories

| Risk | Example | Consequence |
|------|---------|-------------|
| Visual validation | Green checkmarks on advisory output | User reads advisory as validated |
| Confidence conflation | "85% confidence" displayed as bare percentage | User reads as "85% correct" |
| Grade authority | "Quality Grade: A" without heuristic marker | User reads as calibrated measurement |
| Approval semantics | "PASSED" / "FAILED" badges on advisory | User reads advisory as test result |

#### Mitigation Requirements

1. **Color discipline** — No green/approval colors in advisory contexts
2. **Confidence qualification** — All confidence displays must include domain qualifier ("advisory confidence", "model fit confidence")
3. **Grade labeling** — All grade/quality labels must include "(heuristic)" or "(interpretive)"
4. **Badge vocabulary** — Use `REVIEW`, `INFO`, `ATTENTION`; never `VALIDATED`, `APPROVED`, `PASSED`
5. **Icon semantics** — Checkmarks reserved for operator acknowledgment, not advisory approval

See: `docs/ADVISORY_PRESENTATION_BOUNDARY.md` for complete visual and semantic rules.

---

## Relationship to ADR-0009

| ADR | Scope | Enforcement |
|-----|-------|-------------|
| ADR-0009 | Runtime/system separation | CI-enforced via `check_advisory_boundary.py` |
| ADR-0010 | Constitutional authority semantics | Doctrine; future CI hardening recommended |

ADR-0009 answers: *What code may execute where?*

ADR-0010 answers: *What kinds of claims are constitutionally legitimate?*

Both are required. Runtime separation without semantic governance allows authority creep within isolated systems.

---

## Future Governance Hardening (Recommendations)

The following enforcement mechanisms are recommended for future Dev Orders:

### Vocabulary Auditing

Add CI workflow that scans DECISION SUPPORT modules for forbidden vocabulary in:
- String literals
- UI labels
- Docstrings
- Comments

### UI Authority Boundary Linting

Validate that advisory components:
- Do not use validation-style iconography
- Include uncertainty qualifiers
- Display operator sovereignty notices

### Confidence-Semantic Separation

Ensure that numeric confidence scores are never presented as validation:
- `0.95 confidence` ≠ `95% validated`
- `high confidence` ≠ `confirmed`

### Recommendation-Language Detection

Flag language patterns that imply prescriptive authority:
- "should be adjusted"
- "needs to be changed"
- "must be corrected"

---

## Consequences

### Positive

- Constitutional clarity for all future DECISION SUPPORT development
- Prevention of authority creep before it occurs
- Explicit operator sovereignty protection
- Semantic governance complements existing structural governance
- Alignment with luthiers-toolbox constitutional principles

### Negative

- Requires vocabulary discipline in advisory UI development
- May require refactoring of existing advisory language
- Constitutional compliance is initially self-enforced (CI hardening deferred)

---

## Implementation Guidance

### For AGE Development

See: `docs/AGE_CONTRACT.md` for operational subsystem rules derived from this ADR.

### For New Advisory Systems

1. Declare `# INSTRUMENT CLASS: DECISION SUPPORT`
2. Review forbidden vocabulary list before UI text
3. Ensure operator sovereignty is not bypassed
4. Never persist advisory outputs to measurement artifacts
5. Include uncertainty qualifiers in all interpretive statements

### For Code Review

Reviewers should verify:
- No forbidden vocabulary in advisory UI
- No implicit authority escalation
- Operator sovereignty preserved
- Clear measurement-vs-advisory separation in user-facing text

---

## References

- ADR-0009: Advisory Boundary — Measurement vs Decision Support
- `docs/GOVERNANCE.md` Section 9: Analysis vs Interpretation
- `docs/AGE_CONTRACT.md`: Operational AGE rules
- `analyzer/guidance/engine.py`: AGE implementation

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-05-23  
**Owner:** tap-tone-pi governance
