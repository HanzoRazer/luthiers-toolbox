# ADR-0011: Measurement Authority Constitutional Definition

**Status:** Accepted  
**Date:** 2026-05-24  
**Supersedes:** None  
**Extends:** ADR-0009, ADR-0010  
**Scope:** Constitutional doctrine (no runtime implementation)

---

## Context

tap-tone-pi emits measurement artifacts that flow downstream to luthiers-toolbox, RMOS, and other consumers. These artifacts carry implicit authority — they are treated as "true" by downstream systems.

However, the platform has not yet constitutionally defined:

1. What makes a measurement artifact authoritative
2. The distinction between measurement and truth
3. When measurement authority may be legitimately questioned
4. How authority flows (or should not flow) across system boundaries

Without these definitions, authority emerges implicitly through:
- Repetition
- UI reinforcement
- Historical recurrence
- Confidence inheritance

This ADR establishes the constitutional foundation for measurement authority to prevent accidental canonization and authority laundering.

---

## Decision

### 1. Authoritative Measurement Artifact Definition

A measurement artifact is **authoritative** when it satisfies all of the following:

| Requirement | Meaning |
|-------------|---------|
| **Captured** | Data originates from physical sensor observation |
| **Provenance-linked** | Hash, timestamp, device ID, and session ID are recorded |
| **Unmodified** | Raw capture has not been altered post-acquisition |
| **Schema-compliant** | Artifact validates against declared schema version |
| **Instrument-class declared** | Source module declares INSTRUMENT CLASS: MEASUREMENT |

An artifact missing any of these requirements is **not constitutionally authoritative** as a measurement, regardless of how it is labeled or presented.

### 2. Measurement vs Truth Distinction

**Constitutional principle:**

```
Measurement authority ≠ Truth authority
```

A measurement artifact is authoritative as a **captured record of observation**. It is NOT authoritative as:

- Acoustic truth
- Physical reality
- Instrument quality
- Design correctness
- Optimal configuration

| Measurement Says | Measurement Does NOT Say |
|------------------|--------------------------|
| "203.1 Hz was observed" | "203.1 Hz is correct" |
| "Coherence was 0.85" | "The measurement is valid" |
| "WSI peak at 247 Hz" | "Wolf tone exists at 247 Hz" |

This distinction is foundational. Downstream systems may interpret measurements, but interpretation does not inherit measurement authority.

### 3. Capture Integrity Requirements

For a measurement to be constitutionally authoritative, capture integrity must be verifiable:

| Integrity Aspect | Requirement |
|------------------|-------------|
| **Temporal** | Timestamp must be accurate to ±1 second |
| **Device** | Capture device must be identified |
| **Session** | Capture must belong to a traceable session |
| **Hash** | Content hash must be recorded at capture time |
| **Format** | Audio must pass through canonical WAV I/O layer |

Artifacts that bypass these requirements (e.g., direct file imports without provenance) are **not measurement-authoritative** — they are **externally-sourced** with different epistemic status.

### 4. Contextual Measurement Legitimacy

**Constitutional principle:**

```
Measurement legitimacy is context-dependent
```

A measurement artifact may have reduced legitimacy due to:

| Context Factor | Impact |
|----------------|--------|
| **Environmental instability** | Temperature, humidity, or acoustic environment outside calibration bounds |
| **Calibration uncertainty** | Device calibration expired or unverified |
| **Hardware drift** | Sensor characteristics changed since calibration |
| **Capture contamination** | Ambient noise, handling artifacts, or interference detected |
| **Procedural deviation** | Capture did not follow established protocol |

**Constitutional implication:** Downstream systems may NOT assume all measurements are equally legitimate. Environmental and calibration metadata, when present, must be preserved and available for legitimacy assessment.

**Not defined here:** Specific downgrade algorithms, thresholds, or scoring systems. Those are implementation decisions for future Dev Orders.

### 5. Provenance Legitimacy

Provenance is constitutionally distinct from measurement authority:

| Concept | Definition |
|---------|------------|
| **Measurement authority** | The artifact faithfully represents what was captured |
| **Provenance legitimacy** | The chain of custody from capture to current state is traceable |

An artifact may be measurement-authoritative but provenance-incomplete (e.g., hash present but session metadata lost).

An artifact may be provenance-complete but measurement-questionable (e.g., full metadata but environmental contamination noted).

Both dimensions matter independently.

### 6. Authority Does Not Transfer

