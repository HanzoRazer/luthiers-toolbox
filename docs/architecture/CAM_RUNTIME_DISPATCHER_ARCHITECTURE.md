# CAM Runtime Dispatcher Architecture

**Status:** Skeleton Infrastructure  
**Date:** 2026-05-16  
**Dev Orders:** 57, 58

---

## Purpose

The CAM Runtime Dispatcher provides the governed host structure that future runtime plugins will use. It exists to prevent CAM runtime fragmentation.

**The dispatcher consumes intent. It does not redefine intent.**

---

## Design Goal

Future CAM should evolve as:

```
Design Tool
→ Intent Contract
→ Runtime Dispatcher
→ Operation Runtime Plugin
→ Validation
→ Geometry Resolution
→ Planning
→ Preview
→ Export
```

Not:

```
Design Tool
→ operation-specific direct exporter
```

---

## Package Structure

```
services/api/app/cam/runtime/
├── __init__.py              # Package exports
├── dispatcher.py            # RuntimeDispatcher class
├── operation_runtime.py     # CamOperationRuntime protocol
├── operation_manifest.py    # OperationManifestV1 schema
��── plugin_registry.py       # RuntimePluginRegistry
└── runtime_results.py       # Normalized result contracts (Dev Order 58)
```

---

## Runtime Interface

```python
class CamOperationRuntime(Protocol):
    operation_type: str
    runtime_id: str

    def validate(self, intent: CamIntentV1) -> RuntimeValidationResult
    def resolve_geometry(self, intent: CamIntentV1) -> RuntimeGeometryResolution
    def plan(self, intent: CamIntentV1) -> RuntimePlanResult
    def preview(self, intent: CamIntentV1) -> RuntimePreviewResult
    def export(self, intent: CamIntentV1) -> RuntimeExportResult
```

Runtimes implement this protocol to handle specific operation types.

---

## Runtime Result Normalization (Dev Order 58)

All runtime plugins return normalized result contracts that share:

- **Deterministic structure:** Common base class with shared fields
- **Inspectable state:** Status, provenance, diagnostics
- **Governed invariants:** Hard-coded safety constraints
- **Provenance-aware:** Every result carries audit trail

### Shared Runtime Semantics

```python
class RuntimeResultBase(BaseModel):
    result_id: str                              # Unique ID for traceability
    schema_version: Literal["runtime-result.v1"]
    status: Literal["available", "placeholder", "unsupported", "error"]
    provenance: list[str]
    diagnostics: list[str]
    observational_only: Literal[True] = True   # Always true
```

### Stage-Specific Results

| Stage | Result Type | Key Field | Hard Invariant |
|-------|-------------|-----------|----------------|
| Validation | `RuntimeValidationResult` | `validation_gate` | `execution_ready = False`, `machine_operation_authorized = False` |
| Geometry | `RuntimeGeometryResolution` | `geometry_resolution_status` | — |
| Planning | `RuntimePlanResult` | `planning_stage` | — |
| Preview | `RuntimePreviewResult` | `preview_stage` | — |
| Export | `RuntimeExportResult` | `export_stage` | `machine_output_generated = False` |

### Result-Stage Lifecycle

```
validate()
  → RuntimeValidationResult (gate: green/yellow/red)
resolve_geometry()
  → RuntimeGeometryResolution (status: resolved/partial/placeholder/unsupported)
plan()
  → RuntimePlanResult (stage: placeholder/deterministic_stub/unsupported)
preview()
  → RuntimePreviewResult (stage: placeholder/preview_stub/unsupported)
export()
  → RuntimeExportResult (stage: placeholder/export_stub/unsupported)
```

---

## Manifest Invariants

The `OperationManifestV1` enforces hard invariants:

| Field | Value | Enforced |
|-------|-------|----------|
| `execution_ready` | Always `False` | Pydantic validator |
| `machine_operation_authorized` | Always `False` | Pydantic validator |

These invariants cannot be bypassed. The dispatcher does not authorize machine execution.

### Result ID References (Dev Order 58)

