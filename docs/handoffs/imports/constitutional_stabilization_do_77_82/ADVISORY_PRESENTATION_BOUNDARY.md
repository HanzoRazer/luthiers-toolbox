# Advisory Presentation Boundary

**Version:** 1.0.0  
**Date:** 2026-05-23  
**Constitutional Foundation:** ADR-0010 (Advisory Authority Constitutional Boundary)  
**Scope:** Visual and semantic presentation rules for advisory outputs

---

## Purpose

This document defines how the four authority domains (Measurement, Advisory, Interpretive, Operator) must be presented visually and semantically in tap-tone-pi UI, reports, and outputs.

Even with correct runtime boundaries, presentation-layer authority leakage can occur when:

- Advisory outputs use measurement-style visual hierarchy
- Confidence scores are displayed without qualification
- Grade/quality labels imply validation rather than heuristic classification
- Urgency styling resembles approval/rejection indicators

---

## Presentation Domains

### 1. Measurement Presentation

**Purpose:** Display captured observational records with provenance.

**Allowed language:**

| Term | Usage |
|------|-------|
| `recorded` | Factual capture |
| `measured` | Physical observation |
| `captured` | Data acquisition |
| `detected` | Signal presence |
| `specimen` | Physical sample reference |
| `session` | Capture session identifier |

**Visual characteristics:**

- Neutral colors (grays, blues)
- Provenance metadata (timestamp, device, hash)
- No grade badges or approval indicators
- Clear "Measurement" or "Record" section labels

**Example:**

```
┌─────────────────────────────────────┐
│ MEASUREMENT RECORD                  │
│                                     │
│ Specimen: SP_001                    │
│ Captured: 2026-05-23 14:32:01 UTC   │
│ Device: UMIK-1 @ 48kHz              │
│ Dominant frequency: 203.1 Hz        │
│ SHA256: a3f8c9...                   │
└─────────────────────────────────────┘
```

---

### 2. Advisory Presentation

**Purpose:** Guide operator attention without implying validation.

**Allowed language:**

| Term | Usage |
|------|-------|
| `flagged` | Attention marker |
| `suggested for review` | Advisory guidance |
| `attention recommended` | Priority indicator |
| `possible` | Uncertainty qualifier |
| `potential` | Uncertainty qualifier |
| `may indicate` | Hedged interpretation |

**Forbidden language:**

| Forbidden | Reason |
|-----------|--------|
| `verified` | Implies truth authority |
| `validated` | Implies correctness authority |
| `confirmed` | Implies validation authority |
| `diagnosed` | Implies causal authority |
| `optimal` | Implies design authority |
| `best` | Implies ranking authority |

**Visual characteristics:**

- Amber/neutral tones for attention (never green for "good")
- Clear "Advisory" or "Guidance" section labels
- No checkmarks, approval badges, or validation icons
- Urgency indicators use intensity, not approval/rejection semantics

**Example:**

```
┌─────────────────────────────────────┐
│ ● REVIEW                            │
│                                     │
│ Possible wolf tone flagged at 247 Hz│
│                                     │
│ A potential coupling pattern was    │
│ observed. Review suggested.         │
│                                     │
│ [Focus] [Dismiss]                   │
└─────────────────────────────────────┘
```

**Not:**

```
┌─────────────────────────────────────┐
│ ✓ VERIFIED                          │  ← Forbidden
│                                     │
│ Wolf tone confirmed at 247 Hz       │  ← Forbidden
│ Optimal mitigation: add 5g damper   │  ← Forbidden
└─────────────────────────────────────┘
```

---

### 3. Interpretive Presentation

**Purpose:** Provide semantic framing without asserting truth.

**Allowed language:**

| Term | Usage |
|------|-------|
| `suggests` | Interpretive framing |
| `appears to` | Uncertainty-qualified observation |
| `correlates with` | Observational association |
| `consistent with` | Pattern matching |
| `characteristic of` | Category association |
| `heuristic` | Explicitly non-authoritative |

**Visual characteristics:**

- Distinct from measurement presentation (different section styling)
- Clear "Interpretation" or "Analysis" labels
- Confidence displayed with qualification (see Confidence Semantics below)
- Grade labels marked as heuristic, not validation

**Example:**

```
┌─────────────────────────────────────┐
│ INTERPRETATION (heuristic)          │
│                                     │
│ Radiation coefficient: 11.2         │
│ Suggests characteristics consistent │
│ with Sitka spruce.                  │
│                                     │
│ Grade: A (heuristic, not validated) │
└─────────────────────────────────────┘
```

---

### 4. Operator Decision Presentation

**Purpose:** Display choices made by the human operator.

**Allowed language:**

| Term | Usage |
|------|-------|
| `selected` | Operator choice |
| `dismissed` | Operator rejection of advisory |
| `acknowledged` | Operator saw guidance |
| `recorded` | Operator decision logged |

**Visual characteristics:**

