# CAM Normalization Audit — 2026-05-09

**Date:** 2026-05-09  
**Auditor:** Claude (CAM Dev Order 5B)  
**Scope:** Pilot candidate modules vs governed preview standards

---

## Executive Summary

4 pilot candidates evaluated against the canonical preview standards defined in 5B.

| Module | Compliance | Primary Gap |
|--------|------------|-------------|
| Fret Slots CAM | 45% | No gate semantics, no coordinate metadata |
| Drilling | 35% | No preview route, no gate semantics |
| Fan Fret CAM | 40% | Inherits fret_slots gaps |
| Rosette | 50% | Preview route fragmented, partial gate support |

**Reference:** `nut_slot_cam.py` is 100% compliant (canonical reference).

---

## Pilot 1: Fret Slots CAM

**Module:** `calculators/fret_slots_cam.py`  
**Router:** `cam/routers/fret_slots_router.py`  
**Route:** `POST /api/cam/fret_slots/preview`

### Current State vs Standard

| Concern | Standard | Current | Gap |
|---------|----------|---------|-----|
| Preview route | `/fret-slot/preview` | `/fret_slots/preview` | Underscore in path |
| Gate field | `gate: "green\|yellow\|red"` | None | Missing |
| Coordinate system | Full object | None | Missing |
| Structured issues | `issues: [CamIssue]` | `messages: [RmosMessageOut]` | Different schema |
| Statistics | Core required fields | Partial | Missing operation_count, move_count |
| Status field | `"preview"` | None | Missing |
| Units field | `"mm"` | None | Missing |

### Current Output Format

```json
{
  "model_id": "...",
  "fret_count": 22,
  "slots": [...],
  "messages": [...],
  "statistics": {...}
}
```

### Standard Output Format

```json
{
  "operation": "fret_slot_preview",
  "status": "preview",
  "gate": "green",
  "units": "mm",
  "coordinate_system": {...},
  "canonical_toolpath": {...},
  "warnings": [],
  "errors": [],
  "issues": [],
  "statistics": {...}
}
```

### Tests Status

- `test_cam_fret_slots_preview_smoke.py` — exists
- `test_cam_fret_slots_export.py` — exists
- `test_fret_slots_cam_guard.py` — exists

### Coordinate Documentation Status

None in response. Module docstring has partial documentation.

### Gate Semantics Status

None. Uses `messages` array with severity but no gate evaluation.

### Minimal Patches Needed

1. Add `gate` field to response with evaluation logic
2. Add `coordinate_system` object to response
3. Add `operation`, `status`, `units` fields
4. Rename route from `fret_slots` to `fret-slot`
5. Map `messages` to `issues` schema or add both

**Estimated effort:** MEDIUM (response shape change)

---

## Pilot 2: Drilling

**Module:** `cam/drilling/peck_cycle.py`  
**Router:** `cam/routers/drilling/drill_pattern_router.py`  
**Route:** `POST /api/cam/drilling/pattern/gcode` (G-code, not preview)

### Current State vs Standard

| Concern | Standard | Current | Gap |
|---------|----------|---------|-----|
| Preview route | `/drilling/preview` | None | No preview route |
| Gate field | Required | None | Missing |
| Coordinate system | Full object | None | Missing |
| Output type | JSON preview | G-code string | Wrong output type |
| Statistics | Standard core | DrillResult fields | Different schema |

### Current Output Format

The `drill_pattern_router.py` returns G-code directly, not JSON preview.

```python
class DrillResult:
    gcode: str
    hole_count: int
    total_depth_mm: float
    estimated_time_seconds: float
    warnings: List[str]
```

### Standard Output Format

Would need new preview route returning:

```json
{
  "operation": "drilling_preview",
  "status": "preview",
  "gate": "green",
  "units": "mm",
  "coordinate_system": {...},
  "canonical_toolpath": {
    "holes": [...]
  },
  "warnings": [],
  "errors": [],
  "statistics": {...}
}
```

### Tests Status

- `test_cam_drilling_smoke.py` — 3 tests for G-code endpoints

### Coordinate Documentation Status

G83 format documented in module docstring but no coordinate system metadata in output.

### Gate Semantics Status

None. Has warnings array but no gate evaluation.

### Minimal Patches Needed

1. Create new `/drilling/preview` endpoint
2. Add gate evaluation logic
3. Add coordinate_system to response
4. Add statistics mapping
5. Keep existing G-code route for GOVERNED EXPORT path

**Estimated effort:** MEDIUM (new endpoint needed)

---

## Pilot 3: Fan Fret CAM

**Module:** `calculators/fret_slots_fan_cam.py`  
**Router:** Uses `fret_slots_router.py` (mode="fan_fret")  
**Route:** `POST /api/cam/fret_slots/preview` with `mode: "fan_fret"`

### Current State vs Standard

| Concern | Standard | Current | Gap |
|---------|----------|---------|-----|
| Preview route | `/fret-slot/preview` | `/fret_slots/preview` | Inherits fret_slots route |
| Gate field | Required | None | Inherits gap |
| Coordinate system | Full object | None | Inherits gap |
| Fan-fret metadata | Operation-specific | Partial | Has perpendicular_fret_index |

### Current Output Format

Same as fret_slots_cam — inherits response schema.

