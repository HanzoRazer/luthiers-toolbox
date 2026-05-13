# Execution Capability Registry Model

**CAM Dev Order 7A — Future Translator Capability Declarations**

**Status:** Planning Only — No Implementation  
**Date:** 2026-05-13

---

## Purpose

This document defines the future capability registry for translators and postprocessors. It specifies how execution components declare their capabilities, distinct from the governance operation registry.

**This is architecture planning, not implementation.**

---

## Registry Separation

### Two Registries, Two Authorities

```
┌─────────────────────────────────────────────────────────────────────┐
│               CAM_OPERATION_REGISTRY (Governance)                    │
│                                                                      │
│  Purpose: Define what operations exist and their governance state   │
│  Authority: Lifecycle, policy, promotion                            │
│  Entries: nut_slot, drilling, pocket, etc.                         │
│  Owner: Governance layer                                            │
│  Location: app/cam/cam_operation_registry.py                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│            TRANSLATOR_CAPABILITY_REGISTRY (Execution)               │
│                                                                      │
│  Purpose: Define what translators/postprocessors can do            │
│  Authority: Execution capabilities, not governance                  │
│  Entries: dxf_r2000, grbl_postprocessor, etc.                      │
│  Owner: Execution layer                                             │
│  Location: Future — not implemented                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Registry Comparison

| Aspect | CAM_OPERATION_REGISTRY | TRANSLATOR_CAPABILITY_REGISTRY |
|--------|------------------------|-------------------------------|
| Scope | Operations | Translators/Postprocessors |
| Authority | Governance | Execution |
| Controls | Lifecycle policy | Execution capability |
| Maturity | Has maturity levels | Has execution states |
| Policy | Has exportability class | Has format constraints |

---

## Translator Capability Model

### Translator Entry Structure (Future)

```python
# PLANNING ONLY — Do not implement

@dataclass
class TranslatorCapability:
    """
    Capability declaration for a translator plugin.
    """
    
    # Identity
    translator_id: str          # Unique identifier
    translator_name: str        # Human-readable name
    translator_version: str     # Semantic version
    
    # Output format
    output_format: str          # "dxf", "svg", "toolpath", etc.
    output_format_version: str  # Format-specific version
    
    # Supported inputs
    supported_operations: list[str]      # CAM operations
    supported_geometry_types: list[str]  # Geometry types
    supported_units: list[str]           # Unit systems
    
    # Constraints
    max_entity_count: int       # Maximum entities
    max_complexity: str         # "simple", "moderate", "complex"
    
    # Execution state
    execution_state: str        # "validation_only", "approved", "active"
    validation_only: bool       # If True, cannot execute
    
    # Metadata
    description: str
    author: str
    license: str
    
    # Safety
    sandboxed: bool             # Requires sandboxed execution
    deterministic: bool         # Produces deterministic output
    resource_limited: bool      # Has resource limits
```

### Registry Structure (Future)

```python
# PLANNING ONLY

TRANSLATOR_CAPABILITY_REGISTRY: dict[str, TranslatorCapability] = {
    "dxf_r12": TranslatorCapability(
        translator_id="dxf_r12",
        translator_name="DXF R12 Translator",
        translator_version="1.0.0",
        output_format="dxf",
        output_format_version="R12",
        supported_operations=["nut_slot", "drilling", "pocket"],
        supported_geometry_types=["line", "arc", "circle"],
        supported_units=["mm", "inch"],
        max_entity_count=10000,
        max_complexity="moderate",
        execution_state="validation_only",
        validation_only=True,
        description="DXF R12 geometry translator for legacy CAM systems",
        author="luthiers-toolbox",
        license="MIT",
        sandboxed=True,
        deterministic=True,
        resource_limited=True,
    ),
    
    "dxf_r2000": TranslatorCapability(
        translator_id="dxf_r2000",
        translator_name="DXF R2000 Translator",
        translator_version="1.0.0",
        output_format="dxf",
        output_format_version="R2000",
        supported_operations=["nut_slot", "drilling", "pocket", "profile"],
        supported_geometry_types=["line", "arc", "circle", "lwpolyline", "spline"],
        supported_units=["mm", "inch"],
        max_entity_count=50000,
        max_complexity="complex",
        execution_state="validation_only",
        validation_only=True,
        description="DXF R2000 geometry translator for modern CAM systems",
        author="luthiers-toolbox",
        license="MIT",
        sandboxed=True,
        deterministic=True,
        resource_limited=True,
    ),
}
```

---

## Postprocessor Capability Model

### Postprocessor Entry Structure (Future)

```python
# PLANNING ONLY

@dataclass
class PostprocessorCapability:
    """
    Capability declaration for a postprocessor plugin.
    """
    
    # Identity
    postprocessor_id: str
    postprocessor_name: str
    postprocessor_version: str
    
    # Target
    controller_type: str        # "grbl", "fanuc", "shopbot", etc.
    controller_version: str     # Controller version
    output_dialect: str         # G-code dialect identifier
    
    # Supported inputs
    supported_operations: list[str]
    supported_toolpath_types: list[str]
    
    # Machine requirements
    required_axis_count: int
    supported_axis_count: list[int]
    required_capabilities: list[str]  # "spindle", "coolant", etc.
    
    # Output characteristics
    output_extension: str       # ".nc", ".sbp", etc.
    line_numbers: bool          # Includes line numbers
    checksum: bool              # Includes checksum
    
    # Execution state
    execution_state: str
    validation_only: bool
    
    # Safety
    sandboxed: bool
    deterministic: bool
    resource_limited: bool
