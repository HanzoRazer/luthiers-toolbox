# Consumer Without Authority Pattern

```
GOVERNANCE PATTERN EVIDENCE
OBSERVATIONAL AND NON-PRESCRIPTIVE
NOT CONSTITUTIONAL AUTHORITY
NOT MANDATORY IMPLEMENTATION GUIDANCE
MAY INFORM FUTURE GOVERNANCE RECONCILIATION
```

**Date:** 2026-05-18  
**Phase:** C1 Observational Freeze  
**Source Domain:** Acoustics/Observational  
**Classification:** Cross-Domain Governance Pattern Evidence

---

## Purpose

This document describes a governance pattern observed during C1 inventory:

```
A subsystem may consume data, derive observations, produce diagnostics,
and create interpretations without acquiring authority over the
originating semantic domain.
```

This pattern appears foundational for:
- Export systems
- Visualization layers
- Translator systems
- Topology consumption
- Runtime observers

---

## Pattern Definition

### Core Principle

```
Consumption does not imply ownership.
Derivation does not create authority.
```

A consumer system may:
- Read data from an authoritative source
- Derive new values from that data
- Store derived values for local use
- Expose derived values to downstream consumers

A consumer system should NOT:
- Redefine the meaning of consumed data
- Claim ownership over consumed semantics
- Modify the authoritative source
- Assert authority over the originating domain

---

## Observed Implementation (Acoustics Domain)

### Consumer Interface Pattern

```typescript
// packages/client/src/types/acoustics.ts

/**
 * Geometry-like interface for acoustic state.
 * Decoupled from Vue component exports to keep domain types clean.
 */
interface ApertureGeometryLike {
  aperture_type?: string
  area_mm2?: number
  perimeter_mm?: number
  equivalent_diameter_mm?: number
  // ...
}

interface AcousticState {
  /** Associated aperture geometry (reference, not merged) */
  apertureGeometry?: ApertureGeometryLike
  // ...
}
```

Key observations:
- **Consumer interface** — `ApertureGeometryLike` is a consumption interface
- **Explicit decoupling** — "Decoupled from Vue component exports"
- **Reference semantics** — "reference, not merged"
- **Domain separation** — "to keep domain types clean"

### Geometry Summary Pattern

```typescript
// packages/client/src/types/acoustics/measurementArchive.ts

/**
 * Lightweight geometry summary for archive context.
 * Avoids full geometry payload duplication.
 */
interface MeasurementArchiveGeometrySummary {
  apertureType?: string
  areaMm2?: number
  equivalentDiameterMm?: number
  paRatioMmInv?: number
}
```

Key observations:
- **Summary, not duplication** — "Avoids full geometry payload duplication"
- **Context only** — "for archive context"
- **Subset of canonical** — Only essential fields included

---

## Pattern Structure

### Consumption Flow

```
Authoritative Domain (Geometry)
        ↓ exposes canonical interface
Consumer Interface (ApertureGeometryLike)
        ↓ reads via reference
Consumer Domain (Acoustics)
        ↓ derives local values
Local Storage (MeasurementArchiveGeometrySummary)
        ↓ serves local consumers
Downstream Systems
```

### Authority Preservation

| Layer | Authority Status |
|-------|------------------|
| Canonical geometry | Authoritative — owns shape definition |
| Consumer interface | Non-authoritative — read-only consumption |
| Acoustic derivations | Non-authoritative — local interpretation |
| Archive summary | Non-authoritative — snapshot for context |

---

## Pattern Requirements

For a system to implement consumer-without-authority:

### Requirement 1: Explicit Consumer Interface

Define an interface for consumption that is distinct from the authoritative interface:

```typescript
// GOOD: Explicit consumer interface
interface GeometryConsumerView {
  area_mm2: number
  perimeter_mm: number
}

// BAD: Direct dependency on canonical type
import { CanonicalGeometry } from '@/geometry'  // Creates coupling
```

### Requirement 2: Reference Semantics

Hold references to consumed data, not copies that could diverge:

