# C1 Runtime Assumption Inventory

**Phase**: C1 — Collection (no decisions, no changes)  
**Date**: 2026-05-18  
**Purpose**: Document implicit authority assumptions in CAM runtime systems

---

## 1. Dispatcher Authority Model

### 1.1 Explicit Disclaimers

**Source**: `app/cam/runtime/dispatcher.py:9-17`

```
The dispatcher routes intents to operation-specific runtimes.
It does NOT:
- Generate machine output
- Authorize execution
- Mutate geometry
- Persist RMOS runs
```

| Authority | Disclaimed | Enforcement Mechanism |
|-----------|------------|----------------------|
| Machine output generation | Yes | `machine_output_generated: Literal[False]` validator |
| Execution authorization | Yes | `execution_ready: Literal[False]` validator |
| Geometry mutation | Yes | Docstring only (no structural enforcement) |
| RMOS persistence | Yes | Docstring only (no structural enforcement) |

**Gap**: Two disclaimers have structural enforcement, two have only docstring enforcement.

---

### 1.2 Implicit Authorities (Unacknowledged)

| Authority | Evidence | Acknowledged? |
|-----------|----------|---------------|
| Operation type resolution | `resolve_operation_type(intent)` decides what type an intent is | No |
| Plugin selection | `_registry.get(operation_type)` decides which runtime handles intent | No |
| Provenance creation | `provenance.append(...)` creates lineage entries | No |
| Artifact creation | `RuntimeArtifactV1(...)` creates governed artifacts | No |
| Validation gate assignment | `validation_gate="red"` determines pass/fail | No |

**Record**: Dispatcher has 5 implicit authorities not documented in its docstring.

---

## 2. Plugin Authority Model

### 2.1 CamOperationRuntime Protocol

**Source**: `app/cam/runtime/operation_runtime.py`

Plugins must implement:

| Method | Input | Output | Implicit Authority |
|--------|-------|--------|-------------------|
| `validate` | CamIntentV1 | RuntimeValidationResult | Determines if intent is valid |
| `resolve_geometry` | CamIntentV1 | RuntimeGeometryResolution | Interprets geometry requirements |
| `plan` | CamIntentV1 | RuntimePlanResult | Determines operation sequence |
| `preview` | CamIntentV1 | RuntimePreviewResult | Creates visual representation |
| `export` | CamIntentV1 | RuntimeExportResult | Prepares export artifacts |

**Gap**: Plugins have significant interpretive authority over intent, but no governance contract exists for what interpretations are permitted.

---

### 2.2 Plugin Registration Authority

**Source**: `app/cam/runtime/plugin_registry.py`

```python
def register(self, runtime: CamOperationRuntime, operation_type: str) -> None:
```

| Registration Authority | Holder | Check |
|------------------------|--------|-------|
| Who can register | Any caller | None |
| What types can be claimed | Any string | None |
| Deregistration | Not implemented | N/A |

**Gap**: No governance over plugin registration. Any code can register any runtime for any operation type.

---

## 3. 7N Consumer Registration Gap

### 3.1 Expected Relationship

Per 7N specification, runtime consumers should:
1. Register via `register_runtime_semantic_consumer()`
2. Declare consumed ontology terms
3. Be validated against 7M registry

### 3.2 Actual State

| Runtime Component | 7N Registered? | Consumed Terms Declared? |
|-------------------|----------------|-------------------------|
| RuntimeDispatcher | No | No |
| CamOperationRuntime plugins | No | No |
| RuntimePluginRegistry | No | No |

**Gap**: Entire runtime dispatcher system operates outside 7N governance.

---

## 4. Geometry Authority Dependency

### 4.1 Authority Chain Expected

```
7M geometry_authority → dispatcher → plugin.resolve_geometry() → geometry system
```

### 4.2 Authority Chain Actual

```
dispatcher → plugin.resolve_geometry() → (direct call, no authority check)
```