```

### Registry Structure (Future)

```python
# PLANNING ONLY

POSTPROCESSOR_CAPABILITY_REGISTRY: dict[str, PostprocessorCapability] = {
    "grbl_1.1": PostprocessorCapability(
        postprocessor_id="grbl_1.1",
        postprocessor_name="GRBL 1.1 Postprocessor",
        postprocessor_version="1.0.0",
        controller_type="grbl",
        controller_version="1.1",
        output_dialect="grbl_1.1",
        supported_operations=["nut_slot", "drilling", "pocket"],
        supported_toolpath_types=["linear", "arc", "drill"],
        required_axis_count=3,
        supported_axis_count=[3],
        required_capabilities=["spindle"],
        output_extension=".nc",
        line_numbers=False,
        checksum=False,
        execution_state="validation_only",
        validation_only=True,
        sandboxed=True,
        deterministic=True,
        resource_limited=True,
    ),
}
```

---

## Capability Queries

### Query Functions (Future)

```python
# PLANNING ONLY

def get_translator_capability(translator_id: str) -> Optional[TranslatorCapability]:
    """Get translator capability by ID."""
    pass

def get_postprocessor_capability(postprocessor_id: str) -> Optional[PostprocessorCapability]:
    """Get postprocessor capability by ID."""
    pass

def list_translators_for_operation(operation: str) -> list[TranslatorCapability]:
    """List translators that support an operation."""
    pass

def list_postprocessors_for_controller(controller: str) -> list[PostprocessorCapability]:
    """List postprocessors for a controller type."""
    pass

def list_translators_for_format(format: str) -> list[TranslatorCapability]:
    """List translators that produce a format."""
    pass
```

---

## Execution State Model

### Execution States

```
VALIDATION_ONLY ←── Current state for all
       │
       ▼
EXECUTION_PENDING ←── Approved but not activated
       │
       ▼
EXECUTION_ENABLED ←── Active and usable
       │
       ▼
DEPRECATED ←── Superseded, use discouraged
       │
       ▼
DISABLED ←── Blocked from use
```

### State Transitions

| From | To | Requires |
|------|----|----------|
| VALIDATION_ONLY | EXECUTION_PENDING | Architecture approval |
| EXECUTION_PENDING | EXECUTION_ENABLED | Implementation + testing |
| EXECUTION_ENABLED | DEPRECATED | Newer version available |
| Any | DISABLED | Security issue or critical bug |

---

## Integration with Operation Registry

### Cross-Registry Validation

```python
# PLANNING ONLY

def validate_translator_operation_support(
    translator_id: str,
    operation: str,
) -> bool:
    """
    Validate that translator can handle operation.
    
    Checks:
    1. Operation exists in CAM_OPERATION_REGISTRY
    2. Operation is lifecycle_supported
    3. Translator exists in TRANSLATOR_CAPABILITY_REGISTRY
    4. Translator lists operation in supported_operations
    """
    pass
```

### Registry Consistency Rules

1. Translator cannot claim to support operation not in CAM_OPERATION_REGISTRY
2. Postprocessor cannot claim to support operation not in CAM_OPERATION_REGISTRY
3. Translator capability changes do not affect operation maturity
4. Operation maturity changes do not affect translator capabilities

---

## Existing Validation Layer Mapping

### Current Validation Modules → Future Registry

| Current | Future Registry Entry |
|---------|----------------------|
| `DXFTranslatorProfile` | `TRANSLATOR_CAPABILITY_REGISTRY["dxf_*"]` |
| `MachineProfileValidationOnly` | `POSTPROCESSOR_CAPABILITY_REGISTRY["*"]` |

### Validation Flow (Future)

```
Export Object
    │
    ▼
CAM_OPERATION_REGISTRY check (operation exists, lifecycle_supported)
    │
    ▼
TRANSLATOR_CAPABILITY_REGISTRY check (translator supports operation)
    │
    ▼
DXFTranslatorProfile validation (geometry compatibility)
    │
    ▼
[Approval Gate]
    │
    ▼
Translator Execution (if execution_state != "validation_only")
```

---

## Capability Discovery

### Discovery API (Future)

```python
# PLANNING ONLY

def discover_translators(
    operation: str,
    geometry_types: list[str],
    units: str,
) -> list[TranslatorCapability]:
    """
    Discover compatible translators.
    
    Returns translators that:
    - Support the operation
    - Support all required geometry types
    - Support the unit system
    """
    pass

def discover_postprocessors(
    operation: str,
    controller_type: str,
    axis_count: int,
) -> list[PostprocessorCapability]:
    """
    Discover compatible postprocessors.
    """
    pass
```

---

## Registry Governance

### Who Can Modify

| Action | Authority |
|--------|-----------|
| Add translator capability | Architecture review |
| Modify supported_operations | Architecture review |
| Change execution_state | Architecture approval |
| Enable execution | Human approval + testing |
| Disable translator | Security/admin |

### Audit Requirements

All registry modifications must:
- Be recorded in audit log
- Include justification
- Reference approval
- Be reversible

---

## Related Documents

- `TRANSLATOR_PLUGIN_STANDARD.md` — Plugin interface contracts
- `TRANSLATOR_EXECUTION_ARCHITECTURE.md` — Runtime topology
- `EXECUTION_BOUNDARY_POLICY.md` — Governance vs execution isolation

---

*Execution Capability Registry Model — CAM 7A — 2026-05-13*
