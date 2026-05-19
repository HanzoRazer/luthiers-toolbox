# C1 Terminal 5: Export/Serialization Semantic Inventory

**Phase**: C1 — Collection (no decisions, no changes)  
**Date**: 2026-05-18  
**Scope**: Export lifecycle semantics, translator governance, serialization boundary enforcement, provenance propagation, CAD semantic extensions, RMOS export gates

---

## 1. Strategic Significance

Terminal 5 (Export/Serialization) is the **highest-pressure semantic surface** in the repository.

Export/serialization is where:
- Operational semantics become externalized representations
- Internal assumptions propagate into downstream systems
- Translator simplifications may silently become semantic law
- Geometry authority claims crystallize into file artifacts
- Provenance tracking either preserves or collapses lineage

**Primary governance concern:**

```
Serialization-driven ontology hardening:
  Exported geometry becomes assumed canonical.
  Translator simplifications become semantic law.
  Provenance collapse becomes invisible.
```

---

## 2. Export Object Semantics

### 2.1 ExportType

**Source**: `app/cam/export_object.py:40-43`

| Value | Meaning | Serialization Risk |
|-------|---------|-------------------|
| `TOOLPATH` | Contains manufacturing moves | Future G-code generation |
| `GEOMETRY` | Contains geometric entities | DXF/SVG/STEP output |
| `BUNDLE` | Contains multiple exports | Compound artifact |

**Key Invariant** (from docstring):
> "This is NOT machine output. No G-code. No executable."

This invariant is **governance-enforced** — ExportObject explicitly blocks machine output generation in the current phase.

---

### 2.2 Export Schema Version

**Source**: `app/cam/export_object.py:34`

```python
EXPORT_SCHEMA_VERSION = "1.0.0"
```

**Governance Pattern**: Explicit version declaration prevents implicit schema drift.

---

### 2.3 Coordinate System Semantics

**Source**: `app/export/body_export_bridge.py:73-84`

| Field | Value | Semantic Role |
|-------|-------|---------------|
| `origin` | `body_center` | Coordinate reference point |
| `x_axis` | `width` | Lateral axis semantics |
| `y_axis` | `length_toward_neck` | Longitudinal axis direction |
| `z_axis` | `thickness` | Depth axis semantics |
| `z_zero` | `top_face` | Z-origin reference |
| `units` | `mm` | Unit system |
| `handedness` | `right_handed` | Coordinate handedness |
| `frame` | `local_workpiece` | Reference frame |

**Governance Pattern**: Coordinate semantics are **explicit and preserved** through export pipeline. No implicit coordinate transformation occurs.

---

## 3. Translator Governance Vocabulary

### 3.1 TranslatorMaturity

**Source**: `app/cam/translator_capability_registry.py:39-44`

| Value | Meaning | Execution Authorization |
|-------|---------|------------------------|
| `placeholder` | Registered but not implemented | None |
| `candidate` | Under validation | Validation only |
| `governed` | Production-ready, governed | Authorized |
| `canonical` | Canonical implementation | Full authority |

---

### 3.2 ExecutionState

**Source**: `app/cam/translator_capability_registry.py:46-52`

| Value | Meaning | Flags |
|-------|---------|-------|
| `validation_only` | Can validate, cannot execute | All false |
| `execution_planned` | Execution planned but not authorized | All false |
| `execution_disabled` | Explicitly disabled | All false |
| `execution_authorized_future` | Future execution | Transitional |
| `governed_execution` | Full execution authorized | execution_supported=True |

**Key Invariant**: `machine_output_supported` must always be false (no G-code translators authorized).

---

### 3.3 TranslatorCategory (MRP-4A)

**Source**: `app/cam/translators/base/capabilities.py:17-24`

| Value | Meaning | Output Type |
|-------|---------|-------------|
| `SERIALIZATION` | Geometry to file format | DXF, SVG, STEP |
| `VISUALIZATION` | Visual output | PNG, PDF preview |
| `MANUFACTURING` | CAM-ready output | G-code, toolpaths |
| `ARCHIVAL` | Long-term storage | Archive formats |
| `ANALYSIS` | Measurement/analysis | Reports |

**Governance Pattern**: `MANUFACTURING` category is **blocked** — no authorized translators produce machine output.

---

## 4. Translator Protocol Invariants

### 4.1 ExportTranslator Protocol

**Source**: `app/cam/translators/base/contracts.py:108-160`

**Key Invariants** (from docstring):
1. Translators consume semantics, they do not create semantics
2. Translators are stateless
3. Translators cannot mutate the input Export Object
4. Output is deterministic given the same input (excluding timestamps)

