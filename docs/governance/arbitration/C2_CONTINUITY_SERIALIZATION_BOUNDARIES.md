# C2 Continuity Serialization Boundaries

```
C2-DX — TERMINAL 5 CONSTITUTIONAL REVIEW
SERIALIZATION BOUNDARY CONSTRAINTS
CONTINUITY PRESERVATION DISCIPLINE
```

**Terminal:** 5 — Export/Serialization Reviewer  
**Phase:** C2-DX  
**Date:** 2026-05-18  
**Status:** BOUNDARY DEFINITION COMPLETE

---

## 1. Authority Statement

This document defines serialization boundaries for continuity semantics.

This document:
- Enumerates continuity serialization surfaces
- Defines boundary constraints for each surface
- Establishes serializer restraint rules
- Documents authority-state preservation requirements

This document does NOT:
- Implement serialization changes
- Modify existing serializers
- Create new continuity types
- Override C2-C namespace definitions

---

## 2. Constitutional Basis

From C2-D Continuity Arbitration Framework:

```
Serialization preserves semantics
without upgrading semantic legitimacy.
```

This is the foundational boundary rule.

---

## 3. Serialization Surface Inventory

### 3.1 Continuity Types and Serialization Paths

| Continuity Type | Serialization Path | Output Format | Authority Status |
|-----------------|-------------------|---------------|------------------|
| geometric_continuity (ContinuityLevel) | TopologyResult | JSON (internal) | ENFORCEMENT |
| semantic_continuity (ContinuityTarget) | ExportObject.extensions.cad_semantics | JSON | ADVISORY |
| governance_continuity | GovernanceContinuityGraph | JSON (internal) | ISOLATED |
| manufacturing_continuity (TopologyTier) | TopologyRequest | JSON (internal) | OPERATIONAL |
| runtime_continuity | (not serialized) | N/A | TRANSIENT |

### 3.2 Serialization Surface Status

| Surface | Current Behavior | Boundary Compliance |
|---------|------------------|---------------------|
| ContinuityLevel → TopologyResult | Serialized as enum string | COMPLIANT |
| ContinuityTarget → CadSemantics | Serialized as enum string | COMPLIANT |
| ContinuityMetadata → TopologyResult | Serialized with target/achieved | COMPLIANT |
| TranslatorProvenance | No continuity fields | COMPLIANT |
| STEP output | No continuity data | COMPLIANT |
| DXF output | No continuity data | COMPLIANT |

---

## 4. Boundary Constraints

### 4.1 Constraint: No Continuity Upgrade Through Serialization

```
CONSTRAINT-SERIAL-001:
Serializers may NOT upgrade advisory continuity to enforcement continuity.
```

**Rationale:** ContinuityTarget is advisory. Serializing it to a format that implies enforcement would mutate semantic authority.

**Verification:**
- ContinuityTarget remains string enum in JSON
- No conversion to ContinuityLevel in serialization
- No validation enforcement on ContinuityTarget values

**Status:** VERIFIED — No upgrade path exists

### 4.2 Constraint: No Continuity Collapse Through Serialization

```
CONSTRAINT-SERIAL-002:
Serializers may NOT collapse multiple continuity types into single field.
```

**Rationale:** Geometric, governance, and semantic continuity are distinct. A single "continuity" field would destroy namespace separation.

**Verification:**
- TopologyResult has `continuity: List[ContinuityMetadata]` (geometric only)
- CadSemantics has `rim.continuity_target` (semantic only)
- No unified "continuity" field in any output schema

**Status:** VERIFIED — Types remain separate

### 4.3 Constraint: No Continuity Canonization Through Caching

```
CONSTRAINT-SERIAL-003:
Cached continuity values may NOT be treated as canonical without revalidation.
```

**Rationale:** Continuity evaluation may change with different tier, tolerance, or context. Cached values are snapshots, not truth.

**Verification:**
- TopologyResult.continuity is per-request evaluation
- No long-term continuity cache in export artifacts
- Provenance metadata does not include continuity state

**Status:** VERIFIED — No hardening through caching

### 4.4 Constraint: Provenance Preservation

```
CONSTRAINT-SERIAL-004:
Serialized continuity MUST carry sufficient provenance to reconstruct authority source.
```