- Operator actions are logged, not judged
- No "correct" or "incorrect" styling for operator choices
- Dismissal is neutral, not an error condition

---

## Confidence Semantics Boundary

### Problem

Numeric confidence scores (e.g., "85% confidence") can be misread as validation percentages. A user may interpret "85% confidence" as "85% likely to be correct" or "85% validated."

### Rule

Confidence must be decomposed by meaning:

| Context | Display Format | Meaning |
|---------|----------------|---------|
| Measurement repeatability | `Repeatability: 0.92` | Signal consistency |
| Coherence quality | `Coherence: 0.85` | Frequency-domain reliability |
| Model fit | `Model fit: good` | Physics model alignment (not validation) |
| Advisory confidence | `Advisory confidence: high` | Guidance strength (not truth claim) |

### Forbidden Patterns

| Forbidden | Reason |
|-----------|--------|
| `Confidence: 85%` (bare) | Implies validation percentage |
| `Validated with 90% confidence` | Conflates confidence with validation |
| `High confidence = verified` | False equivalence |

### Required Patterns

| Required | Reason |
|----------|--------|
| `Advisory confidence: high` | Scopes confidence to advisory domain |
| `Model confidence: medium (heuristic)` | Marks as interpretive |
| `Repeatability confidence: 0.92` | Scopes to measurement domain |

---

## Grade/Quality Label Rules

### Background

`quality_grade` (A/B/C/D) in wood_properties.py is explicitly annotated as:

> "HEURISTIC ONLY, not a calibrated measurement. Do not include in viewer_pack_v1."

However, UI presentation of "Quality Grade: A" without context can imply validation.

### Rule

Grade labels in advisory/interpretive contexts must include qualification:

| Forbidden | Allowed |
|-----------|---------|
| `Quality Grade: A` | `Quality Grade: A (heuristic)` |
| `Grade: AAA` | `Estimated Grade: AAA (interpretive)` |
| `Rating: Excellent` | `Heuristic Rating: High radiation coefficient` |

---

## Visual Styling Rules

### Color Semantics

| Color | Meaning | NOT Meaning |
|-------|---------|-------------|
| Blue | Information, measurement | — |
| Amber | Attention, review suggested | Warning, error |
| Gray | Neutral, context | — |
| Green | **Forbidden in advisory context** | Approval, validation |
| Red | **Use sparingly** | Error only, not "bad measurement" |

### Icon Semantics

| Icon | Allowed Context | Forbidden Context |
|------|-----------------|-------------------|
| ✓ Checkmark | Operator acknowledged | Advisory validation |
| ✕ X mark | Dismiss advisory | Measurement rejection |
| ● Dot | Attention indicator | Approval indicator |
| ⚠ Warning | System error only | Measurement quality |

### Badge Semantics

| Badge Style | Allowed | Forbidden |
|-------------|---------|-----------|
| `REVIEW` | Advisory action | — |
| `INFO` | Advisory information | — |
| `VALIDATED` | — | All contexts |
| `APPROVED` | — | All contexts |
| `PASSED` | — | Advisory contexts |
| `FAILED` | — | Advisory contexts |

---

## Report Presentation Rules

### HTML Reports

Reports generated by `analyzer/reports/html_report.py` must:

1. Clearly separate measurement sections from interpretive sections
2. Label confidence with domain qualifier
3. Mark grade labels as heuristic
4. Not use green/checkmark styling for advisory outputs

### JSON Reports

Reports generated by `analyzer/reports/json_report.py` must:

1. Include `_presentation_domain` field indicating section type
2. Include `_is_heuristic: true` for advisory/interpretive fields
3. Not include advisory fields in viewer_pack_v1-compatible outputs

---

## Implementation Checklist

For new advisory UI components:

- [ ] No forbidden vocabulary in labels or text
- [ ] Confidence displayed with domain qualifier
- [ ] Grade labels marked as heuristic
- [ ] No green checkmarks or approval badges
- [ ] Clear section label (Advisory/Guidance/Interpretation)
- [ ] Dismissal is neutral, not error-styled
- [ ] Urgency uses intensity, not approval/rejection semantics

---

## Future Hardening Recommendations

### Lexical CI Guard

Future Dev Orders may add a CI workflow that scans presentation strings for:

- Forbidden vocabulary in advisory contexts
- Bare confidence percentages without domain qualifier
- Grade labels without heuristic marker

### UI Component Linting

Future tooling may validate that:

- Advisory components do not use green/checkmark styling
- Confidence displays include qualification
- Grade labels include "(heuristic)" or equivalent

---

## References

- ADR-0010: Advisory Authority Constitutional Boundary
- ADR-0009: Advisory Boundary — Measurement vs Decision Support
- `docs/AGE_CONTRACT.md`: AGE presentation rules
- `analyzer/reports/html_report.py`: Report generation
- `analyzer/guidance/panel.py`: Advisory UI widget

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-05-23  
**Owner:** tap-tone-pi governance
