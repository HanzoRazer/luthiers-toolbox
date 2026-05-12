# Governance Duplication Audit

**Date:** 2026-05-07  
**Status:** AUDIT DELIVERABLE  
**Purpose:** Identify duplicate, overlapping, and conflicting governance definitions

---

## Executive Summary

The repository has accumulated parallel governance systems during rapid development (6A-6I sprint chain + MRP-1A/1B). This audit identifies semantic overlaps that create confusion and potential enforcement conflicts.

**Findings:**
- 3 conflicting lifecycle/maturity taxonomies
- 2 competing "canonical" definitions
- 5 parallel registry/manifest systems
- 1 scope ambiguity (RMOS identity)
- 2 naming convention conflicts

---

## Duplication Category 1: Lifecycle State Terminology

### The Problem

Four governance systems define "lifecycle" or "maturity" states with different names and semantics:

| System | States | Semantics |
|--------|--------|-----------|
| RMOS 2.0 | GREEN, YELLOW, RED | Risk levels for manufacturing |
| CAM Export | GREEN, YELLOW, RED | Gate status for export |
| CAM Capability | experimental, candidate, governed, canonical | Operation maturity |
| Feature Parity | Canonical, Mounted Legacy, Beta Shell, Parity Verified | Migration states |
| MRP | LOCKED, STABILIZED | Protection levels |

### Overlapping Semantics

| Term | RMOS 2.0 | CAM Export | CAM Capability | Feature Parity |
|------|----------|------------|----------------|----------------|
| "Green" | Safe to run | All checks pass | N/A | N/A |
| "Canonical" | N/A | N/A | Highest maturity | Trusted production |
| "Governed" | N/A | N/A | Mid-high maturity | N/A |
| "Locked" | N/A | N/A | N/A | N/A (MRP uses) |

### Conflict Risk

- A "canonical" operation in CAM Capability is not the same as "Canonical" in Feature Parity
- GREEN in RMOS and CAM Export are semantically similar but not explicitly linked
- No unified state machine across systems

### Recommendation

**Consolidate to unified terminology:**

| Universal Term | Meaning | Replaces |
|----------------|---------|----------|
| GREEN/YELLOW/RED | Validation gate status | RMOS risk, CAM gate |
| canonical/governed/candidate/experimental | Component maturity | CAM Capability levels |
| production/migration/beta/deprecated | Lifecycle stage | Feature Parity states |
| locked/stabilized/open | Protection level | MRP levels |

---

## Duplication Category 2: "Canonical" Definition Conflict

### The Problem

Two governance systems define "canonical" with different semantics:

**CAM Capability Registry:**
```python
MaturityLevel = Literal["experimental", "candidate", "governed", "canonical"]
```
- "canonical" = highest maturity, GREEN gate behavior, full lifecycle support

**Feature Parity Migration Policy:**
```text
State 1 — Canonical: The currently trusted implementation
```
- "Canonical" = trusted production implementation, opposite of beta shell

### Conflict Scenario

A component can be:
- "canonical" (CAM Capability) but NOT "Canonical" (Feature Parity)
  - e.g., canonical CAM operation in a beta workspace
- "Canonical" (Feature Parity) but not in CAM registry at all
  - e.g., SpiralSoundholeDesigner.vue is Canonical but has no CAM Capability entry

### Recommendation

**Rename to avoid collision:**

| Current | Proposed | System |
|---------|----------|--------|
| canonical (maturity) | `mature` or keep `canonical` | CAM Capability |
| Canonical (migration) | `production_canonical` or `parity_verified` | Feature Parity |

Or add qualifier in documentation:
- "CAM-canonical" vs "migration-canonical"

---

## Duplication Category 3: Classification Taxonomies

### The Problem

Two separate classification systems exist:

**CAM Export Architecture (Layer Classification):**
- NEUTRAL
- PREVIEW
- EXPORT
- GOVERNANCE
- MACHINE OUTPUT

**CAM Capability Registry (Exportability Class):**
- preview_only
- governed_export
- translator_ready
- machine_candidate

### Overlap Analysis

| CAM Export | CAM Capability | Relationship |
|------------|----------------|--------------|
| PREVIEW | preview_only | Direct mapping |
| EXPORT | governed_export | Partial overlap |
| EXPORT | translator_ready | Subset of EXPORT |
| MACHINE OUTPUT | machine_candidate | Candidate for MACHINE OUTPUT |

### Conflict Risk

- `governed_export` in Capability is not explicitly linked to `EXPORT` in Architecture
- `machine_candidate` suggests future MACHINE OUTPUT but Architecture says "NOT IMPLEMENTED"
- No cross-reference between systems

### Recommendation

**Add explicit mapping table** in CAM_GOVERNED_EXPORT_ARCHITECTURE.md:

```markdown
## Capability → Layer Mapping

| Exportability Class | Applicable Layers |
|---------------------|-------------------|
| preview_only | Layers 1-3 only |
| governed_export | Layers 1-5 |
| translator_ready | Layers 1-6 (validation only) |
| machine_candidate | Layers 1-7 (future) |
```

---

## Duplication Category 4: Multiple Manifest Systems

### The Problem

11 manifest/registry files exist without unified schema or cross-reference:

