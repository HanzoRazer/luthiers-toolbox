# Future CAD Semantic Layer Architecture

**Date:** 2026-05-14  
**Sprint:** MRP-5B  
**Status:** PROPOSAL (FUTURE CONSIDERATION)

---

## Purpose

Evaluates whether a dedicated CAD Semantic Layer between Export Object and STEP Translator would benefit the architecture, or whether direct extension of Export Object is sufficient.

---

## Architecture Options

### Option A: Direct Extension (RECOMMENDED)

```
Export Object
    │
    ├── geometry (2D)
    ├── validation
    ├── intent
    └── extensions
            ├── ibg_morphology (existing)
            └── cad_semantics (NEW)
                    │
                    ▼
            STEP Translator
                    │
                    └── Constructs topology
                    └── Emits STEP
```

**Pros:**
- Simplest architecture
- Single schema to maintain
- Consistent with DXF/SVG pattern
- No additional abstraction layer

**Cons:**
- CAD semantics in generic Export Object
- Complex morphology requires translator intelligence
- Potential schema growth over time

**Recommendation:** Use for MRP-5C through MRP-5E.

### Option B: Separate CAD Semantic Layer (FUTURE)

```
Export Object
    │
    ▼
CAD Semantic Layer
    │
    ├── Consumes Export Object
    ├── Resolves IBG morphology
    ├── Computes thickness profiles
    ├── Produces CADEnrichedObject
    │
    ▼
STEP Translator
    │
    └── Consumes CADEnrichedObject
    └── Constructs topology
    └── Emits STEP
```

**Pros:**
- Separates morphology resolution from serialization
- Multiple CAD translators share semantic layer
- Complex morphology handled once
- Cleaner translator interface

**Cons:**
- Additional layer to maintain
- New schema (CADEnrichedObject)
- May over-engineer simple cases
- Governance complexity

**Recommendation:** Consider only if multiple CAD translators with shared logic emerge.

---

## Analysis: When is Option B Justified?

### Criteria for Separate Layer

| Criterion | Threshold |
|-----------|-----------|
| Number of CAD translators | ≥ 3 |
| Shared morphology resolution logic | > 50% code overlap |
| Complexity of morphology → CAD mapping | Requires dedicated expertise |
| Schema evolution frequency | > 2 changes per quarter |

### Current State

| Criterion | Current | Threshold Met? |
|-----------|---------|----------------|
| CAD translators | 0 (1 proposed) | NO |
| Shared logic | N/A | NO |
| Morphology complexity | MODERATE | MAYBE |
| Schema evolution | STABLE | NO |

**Conclusion:** Option A (direct extension) is appropriate for current needs.

---

## Option B: Detailed Design (For Future Reference)

### CADEnrichedObject Schema

```python
class CADEnrichedObject(BaseModel):
    """
    Intermediate CAD-enriched representation.
    
    Produced by CAD Semantic Layer.
    Consumed by CAD Translators (STEP, IGES).
    """
    
    # Source reference
    source_export_id: str
    source_export_hash: str
    
    # Resolved geometry
    profile_wire: List[Tuple[float, float, float]]  # 3D wire (x, y, z)
    thickness_profile: List[float]  # Per-point thickness
    
    # Resolved morphology
    body_type: str  # flat | variable | carved
    extrusion_type: str  # constant | ruled | swept
    
    # Topology hints
    is_manifold_candidate: bool
    estimated_face_count: int
    
    # IBG resolution (if applicable)
    ibg_resolved: bool
    ibg_confidence: Optional[float]
```

### CAD Semantic Layer Functions

