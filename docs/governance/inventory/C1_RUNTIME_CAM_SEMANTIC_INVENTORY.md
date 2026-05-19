# C1 Terminal 2: CAM/Runtime Semantic Inventory

**Phase**: C1 — Collection (no decisions, no changes)  
**Date**: 2026-05-18  
**Scope**: Runtime lifecycle terms, provenance semantics, dispatcher authority, plugin authority, execution-state semantics

---

## 1. Runtime Lifecycle Terms

### 1.1 Result Status Vocabulary

**Source**: `app/cam/runtime/runtime_results.py:44`

| Term | Meaning | Registered in 7M? | Collision Risk |
|------|---------|-------------------|----------------|
| `available` | Result successfully produced | No | Low |
| `placeholder` | Stub result, not yet implemented | No | Medium — overlaps "stub" concept |
| `unsupported` | Operation not supported by runtime | No | High — see collision log |
| `error` | Runtime error occurred | No | Medium — generic term |

**Lifecycle Axis**: Operational (describes result availability)

---

### 1.2 Dispatch Status Vocabulary

**Source**: `app/cam/runtime/operation_manifest.py:54-59`

| Term | Meaning | Registered in 7M? | Collision Risk |
|------|---------|-------------------|----------------|
| `unsupported_operation` | No plugin registered for operation type | No | Medium |
| `validated_only` | Validation passed, no further execution | No | Low |
| `planned_placeholder` | Planning stub completed | No | Low |
| `runtime_error` | Exception during dispatch | No | Medium |

**Lifecycle Axis**: Operational (describes dispatch outcome)

---

### 1.3 Validation Gate Vocabulary

**Source**: `app/cam/runtime/operation_manifest.py:61`, `runtime_results.py:74`

| Term | Meaning | Registered in 7M? | Collision Risk |
|------|---------|-------------------|----------------|
| `green` | Validation passed | No | High — duplicated elsewhere |
| `yellow` | Validation passed with warnings | No | High — duplicated elsewhere |
| `red` | Validation failed | No | High — duplicated elsewhere |

**Lifecycle Axis**: Enforcement (gate-checking semantics)

**Note**: This vocabulary is duplicated in:
- `app/cam/dxf_validation_gate.py`
- Multiple translator readiness systems
- Governance check systems

---

### 1.4 Geometry Resolution Status

**Source**: `app/cam/runtime/runtime_results.py:117-122`

| Term | Meaning | Registered in 7M? | Collision Risk |
|------|---------|-------------------|----------------|
| `resolved` | Geometry successfully resolved | No | Low |
| `partial` | Partial geometry resolution | No | Low |
| `placeholder` | Stub resolution | No | Medium — overlaps result status |
| `unsupported` | Geometry resolution not supported | No | High — overlaps result status |

**Lifecycle Axis**: Operational

---

### 1.5 Planning/Preview/Export Stage Vocabularies

**Source**: `app/cam/runtime/runtime_results.py:136-179`

| Stage | Terms | Registered? |
|-------|-------|-------------|
| Planning | `placeholder`, `deterministic_stub`, `unsupported` | No |
| Preview | `placeholder`, `preview_stub`, `unsupported` | No |
| Export | `placeholder`, `export_stub`, `unsupported` | No |

**Lifecycle Axis**: Operational

---

## 2. Runtime Provenance Semantics

### 2.1 Provenance List Pattern

**Source**: `app/cam/runtime/runtime_results.py:46`, `operation_manifest.py:79`

```python
provenance: list[str] = Field(default_factory=list)
```

**Usage Pattern**: Append-only string list recording stage executions

**Examples**:
- `"dispatcher:routed:{runtime_id}"`
- `"runtime:validated:{runtime_id}"`
- `"runtime:geometry:{runtime_id}"`
- `"dispatcher:unsupported_operation"`

**Semantic Type**: Action log (what happened)

**Collision with 7M**: 7M defines `provenance` as "immutable lineage chain recording governance decisions" — runtime usage is action log, not governance chain.

---

### 2.2 Diagnostics List Pattern

**Source**: `app/cam/runtime/runtime_results.py:47`, `operation_manifest.py:80`

```python
diagnostics: list[str] = Field(default_factory=list)
```

**Usage Pattern**: Free-form debug/error messages

**Semantic Type**: Debugging (why something happened)

**Not in 7M**: No `diagnostics` term registered

---

## 3. Dispatcher Authority Assumptions

### 3.1 Explicit Non-Authorities

**Source**: `app/cam/runtime/dispatcher.py:9-17`

The dispatcher explicitly disclaims:

| Authority | Disclaimed? | Enforcement |
|-----------|-------------|-------------|
| Generate machine output | Yes | `machine_output_generated: Literal[False]` |
| Authorize execution | Yes | `execution_ready: Literal[False]` |
| Mutate geometry | Yes | Docstring only |
| Persist RMOS runs | Yes | Docstring only |

---

### 3.2 Implicit Authorities (Undeclared)

