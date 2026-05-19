# Geometry Authority Decomposition

**Status:** DRAFT FOR GOVERNANCE RATIFICATION  
**Authority:** NOT CANONICAL UNTIL RATIFIED — NOT CI BLOCKING POLICY UNTIL WIRED  
**Date:** 2026-05-18  
**Purpose:** Geometry layer ownership separation  
**Constitutional Dependency:** REPOSITORY_CONSTITUTION.md §3, §7

---

## 1. Authority Statement

This document decomposes geometry authority across semantic layers.

```
DRAFT FOR GOVERNANCE RATIFICATION
NOT CANONICAL UNTIL RATIFIED
NOT CI BLOCKING POLICY UNTIL WIRED
```

---

## 2. The Geometry Problem

```
"Geometry" refers to both data and visualization.
This ambiguity creates authority confusion.
```

### Current Ambiguity

| Usage | Meaning | Domain |
|-------|---------|--------|
| "Body geometry" | Coordinates, curves, topology | Instrument definition |
| "Geometry layer" | DXF layer, visual grouping | CAM export |
| "Resolve geometry" | Transform intent to shapes | CAM runtime |
| "Geometry validation" | Check shape constraints | Quality assurance |

### Constitutional Grounding

This decomposition implements:
- Constitutional Invariant 1: No subsystem may silently become ontology authority
- Constitutional Invariant 7: Location is not authority

---

## 3. Geometry Layer Decomposition

| Layer | Code | Description | Example |
|-------|------|-------------|---------|
| Semantic Geometry | `GEOM_SEMANTIC` | What the geometry means | "This is the body outline" |
| Coordinate Geometry | `GEOM_COORDINATE` | Where points are located | `[(0,0), (100,0), (100,200)]` |
| Topological Geometry | `GEOM_TOPOLOGY` | How elements connect | "Closed contour", "Adjacent faces" |
| Presentation Geometry | `GEOM_PRESENTATION` | How geometry is displayed | "Blue line, 0.5mm weight" |
| Export Geometry | `GEOM_EXPORT` | How geometry is serialized | "LWPOLYLINE on BODY_OUTLINE layer" |

---

## 4. Authority Ownership Matrix

| Layer | Canonical Owner | Operational Owner | Must NOT Own |
|-------|-----------------|-------------------|--------------|
| `GEOM_SEMANTIC` | Instrument Ontology | Domain Sprint Team | CAM runtime |
| `GEOM_COORDINATE` | Coordinate System Spec | Implementation | Visualization |
| `GEOM_TOPOLOGY` | Instrument Ontology | Domain Sprint Team | Export format |
| `GEOM_PRESENTATION` | UI/Visualization | Frontend Team | Semantic meaning |
| `GEOM_EXPORT` | CAM Export Spec | CAM Team | Instrument definition |

### Must NOT Own Explained

| Layer | Forbidden Owner | Reason |
|-------|-----------------|--------|
| `GEOM_SEMANTIC` | CAM runtime | Runtime consumes ontology; runtime does not define ontology (Invariant 2) |
| `GEOM_COORDINATE` | Visualization | Visualization presents coordinates; visualization does not define them |
| `GEOM_TOPOLOGY` | Export format | Export serializes topology; export does not define it |
| `GEOM_PRESENTATION` | Semantic meaning | Presentation is display; presentation is not definition |
| `GEOM_EXPORT` | Instrument definition | Export is output format; export is not instrument ontology |

---

## 5. Layer Relationships

### Dependency Direction

```
GEOM_SEMANTIC
    ↓ (defines meaning of)
GEOM_TOPOLOGY
    ↓ (constrains structure of)
GEOM_COORDINATE
    ↓ (provides data for)
GEOM_PRESENTATION ← (parallel to) → GEOM_EXPORT
```

### Dependency Rules

| Rule | Description |
|------|-------------|
| Semantic governs topology | Topology must preserve semantic meaning |
| Topology constrains coordinates | Coordinates must satisfy topological constraints |
| Coordinates feed presentation | Presentation renders coordinate data |
| Coordinates feed export | Export serializes coordinate data |
| Presentation does not affect export | Visual choices do not change export format |
| Export does not affect presentation | Export format does not change display |

---

## 6. Current System Mapping

### Instrument Geometry (`instrument_geometry/`)

| Component | Primary Layer | Secondary Layer |
|-----------|---------------|-----------------|
| Body outline | `GEOM_SEMANTIC` | `GEOM_TOPOLOGY` |
| Soundhole position | `GEOM_SEMANTIC` | `GEOM_COORDINATE` |
| Fret positions | `GEOM_COORDINATE` | `GEOM_SEMANTIC` |
| Bridge placement | `GEOM_SEMANTIC` | `GEOM_COORDINATE` |

### CAM Runtime (`cam/runtime/`)

| Component | Primary Layer | Secondary Layer |
|-----------|---------------|-----------------|
| `resolve_geometry` | `GEOM_COORDINATE` | `GEOM_TOPOLOGY` |
| `preview` | `GEOM_PRESENTATION` | `GEOM_COORDINATE` |
| `export` | `GEOM_EXPORT` | `GEOM_COORDINATE` |

### Blueprint Vectorizer (`blueprint-import/`)

| Component | Primary Layer | Secondary Layer |
|-----------|---------------|-----------------|
| Contour extraction | `GEOM_COORDINATE` | `GEOM_TOPOLOGY` |
| Category classification | `GEOM_SEMANTIC` | `GEOM_TOPOLOGY` |
| DXF output | `GEOM_EXPORT` | `GEOM_COORDINATE` |