**Evidence**: `app/cam/runtime/dispatcher.py:208`
```python
geometry_result = runtime.resolve_geometry(intent)
```

No call to:
- `get_canonical_term("geometry_authority")`
- Any geometry governance check
- Any 7M validation

**Gap**: Undeclared geometry authority consumption.

---

## 5. Result Schema Authority

### 5.1 Schema Version Authority

**Source**: `app/cam/runtime/runtime_results.py:42`

```python
schema_version: Literal["runtime-result.v1"] = "runtime-result.v1"
```

| Schema | Version | Owner | Registered? |
|--------|---------|-------|-------------|
| `operation-manifest.v1` | v1 | Dispatcher | No |
| `runtime-result.v1` | v1 | Runtime Results | No |

**Gap**: Schema versions exist but aren't registered in any governance system.

---

### 5.2 Result ID Authority

**Source**: `app/cam/runtime/runtime_results.py:23-25`

```python
def _generate_result_id() -> str:
    return f"rr_{uuid4().hex[:12]}"
```

| ID Type | Prefix | Generator | Governed? |
|---------|--------|-----------|-----------|
| Result ID | `rr_` | UUID | No |
| Manifest ID | `manifest-` | UUID | No |
| Artifact ID | `artifact-` | UUID | No |

**Gap**: ID generation patterns exist but aren't governed by 7M ontology.

---

## 6. Provenance Creation Authority

### 6.1 Provenance Patterns

**Source**: `app/cam/runtime/dispatcher.py:168, 183, 209, etc.`

```python
provenance: list[str] = [f"dispatcher:routed:{runtime_id}"]
provenance.append(f"runtime:validated:{runtime_id}")
provenance.append(f"runtime:geometry:{runtime_id}")
```

| Pattern | Meaning | Governed? |
|---------|---------|-----------|
| `dispatcher:routed:{id}` | Dispatcher routed to runtime | No |
| `dispatcher:unsupported_operation` | No plugin found | No |
| `runtime:validated:{id}` | Plugin validated intent | No |
| `runtime:geometry:{id}` | Plugin resolved geometry | No |
| `runtime:planned:{id}` | Plugin created plan | No |
| `runtime:preview:{id}` | Plugin created preview | No |
| `runtime:export:{id}` | Plugin created export | No |
| `dispatcher:runtime_error:{id}` | Exception occurred | No |

**Gap**: Provenance vocabulary is ad-hoc, not registered.

---

## 7. Summary of Authority Gaps

### High Priority

| Gap | Risk | Location |
|-----|------|----------|
| Runtime system outside 7N | Ungoverned ontology consumption | Entire dispatcher |
| Geometry authority undeclared | Implicit authority dependency | dispatcher.py:208 |
| Plugin registration ungoverned | Any code can claim operations | plugin_registry.py |

### Medium Priority

| Gap | Risk | Location |
|-----|------|----------|
| Provenance vocabulary unregistered | Inconsistent lineage semantics | dispatcher.py |
| Schema versions unregistered | Ungoverned contract evolution | runtime_results.py |
| ID prefixes unregistered | Inconsistent identification | runtime_results.py |

### Low Priority

| Gap | Risk | Location |
|-----|------|----------|
| Implicit dispatcher authorities | Undocumented decision-making | dispatcher.py |
| Plugin interpretive authority | Undefined interpretation bounds | operation_runtime.py |

---

## 8. Recommended C2 Actions (Not Implemented in C1)

1. **Register dispatcher as 7N consumer** with consumed terms: `runtime`, `intent`, `provenance`, `artifact`
2. **Add geometry_authority check** before calling `resolve_geometry()`
3. **Register provenance vocabulary** in 7M with action log semantics
4. **Register schema versions** in a schema governance system
5. **Add plugin registration governance** requiring 7N consumer registration

---

## C1 Rule Observed

> C1 makes semantic collisions visible. C1 does not make semantic decisions.

No changes were made. This inventory is evidence for C2 reconciliation.
