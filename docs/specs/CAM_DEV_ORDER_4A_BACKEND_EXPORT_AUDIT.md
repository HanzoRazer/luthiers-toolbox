# CAM Dev Order 4A — Backend Export Audit / Machine-Readiness Plan

**Status:** SUPERSEDED  
**Date:** 2026-05-07  
**Note:** This document was an early draft focused on adapter implementation.  
**Superseded by:** The actual Dev Order 4A deliverables (governance/audit documents):
- `docs/architecture/CAM_COORDINATE_SYSTEM_GOVERNANCE.md`
- `docs/architecture/CAM_POSTPROCESSOR_BOUNDARY.md`
- `docs/architecture/CAM_MACHINE_READINESS_PLAN.md`
- `docs/architecture/CAM_TOOLING_AND_STOCK_MODEL.md`
- `docs/architecture/CAM_EXPORT_GOVERNANCE_POLICY.md`
- `docs/handoffs/CAM_MODULE_CLASSIFICATION_2026-05-07.md`

---

## Original Content (for reference only)

---

## 1. Why This Dev Order Exists

NECK-A defines `NeckCAMReferences` block with nut slot CAM output, but the spec left several adapter questions unanswered:

1. **String count derivation** — `nutClearancesMm[]` array length vs explicit `num_strings` field
2. **String X positions** — Calculate from nut width or leave null for CAM to compute
3. **Slot depth source** — Conservative default vs explicit field from workflow
4. **Button enable gate** — Check `nutWorkflowResult !== null` alone or also gate on `overall_gate !== 'red'`

These questions must be answered before the adapter can be implemented, or the CAM backend will receive ambiguous input and produce incorrect toolpaths.

Additionally, the E2E pipeline audit (2026-05-06) found:
- 3 P0 silent failures in CAM flows
- 4 P1 partial flows without ToolpathPlayer integration
- 7 orphan backend endpoints with no frontend UI

This dev order audits the NECK-A CAM integration path specifically and establishes machine-readiness validation gates.

---

## 2. Decisions Required

### 2.1 String Count Derivation

**Question:** Derive `num_strings` from `nutClearancesMm.length` or require explicit field?

**Options:**
| Option | Pros | Cons |
|--------|------|------|
| A. Derive from array length | No redundant data, array is authoritative | Silent error if array is malformed |
| B. Explicit field, validate match | Clear contract, validation catches mismatches | Redundant data, sync risk |

**Recommendation:** Option A — derive from `nutClearancesMm.length`.

**Rationale:** The clearances array IS the per-string data. An explicit count creates sync risk. Add validation that array length ∈ {4, 5, 6, 7, 8, 12} (valid string counts) with explicit error message if invalid.

```typescript
function deriveStringCount(nutClearancesMm: number[]): number {
  const validCounts = [4, 5, 6, 7, 8, 12];
  const count = nutClearancesMm.length;
  if (!validCounts.includes(count)) {
    throw new Error(
      `Invalid string count ${count}. Expected one of: ${validCounts.join(', ')}`
    );
  }
  return count;
}
```

---

### 2.2 String X Positions

**Question:** Adapter calculates positions or passes null for CAM backend to compute?

**Options:**
| Option | Pros | Cons |
|--------|------|------|
| A. Pass null — CAM calculates | Single source of truth in backend | Backend needs nut_width_mm and edge_offset |
| B. Calculate in adapter | Frontend has immediate preview | Duplicated logic, sync risk |
| C. Hybrid — adapter calculates default, CAM accepts override | Flexible, preview works | More complex contract |

**Recommendation:** Option B — calculate in adapter using standard formula.

**Rationale:** The nut workflow already has `nut_width_mm`. Calculating positions in the adapter:
1. Enables immediate preview in frontend before backend call
2. Matches existing FretboardEcosphere pattern (frontend computes, backend validates)
3. Uses standard edge offset (3.5mm typical, configurable per instrument)

**Formula:**
```typescript
function calculateStringPositions(
  nutWidthMm: number,
  stringCount: number,
  edgeOffsetMm: number = 3.5
): number[] {
  const usableWidth = nutWidthMm - (2 * edgeOffsetMm);
  const spacing = usableWidth / (stringCount - 1);
  return Array.from(
    { length: stringCount },
    (_, i) => edgeOffsetMm + (i * spacing)
  );
}
```

