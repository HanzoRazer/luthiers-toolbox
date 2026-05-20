# CAM Dev Order 7S Handoff: Governed Manufacturing Cognition Layer

**Date:** 2026-05-20
**Status:** Complete
**Dependencies:** 7R (lifecycle audit lineage)

---

## Executive Summary

Dev Order 7S implements a governed manufacturing cognition layer that delivers external CAM lessons from OpenBuilds-CAM review as repo-native, non-executable infrastructure. It provides:

- **Operation Modality Vocabulary** — 14 seeded modalities (router, laser, plasma, luthier strategies)
- **Machine Envelope Validation** — Pre-export bounds checking with GREEN/YELLOW/RED gates
- **Manufacturing Strategy Artifacts** — Heuristic hints for luthier operation families
- **Workspace Artifacts** — Local-first, serializable workspace model (inspired by .obc)
- **Golden Fixture Registry** — 6 seeded fixtures with clearance zone definitions
- **Cognition Task Model** — Worker-ready task interface (workers not implemented)
- **CAM Assist Router** — HTTP endpoints for all cognition artifacts

**Critical Principle:** CAM Assist generates manufacturing intelligence. CAM Assist does not become a CAM engine or machine controller.

---

## 7S Invariants (Model-Enforced)

All Pydantic models enforce these invariants via `@model_validator`:

```python
execution_authorized = False      # 7S does NOT authorize execution
machine_output_allowed = False    # 7S does NOT allow machine output
generates_gcode = False           # 7S does NOT generate G-code
executable_modality = False       # Modalities are cognition only
executable_payload_present = False # Workspaces contain no executables
generates_motion = False          # Fixtures do not generate motion
```

Attempting to set any of these to `True` raises `ValueError`.

---

## Deliverables

### 1. `cam_operation_modality.py`

**Location:** `services/api/app/cam/cam_operation_modality.py`

**Models:**
- `CAMOperationModality` — Operation modality vocabulary entry

**Seeded Modalities (14):**
| ID | Display Name | Cutter Family | Luthier-Specific |
|----|--------------|---------------|------------------|
| router_profile | Router Profile | router | No |
| router_pocket | Router Pocket | router | No |
| laser_vector | Laser Vector | laser | No |
| laser_raster | Laser Raster | laser | No |
| plasma_profile | Plasma Profile | plasma | No |
| drag_knife_profile | Drag Knife Profile | drag_knife | No |
| pen_plotter_profile | Pen Plotter | pen_plotter | No |
| luthier_rosette_strategy | Rosette Strategy | luthier_strategy | Yes |
| luthier_binding_channel_strategy | Binding Channel Strategy | luthier_strategy | Yes |
| luthier_neck_profile_strategy | Neck Profile Strategy | luthier_strategy | Yes |
| luthier_fret_slotting_strategy | Fret Slotting Strategy | luthier_strategy | Yes |
| luthier_fixture_setup | Fixture Setup | fixture_setup | Yes |
| inspection_pass | Inspection Pass | inspection | No |

**Key Functions:**
```python
get_operation_modality(modality_id: str) -> Optional[CAMOperationModality]
list_operation_modalities() -> List[CAMOperationModality]
list_modalities_by_cutter_family(family: CutterFamily) -> List[...]
list_luthier_modalities() -> List[CAMOperationModality]
classify_modality_for_operation(operation_name: str) -> Optional[str]
get_safety_warnings_for_modality(modality_id: str) -> List[str]
```

### 2. `cam_envelope_validation.py`

**Location:** `services/api/app/cam/cam_envelope_validation.py`

**Models:**
- `CAMBounds2D` — 2D/3D bounding box
- `CAMMachineEnvelope` — Machine working area definition
- `CAMEnvelopeValidationEvaluation` — Validation result with gate

**Seeded Machine Envelopes (5):**
| ID | Display Name | X/Y/Z (mm) |
|----|--------------|------------|
| generic_3018 | Generic 3018 CNC | 300×180×45 |
| generic_6040 | Generic 6040 CNC | 600×400×75 |
| luthier_body_router | Luthier Body Router | 700×500×100 |
| luthier_neck_router | Luthier Neck Router | 800×200×80 |
| laser_k40 | K40 Laser | 300×200×— |

**Gate Logic:**
- **RED** — Bounds exceed envelope limits
- **YELLOW** — Bounds within margin zone (near edges)
- **GREEN** — Bounds safely within envelope

**Key Functions:**
```python
evaluate_bounds_against_envelope(bounds, envelope, subject_id) -> CAMEnvelopeValidationEvaluation
get_machine_envelope(machine_id: str) -> Optional[CAMMachineEnvelope]
register_machine_envelope(envelope: CAMMachineEnvelope) -> None
extract_bounds_from_dict(data: Dict) -> Optional[CAMBounds2D]
```

### 3. `luthier_manufacturing_strategy.py`

**Location:** `services/api/app/cam/luthier_manufacturing_strategy.py`

**Models:**
- `StrategyFamilyHint` — Hints for operation families
- `LuthierManufacturingStrategy` — Manufacturing strategy artifact