### Tests Status

- `test_fan_fret_perpendicular.py` — multiple tests

### Coordinate Documentation Status

Inherits from fret_slots_cam. No explicit coordinate system.

### Gate Semantics Status

None. Inherits fret_slots_cam behavior.

### Minimal Patches Needed

Same as fret_slots_cam — normalizing the parent module normalizes fan fret.

**Estimated effort:** LOW (piggybacks on fret_slots_cam normalization)

---

## Pilot 4: Rosette

**Module:** `cam/rosette/cnc/cnc_gcode_exporter.py`  
**Router:** Multiple routes in art_studio and rmos  
**Routes:**
- `POST /api/rmos/rosette/preview` (rmos)
- `POST /api/art/rosette/preview` (art_studio)
- `POST /api/cam/rosette/post-gcode` (cam)

### Current State vs Standard

| Concern | Standard | Current | Gap |
|---------|----------|---------|-----|
| Preview route | `/api/cam/rosette/preview` | Fragmented across modules | Multiple routes |
| Gate field | Required | Partial (cnc_safety_validator) | Not in response |
| Coordinate system | Full object | Partial (MachineProfile) | Not standardized |
| Machine profile | "generic_cnc_mm_preview_only" | GRBL/FANUC enum | Too specific for preview |

### Current Output Format

G-code exporter produces G-code, not JSON preview.

Rosette preview routes return various schemas:
- `RosettePreviewOut` in art_studio
- Various schemas in rmos

### Tests Status

- `test_golden_rosette_geometry.py` — geometry tests
- `test_rosette_cam_bridge.py` — bridge tests
- `test_cam_pipeline_rosette_op.py` — pipeline tests

### Coordinate Documentation Status

MachineProfile has some metadata but not full coordinate system.

### Gate Semantics Status

`cnc_safety_validator.py` exists but not integrated into preview response.

### Minimal Patches Needed

1. Consolidate to single `/api/cam/rosette/preview` route
2. Create JSON preview response (separate from G-code)
3. Add gate field from cnc_safety_validator
4. Add coordinate_system object
5. Standardize statistics

**Estimated effort:** HIGH (route consolidation + new schema)

---

## Gap Summary

| Gap Type | Fret Slots | Drilling | Fan Fret | Rosette |
|----------|------------|----------|----------|---------|
| Gate semantics | ✗ | ✗ | ✗ | Partial |
| Coordinate system | ✗ | ✗ | ✗ | Partial |
| Preview route | Partial | ✗ | Partial | Partial |
| Statistics | Partial | Partial | Partial | ✗ |
| Status field | ✗ | ✗ | ✗ | ✗ |
| Units field | ✗ | ✗ | ✗ | ✗ |
| Structured issues | Partial | ✗ | Partial | ✗ |

---

## Normalization Priority

Based on score and gap analysis:

| Priority | Module | Reason |
|----------|--------|--------|
| 1 | Fret Slots CAM | Highest score (75), already has route |
| 2 | Fan Fret CAM | Normalizes with parent |
| 3 | Drilling | Score 72, needs new preview route |
| 4 | Rosette | Complex (many routes), needs consolidation |

---

## Minimal Promotion Patch Strategy

**Principle:** Do minimal normalization patches first. Avoid generator rewrites.

### Patch Type 1: Response Wrapper

Add standard fields to existing response without changing generator logic:

```python
# Wrap existing response with standard fields
return NormalizedPreviewResponse(
    operation="fret_slot_preview",
    status="preview",
    gate=evaluate_gate(result),  # New function
    units="mm",
    coordinate_system=FRET_SLOT_COORDINATE_SYSTEM,  # Constant
    canonical_toolpath={"slots": result.slots},
    warnings=result.warnings,
    errors=result.errors,
    statistics=map_statistics(result),
)
```

### Patch Type 2: Gate Evaluation Function

Add gate evaluation without changing generator:

```python
def evaluate_fret_slot_gate(request, result) -> CamGate:
    if result.errors:
        return CamGate.RED
    if result.warnings:
        return CamGate.YELLOW
    return CamGate.GREEN
```

### Patch Type 3: Coordinate System Constant

Define coordinate system as module constant:

```python
FRET_SLOT_COORDINATE_SYSTEM = CoordinateSystem(
    units="mm",
    origin="nut_edge",
    x_axis="string_to_string",
    y_axis="scale_length",
    z_axis="depth_into_board",
    z_zero="top_of_fretboard",
    handedness="right_handed",
    frame="local_part",
)
```

---

## Implementation Not In 5B

5B defines standards and documents gaps.

Actual normalization patches are deferred to future dev orders:
- 5C: Fret Slots + Fan Fret normalization
- 5D: Drilling normalization
- 5E: Rosette normalization

---

## Cross-Reference

| Document | Relevance |
|----------|-----------|
| `CAM_PREVIEW_CONTRACT_STANDARD.md` | Response shape |
| `CAM_GATE_SEMANTICS_STANDARD.md` | Gate evaluation |
| `CAM_PREVIEW_METADATA_STANDARD.md` | Statistics |
| `CAM_PREVIEW_ROUTE_CONVENTIONS.md` | Route naming |
| `cam_preview_standard_manifest.json` | Machine-readable status |

---

*Audit completed: 2026-05-09*