**Constitutional principle:**

```
Measurement authority does not transfer to derived artifacts
```

When a measurement artifact is:
- Transformed (FFT, filtering, resampling)
- Aggregated (averaging, statistical summary)
- Interpreted (peak detection, mode identification)
- Annotated (operator notes, advisory flags)

The resulting artifact has **different epistemic status**. It may be:
- **Derived** (mathematical transform)
- **Estimated** (inferential approximation)
- **Heuristic** (non-authoritative guidance)

But it is NOT measurement-authoritative, even if derived from authoritative measurements.

See: ADR-0012 (Epistemic Status Taxonomy) for complete classification.

---

## Authority Laundering Prevention

### The Laundering Chain

Authority can emerge implicitly through cumulative reinforcement:

```
┌─────────────────────────┐
│  Measurement Confidence │  ← Authoritative as captured record
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Advisory Interpretation │  ← NOT measurement-authoritative
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Historical Weighting   │  ← Repeated observation ≠ truth
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Operator Trust         │  ← Human judgment, not system authority
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Emergent Canonization  │  ← CONSTITUTIONAL VIOLATION
└─────────────────────────┘
```

### Constitutional Interruption Points

At each transition, the system must NOT allow silent authority elevation:

| Transition | Constitutional Gate |
|------------|---------------------|
| Measurement → Advisory | Epistemic status must change to HEURISTIC or DERIVED |
| Advisory → Historical | Repetition does not elevate epistemic status |
| Historical → Operator Trust | Operator judgment is OPERATOR-ANNOTATED, not MEASUREMENT |
| Trust → Canonization | **FORBIDDEN** — no system path may create canonical authority |

### Legitimacy Barriers

Systems must implement explicit barriers:

1. **Epistemic status must be preserved** — artifacts carry their status through all transformations
2. **Status elevation is forbidden** — no operation may upgrade epistemic status
3. **Operator sovereignty is final** — operator judgment cannot be overridden by accumulated system confidence

---

## Downstream Consumer Responsibility

### Scope

tap-tone-pi is the **origin authority** for measurement artifacts.

Downstream systems (luthiers-toolbox, RMOS, future consumers) are **authority consumers** with constitutional responsibilities.

### Consumer Requirements

Downstream systems:

| Must | Must NOT |
|------|----------|
| Preserve epistemic status metadata | Silently elevate epistemic status |
| Display measurement vs advisory distinction | Present derived data as measurement-authoritative |
| Respect operator sovereignty | Override operator judgment with system confidence |
| Maintain provenance chain | Strip provenance metadata |

### Cross-Boundary Authority

When artifacts cross repository boundaries:

1. Epistemic status must be declared in export format
2. Import must not assume MEASUREMENT status without verification
3. Externally-sourced artifacts have EXTERNALLY-SOURCED status, not MEASUREMENT

---

## Relationship to Other ADRs

| ADR | Scope | Relationship |
|-----|-------|--------------|
| ADR-0009 | Runtime boundary (MEASUREMENT vs DECISION SUPPORT) | ADR-0011 defines what MEASUREMENT means constitutionally |
| ADR-0010 | Advisory authority boundaries | ADR-0011 defines what advisory systems may NOT claim |
| ADR-0012 | Epistemic status taxonomy | ADR-0011 establishes why taxonomy is needed |

---

## Future Work (Not Implemented Here)

The following are identified for future Dev Orders:

- Environmental downgrade algorithms and thresholds
- Calibration validity tracking
- Provenance chain verification tooling
- Epistemic status schema fields
- Export format extensions for epistemic metadata
- Historical learning systems with anti-laundering gates

These require constitutional foundation (this ADR) before implementation.

---

## Consequences

### Positive

- Clear definition of measurement authority
- Prevention of accidental canonization
- Authority laundering chain identified and gated
- Downstream consumer responsibilities clarified
- Foundation for epistemic status tracking

### Negative

- Requires epistemic status tracking in future implementations
- Downstream systems must update to preserve status
- Additional metadata overhead

---

## References

- ADR-0009: Advisory Boundary — Measurement vs Decision Support
- ADR-0010: Advisory Authority Constitutional Boundary
- ADR-0012: Epistemic Status Taxonomy
- `docs/EPISTEMIC_STATUS_SCHEMA_IMPLICATIONS_REVIEW.md`

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-05-24  
**Owner:** tap-tone-pi governance