```typescript
// GOOD: Reference semantics
apertureGeometry?: ApertureGeometryLike  // Optional reference

// BAD: Merged ownership
geometry: { ...fullGeometryPayload }  // Implies ownership
```

### Requirement 3: Documented Non-Goals

Explicitly state what the consumer does NOT own:

```
// GOOD: Explicit non-goals
"Archives preserve observations, not conclusions."
"Geometry remains separate (ApertureGeometry is not merged into this)"

// BAD: Ambiguous scope
"Handles all geometry operations"
```

### Requirement 4: Local Vocabulary Scoping

Use domain-specific vocabulary for derived values:

```typescript
// GOOD: Domain-specific derived term
estimatedHelmholtzHz?: number  // Acoustic domain term

// BAD: Generic term that could imply authority
frequency?: number  // Ambiguous scope
```

---

## Anti-Patterns

### Anti-Pattern 1: Authority Accumulation

```
BAD: Consumer starts defining semantics for consumed domain

Example:
Acoustics consumer starts defining what "valid geometry" means,
then other systems start depending on acoustics' geometry validation.

RESULT: Consumer has become de facto authority.
```

### Anti-Pattern 2: Mutation Rights

```
BAD: Consumer modifies consumed data

Example:
Acoustics consumer "normalizes" geometry values before storing,
creating divergence from canonical source.

RESULT: Consumer has acquired mutation authority.
```

### Anti-Pattern 3: Semantic Redefinition

```
BAD: Consumer redefines meaning of consumed terms

Example:
Acoustics uses "area" to mean "acoustic effective area"
which differs from geometric area.

RESULT: Term collision, semantic drift.
```

### Anti-Pattern 4: Coupling Escalation

```
BAD: Consumer interface becomes canonical interface

Example:
Other systems start depending on ApertureGeometryLike
instead of the canonical geometry types.

RESULT: Consumer interface has become authority.
```

---

## Applicability

This pattern is applicable to systems that:
- Read data from authoritative sources
- Derive values for local/domain-specific use
- Do not need to modify the source
- Do not need to define source semantics

This pattern may NOT apply to systems that:
- Are themselves authoritative sources
- Need mutation rights over consumed data
- Define the canonical representation of consumed data
- Own the lifecycle of consumed data

---

## Pattern Benefits

### For the Consumer

- Clear authority boundary — no responsibility for source semantics
- Independent evolution — consumer vocabulary can change without affecting source
- Reduced coupling — consumer interface isolates from source changes

### For the Authority

- Protected semantics — authority definitions are not diluted by consumers
- Clear ownership — no confusion about who defines truth
- Governance clarity — authority can evolve without consumer coordination

### For the Federation

- Scalable consumption — many consumers can exist without authority fragmentation
- Semantic integrity — consumption does not create competing definitions
- Clear reconciliation paths — authority vs consumer distinction is explicit

---

## Implementation Checklist

For systems implementing this pattern:

- [ ] Consumer interface is distinct from authoritative interface
- [ ] References used instead of merged copies
- [ ] Non-goals explicitly documented
- [ ] Domain-specific vocabulary for derived values
- [ ] No mutation of consumed data
- [ ] No redefinition of consumed semantics
- [ ] Documented as consumer, not authority

---

## Extension: Continuity Evaluators

*Added C2-D/C2-DP (2026-05-18) — Extends consumer-without-authority to continuity evaluation systems.*

### Continuity Evaluator Discipline

```
Systems may:
- Evaluate continuity quality (G0/G1/G2 junction analysis)
- Constrain transitions (manufacturing feasibility)
- Report continuity status (pass/fail/warning)
- Enforce continuity requirements (production gates)

WITHOUT:
- Becoming geometry authority
- Defining semantic truth
- Claiming canonical status
- Creating governance
```

### Evaluator Requirements

| Requirement | Implementation | Purpose |
|-------------|----------------|---------|
| Evaluation role explicit | "evaluator", not "definer" | Prevents authority accumulation |
| Constraint provenance | Where constraint originated | Maintains derivation visibility |
| Non-authority marker | Cannot define geometry truth | Preserves authority boundary |
| Scope limitation | Evaluation scope documented | Prevents scope creep |
| Derivation status | Carries PROV_DERIVATION | Constitutional provenance compliance |