**Strategy Families with Hints (11):**
rosette, binding_channel, neck_profile, fret_slotting, bridge_location, body_outline, fixture_setup, inspection, soundhole, headstock, bracing

**Review Status Lifecycle:**
`draft` → `pending_review` → `approved_for_export_review` → (ready for export lifecycle)

**Key Functions:**
```python
create_manufacturing_strategy(operation_family, title, ...) -> LuthierManufacturingStrategy
get_family_hints(family: OperationFamily) -> Optional[StrategyFamilyHint]
update_strategy_review_status(strategy_id, review_status, review_notes) -> ...
```

### 4. `luthier_operation_workspace.py`

**Location:** `services/api/app/cam/luthier_operation_workspace.py`

**Models:**
- `GeometryReference` — Reference to geometry (not actual geometry data)
- `WorkspaceValidationResult` — Completeness validation result
- `LuthierOperationWorkspaceV1` — Serializable workspace artifact

**Workspace Lifecycle:**
`draft` → `geometry_bound` → `strategy_attached` → `validated` → `export_ready` → `archived`

**Serialization Pattern:**
Inspired by OpenBuilds `.obc` files. Workspaces serialize to JSON for local storage.

**Key Functions:**
```python
create_workspace(title, operation_family, ...) -> LuthierOperationWorkspaceV1
add_geometry_reference(workspace_id, reference) -> Optional[...]
attach_strategy(workspace_id, strategy_id) -> Optional[...]
validate_workspace(workspace_id) -> Optional[WorkspaceValidationResult]
promote_to_export_ready(workspace_id) -> Optional[...]
serialize_workspace(workspace_id) -> Optional[str]
deserialize_workspace(json_str: str) -> LuthierOperationWorkspaceV1
```

### 5. `cam_golden_artifact_fixtures.py`

**Location:** `services/api/app/cam/cam_golden_artifact_fixtures.py`

**Models:**
- `ClearanceZone` — Fixture keepout zone definition
- `FixtureCompatibilityHints` — Workpiece compatibility hints
- `CAMGoldenFixture` — Reference fixture configuration

**Seeded Fixtures (6):**
| ID | Type | Luthier-Specific |
|----|------|------------------|
| luthier_body_vacuum | vacuum_table | Yes |
| luthier_neck_side_clamp | side_clamp | Yes |
| luthier_fretboard_tape | double_sided_tape | Yes |
| luthier_rosette_jig | dedicated_jig | Yes |
| generic_corner_clamp | corner_clamp | No |
| generic_t_slot | t_slot + toggle_clamp | No |

**Key Functions:**
```python
find_compatible_fixtures(workpiece_shape, thickness_mm, ...) -> List[CAMGoldenFixture]
evaluate_fixture_clearance(fixture_id, tool_path_points) -> Dict[str, Any]
```

### 6. `cam_cognition_task.py`

**Location:** `services/api/app/cam/cam_cognition_task.py`

**Models:**
- `TaskInput` — Task input payload
- `TaskResult` — Task result (never contains G-code)
- `TaskError` — Error information
- `CAMCognitionTask` — Worker-ready task model

**Task Types:**
strategy_selection, envelope_validation, fixture_recommendation, modality_classification, workspace_validation, clearance_analysis, topology_check, batch_validation

**Task Lifecycle:**
`pending` → `queued` → `running` → `completed`/`failed`/`cancelled`

**Note:** Workers are NOT implemented in 7S. This module defines the interface.

**Key Functions:**
```python
create_cognition_task(task_type, title, input_payload, ...) -> CAMCognitionTask
queue_task(task_id) -> Optional[CAMCognitionTask]
start_task(task_id) -> Optional[CAMCognitionTask]
complete_task(task_id, result) -> Optional[CAMCognitionTask]
```

### 7. `cam_assist_router.py`

**Location:** `services/api/app/routers/cam/cam_assist_router.py`
**Prefix:** `/api/cam/assist`

**Endpoints (40+):**