| Manifest | Owner | Schema |
|----------|-------|--------|
| governance_manifest.json | MRP | Protected systems, paths |
| governed_export_manifest.json | CAM 6A | Layers, classifications |
| cam_preview_standard_manifest.json | CAM 5C | Preview operations |
| cam_machine_output_manifest.json | CAM | Machine output status |
| rosette_cam_route_manifest.json | CAM | Rosette routes |
| rosette_governance_gate_manifest.json | CAM | Rosette gates |
| regression_corpus/manifest.json | MRP | Test artifacts |
| benchmark_manifest.json | Vectorizer | Benchmark cases |

### Overlap Analysis

- `governance_manifest.json` and `governed_export_manifest.json` both govern "what is protected"
- `cam_preview_standard_manifest.json` and `governed_export_manifest.json` both list preview operations
- No unified index of all manifests

### Recommendation

**Create manifest index** in `docs/governance/MANIFEST_INDEX.md`:

```markdown
## Manifest Registry

| Manifest | Domain | Purpose | Schema Version |
|----------|--------|---------|----------------|
| governance_manifest.json | MRP | Protected paths | 1.0.0 |
| governed_export_manifest.json | CAM | Export architecture | 1.0.0 |
```

**Long-term:** Consider unified manifest schema with domain partitions.

---

## Duplication Category 5: RMOS Scope Ambiguity

### The Problem

"RMOS" appears in two contexts with unclear relationship:

**RMOS 2.0 Specification:**
- "Rosette Manufacturing Operating System"
- Focused on rosette/Art Studio workflows
- 6 subsystems: Material, Calculator, Feasibility, Geometry, Toolpath, BOM

**CAM Export Architecture:**
- "Layer 5: RMOS Persistence"
- Generic artifact storage, lineage, provenance
- Not rosette-specific

### Questions

1. Is "RMOS Persistence" in CAM Export the same as RMOS 2.0?
2. Does RMOS 2.0 govern all manufacturing, or just rosette workflows?
3. Should Layer 5 be renamed to avoid confusion?

### Evidence

**RMOS 2.0 Spec says:**
> "RMOS 2.0 = the Manufacturing Brain of the ToolBox"

**But also:**
> "Release Intent: Foundation for AI-assisted rosette manufacturing, Art Studio integration..."

**CAM Export Architecture says:**
> "Layer 5: RMOS Persistence... Artifact storage, lineage, provenance"

### Recommendation

**Clarify scope in RMOS 2.0 Specification:**

Option A: RMOS owns all manufacturing
```markdown
RMOS 2.0 governs all manufacturing workflows including:
- Rosette operations (original scope)
- CAM export persistence (Layer 5)
- Run artifacts for all operations
```

Option B: RMOS is rosette-specific, Layer 5 is separate
```markdown
RMOS 2.0 governs rosette manufacturing.
CAM Export Layer 5 ("Artifact Persistence") is a separate system.
```

Current ambiguity must be resolved.

---

## Duplication Category 6: Naming Convention Conflicts

### Sprint Namespace vs CAM Dev Order

**Sprint Namespace Standard:**
```
{PREFIX}-{NUMBER}{SUFFIX}: {Description}
Examples: VECTOR-1A, IBG-1, CAM-1
```

**CAM Handoffs:**
```
CAM_6A_GOVERNED_EXPORT_HANDOFF.md
CAM_6H_CAPABILITY_REGISTRY_HANDOFF.md
```

These are consistent, but the namespace standard doesn't explicitly register "6A-6I" as a chain.

### Recommendation

**Add 6A-6I to Sprint Namespace registry:**

```markdown
| Prefix | Domain | Notes |
|--------|--------|-------|
| CAM-6 | CAM pipeline | 6A-6I governed export chain |
```

---

## Summary Table: Duplications Found

| Category | Systems | Conflict Level | Recommendation |
|----------|---------|----------------|----------------|
| Lifecycle states | 4 systems | Medium | Consolidate terminology |
| "Canonical" definition | 2 systems | High | Rename or qualify |
| Classification taxonomies | 2 systems | Medium | Add mapping table |
| Manifest systems | 8 manifests | Low | Create index |
| RMOS scope | 2 contexts | High | Clarify in spec |
| Naming conventions | 2 patterns | Low | Register in namespace |

---

## Action Items

### Immediate (documentation only):

1. Add authority hierarchy reference to CLAUDE.md governance section
2. Add RMOS scope clarification to RMOS_2.0_Specification.md
3. Add Capability→Layer mapping to CAM_GOVERNED_EXPORT_ARCHITECTURE.md
4. Create MANIFEST_INDEX.md listing all manifests

### Near-term (low code risk):

1. Add `_maturity_system` field to distinguish CAM vs migration "canonical"
2. Add cross-references between related governance docs
3. Register 6A-6I in SPRINT_NAMESPACE_STANDARD.md

### Future (design required):

1. Unified governance manifest schema
2. Unified lifecycle state machine
3. Single pre-commit enforcement aggregating all governance

---

## Governance Expansion Rules

To prevent future duplication, new governance must:

1. **Check existing systems** — Does this concept already exist under another name?
2. **Declare authority tier** — Is this Tier 1, 2, or 3?
3. **Register in index** — Add to MANIFEST_INDEX.md if creating manifest
4. **Add cross-references** — Link to related governance docs
5. **Use standard terminology** — GREEN/YELLOW/RED for gates, canonical/governed/candidate for maturity

---

*Governance Duplication Audit — 2026-05-07*