**Governance Significance**: These invariants prevent **serialization-driven semantic creation**. Translators may only represent existing semantics — they may not invent new meaning.

---

### 4.2 Gate Enforcement

**Source**: `app/cam/translators/base/contracts.py:204-219`

```python
def _check_gate(self, export_object):
    gate_status = export_object.validation.gate_status
    if gate_status == "red":
        return TranslatorError(
            code=TranslatorErrorCode.GATE_RED,
            message="Export Object gate is red - translation blocked",
        )
    return None
```

**Governance Pattern**: Translators **refuse to process red-gated exports**. This prevents invalid geometry from propagating into externalized representations.

---

## 5. CAD Semantic Extension Authority Model

### 5.1 Authority Declaration

**Source**: `app/export/cad_semantics.py:14-17`

```
Authority Model:
- BOE: Geometry authority (immutable)
- IBG: Morphology authority (advisory)
- cad_semantics: CAD construction hints (optional)
- Translator: Topology construction (from approved data only)
```

**Key Rule** (from docstring):
> "CAD semantics may EXTEND approved geometry context. They may NOT override, reinterpret, or invent approved geometry."

**Governance Significance**: This is the **constitutional boundary** between semantic extension and semantic authority. CAD semantics are hints, not authority.

---

### 5.2 RuntimeSupport Classification

**Source**: `app/export/cad_semantics.py:72-77`

| Value | Meaning | Topology Generation |
|-------|---------|---------------------|
| `SUPPORTED` | Full runtime generation | Yes |
| `SEMANTIC_ONLY` | Schema valid, no runtime | No |
| `UNSUPPORTED` | Not supported | No |

**Governance Pattern**: Many semantic configurations are `SEMANTIC_ONLY` — they exist for schema validation and future use but do not drive runtime generation. This prevents premature semantic hardening.

---

### 5.3 BodyCategory

**Source**: `app/export/cad_semantics.py:31-41`

| Value | RuntimeSupport |
|-------|----------------|
| `FLAT_BODY` | SUPPORTED |
| `ACOUSTIC_FLAT_TOP` | SEMANTIC_ONLY |
| `ACOUSTIC_ARCHED_TOP` | SEMANTIC_ONLY |
| `HOLLOW_ELECTRIC` | SEMANTIC_ONLY |
| `ARCHTOP` | SEMANTIC_ONLY |
| `RESONATOR` | UNSUPPORTED |
| `UNKNOWN` | UNSUPPORTED |

**Governance Pattern**: Only `FLAT_BODY` has runtime support. All acoustic body categories are **semantic-only** — they cannot generate topology but preserve classification intent.

---

## 6. Provenance Propagation

### 6.1 TranslatorProvenance

**Source**: `app/cam/translators/base/contracts.py:48-71`

| Field | Semantic Role |
|-------|---------------|
| `export_id` | Source export identifier |
| `translator_id` | Translator identity |
| `translator_version` | Translator version |
| `translated_at` | Translation timestamp |
| `target_format` | Output format |
| `source_hash` | Geometry content hash |
| `ibg_session_id` | IBG session link (if available) |
| `instrument_spec` | Instrument specification (if available) |

**Governance Pattern**: Provenance is **explicitly embedded** in translator output. This prevents anonymous geometry artifacts.

---

### 6.2 IBG Morphology Extension Propagation

**Source**: `app/export/body_export_bridge.py:163-172`

```python
class IBGMorphologyExtension(BaseModel):
    session_id: str
    confidence: float
    dimensions: Dict[str, float]
    instrument_spec: str
    side_heights_mm: Optional[List[float]] = None
    radii_by_zone: Optional[Dict[str, float]] = None
    missing_landmarks: Optional[List[str]] = None
    recovery_mode: Optional[str] = None
```

**Governance Risk**: IBG morphology data propagates through export pipeline. If downstream consumers treat this as authoritative geometry (rather than advisory morphology), **authority leakage** occurs.

---

## 7. RMOS Export Governance

### 7.1 Feasibility Enforcement Gates

**Source**: `app/rmos/runs_v2/exports.py:5-10`

| Risk Level | Export Behavior |
|------------|-----------------|
| `GREEN` | Proceeds normally |
| `YELLOW` | Requires override attachment |
| `RED` | Requires override AND RMOS_ALLOW_RED_OVERRIDE=1 |

**Governance Pattern**: RMOS exports enforce **feasibility gates** before allowing operator pack download. This prevents manufacturing artifacts from propagating when feasibility is compromised.

---

### 7.2 Operator Pack Contents