| Category | Method | Path | Purpose |
|----------|--------|------|---------|
| Meta | GET | `/` | API metadata |
| Modality | GET | `/modalities` | List modalities |
| Modality | GET | `/modalities/{id}` | Get modality |
| Modality | GET | `/modalities/family/{family}` | By cutter family |
| Modality | GET | `/modalities/luthier` | Luthier modalities |
| Modality | POST | `/modalities/classify` | Classify operation |
| Envelope | GET | `/envelopes` | List envelopes |
| Envelope | GET | `/envelopes/{id}` | Get envelope |
| Envelope | POST | `/envelopes` | Register envelope |
| Envelope | POST | `/envelopes/evaluate` | Evaluate bounds |
| Envelope | GET | `/envelopes/evaluations` | List evaluations |
| Strategy | GET | `/strategies` | List strategies |
| Strategy | GET | `/strategies/{id}` | Get strategy |
| Strategy | GET | `/strategies/family/{family}` | By family |
| Strategy | POST | `/strategies` | Create strategy |
| Strategy | PATCH | `/strategies/{id}/review` | Update review |
| Strategy | GET | `/strategy-hints/{family}` | Get hints |
| Workspace | GET | `/workspaces` | List workspaces |
| Workspace | GET | `/workspaces/{id}` | Get workspace |
| Workspace | POST | `/workspaces` | Create workspace |
| Workspace | POST | `/workspaces/{id}/geometry` | Add geometry |
| Workspace | POST | `/workspaces/{id}/strategies/{sid}` | Attach strategy |
| Workspace | POST | `/workspaces/{id}/validate` | Validate |
| Workspace | POST | `/workspaces/{id}/promote` | Promote to export_ready |
| Workspace | POST | `/workspaces/{id}/archive` | Archive |
| Workspace | GET | `/workspaces/{id}/serialize` | Serialize to JSON |
| Fixture | GET | `/fixtures` | List fixtures |
| Fixture | GET | `/fixtures/{id}` | Get fixture |
| Fixture | POST | `/fixtures/compatible` | Find compatible |
| Fixture | POST | `/fixtures/clearance` | Evaluate clearance |
| Task | GET | `/tasks` | List tasks |
| Task | GET | `/tasks/stats` | Get statistics |
| Task | GET | `/tasks/{id}` | Get task |
| Task | POST | `/tasks` | Create task |
| Task | POST | `/tasks/{id}/queue` | Queue task |
| Task | POST | `/tasks/{id}/cancel` | Cancel task |
| Task | POST | `/tasks/{id}/complete` | Complete task |

### 8. Test Suite

**Location:** `tests/cam/test_cam_assist_7s.py`
**Test Count:** 65+ tests

**Test Classes:**
- `TestCAMOperationModality` — 9 tests
- `TestCAMEnvelopeValidation` — 9 tests
- `TestLuthierManufacturingStrategy` — 7 tests
- `TestLuthierOperationWorkspace` — 9 tests
- `TestCAMGoldenFixtures` — 9 tests
- `TestCAMCognitionTask` — 12 tests
- `TestCAMAssistRouter` — 12 tests

---

## What 7S Does NOT Do

- **Does not authorize execution** — `execution_authorized` always False
- **Does not allow machine output** — `machine_output_allowed` always False
- **Does not generate G-code** — `generates_gcode` always False
- **Does not implement workers** — Task model only, no execution
- **Does not invoke serializers** — Pure cognition concern
- **Does not wire envelope validation into lifecycle gates yet** — Deferred to 7T
- **Does not import OpenBuilds code** — Only salvages patterns

---

## Salvaged Patterns from OpenBuilds-CAM

| Pattern | OpenBuilds Concept | 7S Implementation |
|---------|-------------------|-------------------|
| Operation modality | CNC/laser/plasma mode split | `CAMOperationModality` vocabulary |
| Pre-export validation | Missing in OpenBuilds | `CAMEnvelopeValidationEvaluation` |
| Local-first workspace | `.obc` project file | `LuthierOperationWorkspaceV1` |
| Fixture/workholding | Workholding workflow | `CAMGoldenFixture` registry |
| Task queue | Worker queue concept | `CAMCognitionTask` (interface only) |

---

## Integration Points

### Router Registration

Added to `cam_manifest.py`:
```python
RouterSpec(
    module="app.routers.cam.cam_assist_router",
    prefix="",
    tags=["CAM", "Assist", "Cognition"],
    category="cam",
),
```

### Future Integration (7T+)

1. **Lifecycle orchestrator** — Wire envelope validation into export lifecycle
2. **Strategy binding** — Connect strategies to export objects
3. **Worker implementation** — Implement actual task processing
4. **Operation registry** — Add optional `modality_ids` field

---

## Files Created

| File | Purpose |
|------|---------|
| `app/cam/cam_operation_modality.py` | Operation modality vocabulary |
| `app/cam/cam_envelope_validation.py` | Envelope validation |
| `app/cam/luthier_manufacturing_strategy.py` | Strategy artifacts |
| `app/cam/luthier_operation_workspace.py` | Workspace artifacts |
| `app/cam/cam_golden_artifact_fixtures.py` | Golden fixtures |
| `app/cam/cam_cognition_task.py` | Cognition tasks |
| `app/routers/cam/cam_assist_router.py` | HTTP router |
| `tests/cam/test_cam_assist_7s.py` | Test suite |
| `docs/handoffs/CAM_DEV_ORDER_7S_HANDOFF.md` | This handoff |

---

## Verification Commands

```powershell
# Run test suite
cd services/api
$env:PYTHONPATH = "C:\Users\thepr\Downloads\luthiers-toolbox\services\api"
python -m pytest tests/cam/test_cam_assist_7s.py -v

# Verify imports
python -c "from app.cam.cam_operation_modality import list_operation_modalities; print(f'Modalities: {len(list_operation_modalities())}')"
python -c "from app.cam.cam_envelope_validation import list_machine_envelopes; print(f'Envelopes: {len(list_machine_envelopes())}')"
python -c "from app.cam.cam_golden_artifact_fixtures import list_golden_fixtures; print(f'Fixtures: {len(list_golden_fixtures())}')"
```

---

**Handoff Complete: 7S delivers governed manufacturing cognition infrastructure without authorizing execution, generating machine output, or importing external code.**
