# C2 Continuity Translator Discipline

```
C2-DX — TERMINAL 5 CONSTITUTIONAL REVIEW
TRANSLATOR NON-AUTHORITY EXTENSION
CONTINUITY SEMANTIC PRESERVATION
```

**Terminal:** 5 — Export/Serialization Reviewer  
**Phase:** C2-DX  
**Date:** 2026-05-18  
**Status:** DOCTRINE EXTENSION COMPLETE

---

## 1. Authority Statement

This document extends the translator non-authority doctrine to continuity semantics.

This document:
- Formalizes continuity preservation requirements for translators
- Defines prohibited continuity mutations
- Establishes consumption-without-canonization pattern
- Documents escalation paths for violations

This document does NOT:
- Modify translator implementations
- Create new translator categories
- Override existing translator governance
- Assign new continuity authorities

---

## 2. Constitutional Basis

### 2.1 Core Translator Doctrine

From C2-D and existing translator governance:

```
Translator = semantic consumer, NOT semantic authority.
```

### 2.2 Extended to Continuity

```
Continuity serializers may preserve continuity semantics.
They may NOT reinterpret, upgrade, collapse, or canonize continuity semantics.
```

This is now a formal constitutional extension.

---

## 3. Translator Continuity Discipline

### 3.1 Preservation Requirements

Translators receiving continuity data MUST:

| Requirement | Description |
|-------------|-------------|
| PRESERVE-C1 | Maintain continuity type distinction |
| PRESERVE-C2 | Maintain authority status (advisory vs enforcement) |
| PRESERVE-C3 | Maintain namespace boundaries |
| PRESERVE-C4 | Maintain provenance context |

### 3.2 Prohibited Mutations

Translators receiving continuity data MUST NOT:

| Prohibition | Description |
|-------------|-------------|
| PROHIBIT-C1 | Reinterpret continuity meaning |
| PROHIBIT-C2 | Upgrade advisory to enforcement |
| PROHIBIT-C3 | Collapse distinct continuity types |
| PROHIBIT-C4 | Canonize transient continuity state |
| PROHIBIT-C5 | Inject continuity assumptions |

---

## 4. Continuity Consumption Patterns

### 4.1 Pattern: Advisory Passthrough

```
ContinuityTarget flows through translator without interpretation.
Translator may log/emit the advisory hint.
Translator may NOT condition behavior on advisory hint.
```

**Example (compliant):**
```python
def translate(export_obj):
    # Passthrough — log but don't act
    if export_obj.cad_semantics:
        hint = export_obj.cad_semantics.acoustic.rim.continuity_target
        logger.info(f"Advisory continuity hint: {hint}")
    
    # Generate geometry from approved sources only
    return generate_from_boe(export_obj.geometry)
```

**Example (NON-COMPLIANT):**
```python
def translate(export_obj):
    # VIOLATION: Treating advisory as requirement
    hint = export_obj.cad_semantics.acoustic.rim.continuity_target
    if hint == ContinuityTarget.G1:
        enable_tangent_smoothing()  # WRONG: Advisory became behavior
```

### 4.2 Pattern: Enforcement Consumption

```
ContinuityLevel may condition translator behavior.
But translator does not become continuity authority.
Enforcement decision was made upstream (topology_builder).
```

**Example (compliant):**
```python
def translate(topology_result):
    # Consume enforcement decision, don't remake it
    for cont in topology_result.continuity:
        if not cont.met_target and topology_result.tier == TopologyTier.PRODUCTION:
            return TranslationError("Continuity requirement not met")
    
    # Proceed with approved topology
    return generate_from_topology(topology_result.shells)
```

### 4.3 Pattern: Governance Isolation

```
Governance continuity (7L) is never consumed by CAD/CAM translators.
Complete isolation between governance and geometry domains.
```

**Invariants (model-enforced):**
```
replayable = true (always)
immutable = true (always)
execution_authorized = false (always)
machine_output_allowed = false (always)
```

---

## 5. Translator Category Continuity Rules

### 5.1 SERIALIZATION Translators

| Rule | Requirement |
|------|-------------|
| Input | BOE geometry + optional cad_semantics |
| Continuity data | May receive ContinuityTarget (advisory) |
| Behavior | Geometry serialization only |
| Continuity output | NOT emitted to output format |

**Rationale:** STEP/DXF files are geometry containers. Continuity metadata is internal guidance, not geometry.

### 5.2 VISUALIZATION Translators

| Rule | Requirement |
|------|-------------|
| Input | TopologyResult or ExportObject |
| Continuity data | May receive ContinuityMetadata |
| Behavior | Display continuity status for user |
| Continuity output | Visual annotation only |

**Rationale:** Users may want to see continuity status. Visual display is informational, not authoritative.

### 5.3 MANUFACTURING Translators (Future)