The manifest includes references to each stage's result for traceability:

```python
validation_result_id: str | None
geometry_result_id: str | None
plan_result_id: str | None
preview_result_id: str | None
export_result_id: str | None
```

---

## Dispatch Flow

Full stage chain (Dev Order 58):

```
1. Receive CamIntentV1
2. Resolve operation_type from intent
3. Look up runtime plugin in registry
4. If no plugin → return unsupported manifest (RED)
5. Call plugin.validate()
6. Call plugin.resolve_geometry()
7. Call plugin.plan()
8. Call plugin.preview()
9. Call plugin.export()
10. Return OperationManifestV1 with result IDs
```

---

## Unsupported Operation Behavior

When no plugin is registered for an operation type:

```python
OperationManifestV1(
    dispatch_status="unsupported_operation",
    validation_gate="red",
    execution_ready=False,
    machine_operation_authorized=False,
    diagnostics=["No runtime plugin registered for operation_type ..."]
)
```

This is not an exception — it's a valid dispatch result.

### Unsupported Runtime Semantics

Even unsupported operations return normalized results:

```python
RuntimePreviewResult(
    status="unsupported",
    preview_stage="unsupported",
    diagnostics=["Preview not supported for runtime"]
)
```

No raw dicts, None, or arbitrary strings.

---

## Placeholder Semantics

Placeholder results indicate structural completeness without full implementation:

- `status = "placeholder"` — Stage executed but returned stub
- `planning_stage = "placeholder"` — No real planning performed
- `preview_stage = "placeholder"` — No real preview generated

Placeholders preserve the full stage chain while awaiting real implementation.

---

## Operation Type Resolution

Temporary resolution behavior (until operation vocabulary is formally typed):

```python
def resolve_operation_type(intent: CamIntentV1) -> str:
    if intent.design.get("operation"):
        return str(intent.design["operation"])
    return str(intent.mode.value)
```

1. Use `design.operation` if present
2. Fall back to `mode.value`

---

## Governance Constraints

The dispatcher preserves these invariants:

| Constraint | Enforcement |
|------------|-------------|
| Runtime consumes intent | Protocol design |
| Runtime does not redefine intent | No intent mutation |
| Dispatcher does not generate machine output | No G-code/BCAM |
| Dispatcher does not authorize execution | Manifest validators |
| Dispatcher does not mutate geometry | Read-only intent |
| Dispatcher does not persist RMOS runs | No persistence calls |
| All results are observational only | `observational_only = True` |
| Machine output never generated | `machine_output_generated = False` |

---

## No Machine Output

The dispatcher skeleton does NOT:

- Generate toolpaths
- Export G-code
- Export BCAM
- Execute machine operations
- Create RMOS runs
- Perform postprocessing

These capabilities belong to future runtime plugins operating under explicit execution authorization.

---

## Future Plugin Migration Path

When migrating existing CAM operations to runtime plugins:

1. Create runtime class implementing `CamOperationRuntime`
2. Return normalized results from all five methods
3. Register with `RuntimePluginRegistry`
4. Dispatcher automatically routes matching intents
5. Existing direct exporters can coexist during migration
6. Deprecate direct exporters after parity verification

---

## Normalized Results Preserve Governance

```
Normalized runtime results preserve deterministic governance
before adaptive runtime intelligence exists.
```

All plugins speak the same runtime result language, preventing parallel runtime ontology drift.

---

## Related Documents

- [CAM_INTENT_SCHEMA_V1.md](../governance/CAM_INTENT_SCHEMA_V1.md) — canonical intent contract
- [CANONICAL_AUTHORITY_MAP.md](../governance/CANONICAL_AUTHORITY_MAP.md) — authority ownership
- [CANONICAL_ONTOLOGY_VOCABULARY.md](../governance/CANONICAL_ONTOLOGY_VOCABULARY.md) — runtime result vocabulary
- [CAM_GOVERNED_EXPORT_ARCHITECTURE.md](./CAM_GOVERNED_EXPORT_ARCHITECTURE.md) — export governance