**Source**: `app/rmos/runs_v2/exports.py:279-285`

| File | Role | Immutability |
|------|------|--------------|
| `input.dxf` | Input geometry | Immutable |
| `plan.json` | CAM plan | Immutable |
| `manifest.json` | Run manifest | Immutable |
| `output.nc` | G-code output | Immutable |
| `feasibility.json` | Feasibility report | Immutable |
| `override.json` | Override record | Separate index |

**Key Invariant** (from docstring):
> "This does NOT mutate feasibility or the run artifact; it only records operator intent in a separate index."

**Governance Pattern**: Overrides are recorded **separately from immutable run artifacts**. This preserves audit trail while allowing operational flexibility.

---

## 8. Serialization Boundary Enforcement

### 8.1 Safety Assertions

**Source**: `app/cam/export_lifecycle_orchestrator.py` (docstring)

```
Safety assertions:
  - machine_output_generated: always false
  - translator_output_generated: always false
  - machine_ready: always false
```

**Source**: `app/cam/translator_execution_quarantine.py:25`

```
  - serializer_invocation_allowed: always false
```

**Governance Pattern**: Multiple modules declare **explicit safety assertions** that block machine output generation. These assertions are model-validated at construction time.

---

### 8.2 DXF Translator Boundary

**Source**: `app/cam/dxf_translator_boundary.py:12-15`

```
Core rule:
  - DXF is a translator TARGET, not the manufacturing representation
  - Export Object owns manufacturing intent
  - DXF translator owns serialization adaptation
  - No DXF generation in this module
```

**Governance Pattern**: DXF is explicitly designated as **translator target**, not manufacturing representation. Manufacturing intent stays in Export Object; DXF is just one possible serialization.

---

## 9. Registered Translator Inventory

### 9.1 Current Registry

**Source**: `app/cam/translator_capability_registry.py:213-314`

| Translator ID | Execution State | Maturity | Output |
|---------------|-----------------|----------|--------|
| `dxf_r12` | validation_only | candidate | DXF R12 |
| `dxf_r2000` | validation_only | candidate | DXF R2000 |
| `body_outline_dxf_r12` | governed_execution | governed | DXF R12 |
| `body_outline_dxf_r2000` | governed_execution | governed | DXF R2000 |
| `gcode_grbl_placeholder` | execution_disabled | placeholder | G-code |

**Key Observations**:
1. Only 2 translators have `governed_execution` state
2. G-code translator is `execution_disabled` (placeholder only)
3. All translators have `machine_output_supported=False`

---

## 10. Semantic Collision Analysis

### 10.1 COLL-E001: Serialization Term Overload

| Field | Value |
|-------|-------|
| collision_id | COLL-E001 |
| collision_type | overload |
| risk_level | Medium |
| do_not_fix_in_c1 | true |

**Terms:**
- `serialization` (7M registered term)
- `serializer_invocation` (execution quarantine)
- `SERIALIZATION` (TranslatorCategory enum)

**Collision Description:**
"Serialization" used in multiple semantic contexts:
1. 7M: Canonical ontology term with prohibited reinterpretations
2. Execution quarantine: Operation that is explicitly blocked
3. Translator capability: Category classification

**C2 Candidate:**
Clarify whether `SERIALIZATION` category implies `serialization` 7M term semantics.

---

### 10.2 COLL-E002: IBG Authority Propagation Risk

| Field | Value |
|-------|-------|
| collision_id | COLL-E002 |
| collision_type | authority_overlap |
| risk_level | High |
| do_not_fix_in_c1 | true |

**Terms:**
- IBGMorphologyExtension (Export Object extension)
- IBG morphology vocabulary (sandbox/unratified)

**Collision Description:**
IBG morphology data (radii_by_zone, side_heights_mm, dimensions) propagates through Export Object into translator output. If downstream systems treat this as authoritative geometry rather than advisory morphology, sandbox semantics leak into production artifacts.

**C2 Candidate:**
Add explicit `advisory_only: true` flag to IBGMorphologyExtension or document consumption constraints.

---

### 10.3 COLL-E003: Gate Vocabulary Unification

| Field | Value |
|-------|-------|
| collision_id | COLL-E003 |
| collision_type | synonym |
| risk_level | Low |
| do_not_fix_in_c1 | true |

**Terms:**
- `gate_status` (Export Object validation)
- `risk_level` (RMOS feasibility)
- `gate` (translator compatibility report)

**Collision Description:**
Three related gate vocabularies use similar semantics (green/yellow/red) with slightly different field names. Inconsistent but functionally equivalent.