| Rule | Requirement |
|------|-------------|
| Input | Approved topology with continuity validation |
| Continuity data | ContinuityMetadata (enforcement result) |
| Behavior | May reject if continuity requirements unmet |
| Continuity output | NOT emitted to G-code |

**Rationale:** Manufacturing translators consume enforcement decisions but do not remake them.

**Status:** No manufacturing translators currently authorized (`machine_output_supported=False`)

---

## 6. Escalation Surfaces

### 6.1 Escalation Triggers

| Trigger | Description | Escalation Level |
|---------|-------------|------------------|
| Advisory → Behavior | Translator conditions output on advisory hint | C2 Terminal 5 |
| Namespace Collapse | Multiple continuity types merged | C2 Terminal 3 + 5 |
| Canonization | Cached continuity treated as truth | C2 Terminal 4 + 5 |
| Authority Confusion | Translator claims continuity ownership | C2 Tier 3 (Human) |

### 6.2 Escalation Process

1. **Detection:** Code review or runtime monitoring
2. **Documentation:** Log in SEMANTIC_COLLISION_LOG.md
3. **Terminal Review:** Assigned terminal investigates
4. **Resolution:** Code correction or doctrine clarification

---

## 7. Compliance Verification

### 7.1 Current Translator Compliance

| Translator | Compliance | Evidence |
|------------|------------|----------|
| body_outline_dxf_r12 | COMPLIANT | No continuity consumption |
| body_export_bridge | COMPLIANT | Passthrough only |
| topology_builder | COMPLIANT | Enforcement at source |
| STEP translator | COMPLIANT | No continuity in output |

### 7.2 Verification Checklist

For any translator change involving continuity:

- [ ] Does it preserve advisory/enforcement distinction?
- [ ] Does it avoid conditioning behavior on advisory hints?
- [ ] Does it avoid emitting continuity to output format?
- [ ] Does it avoid canonizing transient continuity state?
- [ ] Is governance continuity completely isolated?

---

## 8. Anti-Patterns

### 8.1 Continuity Inflation

```
ANTI-PATTERN: Translator upgrades ContinuityTarget (advisory) to requirement.
SYMPTOM: Translation fails when G1 hint not met.
VIOLATION: PROHIBIT-C2
```

### 8.2 Continuity Deflation

```
ANTI-PATTERN: Translator ignores ContinuityLevel (enforcement) result.
SYMPTOM: PRODUCTION translation proceeds despite unmet continuity.
VIOLATION: Translator overriding upstream authority
```

### 8.3 Continuity Invention

```
ANTI-PATTERN: Translator infers continuity from geometry shape.
SYMPTOM: Translator assigns G1 based on curve smoothness.
VIOLATION: PROHIBIT-C5 (injecting assumptions)
```

### 8.4 Continuity Hardening

```
ANTI-PATTERN: Translator embeds continuity metadata in output file.
SYMPTOM: STEP file contains "G1_CONTINUITY" custom property.
VIOLATION: Export format becoming semantic authority
```

---

## 9. Relationship to Other Patterns

### 9.1 Consumer-Without-Authority Pattern

This doctrine is a continuity-specific instantiation of the general consumer-without-authority pattern from C2-D.

```
General: Systems may evaluate, constrain, or report without becoming authority.
Continuity: Translators may consume continuity without becoming continuity authority.
```

### 9.2 Translator Non-Geometry-Authority Pattern

This doctrine parallels the existing translator geometry discipline:

```
Geometry: Translators may not define approved geometry.
Continuity: Translators may not define continuity requirements.
```

---

## 10. Documentation Trail

### 10.1 Required Documentation

| Change Type | Documentation Required |
|-------------|----------------------|
| New translator | Continuity consumption plan in translator doc |
| Continuity field addition | Entry in SEMANTIC_INVENTORY.md |
| Consumption behavior change | Terminal 5 review |
| Escalation | Entry in SEMANTIC_COLLISION_LOG.md |

### 10.2 Cross-Reference

- `C2_CONTINUITY_EXPORT_PROPAGATION_REVIEW.md` — Primary review findings
- `C2_CONTINUITY_SERIALIZATION_BOUNDARIES.md` — Serialization constraints
- `C2_CONTINUITY_ARBITRATION_FRAMEWORK.md` — Constitutional basis
- `CONSUMER_WITHOUT_AUTHORITY_PATTERN.md` — General pattern reference

---

## 11. Summary

```
Translator continuity discipline:
  PRESERVE meaning
  PRESERVE authority status
  PRESERVE namespace boundaries
  DO NOT reinterpret
  DO NOT upgrade
  DO NOT collapse
  DO NOT canonize
```

This doctrine prevents export pipelines from becoming hidden ontology engines.

---

*C2-DX Continuity Translator Discipline — Terminal 5*