```python
class CADSemanticLayer:
    """
    Resolves Export Object + IBG morphology into CAD-ready representation.
    """
    
    def enrich(self, export_object: BodyExportObject) -> CADEnrichedObject:
        """
        Transform Export Object to CAD-enriched representation.
        
        Steps:
        1. Extract 2D profile
        2. Resolve thickness (uniform or from IBG)
        3. Compute 3D wire (x, y, thickness)
        4. Classify body type
        5. Generate topology hints
        """
        pass
    
    def _resolve_thickness(self, export_object) -> List[float]:
        """
        Determine thickness at each profile point.
        
        Priority:
        1. cad_semantics.uniform_thickness_mm (uniform)
        2. ibg_morphology.side_heights_mm (variable)
        3. Fail if neither available
        """
        pass
    
    def _compute_3d_wire(self, profile_2d, thickness) -> List[Tuple]:
        """
        Lift 2D profile to 3D using thickness values.
        """
        pass
```

### Integration Pattern

```python
# With CAD Semantic Layer (Option B)
def translate_step_with_layer(export_object):
    layer = CADSemanticLayer()
    enriched = layer.enrich(export_object)
    
    translator = StepTranslator()
    return translator.translate(enriched)

# Without CAD Semantic Layer (Option A - current recommendation)
def translate_step_direct(export_object):
    translator = StepTranslator()
    return translator.translate(export_object)  # Translator does enrichment internally
```

---

## Governance Implications

### Option A Governance

| Concern | Mitigation |
|---------|------------|
| CAD semantics in generic schema | Use extensions.cad_semantics (isolated) |
| Translator complexity | Accept moderate complexity |
| Schema growth | Limit to necessary fields |

### Option B Governance (Future)

| Concern | Mitigation |
|---------|------------|
| Additional schema to govern | New governance doc required |
| Layer authority boundaries | CAD Semantic Layer owns resolution |
| Translator interface change | Versioned interface |

---

## Decision Framework

### When to Adopt Option B

```
IF (
    number_of_cad_translators >= 3
    AND shared_resolution_logic > 50%
    AND morphology_complexity == HIGH
)
THEN
    Consider CAD Semantic Layer
ELSE
    Use Direct Extension (Option A)
```

### Trigger Events for Re-evaluation

1. STEP translator implemented and stable
2. IGES translator requested
3. Complex morphology (arch-top) in scope
4. Significant code duplication in translators
5. Schema evolution becomes frequent

---

## Recommendation

### For MRP-5B through MRP-5E

**Use Option A: Direct Extension**

- Add `extensions.cad_semantics` to Export Object
- STEP translator consumes cad_semantics directly
- IBG morphology remains advisory enrichment
- No separate CAD Semantic Layer

### For Future (MRP-6+ or triggered)

**Re-evaluate Option B if:**

- Multiple CAD translators share > 50% morphology logic
- Arch-top/hollow body support requires complex resolution
- Schema evolution frequency increases

---

## Migration Path (If Option B Adopted Later)

### Phase 1: Compatibility Shim

```python
class CADSemanticLayer:
    def enrich(self, export_object):
        # Initially, just pass through with minimal enrichment
        return CADEnrichedObject(
            source_export_id=export_object.export_id,
            profile_wire=self._lift_to_3d(export_object),
            # ... minimal resolution
        )
```

### Phase 2: Full Resolution

```python
class CADSemanticLayer:
    def enrich(self, export_object):
        # Full morphology resolution
        return CADEnrichedObject(
            # ... complete enrichment
        )
```

### Phase 3: Translator Migration

```python
# Old translator (reads Export Object)
# Deprecated, wrapped by CAD Semantic Layer

# New translator (reads CADEnrichedObject)
# Clean interface, simpler logic
```

---

## References

- `docs/architecture/CAD_SEMANTIC_EXTENSION_MODEL.md` — Extension model
- `docs/architecture/CAD_TRANSLATOR_BOUNDARY_MODEL.md` — Boundary model
- `docs/governance/CAD_SEMANTIC_AUTHORITY_RULES.md` — Authority rules
- `docs/handoffs/MRP_5A_STEP_FEASIBILITY_AUDIT.md` — Feasibility context