| Authority | Location | Risk |
|-----------|----------|------|
| Operation type resolution | `resolve_operation_type()` | Low — temporary behavior |
| Plugin routing | `_registry.get(operation_type)` | Medium — routing is authority |
| Provenance generation | `provenance.append()` | Medium — creates action lineage |

---

### 3.3 Geometry Authority Dependency

**Source**: `app/cam/runtime/dispatcher.py:208`

```python
geometry_result = runtime.resolve_geometry(intent)
```

The dispatcher calls `resolve_geometry()` but:
- Does NOT declare geometry authority dependency
- Does NOT check 7M `geometry_authority` term
- Does NOT validate geometry provenance

**Record**: Undeclared geometry authority dependency

---

## 4. Plugin Authority Assumptions

### 4.1 CamOperationRuntime Protocol

**Source**: `app/cam/runtime/operation_runtime.py` (Protocol)

Required methods:
- `validate(intent) -> RuntimeValidationResult`
- `resolve_geometry(intent) -> RuntimeGeometryResolution`
- `plan(intent) -> RuntimePlanResult`
- `preview(intent) -> RuntimePreviewResult`
- `export(intent) -> RuntimeExportResult`

**Plugin Authority Model**: Plugins implement stages but don't authorize execution

---

### 4.2 Plugin Registration Pattern

**Source**: `app/cam/runtime/plugin_registry.py`

```python
registry.register(runtime_plugin)
```

**Authority Model**: Registration grants routing, not execution authority

**Not in 7N**: Plugin registry is not connected to 7N consumption registry

---

## 5. Execution-State Semantics

### 5.1 Hard Invariants (Structurally Enforced)

| Invariant | Location | Type | Enforcement |
|-----------|----------|------|-------------|
| `execution_ready` | Manifest, ValidationResult | `Literal[False]` | Pydantic validator |
| `machine_operation_authorized` | Manifest, ValidationResult | `Literal[False]` | Pydantic validator |
| `observational_only` | RuntimeResultBase | `Literal[True]` | Pydantic validator |
| `machine_output_generated` | RuntimeExportResult | `Literal[False]` | Pydantic validator |

---

### 5.2 Invariant Naming Collision

| Dev 54-58 Term | 7L-7O Term | Same Semantic? |
|----------------|------------|----------------|
| `execution_ready` | `execution_authorized` | Yes |
| `machine_operation_authorized` | `machine_output_allowed` | Yes |
| `observational_only` | `immutable` | Partial — different focus |

**Record**: Parallel invariant vocabularies for same concepts

---

## 6. Cross-Reference with 7M Registry

### 6.1 Terms Used but Not Registered

| Term | Domain | Usage Location | Registration Status |
|------|--------|----------------|---------------------|
| `dispatch_status` | CAM Runtime | operation_manifest.py | Not registered |
| `result_status` | CAM Runtime | runtime_results.py | Not registered |
| `validation_gate` | CAM Runtime | operation_manifest.py | Not registered |
| `geometry_resolution_status` | CAM Runtime | runtime_results.py | Not registered |
| `planning_stage` | CAM Runtime | runtime_results.py | Not registered |
| `preview_stage` | CAM Runtime | runtime_results.py | Not registered |
| `export_stage` | CAM Runtime | runtime_results.py | Not registered |
| `observational_only` | CAM Runtime | runtime_results.py | Not registered |

---

### 6.2 Terms Registered and Used

| 7M Term | Runtime Usage | Consistent? |
|---------|---------------|-------------|
| `runtime` | Dispatcher routes to runtimes | Yes |
| `intent` | `CamIntentV1` consumed | Yes |
| `provenance` | Action log in results | Partial — semantic split |
| `validation` | `RuntimeValidationResult` | Yes |
| `execution` | Invariants disclaim execution | Yes |
| `artifact` | `RuntimeArtifactV1` | Yes |

---

### 6.3 Terms Registered but Not Observed in Runtime

| 7M Term | Expected Usage | Observed? |
|---------|----------------|-----------|
| `translator` | Export should involve translator | No — export is stub |
| `quarantine` | Failed validation should quarantine | No — not implemented |
| `readiness` | Should check readiness before dispatch | No — not checked |
| `serialization` | Export should use serialization semantics | No — stub only |

---

## 7. Summary of C1 Findings

### High-Priority Collisions

1. **validation_gate duplication** — `green/yellow/red` appears in 3+ locations
2. **provenance semantic split** — action log vs governance chain
3. **invariant naming divergence** — Dev 54-58 vs 7L-7O vocabularies
4. **unsupported term overloading** — used in result_status AND geometry_resolution_status

### Authority Gaps

1. `resolve_geometry()` has undeclared geometry authority dependency
2. Plugin registry not connected to 7N consumption registry
3. Runtime results claim `observational_only` but 7M doesn't register this concept

### Lifecycle Axis Classification

| Vocabulary | Axis |
|------------|------|
| Result status | Operational |
| Dispatch status | Operational |
| Validation gate | Enforcement |
| Stage progressions | Operational |

---

## C1 Rule Observed

> C1 makes semantic collisions visible. C1 does not make semantic decisions.

No changes were made. This inventory is evidence for C2 reconciliation.