**C2 Candidate:**
Document as intentional parallel vocabularies or unify to single `Gate` type.

---

### 10.4 COLL-E004: RuntimeSupport vs ExecutionState

| Field | Value |
|-------|-------|
| collision_id | COLL-E004 |
| collision_type | overload |
| risk_level | Medium |
| do_not_fix_in_c1 | true |

**Terms:**
- `RuntimeSupport` (CAD semantics: SUPPORTED, SEMANTIC_ONLY, UNSUPPORTED)
- `ExecutionState` (Translator capability: validation_only, governed_execution, etc.)

**Collision Description:**
Two different enums describe "can this thing run" with different granularity:
- RuntimeSupport: 3-state (SUPPORTED, SEMANTIC_ONLY, UNSUPPORTED)
- ExecutionState: 5-state with lifecycle semantics

**C2 Candidate:**
Document relationship between these classifications.

---

## 11. Export Lifecycle Semantics

### 11.1 Lifecycle Flow

```
BOE Approved Geometry
        ↓
  BodyExportObject (geometry authority)
        ↓
  Validation Gate (green/yellow/red)
        ↓
  Translator Selection (capability registry)
        ↓
  Translation (deterministic, stateless)
        ↓
  Serialized Artifact (DXF/SVG/etc.)
```

### 11.2 Authority Boundaries

| Stage | Authority | Mutability |
|-------|-----------|------------|
| BOE Export | Geometry (authoritative) | Immutable after approval |
| Export Object | Manufacturing intent | Immutable |
| Translator | Serialization adaptation | Stateless |
| Output Artifact | Serialized representation | Deterministic |

---

## 12. Summary Statistics

### Vocabulary Counts

| Category | Count |
|----------|-------|
| Export types | 3 |
| Translator maturity levels | 4 |
| Execution states | 5 |
| Translator categories | 5 |
| Runtime support levels | 3 |
| Body categories | 7 |
| Registered translators | 5 |

### Governance Pattern Observations

| Pattern | Evidence | Significance |
|---------|----------|--------------|
| Explicit safety assertions | machine_output_supported=False | Blocks machine output generation |
| Gate enforcement | Red gate blocks translation | Prevents invalid geometry export |
| Provenance embedding | TranslatorProvenance in output | Preserves lineage |
| Authority boundary declaration | CAD semantics authority model | Prevents semantic override |
| Immutable run artifacts | RMOS override in separate index | Preserves audit trail |
| SEMANTIC_ONLY classification | Most acoustic body categories | Prevents premature hardening |

---

## 13. Key Invariants

### From Export Object
- "This is NOT machine output. No G-code. No executable."

### From Translator Protocol
- "Translators consume semantics, they do not create semantics."
- "Output is deterministic given the same input."

### From CAD Semantics
- "CAD semantics may EXTEND approved geometry context. They may NOT override, reinterpret, or invent approved geometry."

### From Execution Quarantine
- "serializer_invocation_allowed: always false"
- "machine_output_supported: always false"

---

## 14. C1 Assessment

### Healthy Governance Patterns

The Export/Serialization domain demonstrates **disciplined constitutional enforcement**:

1. **Explicit authority boundaries** — BOE owns geometry, translators own serialization
2. **Gate enforcement** — Invalid geometry cannot propagate
3. **Safety assertions** — Machine output explicitly blocked
4. **Provenance preservation** — Lineage tracked through pipeline
5. **SEMANTIC_ONLY classification** — Future features don't drive premature runtime

### Risk Areas Requiring C2 Attention

1. **IBG morphology propagation** — Advisory data may be consumed as authoritative
2. **Serialization vocabulary overload** — Term used in multiple semantic contexts
3. **RuntimeSupport vs ExecutionState** — Overlapping lifecycle vocabulary
4. **Translator topology vs MRP topology** — Semantic divergence (see COLL-G001)

---

## 15. Cross-Reference

This inventory should be read alongside:
- `C1_GEOMETRY_TOPOLOGY_SEMANTIC_INVENTORY.md` — Geometry/Morphology/Topology (upstream)
- `IBG_SANDBOX_SEMANTIC_CLASSIFICATION.md` — IBG constitutional containment
- `C1_ACOUSTICS_OBSERVATIONAL_SEMANTIC_INVENTORY.md` — Acoustics reference patterns

---

## C1 Rule Observed

> C1 makes semantic collisions visible. C1 does not make semantic decisions.

No changes were made. This inventory is evidence for C2 reconciliation.

The Export/Serialization domain demonstrates **healthy constitutional enforcement** preventing serialization-driven ontology hardening.