### Continuity Evaluator Interface

```typescript
// GOOD: Continuity evaluator interface
interface ContinuityEvaluator {
  evaluateContinuity(junction: JunctionData): ContinuityResult
  // Returns: evaluation result with explicit non-authority marker
}

interface ContinuityResult {
  junction_id: string
  continuity_level: 'G0' | 'G1' | 'G2'
  evaluation_method: string           // How continuity was assessed
  constraint_source: string           // Where constraints originated
  provenance_type: 'PROV_DERIVATION'  // Always derivation
  authority_state: 'derived'          // Never canonical
  does_not_imply: string              // Explicit non-authority statement
}

// BAD: Evaluator claiming authority
interface ContinuityAuthority {
  canonicalContinuity: ContinuityLevel  // NO — evaluators don't define
  validateGeometry(): boolean            // NO — geometry authority elsewhere
}
```

### Continuity Evaluator Anti-Patterns

```
ANTI-PATTERN: Continuity evaluation defining geometry
  Example: G2 evaluation treating smooth junction as "correct geometry"
  Result: Continuity quality ≠ geometry truth

ANTI-PATTERN: Manufacturing constraint becoming canonical
  Example: "Manufacturable" treated as "valid morphology"
  Result: Operational feasibility ≠ constitutional ratification

ANTI-PATTERN: Runtime continuity check becoming semantic law
  Example: State preservation success treated as semantic authority
  Result: Runtime ≠ governance

ANTI-PATTERN: Continuity violation implying geometry invalidity
  Example: Failed G2 check means geometry is "wrong"
  Result: Transition quality ≠ shape correctness

ANTI-PATTERN: Evaluation frequency implying authority
  Example: "We always check this continuity" treated as ownership
  Result: Usage pattern ≠ governance authority
```

### Continuity-Specific Checklist Extension

For continuity evaluators specifically:

- [ ] Evaluator interface uses PROV_DERIVATION provenance
- [ ] Constraint source documented (where requirement originated)
- [ ] Non-authority marker present ("evaluator, not definer")
- [ ] Continuity type preserved (geometric vs manufacturing vs shell vs runtime vs semantic)
- [ ] Evaluation scope explicit (what junctions/surfaces evaluated)
- [ ] Does not escalate operational → canonical
- [ ] Does not collapse continuity types

### False Collapse Prevention

| False Collapse | Risk | Prevention |
|----------------|------|------------|
| G2 achieved → "correct geometry" | Continuity ≠ correctness | Separate concerns |
| Runtime maintained → "semantic preserved" | Runtime ≠ semantic | Different layers |
| Manufacturable → "canonical morphology" | Operational ≠ canonical | Authority-state separation |
| Continuity satisfied → "semantic authority" | Satisfaction ≠ authority | Explicit non-authority markers |

### Constitutional Integration

This extension integrates with:
- C2-D Continuity Arbitration Framework (5 continuity surfaces)
- C2-DP Continuity Provenance Review (provenance requirements)
- RISK-CONT-002 prevention (manufacturability hardening)
- RISK-CONT-003 prevention (runtime escalation)

---

## Related Documents

- `ACOUSTICS_GOVERNANCE_REFERENCE_PATTERN.md` — Source implementation evidence
- `OBSERVATIONAL_SEMANTICS_BOUNDARY_NOTES.md` — Related boundary guidance
- `../inventory/C1_STRATEGIC_FINDINGS.md` — Federation-level observations
- `../GEOMETRY_AUTHORITY_DECOMPOSITION.md` — Geometry authority analysis
- `../REPOSITORY_CONSTITUTION.md` — Constitutional invariants
- `../arbitration/C2_CONTINUITY_ARBITRATION_FRAMEWORK.md` — Continuity decomposition
- `../arbitration/C2_CONTINUITY_PROVENANCE_REVIEW.md` — Continuity provenance requirements

---

*Cross-Domain Governance Pattern Evidence — Observational and Non-Prescriptive*
*C2-D/C2-DP Continuity Extension Integrated*