**Rationale:** Downstream consumers must know whether continuity data is advisory or enforcement, and its source.

**Verification:**
- ContinuityTarget docstring declares advisory status
- TopologyResult includes tier context
- CadSemantics authority rule in docstring

**Status:** PARTIALLY VERIFIED — Source documented in code but not in serialized data. Consider adding `authority_source` field.

---

## 5. Output Format Boundaries

### 5.1 JSON Export Object

**What is serialized:**
- `cad_semantics.acoustic.rim.continuity_target` — advisory hint
- `cad_semantics.body_category` — routing hint
- `cad_semantics.flat_body` — construction parameters

**What is NOT serialized:**
- ContinuityLevel enforcement values
- Governance continuity hashes
- Runtime validation state

**Boundary status:** COMPLIANT

### 5.2 STEP/IGES Output

**What is serialized:**
- Geometry (approved BOE data only)
- Surface topology (constructed by translator)

**What is NOT serialized:**
- Any continuity metadata
- Any advisory hints
- Any governance data

**Boundary status:** COMPLIANT — Output is geometry-only

### 5.3 DXF Output

**What is serialized:**
- 2D geometry (outlines, toolpaths)
- Layer structure

**What is NOT serialized:**
- Any continuity metadata
- Any advisory hints
- Any governance data

**Boundary status:** COMPLIANT — Output is geometry-only

---

## 6. Authority-State Preservation

### 6.1 Advisory Status Markers

| Field | Authority Status | Marker |
|-------|------------------|--------|
| ContinuityTarget | ADVISORY | Docstring: "ADVISORY ONLY" |
| RimSemantics.continuity_target | ADVISORY | Description: "not enforced" |
| IBGMorphologyExtension | ADVISORY | (NEEDS MARKER — see COLL-E002) |

### 6.2 Enforcement Status Markers

| Field | Authority Status | Marker |
|-------|------------------|--------|
| ContinuityLevel | ENFORCEMENT | Used in validate_continuity() |
| TopologyTier | OPERATIONAL | Validation behavior depends on it |

### 6.3 Gap: Serialized Authority Markers

**Issue:** Advisory status is documented in code but not in serialized output.

**Risk:** Downstream consumers (especially external systems) cannot determine authority without reading source code.

**Recommendation:** Consider adding optional `authority` field to serialized schemas:

```python
class ContinuityTarget(str, Enum):
    G0 = "G0"
    G1 = "G1"
    
    @property
    def authority_status(self) -> str:
        return "advisory"  # Always advisory
```

**Priority:** LOW — current consumers are internal and code-aware

---

## 7. Serializer Restraint Rules

### 7.1 Rules for New Serializers

Any new serializer involving continuity data MUST:

1. **Preserve namespace separation**
   - Do not merge continuity types
   - Use distinct field paths

2. **Preserve authority status**
   - Advisory stays advisory
   - Enforcement stays enforcement

3. **Preserve provenance**
   - Include source identifier
   - Include tier/context if applicable

4. **Avoid canonization**
   - Do not cache as permanent truth
   - Revalidate on consumption

### 7.2 Prohibited Patterns

```
ANTI-PATTERN: Flattening continuity types
ANTI-PATTERN: Implicit authority upgrade
ANTI-PATTERN: Caching without provenance
ANTI-PATTERN: Stripping advisory markers
ANTI-PATTERN: Converting hints to requirements
```

---

## 8. Verification Checklist

For any export/serialization change affecting continuity:

- [ ] Does it preserve namespace separation?
- [ ] Does advisory remain advisory?
- [ ] Does enforcement remain enforcement?
- [ ] Is authority source traceable?
- [ ] Is it documented in serialization inventory?
- [ ] Does it comply with CONSTRAINT-SERIAL-001 through 004?

---

## 9. Related Documents

- `C2_CONTINUITY_EXPORT_PROPAGATION_REVIEW.md` — Primary review
- `C2_CONTINUITY_TRANSLATOR_DISCIPLINE.md` — Translator constraints
- `C2_CONTINUITY_ARBITRATION_FRAMEWORK.md` — Constitutional basis
- `inventory/export_serialization/SEMANTIC_INVENTORY.md` — Term inventory

---

*C2-DX Continuity Serialization Boundaries — Terminal 5*