**Edge offset sources:**
| Instrument Type | Typical Edge Offset |
|-----------------|---------------------|
| Electric 6-string | 3.0-3.5mm |
| Acoustic 6-string | 3.5-4.0mm |
| Classical | 4.0-4.5mm |
| Bass 4-string | 4.5-5.0mm |
| 12-string | 3.0mm (doubled courses) |

---

### 2.3 Slot Depth Source

**Question:** Where does slot depth come from?

**Background:** The nut workflow evaluates clearances (string height above fret), not slot depths directly. Slot depth is derived from:
- String gauge (larger strings need deeper slots)
- Nut blank thickness (constraint on max depth)
- Clearance target (the workflow's output)

**Options:**
| Option | Source | Notes |
|--------|--------|-------|
| A. Conservative default | 1.5mm all strings | Safe but suboptimal |
| B. Gauge-based formula | depth = gauge_mm × 0.5 | Varies by string |
| C. Clearance-based derivation | depth = nut_height - clearance - (string_gauge/2) | Requires nut height input |
| D. Explicit user input | User enters per-string depths | Most control, more friction |

**Recommendation:** Option C — derive from clearance workflow output.

**Rationale:** The clearance workflow already solved for optimal clearance. Slot depth is:

```
slot_depth_mm = nut_blank_thickness_mm - target_clearance_mm - (string_gauge_mm / 2)
```

Where:
- `nut_blank_thickness_mm` = typical 6mm, from NeckGeometry.nut_thickness_mm
- `target_clearance_mm` = from nutClearancesMm[i] (the workflow output)
- `string_gauge_mm` = from NeckPhysics.string_gauges_inches[i] × 25.4

**Validation gate:** If computed depth > nut_thickness × 0.7, raise warning — slot too deep, risk of breakage.

---

### 2.4 Button Enable Condition

**Question:** Enable "Generate Nut Slot CAM" button when?

**Options:**
| Option | Condition | Risk |
|--------|-----------|------|
| A. `nutWorkflowResult !== null` | Any workflow result | User generates CAM from RED gate result |
| B. `!== null && overall_gate !== 'red'` | GREEN or YELLOW only | Blocks legitimate edge cases |
| C. `!== null`, button warns if RED | Always enabled, modal confirms | User friction, but informed choice |

**Recommendation:** Option C — always enabled if workflow complete, with confirmation modal on RED.

**Rationale:** 
- Users may have legitimate reasons to generate CAM from RED results (prototyping, experimentation)
- Blocking creates frustration; warning creates informed consent
- Matches pattern used in DxfToGcodeView risk badge

**Implementation:**
```typescript
const canGenerateCam = computed(() => nutWorkflowResult.value !== null);

const generateCam = async () => {
  if (nutWorkflowResult.value?.overall_gate === 'RED') {
    const confirmed = await confirm({
      title: 'Setup Issues Detected',
      message: 'The nut workflow identified RED gate issues. Generated toolpaths may produce an unplayable instrument. Continue anyway?',
      confirmText: 'Generate Anyway',
      cancelText: 'Review Issues',
    });
    if (!confirmed) return;
  }
  await generateNutSlotToolpath();
};
```

---

## 3. Machine-Readiness Validation

Before G-code generation, the CAM backend must validate machine capability.

### 3.1 Required Validations

| Check | Condition | Gate |
|-------|-----------|------|
| Tool diameter | tool_diameter_mm < min(slot_width_mm) | RED if fails |
| Z travel | max(slot_depth_mm) < machine.z_travel_mm | RED if fails |
| Workpiece envelope | nut_width_mm < machine.x_envelope_mm | RED if fails |
| Spindle RPM | recommended_rpm ∈ machine.rpm_range | YELLOW if outside |
| Feed rate | feed_rate_mm_min ≤ machine.max_feed | YELLOW if exceeds |
| Tool length | tool_length_mm > max(slot_depth_mm) + clearance | RED if fails |

### 3.2 Machine Spec Interface

```typescript
interface MachineSpec {
  id: string;
  name: string;
  // Envelope
  x_envelope_mm: number;
  y_envelope_mm: number;
  z_travel_mm: number;
  // Spindle
  spindle_rpm_min: number;
  spindle_rpm_max: number;
  // Feed
  max_feed_mm_min: number;
  // Dialect
  gcode_dialect: 'grbl' | 'linuxcnc' | 'mach3' | 'fanuc';
}
```

### 3.3 Validation Endpoint

```
POST /api/cam/nut-slots/validate
Request: { nutSlotParams, machineId }
Response: {
  valid: boolean,
  gates: ValidationGate[],
  overall_gate: 'GREEN' | 'YELLOW' | 'RED',
  blocking_issues: string[],
  warnings: string[]
}
```

---

## 4. Adapter Implementation Spec

### 4.1 Input: NECK-A State

```typescript
interface NutWorkflowState {
  nutClearancesMm: number[];           // per-string clearances
  nutWidthMm: number;                  // from NeckGeometry
  nutThicknessMm: number;              // from NeckGeometry (blank thickness)
  stringGaugesInches: number[];        // from NeckPhysics
  overallGate: 'GREEN' | 'YELLOW' | 'RED';
}
```

### 4.2 Output: CAM Request

```typescript
interface NutSlotCamRequest {
  // Derived from workflow
  num_strings: number;                 // derived from nutClearancesMm.length
  string_positions_x_mm: number[];     // calculated from nutWidthMm + edge_offset
  slot_depths_mm: number[];            // derived from clearances + gauges
  slot_widths_mm: number[];            // string_gauge_mm + 0.2mm clearance
  
  // From geometry
  nut_width_mm: number;
  nut_thickness_mm: number;
  
  // Tooling (from machine context or user input)
  tool_diameter_mm: number;
  tool_type: 'ball' | 'flat' | 'v_bit';
  
  // Feeds and speeds
  feed_rate_mm_min: number;
  plunge_rate_mm_min: number;
  spindle_rpm: number;
  
  // Safety
  safe_z_mm: number;
  clearance_z_mm: number;
}
```

### 4.3 Adapter Function

```typescript
function adaptNutWorkflowToCamRequest(
  state: NutWorkflowState,
  tooling: ToolingParams,
  edgeOffsetMm: number = 3.5
): NutSlotCamRequest {
  const numStrings = deriveStringCount(state.nutClearancesMm);
  const stringPositions = calculateStringPositions(
    state.nutWidthMm, numStrings, edgeOffsetMm
  );
  
  const slotDepths = state.nutClearancesMm.map((clearance, i) => {
    const gaugeInches = state.stringGaugesInches[i];
    const gaugeMm = gaugeInches * 25.4;
    const depth = state.nutThicknessMm - clearance - (gaugeMm / 2);
    return Math.max(0.5, Math.min(depth, state.nutThicknessMm * 0.7));
  });
  
  const slotWidths = state.stringGaugesInches.map(gauge => {
    const gaugeMm = gauge * 25.4;
    return gaugeMm + 0.2; // 0.2mm clearance for string movement
  });
  
  return {
    num_strings: numStrings,
    string_positions_x_mm: stringPositions,
    slot_depths_mm: slotDepths,
    slot_widths_mm: slotWidths,
    nut_width_mm: state.nutWidthMm,
    nut_thickness_mm: state.nutThicknessMm,
    ...tooling,
  };
}
```

---

## 5. Backend Endpoints Required

### 5.1 New Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/cam/nut-slots/validate` | POST | Machine-readiness validation | NEW |
| `/api/cam/nut-slots/preview` | POST | Toolpath preview JSON | NEW |
| `/api/cam/nut-slots/gcode` | POST | G-code generation | NEW |

### 5.2 Endpoint Contracts

**POST /api/cam/nut-slots/preview**
```python
class NutSlotPreviewRequest(BaseModel):
    num_strings: int
    string_positions_x_mm: List[float]
    slot_depths_mm: List[float]
    slot_widths_mm: List[float]
    nut_width_mm: float
    nut_thickness_mm: float
    tool_diameter_mm: float

class NutSlotPreviewResponse(BaseModel):
    toolpath: ToolpathJSON
    estimated_time_sec: float
    total_travel_mm: float
    warnings: List[str]
```

**POST /api/cam/nut-slots/gcode**
```python
class NutSlotGcodeRequest(NutSlotPreviewRequest):
    tool_type: Literal['ball', 'flat', 'v_bit']
    feed_rate_mm_min: float
    plunge_rate_mm_min: float
    spindle_rpm: int
    safe_z_mm: float = 5.0
    clearance_z_mm: float = 2.0
    gcode_dialect: Literal['grbl', 'linuxcnc', 'mach3'] = 'grbl'

class NutSlotGcodeResponse(BaseModel):
    gcode: str
    line_count: int
    estimated_time_sec: float
    validation_gates: List[ValidationGate]
```

---

## 6. Existing Backend Audit

Per E2E pipeline audit (2026-05-06), check which nut-related code exists:

### 6.1 Search Targets

```bash
# Find existing nut slot code
grep -rn "nut.slot\|nut_slot\|nutslot" services/api/app

# Find string spacing code
grep -rn "string.spacing\|string_spacing\|string.position" services/api/app

# Find existing CAM endpoints for similar operations
grep -rn "@router.post.*fret\|@router.post.*slot" services/api/app
```

### 6.2 Reusable Components

| Component | Location | Reusable For |
|-----------|----------|--------------|
| Toolpath generation | `util/gcode/simulator.py` | Toolpath preview |
| G-code emission | `cam/gcode_emitter.py` | G-code output |
| Machine specs | `cam/machines.py` | Validation |
| Fret slot CAM | `cam/routers/fret_slots_router.py` | Pattern for nut slots |

---

## 7. Implementation Order

### Phase 1: Adapter + Validation (2-3h)

1. Implement `adaptNutWorkflowToCamRequest()` in new file:
   `packages/client/src/composables/useNutSlotCamAdapter.ts`

2. Add validation functions:
   - `deriveStringCount()`
   - `calculateStringPositions()`
   - `calculateSlotDepths()`
   - `validateSlotDepths()` (warn if > 70% of nut thickness)

3. Add button enable logic + RED gate confirmation modal

**Acceptance:**
```
□ Adapter converts NECK-A state to CAM request
□ String count validation rejects invalid lengths
□ String positions calculated from nut width
□ Slot depths derived from clearances + gauges
□ RED gate shows confirmation modal
□ GREEN/YELLOW gates proceed without modal
```

### Phase 2: Backend Preview Endpoint (1-2h)

1. Create `services/api/app/cam/routers/nut_slots_router.py`

2. Implement `POST /api/cam/nut-slots/preview`:
   - Accept NutSlotPreviewRequest
   - Generate toolpath JSON
   - Return estimated time + travel

3. Wire to router manifest

**Acceptance:**
```
□ Endpoint accepts valid request
□ Returns toolpath in ToolpathJSON format
□ Rejects request with invalid string count
□ Rejects request with slot depth > nut thickness
□ Smoke tests pass
```

### Phase 3: G-code Generation (1-2h)

1. Implement `POST /api/cam/nut-slots/gcode`:
   - Accept NutSlotGcodeRequest
   - Run machine-readiness validation
   - Generate dialect-specific G-code
   - Return with validation gates

2. Add machine validation endpoint if needed

**Acceptance:**
```
□ G-code generated for GRBL dialect
□ Machine validation runs before generation
□ RED validation blocks G-code output
□ YELLOW validation returns with warnings
□ G-code includes header comment with parameters
```

---

## 8. Files to Create/Modify

### New Files

```
packages/client/src/composables/useNutSlotCamAdapter.ts     (adapter)
services/api/app/cam/routers/nut_slots_router.py            (endpoints)
services/api/app/cam/nut_slot_generator.py                  (toolpath logic)
services/api/tests/cam/test_nut_slots.py                    (tests)
```

### Modified Files

```
packages/client/src/stores/instrumentGeometryStore.ts       (add CAM action)
packages/client/src/components/cam/NutSlotCAMPanel.vue      (new component)
services/api/app/router_registry/cam_manifest.py            (register router)
```

---

## 9. Test Cases

### Adapter Tests

```typescript
describe('useNutSlotCamAdapter', () => {
  it('derives string count from clearances array', () => {
    const state = mockNutWorkflowState({ nutClearancesMm: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3] });
    const request = adaptNutWorkflowToCamRequest(state, mockTooling());
    expect(request.num_strings).toBe(6);
  });

  it('rejects invalid string counts', () => {
    const state = mockNutWorkflowState({ nutClearancesMm: [0.3, 0.3, 0.3] }); // 3 is invalid
    expect(() => adaptNutWorkflowToCamRequest(state, mockTooling()))
      .toThrow('Invalid string count');
  });

  it('calculates string positions from nut width', () => {
    const state = mockNutWorkflowState({ nutWidthMm: 43, nutClearancesMm: new Array(6).fill(0.3) });
    const request = adaptNutWorkflowToCamRequest(state, mockTooling(), 3.5);
    expect(request.string_positions_x_mm[0]).toBeCloseTo(3.5);
    expect(request.string_positions_x_mm[5]).toBeCloseTo(39.5);
  });

  it('derives slot depths from clearances and gauges', () => {
    const state = mockNutWorkflowState({
      nutClearancesMm: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
      nutThicknessMm: 6.0,
      stringGaugesInches: [0.010, 0.013, 0.017, 0.026, 0.036, 0.046],
    });
    const request = adaptNutWorkflowToCamRequest(state, mockTooling());
    // depth = 6.0 - 0.3 - (gauge_mm / 2)
    // For 0.046" = 1.17mm → depth = 6.0 - 0.3 - 0.58 = 5.12mm
    expect(request.slot_depths_mm[5]).toBeCloseTo(5.12, 1);
  });

  it('clamps slot depth to 70% of nut thickness', () => {
    const state = mockNutWorkflowState({
      nutClearancesMm: [0.1, 0.1, 0.1, 0.1, 0.1, 0.1], // very low clearance
      nutThicknessMm: 6.0,
      stringGaugesInches: [0.010, 0.013, 0.017, 0.026, 0.036, 0.046],
    });
    const request = adaptNutWorkflowToCamRequest(state, mockTooling());
    expect(request.slot_depths_mm.every(d => d <= 4.2)).toBe(true); // 70% of 6mm
  });
});
```

### Backend Tests

```python
class TestNutSlotPreview:
    def test_valid_6_string_request(self, client):
        response = client.post('/api/cam/nut-slots/preview', json={
            'num_strings': 6,
            'string_positions_x_mm': [3.5, 10.7, 17.9, 25.1, 32.3, 39.5],
            'slot_depths_mm': [1.5, 1.6, 1.7, 2.0, 2.3, 2.5],
            'slot_widths_mm': [0.45, 0.53, 0.63, 0.86, 1.11, 1.37],
            'nut_width_mm': 43.0,
            'nut_thickness_mm': 6.0,
            'tool_diameter_mm': 0.4,
        })
        assert response.status_code == 200
        data = response.json()
        assert 'toolpath' in data
        assert data['toolpath']['version'] == '1.0'

    def test_rejects_slot_depth_exceeding_nut(self, client):
        response = client.post('/api/cam/nut-slots/preview', json={
            'num_strings': 6,
            'string_positions_x_mm': [3.5, 10.7, 17.9, 25.1, 32.3, 39.5],
            'slot_depths_mm': [7.0, 7.0, 7.0, 7.0, 7.0, 7.0],  # > nut_thickness
            'slot_widths_mm': [0.45, 0.53, 0.63, 0.86, 1.11, 1.37],
            'nut_width_mm': 43.0,
            'nut_thickness_mm': 6.0,
            'tool_diameter_mm': 0.4,
        })
        assert response.status_code == 422

    def test_rejects_tool_larger_than_slot(self, client):
        response = client.post('/api/cam/nut-slots/preview', json={
            'num_strings': 6,
            'string_positions_x_mm': [3.5, 10.7, 17.9, 25.1, 32.3, 39.5],
            'slot_depths_mm': [1.5, 1.6, 1.7, 2.0, 2.3, 2.5],
            'slot_widths_mm': [0.45, 0.53, 0.63, 0.86, 1.11, 1.37],
            'nut_width_mm': 43.0,
            'nut_thickness_mm': 6.0,
            'tool_diameter_mm': 1.5,  # > smallest slot (0.45mm)
        })
        assert response.status_code == 422
```

---

## 10. Verification Commands

```bash
# Verify adapter tests pass
cd packages/client
npm run test -- --grep "useNutSlotCamAdapter"

# Verify backend tests pass
cd services/api
pytest tests/cam/test_nut_slots.py -v

# Verify endpoint registration
grep -n "nut_slots" app/router_registry/cam_manifest.py

# Verify no duplicate nut slot code
grep -rn "def.*nut.*slot" app --include="*.py" | wc -l
# Should be exactly 3 (preview, gcode, validate)
```

---

## 11. What This Dev Order Does NOT Do

```
- Does NOT modify existing fret slot CAM code
- Does NOT touch DXF export (toolpath JSON only in v1)
- Does NOT implement undo/redo for nut workflow
- Does NOT add new fields to NeckEcosphere schema
- Does NOT modify instrumentGeometryStore beyond adding CAM action
- Does NOT implement G-code dialects beyond GRBL (v1)
- Does NOT add RMOS artifact tracking (deferred to v2)
```

---

## 12. Answers to Initial Questions

| Question | Answer | Rationale |
|----------|--------|-----------|
| String count source | Derive from `nutClearancesMm.length` | Array is authoritative; add validation |
| String X positions | Calculate in adapter | Enables preview; standard formula |
| Slot depth source | Derive from clearance + gauge | Workflow output drives depth calculation |
| Button enable | `!== null` + RED confirmation modal | Informed consent over blocking |

---

*End of CAM Dev Order 4A*