### IBG Morphology (`instrument_geometry/body/ibg/`)

| Component | Primary Layer | Notes |
|-----------|---------------|-------|
| Body grid | `GEOM_TOPOLOGY` | Evidence, not ontology |
| Zone classification | `GEOM_SEMANTIC` | Proposed, not canonical |
| Contour analysis | `GEOM_COORDINATE` | Extracted, not defined |

---

## 7. Authority Boundaries

### Boundary 1: Semantic ↔ Coordinate

```
Semantic layer defines WHAT geometry means.
Coordinate layer defines WHERE geometry is located.
Neither may assume the other's authority.
```

| Permitted | Forbidden |
|-----------|-----------|
| Semantic references coordinate by ID | Semantic hardcodes coordinate values |
| Coordinate satisfies semantic constraints | Coordinate invents semantic meaning |

### Boundary 2: Topology ↔ Export

```
Topology layer defines HOW elements connect.
Export layer defines HOW elements are serialized.
Neither may assume the other's authority.
```

| Permitted | Forbidden |
|-----------|-----------|
| Export preserves topological relationships | Export modifies topology for format |
| Topology agnostic to export format | Topology requires specific export format |

### Boundary 3: Presentation ↔ Semantic

```
Presentation layer defines HOW geometry is displayed.
Semantic layer defines WHAT geometry means.
Neither may assume the other's authority.
```

| Permitted | Forbidden |
|-----------|-----------|
| Presentation varies by semantic category | Presentation defines semantic meaning |
| Semantic agnostic to presentation | Semantic requires specific presentation |

---

## 8. Resolution Process

When geometry authority is unclear:

### Step 1: Identify Layer

| Question | Answer Determines |
|----------|-------------------|
| "What does this represent?" | `GEOM_SEMANTIC` |
| "Where is it located?" | `GEOM_COORDINATE` |
| "How does it connect?" | `GEOM_TOPOLOGY` |
| "How should it look?" | `GEOM_PRESENTATION` |
| "How should it be saved?" | `GEOM_EXPORT` |

### Step 2: Check Ownership Matrix

Refer to §4 for canonical and operational owners.

### Step 3: Apply Constitutional Invariants

- Is runtime claiming semantic authority? (Invariant 2 violation)
- Is evidence being treated as ontology? (Invariant 3 violation)
- Is usage being treated as ratification? (Invariant 8 violation)

### Step 4: Escalate if Unresolved

If layer or ownership is still unclear, escalate to Human Arbiter per `GOVERNANCE_RATIFICATION_MODEL.md`.

---

## 9. Existing Risks

### Risk 1: CAM `resolve_geometry` Scope Creep

| Current State | Risk | Mitigation |
|---------------|------|------------|
| `resolve_geometry` transforms intent to coordinates | May evolve to define semantic meaning | Hard invariant: `observational_only = True` |

### Risk 2: Vectorizer Classification Authority

| Current State | Risk | Mitigation |
|---------------|------|------------|
| Vectorizer classifies contours semantically | May become de facto semantic authority | Containment: evidence flag, not canonical |

### Risk 3: IBG Zone Definition

| Current State | Risk | Mitigation |
|---------------|------|------------|
| IBG proposes zone vocabulary | May leak into canonical without ratification | Experimental containment policy |

### Risk 4: DXF Layer = Semantic Category

| Current State | Risk | Mitigation |
|---------------|------|------------|
| DXF layers named after semantic categories | Export format may be mistaken for semantic definition | Clear documentation: export reflects semantics, does not define them |

---

## 10. Geometry Vocabulary Alignment

### Existing Vocabulary Terms (from CANONICAL_ONTOLOGY_VOCABULARY.md)

| Term | Geometry Layer Mapping |
|------|------------------------|
| `body_outline` | `GEOM_SEMANTIC` (meaning) + `GEOM_TOPOLOGY` (closed contour) |
| `coordinate_system` | `GEOM_COORDINATE` |
| `contour` | `GEOM_TOPOLOGY` |
| `layer` (DXF) | `GEOM_EXPORT` |

### Proposed Vocabulary Extensions

| Term | Layer | Description |
|------|-------|-------------|
| `geometry_layer_semantic` | N/A | Meta-term for this decomposition |
| `geometry_layer_coordinate` | N/A | Meta-term for this decomposition |
| `geometry_layer_topology` | N/A | Meta-term for this decomposition |
| `geometry_layer_presentation` | N/A | Meta-term for this decomposition |
| `geometry_layer_export` | N/A | Meta-term for this decomposition |

These meta-terms describe the decomposition itself, not geometry instances.

---

## 11. Open Geometry Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | Should geometry layers be explicitly tagged in schemas? | Traceability |
| 2 | Should layer crossing require explicit declaration? | Boundary enforcement |
| 3 | Should export format be decoupled from CAM? | Separation of concerns |
| 4 | Should presentation be a domain or cross-cutting concern? | Ownership clarity |
| 5 | Should IBG zone vocabulary be promoted to canonical? | Vocabulary expansion |

---

## Related Documents

- `REPOSITORY_CONSTITUTION.md` — Constitutional authority
- `CANONICAL_ONTOLOGY_VOCABULARY.md` — Geometry-related vocabulary
- `CANONICAL_AUTHORITY_MAP.md` — Authority assignments
- `docs/architecture/CAM_RUNTIME_DISPATCHER_ARCHITECTURE.md` — CAM geometry handling
- `EXPERIMENTAL_ONTOLOGY_POLICY.md` — IBG containment

---

*Geometry Authority Decomposition — DRAFT FOR GOVERNANCE RATIFICATION*
